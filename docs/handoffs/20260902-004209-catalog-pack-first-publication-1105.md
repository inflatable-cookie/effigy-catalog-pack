---
title: Catalog-pack first publication 1105 worker handoff
kind: northstar-handoff
handoff_mode: worker-pr-loop
worker_mode: implementation
dispatch_authority: orchestrator
handoff: single-file-path-only
status: ready-to-launch
owner: Effigy catalog-pack publication worker
created: 2026-09-02
updated: 2026-09-02
handoff_path: /Users/tom/Dev/projects/effigy-catalog-pack/docs/handoffs/20260902-004209-catalog-pack-first-publication-1105.md
base_required: pushed-main
tags: [coordination, handoff, worker, pr, publication]
---

## What This Thread Was Doing

Effigy card `1105` is the first official catalog-pack publication. Foundation
card `1104` is merged. On 2026-09-02 the operator explicitly authorized the
annotated `v1.0.0` source tag, public GHCR package, digest-bound attestation,
and `stable` movement.

This dispatches one bounded two-phase implementation lane. The first phase
lands publication code with no live mutation. After exact-head orchestrator
review and merge, the same worker identity returns for publication and an
evidence PR. No transcript or second briefing is part of the authority chain.

## Why It Matters

The public artifact is the immutable source for Effigy's later generated
baseline and safe update path. A partial or weak first publication would make
the registry pointer, attestation, compatibility floor, and rollback evidence
untrustworthy. The order is therefore part of the product contract.

## Current State

Here is the state the worker is inheriting:

- **Repository:** `inflatable-cookie/effigy-catalog-pack`
- **Planning branch:** `main`
- **Planning base commit:** `b022ba0708568fda6a49b7d37e9e6f8cf72764fa`
- **Pushed main verification:** local `HEAD` and `origin/main` both
  `b022ba0708568fda6a49b7d37e9e6f8cf72764fa` before this handoff commit
- **Planning checkout:** clean before this handoff was written
- **Worker mode:** implementation worker dispatched by the orchestrator; this
  handoff activates the worker-only worktree preflight
- **Planning artifacts included at the base:** external repository authority in
  `AGENTS.md` and Paseo sibling-link lifecycle in `paseo.json`; Effigy planning
  is pushed at `ee7821464e17927593a358d2166bf1897fcc9b12`
- **Worker branch:** `worker/g08-048-first-publication-1105`
- **Worker worktree:** Paseo-managed worktree; launcher-selected actual path
  wins over this planned slug
- **Worktree creation command:** Paseo `branch-off` from `origin/main` with
  worktree slug `catalog-pack-first-publication-1105`
- **Worker worktree policy:** follow `Completion Protocol`; launcher worktree
  first, named/manual fallback only when required
- **Required sibling worktree links:** link `effigy`, source
  `/Users/tom/Dev/projects/effigy`, at `<worktree-container>/effigy`
- **Active spec lane:** Effigy
  `docs/specs/115-catalog-pack-publication-and-cutover-strict-lane.md`
- **Roadmap milestone:** Effigy
  `docs/roadmaps/g08/048-catalog-pack-publication-and-cutover.md`
- **Ready cards, in order:** Effigy
  `docs/roadmaps/g08/batch-cards/1105-publish-first-official-catalog-pack.md`
- **Allowed runway:** card `1105` only, with implementation PR -> orchestrator
  merge -> same-worker live publication -> evidence PR
- **Remaining card budget:** one two-phase card; stop after the implementation
  PR until the orchestrator explicitly resumes this worker after merge
- **Dispatch topology:** only card `1105`; cards `1106` through `1108` remain
  blocked on accepted publication evidence
- **Parallel safety check:** no sibling implementation lane; `1105 -> 1106` is
  a real artifact/evidence dependency
- **Surfaces this lane owns:** `.github/workflows/`, `scripts/`, `effigy.toml`,
  `README.md`, `docs/validation.md`, and `docs/evidence/` in this repository
- **Integration ownership:** the Effigy card, roadmap, spec, contract, logs, and
  front-door closeout remain orchestrator-owned; do not edit the Effigy sibling
- **Merge ordering:** implementation PR first; live mutation only after that PR
  is accepted and merged; evidence PR second
- **Canonical refs:** Effigy architecture `026`; contract `043`; spec `115`;
  roadmap `g08.048`; card `1105`; authority log
  `docs/logs/2026-09/02-003915-catalog-pack-first-publication-authority-1105.md`
- **Review oracle:** card `1105` `## Review Oracle` plus spec `115`
  `## Whole-Lane Review Oracle`
- **Model capability profile:** non-frontier day-to-day implementation; the
  contract and ordered mutation oracle bound the remaining design work
- **Frontier-worker justification:** none
- **Tool/runtime restrictions:** no Effigy edits or release; no tag, package,
  attestation, visibility, or channel mutation before the implementation PR is
  merged; no tag overwrite/re-tag; no admin/ruleset bypass; package writes only
  through the protected publication workflow; ordinary validation stays
  network-free
- **Required validation:** see card `1105`; first phase must restore green
  `effigy doctor`, pass `effigy validate`, `effigy qa`, workflow/provider
  controls, deterministic candidate replay, support freshness/release checks,
  and every no-mutation oracle; post-merge publication must prove the protected
  workflow run, immutable identities, attestation, anonymous digest pull and
  exact bytes, package linkage/public visibility, `stable`, rollback, and
  same-digest retry
- **PR base/head:** first PR `main <- worker/g08-048-first-publication-1105`;
  follow-up evidence PR from a refreshed post-publication branch
- **PR URL:** pending
- **Review state:** awaiting implementation PR
- **Merge path:** orchestrator after accepted review of each current head and
  passing required checks

## Boundaries

Please keep this run inside the named runway:

- **In scope:** diagnose and split ongoing support authority from the immutable
  import pin; implement the protected first-publication transaction; land it
  without mutation; after orchestrator merge, publish exactly `v1.0.0`, prove
  and exercise the named state, then land immutable evidence
- **Out of scope:** Effigy code/docs edits, Effigy binary release, another pack
  version, another registry/repository, automatic publication, public
  `service pack update`, generated Effigy baseline, GitHub App automation, S3,
  retention, extension transport, collaborator-role widening, or bypassing a
  failed gate
- **Outcome shape:** complete card `1105` in two serial phases. The first phase
  ends at a pushed reviewable implementation PR. Do not perform live mutations
  from the implementation branch. After the orchestrator merges and resumes
  this worker, the second phase publishes and opens a separate evidence PR.
- Do not invent architecture, change contracts, widen the roadmap, or choose an
  unresolved product/API/persistence/security decision.
- Work only in the clean worker worktree selected by `Completion Protocol`.
  Never edit the planning checkout or an unrelated dirty checkout.
- Do not merge either PR. Merge belongs to the orchestrator after its accepted
  review/check gate.

## Important Context

- **Planning lineage:** card `1103` established Effigy's support floor; `1104`
  established this public source repository and deterministic no-push proof;
  `1105` is the sole Ready edge before generated baseline card `1106`.
- **Why this card is ready:** foundation and support authority are merged;
  repository controls are live; the exact external mutation set is
  operator-authorized; acceptance, stop conditions, review oracle, and the
  pre-mutation merge boundary are explicit.
- **Decisions and preferences:** source/OCI version `v1.0.0`; registry
  `ghcr.io/inflatable-cookie/effigy-catalog-pack`; `stable` moves only after all
  proofs; OCI manifest digest is immutable identity; source and version tags
  are checked pointers; one-time import evidence must not become ongoing
  support authority.
- **Known base finding:** current `effigy doctor` fails because ongoing support
  proof still requires Effigy `HEAD == 055595340...`. Current Effigy `main` is
  later. This is an in-scope recurrence of the import/support conflation. Fix
  it by implementing contract `043`: resolve current default-branch support
  commit/blob, prove release freshness and compatibility, and leave the import
  commit/tree/blob only in `import-proof`.
- **Open tensions:** generic OCI attestation shape and rollback must be proved
  live. Stop rather than selecting a new artifact shape, weakening anonymous
  proof, changing the support policy, or bypassing provider controls.
- **Report after:** the implementation transaction and adversarial tests are
  coherent and before any live mutation; then report the PR. After merge and
  explicit resume, report immediately on any mutation/gate failure and again
  when publication evidence is complete.
- **Report to:** the operator through the active control plane; the
  orchestrator retains review, merge, and continuation authority.

## Suggested Next Move

Run the `Completion Protocol` preflight before broad reads. Then reproduce the
known doctor failure, separate support-currentness from historical import
evidence, and design the protected transaction so every remote write is
preceded by its card gate. Finish the implementation-only PR and stop. Do not
create `v1.0.0` or contact a registry write surface before the orchestrator
merges that PR and resumes this same worker.

## Completion Protocol

### Before you start

1. This handoff's `worker_mode: implementation` and
   `dispatch_authority: orchestrator` activate worker mode. Before broad reads,
   run `git rev-parse --show-toplevel`, `git branch --show-current`,
   `git status --porcelain`, and `git worktree list --porcelain`.
2. If the current root is a registered worktree, its status is empty, and its
   branch is not `main`, accept it as the launcher-provided worktree. Record its
   actual root/branch; do not compare it with the planned path or branch and do
   not create another worktree merely because they differ.
3. If current context is `main`, dirty, unregistered, or unusable, inspect the
   named worktree. If unusable, read `.agents.local.env`, require
   `AGENTS_WORKTREE_CONTAINER_DIR`, and ask the operator when absent. Create a
   unique worktree/branch there from pushed `origin/main`. Never use `/tmp`,
   `TMPDIR`, or a guessed path; never clean, reset, stash-over, or discard dirty
   state. Report a launcher-supplied dirty or `main` worktree instead of
   creating another.
4. From the selected worktree, record this handoff's repository-relative path.
   Run
   `GIT_SSH_COMMAND="ssh -o ConnectTimeout=10 -o BatchMode=yes" git fetch origin`.
   Confirm `HEAD == origin/main`, confirm
   `git merge-base --is-ancestor b022ba0708568fda6a49b7d37e9e6f8cf72764fa HEAD`,
   and confirm the handoff exists in that `HEAD`. Load it with `git show`. If
   the absolute dispatch file differs from the tracked blob, stop. The tracked
   `HEAD` copy is canonical.
5. Verify required sibling link `effigy` in the worktree container resolves to
   `/Users/tom/Dev/projects/effigy`. The Paseo lifecycle should create it before
   agent launch. Stop on absence, mismatch, file, or directory; never delete,
   replace, overwrite, or skip it.
6. Read `AGENTS.md`, Effigy card `1105`, roadmap `g08.048`, spec `115`, contract
   `043`, and the authority log through the sibling link.
7. Run the repo's cheap orientation checks and record the known base doctor
   failure separately from any new finding.

### While you work

- Execute only card `1105` and keep commits aligned with meaningful chunks.
- Restore a green health path before any live mutation. The support-currentness
  proof and immutable import proof must have distinct inputs and tests.
- Every live write must remain unreachable in ordinary QA and before the
  implementation PR merge. Tests must prove ordering and fail-closed states.
- Report changed files, validation, remaining phase, new risks, and blockers.
- Stop on missing authority/access, tag/package collision, support drift,
  attestation mismatch, anonymous-pull mismatch, permission drift, or any need
  to widen the operator gate.

### First-phase completion

1. Run all required network-free and GET-only validation, including `effigy
   doctor`, `effigy validate`, `effigy qa`, provider controls, workflow guards,
   deterministic candidate replay, and review-oracle counterexamples.
2. Falsify universal, exact, and negative claims. Prove no source tag, package,
   attestation, visibility, or channel mutation occurred.
3. Update external repository docs/evidence for the implementation boundary.
4. Push the worker branch and open a reviewable PR against current `main`.
5. Report PR URL, exact head, checks, and remaining live-publication phase.
6. Stop. Wait for the orchestrator to review, merge, and explicitly resume this
   same worker identity.

### Post-merge publication and evidence

1. On resume, fetch and verify the orchestrator-named merged `main` identity.
   Re-run live provider controls and every pre-mutation gate.
2. Create the protected annotated `v1.0.0` source tag at the reviewed merged
   source. Never re-tag or bypass the tag ruleset.
3. Dispatch the protected workflow with the exact tag and peeled commit. Stop
   immediately on any failed gate; never move `stable` manually around it.
4. Prove and record source tag object/commit, OCI version digest, attestation,
   anonymous digest pull and exact bytes, public package state, `stable` digest,
   rollback target/exercise, and idempotent same-digest retry.
5. Create a fresh evidence branch from current `main`, commit the immutable
   report, push, and open the follow-up evidence PR. Do not merge.

### Review and merge path

The orchestrator reviews both PRs against the canonical refs, diff, provider
state, and checks. When formal self-approval is unavailable, its exact-head PR
comment is the canonical verdict. Blocking findings use `execution-miss`,
`oracle-gap`, `planning-change`, `validation-gap`, or `integration-drift`.
Requested changes are: none. Any head change requires re-review.

- **Closeout refs:** external publication evidence plus Effigy card `1105`,
  roadmap `g08.048`, spec `115`, contract `043`, logs, and front-door Next Task

### Handoff closeout

Do not call card `1105` complete after the implementation PR or successful
workflow alone. Completion requires the reviewed and merged evidence PR plus
orchestrator reconciliation of Effigy's canonical planning surfaces.
