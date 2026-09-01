"""Workflow and current-Effigy consumer checks."""

from __future__ import annotations

from catalog_pack_authority import resolve_authority
from catalog_pack_shared import *


def hosted_control_check() -> dict[str, Any]:
    """Require a normalized, live-captured repository-control evidence file."""

    try:
        evidence = json.loads(HOSTED_EVIDENCE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"hosted control evidence is missing or invalid: {error}")
    require(evidence.get("schema_version") == 1, "hosted control evidence schema is not 1")
    require(evidence.get("repository") == "inflatable-cookie/effigy-catalog-pack", "hosted control evidence names the wrong repository")
    require(isinstance(evidence.get("observed_at"), str) and evidence["observed_at"], "hosted control evidence lacks an observation time")
    require(re.fullmatch(r"[0-9a-f]{40}", evidence.get("observed_head", "")) is not None, "hosted control evidence lacks a source head")

    actions = evidence.get("actions")
    require(isinstance(actions, dict), "hosted Actions control evidence is missing")
    require(actions.get("enabled") is True, "hosted Actions are not enabled")
    require(actions.get("allowed_actions") == "selected", "hosted Actions are not on the selected-actions policy")
    require(actions.get("sha_pinning_required") is True, "hosted Actions do not require full-SHA pinning")
    selected = actions.get("selected_actions")
    require(isinstance(selected, dict), "selected Actions policy evidence is missing")
    require(selected.get("github_owned_allowed") is False, "hosted Actions allow all GitHub-owned actions")
    require(selected.get("verified_allowed") is False, "hosted Actions allow all verified actions")
    require(
        selected.get("patterns_allowed") == [f"actions/checkout@{CHECKOUT_ACTION_SHA}"],
        "hosted Actions allow more than the pinned checkout action",
    )

    environment = evidence.get("environment")
    require(isinstance(environment, dict), "hosted environment evidence is missing")
    require(environment.get("name") == "catalog-pack-publication-rehearsal", "hosted environment has the wrong name")
    require(environment.get("wait_timer") == 0, "hosted environment wait timer changed")
    require(environment.get("prevent_self_review") is True, "hosted environment permits self-review")
    require(environment.get("can_admins_bypass") is False, "hosted environment permits administrator bypass")
    reviewers = environment.get("required_reviewers")
    require(isinstance(reviewers, list) and reviewers, "hosted environment has no required reviewer")
    require(environment.get("deployment_branch_policy") is None, "hosted environment has an unexpected branch policy")

    ruleset = evidence.get("tag_ruleset")
    require(isinstance(ruleset, dict), "hosted tag ruleset evidence is missing")
    require(ruleset.get("target") == "tag" and ruleset.get("enforcement") == "active", "v* tag ruleset is not active")
    require(ruleset.get("ref_name_include") == ["refs/tags/v*"], "tag ruleset does not target exactly v* tags")
    require(ruleset.get("rules") == ["deletion", "update"], "tag ruleset does not reject v* updates and deletions")
    require(ruleset.get("bypass_actors") == [], "tag ruleset has an unexpected bypass actor")
    require(ruleset.get("current_user_can_bypass") == "never", "current user can bypass the v* tag ruleset")
    return {
        "verified": True,
        "observed_at": evidence["observed_at"],
        "observed_head": evidence["observed_head"],
        "actions_enabled": True,
        "environment_protected": True,
        "version_tags_protected": True,
    }


def workflow_check() -> dict[str, Any]:
    workflow_root = ROOT / ".github" / "workflows"
    expected = {"validate.yml", "publication-rehearsal.yml"}
    require(workflow_root.is_dir(), "workflow directory is missing")
    actual = {path.name for path in workflow_root.iterdir() if path.is_file()}
    require(actual == expected, f"workflow inventory is {sorted(actual)}, expected {sorted(expected)}")

    forbidden = re.compile(
        r"(?:oras\s+push|git\s+push|git\s+tag|docker\s+login|gh\s+(?:api|release)|"
        r"contents\s*:\s*write|packages\s*:\s*write|id-token\s*:\s*write|"
        r"attestations\s*:\s*write|actions/upload-artifact)",
        re.IGNORECASE,
    )
    uses_pattern = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
    action_pattern = re.compile(r"^[^@]+@([0-9a-f]{40})$")
    for path in sorted(workflow_root.iterdir()):
        if not path.is_file():
            continue
        contents = path.read_text()
        require(not forbidden.search(contents), f"workflow contains a release mutation or broad permission: {path.name}")
        require("permissions:" in contents and "contents: read" in contents, f"workflow lacks read-only permissions: {path.name}")
        for action in uses_pattern.findall(contents):
            require(action_pattern.match(action), f"workflow action is not pinned by full SHA: {path.name}: {action}")

    validation = (workflow_root / "validate.yml").read_text()
    rehearsal = (workflow_root / "publication-rehearsal.yml").read_text()
    require("pull_request:" in validation, "validate workflow must run for pull requests")
    require(f"ref: {IMPORT_AUTHORITY_COMMIT}" in validation, "validate workflow must pin the Effigy support checkout")
    require("--import-proof" not in validation, "validate workflow must not make Effigy the ongoing pack byte authority")
    require("--require-authority" in validation, "validate workflow must verify the pinned Effigy support policy")
    require("workflow_dispatch:" in rehearsal, "publication rehearsal must be manual")
    require("catalog-pack-publication-rehearsal" in rehearsal, "publication rehearsal must name its protected environment")
    require(f"ref: {IMPORT_AUTHORITY_COMMIT}" in rehearsal, "publication rehearsal must pin the Effigy support checkout")
    require(
        "source_tag:" in rehearsal and "source_ref:" in rehearsal,
        "publication rehearsal must accept source tag and peeled commit inputs",
    )
    require(
        "inputs.source_tag" in rehearsal and "inputs.source_ref" in rehearsal,
        "publication rehearsal must use its source identity inputs",
    )
    require(
        "--source-tag" in rehearsal and "--source-ref" in rehearsal,
        "publication rehearsal must pass source identity inputs",
    )
    hosted = hosted_control_check()
    return {
        "workflow_files": sorted(expected),
        "actions_sha_pinned": True,
        "release_mutations": False,
        "hosted_controls": hosted,
    }


def portable_authority_check() -> dict[str, Any]:
    """Prove an isolated checkout fails with the documented portable remedy."""

    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-portable-") as temporary:
        isolated_root = Path(temporary) / "repo"
        isolated_root.mkdir()
        resolved = resolve_authority(None, repo_root=isolated_root, environment={})
        require(resolved is None, f"isolated checkout resolved unrelated Effigy authority: {resolved}")
    return {
        "without_authority": "fails-closed",
        "remediation": "pass --effigy-root or set EFFIGY_ROOT",
    }


def resolve_effigy_command(authority: Path, requested: str | None, environment: dict[str, str]) -> list[str]:
    explicit = requested or os.environ.get("EFFIGY_BIN")
    if explicit:
        path = Path(explicit)
        require(path.is_file(), f"Effigy binary does not exist: {path}")
        return [str(path)]

    cargo_manifest = authority / "Cargo.toml"
    require(cargo_manifest.is_file(), f"Effigy Cargo manifest is missing: {cargo_manifest}")
    for binary in (authority / "target" / "debug" / "effigy", authority / "target" / "release" / "effigy"):
        if binary.is_file() and os.access(binary, os.X_OK):
            return [str(binary)]

    target_dir = ROOT / ".effigy" / "cargo-target"
    target_dir.mkdir(parents=True, exist_ok=True)
    environment["CARGO_NET_OFFLINE"] = "true"
    environment["CARGO_TARGET_DIR"] = str(target_dir)
    # Effigy task execution can intentionally sanitize the caller's Rust
    # toolchain selection. If rustup exposes a versioned local toolchain, use
    # it without asking rustup to sync the moving `stable` channel.
    if not environment.get("RUSTUP_TOOLCHAIN"):
        toolchains = run_command(["rustup", "toolchain", "list"], check=False)
        versioned = []
        for line in decode_output(toolchains.stdout).splitlines():
            name = line.split()[0] if line.split() else ""
            if re.match(r"^\d+\.\d+(?:\.\d+)?-", name):
                versioned.append(name)
        if versioned:
            environment["RUSTUP_TOOLCHAIN"] = versioned[-1]
    return [
        "cargo",
        "run",
        "--offline",
        "--locked",
        "--manifest-path",
        str(cargo_manifest),
        "--bin",
        "effigy",
        "--",
    ]


def run_effigy(command: list[str], arguments: list[str], cwd: Path, environment: dict[str, str]) -> str:
    result = run_command(command + arguments, cwd=cwd, env=environment)
    return decode_output(result.stdout)


def unwrap_effigy_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("result")
    return result if isinstance(result, dict) else payload


def effigy_smoke(authority: Path | None, requested_binary: str | None) -> dict[str, Any]:
    require(authority is not None, "Effigy authority checkout is required for the binary smoke test")
    pack_facts = validate_pack_tree()
    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-smoke-") as temporary:
        temporary_root = Path(temporary)
        home = temporary_root / "home"
        repo = temporary_root / "repo"
        extract = temporary_root / "extract"
        home.mkdir()
        repo.mkdir()
        extract.mkdir()
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_DATA_HOME": str(home / ".local" / "share"),
                "XDG_CACHE_HOME": str(home / ".cache"),
                "GIT_TERMINAL_PROMPT": "0",
                "CARGO_NET_OFFLINE": "true",
            }
        )
        command = resolve_effigy_command(authority, requested_binary, environment)

        version_output = run_effigy(command, ["--version"], repo, environment)
        require(
            CURRENT_EFFIGY_RELEASE in version_output and IMPORT_AUTHORITY_COMMIT[:7] in version_output,
            f"Effigy smoke binary is not the pinned current build: {version_output}",
        )

        install_output = run_effigy(
            command,
            ["service", "pack", "install", "--path", str(PACK_ROOT)],
            repo,
            environment,
        )
        require(
            pack_facts["content_id"] in install_output,
            "Effigy local pack install did not report the computed content identity",
        )

        status = unwrap_effigy_result(
            json.loads(run_effigy(command, ["service", "pack", "status", "--json"], repo, environment))
        )
        require(status.get("ok") is True, "Effigy pack status did not return ok")
        active = status.get("active")
        require(isinstance(active, dict), "Effigy pack status did not select the installed pack")
        require(active.get("pack_id") == pack_facts["pack_id"], "Effigy selected the wrong pack id")
        require(active.get("pack_version") == pack_facts["pack_version"], "Effigy selected the wrong pack version")
        require(active.get("content_id") == pack_facts["content_id"], "Effigy recorded the wrong content identity")

        service_list = unwrap_effigy_result(
            json.loads(
                run_effigy(command, ["service", "list", "--repo", str(repo), "--json"], repo, environment)
            )
        )
        fragments = service_list.get("fragments")
        require(isinstance(fragments, list) and len(fragments) == 14, "Effigy service list did not expose all catalog fragments")
        require(
            all(fragment.get("source", "").startswith("installed-pack") for fragment in fragments),
            "Effigy service list did not resolve the installed pack",
        )

        run_effigy(
            command,
            ["service", "extract", "workspace-rust-bun", "--repo", str(repo), "--dir", str(extract)],
            repo,
            environment,
        )
        extracted = extract / "workspace-rust-bun"
        require((extracted / "service.toml").is_file(), "Effigy could not extract workspace-rust-bun")
        require((extracted / "Dockerfile").is_file(), "Effigy workspace extraction lost its Dockerfile")

        (repo / "effigy.toml").write_text(
            """[containers]
default = "stack"

[containers.stack]
primary_service = "workspace"

[containers.stack.services.workspace]
catalog = "workspace-rust-bun"

[containers.stack.services.postgres]
catalog = "postgres"
""",
            encoding="utf-8",
        )
        eject_output = run_effigy(command, ["container", "stack", "eject", "--repo", str(repo)], repo, environment)
        compose = repo / "infra" / "dev" / "docker-compose.yml"
        require(compose.is_file(), "Effigy did not eject a representative compose assembly")
        compose_text = compose.read_text(encoding="utf-8")
        require("workspace" in compose_text and "postgres" in compose_text, "ejected compose lost representative services")

        return {
            "binary": "cargo source build" if command[0] == "cargo" else command[0],
            "pack_install": "ok",
            "service_list_fragments": len(fragments),
            "workspace_extract": "ok",
            "representative_assembly": "ok",
            "eject_output": eject_output.splitlines()[-1] if eject_output else "ok",
        }
