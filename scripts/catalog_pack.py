#!/usr/bin/env python3
"""Entry point for the Effigy catalog-pack foundation checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from catalog_pack_authority import prove_authority, resolve_authority
from catalog_pack_effigy import effigy_smoke, workflow_check
from catalog_pack_oci import build_oci_layout, deterministic_oci_proof, no_push_rehearsal, prepare_layout_output
from catalog_pack_shared import (
    CheckFailure,
    PACK_ROOT,
    validate_pack_tree,
)


def validate_command(args: argparse.Namespace) -> dict[str, Any]:
    pack_facts = validate_pack_tree()
    authority = resolve_authority(args.effigy_root)
    authority_facts = prove_authority(authority, args.require_authority)
    return {**pack_facts, **authority_facts}


def test_command(args: argparse.Namespace) -> dict[str, Any]:
    validation = validate_command(argparse.Namespace(effigy_root=args.effigy_root, require_authority=True))
    oci = deterministic_oci_proof()
    rehearsal = no_push_rehearsal()
    workflows = workflow_check()
    authority = resolve_authority(args.effigy_root)
    smoke = effigy_smoke(authority, args.effigy_bin)
    return {"validation": validation, "oci": oci, "rehearsal": rehearsal, "workflows": workflows, "effigy": smoke}


def oci_command(args: argparse.Namespace) -> dict[str, Any]:
    validate_pack_tree()
    output = Path(args.output) if args.output else None
    if output is None:
        output = PACK_ROOT.parent / ".effigy" / "oci-layout"
    if not output.is_absolute():
        output = PACK_ROOT.parent / output
    prepare_layout_output(output)
    report = build_oci_layout(output)
    report["output"] = str(output)
    return report


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("inventory", "validate", "oci-layout", "rehearse", "workflow-check", "effigy-smoke", "test"),
    )
    parser.add_argument("--effigy-root", help="read-only Effigy authority checkout")
    parser.add_argument("--effigy-bin", help="Effigy binary to use for the local smoke test")
    parser.add_argument("--require-authority", action="store_true", help="fail if the pinned Effigy checkout is absent")
    parser.add_argument("--output", help="OCI layout destination for oci-layout")
    args = parser.parse_args(argv)

    try:
        if args.command == "inventory":
            result = validate_pack_tree()
        elif args.command == "validate":
            result = validate_command(args)
        elif args.command == "oci-layout":
            result = oci_command(args)
        elif args.command == "rehearse":
            validate_command(args)
            result = no_push_rehearsal()
        elif args.command == "workflow-check":
            result = workflow_check()
        elif args.command == "effigy-smoke":
            result = effigy_smoke(resolve_authority(args.effigy_root), args.effigy_bin)
        else:
            result = test_command(args)
    except (CheckFailure, OSError, json.JSONDecodeError) as error:
        print(f"[error] {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
