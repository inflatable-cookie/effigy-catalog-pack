"""Previous-target retag and version-drift proofs for finalize."""

from __future__ import annotations

from typing import Any, Callable

from catalog_pack_registry import FakeRegistry
from catalog_pack_shared import *


def retag_and_drift_proof(created: dict[str, Any], run_phase: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    previous = "sha256:" + "e" * 64
    digest = created["candidate_digest"]
    support = created["support"]
    retag = FakeRegistry(
        version_digest=digest,
        stable_digest=previous,
        visibility="public",
        repository=PACK_GITHUB_REPOSITORY,
        attested={digest},
    )
    moved = run_phase(retag, "finalize", expected_support=support)
    require(moved["rollback_exercised"] is True, "existing stable skipped live retag rollback")
    require(
        [entry for entry in retag.writes if entry[0] == "stable"]
        == [("stable", digest), ("stable", previous), ("stable", digest)],
        "retag rollback was not candidate then previous then candidate",
    )
    require(retag.inspect_stable() == digest, "retag rollback did not restore the candidate")
    require(retag.inspect_version("v1.0.1") == digest, "retag rollback moved the version pointer")

    class DriftingVersion(FakeRegistry):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self.version_inspects = 0

        def inspect_version(self, tag: str) -> str | None:
            self.version_inspects += 1
            if self.version_inspects > 1:
                return "sha256:" + "f" * 64
            return super().inspect_version(tag)

    drifted = DriftingVersion(
        version_digest=digest,
        visibility="public",
        repository=PACK_GITHUB_REPOSITORY,
        attested={digest},
    )
    try:
        run_phase(drifted, "finalize", expected_support=support)
    except CheckFailure as error:
        require("version pointer drifted before stable write" in str(error), str(error))
    else:
        fail("version pointer drift was accepted after a stable write")
    require(drifted.writes == [], "version pointer drift mutated stable")

    class SkipStableApply(FakeRegistry):
        def __init__(self, skip_index: int, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self.skip_index = skip_index
            self.stable_writes = 0

        def tag_digest(self, digest_value: str, tag: str) -> None:
            if tag != STABLE_TAG:
                fail(f"unexpected live tag write: {tag}")
            self.writes.append(("stable", digest_value))
            self.stable_writes += 1
            if self.stable_writes - 1 == self.skip_index:
                return
            self.stable_digest = digest_value

    def adapter(skip_index: int) -> SkipStableApply:
        return SkipStableApply(
            skip_index,
            version_digest=digest,
            stable_digest=previous,
            visibility="public",
            repository=PACK_GITHUB_REPOSITORY,
            attested={digest},
        )

    promote_fail = adapter(0)
    try:
        run_phase(promote_fail, "finalize", expected_support=support)
    except CheckFailure as error:
        require("retag did not promote the candidate" in str(error), str(error))
    else:
        fail("failed candidate promotion was accepted")
    require(promote_fail.inspect_stable() == previous, "failed promotion moved stable")
    require(promote_fail.writes == [("stable", digest)], "failed promotion write set drifted")

    rollback_fail = adapter(1)
    try:
        run_phase(rollback_fail, "finalize", expected_support=support)
    except CheckFailure as error:
        require("rollback did not restore the previous stable digest" in str(error), str(error))
    else:
        fail("failed previous-target rollback was accepted")
    require(rollback_fail.inspect_stable() == digest, "failed rollback left stable off the candidate")
    require(
        [entry for entry in rollback_fail.writes if entry[0] == "stable"] == [("stable", digest), ("stable", previous)],
        "failed rollback write set drifted",
    )

    restore_fail = adapter(2)
    try:
        run_phase(restore_fail, "finalize", expected_support=support)
    except CheckFailure as error:
        require("stable does not resolve to the candidate digest" in str(error), str(error))
    else:
        fail("failed candidate restore was accepted")
    require(restore_fail.inspect_stable() == previous, "failed restore did not remain on the previous digest")
    require(restore_fail.inspect_version("v1.0.1") == digest, "failed restore changed the version pointer")
    return {
        "retag_candidate_previous_candidate": True,
        "version_drift_before_stable": True,
        "retag_edge_failures": True,
    }
