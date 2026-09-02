"""Fail-closed classification for remote inspect and attestation verify results."""

from __future__ import annotations

from catalog_pack_shared import *

_AUTH_MARKERS = (
    "unauthorized",
    "authentication required",
    "access denied",
    "permission denied",
    "forbidden",
)
_LOCAL_FAILURE_MARKERS = (
    "executable file not found",
    "command not found",
    "docker-credential",
    "no such file or directory",
    "not found in $path",
    "not found in path",
)
_REGISTRY_ABSENT_MARKERS = (
    "manifest unknown",
    "name unknown",
    "unknown to registry",
    "manifest_unknown",
    "name_unknown",
)
_AUTH_STATUS = re.compile(r"\b(401|403)\b")
_ABSENT_STATUS = re.compile(r"\b404\b")
_REGISTRY_NOT_FOUND = re.compile(r": not found(?:\s|$)")


def classify_registry_inspect(returncode: int, stdout: str, stderr: str) -> str:
    """Classify a remote inspect. Only a proved registry miss is absent."""

    if returncode == 0:
        return "present"
    text = f"{stderr}\n{stdout}".lower()
    if any(marker in text for marker in _AUTH_MARKERS) or _AUTH_STATUS.search(text):
        return "error"
    if any(marker in text for marker in _LOCAL_FAILURE_MARKERS):
        return "error"
    if any(marker in text for marker in _REGISTRY_ABSENT_MARKERS) or _ABSENT_STATUS.search(text):
        return "absent"
    if _REGISTRY_NOT_FOUND.search(text):
        return "absent"
    return "error"


def require_verified_attestation_json(payload_text: str, digest: str) -> None:
    """Require a non-empty JSON array of verified attestations for the exact digest."""

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        fail(f"digest-bound attestation verify did not return JSON: {payload_text}")
    require(isinstance(payload, list), "attestation verify JSON is not an array")
    require(payload, "attestation verify returned no attestations")
    require(all(isinstance(item, dict) for item in payload), "attestation verify JSON entries are not objects")
    require(digest in json.dumps(payload), f"attestation verify JSON does not name digest {digest}")
