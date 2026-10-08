# Release

A pack release is an OCI package at `ghcr.io/inflatable-cookie/effigy-catalog-pack`,
published from an annotated source tag `v<pack-version>`, attested, and then
promoted to `stable`. Publishing is always an operator action.

## Non-root entrypoint repair authority

Tom requested on 2026-10-02: "Can we unblock 068?" Under his standing
bounded-work authority, this permits the canonical non-root entrypoint fix
and review in this repository, plus preparation of the exact release proposal.
The generated Effigy recovery snapshot must continue to come from an accepted
published artifact; hand-editing its bytes or provenance is not a repair path.
Preserve command argv and exit behavior, root-mode bridge socket protections,
and honest diagnostics when optional forwarding or trust setup is unavailable.

This request does not authorize publication, tag creation, workflow dispatch,
package visibility changes, movement of `stable`, secret changes, or live image
deployment. Those actions need the operator's explicit instruction against the
reviewed release proposal. A later Effigy import must use the actual published
identity and pass non-root behavior checks without skipping the defect.

## Steps

1. Change `pack/` and the pack manifest version. Run `effigy qa`, which covers
   the ordered publication transaction offline (`pack:publication-check`) and
   the workflow guard (`pack:workflow-check`). Merge the PR.
2. The operator creates the annotated tag `v<pack-version>` on the reviewed
   merge commit.
3. The operator dispatches the protected manual `publication.yml` workflow with
   the tag name (not `refs/tags/…`) and its full peeled commit. Its environment
   needs the single required reviewer's approval.
4. The version-publish job pushes the version. The operator then makes the
   linked organization package public in GitHub package settings; there is no
   REST PATCH for this.
5. The finalize job (the only path allowed to set
   `CATALOG_PACK_PUBLICATION_MUTATE=1` and pass `--mutate`) verifies the public
   package, attests it with pinned `actions/attest`, checks an anonymous pull,
   and moves `stable`.

The current finalizer also exercises live rollback when a different previous
`stable` exists: it retags candidate, previous, then candidate again. The
v1.1.2 receipt reports this sequence with `rollback_exercised: true`.
Its final readback is the candidate, but the workflow's "move stable once"
label does not describe these intermediate writes. Keep rollback modeling
distinct from claims of a single live promotion; a correction needs reviewed
implementation before a later publication.

## Verify

- The finalize job reads back the package, attestation and `stable` digest.
- `effigy pack:support-releases` confirms that Effigy releases cover the pack's
  compatibility range.
- Optionally, `effigy pack:provider-controls` compares the live GitHub controls
  with the recorded snapshot.

## Roll back

Published versions are immutable. Fix forward with a new pack version, and
move `stable` only through the finalize job.

## Never

- Reuse or move a published tag. `v1.0.0` is permanent incident evidence (see
  `AGENTS.md`).
- Publish from an unreviewed head or outside the protected workflow.

## Approved v1.1.1 publication

Tom answered the exact reviewed publication proposal on 2026-10-02:
"Approve. You have blanket approval" (Queue decision
36a3caf2-c19d-4d59-9a51-e1ab92f03179 v2). This authorizes the annotated
v1.1.1 source tag at c7ec113e0271157e867a6c27025268b34b7435f7 and the
existing protected publication workflow, including its required human
environment gates and public-package/finalize checkpoints. Full Queue pack
QA 33b07484-52b7-4364-9db7-c1fca5d018a5 passed at that exact source.

Expected pack content identity is
sha256:c0f01547849f61e7f9465e6bc7fa483378c0748e75e7fe3fe0534ea0de797bc9.
This ruling is not a published receipt or OCI digest. Verify the actual
version, attestation, anonymous pull and stable readback before resuming
Effigy068's retained artifact import. Preserve immutable versions, failed
v1.0.0 evidence, existing secrets and live images. No workflow edits or
Effigy binary release are included.

## Approved v1.1.2 publication

Tom answered "Authorize exact proposal" through the operator board on
2026-10-08 (Queue decision 5c9088de-838e-4d87-90f1-6968928b318d v2).
The approved source is bffcd0d8446286c49609c5b4659fe1d6f5d69c0f,
with content identity
sha256:f65724ad5eef245fe4f2e6c3e831f1761b415daba8d8a5d4744d30341a6af022
and compatibility >=0.13, <0.15. This permits the new annotated v1.1.2
tag and existing protected publication workflow, including verified stable
promotion. Its required human environment approvals remain in force.

The real annotated tag determines the final OCI provenance identity;
rehearsal digests are not published receipts. Verify the actual version,
digest-bound attestation, anonymous bytes, canonical public package linkage
and stable readback. Preserve v1.1.1 and failed v1.0.0 identities. Workflow
edits, secrets, App controls, live image deployment and a generated Effigy
import remain outside this publication approval.
