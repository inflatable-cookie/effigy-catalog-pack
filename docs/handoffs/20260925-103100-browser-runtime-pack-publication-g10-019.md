---
kind: northstar-handoff
title: "Effigy g10.019 — Publish browser runtime catalog pack"
handoff_mode: worker-pr-loop
worker_mode: implementation
dispatch_authority: orchestrator
status: ready-to-launch
base_required: pushed-main
queue_dispatch: northstar-queue
queue_approval: "Tom explicitly approved the catalog-pack PR and, after independent review, the separately gated pack publication on 2026-09-25. Pack PR #7 is reviewed and merged; this handoff names the publication gate for v1.1.0 only."
queue:
  capability: complex
  notifyOriginOnCloseout: true
---

## What This Thread Was Doing

Execute Effigy [g10.019](/Users/tom/Dev/projects/effigy/docs/roadmaps/g10/019-publish-browser-runtime-catalog-pack.md): publish the reviewed browser-capable catalog pack `v1.1.0` through this repository's protected manual transaction, then open one narrow evidence PR for independent review.

## Why It Matters

Effigy's built-in catalog is a generated recovery snapshot. The retained `g10.017` worker cannot honestly update its `v1.0.1` provenance lock for new Chromium runtime bytes. The canonical `g10.018` source PR #7 is now reviewed and merged. A digest-bound published `v1.1.0` artifact supplies the exact source and OCI identity required for Effigy's baseline import.

## Current State

- Queue closed `g10.018` after PR #7: reviewed head `f009a8c6718cbcf0c602dadea5938158cfeabeca`, merge `76d594d8e72731547c0c2918746d5c98291d77b4`, pack main closeout `c932c58f64cafd10a70d24907dc77fb81230bb01`.
- Pack `pack/pack.toml` declares `1.1.0` and `>=0.13, <0.14`. Released Effigy `v0.13.0` and current support policy require `0.13.0`.
- Read-only checks on pack main passed on 2026-09-25: `effigy pack:provider-controls`, `pack:support-releases`, `pack:publication-check`, and `pack:rehearse`. `v1.1.0` source tag was absent and the organization package was public. Recheck all live facts immediately before writing.
- Queue creates an isolated worker workspace from pushed pack main. The retained Effigy `g10.017` worker/worktree stay parked; do not edit them.

## Boundaries

This handoff is the explicit operator gate for only the new `v1.1.0` pack publication after reviewed PR #7. Use the existing protected `publication.yml` workflow and environment. The canonical source tag must be an annotated `v1.1.0` tag peeling to exactly `c932c58f64cafd10a70d24907dc77fb81230bb01`; do not choose a newer unreviewed source commit or move/reuse any existing tag. Do not alter workflow code, provider settings, Effigy, Underlay bundle, Acowtancy, or the retained `g10.017` workspace. Preserve failed or uncertain publication evidence and stop rather than re-tagging or blind retrying.

## Important Context

Read `AGENTS.md`, `README.md`, `docs/validation.md`, Effigy contract `043`, the `g10.019` task card, publication scripts and workflow, and the `g10.018` review/closeout. Verify remote source, tag absence, current support commit/blob, Effigy release, provider controls, and public package state. The workflow's `publish` job may create the OCI version pointer; `finalize` requires the protected environment checkpoint, digest-bound attestation, anonymous pull, exact-byte validation, and safe `stable` movement. Record each actual immutable identity and provider result. The rehearsal's synthetic tag digest is not the live artifact digest.

## Suggested Next Move

Run the read-only preflight again in the Queue worktree and inspect the exact workflow inputs. If source and provider facts still match, create the annotated source tag at `c932c58f64cafd10a70d24907dc77fb81230bb01` and invoke protected `publication.yml` with `source_tag=v1.1.0` and `source_ref` equal to that full commit. Follow its environment and visibility checkpoints. Stop and report a specific blocker if the protected gate or any publication proof cannot complete.

## Completion Protocol

After version publication and finalize succeed, verify source tag object/peeled commit, OCI digest, attestation, anonymous exact-byte pull, and `stable` read-back. Open one non-draft evidence PR; Queue obtains independent exact-head review, current-base CI, merge, and closeout. Report the accepted artifact digest and source provenance for `g10.017` baseline import. Publication itself is not evidence of task closeout.
