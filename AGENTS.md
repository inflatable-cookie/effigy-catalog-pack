# Agent Instructions For Effigy Catalog Pack

This public repository owns the canonical editable catalog-pack source. Effigy
owns runtime behavior, compatibility authority, and its generated recovery
snapshot.

- Treat `/Users/tom/Dev/projects/effigy` only as the declared read-only sibling
  authority; never edit it from this repository worker.
- Keep canonical assets under `pack/`. Do not create a second editable asset
  root.
- Use Effigy tasks as the repository command surface once the manifest exists.
- Never publish, tag, create or change package visibility, move `stable`, or
  perform a release mutation without an explicit operator gate named by the
  active handoff.
- The failed pre-push `v1.0.0` publication attempt is preserved immutable as
  incident evidence: annotated tag object
  `f2b59e65b1938600907de8dea566ad957e63be69` peeling to
  `f70637abe1024cf7b54cabe58c3bd5877dcf8eca`. Never move, delete, recreate,
  or dispatch against it; no OCI `v1.0.0` package version may be invented.
- Card `1105` recovery authority covers the annotated `v1.0.1` source tag
  created only from a reviewed repair head, the public GHCR package,
  digest-bound attestation, and `stable` movement only. The repair PR must be
  reviewed and merged before those mutations.
- `.github/workflows/` edits are authorized for card `1105` within the
  protected first-publication transaction and its read-only validation path.
- Card `1108` may add the narrow generated-baseline proposal workflow and its
  network-free validation. It does not authorize GitHub App registration or
  installation, secret writes, dispatch, Effigy mutation, approval, merge, or
  release; those provider/live steps require a separate explicit operator gate.
- Keep ordinary validation network-free. Card `1105` may use its protected
  workflow for the named GitHub/GHCR mutations and exact read-back proof.
- Effigy's one-time import commit remains historical byte-import evidence.
  Publication support authority resolves from Effigy's current default-branch
  commit and records that commit plus the support-file blob.
- Worker mode activates only from the committed Northstar handoff under
  `docs/handoffs/`.

The governing architecture, contract, spec, roadmap, and card live in the
Effigy sibling checkout and are named by the active handoff.
