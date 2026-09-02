"""Live GHCR/GitHub adapter. Ordinary QA must not import this path for writes."""

from __future__ import annotations

from typing import Any, Mapping

from catalog_pack_policy import git_blob_oid
from catalog_pack_registry import require_live_mutation_gate
from catalog_pack_shared import *


class LiveRegistry:
    """ORAS/GitHub adapter used only by the protected publication job."""

    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self.env = dict(os.environ if environment is None else environment)
        self.writes: list[tuple[str, str | None]] = []
        self.oras = shutil.which("oras")
        self.gh = shutil.which("gh")
        self.node = shutil.which("node")
        self._logged_in = False
        require(self.oras is not None, "live publication requires oras")
        require(self.gh is not None, "live publication requires gh")

    def inspect_version(self, tag: str) -> str | None:
        return self._inspect_ref(f"{OCI_REPOSITORY}:{tag}")

    def inspect_stable(self) -> str | None:
        return self._inspect_ref(f"{OCI_REPOSITORY}:{STABLE_TAG}")

    def _inspect_ref(self, reference: str) -> str | None:
        result = run_command(
            [self.oras, "manifest", "fetch", "--descriptor", reference],
            check=False,
            env=self._auth_env(),
        )
        if result.returncode != 0:
            return None
        try:
            descriptor = json.loads(decode_output(result.stdout))
        except json.JSONDecodeError as error:
            fail(f"registry descriptor is not JSON for {reference}: {error}")
        digest = descriptor.get("digest")
        require(isinstance(digest, str) and digest.startswith("sha256:"), f"registry descriptor lacks a digest: {reference}")
        return digest

    def push_version(self, layout: Path, tag: str, digest: str) -> None:
        require_live_mutation_gate(self.env)
        self.writes.append(("package-version", digest))
        run_command(
            [self.oras, "cp", "--from-oci-layout", f"{layout}:{tag}", f"{OCI_REPOSITORY}:{tag}"],
            env=self._auth_env(),
        )
        observed = self.inspect_version(tag)
        require(observed == digest, f"pushed version pointer is {observed}, expected {digest}")

    def set_public(self) -> None:
        require_live_mutation_gate(self.env)
        self.writes.append(("visibility", "public"))
        path = "users/inflatable-cookie/packages/container/effigy-catalog-pack"
        result = subprocess.run(
            [self.gh, "api", "--method", "PATCH", path, "--input", "-"],
            input=b'{"visibility":"public"}\n',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=self._auth_env(),
        )
        if result.returncode != 0:
            detail = decode_output(result.stderr) or decode_output(result.stdout)
            fail(f"package visibility PATCH failed: {detail}")
        state = self.package_state()
        require(state["visibility"] == "public", f"package visibility is {state['visibility']}, expected public")

    def package_state(self) -> dict[str, Any]:
        path = "users/inflatable-cookie/packages/container/effigy-catalog-pack"
        result = run_command([self.gh, "api", "--method", "GET", path], check=False, env=self._auth_env())
        if result.returncode != 0:
            detail = decode_output(result.stderr) or decode_output(result.stdout)
            fail(f"package metadata GET failed: {detail}")
        payload = json.loads(decode_output(result.stdout))
        repository = None
        repo = payload.get("repository")
        if isinstance(repo, dict):
            repository = repo.get("full_name")
        return {"visibility": payload.get("visibility"), "repository": repository, "name": payload.get("name")}

    def attest(self, digest: str, subject_name: str) -> None:
        require_live_mutation_gate(self.env)
        require(subject_name == OCI_REPOSITORY, f"attestation subject is {subject_name}")
        require(self.node is not None, "live attestation requires node")
        self.writes.append(("attestation", digest))
        with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-attest-") as temporary:
            root = Path(temporary)
            archive = root / "attest.tar.gz"
            run_command(
                [
                    "curl",
                    "-fsSL",
                    "-o",
                    str(archive),
                    f"https://github.com/actions/attest/archive/{ATTEST_ACTION_COMMIT}.tar.gz",
                ]
            )
            extracted = root / "src"
            extracted.mkdir()
            run_command(["tar", "-xzf", str(archive), "-C", str(extracted), "--strip-components=1"])
            dist = extracted / "dist" / "index.js"
            require(dist.is_file(), "pinned actions/attest dist/index.js is missing")
            blob = git_blob_oid(dist.read_bytes())
            require(blob == ATTEST_DIST_GIT_BLOB, f"actions/attest dist blob is {blob}, expected {ATTEST_DIST_GIT_BLOB}")
            github_output = root / "github-output"
            github_output.write_text("", encoding="utf-8")
            env = self._auth_env()
            env.update(
                {
                    "INPUT_SUBJECT_DIGEST": digest,
                    "INPUT_SUBJECT_NAME": subject_name,
                    "INPUT_PUSH_TO_REGISTRY": "true",
                    "INPUT_SHOW_SUMMARY": "false",
                    "INPUT_GITHUB_TOKEN": env.get("GITHUB_TOKEN", ""),
                    "GITHUB_OUTPUT": str(github_output),
                    "GITHUB_ACTION_PATH": str(extracted),
                }
            )
            run_command([self.node, str(dist)], cwd=extracted, env=env)

    def verify_attestation(self, digest: str) -> None:
        result = run_command(
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
            listed = run_command(
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
            result = run_command(
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
        run_command([self.oras, "tag", f"{OCI_REPOSITORY}@{digest}", tag], env=self._auth_env())

    def untag(self, tag: str) -> None:
        require_live_mutation_gate(self.env)
        require(tag == STABLE_TAG, f"refusing to untag {tag}")
        previous = self.inspect_stable()
        self.writes.append(("stable-rollback", previous))
        result = run_command(
            [self.oras, "manifest", "delete", f"{OCI_REPOSITORY}:{tag}"],
            check=False,
            env=self._auth_env(),
        )
        if result.returncode != 0:
            fail(f"failed to roll back {tag}: {decode_output(result.stderr)}")

    def _auth_env(self) -> dict[str, str]:
        env = dict(self.env)
        token = env.get("GITHUB_TOKEN") or env.get("GH_TOKEN")
        require(bool(token), "live publication requires GITHUB_TOKEN")
        if not self._logged_in:
            actor = env.get("GITHUB_ACTOR") or "x-access-token"
            result = subprocess.run(
                [self.oras, "login", "ghcr.io", "-u", actor, "--password-stdin"],
                input=(str(token) + "\n").encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                env=env,
            )
            if result.returncode != 0:
                fail(f"oras login failed: {decode_output(result.stderr)}")
            self._logged_in = True
        return env
