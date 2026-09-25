# g10.019 Browser Runtime Catalog-Pack Publication — Closeout

Status: closed after accepted exact-head review, passing hosted validation, and merge.

Canonical task card: Effigy sibling `docs/roadmaps/g10/019-publish-browser-runtime-catalog-pack.md`.

## Outcome

Evidence PR [#8](https://github.com/inflatable-cookie/effigy-catalog-pack/pull/8) merged to `main` at `7fd4beaf105ce190bdea31c2a9c60ef1d8d6b4bb` on 2026-09-25 10:49:45 UTC. Its exact reviewed head was `7881d8f9b12826ed38329945022c85b846493bb4`. The PR adds the publication record only; it changes no pack content, workflow, script, or provider setting.

The protected publication succeeded for the reviewed `g10.018` source:

- Annotated source tag `v1.1.0`, tag object `72f5d7551dc0430fcc83af36066463bd9f1aab82`, peels to `c932c58f64cafd10a70d24907dc77fb81230bb01`.
- Workflow run [36124764718](https://github.com/inflatable-cookie/effigy-catalog-pack/actions/runs/36124764718) completed successfully; both protected `publish` and `finalize` jobs passed.
- OCI reference `ghcr.io/inflatable-cookie/effigy-catalog-pack:v1.1.0` resolves to `sha256:5699fcb8641424cc6365feb2a4c4cc7f6056de385fc9dc49f771aec63f6078ba`. `stable` reads back to the same digest after the recorded rollback exercise.
- Digest-bound `https://slsa.dev/provenance/v1` attestation independently verified for that digest. An anonymous pull reproduced all 42 files byte-for-byte.
- Pack identity is `effigy-default-catalog` `1.1.0`, compatibility `>=0.13, <0.14`, content ID `sha256:e92cc2f217fa2ba4de302b8376ec558afb042acd3a83e4d33ecfb03dc40606a3`, 42 files and 90,852 bytes. Support authority was Effigy commit `b231d91d0fa7147d4f7429d112e43e816ceccd06`, blob `38c88a550616f2ed9ed688306c8c841674bd2eb8`, release `0.13.0`.

The full immutable provider evidence is in [the merged evidence record](../../evidence/2026-09-25-browser-runtime-pack-publication-g10-019.md).

## Review and validation

- Independent reviewer `betterthanclay` posted `ready_to_merge` for exact head `7881d8f9b12826ed38329945022c85b846493bb4` in [the PR review comment](https://github.com/inflatable-cookie/effigy-catalog-pack/pull/8#issuecomment-5831153620).
- Hosted `Validate catalog pack` check passed: [run 36125143452](https://github.com/inflatable-cookie/effigy-catalog-pack/actions/runs/36125143452/job/108039417687).
- The reviewer reported all exit 0 for network-free `pack:validate`, `pack:support`, `pack:oci`, `pack:rehearse`, `pack:publication-check`, `pack:proposal-check`, `pack:workflow-check`, the foundation test suite, and `effigy-smoke`. Their independent GET-only checks reproduced the tag, OCI digest, provenance, public exact-byte pull, and package state.
- The authoritative publication candidate digest `sha256:5699fcb8…` differs from the pre-check candidate `sha256:f378b83c…` because the pre-check omits annotated-tag identity. The protected transaction rebuilt and verified the actual annotated-tag candidate; publication, attestation, and registry reads agree on `sha256:5699fcb8…`.

## Deferred state

- The optional `actions/attest` `create-storage-record` step warned that `artifact-metadata:write` was not granted, so no artifact metadata storage record was persisted. The digest-bound attestation verified; workflow permission changes were outside this card's scope.
- The independent reviewer received 403 from the plan-gated rulesets endpoint. The `v*` ruleset detail therefore rests on the live observation at 2026-09-25 10:38:14 UTC recorded in the evidence; this PR did not change provider settings.
- `pack:import-proof` remains expected to fail until `g10.017` imports the published bytes, because the canonical pack has advanced beyond Effigy's historical one-time import snapshot. That task remains the approved next pointer and can resume only after Queue callback identity is reconciled.

## Next pointer

Preserve the approved sequence: resume retained `g10.017` after Queue callback identity reconciliation; import the exact `v1.1.0` bytes and provenance, then continue the downstream Underlay work. Canonical readiness and planning remain in the Effigy sibling.
