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
- Card `1105` has explicit authority for the annotated `v1.0.0` source tag,
  public GHCR package, digest-bound attestation, and `stable` movement only.
  Its implementation PR must be reviewed and merged before those mutations.
- `.github/workflows/` edits are authorized for card `1105` only within the
  protected first-publication transaction and its read-only validation path.
- Keep ordinary validation network-free. Card `1105` may use its protected
  workflow for the named GitHub/GHCR mutations and exact read-back proof.
- Effigy's one-time import commit remains historical byte-import evidence.
  Publication support authority resolves from Effigy's current default-branch
  commit and records that commit plus the support-file blob.
- Worker mode activates only from the committed Northstar handoff under
  `docs/handoffs/`.

The governing architecture, contract, spec, roadmap, and card live in the
Effigy sibling checkout and are named by the active handoff.
