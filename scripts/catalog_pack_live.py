"""Live GHCR/GitHub adapter. Ordinary QA must not import this path for writes."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from catalog_pack_registry import require_live_mutation_gate
from catalog_pack_shared import *

CommandRunner = Callable[..., subprocess.CompletedProcess[bytes]]

_AUTH_MARKERS = (
    "unauthorized",
    "authentication required",
    "access denied",
    "permission denied",
    "forbidden",
)
_ABSENT_MARKERS = (
    "not found",
    "notfound",
    "manifest unknown",
    "name unknown",
    "unknown to registry",
)
_AUTH_STATUS = re.compile(r"\b(401|403)\b")
_ABSENT_STATUS = re.compile(r"\b404\b")


def classify_registry_inspect(returncode: int, stdout: str, stderr: str) -> str:
    """Classify a remote inspect. Only a proved not-found is absent; everything else fails closed."""

    if returncode == 0:
        return "present"
    text = f"{stderr}\n{stdout}".lower()
    if any(marker in text for marker in _AUTH_MARKERS) or _AUTH_STATUS.search(text):
        return "error"
    if any(marker in text for marker in _ABSENT_MARKERS) or _ABSENT_STATUS.search(text):
        return "absent"
    return "error"


def default_command_runner(
    argv: list[str],
    *,
    env: Mapping[str, str] | None = None,
    cwd: str | Path | None = None,
    input: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    cwd_path = Path(cwd) if cwd is not None else None
    env_map = dict(env) if env is not None else None
    if input is None:
        return run_command(list(argv), cwd=cwd_path, env=env_map, check=check)
    result = subprocess.run(
        list(argv),
        cwd=cwd_path,
        env=env_map,
        input=input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        detail = decode_output(result.stderr) or decode_output(result.stdout)
        fail(f"command failed ({result.returncode}): {' '.join(argv)}\n{detail}")
    return result


class LiveRegistry:
    """ORAS/GitHub adapter used only by the protected publication jobs."""

    requires_live_gate = True

    def __init__(
        self,
        environment: Mapping[str, str] | None = None,
        *,
        runner: CommandRunner | None = None,
        which: Callable[[str], str | None] | None = None,
    ) -> None:
        self.env = dict(os.environ if environment is None else environment)
        self.writes: list[tuple[str, str | None]] = []
        self.runner = runner or default_command_runner
        locate = which or shutil.which
        self.oras = locate("oras")
        self.gh = locate("gh")
        self._logged_in = False
        require(self.oras is not None, "live publication requires oras")
        require(self.gh is not None, "live publication requires gh")

    def inspect_version(self, tag: str) -> str | None:
        return self._inspect_ref(f"{OCI_REPOSITORY}:{tag}")

    def inspect_stable(self) -> str | None:
        return self._inspect_ref(f"{OCI_REPOSITORY}:{STABLE_TAG}")

    def _inspect_ref(self, reference: str) -> str | None:
        result = self.runner(
            [self.oras, "manifest", "fetch", "--descriptor", reference],
            check=False,
            env=self._auth_env(),
        )
        stdout = decode_output(result.stdout)
        stderr = decode_output(result.stderr)
        status = classify_registry_inspect(result.returncode, stdout, stderr)
        if status == "absent":
            return None
        if status != "present":
            fail(f"registry inspect failed for {reference}: {stderr or stdout}")
        try:
            descriptor = json.loads(stdout)
        except json.JSONDecodeError as error:
            fail(f"registry descriptor is not JSON for {reference}: {error}")
        digest = descriptor.get("digest")
        require(isinstance(digest, str) and digest.startswith("sha256:"), f"registry descriptor lacks a digest: {reference}")
        return digest

    def push_version(self, layout: Path, tag: str, digest: str) -> None:
        require_live_mutation_gate(self.env)
        self.writes.append(("package-version", digest))
        self.runner(
            [self.oras, "cp", "--from-oci-layout", f"{layout}:{tag}", f"{OCI_REPOSITORY}:{tag}"],
            env=self._auth_env(),
        )
        observed = self.inspect_version(tag)
        require(observed == digest, f"pushed version pointer is {observed}, expected {digest}")

    def package_state(self) -> dict[str, Any]:
        result = self.runner(
            [self.gh, "api", "--method", "GET", PACKAGE_METADATA_PATH],
            check=False,
            env=self._auth_env(),
        )
        if result.returncode != 0:
            detail = decode_output(result.stderr) or decode_output(result.stdout)
            fail(f"package metadata GET failed: {detail}")
        payload = json.loads(decode_output(result.stdout))
        repository = None
        repo = payload.get("repository")
        if isinstance(repo, dict):
            repository = repo.get("full_name")
        return {"visibility": payload.get("visibility"), "repository": repository, "name": payload.get("name")}

    def verify_attestation(self, digest: str) -> None:
        result = self.runner(
            [
                self.gh,
                "attestation",
                "verify",
                f"oci://{OCI_REPOSITORY}@{digest}",
                "--repo",
                PACK_GITHUB_REPOSITORY,
                "--predicate-type",
                SLSA_PROVENANCE_PREDICATE,
            ],
            check=False,
            env=self._auth_env(),
        )
        if result.returncode != 0:
            listed = self.runner(
                [self.gh, "api", "--method", "GET", f"repos/{PACK_GITHUB_REPOSITORY}/attestations/{digest}"],
                check=False,
                env=self._auth_env(),
            )
            detail = decode_output(result.stderr) or decode_output(listed.stderr)
            fail(f"digest-bound attestation did not verify for {digest}: {detail}")

    def anonymous_pull(self, digest: str, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-anon-") as temporary:
            home = Path(temporary)
            docker = home / ".docker"
            docker.mkdir()
            (docker / "config.json").write_text("{}\n", encoding="utf-8")
            env = {
                "HOME": str(home),
                "DOCKER_CONFIG": str(docker),
                "PATH": self.env.get("PATH", ""),
                "LANG": self.env.get("LANG", "C"),
            }
            result = self.runner(
                [self.oras, "pull", f"{OCI_REPOSITORY}@{digest}", "--output", str(destination), "--no-tty"],
                check=False,
                env=env,
            )
            if result.returncode != 0:
                fail(f"anonymous digest pull failed: {decode_output(result.stderr)}")

    def tag_digest(self, digest: str, tag: str) -> None:
        require_live_mutation_gate(self.env)
        if tag == STABLE_TAG:
            self.writes.append(("stable", digest))
        else:
            fail(f"unexpected live tag write: {tag}")
        self.runner([self.oras, "tag", f"{OCI_REPOSITORY}@{digest}", tag], env=self._auth_env())

    def refresh_support_authority(self, authority: Path | None) -> None:
        require(authority is not None, "finalize requires the Effigy authority checkout to refresh")
        result = self.runner(
            [
                "git",
                "-C",
                str(authority),
                "fetch",
                "--prune",
                "--depth",
                "1",
                "origin",
                "+refs/heads/main:refs/remotes/origin/main",
            ],
            check=False,
            env=self.env,
        )
        if result.returncode != 0:
            fail(f"Effigy default-branch refresh failed: {decode_output(result.stderr)}")

    def _auth_env(self) -> dict[str, str]:
        env = dict(self.env)
        token = env.get("GITHUB_TOKEN") or env.get("GH_TOKEN")
        require(bool(token), "live publication requires GITHUB_TOKEN")
        env.setdefault("GITHUB_TOKEN", str(token))
        env.setdefault("GH_TOKEN", str(token))
        if not self._logged_in:
            actor = env.get("GITHUB_ACTOR") or "x-access-token"
            result = self.runner(
                [self.oras, "login", "ghcr.io", "-u", actor, "--password-stdin"],
                input=(str(token) + "\n").encode("utf-8"),
                env=env,
                check=False,
            )
            if result.returncode != 0:
                fail(f"oras login failed: {decode_output(result.stderr)}")
            self._logged_in = True
        return env
