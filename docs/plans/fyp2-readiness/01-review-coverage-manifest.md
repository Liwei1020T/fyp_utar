# StringSence FYP2 Readiness — Review Coverage Manifest

> Historical Gate 1 review evidence. The failures recorded here were the input
> to remediation; current results are in
> [04-remediation-results-and-readiness.md](04-remediation-results-and-readiness.md).

## Purpose

This manifest records what the Gate 1 review actually inspected and executed.
It separates complete source review from binary, generated, protected, and
third-party material so that "reviewed everything" remains an auditable claim.

- Review date: `2026-07-23`
- Baseline commit: `71e4402e1cc7d2350412e05facf8c10e6344539d`
- Branch: `main`
- Review mode: evidence gathering only
- Business-code changes: none
- FYP2 feature work: not started

## Coverage definition

The review covered every human-maintained source, configuration, migration,
test, and documentation file in the repository, plus every code and Markdown
cell in both canonical NLP notebooks. Generated and binary material was handled
according to its type:

| Material | Coverage | Method |
| --- | --- | --- |
| TypeScript / TSX | Complete | Full source read, cross-reference search, TypeScript validation, runtime journeys |
| Python | Complete | Full source read, architecture tracing, Ruff, Mypy, Pytest, runtime/API journeys |
| Alembic migrations | Complete | Full revision-chain read and empty-database upgrade attempt |
| Markdown / JSON / YAML / TOML / env examples | Complete | Full read and cross-file consistency checks |
| NLP notebooks | Complete at cell level | Parsed all Markdown/code cells, checked Python syntax after excluding notebook magics, inspected execution/output metadata |
| CSV / JSON / JSONL / XLSX project data | Structural and semantic validation | Parsed schemas, row counts, duplicates, split integrity, hashes, formula/sheet structure, and backend handoff fields |
| PNG evidence and app assets | Structural validation | Validated all files and dimensions, checked duplicate hashes, and exercised current UI in a browser |
| Third-party dependencies | Manifest/runtime/audit coverage | Lock/manifests, dependency-tree coherence, compatibility checks, and vulnerability audits; vendored package source was not manually read |
| `data/archive_latest.zip` | Intentionally protected | File metadata only; it was not opened, listed internally, extracted, or processed |

The protected ZIP and dependency implementation sources are therefore explicit
exceptions to literal byte-by-byte reading. Opening the ZIP would violate the
accepted data boundary, while manually reviewing all third-party source would
not establish this application's correctness.

## Repository inventory reviewed

The review traversed the repository while excluding dependency/build caches
such as `mobile/node_modules`, `backend/.venv`, Git internals, Python caches,
Expo caches, and Playwright runtime artifacts.

| Area | Reviewed contents |
| --- | --- |
| Root/governance | Root `AGENTS.md`, Git ignores, Compose definition, entry documentation, Graphify report and manifest |
| Mobile | 55 route/app files, 31 shared/feature component files, services, mappers, domain/backend types, mocks, central store, config and smoke test |
| Backend | 193 Python files across entrypoints, use cases, domain, ports, adapters, DTOs, configuration, compatibility AI service, tests and migrations |
| Database | All 18 Alembic revisions from `0001` through `0018`, ORM models, repositories and Compose Postgres configuration |
| NLP | Both canonical notebooks, requirements, README, dictionaries, normalization rules, review corpus, ABSA splits and approved matrix outputs |
| Documentation/evidence | 36 Markdown files and 114 PNG files; all PNGs were valid and 25 duplicate-hash groups were identified |

Graphify's current report contains 2,094 nodes, 5,613 edges and 191
communities. It reports no import cycle; it also shows the unusually broad
reach of `useAppStore` and `useCurrentUser`, which have 82 and 78 graph edges
respectively.

## Static validation executed

### Backend

| Check | Result |
| --- | --- |
| `uv lock --check` | Pass |
| Environment package compatibility (`uv pip check`) | Pass: 37 packages compatible |
| `ruff check .` | Pass |
| `ruff format --check .` | Pass |
| `mypy app ai_service tests` | Pass |
| `pytest -v` | Pass: 47 tests |
| Empty Postgres `alembic upgrade head` | Fail at revision `0008`; see system review P0-1 |
| Python dependency vulnerability audit | 27 known vulnerabilities across 9 packages |

The migration test used an isolated review database. Its transaction rolled
back and the database contained zero tables after failure. It did not alter the
existing project database.

### Mobile and Node

| Check | Node 20.19.0 | Node 24.15.0 |
| --- | --- | --- |
| `npx tsc --noEmit` | Pass | Pass |
| Expo SDK 54 web compile | Pass, 3,747 modules | Pass, 3,747 modules |
| Browser-rendered welcome page | Pass | Pass |
| Expo Doctor | 17/17 checks passed | Not repeated after compatibility proof |

The machine's default Node `25.9.0` was deliberately not used as the project
baseline. Expo startup also reported five SDK-54 package patch releases behind
the versions expected by the installed SDK.

`npm ls --depth=0` found a coherent direct dependency tree. `npm audit
--omit=dev` reported 153 advisories: 3 critical, 47 high, 10 moderate, and 93
low. No automatic audit fix or dependency change was made.

The mobile package currently has no lint command and no application behaviour
test suite. Its single tracked test file is a compatibility smoke file, not a
route or domain regression suite.

## Runtime validation executed

The current Mobile and Backend were run against an isolated Postgres database.
No production or user database was used. Review-only users were created without
recording credentials in the repository.

### Successful end-to-end paths

- Player registration, login and profile retrieval
- Public catalog retrieval: 33 strings
- Drop-off slot retrieval: 236 slots
- V5 recommendation request and result rendering
- Booking creation and player booking retrieval
- Admin login, booking list/detail, check-in/status operations
- Admin inventory list/detail and stock update
- Business-hours retrieval
- Analytics and recommendation-audit retrieval
- Current player and admin route guards under an active in-memory session

### Negative and integrity probes

- The advertised prefilled admin account was rejected on a clean environment.
- A slot with capacity 3 accepted enough direct API bookings to reach a booked
  count of 6.
- A booking with drop-off date `2020-01-01` was accepted.
- Updating stock to zero hid a catalog item; restoring positive stock also
  reactivated it, even though visibility and availability are separate concerns.
- The recommendation result showed `86%` on the list and `8600% MATCH` on its
  detail page.
- A registered player's backend contact information rendered as `Walk-in
  player` / `No contact provided` in the admin booking detail.
- A full page reload deliberately discarded the backend token and returned to
  the welcome route.
- Repeated React Native Web colour-conversion and deprecated-style warnings
  appeared in the browser console.

## NLP validation executed

| Check | Result |
| --- | --- |
| Labeling notebook structure | 30 cells: 14 code; no saved execution counts or outputs |
| Complete-pipeline notebook structure | 44 cells: 21 code; no saved execution counts or outputs |
| Labeling notebook syntax scan | Pass after excluding notebook magics |
| Complete-pipeline syntax scan | Fail in code cell 26 due to an unterminated string expression |
| String/review sources | 33 strings and 22,250 review groups; JSON/JSONL parse cleanly |
| ABSA dictionary | 320 rows, 9 aspects, no duplicate or polarity-conflicting terms |
| Normalization rules | 27 valid regular expressions |
| Current split integrity | 19 review groups and 19 identical review texts occur across train/validation/test |
| Matrix workbook | One visible sheet, 33 rows, 55 columns, no formulas, blank headers or duplicate names |

The current labeling notebook splits by aspect sample ID rather than review ID.
Of 22,250 review groups, 19 cross dataset partitions; 160 identical review
texts therefore leak across partitions. The notebook was not executed because
the accepted review boundary forbids overwriting protected/current artifacts
and because its downstream pipeline contains a syntax error.

The legacy source term `attack` was kept distinct from the backend domain term
`repulsion`; no automated rename or semantic collapse was performed.

## Explicitly not executed

- No protected ZIP read, extraction or rewrite
- No notebook top-to-bottom execution or model training
- No source dataset mutation
- No migration repair or schema edit
- No package install, upgrade, downgrade or audit fix
- No architecture refactor or product defect fix
- No Git stage, commit, reset, restore, branch change or push
- No production infrastructure, authentication or data operation

## Coverage conclusion

Gate 1 has sufficient evidence for architecture discussion. It does not yet
support FYP2 development approval: the empty-database migration, booking
integrity, and NLP evaluation boundary are blocking failures. The detailed
findings and remediation candidates are recorded in the adjacent review files.
