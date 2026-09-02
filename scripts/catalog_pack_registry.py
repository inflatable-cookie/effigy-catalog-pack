"""Registry adapters for catalog-pack publication. Live writes stay behind the mutate gate."""

from __future__ import annotations

from typing import Any, Mapping

from catalog_pack_shared import *


def require_live_mutation_gate(environment: Mapping[str, str] | None = None) -> None:
    env = os.environ if environment is None else environment
    require(env.get("GITHUB_ACTIONS") == "true", "live publication writes require GitHub Actions")
    require(
        env.get("GITHUB_EVENT_NAME") == "workflow_dispatch",
        "live publication writes require workflow_dispatch",
    )
    require(
        env.get("GITHUB_REPOSITORY") == PACK_GITHUB_REPOSITORY,
        "live publication writes are limited to the pack repository",
    )
    require(
        env.get("GITHUB_ENVIRONMENT") == PUBLICATION_ENVIRONMENT,
        f"live publication writes require the {PUBLICATION_ENVIRONMENT} environment",
    )
    require(
        env.get(PUBLICATION_MUTATE_ENV) == "1",
        f"live publication writes require {PUBLICATION_MUTATE_ENV}=1",
    )


class FakeRegistry:
    """In-memory GHCR/package/attestation stand-in. Ordinary QA uses only this."""

    def __init__(
        self,
        *,
        version_digest: str | None = None,
        stable_digest: str | None = None,
        visibility: str = "private",
        repository: str | None = None,
        attested: set[str] | None = None,
        pack_root: Path = PACK_ROOT,
    ) -> None:
        self.version_digest = version_digest
        self.stable_digest = stable_digest
        self.visibility = visibility
        self.repository = repository
        self.attested = set(attested or ())
        self.pack_root = pack_root
        self.writes: list[tuple[str, str | None]] = []
        self.authenticated_pulls = 0
        self.anonymous_pulls = 0

    def inspect_version(self, tag: str) -> str | None:
        require(tag.startswith("v"), f"version tag is not a version pointer: {tag}")
        return self.version_digest

    def inspect_stable(self) -> str | None:
        return self.stable_digest

    def push_version(self, layout: Path, tag: str, digest: str) -> None:
        self.writes.append(("package-version", digest))
        self.version_digest = digest
        if self.repository is None:
            self.repository = PACK_GITHUB_REPOSITORY

    def set_public(self) -> None:
        self.writes.append(("visibility", "public"))
        self.visibility = "public"
        self.repository = PACK_GITHUB_REPOSITORY

    def package_state(self) -> dict[str, Any]:
        return {"visibility": self.visibility, "repository": self.repository}

    def attest(self, digest: str, subject_name: str) -> None:
        require(subject_name == OCI_REPOSITORY, f"attestation subject is {subject_name}")
        self.writes.append(("attestation", digest))
        self.attested.add(digest)

    def verify_attestation(self, digest: str) -> None:
        require(digest in self.attested, f"no digest-bound attestation for {digest}")

    def anonymous_pull(self, digest: str, destination: Path) -> None:
        require(self.visibility == "public", "anonymous pull requires public package visibility")
        self.anonymous_pulls += 1
        shutil.copytree(self.pack_root, destination, dirs_exist_ok=True)

    def tag_digest(self, digest: str, tag: str) -> None:
        if tag == STABLE_TAG:
            self.writes.append(("stable", digest))
            self.stable_digest = digest
            return
        fail(f"unexpected live tag write: {tag}")

    def untag(self, tag: str) -> None:
        require(tag == STABLE_TAG, f"refusing to untag {tag}")
        self.writes.append(("stable-rollback", self.stable_digest))
        self.stable_digest = None
