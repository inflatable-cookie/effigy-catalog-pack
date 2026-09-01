# effigy-catalog-pack

Canonical catalog pack for Effigy service and workspace assets.

The release root is [pack/](pack/). It contains the exact catalog tree copied
from Effigy plus the pack manifest. The Effigy support policy is not copied
into this repository; it remains owned by the pinned Effigy authority.

## Foundation facts

- pack: `effigy-default-catalog` `1.0.0`
- compatibility: `>=0.12, <0.13`
- source commit: `055595340c2219d3d47296072f5818c524c341f0`
- source catalog tree: `539471162c4976551ac720fdcffe6a1de33cef0f`
- support file Git blob OID: `20d0194d52c0bbf46677f8d77ca96fb4505df50e`
- pack content ID: `sha256:511d120f181505f8ecced7687b564c4663663eca8f6f68b2b562c9b676feb29e`

The first official tag and registry publication are deliberately not created
by this foundation change.

## Validation

The checks are network-free except for an explicitly pinned, read-only Effigy
checkout when the authority proof is requested. In the worker checkout, the
launcher-provided `../effigy` symlink supplies that authority. Other checkouts
can set `EFFIGY_ROOT` or pass `--effigy-root`.

```sh
effigy tasks
effigy test --plan
effigy validate
effigy qa
```

The `pack:effigy` task installs `pack/` into a temporary Effigy home and
exercises service listing, fragment extraction, and a workspace-plus-Postgres
compose assembly. It never starts a container. The deterministic OCI task
writes only to `.effigy/`, which is ignored.

See [the dated foundation evidence](docs/evidence/2026-09-01-catalog-pack-foundation-1104.md)
for the imported inventory, digest, support resolution, and no-push rehearsal
results.
