# Papercuts

Small, actionable friction found during agent work. Agents append entries when
they hit a solvable hurdle; they do not stop the current task to fix one.

## Open

<!-- Keep entries short. Append newest entries at the top. Do not include secrets. -->

### [ ] Protected publication environment still named rehearsal — 2026-09-02
- Friction: GitHub environment `catalog-pack-publication-rehearsal` is the live publication gate
- Impact: workflow and evidence keep a rehearsal name after the job became the real write path
- Possible fix: rename the environment after an explicit settings mutation is authorized
- Surface: GitHub environment, `.github/workflows/publication.yml`, hosted-controls.json

## Closed

### [x] User package visibility PATCH is undocumented — 2026-09-02
- Resolution: first publication publishes the private version, then the operator makes the linked organization package public through GitHub package settings. Finalize GET-verifies `orgs/inflatable-cookie/packages/container/effigy-catalog-pack` before attestation, anonymous pull, and `stable`. No REST PATCH is part of the transaction.
