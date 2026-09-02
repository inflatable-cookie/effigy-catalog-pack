"""Network-free publication-transaction and support/import split proofs."""

from __future__ import annotations

from catalog_pack_authority import prove_import, prove_support, resolve_authority
from catalog_pack_constants import IMPORT_AUTHORITY_COMMIT
from catalog_pack_policy import prove_support_releases, version_admitted
from catalog_pack_registry import FakeRegistry, require_live_mutation_gate
from catalog_pack_shared import *
from catalog_pack_transaction import run_publication


def _support_fixture(commit: str = "a" * 40, blob: str = "b" * 40) -> dict[str, Any]:
    return {
        "support_checked": True,
        "import_pin_used": False,
        "support_commit": commit,
        "support_blob_oid": blob,
        "support_as_of_release": "0.12.1",
        "support_required_versions": ["0.12.1"],
        "as_of_release": "0.12.1",
        "required_versions": ["0.12.1"],
    }


def _release_fixture(path: str) -> dict[str, Any]:
    if path.endswith("/releases/latest"):
        return {"draft": False, "prerelease": False, "tag_name": "v0.12.1"}
    require(path.endswith("/releases/tags/v0.12.1"), f"unexpected release GET {path}")
    return {"draft": False, "prerelease": False, "tag_name": "v0.12.1"}


def _run(adapter: FakeRegistry, **extra: Any) -> dict[str, Any]:
    return run_publication(
        authority=None,
        adapter=adapter,
        mutate=True,
        release_getter=_release_fixture,
        support_probe=lambda: _support_fixture(),
        **extra,
    )


def support_import_split_proof(authority: Path | None, require_authority: bool) -> dict[str, Any]:
    if authority is None:
        if require_authority:
            fail("Effigy authority checkout is required for the support/import split proof")
        return {"skipped": True}
    support = prove_support(authority, True)
    imported = prove_import(authority)
    require(support["import_pin_used"] is False, "current support still used the import pin")
    require(support["support_commit"] != IMPORT_AUTHORITY_COMMIT, "current support is still pinned to the import commit")
    require(imported["authority_commit"] == IMPORT_AUTHORITY_COMMIT, "import proof lost the immutable import commit")
    require(support["authority_commit"] == support["support_commit"], "support commit aliases diverged")
    require(
        imported["current_support_commit"] == support["support_commit"],
        "import proof did not observe the current default-branch support commit",
    )
    return {
        "distinct": True,
        "support_commit": support["support_commit"],
        "import_commit": imported["authority_commit"],
        "support_blob_oid": support["support_blob_oid"],
        "import_support_blob_oid": imported["support_blob_oid"],
    }


def mutation_gate_proof() -> dict[str, Any]:
    cases = {
        "empty": {},
        "actions-only": {"GITHUB_ACTIONS": "true"},
        "wrong-event": {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REPOSITORY": PACK_GITHUB_REPOSITORY,
            "GITHUB_ENVIRONMENT": PUBLICATION_ENVIRONMENT,
            PUBLICATION_MUTATE_ENV: "1",
        },
        "wrong-repo": {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": "someone/else",
            "GITHUB_ENVIRONMENT": PUBLICATION_ENVIRONMENT,
            PUBLICATION_MUTATE_ENV: "1",
        },
    }
    for name, env in cases.items():
        try:
            require_live_mutation_gate(env)
        except CheckFailure:
            continue
        fail(f"mutation gate permitted {name}")
    require_live_mutation_gate(
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": PACK_GITHUB_REPOSITORY,
            "GITHUB_ENVIRONMENT": PUBLICATION_ENVIRONMENT,
            PUBLICATION_MUTATE_ENV: "1",
        }
    )
    return {"fail_closed": True, "accepted_protected_dispatch": True}


def publication_transaction_proof() -> dict[str, Any]:
    entry = (ROOT / "scripts" / "catalog_pack.py").read_text()
    prefix, _, _ = entry.partition("def publish_command")
    require("catalog_pack_live" not in prefix, "ordinary catalog_pack entry imports the live registry")
    require(not version_admitted("0.13.0", ">=0.12, <0.13"), "current pack range must reject 0.13.0")

    first = FakeRegistry()
    created = _run(first)
    kinds = [kind for kind, _ in created["writes"]]
    require(kinds[0] == "package-version", "first write was not the version package")
    require(kinds.index("visibility") < kinds.index("attestation"), "visibility did not precede attestation")
    require(kinds.index("attestation") < kinds.index("stable"), "stable moved before attestation")
    require(created["rollback_exercised"] is True, "rollback was not exercised")
    require(first.inspect_version("v1.0.0") == created["candidate_digest"], "version pointer drifted")
    require(first.inspect_stable() == created["candidate_digest"], "stable did not finish on the candidate")
    require(first.anonymous_pulls >= 1, "anonymous pull was skipped")

    retry = FakeRegistry(version_digest=created["candidate_digest"], visibility="public", repository=PACK_GITHUB_REPOSITORY)
    retried = _run(retry)
    require(retried["version_state"] == "same-digest", "same-digest retry was not recognized")
    require(retried["push_attempted"] is False, "same-digest retry attempted a package overwrite")

    colliding = FakeRegistry(version_digest="sha256:" + "c" * 64)
    try:
        _run(colliding)
    except CheckFailure as error:
        require("collision rejected" in str(error), "different-digest collision failed for the wrong reason")
    else:
        fail("different-digest collision was not rejected")
    require(colliding.writes == [], "collision mutated remote state")

    stale_values = [_support_fixture("a" * 40), _support_fixture("d" * 40)]

    def stale_probe() -> dict[str, Any]:
        return stale_values.pop(0)

    stale = FakeRegistry()
    try:
        run_publication(
            authority=None,
            adapter=stale,
            mutate=True,
            release_getter=_release_fixture,
            support_probe=stale_probe,
        )
    except CheckFailure as error:
        require("support commit changed" in str(error), "stale support failed for the wrong reason")
    else:
        fail("stale support input was not rejected")
    require("stable" not in [kind for kind, _ in stale.writes], "stale support moved stable")

    class PrivatePackage(FakeRegistry):
        def set_public(self) -> None:
            self.writes.append(("visibility", "private"))

    private = PrivatePackage()
    try:
        _run(private)
    except CheckFailure as error:
        require("anonymous pull requires public" in str(error) or "package is not public" in str(error), str(error))
    else:
        fail("private package was treated as anonymously readable")

    class Unattested(FakeRegistry):
        def attest(self, digest: str, subject_name: str) -> None:
            self.writes.append(("attestation-skipped", digest))

    unattested = Unattested()
    try:
        _run(unattested)
    except CheckFailure as error:
        require("no digest-bound attestation" in str(error), str(error))
    else:
        fail("unattested subject was allowed to continue")
    require("stable" not in [kind for kind, _ in unattested.writes], "unattested subject moved stable")

    planned = run_publication(
        authority=None,
        adapter=FakeRegistry(),
        mutate=False,
        release_getter=_release_fixture,
        support_probe=lambda: _support_fixture(),
    )
    require(planned["mutated"] is False, "plan mode mutated")
    require(planned["push_attempted"] is False, "plan mode attempted a push")
    require(planned["writes"] == [], "plan mode recorded writes")
    require("remote-version" in planned["gates"], "plan mode skipped remote inspection")
    require("stable" not in planned["gates"], "plan mode reached stable")

    try:
        run_publication(
            authority=None,
            adapter=FakeRegistry(),
            mutate=True,
            live_gate_env={},
            release_getter=_release_fixture,
            support_probe=lambda: _support_fixture(),
        )
    except CheckFailure as error:
        require("GitHub Actions" in str(error), str(error))
    else:
        fail("empty live gate permitted mutation")

    return {
        "absent_creates": True,
        "same_digest_reuses": True,
        "collision_rejected": True,
        "stale_support_rejected": True,
        "private_rejected": True,
        "unattested_rejected": True,
        "plan_is_read_only": True,
        "live_gate_fail_closed": True,
        "candidate_digest": created["candidate_digest"],
        "write_order": kinds,
    }


def publication_check(authority: Path | None, require_authority: bool) -> dict[str, Any]:
    return {
        "support_import_split": support_import_split_proof(authority, require_authority),
        "mutation_gate": mutation_gate_proof(),
        "transaction": publication_transaction_proof(),
        "network_free": True,
        "live_mutation": False,
    }
