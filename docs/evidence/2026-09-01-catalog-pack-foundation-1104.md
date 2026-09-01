# Catalog-pack foundation evidence — 2026-09-01

Card: `1104-build-catalog-pack-repository-foundation`

## Canonical ownership and one-time import

`pack/` is the only editable catalog asset root in
`inflatable-cookie/effigy-catalog-pack`. The pack has 42 regular files: the 41
catalog files below plus `pack.toml`. Total pack bytes are 88,600; the source
catalog is 88,436 bytes.

The explicit one-time import proof compares every byte with the pinned Effigy
authority. It records:

- Effigy commit: `055595340c2219d3d47296072f5818c524c341f0`
- catalog tree object: `539471162c4976551ac720fdcffe6a1de33cef0f`
- support file: `support/catalog-pack-update.toml`
- support Git blob OID: `20d0194d52c0bbf46677f8d77ca96fb4505df50e`
- support floor: `as_of_release = "0.12.1"`, `required_versions = ["0.12.1"]`
- `oldest_update_capable_release`: absent

Imported files:

```text
README.md
compose.override.example.yml
dbgate/compose.fragment.yml
dbgate/service.toml
elasticsearch/compose.fragment.yml
elasticsearch/service.toml
mailpit/compose.fragment.yml
mailpit/service.toml
mariadb/compose.fragment.yml
mariadb/configs/default.conf
mariadb/configs/my.cnf
mariadb/service.toml
memcached/compose.fragment.yml
memcached/service.toml
minio/compose.fragment.yml
minio/service.toml
nginx/compose.fragment.yml
nginx/configs/default.conf
nginx/configs/laravel.conf
nginx/configs/php-app.conf
nginx/configs/spa.conf
nginx/configs/wordpress.conf
nginx/service.toml
node/Dockerfile
node/compose.fragment.yml
node/service.toml
pgweb/compose.fragment.yml
pgweb/service.toml
php-fpm/Dockerfile
php-fpm/compose.fragment.yml
php-fpm/service.toml
phpmyadmin/compose.fragment.yml
phpmyadmin/service.toml
postgres/compose.fragment.yml
postgres/configs/default.conf
postgres/service.toml
redis/compose.fragment.yml
redis/service.toml
workspace-rust-bun/Dockerfile
workspace-rust-bun/compose.fragment.yml
workspace-rust-bun/service.toml
```

The Effigy-compatible pack content ID is:

```text
sha256:511d120f181505f8ecced7687b564c4663663eca8f6f68b2b562c9b676feb29e
```

Routine `validate`, `effigy test`, and `effigy qa` recompute pack facts and
consume only the pinned support policy. They do not require the pack to remain
byte-identical to the one-time import. `import-proof` is the explicit command
for that historical equality claim.

## Deterministic source and OCI identity

The source-only OCI candidate was built from pack repository commit
`a891b90883e644e21ebd54847be64abf15edc37c` at
`2026-09-01T22:18:18Z`:

- reference: `ghcr.io/inflatable-cookie/effigy-catalog-pack:v1.0.0`
- manifest digest: `sha256:f75bb1a92d6af9e08af1ca0dd33a1eb132c93a988909cc0f0c6ec683e751958b`
- 42 sorted raw-file layers
- ORAS local pull round-trip: passed with ORAS `1.3.3+Homebrew`

Two fresh local builds produced the same manifest digest and identical layout
bytes. The Effigy import commit is not used as the OCI revision or timestamp.

The no-push publication candidate adds the planned source identity:

- source tag: `v1.0.0`
- peeled/source commit: `a891b90883e644e21ebd54847be64abf15edc37c`
- planned tag object hash: `a002cad044c9cb8def2a0bd11a9390830ccf5acc`
- candidate digest: `sha256:86a8265818bb44cae44983072fb14dd9dbe4825aba16d0fbf8961303775d3df5`

That tag object was hashed in memory only. No `v1.0.0` tag exists in the source
repository. The protected manual workflow accepts an existing annotated tag
and full peeled commit, then verifies the real tag object, peeled commit, and
manifest version before rehearsal.

## Consumer smoke

Current Effigy binary: `v0.12.1+local.0555953` from the pinned authority
checkout. With a temporary `HOME` and temporary repository it:

- installed and activated the local pack;
- reported the expected pack ID, version, and content ID;
- listed all 14 installed fragments;
- extracted `workspace-rust-bun` with its `Dockerfile`; and
- ejected a representative `workspace-rust-bun` plus `postgres` compose
  assembly without starting a container.

## Publication rehearsal and hosted controls

The no-push rehearsal performed all four in-memory cases:

- absent: candidate would create the ref;
- same digest: candidate would reuse the ref without a write;
- changed source identity/content: rejected without changing state; and
- changed annotated-tag identity: rejected without changing state.

The live repository controls were read back from the GitHub API at
`2026-09-01T22:14:13Z` and are normalized in
[`hosted-controls.json`](hosted-controls.json):

- Actions are enabled, use the selected-actions policy, require full-SHA
  pinning, and allow only `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`.
- `catalog-pack-publication-rehearsal` has one required reviewer, zero wait
  minutes, self-review disabled, administrator bypass disabled, and no
  deployment branch restriction.
- Ruleset `22050144` is active for exactly `refs/tags/v*`, rejects `update` and
  `deletion`, and has no bypass actors.
- The repository workflow default remains read-only and cannot approve pull
  request reviews.

`workflow-check` fails closed if this evidence is absent or any of those live
control facts are weakened. The validation workflow has no package, attestation,
tag, registry-push, stable-channel, or merge mutation.

## Validation

- `python3 scripts/catalog_pack.py inventory` — pass
- `python3 scripts/catalog_pack.py validate` — pass without source-byte proof
- `python3 scripts/catalog_pack.py import-proof --effigy-root ../effigy` — pass
- `python3 scripts/catalog_pack.py oci-layout` — pass
- `python3 scripts/catalog_pack.py rehearse --effigy-root ../effigy --require-authority` — pass
- `python3 scripts/catalog_pack.py portable-check` — isolated authority lookup fails closed
- `effigy test --plan` — pass
- `effigy validate` — pass
- `effigy qa` — pass
- `effigy doctor --json` — expected healthy repository
- `git diff --check` — pass

No source tag, package, registry object, attestation, stable-channel movement,
or Effigy sibling checkout change was made by this card.
