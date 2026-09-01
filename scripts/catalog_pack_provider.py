"""Read-only live GitHub provider-control verification."""

from __future__ import annotations

from datetime import datetime, timezone

from catalog_pack_shared import *


REPOSITORY = "inflatable-cookie/effigy-catalog-pack"
ENVIRONMENT_NAME = "catalog-pack-publication-rehearsal"
RULESET_ID = 22050144

API_PATHS = {
    "actions": f"repos/{REPOSITORY}/actions/permissions",
    "selected_actions": f"repos/{REPOSITORY}/actions/permissions/selected-actions",
    "workflow_permissions": f"repos/{REPOSITORY}/actions/permissions/workflow",
    "environment": f"repos/{REPOSITORY}/environments/{ENVIRONMENT_NAME}",
    "tag_ruleset": f"repos/{REPOSITORY}/rulesets/{RULESET_ID}",
}


def _gh_json(path: str) -> dict[str, Any]:
    gh = shutil.which("gh")
    require(gh is not None, "live provider verification requires the GitHub CLI (gh)")
    result = run_command([gh, "api", "--method", "GET", path], check=False)
    if result.returncode != 0:
        detail = decode_output(result.stderr) or decode_output(result.stdout)
        fail(f"read-only provider GET failed for {path}: {detail}")
    try:
        payload = json.loads(decode_output(result.stdout))
    except json.JSONDecodeError as error:
        fail(f"provider GET returned invalid JSON for {path}: {error}")
    require(isinstance(payload, dict), f"provider GET returned a non-object for {path}")
    return payload


def _environment_facts(payload: dict[str, Any]) -> dict[str, Any]:
    protection_rules = payload.get("protection_rules")
    require(isinstance(protection_rules, list), "live environment response lacks protection rules")
    reviewer_rules = [rule for rule in protection_rules if rule.get("type") == "required_reviewers"]
    require(len(reviewer_rules) == 1, "live environment must have exactly one required-reviewers rule")
    reviewer_rule = reviewer_rules[0]
    raw_reviewers = reviewer_rule.get("reviewers")
    require(isinstance(raw_reviewers, list), "live environment reviewer rule lacks reviewers")
    reviewers: list[dict[str, Any]] = []
    for entry in raw_reviewers:
        require(isinstance(entry, dict), "live environment reviewer entry is invalid")
        reviewer = entry.get("reviewer")
        require(isinstance(reviewer, dict), "live environment reviewer identity is invalid")
        reviewers.append(
            {
                "type": entry.get("type"),
                "login": reviewer.get("login"),
                "id": reviewer.get("id"),
            }
        )
    reviewers.sort(key=lambda value: (str(value.get("type")), str(value.get("login")), int(value.get("id", 0))))

    wait_rules = [rule for rule in protection_rules if rule.get("type") == "wait_timer"]
    require(len(wait_rules) <= 1, "live environment has more than one wait-timer rule")
    wait_timer = wait_rules[0].get("wait_timer", 0) if wait_rules else 0
    require(wait_timer == 0, "live environment wait timer is not zero")
    require(payload.get("name") == ENVIRONMENT_NAME, "live environment has the wrong name")
    require(reviewers == [{"type": "User", "login": "betterthanclay", "id": 1273586}], "live environment reviewer changed")
    require(reviewer_rule.get("prevent_self_review") is False, "live environment still blocks the sole operator's self-review")
    require(payload.get("can_admins_bypass") is False, "live environment permits administrator bypass")
    require(payload.get("deployment_branch_policy") is None, "live environment has an unexpected branch policy")

    return {
        "id": payload.get("id"),
        "name": payload["name"],
        "wait_timer": wait_timer,
        "prevent_self_review": reviewer_rule.get("prevent_self_review"),
        "can_admins_bypass": payload.get("can_admins_bypass"),
        "required_reviewers": reviewers,
        "deployment_branch_policy": payload.get("deployment_branch_policy"),
    }


def _tag_ruleset_facts(payload: dict[str, Any]) -> dict[str, Any]:
    conditions = payload.get("conditions")
    require(isinstance(conditions, dict), "live tag ruleset lacks conditions")
    ref_name = conditions.get("ref_name")
    require(isinstance(ref_name, dict), "live tag ruleset lacks ref-name conditions")
    raw_rules = payload.get("rules")
    require(isinstance(raw_rules, list), "live tag ruleset lacks rules")
    rules = sorted(rule.get("type") for rule in raw_rules if isinstance(rule, dict))
    facts = {
        "id": payload.get("id"),
        "name": payload.get("name"),
        "target": payload.get("target"),
        "enforcement": payload.get("enforcement"),
        "ref_name_include": ref_name.get("include"),
        "rules": rules,
        "bypass_actors": payload.get("bypass_actors"),
        "current_user_can_bypass": payload.get("current_user_can_bypass"),
    }
    require(facts["id"] == RULESET_ID, "live tag ruleset id changed")
    require(facts["target"] == "tag" and facts["enforcement"] == "active", "live v* tag ruleset is not active")
    require(facts["ref_name_include"] == ["refs/tags/v*"], "live tag ruleset does not target exactly v* tags")
    require(facts["rules"] == ["deletion", "update"], "live tag ruleset does not reject v* updates and deletions")
    require(facts["bypass_actors"] == [], "live tag ruleset has an unexpected bypass actor")
    require(facts["current_user_can_bypass"] == "never", "current user can bypass the live v* tag ruleset")
    return facts


def live_provider_check() -> dict[str, Any]:
    """Read and compare the live provider controls without any write method."""

    responses = {name: _gh_json(path) for name, path in API_PATHS.items()}
    actions = responses["actions"]
    selected_actions = responses["selected_actions"]
    workflow_permissions = responses["workflow_permissions"]
    require(actions.get("enabled") is True, "live Actions are not enabled")
    require(actions.get("allowed_actions") == "selected", "live Actions are not on the selected-actions policy")
    require(actions.get("sha_pinning_required") is True, "live Actions do not require full-SHA pinning")
    require(selected_actions.get("github_owned_allowed") is False, "live Actions allow GitHub-owned actions")
    require(selected_actions.get("verified_allowed") is False, "live Actions allow verified actions")
    require(
        selected_actions.get("patterns_allowed") == [f"actions/checkout@{CHECKOUT_ACTION_SHA}"],
        "live Actions allow more than the pinned checkout action",
    )
    require(workflow_permissions.get("default_workflow_permissions") == "read", "live workflow permissions are not read-only")
    require(workflow_permissions.get("can_approve_pull_request_reviews") is False, "live workflows can approve pull requests")

    actions_facts = {
        "enabled": actions.get("enabled"),
        "allowed_actions": actions.get("allowed_actions"),
        "sha_pinning_required": actions.get("sha_pinning_required"),
        "selected_actions": {
            "github_owned_allowed": selected_actions.get("github_owned_allowed"),
            "verified_allowed": selected_actions.get("verified_allowed"),
            "patterns_allowed": selected_actions.get("patterns_allowed"),
        },
    }
    workflow_facts = {
        "default_workflow_permissions": workflow_permissions.get("default_workflow_permissions"),
        "can_approve_pull_request_reviews": workflow_permissions.get("can_approve_pull_request_reviews"),
    }
    return {
        "evidence_kind": "live-provider-observation",
        "mode": "live-read-only",
        "repository": REPOSITORY,
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "observed_head": git_output(ROOT, ["rev-parse", "HEAD"]),
        "read_only": True,
        "write_methods_used": [],
        "api_calls": {name: f"GET /{path}" for name, path in API_PATHS.items()},
        "static_snapshot": {
            "path": str(HOSTED_EVIDENCE_PATH.relative_to(ROOT)),
            "used_for_live_comparison": False,
        },
        "actions": actions_facts,
        "workflow_permissions": workflow_facts,
        "environment": _environment_facts(responses["environment"]),
        "tag_ruleset": _tag_ruleset_facts(responses["tag_ruleset"]),
        "verified": True,
    }
