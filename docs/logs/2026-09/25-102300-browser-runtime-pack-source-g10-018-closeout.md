# g10.018 Browser Runtime Catalog-Pack Source — Closeout

Status: closed after accepted exact-head review, passing hosted validation, and merge.

Canonical task card: Effigy sibling `docs/roadmaps/g10/018-browser-runtime-catalog-pack-source.md`.

## Outcome

PR [#7](https://github.com/inflatable-cookie/effigy-catalog-pack/pull/7) merged to `main` at `76d594d8e72731547c0c2918746d5c98291d77b4` on 2026-09-25 10:18:49 UTC. The PR head reviewed was `f009a8c6718cbcf0c602dadea5938158cfeabeca`.

The merged canonical source publishes the opt-in `browser_runtime` parameter in source form: `none` stays the default, while `chromium` adds Debian runtime libraries and fonts. The image does not include a browser binary, Playwright, Node, or `npx`.

- Pack: `effigy-default-catalog` `1.1.0`
- Effigy compatibility: `>=0.13, <0.14`
- Pack content ID: `sha256:e92cc2f217fa2ba4de302b8376ec558afb042acd3a83e4d33ecfb03dc40606a3`
- Inventory: 42 files, 90,852 bytes
- Effective Dockerfile SHA-256: `1e62ce03da4ae0e4abcc85e0019376cadd5d0cc6efe30247b81560c7ac39a6f6`

The merged Dockerfile, service manifest, and Compose fragment are byte-identical to the retained `g10.017` implementation. Its linux-arm64 non-root Playwright 1.55.1 launch evidence therefore remains applicable: Chromium 140.0.7339.186 passed `ldd`, and headless launch as `dev` printed `SMOKE_OK`. No container rebuild or repeated smoke was needed.

## Review and validation

- Independent exact-head review by `betterthanclay` posted a `ready_to_merge` verdict for `f009a8c6718cbcf0c602dadea5938158cfeabeca` at [the review comment](https://github.com/inflatable-cookie/effigy-catalog-pack/pull/7#issuecomment-5830770867).
- Hosted `Validate catalog pack` check passed for the PR: [Actions run](https://github.com/inflatable-cookie/effigy-catalog-pack/actions/runs/36122702185/job/108031683353).
- The reviewer reports network-free pack validation, source tests, `effigy qa` with Effigy 0.13.0, consumer assembly proof, and `git diff --check` all passed at the reviewed head.
- `effigy pack:validate` passed on the merged source during closeout. It verified pack version `1.1.0`, compatibility `>=0.13, <0.14`, content ID above, and current Effigy 0.13.0 support authority at commit `8c7f0cc6068ab3ac651922913db8c51f97d980ab` / blob `38c88a550616f2ed9ed688306c8c841674bd2eb8`.

## Vision Target Delta

- Primary tags: `ROUTE`, `CONTRACT`.
- Movement: published baseline `1.0.1` without this option -> reviewed canonical source `1.1.0` with `browser_runtime = "none"` by default and `chromium` opt-in.
- Remaining gap: the artifact is not published and the generated Effigy baseline is not imported; the approved next task is `g10.019`.

## Deferred proof and review note

The one-time `pack:import-proof` is expected to fail while the canonical pack has evolved beyond Effigy's historical import snapshot; the reviewer observed the mismatch at `workspace-rust-bun/Dockerfile`. This does not invalidate routine publication checks, which preserve and verify the historical import commit/tree/blob identity separately. `g10.019` must publish the new artifact before `g10.017` imports its exact bytes and provenance.

The accepted review also recorded one non-blocking follow-up note: `catalog_pack_transaction_tests.py` still passes a hard-coded `v1.0.1` to `FakeRegistry.inspect_version`, although that fake ignores the tag argument and the digest assertion remains bound. It was not changed in this closeout.

The pre-merge evidence file `docs/evidence/2026-09-25-browser-runtime-pack-source-g10-018.md` records implementation-time status. This log records the later review and merge outcome.

## Next pointer

Preserve the approved sequence: `g10.019` owns separately gated publication of `1.1.0`; after publication, `g10.017` imports the exact artifact bytes and provenance. This closeout grants no publication authority.
