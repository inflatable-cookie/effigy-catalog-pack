---
kind: northstar-handoff
title: "Effigy g10.018 — Browser runtime catalog-pack source"
handoff_mode: worker-pr-loop
worker_mode: implementation
dispatch_authority: orchestrator
status: ready-to-launch
base_required: pushed-main
queue_dispatch: northstar-queue
queue_approval: "Tom approved the catalog-pack source PR and, after review, separately gated pack publication on 2026-09-25. This task covers the source PR only."
queue:
  capability: general
  notifyOriginOnCloseout: true
---

## What This Thread Was Doing

Implement Effigy [g10.018](/Users/tom/Dev/projects/effigy/docs/roadmaps/g10/018-browser-runtime-catalog-pack-source.md) in this canonical `effigy-catalog-pack` repository. The task card owns scope and acceptance; `pack/` is the editable source of Effigy's generated catalog baseline.

## Why It Matters

Acowtancy's non-root linux-arm64 workspace needs Chromium runtime libraries. The Effigy `g10.017` worker proved an opt-in image and a real Playwright 1.55.1 Chromium launch, but its direct edit to Effigy's generated catalog fails the pinned pack provenance lock. A reviewed source pack change must precede publication and honest baseline import.

## Current State

- Start from pushed `main` in this repository. Queue creates an isolated worker workspace and independent review.
- Pack `v1.0.1` is the current published baseline; `pack/pack.toml` says `1.0.1` and `>=0.12, <0.13`. Released Effigy `v0.13.0` is current and its support policy requires 0.13.0.
- The retained Effigy worker `1b3aa4b0-d492-4e5e-be92-96b972d07296` has uncommitted implementation and smoke evidence under `/Users/tom/.paseo/worktrees/310mya31/ns-3ed8c61d-444d-47da-8630-60d510ae3d2f`. Read it only; do not commit, reset, or clean that worktree.
- `g10.019` will own publication after this source PR merges. `g10.017` will then import exact published bytes and provenance.

## Boundaries

Follow the task card's owned paths. Keep `browser_runtime` default `none`; `chromium` adds only root-installed Debian runtime libraries and fonts. Do not bake a browser, Playwright, Node, or `npx` into the image. Do not edit Effigy, the Underlay bundle, Acowtancy, publication workflows, tags, OCI packages, or `stable` in this task.

## Important Context

Read this repository's `AGENTS.md`, `README.md`, `docs/validation.md`, `pack/pack.toml`, the task card, and the retained Effigy worker diff and smoke log. Recreate the approved option in canonical source rather than copying an unreviewed generated snapshot blindly. Choose a truthful next SemVer version and compatibility including released Effigy 0.13.0. Run `effigy qa` and a focused Effigy consumer assembly proof. If effective Dockerfile or package bytes differ from the proven image, repeat the linux-arm64 non-root Playwright launch. The evidence is under the retained Effigy worktree's `docs/logs/2026-09/25-101900-g10-017-chromium-workspace-runtime.md`.

## Suggested Next Move

Inspect `pack/workspace-rust-bun` and the retained implementation diff. Add the default-off parameter, Compose arg, and bounded Dockerfile branch to pack source; update version, compatibility, tests, and pack docs. Validate before opening one non-draft source PR.

## Completion Protocol

Obtain independent exact-head review and green current-base CI before Queue merges. Record the merged source commit, new version, compatibility, source content identity, and relation to the arm64 smoke. Do not perform publication here. Notify the origin Chatterbox on closeout so `g10.019` can proceed through its separate protected publication gate.
