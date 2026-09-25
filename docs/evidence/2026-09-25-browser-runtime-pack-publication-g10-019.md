# Browser Runtime Catalog-Pack Publication g10.019

Date: 2026-09-25
Card: `g10.019`
Kind: publication and channel evidence (immutable live record)

## Source Identities

- source commit: merged `g10.018` closeout
  `c932c58f64cafd10a70d24907dc77fb81230bb01`, commit time
  `2026-09-25T10:28:40Z`, from reviewed/merged PR
  [#7](https://github.com/inflatable-cookie/effigy-catalog-pack/pull/7)
  (reviewed head `f009a8c6718cbcf0c602dadea5938158cfeabeca`, merge
  `76d594d8e72731547c0c2918746d5c98291d77b4`);
- canonical annotated source tag `v1.1.0`, tag object
  `72f5d7551dc0430fcc83af36066463bd9f1aab82`, peeling to exactly that
  commit. The tag was absent from `origin` immediately before creation; after
  the push, `git ls-remote --tags origin` read back
  `72f5d7551dc0430fcc83af36066463bd9f1aab82 refs/tags/v1.1.0` and
  `c932c58f64cafd10a70d24907dc77fb81230bb01 refs/tags/v1.1.0^{}`.
  This is the only tag created for this card;
- pack content identity:
  `sha256:e92cc2f217fa2ba4de302b8376ec558afb042acd3a83e4d33ecfb03dc40606a3`
  (`effigy-default-catalog` `1.1.0`, compatibility `>=0.13, <0.14`,
  42 files, 90,852 bytes);
- preserved incident and prior records: annotated `v1.0.0` (tag object
  `f2b59e65b1938600907de8dea566ad957e63be69`, peeled
  `f70637abe1024cf7b54cabe58c3bd5877dcf8eca`) was not moved, deleted,
  recreated, or dispatched against, and no `v1.0.0` OCI version was invented;
  the previous published version `v1.0.1` (tag object
  `2bb561109dfe8ec1346779370e2e9f428ef5ddd2`, peeled
  `5ef0ec2b64612c7803cc6105a65ea462862a0b21`) is unchanged.

The dispatch base was pushed `main`
`0d79d43f4e879e357c912bebaf7abcf64529de70`.

## Read-Only Preflight

Run in the isolated Queue worktree immediately before the tag write:

- `pack:validate`, `pack:support`, `pack:rehearse` and `pack:publication-check`
  passed against Effigy authority commit
  `b231d91d0fa7147d4f7429d112e43e816ceccd06`, support blob
  `38c88a550616f2ed9ed688306c8c841674bd2eb8`, `as_of_release = "0.13.0"`,
  `required_versions = ["0.13.0"]`;
- `pack:support-releases` (GET-only) confirmed `v0.13.0` as the latest
  non-draft, non-prerelease Effigy release with `write_methods_used: []`;
- `pack:provider-controls` (GET-only) verified at
  `2026-09-25T10:34:23Z` with `verified: true` and `write_methods_used: []`;
- registry state read anonymously: tag `v1.1.0` absent, `stable` pointing at
  `sha256:91de584e77487765c24f53abb63413783a99c0a7926c25aee1289a3cf370d9f3`
  (`v1.0.1`); org package `effigy-catalog-pack` was already `public` and
  linked to `inflatable-cookie/effigy-catalog-pack`.

## Protected Publication Run

Run [`36124764718`](https://github.com/inflatable-cookie/effigy-catalog-pack/actions/runs/36124764718),
dispatched 2026-09-25T10:35:02Z against `main` with canonical inputs
`source_tag=v1.1.0`,
`source_ref=c932c58f64cafd10a70d24907dc77fb81230bb01`, concurrency group
`catalog-pack-publication-v1.1.0`. Workflow
`.github/workflows/publication.yml` was used exactly as committed on `main` at
`0d79d43f4e879e357c912bebaf7abcf64529de70`; no workflow, provider setting, or
script was modified. Pinned ORAS 1.3.3 was installed by the workflow.

- `publish` job
  [`108038219008`](https://github.com/inflatable-cookie/effigy-catalog-pack/actions/runs/36124764718/job/108038219008)
  succeeded (protected environment deployment `6658819668`): independent source
  validation, current Effigy support proof (same commit/blob as preflight),
  release freshness, deterministic candidate build, first-read remote
  inspection (version `absent`), then one version-pointer push
  (`oras cp --from-oci-layout`). Gates recorded:
  `source-identity`, `support-local`, `support-releases`, `candidate`,
  `remote-version`, `package-version`, `version-reresolve`;
  `version_state: "absent"`, `push_attempted: true`, writes exactly
  `[["package-version", "sha256:5699fcb8…"]]`. `previous_stable` was
  `sha256:91de584e…`.
- Operator checkpoint between the jobs: the linked organization package was
  already `public` and correctly linked, and the new version pointer was
  anonymously pullable, so the documented package-settings checkpoint needed no
  change and no visibility PATCH was made (the transaction forbids one). The
  `finalize` job was approved only after that check.
- `finalize` job
  [`108038382307`](https://github.com/inflatable-cookie/effigy-catalog-pack/actions/runs/36124764718/job/108038382307)
  succeeded (protected environment deployment `6658828821`):
  `finalize-preflight` re-verified `same-digest` version state, unchanged
  support identity, and public package linkage with `writes: []`; pinned
  `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6` attached
  digest-bound provenance with `push-to-registry`; then anonymous exact-byte
  pull, support authority refetch, and the ordered `stable` writes. Gates:
  `source-identity`, `support-local`, `support-releases`, `candidate`,
  `remote-version`, `visibility-linkage`, `attestation`, `anonymous-pull`,
  `support-recheck`, `stable`.
- Run conclusion `success`, attempt 1, no retry. No manifest was deleted and no
  tag was moved.

## Immutable Artifact Identity

- OCI manifest digest:
  `sha256:5699fcb8641424cc6365feb2a4c4cc7f6056de385fc9dc49f771aec63f6078ba`
  (`application/vnd.oci.image.manifest.v1+json`, 10,604 bytes), tagged
  `ghcr.io/inflatable-cookie/effigy-catalog-pack:v1.1.0`.
- Proven twice: a deterministic recompute from the real annotated-tag identity
  against the merged pack bytes (42 sorted raw-file layers, content ID
  `sha256:e92cc2f2…`) and authenticated plus anonymous registry reads returning
  the same `docker-content-digest`.
- `stable` now resolves to the same digest:
  `sha256:5699fcb8641424cc6365feb2a4c4cc7f6056de385fc9dc49f771aec63f6078ba`.
- The pre-check step `Build and verify the deterministic OCI candidate`
  reported `sha256:f378b83c130f88e0cf8c094f84f430f87cdf37d33cc3e8377520883a74b6c11e`.
  That build intentionally uses the bare source-repository identity, so it
  omits the `io.effigy.catalog.pack.source-tag*` annotations and is a different
  manifest. The authoritative candidate is rebuilt inside
  `publish --phase version` from the actual annotated-tag identity, and that
  phase asserts the durable layout digest equals
  `sha256:5699fcb8…` before the push. The publish/finalize reports and the
  registry all agree on `sha256:5699fcb8…`.

## Attestation

`actions/attest` was invoked with
`subject-name: ghcr.io/inflatable-cookie/effigy-catalog-pack`,
`subject-digest: sha256:5699fcb8…`, `push-to-registry: true`, and reported
`Attestation type: Build Provenance` plus `Attestation created for
ghcr.io/inflatable-cookie/effigy-catalog-pack@sha256:5699fcb8…`. The registry
attestation artifact is `sha256:d52f3f17d2c51aac496d3b9df65a3fc193ced1d0b4b8fd2abbc24f0f308eb1ca`.

Independent verification with
`gh attestation verify oci://ghcr.io/inflatable-cookie/effigy-catalog-pack@sha256:5699fcb8…
--repo inflatable-cookie/effigy-catalog-pack --predicate-type https://slsa.dev/provenance/v1`
succeeded and reported:

- sigstore bundle media type `application/vnd.dev.sigstore.bundle.v0.3+json`;
- predicate type `https://slsa.dev/provenance/v1` (the contract's required
  provenance predicate);
- statement subject `ghcr.io/inflatable-cookie/effigy-catalog-pack` with digest
  map `{"sha256": "5699fcb8…"}` — exact digest binding;
- signer workflow
  `https://github.com/inflatable-cookie/effigy-catalog-pack/.github/workflows/publication.yml@refs/heads/main`,
  trigger `workflow_dispatch`, run invocation
  `https://github.com/inflatable-cookie/effigy-catalog-pack/actions/runs/36124764718/attempts/1`;
- Transparency log entry `logIndex 2954420927` (`integratedTime 1790332566`)
  and `sourceRepositoryVisibilityAtSigning: public`.

Non-blocking provider note: `actions/attest`'s optional `create-storage-record`
step warned that `artifact-metadata:write` is not granted, so no artifact
metadata storage record was persisted. That record is not part of the
digest-bound attestation proof above, and the workflow permissions are outside
this card's authorized scope (`publication.yml` edits are reserved).

## Anonymous Pull

With a credentials-less registry token exchange (no user identity), `GET
https://ghcr.io/v2/inflatable-cookie/effigy-catalog-pack/manifests/<ref>`
returned `200` with `docker-content-digest:
sha256:5699fcb8641424cc6365feb2a4c4cc7f6056de385fc9dc49f771aec63f6078ba` and a
body whose sha256 equals that digest byte-for-byte, for the digest address,
`v1.1.0`, and `stable` alike.

An anonymous `oras pull` of the digest into a credentials-less configuration
materialized all 42 pack files, and the pulled tree compared byte-for-byte
equal to `pack/` (which is unchanged from `c932c58f64cafd10a70d24907dc77fb81230bb01`;
`git diff c932c58… HEAD -- pack` is empty at the dispatch base). The finalize
job independently repeated this exact-byte proof before moving `stable`.

## Package State

- org package `effigy-catalog-pack`, type `container`, visibility `public`,
  linked repository `inflatable-cookie/effigy-catalog-pack`;
- version `1294115514` (2026-09-25T10:35:34Z) carries both `v1.1.0` and
  `stable` tags at digest
  `sha256:5699fcb8641424cc6365feb2a4c4cc7f6056de385fc9dc49f771aec63f6078ba`;
- version `1200107352` retains `v1.0.1` only — `stable` no longer resolves to
  the previous digest;
- attestation artifact is version `1294117936` at digest
  `sha256:d52f3f17d2c51aac496d3b9df65a3fc193ced1d0b4b8fd2abbc24f0f308eb1ca`;
- version `1294117962` is the OCI referrers index pointer carrying the
  subject-derived referrers tag
  `sha256-5699fcb8641424cc6365feb2a4c4cc7f6056de385fc9dc49f771aec63f6078ba`
  at digest `sha256:a7382bddf2c88e6549bcd5e4e9c2f12a32674026eccc8b7255f129f4f4a03a48`.

## Channel Safety

The finalize report records `previous_stable:
sha256:91de584e77487765c24f53abb63413783a99c0a7926c25aee1289a3cf370d9f3`,
`rollback_exercised: true`, and stable writes in the order
`[5699fcb8…, 91de584e…, 5699fcb8…]`: promote the candidate, prove the previous
target is still restorable, then restore the candidate. `forbid_finalize_writes`
rejected any visibility PATCH or manifest delete, and the final `stable` read-back
resolves to the candidate digest with the version pointer unchanged. The
version publish itself asserted that `stable` had not moved.

## Provider State

- selected-actions allowlist: exactly
  `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` and
  `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6`;
  `sha_pinning_required: true`, `github_owned_allowed: false`,
  `verified_allowed: false`;
- `v*` tag ruleset `22050144` "Protect v* catalog-pack release tags" active
  (deletion/update blocked, no bypass actors, `current_user_can_bypass:
  never`);
- protected environment `catalog-pack-publication-rehearsal` id `21041670008`:
  single required reviewer `betterthanclay`, `can_admins_bypass: false`,
  `prevent_self_review: false`; two deployments for this run (`6658819668`,
  `6658828821`), both approved by `betterthanclay` and reported `success`;
- default workflow permissions `read`;
- live observation re-verified after publication at `2026-09-25T10:38:14Z`
  with `write_methods_used: []`.

## Consumer Handoff for g10.017

Exact accepted artifact identity for the generated recovery baseline import:

- source tag `v1.1.0`, tag object
  `72f5d7551dc0430fcc83af36066463bd9f1aab82`, source commit
  `c932c58f64cafd10a70d24907dc77fb81230bb01`;
- OCI reference `ghcr.io/inflatable-cookie/effigy-catalog-pack:v1.1.0`
  (`stable` now resolves to the same manifest), digest
  `sha256:5699fcb8641424cc6365feb2a4c4cc7f6056de385fc9dc49f771aec63f6078ba`;
- pack content ID
  `sha256:e92cc2f217fa2ba4de302b8376ec558afb042acd3a83e4d33ecfb03dc40606a3`,
  42 files, 90,852 bytes, compatibility `>=0.13, <0.14`;
- support authority commit
  `b231d91d0fa7147d4f7429d112e43e816ceccd06`, blob
  `38c88a550616f2ed9ed688306c8c841674bd2eb8`, `as_of_release = "0.13.0"`.

## Notes

- Publication is recorded here; it is not task closeout. Queue owns independent
  exact-head review, current-base CI, merge, and closeout of this evidence PR.
- No Effigy, Underlay bundle, Acowtancy, provider setting, workflow, or retained
  `g10.017` workspace file was changed by this card.
