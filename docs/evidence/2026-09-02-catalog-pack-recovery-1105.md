# Catalog-Pack Publication Recovery 1105

Date: 2026-09-02
Card: `1105`
Kind: incident evidence and recovery authority record

## Failed First Publication Attempt

The implementation PR merged at `f70637abe1024cf7b54cabe58c3bd5877dcf8eca`.
After green `effigy doctor`, `effigy validate`, `effigy qa`, GET-only
`support-releases`, and live `provider-controls`, the worker:

1. added exactly the pinned `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6`
   action to the repository selected-actions policy beside the pinned
   `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` action;
2. created the annotated source tag `v1.0.0` at that merge (tag object
   `f2b59e65b1938600907de8dea566ad957e63be69`, peeled commit
   `f70637abe1024cf7b54cabe58c3bd5877dcf8eca`) and pushed it; and
3. dispatched `publication.yml` (run `33622687650`, 2026-09-02T11:04:13Z) with
   `source_tag=v1.0.0` and `source_ref=f70637abe1024cf7b54cabe58c3bd5877dcf8eca`,
   approving the protected `catalog-pack-publication-rehearsal` environment
   for the publish job (deployment `6220923864`).

The publish job failed at the step `Publish the version pointer` on its first
GHCR descriptor read, before any write attempt. Exact stderr:

```text
Error response from registry: failed to find "ghcr.io/inflatable-cookie/effigy-catalog-pack:v1.0.0": ghcr.io/inflatable-cookie/effigy-catalog-pack:v1.0.0: not found
```

`classify_registry_inspect` modeled ORAS absence as `manifest unknown`, HTTP
`404`, or `failed to fetch descriptor: ... not found`. Live ORAS `1.3.3`
against GHCR reports absence as `failed to find "<ref>": <ref>: not found`,
which matched none of those shapes, so the seam failed closed as designed.
The finalize job never started.

## Preserved Failure State

Proved by live read-back after the failed run:

- annotated `v1.0.0` still names tag object
  `f2b59e65b1938600907de8dea566ad957e63be69` and peels to
  `f70637abe1024cf7b54cabe58c3bd5877dcf8eca`; ruleset `22050144` ("Protect v*
  catalog-pack release tags") stays active against deletion and update with no
  bypass actors; the tag is never moved, deleted, recreated, or dispatched
  against;
- the organization package `ghcr.io/inflatable-cookie/effigy-catalog-pack`
  does not exist (`404` on the org package route); no OCI `v1.0.0` package
  version will be invented;
- no attestation exists and no `stable` pointer exists.

Retained provider identities: selected-actions contains exactly the two
authorized pinned actions; the protected environment keeps its single required
reviewer with administrator bypass disabled; default workflow permissions stay
`read`; the live observation is recorded in
[live-provider-controls.json](live-provider-controls.json).

## Recovery Decision

The operator selected the contract-valid recovery recorded in Effigy's
authority log (`02-003915-catalog-pack-first-publication-authority-1105`,
"Failed Attempt And Recovery Decision"): keep `v1.0.0` immutable, land the
exact live-stderr classifier fixture with narrow absence classification,
reconcile the selected-actions live oracle, bump the pack to `1.0.1`, and
retry the protected first-publication transaction only from a reviewed
`v1.0.1` repair head.

Declared recovery delta for the pack tree: the manifest version field only.
The imported catalog bytes remain byte-identical to the one-time import tree
`539471162c4976551ac720fdcffe6a1de33cef0f`, which `import-proof` still
checks. The foundation content identity
`sha256:511d120f181505f8ecced7687b564c4663663eca8f6f68b2b562c9b676feb29e`
recorded in the 1104 foundation evidence remains the historical `1.0.0` fact;
the current pack content identity is
`sha256:9498d33f1eccbb91e971b55f5169830baca26326a8f802408a0432e733254974`.
