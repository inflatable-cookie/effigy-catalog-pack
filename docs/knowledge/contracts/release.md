# Release

A pack release is an OCI package at `ghcr.io/inflatable-cookie/effigy-catalog-pack`,
published from an annotated source tag `v<pack-version>`, attested, and then
promoted to `stable`. Publishing is always an operator action.

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
