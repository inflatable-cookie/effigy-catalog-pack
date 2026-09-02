"""Generate and verify a generated-only Effigy baseline proposal.

The proposal path consumes an already published OCI artifact by its immutable
manifest digest.  Its local preparation seam is deliberately independent of
GitHub: it verifies the pulled bytes, composes the typed Effigy lock, and
checks the exact generated-only diff before a hosted workflow is allowed to
push a branch or open a pull request.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from catalog_pack_inspect import require_verified_attestation_json
from catalog_pack_oci import read_layout_manifest, sha256_digest, tree_snapshot, validate_source_identity
from catalog_pack_proposal_effigy import PROPOSAL_VERIFIER_HARNESS, effigy_verifier_command, run_effigy_verifier
from catalog_pack_proposal_token import app_token_request, mint_installation_token, validate_app_token_response
from catalog_pack_shared import *


EFFIGY_SNAPSHOT_ROOT = Path(PROPOSAL_BASELINE_SNAPSHOT)
EFFIGY_LOCK_PATH = Path(PROPOSAL_BASELINE_LOCK)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_OBJECT_ID_RE = re.compile(r"^[0-9a-f]{40}$")
_EVIDENCE_RE = re.compile(
    rf"^docs/logs/\d{{4}}-\d{{2}}/\d{{2}}-\d{{6}}-{re.escape(PROPOSAL_EVIDENCE_PREFIX)}\.md$"
)


def require_sha256_digest(value: str, label: str = "artifact digest") -> str:
    require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"{label} must be a lowercase sha256 digest")
    return value


def proposal_branch(digest: str) -> str:
    """Return the deterministic, non-overwriting branch name for a digest."""

    value = require_sha256_digest(digest).split(":", 1)[1]
    return f"catalog-pack/baseline-{value}"


def proposal_evidence_path(source_created: str) -> Path:
    return _evidence_path(source_created)


def _evidence_path(source_created: str) -> Path:
    """Format the dated evidence path without allowing Path join ambiguity."""

    require(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", source_created) is not None,
        "artifact source_created is not UTC RFC3339 with whole seconds",
    )
    try:
        moment = datetime.strptime(source_created, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        fail(f"artifact source_created is not a valid UTC timestamp: {error}")
    return Path("docs/logs") / moment.strftime("%Y-%m") / (
        moment.strftime("%d-%H%M%S-") + PROPOSAL_EVIDENCE_PREFIX + ".md"
    )


def validate_proposal_paths(paths: list[str], evidence_path: str | None = None) -> dict[str, Any]:
    """Enforce the only paths a proposal commit may change."""

    require(paths, "proposal diff is empty")
    normalized: list[str] = []
    for raw in paths:
        require(isinstance(raw, str) and raw, "proposal diff contains an empty path")
        path = Path(raw)
        require(not path.is_absolute(), f"proposal diff path is absolute: {raw}")
        require(".." not in path.parts and "." not in path.parts, f"proposal diff path traverses: {raw}")
        require(path.as_posix() == raw, f"proposal diff path is not canonical: {raw}")
        normalized.append(raw)
    require(len(set(normalized)) == len(normalized), "proposal diff contains duplicate paths")

    allowed_snapshot = PROPOSAL_BASELINE_SNAPSHOT + "/"
    snapshot_paths = [path for path in normalized if path.startswith(allowed_snapshot)]
    require(snapshot_paths, "proposal diff does not change the generated catalog snapshot")
    require(PROPOSAL_BASELINE_LOCK in normalized, "proposal diff does not change the typed baseline lock")

    evidence = [path for path in normalized if _EVIDENCE_RE.fullmatch(path)]
    require(len(evidence) == 1, "proposal diff must contain exactly one dated baseline evidence file")
    if evidence_path is not None:
        require(evidence[0] == evidence_path, f"proposal evidence path is {evidence[0]}, expected {evidence_path}")

    unexpected = [
        path
        for path in normalized
        if path not in snapshot_paths and path != PROPOSAL_BASELINE_LOCK and path not in evidence
    ]
    require(not unexpected, f"proposal diff contains non-generated paths: {unexpected}")
    return {
        "allowed": True,
        "snapshot_paths": sorted(snapshot_paths),
        "lock_path": PROPOSAL_BASELINE_LOCK,
        "evidence_path": evidence[0],
        "path_count": len(normalized),
    }


def _safe_source_identity(annotations: Mapping[str, Any], pack_version: str) -> dict[str, str]:
    required = {
        "source_commit": annotations.get("io.effigy.catalog.pack.source-commit"),
        "source_tag": annotations.get("io.effigy.catalog.pack.source-tag"),
        "tag_object": annotations.get("io.effigy.catalog.pack.source-tag-object"),
        "source_created": annotations.get("org.opencontainers.image.created"),
    }
    for name, value in required.items():
        require(isinstance(value, str) and value, f"OCI artifact annotation lacks {name}")
    source_commit = required["source_commit"]
    tag_object = required["tag_object"]
    require(_OBJECT_ID_RE.fullmatch(source_commit) is not None, "artifact source commit is not a full object id")
    require(_OBJECT_ID_RE.fullmatch(tag_object) is not None, "artifact source tag object is not a full object id")
    identity = {
        "source_commit": source_commit,
        "source_created": required["source_created"],
        "source_tag": required["source_tag"],
        "tag_object": tag_object,
        "peeled_commit": source_commit,
        "source_ref": source_commit,
    }
    require(identity["source_tag"] == f"v{pack_version}", "artifact source tag does not match pack version")
    validate_source_identity(identity, pack_version)
    return identity


def verify_pulled_artifact(
    artifact_root: Path,
    manifest_path: Path,
    artifact_digest: str,
    descriptor_path: Path | None = None,
) -> dict[str, Any]:
    """Verify a digest-addressed pull before it can feed an Effigy proposal."""

    digest = require_sha256_digest(artifact_digest)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        fail(f"pulled artifact manifest is invalid: {error}")
    require(isinstance(manifest, dict), "pulled artifact manifest is not an object")

    if descriptor_path is not None:
        try:
            descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            fail(f"pulled artifact descriptor is invalid: {error}")
        require(isinstance(descriptor, dict), "pulled artifact descriptor is not an object")
        require(descriptor.get("digest") == digest, "registry descriptor digest differs from requested artifact digest")
        require(descriptor.get("mediaType") == OCI_MANIFEST_MEDIA_TYPE, "registry descriptor media type changed")
    if manifest.get("digest") is not None:
        require(manifest.get("digest") == digest, "artifact manifest digest differs from requested artifact digest")

    require(manifest.get("schemaVersion") == 2, "proposal artifact manifest schema version is not 2")
    require(manifest.get("mediaType") == OCI_MANIFEST_MEDIA_TYPE, "proposal artifact manifest media type changed")
    require(manifest.get("artifactType") == OCI_ARTIFACT_TYPE, "proposal artifact type changed")
    annotations = manifest.get("annotations")
    require(isinstance(annotations, dict), "proposal artifact annotations are missing")

    facts = validate_pack_tree(artifact_root)
    require(annotations.get("io.effigy.catalog.pack.content-id") == facts["content_id"], "artifact content identity differs from its bytes")
    require(annotations.get("org.opencontainers.image.source") == SOURCE_URL, "artifact source annotation changed")
    require(annotations.get("org.opencontainers.image.revision") == annotations.get("io.effigy.catalog.pack.source-commit"), "artifact revision is not its peeled source commit")
    require(annotations.get("org.opencontainers.image.version") == facts["pack_version"], "artifact version annotation differs from pack.toml")
    identity = _safe_source_identity(annotations, facts["pack_version"])

    config = manifest.get("config")
    require(isinstance(config, dict), "proposal artifact config is missing")
    require(config.get("mediaType") == OCI_EMPTY_CONFIG_MEDIA_TYPE, "proposal artifact config media type changed")
    require(config.get("digest") == sha256_digest(b"{}"), "proposal artifact config is not the fixed empty config")
    require(config.get("size") == 2 and config.get("data") == "e30=", "proposal artifact config bytes changed")

    files, _ = collect_tree(artifact_root)
    layers = manifest.get("layers")
    require(isinstance(layers, list) and len(layers) == len(files), "proposal artifact layer inventory count changed")
    titles: list[str] = []
    for layer in layers:
        require(isinstance(layer, dict), "proposal artifact layer is not an object")
        layer_annotations = layer.get("annotations")
        require(isinstance(layer_annotations, dict), "proposal artifact layer annotations are missing")
        title = layer_annotations.get("org.opencontainers.image.title")
        require(isinstance(title, str), "proposal artifact layer lacks a path title")
        path = Path(title)
        require(not path.is_absolute() and ".." not in path.parts and "." not in path.parts and path.as_posix() == title, f"unsafe proposal artifact layer title: {title!r}")
        require(title in files and title not in titles, f"proposal artifact layer is outside or duplicates the pack inventory: {title}")
        data = (artifact_root / title).read_bytes()
        require(layer.get("digest") == sha256_digest(data), f"proposal artifact layer digest differs for {title}")
        require(layer.get("size") == len(data), f"proposal artifact layer size differs for {title}")
        require(layer.get("mediaType") == OCI_FILE_LAYER_MEDIA_TYPE, f"proposal artifact layer media type changed for {title}")
        titles.append(title)
    require(titles == sorted(files), "proposal artifact layer path order is not deterministic")

    return {
        "artifact_verified": True,
        "manifest_digest": digest,
        "content_id": facts["content_id"],
        "pack_id": facts["pack_id"],
        "pack_version": facts["pack_version"],
        "file_count": facts["file_count"],
        "byte_count": facts["byte_count"],
        "source_identity": identity,
        "network_access": False,
    }


def render_baseline_lock(facts: Mapping[str, Any], identity: Mapping[str, str], artifact_digest: str) -> bytes:
    """Render the exact lock representation consumed by Effigy's Rust parser."""

    digest = require_sha256_digest(artifact_digest)
    require(identity.get("source_repository", PACK_GITHUB_REPOSITORY) == PACK_GITHUB_REPOSITORY, "baseline source repository is not canonical")
    source_commit = str(identity.get("source_commit", ""))
    source_created = str(identity.get("source_created", ""))
    source_tag = str(identity.get("source_tag", ""))
    tag_object = str(identity.get("tag_object", ""))
    require(_OBJECT_ID_RE.fullmatch(source_commit) is not None, "baseline source commit is not a full object id")
    require(_OBJECT_ID_RE.fullmatch(tag_object) is not None, "baseline source tag object is not a full object id")
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", source_created) is not None, "baseline source time is not UTC RFC3339")
    require(source_tag == f"v{facts['pack_version']}", "baseline source tag does not match pack version")
    require(identity.get("peeled_commit") == source_commit, "baseline peeled commit differs from source commit")
    return (
        "# Effigy compiled catalog-pack baseline lock.\n"
        "#\n"
        "# GENERATED FILE — DO NOT HAND-EDIT.\n"
        "#\n"
        "# The generated catalog snapshot and this typed lock are produced from\n"
        "# one verified digest-addressed catalog-pack artifact. A hand edit is\n"
        "# rejected by Effigy's offline baseline verifier.\n"
        "#\n"
        "# OCI manifest digest and unpacked content identity are distinct facts.\n"
        "schema_version = 1\n"
        "\n"
        "[baseline]\n"
        f'source_repository = "{PACK_GITHUB_REPOSITORY}"\n'
        f'source_commit = "{source_commit}"\n'
        f'source_created = "{source_created}"\n'
        f'source_tag = "{source_tag}"\n'
        f'source_tag_object = "{tag_object}"\n'
        f'pack_id = "{facts["pack_id"]}"\n'
        f'pack_version = "{facts["pack_version"]}"\n'
        "\n"
        "[identities]\n"
        f'oci_manifest_digest = "{digest}"\n'
        f'content_identity = "{facts["content_id"]}"\n'
    ).encode("utf-8")


def render_proposal_evidence(report: Mapping[str, Any], evidence_path: Path) -> bytes:
    identity = report["source_identity"]
    return (
        "# Catalog-Pack Generated Baseline Proposal\n\n"
        "Status: generated-only proposal input; Effigy review and merge required\n"
        "Authority: `inflatable-cookie/effigy`\n"
        f"Artifact digest: `{report['manifest_digest']}`\n"
        f"Pack: `{report['pack_id']}` `{report['pack_version']}`\n"
        f"Content identity: `{report['content_id']}`\n"
        f"Source commit: `{identity['source_commit']}`\n"
        f"Source tag: `{identity['source_tag']}`\n"
        f"Source tag object: `{identity['tag_object']}`\n\n"
        "This file is proposal evidence. It does not accept, merge, publish, "
        "release, or activate the baseline. The proposal workflow changes only "
        "the generated catalog snapshot, typed lock, and this dated evidence.\n\n"
        "The pack workflow verifies the digest-bound attestation, exact artifact "
        "inventory and bytes, Effigy's offline baseline verifier, and the path "
        "allowlist before creating a branch and pull request.\n"
    ).encode("utf-8")


def _expected_candidate(
    artifact_root: Path,
    manifest_path: Path,
    artifact_digest: str,
    descriptor_path: Path | None = None,
) -> tuple[dict[str, Any], Path, bytes, bytes]:
    report = verify_pulled_artifact(artifact_root, manifest_path, artifact_digest, descriptor_path)
    identity = dict(report["source_identity"])
    identity["source_repository"] = PACK_GITHUB_REPOSITORY
    lock = render_baseline_lock(report, identity, artifact_digest)
    evidence_path = _evidence_path(identity["source_created"])
    evidence = render_proposal_evidence(report, evidence_path)
    report = {**report, "evidence_path": evidence_path.as_posix(), "lock_bytes": len(lock), "evidence_bytes": len(evidence)}
    return report, evidence_path, lock, evidence


def materialize_candidate(
    effigy_root: Path,
    artifact_root: Path,
    manifest_path: Path,
    artifact_digest: str,
    descriptor_path: Path | None = None,
) -> dict[str, Any]:
    """Write the candidate into a checkout only after all artifact checks pass."""

    require(effigy_root.is_dir() and not effigy_root.is_symlink(), f"Effigy checkout is not a real directory: {effigy_root}")
    require(not _git_status_paths(effigy_root), "Effigy checkout must be clean before proposal materialization")
    report, evidence_path, lock, evidence = _expected_candidate(artifact_root, manifest_path, artifact_digest, descriptor_path)
    target_snapshot = effigy_root / EFFIGY_SNAPSHOT_ROOT
    target_lock = effigy_root / EFFIGY_LOCK_PATH
    target_evidence = effigy_root / evidence_path

    if target_snapshot.exists() or target_snapshot.is_symlink():
        require(target_snapshot.is_dir() and not target_snapshot.is_symlink(), "existing Effigy baseline snapshot is not a real directory")
        shutil.rmtree(target_snapshot)
    shutil.copytree(artifact_root, target_snapshot)

    if target_lock.exists() or target_lock.is_symlink():
        require(target_lock.is_file() and not target_lock.is_symlink(), "existing Effigy baseline lock is not a regular file")
    target_lock.parent.mkdir(parents=True, exist_ok=True)
    target_lock.write_bytes(lock)

    if target_evidence.exists() or target_evidence.is_symlink():
        require(target_evidence.is_file() and not target_evidence.is_symlink(), "existing proposal evidence is not a regular file")
        require(target_evidence.read_bytes() == evidence, "existing proposal evidence differs from the deterministic candidate")
    else:
        target_evidence.parent.mkdir(parents=True, exist_ok=True)
        target_evidence.write_bytes(evidence)

    report.update(
        {
            "materialized": True,
            "snapshot_path": EFFIGY_SNAPSHOT_ROOT.as_posix(),
            "lock_path": EFFIGY_LOCK_PATH.as_posix(),
        }
    )
    return report


def _git_status_paths(effigy_root: Path) -> list[str]:
    result = run_command(["git", "-C", str(effigy_root), "status", "--porcelain", "--untracked-files=all"])
    paths: list[str] = []
    for line in decode_output(result.stdout).splitlines():
        require(len(line) >= 4, f"could not parse Effigy git status line: {line!r}")
        status = line[:2]
        path = line[3:]
        require("->" not in path, "proposal diff contains a rename; generated paths must be added or removed")
        require(status.strip(), f"Effigy git status has an empty status: {line!r}")
        paths.append(path)
    return paths


def verify_generated_only_diff(
    effigy_root: Path,
    artifact_root: Path,
    manifest_path: Path,
    artifact_digest: str,
    descriptor_path: Path | None = None,
) -> dict[str, Any]:
    """Recheck exact bytes and status after staging, catching hand edits."""

    report, evidence_path, lock, evidence = _expected_candidate(artifact_root, manifest_path, artifact_digest, descriptor_path)
    paths = _git_status_paths(effigy_root)
    path_report = validate_proposal_paths(paths, evidence_path.as_posix())
    snapshot = effigy_root / EFFIGY_SNAPSHOT_ROOT
    require(tree_snapshot(snapshot) == tree_snapshot(artifact_root), "Effigy candidate snapshot bytes differ from the verified artifact")
    candidate_lock = effigy_root / EFFIGY_LOCK_PATH
    require(candidate_lock.read_bytes() == lock, "Effigy candidate lock bytes differ from deterministic generation")
    candidate_evidence = effigy_root / evidence_path
    require(candidate_evidence.read_bytes() == evidence, "Effigy proposal evidence bytes differ from deterministic generation")
    report.update({"diff_verified": True, "changed_paths": paths, "path_policy": path_report})
    return report


def proposal_attestation_check(payload_path: Path, artifact_digest: str) -> dict[str, Any]:
    require_sha256_digest(artifact_digest)
    try:
        payload = payload_path.read_text(encoding="utf-8")
    except OSError as error:
        fail(f"proposal attestation output is unreadable: {error}")
    require_verified_attestation_json(payload, artifact_digest)
    return {"attestation_verified": True, "digest": artifact_digest, "network_access": False}


def proposal_body(report: Mapping[str, Any]) -> str:
    identity = report["source_identity"]
    return (
        "## Generated Effigy catalog baseline proposal\n\n"
        "This PR is prepared by the catalog-pack proposal workflow from one "
        "verified, digest-addressed artifact. It is intentionally limited to "
        "generated baseline content and evidence.\n\n"
        f"- Artifact digest: `{report['manifest_digest']}`\n"
        f"- Pack: `{report['pack_id']}` `{report['pack_version']}`\n"
        f"- Content identity: `{report['content_id']}`\n"
        f"- Source commit: `{identity['source_commit']}`\n"
        f"- Source tag: `{identity['source_tag']}`\n"
        f"- Source tag object: `{identity['tag_object']}`\n"
        f"- Evidence: `{report['evidence_path']}`\n\n"
        "The workflow verified the digest-bound attestation, exact artifact "
        "inventory and bytes, Effigy's committed offline baseline verifier, "
        "and the generated-only path policy before opening this PR.\n\n"
        "Effigy owners must review and validate this change. The pack workflow "
        "does not approve, merge, release, publish, or activate it.\n"
    )


def verify_proposal(
    effigy_root: Path,
    artifact_root: Path,
    manifest_path: Path,
    artifact_digest: str,
    descriptor_path: Path | None = None,
    *,
    run_verifier: bool = True,
    offline: bool = False,
) -> dict[str, Any]:
    report = verify_generated_only_diff(effigy_root, artifact_root, manifest_path, artifact_digest, descriptor_path)
    if run_verifier:
        report["effigy_verification"] = run_effigy_verifier(effigy_root, offline=offline)
    else:
        report["effigy_verification"] = {"skipped": True, "reason": "model-only"}
    report["proposal_ready"] = True
    return report


def proposal_model_check() -> dict[str, Any]:
    from catalog_pack_proposal_tests import proposal_model_proof

    return proposal_model_proof()
