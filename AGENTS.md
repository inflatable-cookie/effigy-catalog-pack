# Agent Instructions For Effigy Catalog Pack

This public repository owns the canonical editable catalog-pack source. Effigy
owns runtime behaviour, compatibility authority, and its generated recovery
snapshot.

## Where things live

- Current state and how the pack works: `README.md`
- Knowledge (one owner per fact): `docs/knowledge/README.md`
- How a pack is published: `docs/knowledge/contracts/release.md`
- What's next: `docs/plan.md`

Tasks, briefs and status live in Queue, never in this repository (lean
Northstar, `northstar-lean` skill).

## Product rules

- Keep canonical assets under `pack/`. Do not create a second editable asset
  root.
- Treat the Effigy sibling checkout as a read-only authority; never edit it
  from this repository.
- Keep ordinary validation network-free. Only `support-releases` and
  `provider-controls` make network calls, and those are GET-only.
- The failed pre-push `v1.0.0` publication attempt is immutable incident
  evidence: annotated tag object `f2b59e65b1938600907de8dea566ad957e63be69`,
  peeling to `f70637abe1024cf7b54cabe58c3bd5877dcf8eca`. Never move, delete,
  recreate or dispatch against it, and never invent an OCI `v1.0.0` version.
- `docs/evidence/*.json` are read by the scripts; keep their paths.

## Guardrails

- Never publish, tag, change package visibility, move `stable`, edit
  `.github/workflows/`, or perform any release mutation without an explicit
  operator instruction.
- GitHub App registration or installation, secret writes and workflow
  dispatch always need a separate operator go-ahead.

## Validate

`effigy qa` before opening a PR.
