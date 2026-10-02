#!/usr/bin/env python3
"""Network-free tests for the Effigy smoke identity contract."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from catalog_pack_effigy import validate_effigy_version_output
from catalog_pack_policy import authority_workspace_package_version, workspace_package_version
from catalog_pack_shared import CheckFailure


class EffigySmokeIdentityTests(unittest.TestCase):
    def test_exact_current_release_and_local_build_metadata_are_accepted(self) -> None:
        validate_effigy_version_output("effigy v0.13.1", "0.13.1")
        validate_effigy_version_output("effigy v0.13.1+local.6dc2a97", "0.13.1")

    def test_obsolete_foreign_and_misleading_versions_are_rejected(self) -> None:
        for output in (
            "effigy v0.13.0",
            "effigy v9.13.1",
            "effigy v0.13.10",
            "other-effigy v0.13.1",
            "effigy v0.13.1 extra v0.13.0",
            "effigy v0.13.1-foreign",
            "effigy v0.13.1+foreign.build",
        ):
            with self.subTest(output=output), self.assertRaises(CheckFailure):
                validate_effigy_version_output(output, "0.13.1")

    def test_malformed_version_output_is_rejected(self) -> None:
        for output in (
            "",
            "effigy 0.13.1",
            "effigy v0.13",
            "effigy v0.13.1+local.",
            "effigy v00.13.1",
            "effigy v0.13.1\nanything else",
        ):
            with self.subTest(output=output), self.assertRaises(CheckFailure):
                validate_effigy_version_output(output, "0.13.1")

    def test_workspace_version_is_read_from_the_workspace_package_table(self) -> None:
        cargo_toml = '''
[package]
name = "effigy"
version = "0.13.0"

[workspace.package]
version = "0.13.1" # current authority release
edition = "2021"
'''
        self.assertEqual(workspace_package_version(cargo_toml), "0.13.1")

    def test_missing_or_malformed_authority_manifest_identity_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="effigy-smoke-identity-") as temporary:
            authority = Path(temporary)
            with self.assertRaisesRegex(CheckFailure, "Cargo manifest is missing"):
                authority_workspace_package_version(authority)

            cargo_manifest = authority / "Cargo.toml"
            for contents in (
                "[workspace.package]\nedition = \"2021\"\n",
                "[workspace.package]\nversion = 13\n",
                "[workspace.package]\nversion = \"0.13\"\n",
                "[workspace.package]\nversion = \"0.13.1\n",
                "[workspace.package]\nversion = \"0.13.1\"\n\n[workspace.package]\nversion = \"0.13.2\"\n",
            ):
                with self.subTest(contents=contents):
                    cargo_manifest.write_text(contents, encoding="utf-8")
                    with self.assertRaises(CheckFailure):
                        authority_workspace_package_version(authority)


if __name__ == "__main__":
    unittest.main(verbosity=2)
