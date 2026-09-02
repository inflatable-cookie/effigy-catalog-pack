# Catalog-Pack First Official Publication 1105

Date: 2026-09-02
Card: `1105`
Kind: publication and channel evidence (immutable live record)

## Source Identities

- recovery source: annotated `v1.0.1`, tag object
  `2bb561109dfe8ec1346779370e2e9f428ef5ddd2`, peeling to merged main
  `5ef0ec2b64612c7803cc6105a65ea462862a0b21` (reviewed repair PR `#3` head
  `e580d42516e5ec2a77e49b3e032da946d7fb643c`);
- preserved incident source: annotated `v1.0.0`, tag object
  `f2b59e65b1938600907de8dea566ad957e63be69`, peeling to
  `f70637abe1024cf7b54cabe58c3bd5877dcf8eca`; never moved, deleted, recreated,
  or dispatched against (see [the recovery record](2026-09-02-catalog-pack-recovery-1105.md));
- pack content identity: `sha256:9498d33f1eccbb91e971b55f5169830baca26326a8f802408a0432e733254974`
  (`effigy-default-catalog` `1.0.1`, compatibility `>=0.12, <0.13`).

## Protected Publication Run

Run [`33626891555`](https://github.com/inflatable-cookie/effigy-catalog-pack/actions/runs/33626891555),
dispatched 2026-09-02T11:52:42Z against `main` with canonical inputs
`source_tag=v1.0.1`, `source_ref=5ef0ec2b64612c7803cc6105a65ea462862a0b21`,
concurrency group `catalog-pack-publication-v1.0.1`.

- `publish` job `100236646172` succeeded (protected environment deployment
  `6221719111`): source validation, current Effigy support proof
  (`f3800c8c6e4ba8f5ebfecce5fdfaa6fdab3d9509`, blob
  `20d0194d52c0bbf46677f8d77ca96fb4505df50e`), release freshness (`v0.12.1`),
  deterministic candidate build, first-read remote inspection (the repaired
  classifier path), and one version-pointer push.
- The operator completed the documented package-settings visibility
  checkpoint between the jobs; finalize stayed unapproved until then.
- `finalize` job `100236883736` succeeded (protected environment deployment
  `6221732516`): finalize-preflight re-verified `same-digest` version state,
  unchanged support identity, and public package linkage; pinned
  `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6` attached
  digest-bound provenance with `push-to-registry`; then anonymous exact-byte
  pull, support authority refetch, and one `stable` move. Run conclusion:
  `success`. No manifest was ever deleted.

## Immutable Artifact Identity

- OCI manifest digest:
  `sha256:91de584e77487765c24f53abb63413783a99c0a7926c25aee1289a3cf370d9f3`.
  Proven twice: deterministic recompute through the tagged code from the real
  tag identity, and authenticated GET-only registry read returning the same
  `docker-content-digest`.
- `stable` registry read (GET-only):
  `docker-content-digest: sha256:91de584e77487765c24f53abb63413783a99c0a7926c25aee1289a3cf370d9f3`.
  The finalize report records `previous_stable: null` (first-publication
  absent-target branch: non-mutating rollback-to-absence model, live `stable`
  move exactly once) and exactly one write,
  `["stable", "sha256:91de584e…"]`.

## Attestation

`gh attestation download` verified the sigstore bundle against the trusted
root and produced
`sha256:91de584e77487765c24f53abb63413783a99c0a7926c25aee1289a3cf370d9f3.jsonl`:
media type `application/vnd.dev.sigstore.bundle.v0.3+json`, predicate
`https://slsa.dev/provenance/v1` (the contract's required provenance
predicate), subject `ghcr.io/inflatable-cookie/effigy-catalog-pack` with
digest map `{"sha256": "91de584e…"}` — exact digest binding.

## Anonymous Pull

With a credentials-less token exchange (no user identity), a digest-addressed
`GET https://ghcr.io/v2/inflatable-cookie/effigy-catalog-pack/manifests/sha256:91de584e…`
returned `200` with `docker-content-digest` `sha256:91de584e…` and a body
whose sha256 equals that digest byte-for-byte. While the package was private,
the same anonymous exchange was correctly refused (`401`) before the operator
visibility checkpoint — the fail-closed behavior finalize later re-proved in
reverse.

## Package State

- org package `effigy-catalog-pack`, type `container`,
  visibility `public`, linked repository `inflatable-cookie/effigy-catalog-pack`;
- version `1200107352` carries both `v1.0.1` and `stable` tags (same manifest,
  therefore the same digest); the attestation artifact (`1200380429`,
  referrers tag `sha256-91de584e…`) and its internal index entry (`1200380396`)
  complete the three version records.

## Provider State

- selected-actions allowlist: exactly `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`
  and `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6`; live
  observation verified with `write_methods_used: []`;
- `v*` tag ruleset `22050144` active (deletion/update blocked, no bypass,
  including for the operator);
- protected environment `catalog-pack-publication-rehearsal`: single required
  reviewer, administrator bypass disabled, two deployments approved and
  recorded.

## Notes

- `effigy doctor` reports one warning-level `scan.god-files` finding on
  `scripts/catalog_pack_live_tests.py` (252 code lines) from the review-mandated
  adversarial fixtures; error count zero. Recorded here as known repository
  hygiene, not a publication defect.
- Card `1105` publication is proved by this record; the card completes when
  this evidence is reviewed and merged. Card `1106` (generated Effigy
  baseline) remains blocked until then.
