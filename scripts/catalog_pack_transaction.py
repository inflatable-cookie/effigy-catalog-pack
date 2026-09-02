"""Ordered first-publication transaction. Writes happen only after every card gate."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from catalog_pack_authority import prove_support
from catalog_pack_oci import build_oci_layout, deterministic_oci_proof, tree_snapshot
from catalog_pack_policy import prove_support_releases
from catalog_pack_publication import actual_source_identity, planned_source_identity
from catalog_pack_shared import *


def run_publication(
    *,
    authority: Path | None,
    source_tag: str | None = None,
    source_ref: str | None = None,
    adapter: Any,
    mutate: bool,
    release_getter: Callable[[str], dict[str, Any]] | None = None,
    support_probe: Callable[[], dict[str, Any]] | None = None,
    pack_root: Path = PACK_ROOT,
    live_gate_env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build the candidate, then mutate only in gate order."""

    from catalog_pack_live import LiveRegistry
    from catalog_pack_registry import FakeRegistry, require_live_mutation_gate

    pack_facts = validate_pack_tree(pack_root)
    gates: list[str] = []
    require((source_tag is None) == (source_ref is None), "source tag and source ref must be supplied together")
    if source_tag is not None:
        identity = actual_source_identity(source_tag, source_ref or "", pack_facts["pack_version"])
    else:
        require(
            not mutate or isinstance(adapter, FakeRegistry),
            "live publication requires an existing annotated source tag and peeled commit",
        )
        identity = planned_source_identity(pack_facts["pack_version"])
    gates.append("source-identity")

    probe = support_probe or (lambda: prove_support(authority, True))
    support = probe()
    require(support.get("support_checked") is True, "publication requires current Effigy support proof")
    require(support.get("import_pin_used") is False, "publication must not use the one-time import pin as support authority")
    gates.append("support-local")
    releases = prove_support_releases(support, getter=release_getter)
    gates.append("support-releases")

    candidate = deterministic_oci_proof(identity, pack_root, run_oras=False)
    tag = f"v{pack_facts['pack_version']}"
    digest = candidate["manifest_digest"]
    require(candidate["reference"] == f"{OCI_REPOSITORY}:{tag}", "candidate reference does not match the official repository")
    gates.append("candidate")

    remote_digest = adapter.inspect_version(tag)
    if remote_digest is None:
        version_state = "absent"
    elif remote_digest == digest:
        version_state = "same-digest"
    else:
        fail(f"collision rejected: {remote_digest} is already recorded for {tag}")
    gates.append("remote-version")

    previous_stable = adapter.inspect_stable()
    plan = {
        "would_push_version": version_state == "absent",
        "would_reuse_version": version_state == "same-digest",
        "would_move_stable": previous_stable != digest,
        "previous_stable": previous_stable,
        "candidate_digest": digest,
    }
    if not mutate:
        return {
            "mutated": False,
            "network_access": release_getter is None,
            "push_attempted": False,
            "gates": gates,
            "writes": list(getattr(adapter, "writes", [])),
            "plan": plan,
            "source_identity": identity,
            "support": {
                "commit": support["support_commit"],
                "blob": support["support_blob_oid"],
            },
            "releases": releases,
            "candidate_digest": digest,
            "version_state": version_state,
        }

    if isinstance(adapter, LiveRegistry) or live_gate_env is not None:
        require_live_mutation_gate(live_gate_env)

    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-publish-") as temporary:
        publish_root = Path(temporary)
        layout_dir = publish_root / "layout"
        built = build_oci_layout(layout_dir, pack_root, identity)
        require(built["manifest_digest"] == digest, "durable publication layout digest drifted from the candidate")
        if version_state == "absent":
            adapter.push_version(layout_dir, tag, digest)
        gates.append("package-version")
        resolved = adapter.inspect_version(tag)
        require(resolved == digest, f"version pointer is {resolved}, expected {digest}")
        gates.append("version-reresolve")

        adapter.set_public()
        package = adapter.package_state()
        require(package.get("visibility") == "public", "package is not public")
        require(
            package.get("repository") == PACK_GITHUB_REPOSITORY,
            f"package is not linked to {PACK_GITHUB_REPOSITORY}",
        )
        gates.append("visibility-linkage")

        adapter.attest(digest, OCI_REPOSITORY)
        adapter.verify_attestation(digest)
        gates.append("attestation")

        pulled = publish_root / "anonymous"
        adapter.anonymous_pull(digest, pulled)
        require(tree_snapshot(pulled) == tree_snapshot(pack_root), "anonymous digest pull did not reproduce exact pack bytes")
        if getattr(adapter, "anonymous_pulls", 1) == 0:
            fail("anonymous digest pull was not performed")
        gates.append("anonymous-pull")

        support_again = probe()
        require(
            support_again.get("support_commit") == support["support_commit"],
            "Effigy support commit changed during publication",
        )
        require(
            support_again.get("support_blob_oid") == support["support_blob_oid"],
            "Effigy support blob changed during publication",
        )
        gates.append("support-recheck")

        recorded_previous = adapter.inspect_stable()
        adapter.tag_digest(digest, STABLE_TAG)
        require(adapter.inspect_stable() == digest, "stable does not resolve to the candidate digest")
        gates.append("stable")

        if recorded_previous is None:
            adapter.untag(STABLE_TAG)
            require(adapter.inspect_stable() is None, "rollback did not restore absent stable")
        else:
            adapter.tag_digest(recorded_previous, STABLE_TAG)
            require(adapter.inspect_stable() == recorded_previous, "rollback did not restore the previous stable digest")
        require(adapter.inspect_version(tag) == digest, "rollback changed the version pointer")
        adapter.tag_digest(digest, STABLE_TAG)
        require(adapter.inspect_stable() == digest, "stable was not restored to the candidate digest after rollback")
        gates.append("rollback-exercise")

        retry_state = adapter.inspect_version(tag)
        require(retry_state == digest, "same-digest retry observed a different version digest")
        gates.append("same-digest-retry")

    writes = list(getattr(adapter, "writes", []))
    write_kinds = [kind for kind, _ in writes]
    if version_state == "absent":
        require(write_kinds, "publication recorded no writes")
        require(write_kinds[0] == "package-version", "package write was not the first mutation")
    require("stable" in write_kinds, "stable was not moved")
    require(write_kinds.index("attestation") < write_kinds.index("stable"), "stable moved before attestation")
    require("visibility" in write_kinds, "public visibility was not set")
    require(write_kinds.index("visibility") < write_kinds.index("attestation"), "attestation ran before public visibility")
    require(write_kinds.index("attestation") < write_kinds.index("stable"), "stable moved before attestation")
    return {
        "mutated": True,
        "push_attempted": version_state == "absent",
        "gates": gates,
        "writes": writes,
        "plan": plan,
        "source_identity": identity,
        "support": {
            "commit": support["support_commit"],
            "blob": support["support_blob_oid"],
        },
        "releases": releases,
        "candidate_digest": digest,
        "version_state": version_state,
        "stable_digest": digest,
        "previous_stable": recorded_previous,
        "package": package,
        "rollback_exercised": True,
        "same_digest_retry": "would-reuse",
    }
