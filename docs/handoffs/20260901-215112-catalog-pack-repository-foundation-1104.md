---
title: Catalog-pack repository foundation worker handoff
kind: northstar-handoff
handoff_mode: worker-pr-loop
worker_mode: implementation
dispatch_authority: orchestrator
handoff: single-file-path-only
status: ready-to-launch
owner: Effigy orchestrator
created: 2026-09-01
updated: 2026-09-01
handoff_path: /Users/tom/Dev/projects/effigy-catalog-pack/docs/handoffs/20260901-215112-catalog-pack-repository-foundation-1104.md
base_required: pushed-main
tags: [coordination, handoff, worker, pr]
---

## What This Thread Was Doing

Effigy card `1103` established the machine-readable support-floor authority and
merged it to pushed `main`. The operator selected public visibility for this
dedicated repository. This dispatch owns card `1104`: build the canonical pack
repository foundation and prove publication deterministically without creating
any release or package state.

This dispatches one bounded implementation lane. No transcript or second prompt
is part of the authority chain.

## Why It Matters

Concrete service and workspace assets need one clean owner outside Effigy core.
This foundation must prove exact bytes, compatibility input, deterministic OCI
identity, and safe workflow permissions before the separately gated first
publication can exist.

## Current State

Here is the state the worker is inheriting:

- **Repository:** `inflatable-cookie/effigy-catalog-pack`
- **Planning branch:** `main`
- **Planning base commit:** `f25ad0420e326159ca9cc759f116fa8e6dd7c2b7`
- **Pushed main verification:** local and `origin/main` both resolved to
  `f25ad0420e326159ca9cc759f116fa8e6dd7c2b7` before this handoff commit
- **Planning checkout:** clean public primary checkout at
  `/Users/tom/Dev/projects/effigy-catalog-pack`
- **Worker mode:** implementation worker dispatched by the orchestrator; this
  handoff activates the worker-only worktree preflight.
- **Planning artifacts included at the base:** Effigy planning is committed and
  pushed at `055595340c2219d3d47296072f5818c524c341f0`; this repository's
  bootstrap base contains its initial README
- **Worker branch:** `worker/g08-048-catalog-pack-foundation-1104`
- **Worker worktree:** launcher-managed worktree, intended slug
  `catalog-pack-foundation-1104`
- **Worktree creation command:** Paseo `branch-off` from `origin/main`; manual
  fallback follows `Completion Protocol`
- **Worker worktree policy:** follow `Completion Protocol`; launcher worktree
  first, named/manual fallback only when required.
- **Required sibling worktree links:** link name `effigy`; absolute source
  `/Users/tom/Dev/projects/effigy`; destination
  `<selected-worktree-parent>/effigy`
- **Active spec lane:** sibling
  `effigy/docs/specs/115-catalog-pack-publication-and-cutover-strict-lane.md`
- **Roadmap milestone:** sibling
  `effigy/docs/roadmaps/g08/048-catalog-pack-publication-and-cutover.md`
- **Ready cards, in order:** sibling
  `effigy/docs/roadmaps/g08/batch-cards/1104-build-catalog-pack-repository-foundation.md`
- **Allowed runway:** card `1104` only
- **Remaining card budget:** one card
- **Dispatch topology:** sole ready frontier lane; cards `1105` through `1108`
  remain behind real publication and artifact dependencies
- **Parallel safety check:** no sibling worker lane; Effigy planning checkout is
  read-only authority
- **Surfaces this lane owns:** this repository's `pack/`, manifest, task and
  validation code, repository docs/evidence, and the card-authorized read-only
  CI plus protected manual no-push publication workflow
- **Integration ownership:** the Effigy orchestrator alone updates Effigy card,
  roadmap, logs, and front doors after accepted merge
- **Merge ordering:** same-repository PRs merge one at a time; the orchestrator
  refreshes this head against current `main` and re-reviews it if a sibling lane
  merges first
- **Canonical refs:** sibling
  `effigy/docs/architecture/026-feature-placement-and-command-surface.md`;
  sibling
  `effigy/docs/contracts/043-feature-placement-and-surface-migration-contract.md`
- **Review oracle:** card `1104` `## Review Oracle` plus spec `115`
  `## Whole-Lane Review Oracle`
- **Model capability profile:** economical non-frontier implementation worker;
  the card is bounded by settled architecture and a falsifiable material-risk
  oracle
- **Frontier-worker justification:** none
- **Tool/runtime restrictions:** workflow edits are authorized only in this
  repository and only for card `1104`; do not mutate the Effigy sibling; do not
  publish, tag, create a package, change package visibility, move `stable`, or
  perform a release; do not place package-write credentials in validation
- **Required validation:** repository-owned focused tests and full QA; exact
  imported inventory and content identity; repeated deterministic local OCI
  candidate digest; pinned Effigy support commit/blob; no-push
  absent/same-digest/collision rehearsal; workflow permission review; current
  Effigy local-pack install plus representative service/workspace assembly;
  formatting and diff checks
- **PR base/head:** `main` <-
  `worker/g08-048-catalog-pack-foundation-1104`
- **PR URL:** pending
- **Review state:** awaiting implementation and exact-head review
- **Merge path:** orchestrator after accepted review of the current head and
  passing required checks

## Boundaries

Please keep this run inside the named runway:

- **In scope:** create/import/validate the public repository foundation and
  build the two card-authorized workflow surfaces; prove publication locally in
  no-push mode.
- **Out of scope:** any source tag, GHCR/package creation, package or repository
  visibility mutation, attestation upload, `stable` movement, first publication,
  Effigy snapshot cutover, public update command, baseline proposal automation,
  Effigy workflow/code changes, S3, and extension transport.
- **Outcome shape:** complete implementation of card `1104`, repository-local
  evidence, pushed branch, and reviewable PR. Stop rather than publishing to
  prove the design.
- Do not invent architecture, change contracts, widen the roadmap, or choose an
  unresolved product/API/persistence/security decision.
- This handoff represents one worker lane. Write only inside **Surfaces this
  lane owns**. Leave Effigy's closeout surfaces to **Integration ownership**.
  If shared mutable scope or a hidden dependency appears, stop and report it.
- Work only in the clean worker worktree selected by `Completion Protocol`.
  Never edit the planning checkout or an unrelated dirty checkout.
- Do not merge the PR. Merge belongs to the orchestrator after its accepted
  review/check gate.

## Important Context

- **Planning lineage:** architecture `026` and contract `043` own the extracted
  asset boundary; strict spec `115` sequences support floor, foundation, first
  publication, generated baseline, update, and proposal automation.
- **Why this card is ready:** card `1103` is merged on pushed Effigy `main`; the
  public source-repository visibility choice is operator-confirmed; repository
  creation is complete; card `1104` has bounded acceptance, validation,
  evidence, stop conditions, and a review oracle.
- **Decisions and preferences:** `pack/` is the only editable asset root;
  version is `1.0.0`; support policy is consumed from resolved Effigy commit
  `055595340c2219d3d47296072f5818c524c341f0` and its blob digest; OCI manifest
  digest and unpacked content identity remain distinct; workflow implementation
  must be pinned and least-privilege; publication is manual/protected but this
  card may exercise only no-push paths.
- **Open tensions:** generic OCI attestation must be possible in principle, but
  producing or uploading a live attestation is forbidden here. Stop if the
  generic subject cannot be attested or if deterministic proof would require a
  registry mutation.
- **Report after:** imported source and deterministic validation foundation are
  coherent, then again when workflows and no-push proof are complete.
- **Report to:** the active control plane; the Effigy orchestrator owns review
  and merge.

## Suggested Next Move

Run the `Completion Protocol` preflight before broad reads. Then read
`AGENTS.md`, the sibling milestone, assigned card, and canonical refs from the
selected worker worktree. Start with exact source inventory and deterministic
identity design. At a natural pause, report changed files, validation, what
remains, and any planning decision.

## Completion Protocol

### Before you start

1. This handoff's `worker_mode: implementation` and
   `dispatch_authority: orchestrator` activate worker mode. Before broad reads,
   run `git rev-parse --show-toplevel`, `git branch --show-current`,
   `git status --porcelain`, and `git worktree list --porcelain`.
2. If the current root is a registered worktree, its status is empty, and its
   branch is not `main`, accept it as the launcher-provided worktree. Record its
   actual root/branch; do not compare its generated path/branch with the intended
   values or create another worktree merely because they differ.
3. If current context is `main`, dirty, unregistered, or unusable, inspect the
   named worktree. If unusable, read `.agents.local.env`, require
   `AGENTS_WORKTREE_CONTAINER_DIR`, and ask the operator when absent. Create a
   unique worktree/branch there from pushed `origin/main`. Never use `/tmp`,
   `TMPDIR`, or a guessed path; never clean, reset, stash-over, or discard dirty
   state. Report a launcher-supplied dirty or `main` worktree instead of creating
   another.
4. From the selected worktree, record this handoff's repository-relative path.
   Run
   `GIT_SSH_COMMAND="ssh -o ConnectTimeout=10 -o BatchMode=yes" git fetch origin`.
   Confirm `HEAD == origin/main`, confirm
   `git merge-base --is-ancestor f25ad0420e326159ca9cc759f116fa8e6dd7c2b7 HEAD`,
   and confirm the handoff exists in `HEAD`. Load it with `git show`. If the
   absolute dispatch file differs from that tracked blob, stop. The committed
   `HEAD` copy is canonical.
5. Verify the required sibling link named above. Canonicalize source and
   destination; require the source directory; reuse only a symlink resolving to
   that source. Stop on a missing source, mismatch, directory, or file. Never
   delete, replace, overwrite, or skip it.
6. Read the active milestone, assigned card, `AGENTS.md`, and canonical refs.
7. Run cheap repository orientation checks and record what you actually ran.

### While you work

- Execute card `1104` and keep commits aligned with meaningful chunks.
- Use ordinary causal and implementation judgment inside the card boundaries.
- Report meaningful chunks with changed files, validation, remaining work, new
  risks, and blockers.
- Stop if a contract is missing, intent is ambiguous, scope expands,
  authority/access is missing, or validation changes the plan.
- Do not quietly turn an open question into a new architecture.

### When the assigned runway is complete

1. Run all **Required validation** named above.
2. Try to falsify the diff against every card and whole-lane oracle
   counterexample. Map universal, exact, and negative claims to deterministic
   proof. Stop and return any new threshold, contract choice, or acceptance rule
   to planning.
3. Add a dated repository-local evidence log. Do not edit Effigy's planning or
   closeout files; report the exact evidence path for orchestrator integration.
4. Push the worker branch. If `main` moved, refresh against it and revalidate.
5. Open a reviewable PR against current pushed `main`.
6. Link the external Effigy spec, milestone, card, canonical refs, changed
   surfaces, evidence, validation, and unresolved items in the PR body.
7. Report the PR URL and exact head. Do not merge.

### Review and merge path

The Effigy orchestrator reviews the PR against the canonical refs, complete
diff, and checks. Because review and author may share a GitHub identity, the
canonical verdict may be a PR comment. Requested changes return to this same
worker and branch. Blocking findings use `execution-miss`, `oracle-gap`,
`planning-change`, `validation-gap`, or `integration-drift`; a
`planning-change` returns to Effigy planning first. Requested changes: none.

When the exact reviewed head remains current, required checks pass, the PR is
mergeable into `main`, and no stricter rule or operator pause applies, the
orchestrator merges without another approval prompt.

- **Closeout refs:** repository-local evidence and README/task surfaces belong
  to this PR; Effigy card `1104`, roadmap `g08.048`, spec `115`, log index, and
  front doors remain orchestrator-owned integration after accepted merge.

### Handoff closeout

Leave repository-local evidence and next action honest. If blocked, record the
blocker and stop rather than making the handoff look complete. Card `1105`
remains blocked until accepted merge plus separate operator publication
authority.
