---
kind: northstar-handoff
title: "Effigy g10.018 — Browser runtime catalog-pack source"
handoff_mode: worker-pr-loop
worker_mode: implementation
dispatch_authority: orchestrator
status: closed
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

- PR [#7](https://github.com/inflatable-cookie/effigy-catalog-pack/pull/7) merged to `main` at `76d594d8e72731547c0c2918746d5c98291d77b4` on 2026-09-25. The reviewed PR head was `f009a8c6718cbcf0c602dadea5938158cfeabeca`.
- The independent exact-head review posted `ready_to_merge` for that head; the hosted `validate` check passed. The merge contains no publication or release mutation.
- The merged pack is `effigy-default-catalog` `1.1.0`, compatible with `>=0.13, <0.14`. Its verified content ID is `sha256:e92cc2f217fa2ba4de302b8376ec558afb042acd3a83e4d33ecfb03dc40606a3` (42 files, 90,852 bytes).
- `browser_runtime` remains `none` by default; `chromium` installs only runtime libraries and fonts. The effective Dockerfile and service source remain byte-identical to the retained `g10.017` implementation, so its linux-arm64 non-root Playwright launch evidence still applies.
- The retained Effigy worker `1b3aa4b0-d492-4e5e-be92-96b972d07296` and its worktree remain preserved. No tag, OCI package, attestation, visibility, or `stable` mutation was made.
- The approved next pointer remains `g10.019` for separately gated publication. `g10.017` can import exact published bytes and provenance after that step.

## Boundaries

Follow the task card's owned paths. Keep `browser_runtime` default `none`; `chromium` adds only root-installed Debian runtime libraries and fonts. Do not bake a browser, Playwright, Node, or `npx` into the image. Do not edit Effigy, the Underlay bundle, Acowtancy, publication workflows, tags, OCI packages, or `stable` in this task.

## Important Context

Read this repository's `AGENTS.md`, `README.md`, `docs/validation.md`, `pack/pack.toml`, the task card, and the retained Effigy worker diff and smoke log. Recreate the approved option in canonical source rather than copying an unreviewed generated snapshot blindly. Choose a truthful next SemVer version and compatibility including released Effigy 0.13.0. Run `effigy qa` and a focused Effigy consumer assembly proof. If effective Dockerfile or package bytes differ from the proven image, repeat the linux-arm64 non-root Playwright launch. The evidence is under the retained Effigy worktree's `docs/logs/2026-09/25-101900-g10-017-chromium-workspace-runtime.md`.

## Suggested Next Move

Use the merged source identity in `g10.019`'s separately gated publication. After publication, `g10.017` can import the exact artifact bytes and provenance.

## Completion Protocol

This task is closed. The exact-head review and hosted check passed before merge; the merged source commit, version, compatibility, content identity, and arm64-smoke relation are recorded above and in [the closeout log](../logs/2026-09/25-102300-browser-runtime-pack-source-g10-018-closeout.md). `effigy pack:validate` also passed on the merged source. The historical import byte-equality proof remains expected to fail until the separately published artifact is imported. No publication was performed here. The origin Chatterbox can continue from the preserved `g10.019` next pointer.
