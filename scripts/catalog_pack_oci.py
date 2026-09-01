"""Deterministic OCI layout and no-push publication rehearsal."""

from __future__ import annotations

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


def build_oci_layout(output: Path) -> dict[str, Any]:
    require(not output.exists(), f"OCI layout output already exists: {output}")
    output.mkdir(parents=True)
    (output / "blobs" / "sha256").mkdir(parents=True)

    files, _ = collect_tree(PACK_ROOT)
    layer_descriptors: list[dict[str, Any]] = []
    for relative in files:
        data = (PACK_ROOT / relative).read_bytes()
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
        "annotations": {
            "io.effigy.catalog.pack.content-id": PACK_CONTENT_ID,
            "org.opencontainers.image.created": SOURCE_CREATED,
            "org.opencontainers.image.revision": AUTHORITY_COMMIT,
            "org.opencontainers.image.source": SOURCE_URL,
            "org.opencontainers.image.version": PACK_VERSION,
        },
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
            "org.opencontainers.image.created": SOURCE_CREATED,
            "org.opencontainers.image.ref.name": f"v{PACK_VERSION}",
            "org.opencontainers.image.version": PACK_VERSION,
        },
        "artifactType": OCI_ARTIFACT_TYPE,
        "digest": manifest_digest,
        "mediaType": OCI_MANIFEST_MEDIA_TYPE,
        "size": len(manifest_bytes),
    }
    index = {"manifests": [descriptor], "mediaType": OCI_INDEX_MEDIA_TYPE, "schemaVersion": 2}
    (output / "oci-layout").write_bytes(canonical_json({"imageLayoutVersion": OCI_LAYOUT_VERSION}))
    (output / "index.json").write_bytes(canonical_json(index))
    verify_oci_layout(output)
    return {
        "layout": str(output),
        "reference": OCI_REFERENCE,
        "manifest_digest": manifest_digest,
        "content_id": PACK_CONTENT_ID,
        "layer_count": len(layer_descriptors),
        "created": SOURCE_CREATED,
        "revision": AUTHORITY_COMMIT,
    }


def read_layout_manifest(layout: Path) -> tuple[dict[str, Any], bytes, str]:
    try:
        layout_metadata = json.loads((layout / "oci-layout").read_text())
        index = json.loads((layout / "index.json").read_text())
    except (OSError, json.JSONDecodeError) as error:
        fail(f"invalid OCI layout metadata: {error}")
    require(layout_metadata == {"imageLayoutVersion": OCI_LAYOUT_VERSION}, "OCI layout version is not fixed")
    manifests = index.get("manifests")
    require(isinstance(manifests, list) and len(manifests) == 1, "OCI index must contain one candidate")
    descriptor = manifests[0]
    require(descriptor.get("annotations", {}).get("org.opencontainers.image.ref.name") == f"v{PACK_VERSION}", "OCI index tag is not v1.0.0")
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


def verify_oci_layout(layout: Path) -> dict[str, Any]:
    manifest, manifest_bytes, manifest_digest = read_layout_manifest(layout)
    require(manifest.get("schemaVersion") == 2, "OCI manifest schema version is not 2")
    require(manifest.get("mediaType") == OCI_MANIFEST_MEDIA_TYPE, "OCI manifest media type changed")
    require(manifest.get("artifactType") == OCI_ARTIFACT_TYPE, "OCI artifact type changed")
    annotations = manifest.get("annotations")
    require(isinstance(annotations, dict), "OCI manifest annotations are missing")
    require(annotations.get("org.opencontainers.image.created") == SOURCE_CREATED, "OCI timestamp is not source-derived")
    require(annotations.get("org.opencontainers.image.revision") == AUTHORITY_COMMIT, "OCI revision is not pinned")
    require(annotations.get("org.opencontainers.image.source") == SOURCE_URL, "OCI source annotation changed")
    require(annotations.get("org.opencontainers.image.version") == PACK_VERSION, "OCI version annotation changed")
    require(annotations.get("io.effigy.catalog.pack.content-id") == PACK_CONTENT_ID, "OCI content annotation changed")

    config = manifest.get("config")
    require(isinstance(config, dict), "OCI config descriptor is missing")
    require(config.get("mediaType") == OCI_EMPTY_CONFIG_MEDIA_TYPE, "OCI config media type changed")
    require(config.get("digest") == sha256_digest(b"{}"), "OCI config is not the fixed empty config")
    require(config.get("size") == 2 and config.get("data") == "e30=", "OCI empty config bytes changed")

    layers = manifest.get("layers")
    require(isinstance(layers, list) and len(layers) == len(PACK_FILES), "OCI layer inventory count changed")
    titles: list[str] = []
    for layer in layers:
        require(layer.get("mediaType") == OCI_FILE_LAYER_MEDIA_TYPE, "OCI pack layer media type changed")
        title = layer.get("annotations", {}).get("org.opencontainers.image.title")
        require(isinstance(title, str), "OCI layer lacks a path title")
        path = Path(title)
        require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == title, f"unsafe OCI layer title: {title!r}")
        titles.append(title)
        require(title in PACK_FILES, f"OCI layer is outside the pack inventory: {title}")
        digest = layer.get("digest")
        require(isinstance(digest, str) and digest.startswith("sha256:"), f"OCI layer lacks a digest: {title}")
        blob = layout / "blobs" / "sha256" / digest.split(":", 1)[1]
        data = blob.read_bytes()
        require(len(data) == layer.get("size"), f"OCI layer size differs for {title}")
        require(sha256_digest(data) == digest, f"OCI layer digest differs for {title}")
        require(data == (PACK_ROOT / title).read_bytes(), f"OCI layer bytes differ for {title}")
    require(titles == sorted(PACK_FILES), "OCI layer path order is not deterministic")
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


def deterministic_oci_proof() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-oci-") as temporary:
        temporary_root = Path(temporary)
        first = temporary_root / "first"
        second = temporary_root / "second"
        first_report = build_oci_layout(first)
        second_report = build_oci_layout(second)
        require(
            first_report["manifest_digest"] == second_report["manifest_digest"],
            "repeated OCI candidates produced different manifest digests",
        )
        require(tree_snapshot(first) == tree_snapshot(second), "repeated OCI candidates differ in layout bytes")
        verify_oci_layout(first)

        roundtrip = "native"
        oras = shutil.which("oras")
        if oras:
            pulled = temporary_root / "oras-pulled"
            result = run_command(
                [oras, "pull", "--oci-layout", f"{first}:v{PACK_VERSION}", "--output", str(pulled), "--no-tty"],
                check=False,
            )
            if result.returncode != 0:
                fail(f"ORAS could not pull the local candidate: {decode_output(result.stderr)}")
            require(tree_snapshot(pulled) == tree_snapshot(PACK_ROOT), "ORAS round-trip changed pack bytes")
            roundtrip = "oras"
        first_report["roundtrip"] = roundtrip
        return first_report


def no_push_rehearsal() -> dict[str, Any]:
    candidate = deterministic_oci_proof()
    digest = candidate["manifest_digest"]
    tag = OCI_REFERENCE

    def reconcile(remote: dict[str, str], candidate_digest: str) -> str:
        existing = remote.get(tag)
        if existing is None:
            remote[tag] = candidate_digest
            return "absent-would-create"
        if existing == candidate_digest:
            return "same-digest-would-reuse"
        raise CheckFailure(f"collision rejected: {existing} is already recorded for {tag}")

    absent_remote: dict[str, str] = {}
    absent_result = reconcile(absent_remote, digest)
    require(absent_remote == {tag: digest}, "absent rehearsal did not record the candidate decision")

    same_remote = {tag: digest}
    same_before = dict(same_remote)
    same_result = reconcile(same_remote, digest)
    require(same_remote == same_before, "same-digest rehearsal changed remote state")

    collision_digest = "sha256:" + "0" * 64
    require(collision_digest != digest, "collision fixture unexpectedly matches candidate")
    collision_remote = {tag: collision_digest}
    collision_before = dict(collision_remote)
    try:
        reconcile(collision_remote, digest)
    except CheckFailure as error:
        require("collision rejected" in str(error), "collision rehearsal failed for the wrong reason")
    require(collision_remote == collision_before, "collision rehearsal changed remote state")

    return {
        "reference": tag,
        "candidate_digest": digest,
        "network_access": False,
        "push_attempted": False,
        "scenarios": {
            "absent": absent_result,
            "same_digest": same_result,
            "collision": "rejected-without-write",
        },
    }
