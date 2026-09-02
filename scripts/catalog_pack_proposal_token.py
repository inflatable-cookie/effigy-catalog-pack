"""GitHub App installation-token seam for the hosted proposal workflow."""

from __future__ import annotations

import time
from typing import Any, Mapping

from catalog_pack_shared import *


_ALLOWED_PROPOSAL_PERMISSIONS = dict(PROPOSAL_APP_PERMISSIONS)
_ALLOWED_TOKEN_RESPONSE_PERMISSIONS = {"contents", "pull_requests", "metadata"}


def app_token_request(app_id: str, installation_id: str) -> dict[str, Any]:
    """Describe the least-privilege installation-token request."""

    require(re.fullmatch(r"[1-9][0-9]*", str(app_id)) is not None, "GitHub App id must be a positive integer")
    require(
        re.fullmatch(r"[1-9][0-9]*", str(installation_id)) is not None,
        "GitHub App installation id must be a positive integer",
    )
    return {
        "method": "POST",
        "endpoint": PROPOSAL_APP_TOKEN_ENDPOINT.format(installation_id=installation_id),
        "repositories": [PROPOSAL_APP_REPOSITORY],
        "permissions": dict(_ALLOWED_PROPOSAL_PERMISSIONS),
        "short_lived": True,
    }


def validate_app_token_response(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Accept only a token response scoped to Effigy and the two write needs."""

    token = payload.get("token")
    require(isinstance(token, str) and token, "GitHub App token response has no token")
    expires_at = payload.get("expires_at")
    require(isinstance(expires_at, str) and expires_at.endswith("Z"), "GitHub App token response has no expiry")
    permissions = payload.get("permissions")
    require(isinstance(permissions, dict), "GitHub App token response has no permissions")
    unexpected_permissions = set(permissions) - _ALLOWED_TOKEN_RESPONSE_PERMISSIONS
    require(not unexpected_permissions, f"GitHub App token response has broad permissions: {sorted(unexpected_permissions)}")
    require(permissions.get("contents") == "write", "GitHub App token lacks contents: write")
    require(permissions.get("pull_requests") == "write", "GitHub App token lacks pull_requests: write")
    if "metadata" in permissions:
        require(permissions["metadata"] == "read", "GitHub App token metadata permission is broader than read")
    repositories = payload.get("repositories")
    require(isinstance(repositories, list) and repositories, "GitHub App token response has no repository scope")
    full_names: list[str] = []
    for repository in repositories:
        require(isinstance(repository, dict), "GitHub App token repository scope is malformed")
        name = repository.get("name")
        require(name == PROPOSAL_APP_REPOSITORY, "GitHub App token repository scope has the wrong short name")
        full_name = repository.get("full_name")
        require(full_name == PROPOSAL_APP_REPOSITORY_FULL_NAME, "GitHub App token repository scope is not canonical Effigy")
        owner = repository.get("owner")
        if owner is not None:
            require(isinstance(owner, dict), "GitHub App token repository owner is malformed")
            require(owner.get("login") == PROPOSAL_APP_REPOSITORY_OWNER, "GitHub App token repository owner is not canonical")
        full_names.append(full_name)
    require(full_names == [PROPOSAL_APP_REPOSITORY_FULL_NAME], f"GitHub App token is scoped to {full_names}, not canonical Effigy alone")
    return {
        "token": "redacted",
        "expires_at": expires_at,
        "repositories": full_names,
        "repository_full_name": full_names[0],
        "repository_owner": PROPOSAL_APP_REPOSITORY_OWNER,
        "permissions": dict(permissions),
        "short_lived": True,
    }


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _input_command(command: list[str], payload: bytes, environment: Mapping[str, str]) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        command,
        env=dict(environment),
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = decode_output(result.stderr) or decode_output(result.stdout)
        fail(f"command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return result


def mint_installation_token(
    app_id: str,
    installation_id: str,
    private_key_path: Path,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Mint the scoped token used only by the hosted proposal checkpoint."""

    request = app_token_request(app_id, installation_id)
    require(private_key_path.is_file() and not private_key_path.is_symlink(), "GitHub App private key is missing or not a regular file")
    env = dict(os.environ if environment is None else environment)
    openssl = shutil.which("openssl")
    curl = shutil.which("curl")
    require(openssl is not None, "proposal token minting requires openssl")
    require(curl is not None, "proposal token minting requires curl")

    issued_at = int(time.time()) - 60
    header = _base64url(b'{"alg":"RS256","typ":"JWT"}')
    claims = _base64url(
        json.dumps(
            {"iat": issued_at, "exp": issued_at + 540, "iss": str(app_id)},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    signing_input = f"{header}.{claims}".encode("ascii")
    signature = _input_command([openssl, "dgst", "-sha256", "-sign", str(private_key_path)], signing_input, env).stdout
    jwt = f"{header}.{claims}.{_base64url(signature)}"
    body = json.dumps(
        {"permissions": request["permissions"], "repositories": request["repositories"]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    api_root = env.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    result = _input_command(
        [
            curl,
            "-fsS",
            "--retry",
            "2",
            "--max-time",
            "30",
            "-X",
            "POST",
            api_root + request["endpoint"],
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            f"Authorization: Bearer {jwt}",
            "-H",
            "X-GitHub-Api-Version: 2022-11-28",
            "-H",
            "Content-Type: application/json",
            "--data-binary",
            "@-",
        ],
        body,
        env,
    )
    try:
        payload = json.loads(decode_output(result.stdout))
    except json.JSONDecodeError as error:
        fail(f"GitHub App token response is not JSON: {error}")
    require(isinstance(payload, dict), "GitHub App token response is not an object")
    report = validate_app_token_response(payload)
    output = env.get("GITHUB_OUTPUT")
    require(output, "GitHub App token minting requires GITHUB_OUTPUT")
    with open(output, "a", encoding="utf-8") as handle:
        handle.write(f"token={payload['token']}\n")
        handle.write(f"expires_at={payload['expires_at']}\n")
    print(f"::add-mask::{payload['token']}")
    return {**report, "request": request, "network_access": True}
