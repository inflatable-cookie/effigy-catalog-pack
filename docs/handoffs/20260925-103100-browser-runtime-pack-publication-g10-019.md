---
kind: northstar-handoff
title: "Effigy g10.019 — Publish browser runtime catalog pack"
handoff_mode: worker-pr-loop
worker_mode: implementation
dispatch_authority: orchestrator
status: closed
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

- PR [#8](https://github.com/inflatable-cookie/effigy-catalog-pack/pull/8) merged to `main` at `7fd4beaf105ce190bdea31c2a9c60ef1d8d6b4bb` on 2026-09-25 10:49:45 UTC. Its reviewed head was `7881d8f9b12826ed38329945022c85b846493bb4`.
- The independent exact-head review posted `ready_to_merge` for that head; hosted `validate` passed. The merged PR adds only the publication evidence record.
- The protected publication completed successfully. Annotated source tag `v1.1.0` (object `72f5d7551dc0430fcc83af36066463bd9f1aab82`) peels to `c932c58f64cafd10a70d24907dc77fb81230bb01`. OCI digest `sha256:5699fcb8641424cc6365feb2a4c4cc7f6056de385fc9dc49f771aec63f6078ba` is bound to SLSA provenance, anonymously pullable, byte-identical to the 42-file pack, and is the final `stable` target.
- The approved next pointer is `g10.017`: resume its retained worker only after Queue callback identity is reconciled, then import these exact published bytes and provenance.

## Boundaries

This handoff is the explicit operator gate for only the new `v1.1.0` pack publication after reviewed PR #7. Use the existing protected `publication.yml` workflow and environment. The canonical source tag must be an annotated `v1.1.0` tag peeling to exactly `c932c58f64cafd10a70d24907dc77fb81230bb01`; do not choose a newer unreviewed source commit or move/reuse any existing tag. Do not alter workflow code, provider settings, Effigy, Underlay bundle, Acowtancy, or the retained `g10.017` workspace. Preserve failed or uncertain publication evidence and stop rather than re-tagging or blind retrying.

## Important Context

Read `AGENTS.md`, `README.md`, `docs/validation.md`, Effigy contract `043`, the `g10.019` task card, publication scripts and workflow, and the `g10.018` review/closeout. Verify remote source, tag absence, current support commit/blob, Effigy release, provider controls, and public package state. The workflow's `publish` job may create the OCI version pointer; `finalize` requires the protected environment checkpoint, digest-bound attestation, anonymous pull, exact-byte validation, and safe `stable` movement. Record each actual immutable identity and provider result. The rehearsal's synthetic tag digest is not the live artifact digest.

## Suggested Next Move

Resume the retained `g10.017` worker after Queue callback identity is reconciled. It can import the exact `v1.1.0` artifact and regenerate the baseline provenance lock.

## Completion Protocol

This task is closed after successful protected publication, accepted exact-head review, passing hosted validation, and merge of evidence PR #8. The source tag, OCI digest, attestation, anonymous exact-byte pull, and `stable` read-back are recorded in the [publication evidence](../evidence/2026-09-25-browser-runtime-pack-publication-g10-019.md) and [closeout log](../logs/2026-09/25-105246-browser-runtime-pack-publication-g10-019-closeout.md). The optional artifact-metadata storage record was not created because the workflow lacked `artifact-metadata:write`; the attestation itself verified. The independent reviewer could not re-read the plan-gated ruleset endpoint (403), so that detail relies on the earlier live observation recorded in the evidence. Continue with the approved `g10.017` pointer only after Queue callback identity reconciliation.
