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
from catalog_pack_proposal import (
    mint_installation_token,
    proposal_attestation_check,
    proposal_body,
    proposal_branch,
    proposal_evidence_path,
    proposal_model_check,
    materialize_candidate,
    verify_pulled_artifact,
    verify_proposal,
)
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
    proposal = proposal_model_check()
    smoke = effigy_smoke(authority, args.effigy_bin)
    return {
        "validation": validation,
        "oci": oci,
        "rehearsal": rehearsal,
        "workflows": workflows,
        "portable": portable,
        "publication": publication,
        "proposal": proposal,
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


def proposal_artifact_args(args: argparse.Namespace) -> dict[str, Any]:
    require(args.artifact_root is not None, "proposal artifact root is required")
    require(args.artifact_manifest is not None, "proposal artifact manifest is required")
    require(args.artifact_descriptor is not None, "proposal artifact descriptor is required")
    require(args.artifact_digest is not None, "proposal artifact digest is required")
    return {
        "artifact_root": Path(args.artifact_root),
        "manifest_path": Path(args.artifact_manifest),
        "artifact_digest": args.artifact_digest,
        "descriptor_path": Path(args.artifact_descriptor),
    }


def proposal_body_command(args: argparse.Namespace) -> dict[str, Any]:
    artifact_args = proposal_artifact_args(args)
    artifact = verify_pulled_artifact(**artifact_args)
    artifact["evidence_path"] = proposal_evidence_path(artifact["source_identity"]["source_created"]).as_posix()
    body = proposal_body(artifact)
    require(args.output is not None, "proposal body output is required")
    output = Path(args.output)
    output.write_text(body, encoding="utf-8")
    return {"output": str(output), "bytes": len(body.encode("utf-8")), "network_access": False}


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
            "proposal-check",
            "proposal-artifact-check",
            "proposal-prepare",
            "proposal-verify",
            "proposal-attestation",
            "proposal-token",
            "proposal-branch",
            "proposal-body",
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
    parser.add_argument("--artifact-root", help="pulled artifact pack root for proposal checks")
    parser.add_argument("--artifact-manifest", help="JSON manifest fetched for the artifact digest")
    parser.add_argument("--artifact-descriptor", help="JSON registry descriptor for the artifact digest")
    parser.add_argument("--artifact-digest", help="immutable sha256 artifact digest")
    parser.add_argument("--app-id", help="GitHub App id for the hosted proposal token")
    parser.add_argument("--installation-id", help="GitHub App installation id for the hosted proposal token")
    parser.add_argument("--private-key-file", help="GitHub App private key file for the hosted proposal token")
    parser.add_argument("--offline", action="store_true", help="run the Effigy verifier with Cargo offline")
    parser.add_argument("--skip-effigy-verifier", action="store_true", help="skip only the model-only Effigy verifier seam")
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
        elif args.command == "proposal-check":
            result = proposal_model_check()
        elif args.command == "proposal-artifact-check":
            result = verify_pulled_artifact(**proposal_artifact_args(args))
        elif args.command == "proposal-prepare":
            require(args.effigy_root is not None, "proposal Effigy checkout is required")
            result = materialize_candidate(Path(args.effigy_root), **proposal_artifact_args(args))
        elif args.command == "proposal-verify":
            require(args.effigy_root is not None, "proposal Effigy checkout is required")
            artifact_args = proposal_artifact_args(args)
            result = verify_proposal(
                Path(args.effigy_root),
                **artifact_args,
                run_verifier=not args.skip_effigy_verifier,
                offline=args.offline,
            )
        elif args.command == "proposal-attestation":
            require(args.output is not None, "attestation output is required")
            require(args.artifact_digest is not None, "proposal artifact digest is required")
            result = proposal_attestation_check(Path(args.output), args.artifact_digest)
        elif args.command == "proposal-token":
            require(args.app_id is not None, "GitHub App id is required")
            require(args.installation_id is not None, "GitHub App installation id is required")
            require(args.private_key_file is not None, "GitHub App private key file is required")
            result = mint_installation_token(
                args.app_id,
                args.installation_id,
                Path(args.private_key_file),
            )
        elif args.command == "proposal-branch":
            require(args.artifact_digest is not None, "proposal artifact digest is required")
            result = {"branch": proposal_branch(args.artifact_digest), "network_access": False}
        elif args.command == "proposal-body":
            result = proposal_body_command(args)
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
