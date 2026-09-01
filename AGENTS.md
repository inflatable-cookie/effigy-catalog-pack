# Agent Instructions For Effigy Catalog Pack

This public repository owns the canonical editable catalog-pack source. Effigy
owns runtime behavior, compatibility authority, and its generated recovery
snapshot.

- Treat `/Users/tom/Dev/projects/effigy` only as the declared read-only sibling
  authority during card `1104`; never edit it from this repository worker.
- Keep canonical assets under `pack/`. Do not create a second editable asset
  root.
- Use Effigy tasks as the repository command surface once the manifest exists.
- Never publish, tag, create or change package visibility, move `stable`, or
  perform a release mutation without a later explicit operator gate.
- `.github/workflows/` edits are authorized only for the read-only validation
  and protected manual no-push publication-rehearsal surfaces in card `1104`.
- Keep validation network-free except for the explicitly pinned, read-only
  Effigy support-file resolution proof required by the card.
- Worker mode activates only from the committed Northstar handoff under
  `docs/handoffs/`.

The governing architecture, contract, spec, roadmap, and card live in the
Effigy sibling checkout and are named by the active handoff.
