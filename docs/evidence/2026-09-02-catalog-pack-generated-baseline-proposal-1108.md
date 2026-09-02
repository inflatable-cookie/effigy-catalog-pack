# Catalog-Pack Generated Baseline Proposal 1108

Status: provider checkpoint observed; no proposal dispatched because the
published digest already matches Effigy's generated baseline
Card: `1108`
Repository: `inflatable-cookie/effigy-catalog-pack`
Branch: `worker/g08-048-generated-baseline-proposals-1108-live`

## Outcome

The pack repository now contains a separate manual proposal workflow. It takes
one lowercase OCI manifest digest, verifies the public artifact and its
digest-bound attestation, materializes an Effigy candidate, and may open a
generated-only review PR. It does not accept, merge, release, publish, move
`stable`, or activate a baseline.

## Security Boundary

The installation-token request is:

```json
{"permissions":{"contents":"write","pull_requests":"write"},"repositories":["effigy"]}
```

It is sent to
`POST /app/installations/{installation_id}/access_tokens` after an RS256 App
JWT is created with a ten-minute maximum lifetime. The response is checked for
exactly one repository whose canonical `full_name` is
`inflatable-cookie/effigy` (and whose retained owner login, when present, is
`inflatable-cookie`), plus `contents: write`, `pull_requests: write`, and no
permission outside those two plus GitHub's implicit `metadata: read`. Reports
return the canonical repository identity, never the token.

The hosted Actions job itself has `contents: read` only. It uses the exact-SHA
checkout action
`actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`. ORAS `1.3.3` is
downloaded with SHA-256
`9ce999f8d2de03fc03968b29d743077a58783e545e5eaa53917ca177352d0e59`.

The proposal token is checked out against current Effigy `main` and is used
only to push the deterministic digest-named branch and call `gh pr create`.
The workflow contains no approval, merge, release, package-write,
attestation-write, or publication command. The App registration, installation,
secret values, dispatch, and hosted run remain a separate operator checkpoint.

## Generated-Only Policy

The candidate may change exactly:

- `crates/effigy-catalog/catalog/**`;
- `crates/effigy-catalog/catalog-pack.lock.toml`; and
- one dated `docs/logs/*-catalog-pack-generated-baseline-proposal.md` file.

The artifact is pulled by digest. The raw OCI manifest bytes are hashed and
must equal the requested digest; the registry descriptor must carry that same
digest and its exact byte size. Every layer title is checked for safe sorted
inventory, and every layer size and byte digest is compared with the pulled pack
root. The lock is rendered twice from the same facts and the candidate bytes are
checked again after staging. Product code, workflows, unrelated docs,
traversal paths, hand-edited snapshot bytes, and incomplete lock/evidence
changes fail closed.

## Review Finding Map

| Review finding | Repair | Proof |
| --- | --- | --- |
| Manifest identity was not bound to the requested digest. | The workflow fetches raw manifest bytes; verification hashes those bytes against the request and binds the descriptor size before parsing or materializing. | `immutable_artifact_input_proof` changes manifest annotations while keeping request and descriptor fixed; it is rejected. `no_provider_mutation_proof` verifies artifact rejection precedes token mint, materialization, and push. |
| App response checked only the short repository name. | Verification requires canonical `full_name` `inflatable-cookie/effigy`, validates a retained canonical owner login, and reports the canonical identity. | `app_token_scope_proof` rejects a foreign-owner `foreign-owner/effigy` response and checks the canonical identity in the accepted report. |

## Independent Effigy Verification

The workflow copies a disposable integration test into the checked-out Effigy
crate, runs `cargo test --locked --test catalog_pack_proposal_baseline`, and
removes the harness in a `finally` path. The harness calls Effigy's committed
`CompiledBaselineLock::load` and `verify_snapshot` APIs against the candidate.
This reruns Effigy's offline manifest, content-identity, and deterministic OCI
digest proof independently of the pack script's artifact model.

## Network-Free Proofs

`effigy pack:proposal-check` and `effigy pack:workflow-check` pass without
provider access. Named counterexamples cover:

- `generated_only_path_allowlist_proof` — product code, workflows, unrelated
  docs, traversal, and incomplete evidence;
- `immutable_artifact_input_proof` — raw manifest hash and descriptor size,
  fixed-request manifest change, wrong descriptor, hand-edited layer bytes,
  exact inventory, and exact layer digests;
- `candidate_diff_proof` — materialization, clean status, staged-policy proof,
  hand edits, and product-code changes;
- `exact_lock_generation_proof` — byte-identical repeated lock generation and
  complete typed fields;
- `app_token_scope_proof` — exact endpoint/repository/permissions, canonical
  repository identity, foreign-owner same-name rejection, and broad response
  rejection;
- `effigy_verifier_seam_proof` — explicit offline Cargo command and Effigy API
  harness; and
- `no_provider_mutation_proof` — branch/PR-only authority and publication
  independence.

At the implementation-only phase, before the separately authorized provider
checkpoint, no GitHub App was registered or installed, no secret was written,
and no workflow was dispatched. No Effigy branch or PR was created. No
package, tag, attestation, channel, approval, merge, or release mutation
occurred in that implementation phase.

## Live Provider Checkpoint — Observed Empty Baseline Delta

Observed: `2026-09-02T17:48:03Z`
Catalog-pack head: `4dd8b8a556e6f1abe0d59c506ef16f0804e00e3f` (equal to
`origin/main`)

Provider setup was present before this continuation. Read-only verification
returned:

- GitHub App: `effigy-catalog-pack-proposer`, owner `inflatable-cookie`, App ID
  `4808098`, permissions exactly `contents: write`, `pull_requests: write`,
  `metadata: read`, and no webhook events;
- organization installation: ID `158560132`, account
  `inflatable-cookie` (organization ID `264157789`),
  `repository_selection: selected`, exact permissions as above, and
  `suspended_at: null`;
- repository Actions secret names exactly:
  `CATALOG_PACK_EFFIGY_APP_ID`, `CATALOG_PACK_EFFIGY_INSTALLATION_ID`, and
  `CATALOG_PACK_EFFIGY_APP_PRIVATE_KEY`; secret values were never read;
- the uploaded PEM was reported disposed to Trash after secret upload; it was
  not read during this continuation;
- live catalog-pack controls: verified, read-only, `write_methods_used: []`,
  default workflow permissions `read`, approval permission `false`, and only
  the pinned checkout and attest actions allowed;
- public `stable` read: `sha256:91de584e77487765c24f53abb63413783a99c0a7926c25aee1289a3cf370d9f3`;
  the digest-bound SLSA provenance attestation verified successfully.

The current Effigy main is `20d9040c1ffedce83e6594e729c9d494dedfbc5d`, a
descendant of the handoff authority commit. Its typed lock records the same
published digest and content identity `sha256:9498d33f1eccbb91e971b55f5169830baca26326a8f802408a0432e733254974`,
and `diff -r pack ../effigy/crates/effigy-catalog/catalog` is byte-identical.
The current proposal oracle requires the generated snapshot and typed lock to
appear in the changed-path set. Because both are already exact, dispatching
`proposal.yml` would be a no-op proposal rejected by the oracle. Therefore:

- proposal dispatch: **not performed**;
- hosted run: none;
- Effigy branch/PR/head: none;
- no new pack release, tag, package, attestation, channel movement, approval,
  merge, or release mutation was attempted.

The API's selected-installation record was independently read back. The
repository-list endpoint requires the current operator token's `read:user`
scope; that scope was not added, so no credential widening was performed.
The supplied exact selection (`inflatable-cookie/effigy` only) was not
replaced by an unverified broader assumption.

Resume validation passed with current Effigy main: `effigy doctor --json`
(zero errors; three known warning-level god-file findings), `effigy validate`,
`effigy pack:proposal-check`, `effigy pack:workflow-check`, and `effigy qa`.

## Next Task

Review this evidence-only PR. The digest remains the accepted baseline, so no
generated Effigy proposal is pending. Preserve Effigy orchestrator exact-head
review and merge authority; do not invent a new pack release to create a
non-empty proposal.
