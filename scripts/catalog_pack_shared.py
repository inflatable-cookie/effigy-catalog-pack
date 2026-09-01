"""Shared tree, manifest, and content-identity checks."""

from __future__ import annotations

from catalog_pack_constants import *

class CheckFailure(RuntimeError):
    """A repository proof failed."""


def fail(message: str) -> None:
    raise CheckFailure(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def decode_output(value: bytes) -> str:
    return value.decode("utf-8", errors="replace").strip()


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        detail = decode_output(result.stderr) or decode_output(result.stdout)
        fail(f"command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return result


def git_output(authority: Path, arguments: list[str]) -> str:
    result = run_command(["git", "-C", str(authority), *arguments])
    return decode_output(result.stdout)


def git_bytes(authority: Path, arguments: list[str]) -> bytes:
    return run_command(["git", "-C", str(authority), *arguments]).stdout


def expected_directories(files: Iterable[str]) -> set[str]:
    directories: set[str] = set()
    for filename in files:
        parent = Path(filename).parent
        while parent != Path("."):
            directories.add(parent.as_posix())
            parent = parent.parent
    return directories


def relative_sort(paths: Iterable[Path]) -> list[Path]:
    return sorted(paths, key=lambda path: path.as_posix().encode("utf-8"))


def collect_tree(root: Path) -> tuple[list[str], list[str]]:
    """Return regular files and real directories below root, rejecting links."""

    try:
        root_metadata = root.lstat()
    except OSError as error:
        fail(f"missing tree {root}: {error}")
    require(stat.S_ISDIR(root_metadata.st_mode), f"tree root is not a real directory: {root}")

    files: list[Path] = []
    directories: list[Path] = []

    def visit(directory: Path, relative: Path) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: os.fsencode(entry.name))
        except OSError as error:
            fail(f"cannot read {directory}: {error}")
        for entry in entries:
            try:
                name = entry.name
                name.encode("utf-8")
                metadata = entry.stat(follow_symlinks=False)
            except UnicodeError:
                fail(f"non-UTF-8 entry name under {root}: {entry.name!r}")
            except OSError as error:
                fail(f"cannot inspect {entry.path}: {error}")

            child_relative = relative / name
            mode = metadata.st_mode
            if stat.S_ISLNK(mode):
                fail(f"symlink is not allowed in pack tree: {child_relative}")
            if stat.S_ISDIR(mode):
                directories.append(child_relative)
                visit(Path(entry.path), child_relative)
            elif stat.S_ISREG(mode):
                files.append(child_relative)
            else:
                fail(f"special file is not allowed in pack tree: {child_relative}")

    visit(root, Path("."))
    return (
        [path.as_posix() for path in relative_sort(files)],
        [path.as_posix() for path in relative_sort(directories)],
    )


def load_toml(path: Path) -> dict[str, Any]:
    try:
        contents = path.read_bytes()
    except OSError as error:
        fail(f"cannot read TOML file {path}: {error}")
    try:
        value = parse_toml(contents.decode("utf-8"))
    except (UnicodeDecodeError, TOMLDecodeError) as error:
        fail(f"invalid TOML in {path}: {error}")
    require(isinstance(value, dict), f"TOML root is not a table: {path}")
    return value


def validate_pack_tree() -> dict[str, Any]:
    files, directories = collect_tree(PACK_ROOT)
    expected_files = sorted(PACK_FILES)
    expected_directories = sorted(expected_directories_for_pack())
    require(files == expected_files, describe_difference("pack files", files, expected_files))
    require(
        directories == expected_directories,
        describe_difference("pack directories", directories, expected_directories),
    )

    manifest = load_toml(PACK_ROOT / "pack.toml")
    require(manifest.get("schema_version") == 1, "pack.toml must declare schema_version = 1")
    identity = manifest.get("pack")
    compatibility = manifest.get("compatibility")
    require(isinstance(identity, dict), "pack.toml must contain [pack]")
    require(isinstance(compatibility, dict), "pack.toml must contain [compatibility]")
    require(identity.get("id") == PACK_ID, f"pack id must be {PACK_ID}")
    require(identity.get("version") == PACK_VERSION, f"pack version must be {PACK_VERSION}")
    require(
        identity.get("description") == "Default Effigy service catalog",
        "pack description does not match the foundation manifest",
    )
    require(
        compatibility.get("effigy") == PACK_COMPATIBILITY,
        f"pack compatibility must be {PACK_COMPATIBILITY!r}",
    )
    require("update" not in manifest, "pack.toml must not own update-channel authority")

    service_names = sorted(
        path.split("/", 1)[0]
        for path in SOURCE_FILES
        if "/" in path
    )
    service_names = sorted(set(service_names))
    for service_name in service_names:
        service_root = PACK_ROOT / service_name
        service_manifest = load_toml(service_root / "service.toml")
        service_table = service_manifest.get("service")
        require(isinstance(service_table, dict), f"{service_name}/service.toml lacks [service]")
        require(
            service_table.get("name") == service_name,
            f"{service_name}/service.toml has the wrong service name",
        )
        compose = service_root / "compose.fragment.yml"
        require(compose.read_bytes(), f"{compose} must not be empty")

    content_id = calculate_content_id(PACK_ROOT, files)
    require(content_id == PACK_CONTENT_ID, f"pack content identity changed: {content_id}")
    return {
        "pack_id": PACK_ID,
        "pack_version": PACK_VERSION,
        "manifest_schema_version": 1,
        "effigy_compatibility": PACK_COMPATIBILITY,
        "file_count": len(files),
        "byte_count": sum((PACK_ROOT / path).stat().st_size for path in files),
        "content_id": content_id,
    }


def expected_directories_for_pack() -> set[str]:
    return expected_directories(PACK_FILES)


def describe_difference(label: str, actual: list[str], expected: list[str]) -> str:
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    detail: list[str] = []
    if missing:
        detail.append(f"missing={missing}")
    if extra:
        detail.append(f"extra={extra}")
    return f"{label} differ" + (f": {', '.join(detail)}" if detail else "")


def calculate_content_id(root: Path, files: Iterable[str] | None = None) -> str:
    if files is None:
        files, _ = collect_tree(root)
    hasher = hashlib.sha256()
    for filename in sorted(files, key=lambda value: value.encode("utf-8")):
        relative = Path(filename)
        encoded_path = bytearray()
        for component in relative.parts:
            component_bytes = component.encode("utf-8")
            encoded_path.extend(len(component_bytes).to_bytes(8, "little"))
            encoded_path.extend(component_bytes)
        data = (root / relative).read_bytes()
        hasher.update(encoded_path)
        hasher.update(b"\0")
        hasher.update(len(data).to_bytes(8, "little"))
        hasher.update(data)
    return f"sha256:{hasher.hexdigest()}"
