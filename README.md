# effigy-catalog-pack

Canonical catalog pack for Effigy service and workspace assets.

The release root is [pack/](pack/). It contains the exact catalog tree copied
from Effigy plus the pack manifest. The Effigy support policy is not copied
into this repository; ongoing publication support is consumed from Effigy's
current default-branch commit and blob.

## Foundation facts

- pack: `effigy-default-catalog` `1.0.1`
- compatibility: `>=0.12, <0.13`
- pack source repository: `inflatable-cookie/effigy-catalog-pack`
- one-time Effigy import commit: `055595340c2219d3d47296072f5818c524c341f0`
- one-time Effigy catalog tree: `539471162c4976551ac720fdcffe6a1de33cef0f`
- import-era support Git blob OID: `20d0194d52c0bbf46677f8d77ca96fb4505df50e`
- pack content ID: `sha256:9498d33f1eccbb91e971b55f5169830baca26326a8f802408a0432e733254974`

The source repository commit, commit timestamp, annotated `v1.0.1` tag object,
and peeled commit are the OCI provenance inputs. Ordinary QA models that
identity without creating the tag or contacting a registry.

## Validation

Routine pack validation is independent of Effigy source bytes. It computes the
manifest, inventory, compatibility range, and content ID from `pack/`. The
support policy is consumed from Effigy's current default-branch commit. The
one-time import proof is opt-in and checks exact import-commit catalog bytes; it
is not part of routine `validate`, `test`, or `qa` runs.

Checks are network-free except the explicit GET-only `support-releases` and
`provider-controls` commands. The worker checkout's launcher-provided
`../effigy` symlink supplies the support/import authority when requested. Other
checkouts can set `EFFIGY_ROOT` or pass `--effigy-root`.

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
and changed-annotated-tag collision handling without a push.
`pack:publication-check` proves the ordered publication transaction, including
fail-closed collision, stale support, unattested/private subjects, the live
mutate gate, injected command-runner inspect/org-route/refetch proofs, and safe
absent-`stable` behavior, without contacting a registry.

The protected manual `publication.yml` workflow requires the canonical
annotated source tag `v<pack-version>` (not `refs/tags/v…`) and its full peeled
commit. It serializes a version-publish job and a finalize job. The operator
makes the linked organization package public through GitHub package settings
between those jobs. Finalize uses pinned `actions/attest` and is the only path
that may set `CATALOG_PACK_PUBLICATION_MUTATE=1` and pass `--mutate`. Ordinary
QA never imports the live registry adapter. This PR does not change
selected-actions provider policy.

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
approve the manual publication job, while administrator bypass remains disabled.
No collaborator access is added. The manual workflow passes dispatch inputs
through step environment variables and quoted shell variables, and
`workflow-check` includes a raw-input injection counterexample as a recurrence
guard.

The `pack:effigy` task installs `pack/` into a temporary Effigy home and
exercises service listing, fragment extraction, and a workspace-plus-Postgres
compose assembly. It never starts a container. The deterministic OCI task
writes only to `.effigy/`, which is ignored.

See [the dated foundation evidence](docs/evidence/2026-09-01-catalog-pack-foundation-1104.md)
and [the implementation-boundary evidence](docs/evidence/2026-09-02-catalog-pack-publication-implementation-1105.md).
