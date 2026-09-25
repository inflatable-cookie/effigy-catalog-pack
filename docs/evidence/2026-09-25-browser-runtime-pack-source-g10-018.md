# Browser Runtime Catalog-Pack Source g10.018

Status: implementation and local proof complete; awaiting independent exact-head
review and current-base CI. No tag, registry, attestation, or `stable` mutation.
Card: `g10.018`
Repository: `inflatable-cookie/effigy-catalog-pack`
Feature commit: `d009483db17a803935440bf71d9fb4bbb11ce2d8`

## Outcome

The canonical pack source now carries the default-off `browser_runtime`
parameter already proven by the retained `g10.017` worker:

- `pack/workspace-rust-bun/service.toml` declares `browser_runtime` with
  default `"none"` and documents the `chromium` opt-in;
- `pack/workspace-rust-bun/compose.fragment.yml` passes `BROWSER_RUNTIME` into
  the image build;
- `pack/workspace-rust-bun/Dockerfile` installs Debian Bookworm Chromium
  shared libraries and a basic font set only in the `chromium` branch and
  fails unknown values with
  `unsupported BROWSER_RUNTIME='…'; expected none or chromium`.

`browser_runtime = "none"` remains the default, so ordinary workspaces stay
toolchain-only. The image still contains no browser binary, Playwright, Node,
or `npx`; the consumer downloads its matching browser into the `dev` user
cache.

## Version and compatibility

- pack: `effigy-default-catalog` `1.1.0` (additive minor over the published
  `1.0.1`)
- compatibility: `>=0.13, <0.14`
- support authority at proof time: Effigy default-branch commit
  `8c7f0cc6068ab3ac651922913db8c51f97d980ab`, support blob
  `38c88a550616f2ed9ed688306c8c841674bd2eb8`, `as_of_release = "0.13.0"`,
  `required_versions = ["0.13.0"]`

The range admits released Effigy 0.13.0 and deliberately does not claim the
untested older 0.12 release.

## Source content identity

- pack content ID:
  `sha256:e92cc2f217fa2ba4de302b8376ec558afb042acd3a83e4d33ecfb03dc40606a3`
- pack inventory: 42 files, 90,852 bytes
- effective `pack/workspace-rust-bun/Dockerfile` SHA-256:
  `1e62ce03da4ae0e4abcc85e0019376cadd5d0cc6efe30247b81560c7ac39a6f6`
- OCI candidate reference: `ghcr.io/inflatable-cookie/effigy-catalog-pack:v1.1.0`
  with 42 sorted raw-file layers and anchor content ID equal to the source
  content ID above.

The OCI manifest digest is derived from the pack repository commit and timestamp
at proof time. `g10.019` must recompute the candidate from the merged `main`
commit; this evidence intentionally does not freeze a pre-merge digest.

## Relation to the linux-arm64 smoke

The three effective source files (Dockerfile, `service.toml`,
`compose.fragment.yml`) are byte-identical to the retained `g10.017`
implementation under
`/Users/tom/.paseo/worktrees/310mya31/ns-3ed8c61d-444d-47da-8630-60d510ae3d2f`.
The package list, Dockerfile layer position, and `none`/`chromium` branches are
unchanged, so the retained linux-arm64 non-root Playwright 1.55.1 launch
evidence applies without repeating the container build:

- `bun add @playwright/test@1.55.1`; Chromium `140.0.7339.186` (build v1193);
- `ldd` clean on
  `/home/dev/.cache/ms-playwright/chromium-1193/chrome-linux/chrome`;
- headless launch as `dev` printed `SMOKE_OK`.

That evidence remains under the retained worker worktree's
`docs/logs/2026-09/25-101900-g10-017-chromium-workspace-runtime.md`.

## Consumer assembly proof

`effigy qa` installs `pack/` into a temporary Effigy home using the current
0.13.0 binary and ejects a representative `workspace-rust-bun` plus `postgres`
assembly. The extended `pack:effigy` proof now asserts:

- the default assembly emits `BROWSER_RUNTIME: none` and the ejected Dockerfile
  defaults `ARG BROWSER_RUNTIME=none` with the bounded `case` branch;
- an explicit `browser_runtime = "chromium"` reaches the consumer build arg as
  `BROWSER_RUNTIME: chromium`.

No container is started.

## Validation-harness repair

Changing a catalog file exposes a latent contradiction: the routine
`publication-check` split proof called the full one-time import byte-equality
proof, which cannot hold once the editable pack evolves, while the repository
docs promise that routine runs are independent of the import snapshot.

The proof is split so that routine runs verify only Effigy's immutable import
commit/tree/blob identity plus the distinct current support commit
(`import_proof: identity-checked`). The explicit `import-proof` command keeps
the exact current-pack-equals-import equality claim and is expected to fail
after a legitimate catalog change.

The generated-baseline proposal counterexample now derives its manifest-change
tag from the current pack version instead of a hardcoded `v1.0.1`, so it keeps
exercising a real same-size manifest mutation after the version bump.

## Validation

- `python3 scripts/catalog_pack.py validate --effigy-root ../effigy --require-authority` — pass
- `python3 scripts/catalog_pack.py test --effigy-root ../effigy` — pass
- `effigy qa` — pass
- `git diff --check` — pass

No Effigy, Underlay bundle, Acowtancy, publication-workflow, tag, OCI package,
attestation, visibility, or `stable` change was made. The one-time import
commit/tree/blob and its constants are preserved unchanged.

## Next Task

Independent exact-head review and current-base CI, then Queue merge. After
merge, `g10.019` performs the separately approved protected publication of
`1.1.0` and `g10.017` imports the exact published bytes and provenance.
