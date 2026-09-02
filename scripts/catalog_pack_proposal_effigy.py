"""Bridge for running Effigy's committed baseline verifier on a candidate."""

from __future__ import annotations

from catalog_pack_shared import *


PROPOSAL_VERIFIER_HARNESS = r'''use std::env;
use std::path::PathBuf;

use effigy_catalog::pack::baseline::{CompiledBaselineLock, verify_snapshot};

#[test]
fn generated_baseline_passes_effigy_offline_verifier() {
    let root = PathBuf::from(env::var("EFFIGY_PROPOSAL_ROOT").expect("EFFIGY_PROPOSAL_ROOT"));
    let lock = CompiledBaselineLock::load(&root.join("crates/effigy-catalog/catalog-pack.lock.toml"))
        .expect("candidate baseline lock");
    let proof = verify_snapshot(&root.join("crates/effigy-catalog/catalog"), &lock)
        .expect("candidate baseline snapshot");
    assert_eq!(proof.content_identity, lock.identities.content_identity);
    assert_eq!(proof.oci_manifest_digest, lock.identities.oci_manifest_digest);
}
'''


def effigy_verifier_command(effigy_root: Path, offline: bool = False) -> list[str]:
    command = [
        "cargo",
        "test",
        "--locked",
        "--manifest-path",
        str(effigy_root / "crates/effigy-catalog/Cargo.toml"),
        "--test",
        "catalog_pack_proposal_baseline",
    ]
    if offline:
        command.insert(2, "--offline")
    return command


def run_effigy_verifier(effigy_root: Path, *, offline: bool = False) -> dict[str, Any]:
    """Run Effigy's committed Rust verifier in a disposable integration test."""

    test_dir = effigy_root / "crates/effigy-catalog/tests"
    test_path = test_dir / "catalog_pack_proposal_baseline.rs"
    require(test_dir.is_dir(), f"Effigy catalog integration-test directory is missing: {test_dir}")
    require(not test_path.exists() and not test_path.is_symlink(), "proposal verifier harness path is already present")
    test_path.write_text(PROPOSAL_VERIFIER_HARNESS, encoding="utf-8")
    environment = os.environ.copy()
    environment["EFFIGY_PROPOSAL_ROOT"] = str(effigy_root)
    try:
        run_command(effigy_verifier_command(effigy_root, offline), cwd=effigy_root, env=environment)
    finally:
        test_path.unlink(missing_ok=True)
    return {"effigy_verifier": "passed", "network_access": not offline, "harness_removed": True}
