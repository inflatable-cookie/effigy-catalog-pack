"""No-push publication identity and immutable retry rehearsal."""

from __future__ import annotations

from datetime import datetime, timezone

from catalog_pack_oci import deterministic_oci_proof, source_repository_identity
from catalog_pack_shared import *


def synthetic_tag_object(source_commit: str, tag_name: str, message: str) -> str:
    """Hash an annotated tag payload without writing a Git object or ref."""

    payload = (
        f"object {source_commit}\n"
        "type commit\n"
        f"tag {tag_name}\n"
        "tagger catalog-pack-rehearsal <noreply@inflatable-cookie.com> 0 +0000\n"
        f"\n{message}\n"
    ).encode("utf-8")
    return hashlib.sha1(b"tag " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()


def commit_created(commit: str) -> str:
    try:
        epoch = int(git_output(ROOT, ["show", "-s", "--format=%ct", commit]))
        return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError, OverflowError) as error:
        fail(f"source repository commit timestamp is invalid: {error}")


def actual_source_identity(source_tag: str, source_ref: str, pack_version: str) -> dict[str, str]:
    """Resolve and verify the annotated tag/ref pair supplied to publication."""

    tag_name = source_tag.removeprefix("refs/tags/")
    tag_ref = f"refs/tags/{tag_name}"
    require(tag_name == f"v{pack_version}", "source tag does not match pack version")
    require(re.fullmatch(r"[0-9a-f]{40}", source_ref) is not None, "source ref must be a full commit")
    require(git_output(ROOT, ["cat-file", "-t", tag_ref]) == "tag", "source ref is not an annotated tag")
    tag_object = git_output(ROOT, ["rev-parse", f"{tag_ref}^{{tag}}"])
    peeled_commit = git_output(ROOT, ["rev-parse", f"{tag_ref}^{{commit}}"])
    source_commit = git_output(ROOT, ["rev-parse", f"{source_ref}^{{commit}}"])
    require(peeled_commit == source_commit, "source tag does not peel to the requested pack commit")
    require(git_output(ROOT, ["rev-parse", "HEAD"]) == source_commit, "checkout is not at the requested pack commit")
    try:
        tag_body = git_bytes(ROOT, ["cat-file", "-p", tag_ref]).decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"annotated source tag is not UTF-8: {error}")
    require(f"object {source_commit}\n" in tag_body, "annotated source tag object target changed")
    require("type commit\n" in tag_body, "annotated source tag does not name a commit")
    require(f"tag {tag_name}\n" in tag_body, "annotated source tag name changed")
    return {
        "source_commit": source_commit,
        "source_created": commit_created(source_commit),
        "source_tag": tag_name,
        "tag_object": tag_object,
        "peeled_commit": peeled_commit,
        "source_ref": source_ref,
    }


def planned_source_identity(pack_version: str) -> dict[str, str]:
    identity = source_repository_identity()
    tag_name = f"v{pack_version}"
    identity.update(
        {
            "source_tag": tag_name,
            "tag_object": synthetic_tag_object(identity["source_commit"], tag_name, "planned no-push publication"),
            "peeled_commit": identity["source_commit"],
            "source_ref": identity["source_commit"],
        }
    )
    return identity


def candidate_state(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest_digest": candidate["manifest_digest"],
        "content_id": candidate["content_id"],
        "pack_version": candidate["source_identity"].get("source_tag", "").removeprefix("v"),
        "source_identity": candidate["source_identity"],
    }


def no_push_rehearsal(source_tag: str | None = None, source_ref: str | None = None) -> dict[str, Any]:
    pack_facts = validate_pack_tree()
    require((source_tag is None) == (source_ref is None), "source tag and source ref must be supplied together")
    identity = (
        planned_source_identity(pack_facts["pack_version"])
        if source_tag is None
        else actual_source_identity(source_tag, source_ref or "", pack_facts["pack_version"])
    )
    candidate = deterministic_oci_proof(identity, run_oras=False)
    tag = candidate["reference"]
    base_state = candidate_state(candidate)

    def reconcile(remote: dict[str, dict[str, Any]], candidate_state_value: dict[str, Any]) -> str:
        existing = remote.get(tag)
        if existing is None:
            remote[tag] = candidate_state_value
            return "absent-would-create"
        if existing == candidate_state_value:
            return "same-digest-would-reuse"
        raise CheckFailure(f"collision rejected: {existing['manifest_digest']} is already recorded for {tag}")

    absent_remote: dict[str, dict[str, Any]] = {}
    absent_result = reconcile(absent_remote, base_state)
    require(absent_remote == {tag: base_state}, "absent rehearsal did not record the candidate decision")

    same_remote = {tag: base_state}
    same_before = dict(same_remote)
    same_result = reconcile(same_remote, base_state)
    require(same_remote == same_before, "same-digest rehearsal changed remote state")

    with tempfile.TemporaryDirectory(prefix="effigy-catalog-pack-collision-") as temporary:
        temporary_root = Path(temporary)
        changed_pack = temporary_root / "changed-pack"
        shutil.copytree(PACK_ROOT, changed_pack)
        changed_file = changed_pack / "README.md"
        changed_file.write_bytes(changed_file.read_bytes() + b"\nchanged source fixture\n")
        changed_commit = hashlib.sha1((identity["source_commit"] + " changed source").encode("ascii")).hexdigest()
        changed_identity = dict(identity)
        changed_identity.update(
            {
                "source_commit": changed_commit,
                "peeled_commit": changed_commit,
                "source_ref": changed_commit,
                "tag_object": synthetic_tag_object(changed_commit, identity["source_tag"], "changed source fixture"),
            }
        )
        changed_source = deterministic_oci_proof(changed_identity, changed_pack, run_oras=False)
        require(changed_source["manifest_digest"] != candidate["manifest_digest"], "changed source did not change the OCI digest")
        changed_source_before = dict(same_remote)
        try:
            reconcile(same_remote, candidate_state(changed_source))
        except CheckFailure as error:
            require("collision rejected" in str(error), "changed-source retry failed for the wrong reason")
        require(same_remote == changed_source_before, "changed-source collision changed remote state")

        changed_tag_identity = dict(identity)
        changed_tag_identity["tag_object"] = synthetic_tag_object(
            identity["source_commit"], identity["source_tag"], "changed tag object fixture"
        )
        changed_tag = deterministic_oci_proof(changed_tag_identity, run_oras=False)
        require(changed_tag["manifest_digest"] != candidate["manifest_digest"], "changed tag identity did not change the OCI digest")
        changed_tag_before = dict(same_remote)
        try:
            reconcile(same_remote, candidate_state(changed_tag))
        except CheckFailure as error:
            require("collision rejected" in str(error), "changed-tag retry failed for the wrong reason")
        require(same_remote == changed_tag_before, "changed-tag collision changed remote state")

    return {
        "reference": tag,
        "candidate_digest": candidate["manifest_digest"],
        "source_identity": identity,
        "network_access": False,
        "push_attempted": False,
        "scenarios": {
            "absent": absent_result,
            "same_digest": same_result,
            "changed_source": "rejected-without-write",
            "changed_tag_identity": "rejected-without-write",
        },
    }
