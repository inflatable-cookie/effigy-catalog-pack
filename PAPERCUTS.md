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

### [ ] User package visibility PATCH is undocumented — 2026-09-02
- Friction: GHCR packages default private; REST docs expose visibility on GET but not a first-class public mutation
- Impact: first publication must PATCH `/users/.../packages/container/...` and treat failure as stop, not UI bypass
- Possible fix: replace with a documented GitHub API once one exists
- Surface: `scripts/catalog_pack_live.py` `set_public`
