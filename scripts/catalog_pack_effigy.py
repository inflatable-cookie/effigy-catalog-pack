"""Current-Effigy consumer checks."""

from __future__ import annotations

from catalog_pack_shared import *


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
