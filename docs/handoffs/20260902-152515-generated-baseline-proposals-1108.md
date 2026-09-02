---
title: Generated baseline proposals 1108 worker handoff
kind: northstar-handoff
handoff_mode: worker-pr-loop
worker_mode: implementation
dispatch_authority: orchestrator
handoff: single-file-path-only
status: ready-to-launch
owner: Effigy catalog-pack baseline proposal automation
created: 2026-09-02
updated: 2026-09-02
handoff_path: /Users/tom/Dev/projects/effigy-catalog-pack/docs/handoffs/20260902-152515-generated-baseline-proposals-1108.md
base_required: pushed-main
tags: [coordination, handoff, worker, pr, automation]
---

## What This Thread Was Doing

Effigy card `1106` merged the exact generated recovery baseline. Card `1108`
is now ready for its implementation-only phase: let a verified pack artifact
prepare a generated-only Effigy baseline proposal through a narrowly scoped
GitHub App path, without granting acceptance, merge, release, or publication
authority.

This dispatches one bounded implementation lane. No transcript or second
prompt is part of the authority chain.

## Why It Matters

The externalized catalog remains maintainable only if baseline refreshes are
repeatable without making the pack repository an Effigy code owner. The
proposal boundary must automate exact reproduction while Effigy independently
reviews, validates, and accepts every change.

## Current State

- **Repository:** `inflatable-cookie/effigy-catalog-pack`
- **Planning branch:** `main`
- **Planning base commit:** `7427421a3bebf207ce9979c47f60609d1b276713`
- **Pushed main verification:** local and remote `main` must include this
  handoff and the card `1108` workflow authorization before launch
- **Planning checkout:** clean before this handoff batch
- **Worker mode:** implementation worker dispatched by the orchestrator; this
  handoff activates worker-only worktree preflight
- **Planning artifacts included at the base:** canonical pack repository and
  accepted `v1.0.1` publication evidence; Effigy planning at
  `a63b5d5bba70b515f0a7ca71522d20201e6ede39` promotes cards `1107`/`1108`
- **Worker branch:** `worker/g08-048-generated-baseline-proposals-1108`
- **Worker worktree:** Paseo-managed worktree; launcher-selected path wins
- **Worktree creation command:** Paseo branch-off from pushed `origin/main`
- **Required sibling worktree links:** `effigy`, source
  `/Users/tom/Dev/projects/effigy`, destination beside the worker worktree as
  `../effigy`
- **Active spec lane:** Effigy `docs/specs/115-catalog-pack-publication-and-cutover-strict-lane.md`
- **Roadmap milestone:** Effigy `docs/roadmaps/g08/048-catalog-pack-publication-and-cutover.md`
- **Ready card:** Effigy `docs/roadmaps/g08/batch-cards/1108-propose-generated-baseline-updates.md`
- **Allowed runway:** card `1108` implementation/no-provider-mutation phase only
- **Remaining card budget:** one card; stop after the implementation PR until
  the operator explicitly authorizes a live provider phase
- **Dispatch topology:** parallel with card `1107`, which writes only Effigy
- **Parallel safety check:** repository and implementation surfaces are
  disjoint; Effigy shared planning/front-door integration stays orchestrator-owned
- **Surfaces this lane owns:** pack-repository workflow, scripts, tests, task
  wiring, directly related README/validation docs, one dated evidence file,
  and this handoff; no Effigy sibling edits
- **Integration ownership:** Effigy card/roadmap/spec/contract/front doors and
  product code remain orchestrator or card-`1107` owned; do not edit them
- **Merge ordering:** repository-local PRs merge serially; orchestrator reviews
  the exact current head after any base refresh
- **Canonical refs:** Effigy architecture `026`; contract `043`; spec `115`;
  roadmap `g08.048`; card `1108`; accepted `1105`/`1106` evidence
- **Review oracle:** card `1108` plus spec `115` whole-lane row 8
- **Model capability profile:** long mechanical/security-sensitive workflow
  implementation with settled boundaries; use an economical capable
  non-frontier profile, with frontier review retained by the orchestrator
- **Frontier-worker justification:** none
- **Tool/runtime restrictions:** network-free model/validation only in this
  phase. Do not register/install an App, write secrets, dispatch the proposal,
  create an Effigy branch/PR, alter provider settings, publish/tag/move
  `stable`, approve/merge, or release. Pin every third-party action to exact SHA.
- **Required validation:** every card `1108` Validation row; adversarial path-
  allowlist and permission/token tests; immutable artifact and exact-byte lock
  generation proof; no-write/provider proof; repository doctor, validate, QA,
  workflow guards, docs checks, and diff checks
- **PR base/head:** current pushed `main` / worker branch above
- **PR URL:** pending
- **Review state:** awaiting implementation
- **Merge path:** orchestrator after accepted exact-head review and green checks;
  live provider phase remains separately operator-gated

## Boundaries

- **In scope:** implement and prove the no-provider-mutation proposal workflow,
  narrow GitHub App token request, exact generated-only diff policy, and
  independent Effigy verification seam.
- **Out of scope:** live App registration/installation, secret writes, workflow
  dispatch, an actual Effigy proposal PR, Effigy edits, publication changes,
  package/tag/channel mutation, approval, merge, or release.
- **Outcome shape:** complete implementation-only PR with executable network-
  free counterexamples and honest provider checkpoint; not diagnostics-only.
- The proposal may change only Effigy's generated catalog snapshot, typed lock,
  and required evidence. It must fail before push on any other path.
- Publication success must not call or depend on this proposal path.
- Stop on an unresolved App permission choice, a need for broader repository
  access, inability to pin the action, or inability to reproduce Effigy's
  committed verifier independently.
- Work only in the clean worker worktree. Do not merge.

## Important Context

- **Planning lineage:** Effigy architecture `026` -> contract `043` -> spec
  `115` -> roadmap `g08.048` -> card `1108`.
- **Why ready:** card `1106` merged and supplies the exact generated snapshot,
  lock schema, offline verifier, and accepted public-artifact identities that a
  proposal must reproduce.
- **Decisions:** GitHub App, not PAT; short-lived installation token narrowed to
  Effigy contents and pull requests; proposals only; Effigy independently
  validates and retains all review/merge/release authority.
- **Open tensions:** live App identity, installation, secrets, and dispatch are
  intentionally unresolved provider state, not implementation authority. Build
  the fail-closed seam and stop after PR review unless separately authorized.
- **Report after:** workflow/model tests, path/permission adversaries, no-write
  proof, docs, and PR are coherent, or at the first stop condition.
- **Report to:** the operator, who relays completion to the orchestrator.

## Suggested Next Move

Run worker preflight, load the Effigy card and canonical refs through the
required sibling, then inspect the existing publication workflow and baseline
verifier. Design a separate proposal workflow whose token, artifact, diff, and
PR body are deterministic and testable without provider credentials.

## Completion Protocol

Before broad reads, run `git rev-parse --show-toplevel`, `git branch
--show-current`, `git status --porcelain`, and `git worktree list --porcelain`.
Accept a clean launcher-provided non-main registered worktree. Otherwise stop
on a dirty/main launcher checkout; use manual fallback only under the repository
worktree contract.

Fetch with bounded non-interactive SSH. Confirm selected `HEAD == origin/main`,
the planning base is its ancestor, and this handoff exists in selected `HEAD`;
load it with `git show`. Verify the `effigy` sibling resolves to the primary
checkout at or after planning commit `a63b5d5b`. Read this repository's
`AGENTS.md` and Effigy's card, milestone, spec, architecture, contract, and
accepted baseline evidence.

Complete the implementation-only phase in coherent batches. Map every
acceptance/oracle counterexample to named tests. Prove ordinary QA is
network-free and uses no provider writes. Do not manufacture a live success
without an installed App.

Push and open a PR against current catalog-pack `main`. Report URL, exact head,
checks, evidence, unresolved provider checkpoint, and docs-QA classification.
Do not merge. Requested review changes return to this same branch. After an
accepted merge, only an explicit operator authorization may resume this worker
for App/provider setup and a live proposal/evidence phase.

