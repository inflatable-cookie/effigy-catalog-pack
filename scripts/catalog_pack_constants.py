#!/usr/bin/env python3
"""Network-free foundation checks for the Effigy catalog pack.

The repository deliberately keeps the release input in one place: ``pack/``.
The repository checks its pack tree independently, consumes Effigy's current
default-branch support policy, and exposes a separate one-time import proof. It
also computes the pack content identity, builds a deterministic OCI layout, and
models the protected publication transaction without contacting a registry in
ordinary QA.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

try:
    import tomllib

    TOMLDecodeError = tomllib.TOMLDecodeError

    def parse_toml(contents: str) -> dict[str, Any]:
        return tomllib.loads(contents)

except ModuleNotFoundError:  # pragma: no cover - exercised on the macOS worker's Python 3.9
    class TOMLDecodeError(ValueError):
        """Fallback parser error for the small foundation TOML surface."""

    def _strip_toml_comment(line: str) -> str:
        quoted = False
        escaped = False
        for index, character in enumerate(line):
            if character == "\\" and quoted and not escaped:
                escaped = True
                continue
            if character == '"' and not escaped:
                quoted = not quoted
            if character == "#" and not quoted:
                return line[:index]
            escaped = False
        return line

    def _split_toml_array(value: str) -> list[str]:
        items: list[str] = []
        start = 0
        quoted = False
        escaped = False
        depth = 0
        for index, character in enumerate(value):
            if character == "\\" and quoted and not escaped:
                escaped = True
                continue
            if character == '"' and not escaped:
                quoted = not quoted
            elif not quoted and character == "[":
                depth += 1
            elif not quoted and character == "]":
                depth -= 1
            elif not quoted and character == "," and depth == 0:
                items.append(value[start:index].strip())
                start = index + 1
            escaped = False
        tail = value[start:].strip()
        if tail:
            items.append(tail)
        return items

    def _parse_toml_value(value: str) -> Any:
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            try:
                return json.loads(value)
            except json.JSONDecodeError as error:
                raise TOMLDecodeError(str(error)) from error
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        if value in {"true", "false"}:
            return value == "true"
        if value.startswith("[") and value.endswith("]"):
            return [_parse_toml_value(item) for item in _split_toml_array(value[1:-1])]
        if re.fullmatch(r"[+-]?\d+", value):
            return int(value)
        raise TOMLDecodeError(f"unsupported TOML value: {value!r}")

    def parse_toml(contents: str) -> dict[str, Any]:
        document: dict[str, Any] = {}
        current = document
        for raw_line in contents.splitlines():
            line = _strip_toml_comment(raw_line).strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                if line.startswith("[["):
                    raise TOMLDecodeError("array-of-table syntax is not supported")
                current = document
                for part in line[1:-1].split("."):
                    part = part.strip()
                    if not part:
                        raise TOMLDecodeError(f"invalid table header: {line!r}")
                    value = current.setdefault(part, {})
                    if not isinstance(value, dict):
                        raise TOMLDecodeError(f"table conflicts with a value: {line!r}")
                    current = value
                continue
            if "=" not in line:
                raise TOMLDecodeError(f"expected key/value: {line!r}")
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                raise TOMLDecodeError(f"empty key: {line!r}")
            current[key] = _parse_toml_value(value)
        return document


ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = ROOT / "pack"
SOURCE_CATALOG_RELATIVE = Path("crates/effigy-catalog/catalog")
SUPPORT_RELATIVE = Path("support/catalog-pack-update.toml")
HOSTED_EVIDENCE_PATH = ROOT / "docs" / "evidence" / "hosted-controls.json"

# These values identify the one-time import proof. They are deliberately not
# the ongoing pack validator's source of truth.
IMPORT_AUTHORITY_COMMIT = "055595340c2219d3d47296072f5818c524c341f0"
IMPORT_AUTHORITY_TREE = "539471162c4976551ac720fdcffe6a1de33cef0f"
IMPORT_SUPPORT_BLOB = "20d0194d52c0bbf46677f8d77ca96fb4505df50e"
CURRENT_EFFIGY_RELEASE = "0.12.1"
FOUNDATION_PACK_ID = "effigy-default-catalog"
FOUNDATION_PACK_CONTENT_ID = "sha256:511d120f181505f8ecced7687b564c4663663eca8f6f68b2b562c9b676feb29e"
SOURCE_URL = "https://github.com/inflatable-cookie/effigy-catalog-pack"
OCI_REPOSITORY = "ghcr.io/inflatable-cookie/effigy-catalog-pack"
PACK_GITHUB_REPOSITORY = "inflatable-cookie/effigy-catalog-pack"
EFFIGY_GITHUB_REPOSITORY = "inflatable-cookie/effigy"
PUBLICATION_ENVIRONMENT = "catalog-pack-publication-rehearsal"
PUBLICATION_MUTATE_ENV = "CATALOG_PACK_PUBLICATION_MUTATE"
STABLE_TAG = "stable"
CHECKOUT_ACTION_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
ATTEST_ACTION_COMMIT = "1e69f48acb82d1966a394da916b4c1698aa569d6"
ATTEST_DIST_GIT_BLOB = "ae6dd7873447202be6e0a3f99a5472e31fe86b6e"
ORAS_VERSION = "1.3.3"
ORAS_LINUX_AMD64_SHA256 = "9ce999f8d2de03fc03968b29d743077a58783e545e5eaa53917ca177352d0e59"
SLSA_PROVENANCE_PREDICATE = "https://slsa.dev/provenance/v1"

OCI_LAYOUT_VERSION = "1.0.0"
OCI_INDEX_MEDIA_TYPE = "application/vnd.oci.image.index.v1+json"
OCI_MANIFEST_MEDIA_TYPE = "application/vnd.oci.image.manifest.v1+json"
OCI_EMPTY_CONFIG_MEDIA_TYPE = "application/vnd.oci.empty.v1+json"
OCI_ARTIFACT_TYPE = "application/vnd.effigy.catalog.pack.v1"
OCI_FILE_LAYER_MEDIA_TYPE = "application/vnd.effigy.catalog.pack.file.v1"

SOURCE_FILES = (
    "README.md",
    "compose.override.example.yml",
    "dbgate/compose.fragment.yml",
    "dbgate/service.toml",
    "elasticsearch/compose.fragment.yml",
    "elasticsearch/service.toml",
    "mailpit/compose.fragment.yml",
    "mailpit/service.toml",
    "mariadb/compose.fragment.yml",
    "mariadb/configs/default.conf",
    "mariadb/configs/my.cnf",
    "mariadb/service.toml",
    "memcached/compose.fragment.yml",
    "memcached/service.toml",
    "minio/compose.fragment.yml",
    "minio/service.toml",
    "nginx/compose.fragment.yml",
    "nginx/configs/default.conf",
    "nginx/configs/laravel.conf",
    "nginx/configs/php-app.conf",
    "nginx/configs/spa.conf",
    "nginx/configs/wordpress.conf",
    "nginx/service.toml",
    "node/Dockerfile",
    "node/compose.fragment.yml",
    "node/service.toml",
    "pgweb/compose.fragment.yml",
    "pgweb/service.toml",
    "php-fpm/Dockerfile",
    "php-fpm/compose.fragment.yml",
    "php-fpm/service.toml",
    "phpmyadmin/compose.fragment.yml",
    "phpmyadmin/service.toml",
    "postgres/compose.fragment.yml",
    "postgres/configs/default.conf",
    "postgres/service.toml",
    "redis/compose.fragment.yml",
    "redis/service.toml",
    "workspace-rust-bun/Dockerfile",
    "workspace-rust-bun/compose.fragment.yml",
    "workspace-rust-bun/service.toml",
)
PACK_FILES = ("pack.toml",) + SOURCE_FILES
