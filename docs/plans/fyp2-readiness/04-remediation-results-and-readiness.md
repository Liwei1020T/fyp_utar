# StringSence FYP2 Readiness — Remediation Results and Gate 5 Decision

Date: 2026-07-23

## Decision

**TECHNICALLY READY FOR USER APPROVAL. FYP2 DEVELOPMENT HAS NOT STARTED.**

All P0 blockers and the code, architecture, tooling, dependency, data-integrity
and auditability defects that were accepted for remediation have been repaired
or given an explicit non-fabrication/preservation disposition. The remaining
Gate 5 condition is the user's explicit approval to begin FYP2 development.

This decision supersedes the historical `NOT READY` result in
[02-system-review.md](02-system-review.md). It does not authorize an automatic
transition into FYP2 work.

## Selected architecture

The approved sequence was executed as `F -> A -> C -> B -> D -> E`:

| Phase | Resulting boundary |
| --- | --- |
| F — toolchain | Mobile uses exact Node `24.18.0` with `>=24.18.0 <25`; the machine's Node 25 is not the project runtime. Backend and NLP dependencies are locked and audited. |
| A — database | Alembic models and revisions `0001`–`0018` are the schema authority. Clean PostgreSQL migration reaches head. Booking capacity is reserved under a database row lock. |
| C — backend | FastAPI use cases own validation and transactions. Catalog editing is one atomic backend command. Legacy optional AI adapters no longer initialize at API startup. |
| B — mobile | Expo is a backend-backed mobile client. Zustand owns current server-state hydration; the unused QueryClient boundary was removed. Native tokens use SecureStore. |
| D — recommendation | The in-process FYP1 scorer is the sole live owner. Saved runs preserve algorithm, matrix, source timestamps, evidence counts and score layers for admin audit. |
| E — NLP | `ml/nlp-workbench-latest` is the canonical offline workbench. Thin notebooks call tested modules and write immutable run directories; no public NLP service was introduced. |

## Finding disposition

### P0 blockers

| ID | Status | Remediation evidence |
| --- | --- | --- |
| P0-1 | Resolved | Revisions `0008`/`0009` now support a clean PostgreSQL chain; an isolated empty database reached `20260423_0018 (head)`. |
| P0-2 | Resolved | Booking requests use a server-owned slot ID, validate schedule/timezone rules and reserve capacity atomically. The real PostgreSQL concurrency test created exactly capacity bookings and rejected the overflow workers. |
| P0-3 | Resolved | Both notebooks execute through tested modules. Split assignment is review-text-group based; review, group and normalized-text cross-partition counts are all zero. Two complete runs have identical metrics and seven identical CSV hashes. |

### P1 findings

| ID | Status | Remediation |
| --- | --- | --- |
| P1-1 | Resolved | Bundled/demo credentials and autofill were removed. Admin access is explicitly operator-configured through `SEED_ADMIN_*`; player registration remains the reproducible entry path. |
| P1-2 | Resolved | Recommendation percentages have one 0–1 to percent conversion; browser detail and list both rendered `91%`. |
| P1-3 | Resolved | Live slot-load failure remains an error state and cannot silently submit mock availability to the backend. |
| P1-4 | Resolved | Booking mapping no longer invents paid state or mutable historical payment facts; FYP1 displays a quote while payment remains deferred. |
| P1-5 | Resolved | Real backend username and phone fields flow into admin booking detail. |
| P1-6 | Resolved | Hybrid main/cross gauge and hybrid status survive unrelated admin edits. |
| P1-7 | Resolved | Catalog, inventory, scores and image metadata are saved by one backend editor transaction. |
| P1-8 | Resolved | Stock availability and catalog activation are independent fields. Stock corrections no longer publish or hide products. |
| P1-9 | Resolved | Conditional-hook paths were reordered and Expo ESLint is now a project gate. |
| P1-10 | Resolved | Unused legacy review/RAG/recommendation adapters were removed from eager dependency construction; a boundary test protects startup ownership. |
| P1-11 | Resolved | Mobile production/full audits, backend locked dependency audit and NLP locked dependency audit report no known vulnerabilities. |
| P1-12 | Resolved for the primary mobile target | iOS/Android tokens persist in SecureStore and are validated during bootstrap; logout clears the token. Web intentionally remains memory-only, so a full web reload requires login. |
| P1-13 | Closed without fabricated data | Zero/absent source prices are treated as missing, never as `RM 0` or an invented value. The current live inventory has one hidden price-pending item; admin summary and `Price Missing` filter both report one. |

### P2 findings

| IDs | Status | Remediation |
| --- | --- | --- |
| P2-1–P2-5 | Resolved | Inventory movements store deltas; business-hour breaks are validated; matrix re-import refreshes source timestamps; “Today” uses service/drop-off time; explicit backend tension ranges are authoritative. |
| P2-6–P2-11 | Resolved | Explanations no longer manufacture review claims; compare handles missing/tied evidence; setup copy is data-driven; rejected stays rejected; booking dates are formatted; username changes persist through the backend. |
| P2-12–P2-15 | Resolved | Server-state ownership was simplified, Expo SDK patches aligned, web console errors/warnings removed, and Node 24 replaced unsupported Node 20. |

### P3 findings

| ID | Status | Disposition |
| --- | --- | --- |
| P3-1 | Resolved | Scoring documentation and code both use `.60/.15/.15/.10`. |
| P3-2 | Resolved | Database documentation lists revisions through `0018`. |
| P3-3 | Resolved | Current player, booking, inventory and recommendation-audit browser evidence was regenerated under `mobile/output/playwright/fyp2-readiness-20260723/`. |
| P3-4 | Preserved intentionally | Ignored AppleDouble sidecars were not deleted because they are filesystem metadata in the protected NLP tree. |
| P3-5 | Preserved intentionally | Duplicate appendix/evidence images were not deduplicated without evidence-owner approval. |
| P3-6 | Resolved | New NLP artifacts live under immutable `output/runs/<run-id>/` directories with manifests and hashes; protected historical `*_latest` assets were not overwritten. |

## Verification record

| Area | Command or flow | Result |
| --- | --- | --- |
| Clean database | Empty temporary PostgreSQL DB + `alembic upgrade head` | Passed all 18 revisions; `20260423_0018 (head)`. Temporary DB was dropped after proof. |
| Booking concurrency | `POSTGRES_TEST_DATABASE_URL=... pytest tests/test_booking_capacity_postgres.py` | `1 passed`; capacity never exceeded. |
| Backend static/tests | Ruff, Ruff format, Mypy, full Pytest | Ruff passed; 196 files formatted; 176 files type-safe; `53 passed, 1 skipped`. The skipped PostgreSQL test then passed explicitly above. |
| Backend packages | `uv pip check`; locked `pip-audit` | Compatible; no known vulnerabilities. |
| Mobile runtime | Node/npm | Node `24.18.0`, npm `11.16.0`; package engine excludes Node 25. |
| Mobile static/build | Expo lint, `tsc --noEmit`, Expo Doctor, Expo web export | Passed; Doctor `18/18`; final export bundled 3,626 modules. |
| Mobile packages | Production and full `npm audit` | `0 vulnerabilities` in both scopes. |
| Browser player flow | Login -> profile/catalog -> recommendation -> explanation -> slot -> booking | All application API calls returned 200; created `ORD-2AD07`; displayed evidence-backed `91%` shortlist. |
| Browser admin flow | Booking queue -> expected completion -> status -> service log -> inventory -> recommendation audit | Same booking reached `In Progress`; service note persisted; price filter/count agreed; source time and review counts rendered. |
| Browser console | Final rebuilt export | 0 errors, 0 warnings. Chrome emits one verbose password-manager hint because React Native Web does not render a native HTML form. |
| NLP static/tests | Pytest + Ruff + Ruff format | `10 passed`; lint and format checks passed. |
| NLP full execution | Runs `fyp2-readiness-20260723-v2-r1` and `-r2` | Both completed; 33 strings, 22,250 reviews, 200,250 long rows and 178,219 high-confidence rows. |
| NLP leakage | Both run manifests | Review/group/text cross-partition counts `0`; duplicate sample IDs `0`. |
| NLP reproducibility | `fyp2-readiness-20260723-v2-reproducibility.json` | Metrics and all seven CSV hashes match. |
| Repository hygiene | `git diff --check`; tracked credential/key scan | Passed; no tracked private-key, OpenAI-key or AWS-key pattern found. |

The two reproducible NLP runs reported:

- mention test accuracy `0.730852`, macro F1 `0.717943`;
- sentiment test accuracy `0.893035`, macro F1 `0.839618`;
- canonical V9 workbook SHA-256
  `382d71cd90e195fcc41550c38175c13e1bb01515615fda572cf22fee90e05209`;
- protected raw reviews, dictionary, normalization rules, canonical workbook
  and ZIP metadata unchanged. The ZIP content was intentionally not opened.

## Controlled residual boundaries

These are explicit product/deployment boundaries, not hidden pass claims:

1. The primary target is Expo mobile. Native sessions persist securely; the
   web smoke target deliberately keeps tokens in memory.
2. A plain Python static server has no SPA rewrite rule, so directly reloading a
   nested exported web URL returns the server's 404. Client-side navigation is
   valid; a real web host must route unmatched paths to `index.html`.
3. Source prices that are absent remain `Price pending`. No repair invented
   business prices.
4. The browser acceptance test intentionally left local evidence booking
   `ORD-2AD07` in `In Progress`, with an acceptance-test note and expected
   completion on 25 July 2026.
5. PostgreSQL remains healthy as the local runtime data service. The backend,
   temporary web server and all acceptance browser sessions were stopped after
   verification without deleting data.

## Gate 5

Technical gates 1–6 are satisfied. Gate 7 is still open:

> Do not begin FYP2 development until the user explicitly approves the final
> readiness gate.

After approval, the first FYP2 task should be selected as a bounded task card;
this remediation does not implicitly select or implement one.
