# StringSence FYP2 Readiness — Current Baseline

> Historical Gate 0 snapshot. The post-remediation decision and current
> verification evidence are recorded in
> [04-remediation-results-and-readiness.md](04-remediation-results-and-readiness.md).

## Purpose and gate

This document freezes the repository and local runtime facts that the FYP2
readiness review will use. It is a Phase 0 inventory, not an architecture
finding, test result, or approval to change behaviour.

- Snapshot time: `2026-07-23T01:09:20+08:00`
- Workspace: `/Volumes/TLW/Utar/FYP/UI/StringSence`
- Review gate: stop at Gate 0 after this baseline is reported
- Approved next activity after Gate 0: discuss architecture deepening candidates
- Not approved yet: architecture edits, defect fixes, FYP2 feature work, schema
  changes, dependency upgrades, staging, commits, or destructive cleanup

## Repository state

| Fact | Current evidence |
| --- | --- |
| Branch | `main` |
| HEAD | `71e4402e1cc7d2350412e05facf8c10e6344539d` |
| Upstream | `origin/main` |
| Ahead / behind | `0 / 0` |
| Tracked files | `494` |
| Modified / deleted / untracked | `0 / 0 / 0` |
| Staged files | `0` |

The authoritative current worktree is clean. During the earlier read-only
snapshot at `2026-07-23T00:43:40+08:00`, the workspace was still at
`a9a5812` with the canonical NLP reconciliation present as local changes.
Three commits appeared outside this review before the authoritative snapshot:

1. `1bd28d0 chore: make latest NLP workbench canonical`
2. `cbe260f chore: regenerate graphify code graph`
3. `71e4402 chore: sync graphify manifest`

No review action created, staged, committed, reset, restored, or pushed those
changes. All later phases must use `71e4402` or explicitly capture a newer
baseline if HEAD changes again.

## Protected inputs and data state

`ml/nlp-workbench-latest/` is the current canonical NLP workspace.

- Git tracks `17` files in this directory; legacy `ml/nlp-workbench/` has no
  tracked files at the current HEAD.
- The directory occupies approximately `177 MiB` locally.
- `data/archive_latest.zip` is tracked, is `5,183,835` bytes, and was not opened,
  listed internally, extracted, or processed during Phase 0.
- Extracted raw inputs, ABSA CSV files, notebooks, and the two approved matrix
  outputs are present and tracked.
- Raw data remains read-only for this review. Notebook or pipeline runs may not
  overwrite source or approved outputs; any new output must be versioned.
- `backend/.env` exists and is ignored. Its contents were not read or reported.
- AppleDouble sidecars are ignored and were not cleaned.

The historical description of this canonical workspace as wholly untracked is
no longer current. The new Git history is authoritative; the protection rules
remain in force.

## Toolchain snapshot

| Area | Project requirement | Observed locally | Phase 0 interpretation |
| --- | --- | --- | --- |
| Mobile Node | `20.19.0` / Node `20.x` | active shell `v25.9.0` | mismatch recorded; no validation run |
| npm | project lockfile present | `11.12.1` | inventory only |
| TypeScript | package `~5.9.2` | local CLI `5.9.3` | inventory only |
| Expo | package `~54.0.33` | local CLI `54.0.23` | inventory only |
| Backend Python | `>=3.12` | `.venv` Python `3.13.12` | compatible version; no tests run |
| Shell Python | not the backend runtime | `3.14.2` | do not substitute for `.venv` silently |
| uv | repository uses `uv.lock` | `0.10.0` | inventory only |
| Ruff | backend validation tool | `0.15.8` | installed, not run |
| Mypy | backend validation tool | `1.19.1` | installed, not run |
| Pytest | backend validation tool | `9.0.2` | installed, not run |
| Alembic | migration tool | `1.18.4` | installed, not run |
| Docker / Compose | Postgres runtime | `29.3.1` / `v5.1.0` | CLI installed; daemon unavailable |
| Graphify | code graph aid | `0.9.16` | generated files exist; no update run |

`mobile/node_modules/`, `mobile/package-lock.json`, `backend/.venv/`, and
`backend/uv.lock` are present. Phase 0 did not install or update dependencies.

## Runtime and service state

- Docker Compose could not connect to
  `/Users/lwt/.docker/run/docker.sock`; the Docker daemon was not running.
- No listener was present on:
  - `55432` — local Postgres
  - `3001` — FastAPI backend
  - `8081` — common Expo/Metro web port
  - `19000` — Expo development port
- No service was started and no database was created, migrated, seeded, or
  queried during Phase 0.

This is an environment state, not a failed application validation. Runtime
checks remain `NOT RUN` until their later gate.

## Workspace inventory

### Mobile

- Entry points: `mobile/app/_layout.tsx`, `mobile/app/index.tsx`
- `55` route/app files, `31` shared or feature component files, `3` service
  files, and one central `store/appStore.ts`
- Role workspaces: `auth`, `player`, and `admin`
- Current seam documents: route guards, shared UI modules, centralized domain
  types, hybrid live/mock data behaviour
- Tracked test files: `1` (`mobile/tests/heroui-compat.smoke.tsx`)
- Current validation commands available: pinned-Node TypeScript check and web
  smoke; neither was run in Phase 0

### Backend

- Entry points: `backend/app/main.py`, `backend/ai_service/main.py`
- `152` application files and `14` compatibility AI-service files, excluding
  caches
- Existing organization: entrypoints, use cases, domain, ports, adapters, DTOs,
  config, and shared code
- `18` numbered Alembic revisions (`0001` through `0018`)
- Tracked test files: `9`
- Full Ruff, format, Mypy, Pytest, migration, and runtime checks were not run in
  Phase 0

### Postgres

- Compose image: `postgres:16-alpine`
- Host mapping: `55432:5432`
- Named volume: `stringsense_postgres_data`
- Docker daemon and database service were not running at snapshot time

### NLP artifact handoff

The repository currently configures these paths in `backend/.env.example`:

| Purpose | Configured target | Presence |
| --- | --- | --- |
| Approved catalog | `backend/data/string_catalog_db_ready.json` | present |
| Unified recommendation matrix | `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx` | present |
| Compatibility matrix | `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v8_v6dict.csv` | present |
| Compatibility review aspects | `ml/nlp-workbench-latest/output/rule_based_review_aspect_signals.csv` | missing |

The missing compatibility target is an inventory observation only. Phase 1
must trace its callers and fallback behaviour before deciding whether it is a
confirmed defect, an optional generated artifact, or obsolete configuration.

## Documentation and governance state

- Root, Mobile, and Backend `AGENTS.md` files exist and name
  `ml/nlp-workbench-latest/` as canonical.
- No `CONTEXT.md` was found.
- No files were found under `docs/adr/` or `docs/adrs/`.
- `docs/plans/fyp2-execution/` contains no normal evidence, ledger, ADR, or
  baseline files in the current checkout.
- `canonical_workspace_manifest.json` was not found.
- This baseline is the first normal file under `docs/plans/fyp2-readiness/`.

Historical F0-01/F0-02 records described an accepted ADR, an execution ledger,
a canonical asset manifest, and a previously untracked canonical workspace.
Those are historical facts only. The files are not present in the current
checkout, and this review will not recreate their contents from memory.

## Validation truth table

| Check | Phase 0 status | Reason |
| --- | --- | --- |
| Git state capture | `PASS` | current command output captured |
| Protected input preservation | `PASS` | no ZIP/data read or mutation performed |
| Backend lint/type/tests | `NOT RUN` | belongs to later validation gate |
| Alembic empty-database upgrade | `NOT RUN` | Docker/database unavailable; later gate |
| Mobile pinned-Node typecheck | `NOT RUN` | belongs to later validation gate |
| Mobile web/core journeys | `NOT RUN` | services intentionally not started |
| NLP manifest/hash validation | `BLOCKED` | canonical manifest absent in current checkout |
| Notebook runtime | `NOT RUN` | would require an isolated, non-overwriting run |

Only the two Phase 0 invariants are marked `PASS`; no application correctness,
architecture quality, or FYP2 readiness claim has been made.

## Reproduction commands

The following read-only commands reproduce the baseline without reading
protected data contents:

```bash
git status --porcelain=v2 --branch
git rev-parse HEAD
git rev-list --left-right --count HEAD...origin/main
git ls-files | wc -l
git ls-files ml/nlp-workbench-latest
node --version
backend/.venv/bin/python --version
docker compose ps --format json
lsof -nP -iTCP:55432 -sTCP:LISTEN
lsof -nP -iTCP:3001 -sTCP:LISTEN
rg -n "RECOMMENDATION_MATRIX_SOURCE_PATH|AI_MATRIX_CSV_PATH|AI_REVIEW_ASPECT_CSV_PATH" backend/.env.example backend/app backend/ai_service
find docs/plans/fyp2-execution -type f ! -name '._*' -print
```

## Gate 0 decision

Phase 0 is complete when the newly created baseline file is the only review
change and the protected workspace remains otherwise unchanged. Gate 0 approval
authorizes Phase 1 read-only architecture and system review. It does not
authorize architecture edits.

During Phase 1, architecture candidates will be presented as numbered options
using the existing domain language. For each candidate, the review will identify
the files, current friction, proposed deepening, locality/leverage benefits, and
test impact. No new interface will be designed until the user selects a
candidate for discussion.
