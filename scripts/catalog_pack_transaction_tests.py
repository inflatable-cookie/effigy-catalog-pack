"""In-memory first-publication transaction proofs. Ordinary QA stays write-free."""

from __future__ import annotations

from catalog_pack_policy import version_admitted
from catalog_pack_registry import FakeRegistry
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


def _run(adapter: FakeRegistry, phase: str, **extra: Any) -> dict[str, Any]:
    return run_publication(
        authority=None,
        adapter=adapter,
        mutate=True,
        phase=phase,
        release_getter=_release_fixture,
        support_probe=lambda: _support_fixture(),
        **extra,
    )


def _operator_public(adapter: FakeRegistry) -> None:
    adapter.visibility = "public"
    adapter.repository = PACK_GITHUB_REPOSITORY


def _first_publication(adapter: FakeRegistry | None = None) -> tuple[FakeRegistry, dict[str, Any], dict[str, Any]]:
    adapter = adapter or FakeRegistry()
    fd, raw_output = tempfile.mkstemp(prefix="catalog-pack-github-output-")
    os.close(fd)
    output = Path(raw_output)
    try:
        created = _run(adapter, "version", runtime_env={"GITHUB_OUTPUT": str(output)})
        emitted = output.read_text(encoding="utf-8")
    finally:
        output.unlink(missing_ok=True)
    require("manifest_digest=" in emitted, "version phase did not emit the manifest digest")
    require("support_commit=" in emitted, "version phase did not emit the support commit")
    require(adapter.inspect_stable() is None, "version publish moved absent stable")
    _operator_public(adapter)
    expected = created["support"]
    _run(adapter, "finalize-preflight", expected_support=expected)
    adapter.attest(created["candidate_digest"], OCI_REPOSITORY)
    finalized = _run(adapter, "finalize", expected_support=expected)
    return adapter, created, finalized


def absent_stable_model_proof() -> dict[str, Any]:
    digest = "sha256:" + "a" * 64
    model = FakeRegistry(version_digest=digest, stable_digest=None)
    require(model.inspect_stable() is None, "model did not record absent stable")
    model.untag(STABLE_TAG)
    require(model.inspect_stable() is None, "model rollback-to-absence mutated the channel")
    require(model.version_digest == digest, "model rollback-to-absence deleted the version digest")
    live_src = (ROOT / "scripts" / "catalog_pack_live.py").read_text()
    tx_src = (ROOT / "scripts" / "catalog_pack_transaction.py").read_text()
    phase_src = (ROOT / "scripts" / "catalog_pack_phases.py").read_text()
    wf_src = (ROOT / ".github" / "workflows" / "publication.yml").read_text()
    combined = tx_src + phase_src
    require("manifest delete" not in live_src, "live adapter still deletes manifests")
    require("untag" not in live_src, "live adapter still exposes untag")
    require("set_public" not in live_src, "live adapter still mutates visibility")
    require("PATCH" not in live_src, "live adapter still PATCHes package visibility")
    require("users/inflatable-cookie" not in live_src, "live adapter still uses the user package route")
    require("PACKAGE_METADATA_PATH" in live_src, "live adapter does not GET the org package route")
    require(".untag(" not in combined, "transaction still calls untag")
    require("set_public" not in combined, "transaction still sets visibility")
    require("PATCH" not in wf_src, "publication workflow still PATCHes visibility")
    return {"model_only_absent_rollback": True, "live_manifest_delete": False}


def publication_transaction_proof() -> dict[str, Any]:
    entry = (ROOT / "scripts" / "catalog_pack.py").read_text()
    prefix, _, _ = entry.partition("def publish_command")
    require("catalog_pack_live" not in prefix, "ordinary catalog_pack entry imports the live registry")
    require(not version_admitted("0.13.0", ">=0.12, <0.13"), "current pack range must reject 0.13.0")

    first, created, finalized = _first_publication()
    kinds = [kind for kind, _ in first.writes]
    require(kinds[0] == "package-version", "first write was not the version package")
    require("visibility" not in kinds, "transaction PATCHed package visibility")
    require(kinds.index("attestation") < kinds.index("stable"), "stable moved before attestation")
    require(kinds.count("stable") == 1, "absent first-publication stable did not move once")
    require(finalized["rollback_exercised"] is False, "absent stable used a live rollback delete")
    require(finalized["absent_stable_recorded"] is True, "absent stable was not recorded")
    require(first.inspect_version("v1.0.0") == created["candidate_digest"], "version pointer drifted")
    require(first.inspect_stable() == created["candidate_digest"], "stable did not finish on the candidate")
    require(first.anonymous_pulls >= 1, "anonymous pull was skipped")
    require(first.refetches == 1, "finalize did not refresh Effigy support authority")

    retry = FakeRegistry(
        version_digest=created["candidate_digest"],
        visibility="public",
        repository=PACK_GITHUB_REPOSITORY,
    )
    retried = _run(retry, "version")
    require(retried["version_state"] == "same-digest", "same-digest retry was not recognized")
    require(retried["push_attempted"] is False, "same-digest retry attempted a package overwrite")
    require(retry.inspect_stable() is None, "same-digest version retry moved stable")

    colliding = FakeRegistry(version_digest="sha256:" + "c" * 64)
    try:
        _run(colliding, "version")
    except CheckFailure as error:
        require("collision rejected" in str(error), "different-digest collision failed for the wrong reason")
    else:
        fail("different-digest collision was not rejected")
    require(colliding.writes == [], "collision mutated remote state")

    stale_values = [_support_fixture("a" * 40), _support_fixture("d" * 40)]

    def stale_probe() -> dict[str, Any]:
        return stale_values.pop(0)

    stale = FakeRegistry(
        version_digest=created["candidate_digest"],
        visibility="public",
        repository=PACK_GITHUB_REPOSITORY,
        attested={created["candidate_digest"]},
    )
    try:
        run_publication(
            authority=None,
            adapter=stale,
            mutate=True,
            phase="finalize",
            release_getter=_release_fixture,
            support_probe=stale_probe,
            expected_support={"commit": "a" * 40, "blob": "b" * 40},
        )
    except CheckFailure as error:
        require("support commit drifted" in str(error), "stale support failed for the wrong reason")
    else:
        fail("stale support input was not rejected")
    require("stable" not in [kind for kind, _ in stale.writes], "stale support moved stable")

    private = FakeRegistry()
    _run(private, "version")
    try:
        _run(private, "finalize-preflight", expected_support=created["support"])
    except CheckFailure as error:
        require("package is not public" in str(error), str(error))
    else:
        fail("private package was treated as anonymously readable")
    require("stable" not in [kind for kind, _ in private.writes], "private package moved stable")

    unattested = FakeRegistry()
    _run(unattested, "version")
    _operator_public(unattested)
    _run(unattested, "finalize-preflight", expected_support=created["support"])
    try:
        _run(unattested, "finalize", expected_support=created["support"])
    except CheckFailure as error:
        require("no digest-bound attestation" in str(error), str(error))
    else:
        fail("unattested subject was allowed to continue")
    require("stable" not in [kind for kind, _ in unattested.writes], "unattested subject moved stable")

    previous = "sha256:" + "e" * 64
    retag = FakeRegistry(
        version_digest=created["candidate_digest"],
        stable_digest=previous,
        visibility="public",
        repository=PACK_GITHUB_REPOSITORY,
        attested={created["candidate_digest"]},
    )
    moved = _run(retag, "finalize", expected_support=created["support"])
    require(moved["rollback_exercised"] is True, "existing stable skipped live retag rollback")
    require([kind for kind, _ in retag.writes] == ["stable", "stable"], "retag rollback write set drifted")
    require(retag.inspect_stable() == created["candidate_digest"], "retag rollback did not restore the candidate")
    require(retag.inspect_version("v1.0.0") == created["candidate_digest"], "retag rollback moved the version pointer")

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
            phase="version",
            live_gate_env={},
            release_getter=_release_fixture,
            support_probe=lambda: _support_fixture(),
        )
    except CheckFailure as error:
        require("GitHub Actions" in str(error), str(error))
    else:
        fail("empty live gate permitted mutation")

    model = absent_stable_model_proof()
    return {
        "absent_creates": True,
        "same_digest_reuses": True,
        "collision_rejected": True,
        "stale_support_rejected": True,
        "private_rejected": True,
        "unattested_rejected": True,
        "plan_is_read_only": True,
        "live_gate_fail_closed": True,
        "absent_stable_moves_once": True,
        "live_retag_when_previous_exists": True,
        "candidate_digest": created["candidate_digest"],
        "write_order": kinds,
        **model,
    }
