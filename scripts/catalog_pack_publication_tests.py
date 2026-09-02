"""Network-free publication-transaction and support/import split proofs."""

from __future__ import annotations

from catalog_pack_authority import prove_import, prove_support
from catalog_pack_constants import IMPORT_AUTHORITY_COMMIT
from catalog_pack_registry import require_live_mutation_gate
from catalog_pack_shared import *
from catalog_pack_transaction_tests import publication_transaction_proof


def support_import_split_proof(authority: Path | None, require_authority: bool) -> dict[str, Any]:
    if authority is None:
        if require_authority:
            fail("Effigy authority checkout is required for the support/import split proof")
        return {"skipped": True}
    support = prove_support(authority, True)
    require(support["import_pin_used"] is False, "current support still used the import pin")
    require(support["support_commit"] != IMPORT_AUTHORITY_COMMIT, "current support is still pinned to the import commit")
    require(support["authority_commit"] == support["support_commit"], "support commit aliases diverged")
    import_available = (
        run_command(
            ["git", "-C", str(authority), "cat-file", "-e", f"{IMPORT_AUTHORITY_COMMIT}^{{commit}}"],
            check=False,
        ).returncode
        == 0
    )
    if not import_available:
        return {
            "distinct": True,
            "import_proof": "skipped-import-commit-absent",
            "support_commit": support["support_commit"],
            "import_commit": IMPORT_AUTHORITY_COMMIT,
            "support_blob_oid": support["support_blob_oid"],
        }
    imported = prove_import(authority)
    require(imported["authority_commit"] == IMPORT_AUTHORITY_COMMIT, "import proof lost the immutable import commit")
    require(
        imported["current_support_commit"] == support["support_commit"],
        "import proof did not observe the current default-branch support commit",
    )
    return {
        "distinct": True,
        "import_proof": "checked",
        "support_commit": support["support_commit"],
        "import_commit": imported["authority_commit"],
        "support_blob_oid": support["support_blob_oid"],
        "import_support_blob_oid": imported["support_blob_oid"],
    }


def mutation_gate_proof() -> dict[str, Any]:
    cases = {
        "empty": {},
        "actions-only": {"GITHUB_ACTIONS": "true"},
        "wrong-event": {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REPOSITORY": PACK_GITHUB_REPOSITORY,
            "GITHUB_ENVIRONMENT": PUBLICATION_ENVIRONMENT,
            PUBLICATION_MUTATE_ENV: "1",
        },
        "wrong-repo": {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": "someone/else",
            "GITHUB_ENVIRONMENT": PUBLICATION_ENVIRONMENT,
            PUBLICATION_MUTATE_ENV: "1",
        },
        "missing-environment": {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": PACK_GITHUB_REPOSITORY,
            PUBLICATION_MUTATE_ENV: "1",
        },
    }
    for name, env in cases.items():
        try:
            require_live_mutation_gate(env)
        except CheckFailure:
            continue
        fail(f"mutation gate permitted {name}")
    require_live_mutation_gate(
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": PACK_GITHUB_REPOSITORY,
            "GITHUB_ENVIRONMENT": PUBLICATION_ENVIRONMENT,
            PUBLICATION_MUTATE_ENV: "1",
        }
    )
    return {"fail_closed": True, "accepted_protected_dispatch": True}


def publication_check(authority: Path | None, require_authority: bool) -> dict[str, Any]:
    from catalog_pack_live_tests import live_seam_proof

    return {
        "support_import_split": support_import_split_proof(authority, require_authority),
        "mutation_gate": mutation_gate_proof(),
        "transaction": publication_transaction_proof(),
        "live_seam": live_seam_proof(),
        "network_free": True,
        "live_mutation": False,
    }
