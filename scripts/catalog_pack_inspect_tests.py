"""Inspect classification and structured attestation-verify proofs."""

from __future__ import annotations

from catalog_pack_live import classify_registry_inspect
from catalog_pack_live_tests import ScriptedRunner, _binary, _live, _proc, _when
from catalog_pack_shared import *


def classify_inspect_proof() -> dict[str, Any]:
    require(classify_registry_inspect(0, '{"digest":"sha256:abc"}', "") == "present", "zero status was not present")
    require(
        classify_registry_inspect(1, "", "Error: failed to fetch descriptor: not found") == "absent",
        "not-found was not classified absent",
    )
    require(
        classify_registry_inspect(1, "", "Error: manifest unknown") == "absent",
        "manifest unknown was not classified absent",
    )
    require(
        classify_registry_inspect(1, "", "Error: unauthorized: authentication required") == "error",
        "unauthorized was not classified as failure",
    )
    require(
        classify_registry_inspect(1, "", "denied: 401 Unauthorized") == "error",
        "HTTP 401 was not classified as failure",
    )
    require(
        classify_registry_inspect(1, "", "Error: context deadline exceeded") == "error",
        "timeout was treated as absent",
    )
    require(
        classify_registry_inspect(1, "", "dial tcp: connection refused") == "error",
        "network failure was treated as absent",
    )
    require(
        classify_registry_inspect(1, "", "unauthorized: requested access to the resource is denied: 404") == "error",
        "auth failure with 404 was treated as absent",
    )
    require(
        classify_registry_inspect(1, "", "exec: docker-credential-pass: executable file not found in $PATH") == "error",
        "local credential helper miss was treated as registry absence",
    )
    require(
        classify_registry_inspect(1, "", "oras: command not found") == "error",
        "missing oras binary was treated as registry absence",
    )
    return {"registry_miss_absent": True, "auth_and_network_fail_closed": True, "local_not_found_fail_closed": True}


def verify_attestation_proof() -> dict[str, Any]:
    digest = "sha256:" + "a" * 64
    verified = json.dumps([{"verificationResult": {"isValid": True, "digest": digest}}])

    def attestation_verify(call: dict[str, Any]) -> bool:
        return _binary(call, "gh") and "attestation" in call["argv"] and "verify" in call["argv"]

    good = ScriptedRunner(
        [
            _when(lambda call: _binary(call, "oras") and "login" in call["argv"], _proc()),
            _when(attestation_verify, _proc(0, stdout=verified)),
        ]
    )
    _live(good).verify_attestation(digest)
    verify = [call for call in good.calls if attestation_verify(call)][0]
    require("--format" in verify["argv"] and "json" in verify["argv"], "attestation verify did not request JSON")
    require(f"oci://{OCI_REPOSITORY}@{digest}" in verify["argv"], "attestation verify lost the subject digest")

    empty = ScriptedRunner(
        [
            _when(lambda call: _binary(call, "oras") and "login" in call["argv"], _proc()),
            _when(attestation_verify, _proc(0, stdout="[]")),
        ]
    )
    try:
        _live(empty).verify_attestation(digest)
    except CheckFailure as error:
        require("returned no attestations" in str(error), str(error))
    else:
        fail("empty JSON attestation verify was accepted")

    nomatch = ScriptedRunner(
        [
            _when(lambda call: _binary(call, "oras") and "login" in call["argv"], _proc()),
            _when(attestation_verify, _proc(0, stdout="No attestations found")),
        ]
    )
    try:
        _live(nomatch).verify_attestation(digest)
    except CheckFailure as error:
        require("did not return JSON" in str(error), str(error))
    else:
        fail("zero-exit no-match attestation verify was accepted")

    nonzero = ScriptedRunner(
        [
            _when(lambda call: _binary(call, "oras") and "login" in call["argv"], _proc()),
            _when(attestation_verify, _proc(1, stderr="verify failed")),
            _when(lambda call: _binary(call, "gh") and "api" in call["argv"], _proc(1, stderr="missing")),
        ]
    )
    try:
        _live(nonzero).verify_attestation(digest)
    except CheckFailure as error:
        require("did not verify" in str(error), str(error))
    else:
        fail("nonzero attestation verify was accepted")
    return {"structured_json_required": True, "zero_exit_no_match_rejected": True, "nonzero_rejected": True}
