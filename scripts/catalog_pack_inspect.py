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
_ORAS_DESCRIPTOR_ABSENT = re.compile(r"failed to fetch descriptor:.*\bnot found\b")
_ORAS_FIND_ABSENT = re.compile(r'failed to find "[^"]+":.*\bnot found\b')
_DIGEST_PARTS = re.compile(r"^([a-z0-9]+):([0-9a-f]+)$")


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
    if _ORAS_DESCRIPTOR_ABSENT.search(text):
        return "absent"
    if _ORAS_FIND_ABSENT.search(text):
        return "absent"
    return "error"


def require_verified_attestation_json(payload_text: str, digest: str) -> None:
    """Require a non-empty JSON array whose statement subjects name the exact digest map."""

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        fail(f"digest-bound attestation verify did not return JSON: {payload_text}")
    require(isinstance(payload, list), "attestation verify JSON is not an array")
    require(payload, "attestation verify returned no attestations")
    require(all(isinstance(item, dict) for item in payload), "attestation verify JSON entries are not objects")
    parts = _DIGEST_PARTS.fullmatch(digest)
    require(parts is not None, f"attestation subject digest is not algorithm:hex: {digest}")
    algorithm, digest_hex = parts.group(1), parts.group(2)
    matched = False
    for item in payload:
        for subject in _statement_subjects(item):
            if _subject_digest_matches(subject, algorithm, digest_hex):
                matched = True
    require(matched, f"attestation verify JSON has no subject digest {algorithm}:{digest_hex}")


def _statement_subjects(entry: dict[str, Any]) -> list[Any]:
    verification = entry.get("verificationResult")
    require(isinstance(verification, dict), "attestation verify JSON lacks verificationResult")
    statement = verification.get("statement")
    require(isinstance(statement, dict), "attestation verify JSON lacks verificationResult.statement")
    subject = statement.get("subject")
    if isinstance(subject, dict):
        return [subject]
    require(isinstance(subject, list) and subject, "attestation statement has no subjects")
    return subject


def _subject_digest_matches(subject: Any, algorithm: str, digest_hex: str) -> bool:
    if not isinstance(subject, dict):
        return False
    digest_map = subject.get("digest")
    if not isinstance(digest_map, dict):
        return False
    observed = digest_map.get(algorithm)
    return isinstance(observed, str) and observed.lower() == digest_hex
