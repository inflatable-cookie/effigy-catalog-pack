# Plan

Updated: 2026-09-26

## Now

1. **Proposal evidence goes in the PR body, not Effigy's logs** — the
   generated-baseline proposal (`proposal.yml`, `scripts/catalog_pack_proposal.py`)
   writes a dated evidence file into Effigy's `docs/logs/`, which lean Effigy no
   longer has. Put that evidence in the proposal PR body instead, and drop the
   evidence file from the generated-only allowlist, the diff checks and the
   `git add` step. Effigy's baseline verifier doesn't read the file. Tom
   approved the workflow edit on 2026-09-26. Dispatch it as a Queue brief once
   Queue's no-manifest closeout (`g01.053`) is live.

## Next

- **Rename the publication environment** — `catalog-pack-publication-rehearsal`
  is the live publication gate but still carries a rehearsal name. Needs an
  explicit operator go-ahead for the GitHub settings change (see
  `PAPERCUTS.md`).
