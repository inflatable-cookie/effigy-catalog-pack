#!/usr/bin/env python3
"""Entry point for the Effigy catalog-pack foundation and publication checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from catalog_pack_authority import prove_import, prove_support, resolve_authority
from catalog_pack_effigy import effigy_smoke
from catalog_pack_hosted import portable_authority_check, workflow_check
from catalog_pack_oci import build_oci_layout, deterministic_oci_proof, prepare_layout_output
from catalog_pack_policy import prove_support_releases
from catalog_pack_publication import no_push_rehearsal
from catalog_pack_publication_tests import publication_check
from catalog_pack_provider import live_provider_check
from catalog_pack_registry import FakeRegistry
from catalog_pack_shared import (
    CheckFailure,
    PACK_ROOT,
    require,
    validate_pack_tree,
)
from catalog_pack_transaction import run_publication


def validate_command(args: argparse.Namespace) -> dict[str, Any]:
    pack_facts = validate_pack_tree()
    authority = resolve_authority(args.effigy_root)
    support_facts = prove_support(authority, args.require_authority)
    result = {**pack_facts, **support_facts}
    if getattr(args, "import_proof", False):
        result["import"] = prove_import(authority)
    return result


def test_command(args: argparse.Namespace) -> dict[str, Any]:
    validation = validate_command(
        argparse.Namespace(effigy_root=args.effigy_root, require_authority=True, import_proof=False)
    )
    oci = deterministic_oci_proof()
    rehearsal = no_push_rehearsal()
    workflows = workflow_check()
    portable = portable_authority_check()
    authority = resolve_authority(args.effigy_root)
    publication = publication_check(authority, True)
    smoke = effigy_smoke(authority, args.effigy_bin)
    return {
        "validation": validation,
        "oci": oci,
        "rehearsal": rehearsal,
        "workflows": workflows,
        "portable": portable,
        "publication": publication,
        "effigy": smoke,
    }


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


def support_releases_command(args: argparse.Namespace) -> dict[str, Any]:
    authority = resolve_authority(args.effigy_root)
    support = prove_support(authority, True)
    return {"support": support, "releases": prove_support_releases(support)}


def publish_command(args: argparse.Namespace) -> dict[str, Any]:
    authority = resolve_authority(args.effigy_root)
    if args.mutate:
        require(
            args.phase in {"version", "finalize-preflight", "finalize"},
            "live publication requires --phase version, finalize-preflight, or finalize",
        )
        from catalog_pack_live import LiveRegistry

        adapter: Any = LiveRegistry()
    else:
        adapter = FakeRegistry()
    return run_publication(
        authority=authority,
        source_tag=args.source_tag,
        source_ref=args.source_ref,
        adapter=adapter,
        mutate=args.mutate,
        phase=args.phase or "version",
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "inventory",
            "validate",
            "import-proof",
            "oci-layout",
            "rehearse",
            "workflow-check",
            "provider-controls",
            "portable-check",
            "support-releases",
            "publication-check",
            "publish",
            "effigy-smoke",
            "test",
        ),
    )
    parser.add_argument("--effigy-root", help="read-only Effigy authority checkout")
    parser.add_argument("--effigy-bin", help="Effigy binary to use for the local smoke test")
    parser.add_argument("--require-authority", action="store_true", help="fail if the Effigy checkout is absent")
    parser.add_argument("--source-tag", help="existing annotated source tag for publication")
    parser.add_argument("--source-ref", help="full peeled pack commit for publication")
    parser.add_argument("--output", help="OCI layout destination for oci-layout")
    parser.add_argument("--mutate", action="store_true", help="perform live publication writes (protected job only)")
    parser.add_argument(
        "--phase",
        choices=("version", "finalize-preflight", "finalize"),
        help="protected publication phase",
    )
    args = parser.parse_args(argv)

    try:
        if args.command == "inventory":
            result = validate_pack_tree()
        elif args.command == "validate":
            result = validate_command(args)
        elif args.command == "import-proof":
            args.require_authority = True
            args.import_proof = True
            result = validate_command(args)
        elif args.command == "oci-layout":
            result = oci_command(args)
        elif args.command == "rehearse":
            validate_command(args)
            result = no_push_rehearsal(args.source_tag, args.source_ref)
        elif args.command == "workflow-check":
            result = workflow_check()
        elif args.command == "provider-controls":
            result = live_provider_check()
        elif args.command == "portable-check":
            result = portable_authority_check()
        elif args.command == "support-releases":
            result = support_releases_command(args)
        elif args.command == "publication-check":
            result = publication_check(resolve_authority(args.effigy_root), args.require_authority)
        elif args.command == "publish":
            result = publish_command(args)
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
