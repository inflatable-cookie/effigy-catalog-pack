#!/usr/bin/env python3
"""Focused compatibility and current-support proof for the canonical pack."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any

from catalog_pack_authority import resolve_authority
from catalog_pack_policy import parse_support_policy, prove_current_support, version_admitted
from catalog_pack_shared import CheckFailure, fail, require, validate_pack_tree


EXPECTED_COMPATIBILITY = ">=0.13, <0.15"
ADMITTED_VERSIONS = ("0.13.0", "0.13.1", "0.14.0", "0.14.1")
REJECTED_VERSIONS = ("0.12.0", "0.15.0")


def expect_failure(label: str, check: Callable[[], Any], expected: str) -> None:
    try:
        check()
    except CheckFailure as error:
        require(expected in str(error), f"{label} failed with an unexpected reason: {error}")
        return
    fail(f"{label} was accepted")


def compatibility_check() -> dict[str, Any]:
    facts = validate_pack_tree()
    compatibility = facts["effigy_compatibility"]
    require(
        compatibility == EXPECTED_COMPATIBILITY,
        f"pack compatibility is {compatibility}, expected {EXPECTED_COMPATIBILITY}",
    )
    for version in ADMITTED_VERSIONS:
        require(version_admitted(version, compatibility), f"pack compatibility does not admit Effigy {version}")
    for version in REJECTED_VERSIONS:
        require(not version_admitted(version, compatibility), f"pack compatibility unexpectedly admits Effigy {version}")

    authority = resolve_authority(None)
    support = prove_current_support(authority, True, compatibility)
    current_release = support["effigy_workspace_release"]
    valid_policy = {
        "schema_version": 1,
        "as_of_release": current_release,
        "required_versions": support["support_required_versions"],
        "oldest_update_capable_release": support["support_oldest_update_capable_release"],
    }
    parse_support_policy(valid_policy, current_release)

    negative_controls = (
        (
            "wrong schema",
            {**valid_policy, "schema_version": 2},
            "schema_version is not 1",
        ),
        (
            "stale support release",
            {**valid_policy, "as_of_release": "0.12.0"},
            f"as_of_release is 0.12.0, but the Effigy workspace release is {current_release}",
        ),
        (
            "wrong support floor",
            {**valid_policy, "oldest_update_capable_release": "0.13.1"},
            "oldest_update_capable_release is 0.13.1",
        ),
        (
            "missing required current release",
            {**valid_policy, "required_versions": ["0.13.0", "0.13.1"]},
            f"required_versions does not include the current Effigy release {current_release}",
        ),
    )
    for label, document, expected in negative_controls:
        expect_failure(
            label,
            lambda document=document: parse_support_policy(document, current_release),
            expected,
        )

    expect_failure(
        "previous upper bound",
        lambda: prove_current_support(authority, True, ">=0.13, <0.14"),
        "does not admit required Effigy",
    )

    return {
        "pack_version": facts["pack_version"],
        "pack_compatibility": compatibility,
        "pack_content_id": facts["content_id"],
        "admitted_versions": list(ADMITTED_VERSIONS),
        "rejected_versions": list(REJECTED_VERSIONS),
        "support": support,
        "support_negative_controls": [label for label, _, _ in negative_controls]
        + ["previous upper bound"],
        "network_access": False,
    }


def main() -> int:
    try:
        print(json.dumps(compatibility_check(), indent=2, sort_keys=True))
    except (CheckFailure, OSError, ValueError) as error:
        print(f"[error] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
