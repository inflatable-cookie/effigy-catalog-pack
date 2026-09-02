"""Hosted repository-control and workflow checks."""

from __future__ import annotations

from catalog_pack_authority import resolve_authority
from catalog_pack_shared import *


def hosted_control_check() -> dict[str, Any]:
    """Require a normalized static provider-control evidence snapshot."""

    try:
        evidence = json.loads(HOSTED_EVIDENCE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"hosted control evidence is missing or invalid: {error}")
    require(evidence.get("schema_version") == 1, "hosted control evidence schema is not 1")
    require(evidence.get("evidence_kind") == "static-provider-snapshot", "hosted control evidence is not marked static")
    require(evidence.get("repository") == "inflatable-cookie/effigy-catalog-pack", "hosted control evidence names the wrong repository")
    require(isinstance(evidence.get("observed_at"), str) and evidence["observed_at"], "hosted control evidence lacks an observation time")
    require(re.fullmatch(r"[0-9a-f]{40}", evidence.get("observed_head", "")) is not None, "hosted control evidence lacks a source head")
    require(
        evidence.get("verification_command") == "python3 scripts/catalog_pack.py provider-controls",
        "hosted control evidence lacks the live verification command",
    )

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
    require(environment.get("prevent_self_review") is False, "hosted environment blocks the sole operator's self-review")
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
        "evidence_kind": "static-provider-snapshot",
        "live_verification_required": True,
        "hosted_validation_separate": True,
        "actions_enabled": True,
        "environment_protected": True,
        "version_tags_protected": True,
    }


def workflow_check() -> dict[str, Any]:
    workflow_root = ROOT / ".github" / "workflows"
    expected = {"validate.yml", "publication.yml"}
    require(workflow_root.is_dir(), "workflow directory is missing")
    actual = {path.name for path in workflow_root.iterdir() if path.is_file()}
    require(actual == expected, f"workflow inventory is {sorted(actual)}, expected {sorted(expected)}")

    validate_forbidden = re.compile(
        r"(?:oras\s+push|git\s+push|git\s+tag|docker\s+login|gh\s+(?:api|release)|"
        r"contents\s*:\s*write|packages\s*:\s*write|id-token\s*:\s*write|"
        r"attestations\s*:\s*write|actions/upload-artifact|--mutate)",
        re.IGNORECASE,
    )
    publication_forbidden = re.compile(
        r"(?:git\s+push|git\s+tag|docker\s+login|actions/upload-artifact|"
        r"contents\s*:\s*write|pull_request:)",
        re.IGNORECASE,
    )
    uses_pattern = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
    action_pattern = re.compile(r"^[^@]+@([0-9a-f]{40})$")
    for path in sorted(workflow_root.iterdir()):
        if not path.is_file():
            continue
        contents = path.read_text()
        require("permissions:" in contents and "contents: read" in contents, f"workflow lacks contents: read: {path.name}")
        for action in uses_pattern.findall(contents):
            require(action_pattern.match(action), f"workflow action is not pinned by full SHA: {path.name}: {action}")
            require(
                action == f"actions/checkout@{CHECKOUT_ACTION_SHA}",
                f"workflow uses an action other than the pinned checkout: {path.name}: {action}",
            )

    def run_blocks(contents: str) -> list[str]:
        lines = contents.splitlines()
        blocks: list[str] = []
        for index, line in enumerate(lines):
            match = re.match(r"^(?P<indent> *)run:\s*(?P<value>.*)$", line)
            if match is None:
                continue
            indent = len(match.group("indent"))
            block = [line]
            if match.group("value").strip().startswith(("|", ">")):
                following = index + 1
                while following < len(lines):
                    candidate = lines[following]
                    candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                    if candidate.strip() or candidate_indent > indent:
                        if candidate.strip() and candidate_indent <= indent:
                            break
                        block.append(candidate)
                        following += 1
                        continue
                    block.append(candidate)
                    following += 1
            blocks.append("\n".join(block))
        return blocks

    def has_raw_input_in_run(contents: str) -> bool:
        expression = re.compile(r"\$\{\{\s*inputs\.[A-Za-z_][A-Za-z0-9_]*\s*\}\}")
        return any(expression.search(block) for block in run_blocks(contents))

    def require_no_raw_input_in_run(contents: str) -> None:
        require(not has_raw_input_in_run(contents), "publication interpolates a workflow input directly in run")

    validation = (workflow_root / "validate.yml").read_text()
    publication = (workflow_root / "publication.yml").read_text()
    require(not validate_forbidden.search(validation), "validate workflow contains a release mutation or write permission")
    require(not publication_forbidden.search(publication), "publication workflow contains a forbidden mutation")
    require("pull_request:" in validation, "validate workflow must run for pull requests")
    require(f"ref: {IMPORT_AUTHORITY_COMMIT}" not in validation, "validate workflow must not pin support to the import commit")
    require("ref: main" in validation, "validate workflow must check out Effigy's current default branch")
    require("repository: inflatable-cookie/effigy" in validation, "validate workflow must check out the Effigy support repository")
    require("--import-proof" not in validation, "validate workflow must not make Effigy the ongoing pack byte authority")
    require("--require-authority" in validation, "validate workflow must verify the current Effigy support policy")
    require("publication-check" in validation, "validate workflow must run the network-free publication transaction proof")
    require("workflow_dispatch:" in publication, "publication must be manual")
    require("pull_request:" not in publication and "push:" not in publication, "publication must not run on push or pull_request")
    require("catalog-pack-publication-rehearsal" in publication, "publication must name its protected environment")
    require("ref: main" in publication, "publication must check out Effigy's current default branch")
    require(f"ref: {IMPORT_AUTHORITY_COMMIT}" not in publication, "publication must not pin support to the import commit")
    require("packages: write" in publication, "publication must grant packages: write")
    require("id-token: write" in publication, "publication must grant id-token: write")
    require("attestations: write" in publication, "publication must grant attestations: write")
    require("CATALOG_PACK_PUBLICATION_MUTATE: \"1\"" in publication, "publication must set the mutate gate")
    require("--mutate" in publication, "publication must pass --mutate only in the protected job")
    require(
        "source_tag:" in publication and "source_ref:" in publication,
        "publication must accept source tag and peeled commit inputs",
    )
    require(
        "inputs.source_tag" in publication and "inputs.source_ref" in publication,
        "publication must use its source identity inputs",
    )
    require(
        "--source-tag" in publication and "--source-ref" in publication,
        "publication must pass source identity inputs",
    )
    require("SOURCE_TAG: ${{ inputs.source_tag }}" in publication, "publication must bind source_tag through step env")
    require("SOURCE_REF: ${{ inputs.source_ref }}" in publication, "publication must bind source_ref through step env")
    require('--source-tag "$SOURCE_TAG"' in publication, "publication must quote the source_tag shell variable")
    require('--source-ref "$SOURCE_REF"' in publication, "publication must quote the source_ref shell variable")
    require_no_raw_input_in_run(publication)

    injection_counterexample = """
      - name: Input injection counterexample
        run: >-
          printf '%s\\n' "${{ inputs.source_tag }}"
    """
    require(has_raw_input_in_run(injection_counterexample), "workflow input injection counterexample missed the run guard")
    try:
        require_no_raw_input_in_run(injection_counterexample)
    except CheckFailure:
        pass
    else:
        fail("workflow input injection counterexample bypassed the run guard")
    hosted = hosted_control_check()
    return {
        "workflow_files": sorted(expected),
        "actions_sha_pinned": True,
        "checkout_only_actions": True,
        "validate_read_only": True,
        "publication_write_scoped": True,
        "release_mutations_in_validate": False,
        "workflow_input_shell_guard": True,
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
