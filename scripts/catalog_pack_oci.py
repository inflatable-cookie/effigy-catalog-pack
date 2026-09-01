"""Deterministic OCI layout for the canonical pack source."""

from __future__ import annotations

from datetime import datetime, timezone

from catalog_pack_shared import *


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_digest(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def write_blob(layout: Path, data: bytes) -> str:
    digest = sha256_digest(data)
    algorithm, encoded = digest.split(":", 1)
    blob = layout / "blobs" / algorithm / encoded
    blob.parent.mkdir(parents=True, exist_ok=True)
    blob.write_bytes(data)
    return digest


def prepare_layout_output(output: Path) -> None:
    if not output.exists() and not output.is_symlink():
        return
    if output.is_symlink() or not output.is_dir():
        fail(f"OCI layout output is not a real directory: {output}")
    generated_root = (ROOT / ".effigy").resolve()
    require(
        output.resolve().is_relative_to(generated_root),
        f"refusing to replace an existing OCI layout outside {generated_root}",
    )
    shutil.rmtree(output)


def source_repository_identity() -> dict[str, str]:
    """Resolve OCI provenance from this source repository, not Effigy."""

    status = run_command(["git", "-C", str(ROOT), "status", "--porcelain", "--", "pack"])
    require(not decode_output(status.stdout), "pack source has uncommitted changes; commit it before OCI identity proof")
    source_commit = git_output(ROOT, ["rev-parse", "HEAD"])
    require(re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None, "source repository HEAD is not a full commit")
    try:
        epoch = int(git_output(ROOT, ["show", "-s", "--format=%ct", source_commit]))
        created = datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError, OverflowError) as error:
        fail(f"source repository commit timestamp is invalid: {error}")
    return {"source_commit": source_commit, "source_created": created}


def validate_source_identity(identity: dict[str, str], pack_version: str, require_tag: bool = False) -> None:
    source_commit = identity.get("source_commit", "")
    source_created = identity.get("source_created", "")
    require(re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None, "OCI source revision is not a full commit")
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", source_created) is not None, "OCI source timestamp is not UTC RFC3339")
    has_tag = "source_tag" in identity or "tag_object" in identity or "peeled_commit" in identity
    require(not require_tag or has_tag, "publication rehearsal requires annotated source-tag identity")
    if has_tag:
        require(identity.get("source_tag") == f"v{pack_version}", "source tag does not match pack version")
        require(re.fullmatch(r"[0-9a-f]{40}", identity.get("tag_object", "")) is not None, "source tag object is not a full object id")
        require(identity.get("peeled_commit") == source_commit, "annotated source tag does not peel to the source commit")
        require(identity.get("source_ref") == source_commit, "source ref does not match the peeled source commit")


def manifest_annotations(pack_facts: dict[str, Any], source_identity: dict[str, str]) -> dict[str, str]:
    annotations = {
        "io.effigy.catalog.pack.content-id": pack_facts["content_id"],
        "org.opencontainers.image.created": source_identity["source_created"],
        "org.opencontainers.image.revision": source_identity["source_commit"],
        "org.opencontainers.image.source": SOURCE_URL,
        "org.opencontainers.image.version": pack_facts["pack_version"],
    }
    if "source_tag" in source_identity:
        annotations.update(
            {
                "io.effigy.catalog.pack.source-tag": source_identity["source_tag"],
                "io.effigy.catalog.pack.source-tag-object": source_identity["tag_object"],
                "io.effigy.catalog.pack.source-commit": source_identity["peeled_commit"],
            }
        )
    return annotations


def build_oci_layout(
    output: Path,
    pack_root: Path = PACK_ROOT,
    source_identity: dict[str, str] | None = None,
) -> dict[str, Any]:
    require(not output.exists(), f"OCI layout output already exists: {output}")
    pack_facts = validate_pack_tree(pack_root)
    identity = source_identity or source_repository_identity()
    validate_source_identity(identity, pack_facts["pack_version"])
    output.mkdir(parents=True)
    (output / "blobs" / "sha256").mkdir(parents=True)

    files, _ = collect_tree(pack_root)
    layer_descriptors: list[dict[str, Any]] = []
    for relative in files:
        data = (pack_root / relative).read_bytes()
        digest = write_blob(output, data)
        layer_descriptors.append(
            {
                "annotations": {"org.opencontainers.image.title": relative},
                "digest": digest,
                "mediaType": OCI_FILE_LAYER_MEDIA_TYPE,
                "size": len(data),
            }
        )

    empty_config = b"{}"
    config_digest = write_blob(output, empty_config)
    manifest = {
        "annotations": manifest_annotations(pack_facts, identity),
        "artifactType": OCI_ARTIFACT_TYPE,
        "config": {
            "data": base64.b64encode(empty_config).decode("ascii"),
            "digest": config_digest,
            "mediaType": OCI_EMPTY_CONFIG_MEDIA_TYPE,
            "size": len(empty_config),
        },
        "layers": layer_descriptors,
        "mediaType": OCI_MANIFEST_MEDIA_TYPE,
        "schemaVersion": 2,
    }
    manifest_bytes = canonical_json(manifest)
    manifest_digest = write_blob(output, manifest_bytes)
    descriptor = {
        "annotations": {
            "org.opencontainers.image.created": identity["source_created"],
            "org.opencontainers.image.ref.name": f"v{pack_facts['pack_version']}",
            "org.opencontainers.image.version": pack_facts["pack_version"],
        },
        "artifactType": OCI_ARTIFACT_TYPE,
        "digest": manifest_digest,
        "mediaType": OCI_MANIFEST_MEDIA_TYPE,
        "size": len(manifest_bytes),
    }
    index = {"manifests": [descriptor], "mediaType": OCI_INDEX_MEDIA_TYPE, "schemaVersion": 2}
    (output / "oci-layout").write_bytes(canonical_json({"imageLayoutVersion": OCI_LAYOUT_VERSION}))
    (output / "index.json").write_bytes(canonical_json(index))
    verify_oci_layout(output, pack_root, pack_facts, identity)
    return {
        "layout": str(output),
        "reference": f"{OCI_REPOSITORY}:v{pack_facts['pack_version']}",
        "manifest_digest": manifest_digest,
        "content_id": pack_facts["content_id"],
        "layer_count": len(layer_descriptors),
        "created": identity["source_created"],
        "revision": identity["source_commit"],
        "source_identity": identity,
    }


def read_layout_manifest(layout: Path, expected_version: str | None = None) -> tuple[dict[str, Any], bytes, str]:
    try:
        layout_metadata = json.loads((layout / "oci-layout").read_text())
        index = json.loads((layout / "index.json").read_text())
    except (OSError, json.JSONDecodeError) as error:
        fail(f"invalid OCI layout metadata: {error}")
    require(layout_metadata == {"imageLayoutVersion": OCI_LAYOUT_VERSION}, "OCI layout version is not fixed")
    manifests = index.get("manifests")
    require(isinstance(manifests, list) and len(manifests) == 1, "OCI index must contain one candidate")
    descriptor = manifests[0]
    ref_name = descriptor.get("annotations", {}).get("org.opencontainers.image.ref.name")
    require(isinstance(ref_name, str) and ref_name.startswith("v"), "OCI index tag is missing")
    if expected_version is not None:
        require(ref_name == f"v{expected_version}", "OCI index tag does not match pack version")
    digest = descriptor.get("digest")
    require(isinstance(digest, str) and digest.startswith("sha256:"), "OCI index descriptor lacks a sha256 digest")
    blob = layout / "blobs" / "sha256" / digest.split(":", 1)[1]
    manifest_bytes = blob.read_bytes()
    require(sha256_digest(manifest_bytes) == digest, "OCI manifest digest does not match its bytes")
    try:
        manifest = json.loads(manifest_bytes)
    except json.JSONDecodeError as error:
        fail(f"OCI manifest is not JSON: {error}")
    return manifest, manifest_bytes, digest


def verify_oci_layout(
    layout: Path,
    pack_root: Path = PACK_ROOT,
    pack_facts: dict[str, Any] | None = None,
    source_identity: dict[str, str] | None = None,
) -> dict[str, Any]:
    facts = pack_facts or validate_pack_tree(pack_root)
    identity = source_identity or source_repository_identity()
    validate_source_identity(identity, facts["pack_version"])
    manifest, manifest_bytes, manifest_digest = read_layout_manifest(layout, facts["pack_version"])
    require(manifest.get("schemaVersion") == 2, "OCI manifest schema version is not 2")
    require(manifest.get("mediaType") == OCI_MANIFEST_MEDIA_TYPE, "OCI manifest media type changed")
    require(manifest.get("artifactType") == OCI_ARTIFACT_TYPE, "OCI artifact type changed")
    annotations = manifest.get("annotations")
    require(isinstance(annotations, dict), "OCI manifest annotations are missing")
    expected_annotations = manifest_annotations(facts, identity)
    for key, value in expected_annotations.items():
        require(annotations.get(key) == value, f"OCI annotation changed: {key}")

    config = manifest.get("config")
    require(isinstance(config, dict), "OCI config descriptor is missing")
    require(config.get("mediaType") == OCI_EMPTY_CONFIG_MEDIA_TYPE, "OCI config media type changed")
    require(config.get("digest") == sha256_digest(b"{}"), "OCI config is not the fixed empty config")
    require(config.get("size") == 2 and config.get("data") == "e30=", "OCI empty config bytes changed")

    files, _ = collect_tree(pack_root)
    layers = manifest.get("layers")
    require(isinstance(layers, list) and len(layers) == len(files), "OCI layer inventory count changed")
    titles: list[str] = []
    for layer in layers:
        require(layer.get("mediaType") == OCI_FILE_LAYER_MEDIA_TYPE, "OCI pack layer media type changed")
        title = layer.get("annotations", {}).get("org.opencontainers.image.title")
        require(isinstance(title, str), "OCI layer lacks a path title")
        path = Path(title)
        require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == title, f"unsafe OCI layer title: {title!r}")
        titles.append(title)
        require(title in files, f"OCI layer is outside the pack inventory: {title}")
        digest = layer.get("digest")
        require(isinstance(digest, str) and digest.startswith("sha256:"), f"OCI layer lacks a digest: {title}")
        blob = layout / "blobs" / "sha256" / digest.split(":", 1)[1]
        data = blob.read_bytes()
        require(len(data) == layer.get("size"), f"OCI layer size differs for {title}")
        require(sha256_digest(data) == digest, f"OCI layer digest differs for {title}")
        require(data == (pack_root / title).read_bytes(), f"OCI layer bytes differ for {title}")
    require(titles == sorted(files), "OCI layer path order is not deterministic")
    require(len(set(titles)) == len(titles), "OCI layer paths are duplicated")
    return {"manifest_digest": manifest_digest, "manifest_bytes": len(manifest_bytes), "layer_count": len(layers)}


def materialize_oci_layers(layout: Path, destination: Path) -> None:
    manifest, _, _ = read_layout_manifest(layout)
    for layer in manifest["layers"]:
        title = layer["annotations"]["org.opencontainers.image.title"]
        target = destination / title
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = layer["digest"].split(":", 1)[1]
        target.write_bytes((layout / "blobs" / "sha256" / digest).read_bytes())


def tree_snapshot(root: Path) -> dict[str, bytes]:
    files, _ = collect_tree(root)
    return {relative: (root / relative).read_bytes() for relative in files}


def deterministic_oci_proof(
    source_identity: dict[str, str] | None = None,
    pack_root: Path = PACK_ROOT,
    run_oras: bool = True,
) -> dict[str, Any]:
    pack_facts = validate_pack_tree(pack_root)
    identity = source_identity or source_repository_identity()
    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-oci-") as temporary:
        temporary_root = Path(temporary)
        first = temporary_root / "first"
        second = temporary_root / "second"
        first_report = build_oci_layout(first, pack_root, identity)
        second_report = build_oci_layout(second, pack_root, identity)
        require(
            first_report["manifest_digest"] == second_report["manifest_digest"],
            "repeated OCI candidates produced different manifest digests",
        )
        require(tree_snapshot(first) == tree_snapshot(second), "repeated OCI candidates differ in layout bytes")
        verify_oci_layout(first, pack_root, pack_facts, identity)

        roundtrip = "skipped"
        if run_oras:
            roundtrip = "native"
            oras = shutil.which("oras")
            if oras:
                pulled = temporary_root / "oras-pulled"
                result = run_command(
                    [oras, "pull", "--oci-layout", f"{first}:v{pack_facts['pack_version']}", "--output", str(pulled), "--no-tty"],
                    check=False,
                )
                if result.returncode != 0:
                    fail(f"ORAS could not pull the local candidate: {decode_output(result.stderr)}")
                require(tree_snapshot(pulled) == tree_snapshot(pack_root), "ORAS round-trip changed pack bytes")
                roundtrip = "oras"
        first_report["roundtrip"] = roundtrip
        return first_report
