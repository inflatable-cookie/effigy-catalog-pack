# Catalog-pack first-publication implementation — 2026-09-02

Card: `1105-publish-first-official-catalog-pack`
Phase: implementation PR only. No live mutation.

## Support / import split

Ongoing support proof now resolves Effigy's current default-branch commit and
records that commit plus the support-file blob. This implementation observed:

- support commit: `0a84a911aa7c76202521d676fb716893bd2df857`
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
serializes two jobs on the source tag with `cancel-in-progress: false`.

- `publish` grants `packages: write` and pushes OCI `v1.0.0` only. `stable`
  stays unchanged.
- The operator then makes the linked organization package public through GitHub
  package settings.
- `finalize` waits for that checkpoint, GET-verifies org package public
  linkage, attaches provenance with pinned `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6`,
  pulls anonymously, fetches/rechecks Effigy support and releases, then moves
  `stable`. An absent first-publication `stable` moves once. When a previous
  digest exists, finalization retags candidate → previous → candidate. Live
  retag rollback never deletes a manifest.

Both jobs export `GITHUB_TOKEN`/`GH_TOKEN` from `${{ github.token }}` and set
`GITHUB_ENVIRONMENT` explicitly. Selected-actions provider policy is unchanged
in this PR; adding the attest pin is a post-merge operator step.

`validate.yml` remains `contents: read` and never passes `--mutate`. Live writes
also require `GITHUB_ACTIONS`, `workflow_dispatch`, this repository, that
environment, and `CATALOG_PACK_PUBLICATION_MUTATE=1`. Ordinary `catalog_pack.py`
entry does not import the live registry adapter.

In-memory transaction proof plus injected command-runner tests established:

1. version package write, `stable` unchanged
2. operator visibility checkpoint (no REST PATCH)
3. pinned `actions/attest` in the finalizer
4. anonymous exact-byte pull
5. remote Effigy support/release recheck immediately before `stable`
6. one `stable` move when the prior channel is absent; when a previous digest
   exists, live retag is candidate then previous then candidate
7. fail-closed inspect for auth/timeout/server errors and local
   credential/tool misses, including `credential store: not found`; only 404,
   manifest-unknown, name-unknown, or an ORAS descriptor miss is absence
8. concurrency keyed by the canonical `v<pack-version>` source-tag spelling;
   `refs/tags/v1.0.0` is rejected so it cannot open a parallel mutation lane
9. structured `gh attestation verify --format json` parsed from
   `verificationResult.statement.subject` digest maps; empty, non-JSON,
   wrong-algorithm, and wrong-hex results are rejected
10. version pointer rechecked immediately before any `stable` write

Different-digest collision, stale support, private package, and unattested
subject all stop before `stable`. Same-digest version retry does not overwrite.

## No live mutation in this phase

Recorded at this implementation head:

- no `v*` source tag in this repository
- package metadata remains unpublished; this PR does not PATCH visibility
- `provider-controls` remained GET-only
- `publication-check` `live_mutation` is false
- `docs/evidence/hosted-controls.json` still allows only pinned `actions/checkout`

Do not create `v1.0.0`, dispatch `publication.yml`, change selected-actions, or
contact a registry write surface until this PR is accepted and merged and the
same worker is resumed.
