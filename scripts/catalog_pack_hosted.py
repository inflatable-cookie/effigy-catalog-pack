"""Hosted repository-control and workflow checks."""

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

    hosted_validation = evidence.get("hosted_validation")
    require(isinstance(hosted_validation, dict), "hosted validation evidence is missing")
    require(
        isinstance(hosted_validation.get("run_id"), int) and hosted_validation["run_id"] > 0,
        "hosted validation evidence lacks a run id",
    )
    require(
        re.fullmatch(r"[0-9a-f]{40}", hosted_validation.get("head", "")) is not None,
        "hosted validation evidence lacks a source head",
    )
    require(hosted_validation.get("event") == "pull_request", "hosted validation was not a pull-request run")
    require(hosted_validation.get("conclusion") == "success", "hosted validation did not succeed")
    require(
        isinstance(hosted_validation.get("url"), str) and hosted_validation["url"].startswith("https://"),
        "hosted validation URL is missing",
    )
    return {
        "verified": True,
        "observed_at": evidence["observed_at"],
        "observed_head": evidence["observed_head"],
        "hosted_validation_run": hosted_validation["run_id"],
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
