"""Current Effigy support proof and one-time catalog import proof."""

from __future__ import annotations

from typing import Mapping

from catalog_pack_policy import prove_current_support, resolve_support_commit
from catalog_pack_shared import *


def resolve_authority(
    explicit: str | None,
    repo_root: Path = ROOT,
    environment: Mapping[str, str] | None = None,
) -> Path | None:
    """Resolve only explicit, configured, or conventional sibling authority."""

    env = os.environ if environment is None else environment
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    if env.get("EFFIGY_ROOT"):
        candidates.append(Path(env["EFFIGY_ROOT"]))
    candidates.append(repo_root.parent / "effigy")

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
    raw = git_bytes(
        authority,
        ["ls-tree", "-r", "-z", IMPORT_AUTHORITY_COMMIT, "--", SOURCE_CATALOG_RELATIVE.as_posix()],
    )
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


def prove_support(authority: Path | None, require_authority: bool) -> dict[str, Any]:
    """Prove only Effigy's current compatibility input, never pack source ownership."""

    return prove_current_support(authority, require_authority)


def prove_import(authority: Path | None) -> dict[str, Any]:
    """Prove the immutable foundation import. Current Effigy HEAD may be later."""

    require(authority is not None, "Effigy authority checkout is required for the import proof")
    require(
        git_output(authority, ["rev-parse", f"{IMPORT_AUTHORITY_COMMIT}^{{commit}}"]) == IMPORT_AUTHORITY_COMMIT,
        "one-time Effigy import commit is not available",
    )
    source_entries = source_git_inventory(authority)
    require(
        [entry[0] for entry in source_entries] == sorted(SOURCE_FILES),
        "pinned Effigy catalog tree inventory differs from the expected source",
    )
    tree = git_output(authority, ["rev-parse", f"{IMPORT_AUTHORITY_COMMIT}:{SOURCE_CATALOG_RELATIVE.as_posix()}"])
    require(tree == IMPORT_AUTHORITY_TREE, f"Effigy catalog tree is {tree}, expected {IMPORT_AUTHORITY_TREE}")

    pack_files, _ = collect_tree(PACK_ROOT)
    require(
        pack_files == sorted(PACK_FILES),
        describe_difference("foundation pack files", pack_files, sorted(PACK_FILES)),
    )
    for relative in SOURCE_FILES:
        committed = git_bytes(
            authority,
            ["show", f"{IMPORT_AUTHORITY_COMMIT}:{(SOURCE_CATALOG_RELATIVE / relative).as_posix()}"],
        )
        require(
            committed == (PACK_ROOT / relative).read_bytes(),
            f"imported catalog bytes differ for {relative}",
        )

    pack_facts = validate_pack_tree()
    require(
        pack_facts["content_id"] == FOUNDATION_PACK_CONTENT_ID,
        f"foundation pack content identity changed: {pack_facts['content_id']}",
    )
    support_oid = git_output(authority, ["rev-parse", f"{IMPORT_AUTHORITY_COMMIT}:{SUPPORT_RELATIVE.as_posix()}"])
    require(support_oid == IMPORT_SUPPORT_BLOB, f"import-era support blob is {support_oid}, expected {IMPORT_SUPPORT_BLOB}")
    return {
        "import_checked": True,
        "authority_commit": IMPORT_AUTHORITY_COMMIT,
        "catalog_tree": IMPORT_AUTHORITY_TREE,
        "support_blob_oid": IMPORT_SUPPORT_BLOB,
        "source_file_count": len(SOURCE_FILES),
        "source_byte_count": sum(len(git_bytes(authority, ["show", f"{IMPORT_AUTHORITY_COMMIT}:{(SOURCE_CATALOG_RELATIVE / relative).as_posix()}"])) for relative in SOURCE_FILES),
        "pack_content_id": pack_facts["content_id"],
        "current_support_commit": resolve_support_commit(authority),
    }
