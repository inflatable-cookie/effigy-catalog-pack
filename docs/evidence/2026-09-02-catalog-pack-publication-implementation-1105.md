# Catalog-pack first-publication implementation — 2026-09-02

Card: `1105-publish-first-official-catalog-pack`
Phase: implementation PR only. No live mutation.

## Support / import split

Ongoing support proof now resolves Effigy's current default-branch commit and
records that commit plus the support-file blob. This implementation observed:

- support commit: `ee7821464e17927593a358d2166bf1897fcc9b12`
- support blob: `20d0194d52c0bbf46677f8d77ca96fb4505df50e`
- `as_of_release`: `0.12.1`
- `required_versions`: `["0.12.1"]`
- pack compatibility `>=0.12, <0.13` admits `0.12.1`

The one-time import pin remains only on `import-proof`:

- import commit: `055595340c2219d3d47296072f5818c524c341f0`
- catalog tree: `539471162c4976551ac720fdcffe6a1de33cef0f`
- import-era support blob: `20d0194d52c0bbf46677f8d77ca96fb4505df50e`

The blob may match while the commits stay distinct. That is expected until
Effigy changes the support file.

GET-only `support-releases` confirmed GitHub release `v0.12.1` as latest
non-draft/non-prerelease and as the required version.

## Protected transaction, still unrun

`publication.yml` is the bounded write path. It stays `workflow_dispatch`, uses
the existing protected environment `catalog-pack-publication-rehearsal`, and
grants `packages`, `id-token`, and `attestations` write only on that job.
`validate.yml` remains `contents: read` and never passes `--mutate`.

Live writes also require `GITHUB_ACTIONS`, `workflow_dispatch`, this repository,
that environment, and `CATALOG_PACK_PUBLICATION_MUTATE=1`. Ordinary
`catalog_pack.py` entry does not import the live registry adapter.

In-memory transaction proof established this write order for a first
publication:

1. package version
2. public visibility / repository linkage
3. digest-bound attestation
4. `stable`
5. rollback exercise
6. restore `stable` to the candidate

Different-digest collision, stale support, private package, and unattested
subject all stop before `stable`. Same-digest retry does not overwrite.

## No live mutation in this phase

Recorded at this implementation head:

- no `v*` source tag in this repository
- `GET /users/inflatable-cookie/packages/container/effigy-catalog-pack` → 404
- `provider-controls` remained GET-only
- `publication-check` `live_mutation` is false

Do not create `v1.0.0`, dispatch `publication.yml`, or contact a registry write
surface until this PR is accepted and merged and the same worker is resumed.
