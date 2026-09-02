"""Injected command-runner proofs for the live publication adapter and workflow wiring."""

from __future__ import annotations

from typing import Any, Mapping

from catalog_pack_live import LiveRegistry
from catalog_pack_shared import *


def _proc(code: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(args=[], returncode=code, stdout=stdout.encode(), stderr=stderr.encode())


def _binary(call: dict[str, Any], name: str) -> bool:
    argv = call["argv"]
    return bool(argv) and Path(argv[0]).name == name


class ScriptedRunner:
    def __init__(self, handlers: list[Any]) -> None:
        self.calls: list[dict[str, Any]] = []
        self.handlers = list(handlers)

    def __call__(
        self,
        argv: list[str],
        *,
        env: Mapping[str, str] | None = None,
        cwd: str | Path | None = None,
        input: bytes | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[bytes]:
        recorded = {
            "argv": [str(part) for part in argv],
            "env": dict(env or {}),
            "cwd": None if cwd is None else str(cwd),
            "input": input,
        }
        self.calls.append(recorded)
        for handler in self.handlers:
            result = handler(recorded)
            if result is None:
                continue
            if check and result.returncode != 0:
                detail = decode_output(result.stderr) or decode_output(result.stdout)
                fail(f"command failed ({result.returncode}): {' '.join(argv)}\n{detail}")
            return result
        fail(f"unexpected command: {argv}")
        raise AssertionError


def _when(predicate: Any, result: subprocess.CompletedProcess[bytes]) -> Any:
    def handler(call: dict[str, Any]) -> subprocess.CompletedProcess[bytes] | None:
        if predicate(call):
            return result
        return None

    return handler


def _gate_env() -> dict[str, str]:
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REPOSITORY": PACK_GITHUB_REPOSITORY,
        "GITHUB_ENVIRONMENT": PUBLICATION_ENVIRONMENT,
        PUBLICATION_MUTATE_ENV: "1",
        "GITHUB_TOKEN": "test-token",
        "GH_TOKEN": "test-token",
        "GITHUB_ACTOR": "tester",
        "PATH": "/usr/bin",
        "LANG": "C",
    }


def _live(runner: ScriptedRunner) -> LiveRegistry:
    return LiveRegistry(
        _gate_env(),
        runner=runner,
        which=lambda name: f"/usr/bin/{name}",
    )


def inspect_runner_proof() -> dict[str, Any]:
    absent = ScriptedRunner(
        [
            _when(lambda call: _binary(call, "oras") and "login" in call["argv"], _proc()),
            _when(
                lambda call: _binary(call, "oras") and "fetch" in call["argv"],
                _proc(1, stderr="Error: failed to fetch descriptor: not found"),
            ),
        ]
    )
    require(_live(absent).inspect_stable() is None, "proved not-found did not return None")
    fetch = [call for call in absent.calls if _binary(call, "oras") and "fetch" in call["argv"]][0]
    require(fetch["env"].get("GITHUB_TOKEN") == "test-token", "inspect did not receive GITHUB_TOKEN")
    require(f"{OCI_REPOSITORY}:{STABLE_TAG}" in fetch["argv"], "inspect argv lost the stable reference")
    live_miss = ScriptedRunner(
        [
            _when(lambda call: _binary(call, "oras") and "login" in call["argv"], _proc()),
            _when(
                lambda call: _binary(call, "oras") and "fetch" in call["argv"],
                _proc(
                    1,
                    stderr=(
                        "Error response from registry: failed to find "
                        f'"{OCI_REPOSITORY}:v1.0.0": {OCI_REPOSITORY}:v1.0.0: not found'
                    ),
                ),
            ),
        ]
    )
    require(_live(live_miss).inspect_stable() is None, "live ORAS 1.3.3 GHCR miss did not return None")

    denied = ScriptedRunner(
        [
            _when(lambda call: _binary(call, "oras") and "login" in call["argv"], _proc()),
            _when(
                lambda call: _binary(call, "oras") and "fetch" in call["argv"],
                _proc(1, stderr="Error: unauthorized: authentication required"),
            ),
        ]
    )
    try:
        _live(denied).inspect_version("v1.0.1")
    except CheckFailure as error:
        require("registry inspect failed" in str(error), str(error))
    else:
        fail("unauthorized inspect was treated as absent")

    timeout = ScriptedRunner(
        [
            _when(lambda call: _binary(call, "oras") and "login" in call["argv"], _proc()),
            _when(
                lambda call: _binary(call, "oras") and "fetch" in call["argv"],
                _proc(1, stderr="Error: context deadline exceeded"),
            ),
        ]
    )
    try:
        _live(timeout).inspect_stable()
    except CheckFailure as error:
        require("registry inspect failed" in str(error), str(error))
    else:
        fail("timeout inspect was treated as absent")
    return {"argv_recorded": True, "token_wired": True}


def package_and_stable_runner_proof() -> dict[str, Any]:
    public = json.dumps(
        {
            "name": "effigy-catalog-pack",
            "visibility": "public",
            "repository": {"full_name": PACK_GITHUB_REPOSITORY},
        }
    )
    runner = ScriptedRunner(
        [
            _when(lambda call: _binary(call, "oras") and "login" in call["argv"], _proc()),
            _when(
                lambda call: _binary(call, "gh") and call["argv"][1:4] == ["api", "--method", "GET"],
                _proc(0, stdout=public),
            ),
            _when(lambda call: _binary(call, "oras") and "tag" in call["argv"], _proc()),
            _when(
                lambda call: call["argv"][:1] == ["git"] or (len(call["argv"]) > 1 and call["argv"][0] == "git"),
                _proc(),
            ),
            _when(lambda call: _binary(call, "git"), _proc()),
        ]
    )
    adapter = _live(runner)
    state = adapter.package_state()
    require(state["visibility"] == "public", "org package GET did not report public visibility")
    require(state["repository"] == PACK_GITHUB_REPOSITORY, "org package GET lost repository linkage")
    get_calls = [call for call in runner.calls if _binary(call, "gh")]
    require(get_calls, "package metadata GET was not issued")
    require(PACKAGE_METADATA_PATH in get_calls[0]["argv"], "package GET used the wrong route")
    require("GET" in get_calls[0]["argv"], "package metadata was not a GET")
    require(not any("PATCH" in call["argv"] for call in runner.calls), "live adapter issued a visibility PATCH")
    require("users/inflatable-cookie" not in " ".join(get_calls[0]["argv"]), "package GET still used the user route")

    adapter.tag_digest("sha256:" + "a" * 64, STABLE_TAG)
    tag_calls = [call for call in runner.calls if _binary(call, "oras") and "tag" in call["argv"]]
    require(len(tag_calls) == 1, "stable move was not a single oras tag")
    require("manifest" not in tag_calls[0]["argv"], "stable move used a manifest subcommand")
    require("delete" not in tag_calls[0]["argv"], "stable move deleted a manifest")

    adapter.refresh_support_authority(Path("/tmp/effigy-authority"))
    fetch = [call for call in runner.calls if _binary(call, "git") and "fetch" in call["argv"]]
    require(fetch, "support refresh did not fetch")
    require("origin" in fetch[0]["argv"] and "main" in "".join(fetch[0]["argv"]), "support refresh did not re-resolve origin/main")
    require(fetch[0]["argv"][fetch[0]["argv"].index("-C") + 1] == "/tmp/effigy-authority", "support refresh used the wrong checkout")
    require(not hasattr(adapter, "untag"), "live adapter still exposes untag")
    require(not hasattr(adapter, "set_public"), "live adapter still exposes set_public")
    require(not hasattr(adapter, "attest"), "live adapter still attests in-process")
    return {"org_package_get": True, "stable_is_retag": True, "support_refetch": True}


def workflow_wiring_proof() -> dict[str, Any]:
    publication = (ROOT / ".github" / "workflows" / "publication.yml").read_text()
    hosted = json.loads(HOSTED_EVIDENCE_PATH.read_text(encoding="utf-8"))
    require(
        "group: catalog-pack-publication-${{ inputs.source_tag }}" in publication,
        "publication is not serialized by source tag",
    )
    require("cancel-in-progress: false" in publication, "publication concurrency cancels in-progress runs")
    require("GITHUB_TOKEN: ${{ github.token }}" in publication, "publication does not export github.token as GITHUB_TOKEN")
    require("GH_TOKEN: ${{ github.token }}" in publication, "publication does not export github.token as GH_TOKEN")
    require(
        f"GITHUB_ENVIRONMENT: {PUBLICATION_ENVIRONMENT}" in publication,
        "publication does not set GITHUB_ENVIRONMENT explicitly",
    )
    require("--phase version" in publication, "publication is missing the version phase")
    require("--phase finalize-preflight" in publication, "publication is missing finalize-preflight")
    require("--phase finalize" in publication, "publication is missing the finalize phase")
    require("needs: publish" in publication, "finalize is not serialized after publish")
    require(
        f"uses: actions/attest@{ATTEST_ACTION_COMMIT}" in publication,
        "finalize does not use the pinned actions/attest action",
    )
    require("push-to-registry: true" in publication, "pinned attest action does not push to the registry")
    require("dist/index.js" not in publication, "publication still executes actions/attest out of band")
    require("package settings" in publication, "publication does not document the operator visibility checkpoint")
    require("not refs/tags/v1.0.1" in publication, "publication does not name the canonical source-tag spelling")
    require(
        hosted["actions"]["selected_actions"]["patterns_allowed"]
        == [f"actions/checkout@{CHECKOUT_ACTION_SHA}"],
        "this PR changed selected-actions provider policy",
    )
    from catalog_pack_publication import actual_source_identity, publication_concurrency_group

    require(
        publication_concurrency_group("v1.0.1", "1.0.1") == "catalog-pack-publication-v1.0.1",
        "canonical concurrency key drifted",
    )
    try:
        publication_concurrency_group("refs/tags/v1.0.1", "1.0.1")
    except CheckFailure as error:
        require("canonical" in str(error), str(error))
    else:
        fail("refs/tags alias was accepted as a concurrency key")
    try:
        actual_source_identity("refs/tags/v1.0.1", "a" * 40, "1.0.1")
    except CheckFailure as error:
        require("canonical" in str(error), str(error))
    else:
        fail("refs/tags alias was accepted as source identity")
    try:
        publication_concurrency_group("v1.0.0", "1.0.1")
    except CheckFailure as error:
        require("canonical" in str(error), str(error))
    else:
        fail("the preserved v1.0.0 identity was accepted after the recovery bump")
    require(
        "catalog-pack-publication-refs/tags/v1.0.1" != publication_concurrency_group("v1.0.1", "1.0.1"),
        "raw alias would not have been a distinct mutation lane",
    )
    return {
        "concurrency_keyed_by_source_tag": True,
        "canonical_source_tag_only": True,
        "token_and_environment_exported": True,
        "finalize_uses_pinned_attest": True,
        "selected_actions_unchanged": True,
    }


def live_seam_proof() -> dict[str, Any]:
    from catalog_pack_inspect_tests import classify_inspect_proof, verify_attestation_proof

    return {
        "classify": classify_inspect_proof(),
        "inspect": inspect_runner_proof(),
        "package_and_stable": package_and_stable_runner_proof(),
        "attestation": verify_attestation_proof(),
        "workflow": workflow_wiring_proof(),
        "network_free": True,
    }
