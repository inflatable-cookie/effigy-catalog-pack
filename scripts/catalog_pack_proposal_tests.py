"""Named network-free proofs for the generated-baseline proposal lane."""

from __future__ import annotations

from catalog_pack_oci import build_oci_layout, materialize_oci_layers, read_layout_manifest
from catalog_pack_proposal import *
from catalog_pack_publication import planned_source_identity


def _expect_failure(action: Any, label: str) -> None:
    try:
        action()
    except CheckFailure:
        return
    fail(f"{label} was accepted")


def generated_only_path_allowlist_proof() -> dict[str, Any]:
    evidence = "docs/logs/2026-09/02-114910-catalog-pack-generated-baseline-proposal.md"
    valid = [
        "crates/effigy-catalog/catalog/pack.toml",
        "crates/effigy-catalog/catalog/postgres/service.toml",
        PROPOSAL_BASELINE_LOCK,
        evidence,
    ]
    validate_proposal_paths(valid, evidence)
    _expect_failure(
        lambda: validate_proposal_paths(valid + ["crates/effigy-catalog/src/lib.rs"], evidence),
        "Effigy product-code diff",
    )
    _expect_failure(
        lambda: validate_proposal_paths(valid + [".github/workflows/release.yml"], evidence),
        "Effigy workflow diff",
    )
    _expect_failure(
        lambda: validate_proposal_paths(valid + ["docs/README.md"], evidence),
        "unrelated documentation diff",
    )
    _expect_failure(
        lambda: validate_proposal_paths(valid[:-1], None),
        "incomplete evidence diff",
    )
    _expect_failure(
        lambda: validate_proposal_paths(
            ["crates/effigy-catalog/catalog/../src/lib.rs", PROPOSAL_BASELINE_LOCK, evidence], evidence
        ),
        "traversing proposal path",
    )
    return {
        "valid_generated_paths": True,
        "product_code_rejected": True,
        "workflow_rejected": True,
        "unrelated_docs_rejected": True,
        "incomplete_evidence_rejected": True,
        "traversal_rejected": True,
    }


def immutable_artifact_input_proof() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-proposal-artifact-") as temporary:
        root = Path(temporary)
        layout = root / "layout"
        artifact = root / "artifact"
        identity = planned_source_identity(validate_pack_tree()["pack_version"])
        built = build_oci_layout(layout, PACK_ROOT, identity)
        materialize_oci_layers(layout, artifact)
        _manifest, manifest_bytes, _ = read_layout_manifest(layout)
        descriptor = json.loads((layout / "index.json").read_text(encoding="utf-8"))["manifests"][0]
        manifest_path = root / "manifest.json"
        descriptor_path = root / "descriptor.json"
        manifest_path.write_bytes(manifest_bytes)
        descriptor_path.write_text(json.dumps(descriptor), encoding="utf-8")
        report = verify_pulled_artifact(artifact, manifest_path, built["manifest_digest"], descriptor_path)
        require(report["artifact_verified"] is True, "verified artifact was not accepted")
        require(report["manifest_digest"] == built["manifest_digest"], "artifact digest was not retained")
        require(report["manifest_digest_verified"] is True, "manifest bytes were not hash-bound")
        require(report["descriptor_size_verified"] is True, "manifest bytes were not descriptor-size-bound")

        changed_manifest_bytes = manifest_bytes.replace(b"v1.0.1", b"v1.0.2", 1)
        require(len(changed_manifest_bytes) == len(manifest_bytes), "manifest-change counterexample changed descriptor size")
        manifest_path.write_bytes(changed_manifest_bytes)
        _expect_failure(
            lambda: verify_pulled_artifact(artifact, manifest_path, built["manifest_digest"], descriptor_path),
            "manifest bytes changed with request and descriptor fixed",
        )
        manifest_path.write_bytes(manifest_bytes)

        tampered = artifact / "README.md"
        tampered.write_bytes(tampered.read_bytes() + b"hand edit\n")
        _expect_failure(
            lambda: verify_pulled_artifact(artifact, manifest_path, built["manifest_digest"], descriptor_path),
            "hand-edited artifact",
        )
        tampered.write_bytes((PACK_ROOT / "README.md").read_bytes())

        wrong_descriptor = root / "wrong-descriptor.json"
        wrong_descriptor.write_text(json.dumps({**descriptor, "digest": "sha256:" + "f" * 64}), encoding="utf-8")
        _expect_failure(
            lambda: verify_pulled_artifact(root / "artifact", manifest_path, built["manifest_digest"], wrong_descriptor),
            "descriptor digest mismatch",
        )
    return {
        "digest_required": True,
        "descriptor_bound": True,
        "raw_manifest_hash_verified": True,
        "descriptor_size_verified": True,
        "manifest_change_rejected": True,
        "exact_inventory_verified": True,
        "exact_layer_bytes_verified": True,
        "hand_edit_rejected": True,
    }


def exact_lock_generation_proof() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-proposal-lock-") as temporary:
        root = Path(temporary)
        identity = planned_source_identity(validate_pack_tree()["pack_version"])
        report = {
            **validate_pack_tree(),
            "manifest_digest": "sha256:" + "b" * 64,
            "source_identity": identity,
        }
        first = render_baseline_lock(report, {**identity, "source_repository": PACK_GITHUB_REPOSITORY}, report["manifest_digest"])
        second = render_baseline_lock(report, {**identity, "source_repository": PACK_GITHUB_REPOSITORY}, report["manifest_digest"])
        require(first == second, "repeated lock generation changed bytes")
        parsed = parse_toml(first.decode("utf-8"))
        require(parsed["schema_version"] == 1, "generated lock schema changed")
        require(parsed["baseline"]["source_repository"] == PACK_GITHUB_REPOSITORY, "generated lock source changed")
        require(parsed["identities"]["oci_manifest_digest"] == report["manifest_digest"], "generated lock digest changed")
        require(parsed["identities"]["content_identity"] == report["content_id"], "generated lock content identity changed")
        require(b"GENERATED FILE" in first and b"DO NOT HAND-EDIT" in first, "generated lock marker was lost")
        (root / "first.lock").write_bytes(first)
        (root / "second.lock").write_bytes(second)
        require((root / "first.lock").read_bytes() == (root / "second.lock").read_bytes(), "lock files differ")
    return {"byte_deterministic": True, "typed_fields_complete": True, "generated_marker_present": True}


def candidate_diff_proof() -> dict[str, Any]:
    """Exercise materialisation, status capture, and tamper rejection together."""

    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-proposal-diff-") as temporary:
        root = Path(temporary)
        layout = root / "layout"
        artifact = root / "artifact"
        effigy = root / "effigy"
        identity = planned_source_identity(validate_pack_tree()["pack_version"])
        built = build_oci_layout(layout, PACK_ROOT, identity)
        materialize_oci_layers(layout, artifact)
        _manifest, manifest_bytes, _ = read_layout_manifest(layout)
        descriptor = json.loads((layout / "index.json").read_text(encoding="utf-8"))["manifests"][0]
        manifest_path = root / "manifest.json"
        descriptor_path = root / "descriptor.json"
        manifest_path.write_bytes(manifest_bytes)
        descriptor_path.write_text(json.dumps(descriptor), encoding="utf-8")

        (effigy / "crates/effigy-catalog").mkdir(parents=True)
        (effigy / "README.md").write_text("proposal fixture\n", encoding="utf-8")
        run_command(["git", "-C", str(effigy), "init", "--quiet"])
        run_command(["git", "-C", str(effigy), "config", "user.email", "proposal-test@example.invalid"])
        run_command(["git", "-C", str(effigy), "config", "user.name", "proposal test"])
        run_command(["git", "-C", str(effigy), "add", "."])
        run_command(["git", "-C", str(effigy), "commit", "--quiet", "-m", "fixture"])

        materialize_candidate(effigy, artifact, manifest_path, built["manifest_digest"], descriptor_path)
        verified = verify_generated_only_diff(effigy, artifact, manifest_path, built["manifest_digest"], descriptor_path)
        require(verified["diff_verified"] is True, "candidate diff did not verify")
        (effigy / EFFIGY_SNAPSHOT_ROOT / "README.md").write_bytes(b"hand edited\n")
        _expect_failure(
            lambda: verify_generated_only_diff(effigy, artifact, manifest_path, built["manifest_digest"], descriptor_path),
            "hand-edited candidate snapshot",
        )
        (effigy / EFFIGY_SNAPSHOT_ROOT / "README.md").write_bytes((artifact / "README.md").read_bytes())
        (effigy / "crates/effigy-catalog/src").mkdir(parents=True)
        (effigy / "crates/effigy-catalog/src/lib.rs").write_text("malicious change\n", encoding="utf-8")
        _expect_failure(
            lambda: verify_generated_only_diff(effigy, artifact, manifest_path, built["manifest_digest"], descriptor_path),
            "product-code candidate diff",
        )
    return {"candidate_materialized": True, "clean_diff_verified": True, "hand_edit_rejected": True, "product_code_rejected": True}


def app_token_scope_proof() -> dict[str, Any]:
    request = app_token_request("123", "456")
    require(request == {
        "method": "POST",
        "endpoint": "/app/installations/456/access_tokens",
        "repositories": ["effigy"],
        "permissions": {"contents": "write", "pull_requests": "write"},
        "short_lived": True,
    }, "App token request widened or changed")
    accepted = validate_app_token_response(
        {
            "token": "test-token",
            "expires_at": "2026-09-02T16:00:00Z",
            "permissions": {"contents": "write", "pull_requests": "write", "metadata": "read"},
            "repositories": [{
                "name": "effigy",
                "full_name": PROPOSAL_APP_REPOSITORY_FULL_NAME,
                "owner": {"login": PROPOSAL_APP_REPOSITORY_OWNER},
            }],
        }
    )
    require(accepted["token"] == "redacted", "App token entered a report")
    require(accepted["repository_full_name"] == PROPOSAL_APP_REPOSITORY_FULL_NAME, "App token report lost canonical identity")
    require(accepted["repository_owner"] == PROPOSAL_APP_REPOSITORY_OWNER, "App token report lost canonical owner")
    _expect_failure(
        lambda: validate_app_token_response(
            {
                "token": "test-token",
                "expires_at": "2026-09-02T16:00:00Z",
                "permissions": {"contents": "write", "pull_requests": "write", "administration": "write"},
                "repositories": [{"name": "effigy", "full_name": PROPOSAL_APP_REPOSITORY_FULL_NAME}],
            }
        ),
        "broad App permission response",
    )
    _expect_failure(
        lambda: validate_app_token_response(
            {
                "token": "test-token",
                "expires_at": "2026-09-02T16:00:00Z",
                "permissions": {"contents": "write", "pull_requests": "write", "metadata": "write"},
                "repositories": [{"name": "effigy", "full_name": PROPOSAL_APP_REPOSITORY_FULL_NAME}],
            }
        ),
        "broad metadata permission response",
    )
    _expect_failure(
        lambda: validate_app_token_response(
            {
                "token": "test-token",
                "expires_at": "2026-09-02T16:00:00Z",
                "permissions": {"contents": "write", "pull_requests": "write"},
                "repositories": [{"name": "effigy", "full_name": "foreign-owner/effigy", "owner": {"login": "foreign-owner"}}],
            }
        ),
        "foreign-owner same-name token response",
    )
    _expect_failure(lambda: app_token_request("0", "456"), "zero App id")
    return {
        "post_installation_token_endpoint": True,
        "effigy_repository_only": True,
        "contents_write_only_for_effigy": True,
        "pull_requests_write_only_for_effigy": True,
        "canonical_repository_identity": PROPOSAL_APP_REPOSITORY_FULL_NAME,
        "foreign_owner_same_name_rejected": True,
        "broad_response_rejected": True,
        "token_redacted": True,
    }


def effigy_verifier_seam_proof() -> dict[str, Any]:
    command = effigy_verifier_command(Path(".proposal/effigy"), offline=True)
    require(command[:3] == ["cargo", "test", "--offline"], "Effigy verifier command is not offline")
    require(command[-2:] == ["--test", "catalog_pack_proposal_baseline"], "Effigy verifier test target changed")
    require("effigy_catalog::pack::baseline" in PROPOSAL_VERIFIER_HARNESS, "harness is not Effigy-owned")
    require("CompiledBaselineLock::load" in PROPOSAL_VERIFIER_HARNESS, "harness does not load the typed lock")
    require("verify_snapshot" in PROPOSAL_VERIFIER_HARNESS, "harness does not run Effigy's verifier")
    require("EFFIGY_PROPOSAL_ROOT" in PROPOSAL_VERIFIER_HARNESS, "harness root is not explicit")
    return {
        "committed_rust_verifier_used": True,
        "offline_command_available": True,
        "temporary_harness_explicit": True,
    }


def no_provider_mutation_proof() -> dict[str, Any]:
    workflow = (ROOT / ".github" / "workflows" / "proposal.yml").read_text(encoding="utf-8")
    forbidden = re.compile(
        r"(?:gh\s+pr\s+(?:merge|review)|gh\s+release|release\s+(?:prepare|execute)|"
        r"--approve|--merge|packages\s*:\s*write|id-token\s*:\s*write|"
        r"attestations\s*:\s*write|actions/attest|oras\s+(?:cp|push))",
        re.IGNORECASE,
    )
    require(not forbidden.search(workflow), "proposal workflow contains acceptance, release, or publication authority")
    require('git -C "$EFFIGY_ROOT" push' in workflow, "proposal workflow does not publish its branch")
    require("gh pr create" in workflow, "proposal workflow does not create a review PR")
    require("contents: read" in workflow, "proposal workflow lacks read-only Actions permissions")
    require('oras manifest fetch "ghcr.io/inflatable-cookie/effigy-catalog-pack@$ARTIFACT_DIGEST"' in workflow, "proposal workflow does not fetch raw manifest bytes")
    require("oras manifest fetch --format json" not in workflow, "proposal workflow rewrites the raw manifest")
    require("CATALOG_PACK_PUBLICATION_MUTATE" not in workflow, "proposal workflow imports publication mutation authority")
    require("publication.yml" not in workflow, "proposal workflow depends on publication workflow completion")
    publication = (ROOT / ".github" / "workflows" / "publication.yml").read_text(encoding="utf-8")
    require("proposal.yml" not in publication, "publication workflow depends on proposal acceptance")
    entry = (ROOT / "scripts" / "catalog_pack.py").read_text(encoding="utf-8")
    publish_body = entry.partition("def publish_command")[2].partition("def main")[0].lower()
    require("proposal" not in publish_body, "publish path depends on proposal")
    artifact_check = workflow.index("proposal-artifact-check")
    token_mint = workflow.index("Mint a narrow short-lived Effigy installation token")
    materialize = workflow.index("Generate the candidate snapshot, lock, and evidence")
    branch_push = workflow.index('git -C "$EFFIGY_ROOT" push')
    require(artifact_check < token_mint < materialize < branch_push, "manifest verification does not precede token, materialization, and push")
    return {
        "branch_and_pr_only": True,
        "approve_merge_release_rejected": True,
        "publication_independent": True,
        "raw_manifest_and_descriptor_bound": True,
        "manifest_verified_before_materialize_token_push": True,
        "ordinary_model_provider_writes": [],
    }


def proposal_model_proof() -> dict[str, Any]:
    return {
        "generated_only_paths": generated_only_path_allowlist_proof(),
        "immutable_artifact": immutable_artifact_input_proof(),
        "exact_lock": exact_lock_generation_proof(),
        "candidate_diff": candidate_diff_proof(),
        "app_token": app_token_scope_proof(),
        "effigy_verifier": effigy_verifier_seam_proof(),
        "no_provider_mutation": no_provider_mutation_proof(),
        "network_access": False,
    }
