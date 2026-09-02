"""Ordered first-publication transaction. Writes happen only after every card gate."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from catalog_pack_authority import prove_support
from catalog_pack_oci import deterministic_oci_proof
from catalog_pack_phases import (
    emit_github_output,
    expected_support as recorded_support_identity,
    forbid_finalize_writes,
    phase_finalize,
    phase_version,
    require_public_package,
    require_same_support,
)
from catalog_pack_policy import prove_support_releases
from catalog_pack_publication import actual_source_identity, planned_source_identity
from catalog_pack_shared import *

PUBLICATION_PHASES = ("version", "finalize-preflight", "finalize")


def run_publication(
    *,
    authority: Path | None,
    source_tag: str | None = None,
    source_ref: str | None = None,
    adapter: Any,
    mutate: bool,
    phase: str = "version",
    release_getter: Callable[[str], dict[str, Any]] | None = None,
    support_probe: Callable[[], dict[str, Any]] | None = None,
    pack_root: Path = PACK_ROOT,
    live_gate_env: Mapping[str, str] | None = None,
    expected_support: Mapping[str, str] | None = None,
    runtime_env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build the candidate, then mutate only the requested phase after every gate."""

    from catalog_pack_registry import FakeRegistry, require_live_mutation_gate

    environment = dict(os.environ if runtime_env is None else runtime_env)
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
    recorded_digest = environment.get("CATALOG_PACK_VERSION_DIGEST")
    if recorded_digest:
        require(recorded_digest == digest, "recorded version digest drifted from the candidate")
    support_identity = {
        "commit": support["support_commit"],
        "blob": support["support_blob_oid"],
    }
    expected = recorded_support_identity(expected_support, environment)
    plan = {
        "would_push_version": version_state == "absent",
        "would_reuse_version": version_state == "same-digest",
        "would_move_stable": previous_stable != digest,
        "previous_stable": previous_stable,
        "candidate_digest": digest,
    }
    report = {
        "mutated": False,
        "network_access": release_getter is None,
        "push_attempted": False,
        "gates": gates,
        "writes": list(getattr(adapter, "writes", [])),
        "plan": plan,
        "source_identity": identity,
        "support": support_identity,
        "releases": releases,
        "candidate_digest": digest,
        "version_state": version_state,
        "previous_stable": previous_stable,
        "phase": "plan",
    }
    if not mutate:
        return report

    require(phase in PUBLICATION_PHASES, f"publication phase is {phase}, expected one of {PUBLICATION_PHASES}")
    if getattr(adapter, "requires_live_gate", False) or live_gate_env is not None:
        require_live_mutation_gate(live_gate_env if live_gate_env is not None else environment)
    report["phase"] = phase
    report["mutated"] = True

    if phase == "version":
        return phase_version(
            adapter=adapter,
            pack_root=pack_root,
            identity=identity,
            tag=tag,
            digest=digest,
            version_state=version_state,
            previous_stable=previous_stable,
            environment=environment,
            report=report,
        )
    require(
        version_state == "same-digest",
        f"finalize requires the version pointer to already be {digest}, observed {remote_digest}",
    )
    if expected is not None:
        require_same_support(support, expected, "since version publish")
    package = require_public_package(adapter)
    report["package"] = package
    gates.append("visibility-linkage")
    emit_github_output({"manifest_digest": digest}, environment)
    if phase == "finalize-preflight":
        report["writes"] = list(getattr(adapter, "writes", []))
        forbid_finalize_writes(adapter, allow_stable=False)
        return report
    return phase_finalize(
        adapter=adapter,
        authority=authority,
        pack_root=pack_root,
        tag=tag,
        digest=digest,
        previous_stable=previous_stable,
        probe=probe,
        release_getter=release_getter,
        support=support,
        expected=expected,
        report=report,
    )
