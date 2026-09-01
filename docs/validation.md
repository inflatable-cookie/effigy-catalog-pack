# Catalog-pack validation

Card 1104 keeps the public repository proof local and explicit.

`scripts/catalog_pack.py` checks five boundaries:

1. `pack/` is the only editable asset root. It has one canonical inventory, no
   links or special files, and a computed content identity.
2. The pack manifest and every fragment pass independent foundation shape
   checks. The
   current Effigy binary performs the authoritative fragment-schema validation
   during the local install smoke.
3. An explicit support proof consumes only Effigy's pinned
   `support/catalog-pack-update.toml` commit/blob. The separate `import-proof`
   command checks the original Effigy catalog inventory and bytes exactly.
4. The OCI layout uses fixed JSON, sorted raw-file layers, the pack content ID,
   and the pack repository commit/timestamp as source-derived annotations.
   Rebuilding it produces the same manifest digest. If ORAS is installed, the
   proof also pulls the layout back and compares every file.
5. The publication rehearsal models only an in-memory ref: absent creates a
   candidate, the same digest is reused, and changed source or annotated-tag
   identity is rejected without changing state. It does not contact a
   registry or invoke a push.

The support proof resolves `support/catalog-pack-update.toml` from Effigy commit
`055595340c2219d3d47296072f5818c524c341f0`, verifies its Git blob OID, and
checks the closed `0.12.1` required-version floor. No support file is editable
under `pack/`; no personal absolute Effigy path is used as a fallback.

The independent commands are:

```sh
python3 scripts/catalog_pack.py validate
python3 scripts/catalog_pack.py validate --effigy-root ../effigy --require-authority
python3 scripts/catalog_pack.py import-proof --effigy-root ../effigy
```

Only the last command requires the pack bytes to remain the one-time import
snapshot. Routine `validate`, `effigy test`, and `effigy qa` do not.

The two workflows are intentionally narrow:

- `validate.yml` runs read-only checks for pull requests and `main` pushes.
- `publication-rehearsal.yml` is manual, accepts only an existing annotated
  source tag plus its full peeled commit, and names the protected
  `catalog-pack-publication-rehearsal` environment. It still has only
  `contents: read` permission, binds dispatch inputs through step `env`, quotes
  the shell variables, and performs no publication mutation. `workflow-check`
  rejects raw `inputs.*` expressions in `run:` blocks and tests a malicious
  counterexample.
- `docs/evidence/hosted-controls.json` is a checked-in static provider
  snapshot consumed by the network-free `workflow-check`; it is not a claim
  that the provider still has those settings or that a hosted run passed.

For an authenticated operator-only closeout, run the separate live verifier:

```sh
python3 scripts/catalog_pack.py provider-controls
# or: effigy pack:provider-controls
```

It uses only explicit GitHub `GET` requests, compares the current Actions
policy, workflow permissions, protected environment, and `v*` ruleset, and
does not read or rewrite the static snapshot. The captured observation is
[`live-provider-controls.json`](evidence/live-provider-controls.json). Hosted
pull-request validation is recorded separately from both provider evidence
files so an evidence commit cannot make its own run evidence self-referential.
