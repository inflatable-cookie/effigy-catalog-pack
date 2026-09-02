# Catalog-Pack Generated Baseline Proposal 1108

Status: implementation-only; no provider mutation performed
Card: `1108`
Repository: `inflatable-cookie/effigy-catalog-pack`
Branch: `worker/g08-048-generated-baseline-proposals-1108`

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

No GitHub App was registered or installed. No secret was written. No workflow
was dispatched. No Effigy branch or PR was created. No package, tag,
attestation, channel, approval, merge, or release mutation occurred.

## Next Task

Review this exact worker head and merge the implementation PR if accepted.
Only a separately named operator gate may proceed to App/provider setup and a
live proposal run.
