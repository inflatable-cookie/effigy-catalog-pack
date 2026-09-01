"""Pinned Effigy source and support-policy proof."""

from __future__ import annotations

from catalog_pack_shared import *

def resolve_authority(explicit: str | None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("EFFIGY_ROOT"):
        candidates.append(Path(os.environ["EFFIGY_ROOT"]))
    candidates.extend(
        [
            ROOT.parent / "effigy",
            Path("/Users/tom/Dev/projects/effigy"),
        ]
    )
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_dir() and (resolved / ".git").exists():
            return resolved
    return None


def source_git_inventory(authority: Path) -> list[tuple[str, str, str]]:
    prefix = SOURCE_CATALOG_RELATIVE.as_posix().encode("utf-8") + b"/"
    raw = git_bytes(authority, ["ls-tree", "-r", "-z", AUTHORITY_COMMIT, "--", SOURCE_CATALOG_RELATIVE.as_posix()])
    entries: list[tuple[str, str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, full_path = record.split(b"\t", 1)
            mode, object_type, object_id = metadata.split()
        except ValueError as error:
            fail(f"could not parse Effigy catalog tree record: {record!r}")
            raise AssertionError from error
        require(object_type == b"blob", f"catalog entry is not a blob: {full_path!r}")
        require(mode in {b"100644", b"100755"}, f"catalog entry is not a regular file: {full_path!r}")
        require(full_path.startswith(prefix), f"unexpected catalog tree path: {full_path!r}")
        relative = full_path[len(prefix) :].decode("utf-8")
        entries.append((relative, mode.decode("ascii"), object_id.decode("ascii")))
    return sorted(entries)


def prove_authority(authority: Path | None, require_authority: bool) -> dict[str, Any]:
    if authority is None:
        if require_authority:
            fail("Effigy authority checkout is required; pass --effigy-root or set EFFIGY_ROOT")
        return {"authority": "not provided", "source_checked": False, "support_checked": False}

    head = git_output(authority, ["rev-parse", "HEAD"])
    require(head == AUTHORITY_COMMIT, f"Effigy authority HEAD is {head}, expected {AUTHORITY_COMMIT}")
    require(
        git_output(authority, ["rev-parse", f"{AUTHORITY_COMMIT}^{{commit}}"]) == AUTHORITY_COMMIT,
        "pinned Effigy authority commit is not available",
    )

    source_root = authority / SOURCE_CATALOG_RELATIVE
    source_files, _ = collect_tree(source_root)
    require(
        source_files == sorted(SOURCE_FILES),
        describe_difference("Effigy source files", source_files, sorted(SOURCE_FILES)),
    )
    source_entries = source_git_inventory(authority)
    require(
        [entry[0] for entry in source_entries] == sorted(SOURCE_FILES),
        "pinned Effigy catalog tree inventory differs from the expected source",
    )
    tree = git_output(authority, ["rev-parse", f"{AUTHORITY_COMMIT}:{SOURCE_CATALOG_RELATIVE.as_posix()}"])
    require(tree == AUTHORITY_TREE, f"Effigy catalog tree is {tree}, expected {AUTHORITY_TREE}")

    for relative in SOURCE_FILES:
        source_path = source_root / relative
        committed = git_bytes(authority, ["show", f"{AUTHORITY_COMMIT}:{(SOURCE_CATALOG_RELATIVE / relative).as_posix()}" ])
        require(
            source_path.read_bytes() == committed == (PACK_ROOT / relative).read_bytes(),
            f"source bytes differ for {relative}",
        )

    support_bytes = git_bytes(authority, ["show", f"{AUTHORITY_COMMIT}:{SUPPORT_RELATIVE.as_posix()}"])
    support_oid = git_output(authority, ["rev-parse", f"{AUTHORITY_COMMIT}:{SUPPORT_RELATIVE.as_posix()}"])
    require(support_oid == SUPPORT_BLOB, f"support blob is {support_oid}, expected {SUPPORT_BLOB}")
    calculated_support_oid = hashlib.sha1(
        b"blob " + str(len(support_bytes)).encode("ascii") + b"\0" + support_bytes
    ).hexdigest()
    require(calculated_support_oid == SUPPORT_BLOB, "support Git blob OID does not match its bytes")
    support_path = authority / SUPPORT_RELATIVE
    if support_path.exists():
        require(support_path.read_bytes() == support_bytes, "Effigy support worktree differs from pinned commit")
    try:
        support = parse_toml(support_bytes.decode("utf-8"))
    except (UnicodeDecodeError, TOMLDecodeError) as error:
        fail(f"pinned Effigy support file is invalid TOML: {error}")
    require(
        support == {
            "schema_version": 1,
            "as_of_release": CURRENT_EFFIGY_RELEASE,
            "required_versions": [CURRENT_EFFIGY_RELEASE],
        },
        "pinned Effigy support policy is not the closed 0.12.1 floor",
    )
    require("oldest_update_capable_release" not in support, "support policy exposes an update floor too early")

    cargo_text = git_bytes(authority, ["show", f"{AUTHORITY_COMMIT}:Cargo.toml"]).decode("utf-8")
    require(
        f'version = "{CURRENT_EFFIGY_RELEASE}"' in cargo_text,
        "pinned Effigy workspace release does not match the support floor",
    )
    return {
        "authority": str(authority),
        "authority_commit": AUTHORITY_COMMIT,
        "catalog_tree": AUTHORITY_TREE,
        "source_checked": True,
        "source_file_count": len(SOURCE_FILES),
        "source_byte_count": sum((source_root / relative).stat().st_size for relative in SOURCE_FILES),
        "support_checked": True,
        "support_blob_oid": SUPPORT_BLOB,
        "support_as_of_release": CURRENT_EFFIGY_RELEASE,
    }
