# Catalog-pack validation

Card 1105 keeps ordinary proof local and fail-closed. Live package, attestation,
visibility, and `stable` writes exist only in the protected publication job
after the implementation PR is merged.

`scripts/catalog_pack.py` checks these boundaries:

1. `pack/` is the only editable asset root. It has one canonical inventory, no
   links or special files, and a computed content identity.
2. The pack manifest and every fragment pass independent foundation shape
   checks. The current Effigy binary performs the authoritative fragment-schema
   validation during the local install smoke.
3. Ongoing support proof resolves `support/catalog-pack-update.toml` from
   Effigy's current default-branch commit, records that commit and blob, checks
   schema/oldest-version agreement, and admits every required version in the
   pack compatibility range. The separate `import-proof` command is the only
   check that uses the one-time import commit/tree/blob.
4. The OCI layout uses fixed JSON, sorted raw-file layers, the pack content ID,
   and the pack repository commit/timestamp as source-derived annotations.
   Rebuilding it produces the same manifest digest.
5. `rehearse` still models absent, same-digest, and collision outcomes without a
   push. `publication-check` runs the ordered transaction against an in-memory
   registry and proves fail-closed collision, stale support, private/unattested
   subjects, plan-only mode, and the live mutate gate.

The GET-only `support-releases` command checks that a GitHub Release exists for
every required version and that `as_of_release` equals the latest non-draft,
non-prerelease Effigy release. It is not part of `doctor`, `validate`, or `qa`.

The independent commands are:

```sh
python3 scripts/catalog_pack.py validate
python3 scripts/catalog_pack.py validate --effigy-root ../effigy --require-authority
python3 scripts/catalog_pack.py import-proof --effigy-root ../effigy
python3 scripts/catalog_pack.py publication-check --effigy-root ../effigy --require-authority
python3 scripts/catalog_pack.py support-releases --effigy-root ../effigy
```

Only `import-proof` requires the pack bytes to remain the one-time import
snapshot. Routine `validate`, `effigy test`, and `effigy qa` do not.

The two workflows stay narrow:

- `validate.yml` runs read-only checks for pull requests and `main` pushes. It
  checks out Effigy `main` for current support and never passes `--mutate`.
- `publication.yml` is manual, accepts only an existing annotated source tag
  plus its full peeled commit, and names the protected
  `catalog-pack-publication-rehearsal` environment. Job permissions are
  `contents: read` plus `packages`, `id-token`, and `attestations` write. It is
  the only workflow that may set `CATALOG_PACK_PUBLICATION_MUTATE=1` and pass
  `--mutate`. `workflow-check` still rejects raw `inputs.*` expressions in
  `run:` blocks and tests a malicious counterexample.
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
