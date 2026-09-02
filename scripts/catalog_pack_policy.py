"""Current Effigy support-policy consumption and release freshness."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from catalog_pack_shared import *


SUPPORT_KEYS = {
    "schema_version",
    "as_of_release",
    "required_versions",
    "oldest_update_capable_release",
}


def git_blob_oid(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def parse_semver_tuple(value: str, label: str) -> tuple[int, int, int]:
    require(isinstance(value, str) and value, f"{label} is missing")
    require(re.fullmatch(r"\d+\.\d+(?:\.\d+)?", value) is not None, f"{label} is not a semantic version: {value}")
    parts = [int(part) for part in value.split(".")]
    while len(parts) < 3:
        parts.append(0)
    return parts[0], parts[1], parts[2]


def format_semver(value: tuple[int, int, int]) -> str:
    return f"{value[0]}.{value[1]}.{value[2]}"


def workspace_package_version(cargo_toml: str) -> str:
    match = re.search(
        r'(?ms)^\[workspace\.package\][^\[]*?^version\s*=\s*"([^"]+)"',
        cargo_toml,
    )
    require(match is not None, "Effigy Cargo.toml does not declare [workspace.package] version")
    version = match.group(1)
    parse_semver_tuple(version, "workspace package version")
    return version


def version_admitted(version: str, spec: str) -> bool:
    """Admit a version against the pack's `>=x.y, <a.b` compatibility range."""

    candidate = parse_semver_tuple(version, "required Effigy version")
    clauses = [clause.strip() for clause in spec.split(",")]
    require(clauses, "pack compatibility range is empty")
    for clause in clauses:
        if clause.startswith(">="):
            bound = parse_semver_tuple(clause[2:].strip(), "compatibility lower bound")
            if candidate < bound:
                return False
        elif clause.startswith("<="):
            bound = parse_semver_tuple(clause[2:].strip(), "compatibility upper bound")
            if candidate > bound:
                return False
        elif clause.startswith("<"):
            bound = parse_semver_tuple(clause[1:].strip(), "compatibility upper bound")
            if candidate >= bound:
                return False
        elif clause.startswith(">"):
            bound = parse_semver_tuple(clause[1:].strip(), "compatibility lower bound")
            if candidate <= bound:
                return False
        else:
            fail(f"unsupported pack compatibility clause: {clause!r}")
    return True


def parse_support_policy(document: dict[str, Any], current_release: str) -> dict[str, Any]:
    extra = sorted(set(document) - SUPPORT_KEYS)
    require(not extra, f"Effigy support policy has unknown keys: {extra}")
    require(document.get("schema_version") == 1, "Effigy support schema_version is not 1")
    as_of = document.get("as_of_release")
    require(isinstance(as_of, str), "Effigy support as_of_release is missing")
    parse_semver_tuple(as_of, "as_of_release")
    require(as_of == current_release, f"as_of_release is {as_of}, but the Effigy workspace release is {current_release}")
    required = document.get("required_versions")
    require(isinstance(required, list) and required, "Effigy support required_versions is empty")
    parsed: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(required):
        require(isinstance(item, str), f"required_versions[{index}] is not a string")
        parse_semver_tuple(item, f"required_versions[{index}]")
        require(item not in seen, f"required_versions contains duplicate version {item}")
        seen.add(item)
        parsed.append(item)
    require(current_release in seen, f"required_versions does not include the current Effigy release {current_release}")
    oldest = document.get("oldest_update_capable_release")
    if oldest is not None:
        require(isinstance(oldest, str), "oldest_update_capable_release is not a string")
        parse_semver_tuple(oldest, "oldest_update_capable_release")
        minimum = min(parsed, key=lambda value: parse_semver_tuple(value, "required version"))
        require(
            oldest == minimum,
            f"oldest_update_capable_release is {oldest}, but the minimum required version is {minimum}",
        )
    return {
        "schema_version": 1,
        "as_of_release": as_of,
        "required_versions": parsed,
        "oldest_update_capable_release": oldest,
    }


def resolve_support_commit(authority: Path) -> str:
    """Resolve Effigy's current default-branch commit, never the import pin."""

    for arguments in (
        ["rev-parse", "--abbrev-ref", "origin/HEAD"],
        ["rev-parse", "--verify", "origin/main"],
        ["rev-parse", "--verify", "refs/heads/main"],
        ["rev-parse", "--verify", "main"],
    ):
        result = run_command(["git", "-C", str(authority), *arguments], check=False)
        if result.returncode != 0:
            continue
        resolved = decode_output(result.stdout)
        if arguments[:2] == ["rev-parse", "--abbrev-ref"]:
            if not resolved.startswith("origin/"):
                continue
            return git_output(authority, ["rev-parse", resolved])
        require(re.fullmatch(r"[0-9a-f]{40}", resolved) is not None, "Effigy default-branch commit is not a full object")
        return resolved
    return git_output(authority, ["rev-parse", "HEAD"])


def read_support_from_commit(authority: Path, commit: str) -> tuple[bytes, str, dict[str, Any], str]:
    require(
        git_output(authority, ["rev-parse", f"{commit}^{{commit}}"]) == commit,
        f"Effigy support commit {commit} is not available",
    )
    support_bytes = git_bytes(authority, ["show", f"{commit}:{SUPPORT_RELATIVE.as_posix()}"])
    support_oid = git_output(authority, ["rev-parse", f"{commit}:{SUPPORT_RELATIVE.as_posix()}"])
    calculated = git_blob_oid(support_bytes)
    require(calculated == support_oid, "support Git blob OID does not match its bytes")
    try:
        document = parse_toml(support_bytes.decode("utf-8"))
    except (UnicodeDecodeError, TOMLDecodeError) as error:
        fail(f"Effigy support file is invalid TOML: {error}")
    cargo_text = git_bytes(authority, ["show", f"{commit}:Cargo.toml"]).decode("utf-8")
    current_release = workspace_package_version(cargo_text)
    policy = parse_support_policy(document, current_release)
    return support_bytes, support_oid, policy, current_release


def prove_current_support(
    authority: Path | None,
    require_authority: bool,
    pack_compatibility: str | None = None,
) -> dict[str, Any]:
    """Prove current default-branch support. Never uses the one-time import pin."""

    if authority is None:
        if require_authority:
            fail("Effigy authority checkout is required; pass --effigy-root or set EFFIGY_ROOT")
        return {
            "authority": "not provided",
            "source_checked": False,
            "support_checked": False,
            "import_pin_used": False,
        }

    commit = resolve_support_commit(authority)
    _, support_oid, policy, current_release = read_support_from_commit(authority, commit)
    compatibility = pack_compatibility
    if compatibility is None:
        compatibility = validate_pack_tree()["effigy_compatibility"]
    for version in policy["required_versions"]:
        require(
            version_admitted(version, compatibility),
            f"pack compatibility {compatibility} does not admit required Effigy {version}",
        )
    return {
        "authority": str(authority),
        "authority_commit": commit,
        "support_commit": commit,
        "source_checked": False,
        "support_checked": True,
        "import_pin_used": False,
        "support_blob_oid": support_oid,
        "support_as_of_release": policy["as_of_release"],
        "support_required_versions": policy["required_versions"],
        "support_schema_version": policy["schema_version"],
        "support_oldest_update_capable_release": policy["oldest_update_capable_release"],
        "effigy_workspace_release": current_release,
        "pack_compatibility": compatibility,
    }


def prove_support_releases(
    policy: Mapping[str, Any],
    getter: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """GET-only GitHub Release freshness for the already-parsed support policy."""

    fetch = getter or _gh_release_get
    latest = fetch(f"repos/{EFFIGY_GITHUB_REPOSITORY}/releases/latest")
    require(latest.get("draft") is False, "latest Effigy GitHub release is a draft")
    require(latest.get("prerelease") is False, "latest Effigy GitHub release is a prerelease")
    latest_tag = str(latest.get("tag_name") or "")
    latest_version = latest_tag.removeprefix("v")
    as_of = policy["as_of_release"] if "as_of_release" in policy else policy.get("support_as_of_release")
    require(isinstance(as_of, str), "support policy as_of_release is missing for release freshness")
    require(
        latest_version == as_of,
        f"as_of_release is {as_of}, but the latest non-draft GitHub release is {latest_tag}",
    )
    required = policy["required_versions"] if "required_versions" in policy else policy.get("support_required_versions")
    require(isinstance(required, list) and required, "support required_versions missing for release freshness")
    checked: list[str] = []
    for version in required:
        release = fetch(f"repos/{EFFIGY_GITHUB_REPOSITORY}/releases/tags/v{version}")
        require(release.get("draft") is False, f"required Effigy release v{version} is a draft")
        require(str(release.get("tag_name") or "").removeprefix("v") == version, f"required release tag is not v{version}")
        checked.append(version)
    return {
        "checked": True,
        "network": "GET-only",
        "latest_release": latest_tag,
        "as_of_release": as_of,
        "required_releases": checked,
        "write_methods_used": [],
    }


def _gh_release_get(path: str) -> dict[str, Any]:
    gh = shutil.which("gh")
    require(gh is not None, "support release freshness requires the GitHub CLI (gh)")
    result = run_command([gh, "api", "--method", "GET", path], check=False)
    if result.returncode != 0:
        detail = decode_output(result.stderr) or decode_output(result.stdout)
        fail(f"read-only release GET failed for {path}: {detail}")
    try:
        payload = json.loads(decode_output(result.stdout))
    except json.JSONDecodeError as error:
        fail(f"release GET returned invalid JSON for {path}: {error}")
    require(isinstance(payload, dict), f"release GET returned a non-object for {path}")
    return payload
