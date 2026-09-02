"""Version and finalize phase bodies for the catalog-pack publication transaction."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from catalog_pack_oci import build_oci_layout, tree_snapshot
from catalog_pack_policy import prove_support_releases
from catalog_pack_shared import *


def expected_support(
    explicit: Mapping[str, str] | None,
    environment: Mapping[str, str],
) -> dict[str, str] | None:
    if explicit is not None:
        return {"commit": explicit["commit"], "blob": explicit["blob"]}
    commit = environment.get("CATALOG_PACK_SUPPORT_COMMIT")
    blob = environment.get("CATALOG_PACK_SUPPORT_BLOB")
    if commit or blob:
        require(bool(commit) and bool(blob), "recorded support identity is incomplete")
        return {"commit": str(commit), "blob": str(blob)}
    return None


def require_same_support(observed: Mapping[str, Any], expected: Mapping[str, str], when: str) -> None:
    require(
        observed.get("support_commit") == expected["commit"],
        f"Effigy support commit drifted {when}",
    )
    require(
        observed.get("support_blob_oid") == expected["blob"],
        f"Effigy support blob drifted {when}",
    )


def require_public_package(adapter: Any) -> dict[str, Any]:
    package = adapter.package_state()
    require(package.get("visibility") == "public", "package is not public")
    require(
        package.get("repository") == PACK_GITHUB_REPOSITORY,
        f"package is not linked to {PACK_GITHUB_REPOSITORY}",
    )
    return package


def emit_github_output(fields: Mapping[str, str], environment: Mapping[str, str]) -> None:
    path = environment.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for name, value in fields.items():
            handle.write(f"{name}={value}\n")


def forbid_finalize_writes(adapter: Any, *, allow_stable: bool) -> None:
    kinds = [kind for kind, _ in getattr(adapter, "writes", [])]
    require("visibility" not in kinds, "publication must not PATCH package visibility")
    require("stable-rollback" not in kinds, "publication must not delete a manifest to imitate absent stable")
    if not allow_stable:
        require("stable" not in kinds, "stable moved before the finalize phase")


def phase_version(
    *,
    adapter: Any,
    pack_root: Path,
    identity: dict[str, Any],
    tag: str,
    digest: str,
    version_state: str,
    previous_stable: str | None,
    environment: Mapping[str, str],
    report: dict[str, Any],
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-publish-") as temporary:
        layout_dir = Path(temporary) / "layout"
        built = build_oci_layout(layout_dir, pack_root, identity)
        require(built["manifest_digest"] == digest, "durable publication layout digest drifted from the candidate")
        if version_state == "absent":
            adapter.push_version(layout_dir, tag, digest)
        report["gates"].append("package-version")
        resolved = adapter.inspect_version(tag)
        require(resolved == digest, f"version pointer is {resolved}, expected {digest}")
        report["gates"].append("version-reresolve")
        require(adapter.inspect_stable() == previous_stable, "version publish moved stable")
    emit_github_output(
        {
            "manifest_digest": digest,
            "support_commit": report["support"]["commit"],
            "support_blob": report["support"]["blob"],
        },
        environment,
    )
    writes = list(getattr(adapter, "writes", []))
    kinds = [kind for kind, _ in writes]
    if version_state == "absent":
        require(kinds == ["package-version"], f"version publish write set was {kinds}")
    else:
        require(kinds == [], f"same-digest version retry recorded writes: {kinds}")
    report["writes"] = writes
    report["push_attempted"] = version_state == "absent"
    report["stable_digest"] = previous_stable
    return report


def phase_finalize(
    *,
    adapter: Any,
    authority: Path | None,
    pack_root: Path,
    tag: str,
    digest: str,
    previous_stable: str | None,
    probe: Callable[[], dict[str, Any]],
    release_getter: Callable[[str], dict[str, Any]] | None,
    support: Mapping[str, Any],
    expected: Mapping[str, str] | None,
    report: dict[str, Any],
) -> dict[str, Any]:
    adapter.verify_attestation(digest)
    report["gates"].append("attestation")
    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-finalize-") as temporary:
        pulled = Path(temporary) / "anonymous"
        adapter.anonymous_pull(digest, pulled)
        require(tree_snapshot(pulled) == tree_snapshot(pack_root), "anonymous digest pull did not reproduce exact pack bytes")
        if getattr(adapter, "anonymous_pulls", 1) == 0:
            fail("anonymous digest pull was not performed")
        report["gates"].append("anonymous-pull")

        adapter.refresh_support_authority(authority)
        support_again = probe()
        require_same_support(
            support_again,
            {"commit": support["support_commit"], "blob": support["support_blob_oid"]},
            "during finalization",
        )
        if expected is not None:
            require_same_support(support_again, expected, "since version publish")
        report["releases"] = prove_support_releases(support_again, getter=release_getter)
        report["gates"].append("support-recheck")

        recorded_previous = adapter.inspect_stable()
        require(recorded_previous == previous_stable, "stable changed before the authorized move")
        if recorded_previous is None:
            adapter.tag_digest(digest, STABLE_TAG)
        elif recorded_previous != digest:
            adapter.tag_digest(recorded_previous, STABLE_TAG)
            require(adapter.inspect_stable() == recorded_previous, "rollback did not restore the previous stable digest")
            adapter.tag_digest(digest, STABLE_TAG)
        require(adapter.inspect_stable() == digest, "stable does not resolve to the candidate digest")
        require(adapter.inspect_version(tag) == digest, "stable move changed the version pointer")
        report["gates"].append("stable")
        report["rollback_exercised"] = recorded_previous is not None and recorded_previous != digest
        report["absent_stable_recorded"] = recorded_previous is None

    writes = list(getattr(adapter, "writes", []))
    kinds = [kind for kind, _ in writes]
    forbid_finalize_writes(adapter, allow_stable=True)
    if recorded_previous is None:
        require(kinds.count("stable") == 1, "absent first-publication stable must move once")
        require("stable-rollback" not in kinds, "absent stable used a delete rollback")
    elif recorded_previous != digest:
        require(kinds.count("stable") == 2, "live retag rollback must restore previous then candidate")
    require(adapter.inspect_version(tag) == digest, "finalize changed the version pointer")
    report["writes"] = writes
    report["stable_digest"] = digest
    report["previous_stable"] = recorded_previous
    report["same_digest_retry"] = "would-reuse"
    return report
