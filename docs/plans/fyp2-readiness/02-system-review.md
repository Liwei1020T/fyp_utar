# StringSence FYP2 Readiness — Complete System Review

> Historical Gate 1 finding report. Its `NOT READY` decision has been
> superseded by the post-remediation verification in
> [04-remediation-results-and-readiness.md](04-remediation-results-and-readiness.md).
> FYP2 development still requires explicit user approval.

## Gate 1 decision

**Status: NOT READY FOR FYP2 DEVELOPMENT.**

The application has a usable FYP1 core and its existing backend tests and
static checks pass, but three release-blocking contracts fail on a clean or
adversarial path:

1. a new database cannot migrate to head;
2. booking capacity and date rules are not enforced by the backend;
3. the canonical NLP evaluation split leaks reviews and the complete notebook
   has a syntax error.

No issue below has been repaired during Gate 1. Architecture direction must be
approved before implementation starts.

## Severity model

- **P0 — blocker:** invalidates clean setup, core data integrity, or FYP
  evaluation evidence.
- **P1 — high:** can corrupt or materially misrepresent live user/admin data,
  security/support status, or recommendation behaviour.
- **P2 — medium:** incorrect secondary behaviour, fragile contracts, or missing
  verification likely to become a regression.
- **P3 — low:** hygiene, stale evidence, or maintainability debt without a
  demonstrated immediate integrity failure.

## P0 blockers

### P0-1 — Empty-database migration fails at revision 0008

`backend/migrations/versions/20260412_0008_normalize_string_catalog.py:1079`
recreates `bookings`. PostgreSQL refuses to drop its primary key because later
booking-status tables already have incoming foreign keys. The documented clean
setup command therefore cannot reach migration head.

**Evidence:** `alembic upgrade head` failed against an empty isolated Postgres
database and rolled back to zero tables. Existing unit tests do not exercise a
fresh PostgreSQL migration chain.

**Impact:** a teammate, assessor, CI job, or deployment cannot reproduce the
system from the repository.

### P0-2 — Booking creation bypasses slot capacity and scheduling policy

`backend/app/use_cases/booking/create_booking.py:18` checks that the selected
string exists but does not reserve or validate a drop-off slot. The request DTO
accepts an arbitrary datetime at `backend/app/dto/booking.py:23`. Mobile sends a
datetime rather than a server-owned slot identity at
`mobile/app/player/bookings/summary.tsx:87`.

**Runtime proof:** a capacity-3 slot reached `booked_count = 6`, and a booking
dated `2020-01-01` was accepted. UI disabling of full slots does not protect the
API against concurrency, stale clients, or direct calls.

**Impact:** overbooking and impossible schedules become committed runtime data.

### P0-3 — Canonical NLP evidence is not executable or evaluation-safe

`ml/nlp-workbench-latest/stringsense_complete_absa_pipeline_notebook_latest.ipynb`
code cell 26 contains an unterminated join expression, so it cannot run
top-to-bottom. Code cells 16 and 20 of
`ml/nlp-workbench-latest/stringsense_absa_labeling_notebook_latest.ipynb`
build `sample_id = review_id + aspect` and apply the deterministic split to that
sample ID rather than to the review group.

**Data proof:** 19 review groups cross partitions; those groups account for 160
identical review texts appearing in more than one of train, validation and
test. Both notebooks have no saved execution counts or outputs.

**Impact:** reported validation/test performance would contain leakage and
cannot be accepted as FYP2 model evidence.

## P1 high-severity findings

### P1-1 — Clean-environment demo credentials are not reproducible

`mobile/app/auth/login.tsx:41` advertises player and admin credentials. The
backend example configuration keeps seeding disabled and provides only optional
admin placeholders at `backend/.env.example:21`; no player seed exists.

**Runtime proof:** the prefilled admin login returned `Invalid credentials` on
the isolated environment.

### P1-2 — Recommendation percentage is multiplied twice

`mobile/services/backendMappers.ts:899` converts a 0–1 backend score to an
integer percentage. `mobile/app/player/strings/[id].tsx:289` multiplies that
integer by 100 again.

**Runtime proof:** the result list displayed `86%`; the detail displayed
`8600% MATCH`.

### P1-3 — Failed live slot loading silently switches to mock booking data

`mobile/app/player/bookings/new.tsx:102` falls back to mock slots when the live
request fails. The chosen mock time is later submitted to the real booking API,
whose missing validation is described in P0-2.

**Impact:** degraded connectivity can create a real booking from a schedule the
server never offered.

### P1-4 — Booking mapper invents payment facts and mutable prices

`mobile/services/backendMappers.ts:755` maps every backend booking to
`paymentStatus: 'paid'` and derives paid amount from the current catalog price.
The FYP1 backend has neither a payment transaction nor a booked-price snapshot
in that response.

**Impact:** a refresh can turn a locally pending booking into paid and can
rewrite historical value when catalog price changes.

### P1-5 — Admin booking detail discards real customer identity/contact

The backend mobile type already exposes `customer_phone_number` and
`customer_username` at `mobile/types/backend.ts:281`, but the mapper at
`mobile/services/backendMappers.ts:755` ignores both. The admin detail then
looks up mock users and falls back at
`mobile/app/admin/bookings/[id].tsx:370` and
`mobile/app/admin/bookings/[id].tsx:913`.

**Runtime proof:** a registered review player appeared as `Walk-in player` and
`No contact provided`.

### P1-6 — Editing a hybrid string can erase its cross-string metadata

The backend represented AEROBITE with different main/cross gauge values
(`0.67`/`0.61`). The admin editor exposes one gauge and its payload sends that
value for both fields plus `is_hybrid: false` at
`mobile/app/admin/inventory/[id].tsx:420`.

**Impact:** an unrelated catalog edit can silently convert hybrid data into a
non-hybrid record.

### P1-7 — Admin catalog save is a non-atomic sequence

`mobile/app/admin/inventory/[id].tsx:892` issues separate image, catalog, score
and inventory writes. There is no compensating transaction or backend command
owning the complete update.

**Impact:** a later request failure leaves a partially saved catalog item.

### P1-8 — Stock level controls catalog visibility

`backend/app/entrypoints/api/routes/admin_routes.py:343` assigns
`is_active = stock_level > 0`; the repository mirrors that value into catalog
records at
`backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py:349`.

**Runtime proof:** stock zero hid an item, and restoring positive stock
reactivated it. A deliberately hidden product can therefore become public after
a stock correction.

### P1-9 — Hooks are called conditionally on six screens

Hooks appear after an early conditional user return in:

- `mobile/app/player/profile/edit.tsx:97`
- `mobile/app/player/bookings/new.tsx:73`
- `mobile/app/player/(tabs)/recommend.tsx:57`
- `mobile/app/player/(tabs)/bookings.tsx:41`
- `mobile/app/admin/(tabs)/chat.tsx:17`
- `mobile/app/admin/(tabs)/bookings.tsx:167`

TypeScript does not enforce the Rules of Hooks and the project has no ESLint
gate. A user/session transition can change hook order and trigger a render
failure.

### P1-10 — Legacy AI implementations are eagerly loaded at API startup

`backend/app/entrypoints/api/dependencies.py:34` imports and constructs three
compatibility adapters. The review/RAG constructors instantiate the legacy
`ai_service.RecommendationService`, whose data loader defaults to older V8
files at `backend/ai_service/data_loader.py:14`. The corresponding dependency
getters have no current route caller; the live recommendation scorer is instead
`backend/app/domain/recommendation/scoring.py`.

**Impact:** startup depends on obsolete optional artifacts and the system has
two plausible recommendation implementations with different ownership.

### P1-11 — Current dependency baseline contains known vulnerabilities

The mobile production dependency audit reported 153 advisories, including 3
critical and 47 high; Axios and Expo/React Native transitive packages are among
the affected paths. The backend audit reported 27 advisories across 9 packages,
including Starlette, PyJWT and python-multipart.

**Impact:** the repository cannot claim a reviewed security baseline. Blind
`audit fix` is not appropriate because many paths require controlled framework
updates and regression testing.

### P1-12 — Backend sessions are intentionally lost on app/browser restart

`mobile/store/appStore.ts:218` returns no backend session state, and
`extractPersistedState` at `:222` strips the backend token and live identity.

**Runtime proof:** a full page reload returned the authenticated user to the
welcome route.

**Impact:** the current behaviour is secure-by-discard but is not a usable
mobile session contract; token storage/refresh/logout policy is undefined.

### P1-13 — Most catalog prices are incomplete

The approved V9 workbook has 33 valid string names but 23 rows with
`price_rm = 0`. The admin inventory browser view reported the same 23
`Price pending` items.

**Impact:** the booking/payment presentation cannot produce credible prices for
most recommendations. This is a data-readiness issue, not permission to invent
values.

## P2 medium-severity findings

| ID | Finding and evidence | Consequence |
| --- | --- | --- |
| P2-1 | Inventory movement writes the resulting available stock as `quantity` at `backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py:418`, not the change delta. | Audit history cannot distinguish additions, removals or corrections. |
| P2-2 | Business-hours validation at `backend/app/dto/store.py:20` checks ordering but not paired break fields or whether the break is inside opening hours. | Internally inconsistent schedules can be saved. |
| P2-3 | Recommendation matrix update fields at `backend/app/adapters/persistence/sqlalchemy/recommendation_matrix_import.py:251` omit `source_generated_at`, although the payload builds it. | Re-imported records can retain stale provenance timestamps. |
| P2-4 | Dashboard and admin booking filters use `createdAt` (`mobile/app/admin/(tabs)/dashboard.tsx:79`, `mobile/app/admin/(tabs)/bookings.tsx:211`) for “Today”, not the drop-off/service date. | Historical or future service work is counted on creation day; runtime showed seven “today” bookings including a 2020 drop-off. |
| P2-5 | `deriveRecommendedTension` ignores explicit backend tension min/max at `mobile/services/backendMappers.ts:325`, while catalog mapping stores those values separately. | Admin changes and player-facing tension guidance can disagree. |
| P2-6 | Detail/explanation pages manufacture review confidence and performance claims when evidence is absent (`mobile/app/player/strings/[id].tsx:142`, `mobile/app/player/strings/[id].tsx:409`, `mobile/app/player/recommend/explain/[id].tsx:553`). | Recommendation explanations overstate what the model/data proves. |
| P2-7 | Compare logic at `mobile/app/player/strings/compare.tsx:49` only selects A when both scores exist; otherwise B receives visual and CTA preference. | Missing data becomes an accidental product recommendation. |
| P2-8 | Compare copy at `mobile/app/player/strings/compare.tsx:333` always describes a hard-coded 24–29 lb aggressive setup. | Advice ignores profile, string and recommendation evidence. |
| P2-9 | Backend `rejected` maps to client `cancelled` at `mobile/services/backendMappers.ts:680`. | Operational reason and audit semantics are lost. |
| P2-10 | `mobile/components/booking/BookingCard.tsx:111` uses the truthy raw date before its formatter. | Dates render in backend/raw form instead of the intended label. |
| P2-11 | Profile edit posts preference/profile fields but not username (`mobile/app/player/profile/edit.tsx:135`); the backend profile DTO has no username field (`backend/app/dto/profile.py:11`). | The visible name update is local and disappears after login. |
| P2-12 | QueryClient is provided in `mobile/app/_layout.tsx:5`, but reviewed app data flows use manual hydration and Zustand rather than query ownership. | Cache invalidation, request lifecycle and server-state consistency remain ad hoc. |
| P2-13 | Expo startup reported five SDK-54 patch mismatches. | Known SDK fixes are missing even though the major-version baseline is coherent. |
| P2-14 | Repeated React Native Web colour-conversion and deprecated style/pointer-event warnings occurred across live routes. | Console signal is noisy and browser rendering behaviour is more fragile. |
| P2-15 | Node is pinned to 20.19.0 even though Node 20 ended support on 2026-03-24. | Security/maintenance baseline is unsupported despite current compatibility. |

## P3 hygiene and evidence findings

| ID | Finding | Recommended disposition |
| --- | --- | --- |
| P3-1 | Backend README and runbook describe recommendation weights as `.60/.25/.15`, while runtime code uses `.60/.15/.15/.10`. | Update docs only after the canonical scoring implementation is approved. |
| P3-2 | Database documentation ends its migration sequence at `0014`; repository head is `0018`. | Regenerate/repair migration documentation with the migration fix. |
| P3-3 | Historical route inventory and Playwright snapshots refer to removed routes and mock-only/hidden flows. | Archive or regenerate evidence from the current app. |
| P3-4 | Twenty ignored AppleDouble `._*` sidecars exist in the NLP tree. | Clean only with explicit approval; keep ignore rules. |
| P3-5 | 25 duplicate PNG hash groups cover 51 files, mostly appendix copies and before/after evidence. | Deduplicate only if evidence ownership permits it. |
| P3-6 | The labeling notebook writes `*_latest.csv`, while its README promises versioned outputs. | Adopt immutable run IDs/manifests before another notebook run. |

## Positive findings

The review also confirmed working foundations worth preserving:

- Backend Ruff, format, Mypy and all 47 existing tests pass.
- Mobile TypeScript passes under both Node 20.19.0 and Node 24.15.0.
- Expo Doctor passes all 17 checks.
- Node 24 successfully compiles and renders the current Expo SDK 54 web app.
- Real registration, catalog, recommendation, booking, admin, check-in,
  analytics and audit APIs operate against isolated Postgres.
- Production configuration rejects an absent JWT secret; the development
  fallback is explicitly scoped.
- CORS configuration is explicit.
- No tracked `.env`, private key, AWS-style credential or OpenAI-key pattern was
  found; the local backend environment is ignored.
- Graphify reports no import cycle.
- The NLP dictionaries, JSON/JSONL sources and workbooks parse cleanly.
- The V9 matrix contains 33 unique products, one visible sheet, no formulas and
  no duplicate/blank names.
- All 114 PNG assets are valid image files.

## Node decision

Use Node 20.19.0 only to reproduce the current baseline. Do not standardize on
the machine's Node 25.9.0. The remediation baseline should move to Node 24 LTS
in one controlled change that updates `.nvmrc`, `package.json` engines,
documentation and CI together, then repeats TypeScript, Expo Doctor, web smoke
and core browser journeys.

This recommendation is supported by the direct Node 24 compatibility proof and
by the fact that the current Node 20 line is no longer supported. It is not a
request to upgrade before Gate 1 approval.

## Readiness conclusion

FYP2 development must remain blocked until, at minimum:

1. clean PostgreSQL migration reaches head;
2. booking creation performs an atomic server-side slot reservation and rejects
   invalid/full slots;
3. the NLP pipeline is executable and review-level split integrity is proven;
4. high-risk mapper/catalog corruption paths have regression coverage;
5. supported Node and controlled dependency baselines are verified;
6. the complete post-fix static, API and browser regression suite passes; and
7. the user explicitly approves the final FYP2 readiness gate.
