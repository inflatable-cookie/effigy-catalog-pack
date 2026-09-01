# effigy-catalog-pack

Canonical catalog pack for Effigy service and workspace assets.

The release root is [pack/](pack/). It contains the exact catalog tree copied
from Effigy plus the pack manifest. The Effigy support policy is not copied
into this repository; it remains owned by the pinned Effigy authority.

## Foundation facts

- pack: `effigy-default-catalog` `1.0.0`
- compatibility: `>=0.12, <0.13`
- pack source repository: `inflatable-cookie/effigy-catalog-pack`
- one-time Effigy import commit: `055595340c2219d3d47296072f5818c524c341f0`
- one-time Effigy catalog tree: `539471162c4976551ac720fdcffe6a1de33cef0f`
- Effigy support file Git blob OID: `20d0194d52c0bbf46677f8d77ca96fb4505df50e`
- pack content ID: `sha256:511d120f181505f8ecced7687b564c4663663eca8f6f68b2b562c9b676feb29e`

The source repository commit, commit timestamp, annotated `v1.0.0` tag object,
and peeled commit are the OCI provenance inputs. The no-push rehearsal models
that identity without creating the tag or contacting a registry.

## Validation

Routine pack validation is independent of Effigy source bytes. It computes the
manifest, inventory, compatibility range, and content ID from `pack/`. The
support policy is consumed separately from an explicitly pinned, read-only
Effigy checkout. The one-time import proof is opt-in and checks exact Effigy
catalog bytes; it is not part of routine `validate`, `test`, or `qa` runs.

Checks are network-free. The worker checkout's launcher-provided `../effigy`
symlink supplies the support/import authority when requested. Other checkouts
can set `EFFIGY_ROOT` or pass `--effigy-root`.

```sh
effigy tasks
effigy test --plan
effigy validate
effigy qa
```

For the card's one-time import proof, run:

```sh
python3 scripts/catalog_pack.py import-proof --effigy-root ../effigy
```

`pack:oci` derives OCI revision and creation time from the pack repository's
current commit. `pack:rehearse` proves absent, same-digest, changed-source,
and changed-annotated-tag collision handling without a push. The protected
manual workflow requires an already-existing annotated source tag and its full
peeled commit.

Hosted Actions, environment, and tag-rule evidence is normalized in
[hosted-controls.json](docs/evidence/hosted-controls.json).

`hosted-controls.json` is a checked-in static provider snapshot used by the
network-free `workflow-check`; it is not a live guarantee and does not contain
current-head Actions-run evidence. An authenticated operator can verify the
current controls independently with:

```sh
python3 scripts/catalog_pack.py provider-controls
# or: effigy pack:provider-controls
```

That command performs only explicit GitHub `GET` requests and compares the
live Actions policy, workflow permissions, protected environment, and `v*`
ruleset. Its output is marked `live-provider-observation` and does not read the
static snapshot. The recorded observation is
[live-provider-controls.json](docs/evidence/live-provider-controls.json).

The protected environment retains exactly one required reviewer,
`betterthanclay`; self-review is permitted so that this single operator can
approve its own manual rehearsal, while administrator bypass remains disabled.
No collaborator access is added. The manual workflow passes dispatch inputs
through step environment variables and quoted shell variables, and
`workflow-check` includes a raw-input injection counterexample as a recurrence
guard.

The `pack:effigy` task installs `pack/` into a temporary Effigy home and
exercises service listing, fragment extraction, and a workspace-plus-Postgres
compose assembly. It never starts a container. The deterministic OCI task
writes only to `.effigy/`, which is ignored.

See [the dated foundation evidence](docs/evidence/2026-09-01-catalog-pack-foundation-1104.md)
for the imported inventory, digest, source identity, support resolution,
hosted controls, and no-push rehearsal results.
