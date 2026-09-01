# Catalog-pack validation

Card 1104 keeps the public repository proof local and explicit.

`scripts/catalog_pack.py` checks four boundaries:

1. `pack/` has one canonical inventory, no links or special files, and the
   pinned Effigy catalog bytes match exactly.
2. The pack manifest and every fragment pass the foundation shape checks. The
   current Effigy binary performs the authoritative fragment-schema validation
   during the local install smoke.
3. The OCI layout uses fixed JSON, sorted raw-file layers, source-derived
   annotations, and the Effigy content ID. Rebuilding it produces the same
   manifest digest. If ORAS is installed, the proof also pulls the layout back
   and compares every file.
4. The publication rehearsal models only an in-memory ref: absent creates a
   candidate, the same digest is reused, and a different digest is rejected
   without changing state. It does not contact a registry or invoke a push.

The support proof resolves `support/catalog-pack-update.toml` from Effigy commit
`055595340c2219d3d47296072f5818c524c341f0`, verifies its Git blob OID, and
checks the closed `0.12.1` required-version floor. No support file is editable
under `pack/`.

The two workflows are intentionally narrow:

- `validate.yml` runs read-only checks for pull requests and `main` pushes.
- `publication-rehearsal.yml` is manual and names the protected
  `catalog-pack-publication-rehearsal` environment, but still has only
  `contents: read` permission and performs no publication mutation.
