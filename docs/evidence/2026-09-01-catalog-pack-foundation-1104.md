# Catalog-pack foundation evidence — 2026-09-01

Card: `1104-build-catalog-pack-repository-foundation`

## Imported source

The canonical release root is `pack/`. It contains 42 regular files: the 41
catalog files below plus `pack.toml`. Total pack bytes are 88,600; the source
catalog is 88,436 bytes.

Source authority:

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

## Deterministic candidate

The local OCI candidate has 42 sorted raw-file layers and fixed source-derived
metadata:

- reference: `ghcr.io/inflatable-cookie/effigy-catalog-pack:v1.0.0`
- manifest digest: `sha256:8969288f4251c69ca4054dc53362a4d167e0bd38739e8478eaf9970c3a882495`
- created: `2026-09-01T20:53:27Z`
- revision: `055595340c2219d3d47296072f5818c524c341f0`
- ORAS local pull round-trip: passed with ORAS `1.3.3+Homebrew`

Two fresh local builds produced the same manifest digest and identical layout
bytes.

## Consumer smoke

Current Effigy binary: `v0.12.1+local.0555953` from the pinned authority
checkout. With a temporary `HOME` and temporary repository it:

- installed and activated the local pack;
- reported the expected pack ID, version, and content ID;
- listed all 14 installed fragments;
- extracted `workspace-rust-bun` with its `Dockerfile`; and
- ejected a representative `workspace-rust-bun` plus `postgres` compose
  assembly without starting a container.

## Publication rehearsal and workflow scope

The no-push rehearsal passed all three immutable-ref cases:

- absent: candidate would create the ref;
- same digest: candidate would reuse the ref without a write; and
- collision: different digest rejected without changing state.

The workflow check passed for `validate.yml` and
`publication-rehearsal.yml`: checkout actions are pinned by full SHA, both
workflows use `contents: read`, and no package, attestation, tag, stable-channel,
registry-push, or merge mutation is present.

No source tag, package, registry object, attestation, stable-channel movement,
or Effigy sibling checkout change was made by this card.

## Validation commands

- `effigy test` — pass
- `effigy qa` — pass
- `effigy doctor --json` — `ok: true`, 20 checks passed, no findings
- `git diff --check` — pass
