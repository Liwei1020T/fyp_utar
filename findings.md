# Agent Scope Findings

> Historical, append-only findings log. Dated observations below are evidence
> from earlier runtimes and are not current schema truth. Use the repository
> README and `backend/docs/database.md` for the current 12-string seed,
> migration head, and active table boundaries.

## Agent comparison and validation (2026-08-24)

- `compare_strings` is fully implemented and currently excluded only by the
  player tool allowlist, focused prompt, starter question, tests, and docs.
- The existing comparison tool returns approved catalog, official performance,
  price, stock, and aspect-score fields for two or three distinct catalog IDs;
  V11 remains the only ranking owner.
- The task requires separate evidence for fake-model contracts, live provider
  behavior, and browser UI; success in one layer does not imply the others.
- Focused contracts now pass with `compare_strings` active; all Agent write
  actions remain restricted to the existing `open_string` navigation action.
- Live runtime preflight found Docker Desktop stopped, no listeners on backend
  port 3001 or Web port 8081, and 16 untracked AppleDouble migration sidecars.
  The repository Alembic wrapper is the documented cleanup boundary for those
  metadata files before the full suite is rerun.
- The standard wrapper safely removed only AppleDouble sidecars; PostgreSQL is
  healthy at migration head and the Web production bundle exports successfully.
- A real DeepSeek request completed successfully and returned a valid grounded
  response ID, proving the configured provider/model path works. The first
  comparison still returned `insufficient_evidence` because the model supplied
  display names while `compare_strings` accepted only exact catalog IDs.
- The isolated seed contains the requested Yonex BG80/BG65 rows under
  `yonex-bg80` and `yonex-bg65`; the failure is an identifier-resolution contract
  gap, not missing catalog data.
- `CatalogRepository.list_active_catalog()` already provides the bounded,
  approved set needed for exact case-insensitive display-name resolution; no
  fuzzy search, new endpoint, or dependency is required.
- After exact-name resolution was added, a fresh real DeepSeek comparison
  succeeded for Yonex BG80 versus BG65. The response cited both backend catalog
  sources, reported truthful pending prices and live stock, and used
  `evidence_status=partial` without claiming review analysis.
- Live store-information retrieval also passed with two backend sources. The
  first live guided preview correctly reached V11 but returned no candidates
  because the isolated fresh catalog has pending prices and the required RM
  budget filters unknown-price items; isolated admin pricing is needed to test
  a non-empty recommendation result.
- After isolated admin pricing, the live guided preview returned Yonex BG80 and
  EXBOLT 63 with truthful prices, recommendation-run provenance, and verified
  `open_string` actions. Live admin summary and low-stock inventory queries also
  passed with the expected backend source types.
- The first live booking-attention wording was answered from the operations
  summary, so it does not yet prove the provider selected `find_admin_bookings`;
  an explicit record-search prompt remains required.
- After creating one isolated booking through the public player API, the real
  admin Agent returned both operations and booking sources, proving live
  `find_admin_bookings` selection. All active admin reads remain action-free.
- The production Web bundle defaults to the correct local API base
  `http://127.0.0.1:3001/api`, so it can be served directly for browser testing.
- Playwright production-Web acceptance passed through the real navigation path:
  player login -> home -> StringSense AI -> Compare BG80/BG65. The rendered
  answer shows both prices, stock, specifications, trade-off, and three evidence
  bullets without exposing internal tool names or calculations.
- Browser network evidence shows the Agent POST returned HTTP 200 after all
  authenticated bootstrap reads; Playwright reported zero console errors and
  zero warnings on the accepted comparison page.
- Final quality gates are green: 147 backend tests passed with 2 expected skips,
  all backend static checks passed, all Mobile checks passed, and the final diff
  contains no whitespace errors or AppleDouble migration sidecars.

## WhatsApp password-reset delivery (2026-08-18)

- Forgot Password now sends its six-digit code through the configured OpenWA
  session; development preview remains separately gated.
- Unknown phone numbers and provider failures retain the same generic response,
  so the endpoint does not reveal whether an account exists.
- Admin notifications already establish the required transaction pattern:
  prepare the persisted record, commit it, and only then perform provider I/O.
- The smallest safe integration is one shared stdlib OpenWA text sender plus an
  internal reset result that carries the plaintext code only in process memory.
- The route commits before scheduling provider I/O, and the regression test
  proves the committed code is visible from a separate database session before
  the OpenWA sender runs.
- Automated verification is complete, but the current OpenWA session still
  requires QR connection and a real-phone receipt before live delivery can be
  claimed.

## Password delivery, service fee, and commit handoff (2026-08-18)

- The user expects Forgot Password to use WhatsApp; verify the actual route and
  provider call before describing it as complete.
- `default_service_price` must be traced into the current quote/UI flow before
  deciding whether RM0 is intentional or missing configuration.
- Use a scoped Git commit and preserve unrelated/generated dirty-tree content.
- Forgot Password is not currently delivered through WhatsApp. The request use
  case generates and stores a six-digit code and only returns it when the
  development preview is enabled; it has no OpenWA/provider dependency. The
  mobile helper copy also says WhatsApp delivery can be added later.
- `default_service_price` is the shop's stringing/service labor fee. Booking
  payment quotes and writes use `string selling price + service fee`; the Admin
  Settings field controls it. The retained database value is RM0, so the current
  total charges only the string price.
- Pre-commit verification passed: `git diff --check`, Ruff, 10 notification
  tests, and 6 system-cohort tests.

## Runtime catalog archival (2026-08-18)

- The user superseded the earlier runtime-retention boundary: only the approved
  12 strings should remain in the live system, while the other catalog material
  must be recoverable later.
- This does not authorize deletion of the original 33-string research source,
  protected NLP workbooks, or run artifacts. The mutation target is the retained
  PostgreSQL runtime database after a verified archive is created.
- PostgreSQL has eight direct foreign keys to `strings`: seven catalog/cache
  tables cascade on delete, while `bookings.string_id` is restrictive and may
  block pruning if historical bookings reference non-approved strings.
- Recommendation run items also carry string `catalog_id` values without a
  foreign key, so dependency discovery cannot rely only on `pg_constraint`.
- Runtime schema contains nine tables with a direct `catalog_id` or `string_id`
  column, including both current `inventory_items` and legacy
  `string_inventory_items`. Inventory movements depend on current inventory
  rows indirectly through `inventory_id` and must be archived with them.
- The 21 non-approved strings currently own 21 inventory rows, 22 inventory
  movements, 21 metric rows, 82 tags, 21 official-performance rows, 273 matrix
  rows, and 18 cache rows. The legacy inventory table has no matching rows.
- Four non-approved strings are referenced by six historical bookings, and
  non-approved IDs appear in 19 recommendation-run items. Physical deletion
  would therefore either fail or damage retained business history unless the
  design is broadened beyond catalog cleanup.
- Startup seeding only runs when the `strings` table is empty. It already marks
  non-cohort seed rows and inventory inactive/out-of-stock, so a soft archive
  will not be silently reversed on normal backend restart.
- The existing `is_active` and inventory availability fields are the minimal
  reversible mechanism: archive all 21 in place, preserve their catalog and
  history dependencies, and keep the approved cohort as the separate gate for
  any future restoration.
- The six dependent bookings are historical/current business records across
  completed, ready-for-collection, and in-progress states; they must not be
  deleted merely to reduce catalog row count.
- Created a private custom-format PostgreSQL backup at
  `backend/var/backups/stringsense-pre-12-only-20260818T142221.dump` plus SHA-256
  sidecar. A full restore into a temporary database verified migration head
  `20260818_0032`, 33 strings, and 377 bookings before the temporary database
  was removed.
- Created a 21-row pre-archive activation/inventory manifest at
  `backend/var/backups/nonapproved-string-state-20260818T142221.csv` with its own
  SHA-256 sidecar.
- A single PostgreSQL transaction archived all 21 non-approved catalog and
  inventory records. Database assertions passed: exactly 12 strings remain
  active and no non-approved string or inventory row remains active.
- Post-start verification passed: backend health is `ok`, the MacBERT artifact
  still imports 108 rows, active strings/inventory are 12/12, archived
  strings/inventory are 21/21, both recovery checksums validate, and
  `git diff --check` is clean.

## WhatsApp and database continuation (2026-08-18)

- The latest requested boundary is live OpenWA delivery, retained-database
  migration, and a database-backed list of the approved system strings.
- Preserve the existing notification contract: persist the in-app delivery
  first, then attempt OpenWA; a provider failure must not remove the record.
- Do not reset the PostgreSQL volume. Inspect current revision and data before
  applying the existing migration head.
- The repository Compose file currently defines only PostgreSQL; OpenWA is not
  a managed service in this workspace.
- `backend/.env` currently contains no OpenWA settings, while `.env.example`
  documents a disabled provider, base URL, session ID, and server-side API key.
- The current branch includes commit `6a303ce` for QR/cash payments and the
  Alembic source head is `20260818_0032`.
- Official OpenWA `v0.11.1` is the current release. Its documented API matches
  the existing StringSense endpoint and `X-API-Key` contract: create a session,
  start it, fetch the QR, then send text through
  `/api/sessions/{sessionId}/messages/send-text`.
- OpenWA session data and API keys must live in a persistent `/app/data` volume;
  do not use a volume-reset troubleshooting path because it would remove the
  linked WhatsApp profile and credentials.
- Official first boot generates a cryptographically random admin API key and
  stores it at `/app/data/.api-key`; this avoids hard-coding a development key.
  A least-privilege session-scoped operator key can then be minted through
  `POST /api/auth/api-keys` for StringSense.
- OpenWA `v0.11.1` now runs healthy as `stringsense-openwa`, bound only to
  `127.0.0.1:2785`, with `stringsense_openwa_data` mounted at `/app/data`.
- The first boot key that appeared in startup output was rotated immediately.
  The orphan intermediate key and exposed default key are revoked; the persisted
  replacement admin key validates with HTTP 200 and the exposed key returns 401.
- Created a dedicated OpenWA session named `stringsense-fyp` with UUID
  `763e6069-c658-4510-8040-d358976f8162` and default auto-reconnect behavior.
- Created and validated a session-scoped operator key for the StringSense
  backend, enabled OpenWA in ignored `backend/.env`, and kept the env file at
  mode 600. The session started successfully and reached `qr_ready`.
- Pairing remains user-authorized: nine polls stayed at `qr_ready`; no connected
  state or real-phone receipt is claimed until the QR is scanned.
- Enabling OpenWA exposed an environment-dependent test isolation gap: the two
  Expo-specific tests enabled Expo but did not disable OpenWA. The minimal fix
  mirrors existing OpenWA tests by explicitly selecting only the provider under
  test; runtime code is unchanged.
- The focused notification module passes again: Ruff passed and all 10 tests
  passed with live OpenWA enabled in the local environment.
- The synchronized database contains all 12 approved cohort IDs, every one
  active, with gauges ranging from 0.63 mm to 0.70 mm. These are the system
  strings to report; the other retained rows are historical and hidden by the
  approved-cohort boundary.
- Docker Engine `29.3.1` is healthy. The retained
  `stringsence_stringsense_postgres_data` volume exists, and the stopped
  `stringsense-postgres` container is attached to it. Ports 2785 and 55432 were
  free before startup.
- PostgreSQL restarted healthy on port 55432 using the same named volume. The
  retained database is currently at `20260813_0029`; source head is
  `20260818_0032`, so three approved revisions remain to synchronize.
- The retained database contains 33 historical string rows and 24 rows marked
  active before migration. Runtime exposure must still be intersected with the
  approved 12-string cohort; `is_active` alone is not the system boundary.
- Revisions `0030` and `0032` add booking-free support and QR-proof schema.
  Revision `0031` only normalizes duplicated punctuation in catalog description
  text; it does not delete string rows or business records.
- Retained PostgreSQL synchronization completed successfully at
  `20260818_0032 (head)`. All 33 historical string rows and 24 active flags are
  preserved; `support_conversations`, `payments.proof_path`, and
  `store_settings.payment_qr_path` are present.
- The recommendation matrix remains populated with 537 rows across 33 retained
  catalog IDs; runtime still filters this history to the approved cohort.

## Cash payment option (2026-08-18)

- Cash can reuse the existing `payments.method`, `pending` status, admin review,
  and exactly-once wallet-credit path; no schema migration is needed.
- Only `qr_transfer` should require a configured QR and proof image. Cash must
  accept neither as a prerequisite and remains pending until shop confirmation.
- The smallest complete change touches the backend multipart method contract,
  mobile booking/top-up choices, payment-result copy, and focused commerce tests.
- Focused cash evidence confirms a booking cash request and top-up start pending
  without proof, wallet balance stays unchanged, and admin approval credits the
  top-up through the existing ledger exactly once.

## QR transfer and payment-proof planning (2026-08-17)

- The user selected a manual QR-transfer flow for both wallet top-up and booking
  payment: preview/download QR, transfer externally, upload screenshot, then wait
  for admin review.
- Admin must manage the active QR from Store Settings, including upload,
  preview, replacement, and deletion.
- Existing commerce behavior already provides pending admin decisions, locked
  terminal transitions, and exactly-once wallet credit; the change should extend
  those records instead of adding another ledger.
- Existing upload infrastructure already provides `expo-image-picker`,
  multipart requests, JPG/PNG/WEBP magic-byte validation, a 5 MB limit, UUID
  filenames, traversal protection, signed media URLs, and transaction-aware file
  cleanup.
- Current migration head was `20260817_0031`; the implementation revision is
  `20260818_0032_qr_payment_proofs.py`.
- The minimal contract stores one server-owned QR path on `store_settings` and
  one immutable proof path on each external `payment`.
- New writes should expose only the truthful `qr_transfer` method or
  `wallet_balance`. Historical Card/Online banking/E-wallet rows must remain
  unchanged because they have no screenshot and must not be misrepresented as
  evidence-backed QR transfers.
- The formal plan is
  `docs/plans/qr-payment-proof-plan-2026-08-17.md`.
- Store Settings mapping currently flows through `StoreSettingsRecord` and
  `settings_to_dto`; adding `payment_qr_path` there keeps public/admin reads
  consistent without bypassing the repository.
- Existing multipart client helpers send the bearer token and preserve the
  mobile/web file normalization path, so QR/proof uploads can reuse them.
- Current media storage only allows `booking-updates` and `string-images`; the
  QR/proof directories must be added to the same traversal-safe resolver before
  any new file can be served.
- Backend implementation now has proposed revision `20260818_0032`, QR/proof
  columns, the `qr_transfer` evidence check, signed `payment_qr_url` and
  `proof_url` fields, and multipart create routes.
- Mobile implementation now has a shared QR/proof panel, admin QR controls, and
  player/admin payment type/evidence fields; compile/type checks still remain.
- Implementation is complete at migration head `20260818_0032`; the dated
  acceptance record classifies local Chromium and physical Expo Go checks as
  `unverified` rather than passing them by inference.

## Full Page Review (2026-08-17)

- Review requested for every current page and its functional behavior.
- The review will use a newly enumerated route list rather than the older 46-page acceptance count.
- Dynamic pages will be exercised only after creating real isolated records for their route parameters.
- Current inventory contains 51 real renderable pages: 3 authentication, 30 player, and 18 administrator pages.
- Redirect-only routes are `/`, `/auth/welcome`, `/player`, and `/admin`; layout files and AppleDouble metadata are excluded from the page count but their role guards remain part of acceptance.
- The earlier 46-page record is stale because guided Agent, Admin AI, notification management, feedback operations, and other current surfaces have since changed the count.
- All local services were stopped at review start; the existing dirty worktree remains untouched except for review records and evidence.
- A fresh isolated PostgreSQL database was created and migrated through every revision to `20260813_0029`; retained demo data is not in scope for page mutations.
- The live fixture now contains: one configured player profile, two priced strings, one racket, one saved three-result recommendation run, an awaiting-dropoff booking with pending payment/support thread, a completed booking with feedback, an in-progress booking, a pending wallet top-up, and an in-app notification.
- The fixture was created entirely through authenticated public/admin APIs; no direct database rows were fabricated.
- Current Expo Web production export passed again with 3,676 modules. A task-owned SPA rewrite server now supports direct deep-link review of every route without changing the repository or user Expo cache.
- Backend health is OK with 108 imported recommendation rows.

### Authentication Pages

- `/auth/welcome` correctly redirects to `/auth/login`.
- `/auth/login` renders within 390x844 with phone, password, forgot-password, registration, and sign-in controls visible and accessible.
- Invalid login stays on the page and shows `Invalid credentials`; the accompanying 401 console resource error is expected for this negative test.
- `/auth/register` renders all required fields and blocks mismatched confirmation with inline `Passwords don't match` without making an API request.
- Navigating from login to registration produces a browser accessibility warning because a focused button remains inside an `aria-hidden` route container. Functionality continues, but this is a real minor accessibility defect in route transitions.
- `/auth/forgot-password` successfully requested a code, showed the controlled development preview, accepted the code and same compliant password, then returned to login with the phone identifier.
- Clicking forgot password from an empty login form passes `identifier=+60`, so the reset page starts with only the country code. This is harmless but slightly untidy UX.
- Production code delivery remains outside this page review; the tested preview behavior is intentionally development-only.

### Player Pages

- `/player/home` renders the authenticated player, unread indicator, quick actions, in-progress booking and next-step tracking correctly.
- `/player/strings` renders search, brand/filter controls, prices, pending-price labels and comparison actions. The API returned all 12 approved strings; the accessibility snapshot showed only the virtualized visible subset, not a missing-data response.
- `/player/recommend` correctly renders the saved profile, priorities, selected racket and generate/edit actions.
- `/player/results` initially showed its correct recoverable `No cached recommendations` state because later fixture feedback had invalidated the earlier cache. After the expected regeneration, it rendered three ranked results with booking, explanation and comparison actions.
- `/player/bookings` renders all three persisted bookings, correct two-active count, search/status filters and their distinct lifecycle states.
- `/player/chat` renders the persisted support thread, latest admin reply, `Admin Joined` state and quick prompts.
- Booking cards without a payment record display `Vendor quote` or `Price pending` even when the linked catalog item has a configured selling price. This is potentially confusing copy/data mapping, but it does not block booking detail or payment creation.
- `/player/profile` renders the persisted identity, three booking count, preferences, tension/frequency summary and account actions correctly.
- `/player/bookings/[id]` renders the owned awaiting-dropoff booking, lifecycle, quote confirmation, admin reply, payment state, check-in, support, cancellation and tracking actions correctly.
- Fresh store address is truthfully shown as `Not configured`; this is missing demo configuration, not a page failure.
- `/player/bookings/[id]/tracking` renders the current stage, next milestone and complete ordered timeline correctly.
- `/player/bookings/new` initially blocked continuation with no date chips because a fresh database intentionally seeds every business day as closed. After recording this safe default, the isolated admin schedule was opened so the actual slot-selection function can be tested.
- A clean FYP demo database therefore requires both store address and business-hour configuration before booking acceptance.
- With hours configured, `/player/bookings/new` loaded 14 date choices, live capacity, racket passport selection, tension controls, service method, price and an automatically selected available slot.
- Hard-refreshing the booking form briefly renders `String unavailable` before authenticated catalog hydration completes, then corrects itself after about one second. Normal in-app navigation is unaffected, but the transient false error is a minor deep-link loading-state defect.
- `/player/bookings/summary` rendered the complete draft and server-aligned pricing; `Confirm booking` created a real slot-backed booking and routed to its persisted detail page.
- `/player/chat/[id]` renders both player/admin messages, `Admin Joined` state, quick prompts and a disabled-until-text composer correctly.
- `/player/chatbot` renders the reduced guided-selection surface and direct human-support entry; a live DeepSeek request returned the first short playing-style question without raw Markdown markers or technical scoring text.
- `/player/check-in` generated a secure 10-minute QR token, displayed the expiry countdown and enabled refresh after the asynchronous request completed.
- `/player/feedback/[bookingId]` renders the persisted 5/5 feedback, all structured scores, comments, delayed durability placeholder and edit/back actions correctly.
- `/player/notifications` renders booking, recommendation, service, system and chat events from persisted backend state with clickable routes.
- `/player/notifications/preferences` renders all six categories; a system-category off/on cycle persisted through both API writes and restored the original enabled state.
- `/player/payments/[bookingId]` renders the server quote, four payment methods, wallet balance and correctly blocks duplicate submission when a pending payment already exists.
- `/player/payments/[bookingId]/result` correctly reports external-transfer verification pending and links to booking detail/tracking.

## FYP2 Completion Audit (2026-08-17)

- Audit started from current repository state; prior Agent simplification evidence remains relevant but will be revalidated where cheap.
- Initial hypothesis to test: payment and notification may not be the only remaining gaps; external delivery, runtime configuration, migrations, tests, and demo-critical flows must be checked separately.
- The worktree is heavily dirty and includes both prior completed changes and generated/untracked evidence; the audit must not equate uncommitted state with missing behavior, and must not overwrite unrelated work.
- Current high-level docs claim persisted payment/wallet, notification, support, racket, check-in, feedback, Agent, admin operations, and day-7/day-10 follow-up flows already exist.
- Current docs explicitly distinguish in-app notification persistence from configured WhatsApp delivery; the latter still requires live OpenWA configuration and real-phone proof.
- Existing FYP2 readiness documents and current code/tests must be cross-checked because older acceptance records may predate the Agent and notification changes.
- The July 24 acceptance record already proved internal payment and wallet flows end to end with PostgreSQL: server quote, pending payment/top-up, admin verification, paid state, and exactly-once wallet credit.
- The same acceptance proved persisted in-app notifications, category preferences, support chat, completed-service feedback, and all principal player/admin operational flows; it did not prove an external payment gateway or password-reset message delivery.
- Therefore “payment remains” is only true if the FYP requirement specifically demands a real gateway. The current manual-admin-verification payment design is implemented and previously browser-accepted.
- Historical acceptance covered 46 data-backed screens and zero unmatched mobile API paths at that snapshot, but current changes require fresh quality-gate reruns and targeted inspection of newly added Agent/OpenWA/follow-up behavior.
- The readiness record classifies all earlier P0-P3 engineering findings as resolved or intentionally preserved; it is historical and explicitly predates later FYP2 feature work.
- Current source contains real commerce endpoints and models: booking quotes, pending external-payment records, direct wallet payment, top-up records, admin verification, and append-only wallet transactions.
- Current source contains persisted notification delivery, in-app feed/read state/preferences, OpenWA delivery transport, and due feedback follow-ups. The follow-up code itself documents single-process deduplication as the deliberate FYP ceiling.
- No evidence yet shows a real external gateway webhook/redirect, real OpenWA phone receipt, or automatic password-reset code delivery. These are separate external boundaries, not one generic “payment and notification” item.
- The official NLP proposal is research-scoped and already records the completed MacBERT training/matrix path; future work such as human Gold evaluation and automatic retraining is explicitly excluded, so it is not a blocker for the bounded FYP2 system.
- The FYP1 source-of-truth excludes payment, wallet, notifications, racket passport, QR check-in, service queue, support chat, feedback, analytics, and Agent. Current FYP2 code/docs show these have since been added.
- Current route inventory covers authentication/security, profile/privacy, catalog/feedback, recommendation, booking/cancel/check-in/update, support conversation, payments/wallet, notifications/preferences, rackets/feedback, admin operations, analytics, and Agent.
- Test inventory is substantial: 142 backend test functions, 10 mobile policy tests, and 37 NLP tests. Passing status still needs a fresh run in the present dirty worktree.
- Hidden AppleDouble `._*` metadata files exist under mobile paths; they are not product functionality and have historically been intentionally preserved/ignored.
- Payment is not merely a placeholder: ownership checks, server-owned pricing, stale-quote conflict, one-active-payment behavior, row locking, sufficient-wallet validation, admin-only verification, and unique wallet transaction linkage are implemented.
- The local untracked backend environment currently has the DeepSeek Agent enabled, but OpenWA and Expo remote push are disabled. Thus current local runtime can exercise Agent calls but cannot deliver remote notifications.
- The backend starts an hourly feedback-follow-up loop inside FastAPI lifespan. This is suitable for a single-process FYP demo but not a multi-worker/production scheduler.
- Notification preferences, persisted delivery records, read tracking, and remote-provider validation exist. Settings reject enabling OpenWA and Expo push simultaneously and require OpenWA session/key when enabled.
- Password-reset rules are implemented, but delivery remains separate; the current audit has not established a configured code-delivery channel.
- Feedback follow-ups query completed bookings with no feedback, create a day-7 notification and one final day-10 reminder, deduplicate by user/title/route, obey notification preferences, and stop once feedback exists; a focused regression test covers this sequence.
- Mobile payment UI clearly labels card/online banking/external e-wallet as records awaiting shop verification, while wallet-balance payment is immediate after server balance checks. It does not falsely claim gateway processing.
- Player and admin payment/notification pages are wired to the centralized backend API layer; player booking detail exposes payment, check-in, support, tracking, and feedback entry points.
- Backend Agent tests cover active allowlists, short non-technical recommendation explanation, ownership, non-mutating what-if preview, in-stock alternatives, DeepSeek transport, auth/roles, and admin read-only behavior.
- Fresh validation so far: backend Ruff and format checks pass, Mypy passes for 213 source files, mobile lint and TypeScript pass, all 10 mobile policy tests pass, all 43 NLP tests pass, and `git diff --check` passes.
- Docker Compose currently reports no running services, so local PostgreSQL migration/runtime acceptance is not yet current; full backend tests are still running with two real-PostgreSQL concurrency tests expected to skip without an opt-in URL.
- Fresh full backend suite completed with 148 passed and 2 skipped; the only skips are the explicit real-PostgreSQL concurrency tests.
- Local PostgreSQL was then started successfully on port 55432 and reports ready, so migrations and the two skipped concurrency checks can now be validated against the real database.
- The existing local PostgreSQL database upgraded cleanly and `alembic current` equals the single head `20260813_0029`.
- The concurrency tests mutate shared store settings, so they will not be run against the retained local demo database. A uniquely named empty audit database was created instead to avoid corrupting user/demo state.
- A clean empty PostgreSQL database migrated through every revision from base to `20260813_0029` successfully.
- Both PostgreSQL-only concurrency tests passed: slot capacity stays bounded under concurrent booking creation, and concurrent password-reset/check-in requests retain only one active token.
- The task-created audit database was dropped after verification; the retained demo database was not used for destructive concurrency mutations.
- Expo Web production export passed with 3,676 modules using the current API base configuration.
- A separate browser-smoke database is being used for current runtime checks so player/admin acceptance actions do not pollute the retained demo database.
- Current live smoke stack is healthy: FastAPI startup completed against the fresh database, health reports 108 imported recommendation rows, and the exported Expo Web client is served at mobile width 390x844.
- Browser registration succeeded through the real API and routed a new player into the three-step persisted onboarding flow; the login/register/profile UI is usable and accessibility-visible at the target mobile viewport.
- The full three-step player profile onboarding saved successfully and redirected to the live player home. Home exposes notifications, recommendation, booking, catalog, AI, tools, and role-specific navigation without mock fallback.
- A real DeepSeek browser call succeeded. The reduced Agent showed one short playing-style question, did not show algorithm/evidence-status/source clutter, and kept the direct `Contact human support` button.
- The human-support button correctly routes to `/player/chat`, but the current support model is booking-scoped. A newly registered player with no eligible booking sees “No booking threads yet” and cannot actually start a general pre-booking human conversation. This is a genuine UX/requirement gap if “human access for every user” means support before a booking exists.
- Live notification UI loaded correctly, showed the empty state, exposed all six preference categories, persisted a service-category disable through navigation, and reflected it on reopening. This confirms the current App preference write/read path, not remote WhatsApp delivery.
- Player session restoration after a full root reload and logout both worked. Temporary admin credentials then authenticated and routed to the real admin dashboard with all 11 operational tools.
- A real DeepSeek admin-summary call succeeded and returned only a read-only current-operations summary with no write actions or raw Markdown asterisks.
- Admin notification composition intentionally derives recipients from bookings and registered device records. With a fresh player but no booking/device, the screen has no recipient chip; this is consistent with booking-centric shop communication but means arbitrary pre-booking broadcast is not supported.
- Fresh runtime API inspection found all 12 approved catalog items stocked but with `price_rm=null`. Therefore the payment engine is complete, but a brand-new database cannot quote or accept a booking payment until the admin configures at least the demo strings' selling prices. The retained historical acceptance database may already contain prices; fresh-install demo readiness does not.
- One attempted unauthenticated catalog read correctly returned 401; the authenticated retry succeeded. A shell-local variable expansion attempt also produced an empty bearer header and was replaced with a direct non-printing token substitution; no token value was printed.
- Admin inventory confirms all 12 fresh-database products are `price_pending`; this is configuration data, not a missing payment API.
- After assigning one temporary audit price in the isolated browser database, a player booking produced a server quote of RM30 and an online-banking payment record in `pending` state with the explicit “Awaiting shop verification” note. This verifies the intended internal payment boundary end to end.
- Admin Payments displayed the exact pending RM30 request, required irreversible-action confirmation, and persisted the final `paid` state without changing the booking workflow.
- Admin notification send respected the player's disabled `service` category: the in-app delivery record remained auditable as `disabled`, remote delivery was not attempted, and the provider message explained the preference.
- With an enabled `system` category but OpenWA disabled and no device token, the notification persisted while remote delivery was recorded as `failed` with “No active device token”. The admin copy labels this as WhatsApp failure even though OpenWA is disabled; this is a small status-copy/configuration mismatch, not data loss.
- After player re-login, the home unread indicator appeared and the in-app feed showed the enabled system update plus derived `Payment confirmed` and `Booking created` events. The disabled service follow-up was correctly absent.
- Current browser smoke finished with zero console errors/warnings and all observed API requests returning 200.
- OpenWA has no listener on port 2785, is not part of the repository Compose stack, and remains disabled/unconfigured in local env. Real WhatsApp delivery is therefore definitely not complete.
- No external payment gateway/webhook implementation is present; manual shop verification remains the intentional boundary.
- Password-reset code generation/reset exists, but no SMS or WhatsApp sender is implemented. The UI says delivery can be added later, so production-style forgot-password is incomplete even though controlled demo preview can work.
- Mobile release configuration lacks an iOS bundle identifier, Android application package, and configured EAS project ID. Expo Go/web demo can still run, but a distributable install build has not been configured or proven.
- Current JavaScript bundles export successfully for both iOS (4,196 modules) and Android (4,193 modules). This proves bundling, not installation, camera/notification permissions, or real-device behavior.

## Final FYP2 Classification

- Already complete and freshly validated: authentication/roles, profile/privacy, 12-string catalog, recommendation and saved explanations, guided player Agent, read-only Admin AI, booking and capacity controls, inventory, business hours/settings, check-in/service queue, booking support, racket records, structured feedback, analytics, internal payment/wallet ledger, in-app notifications/preferences, migrations, and offline NLP tests.
- Required before claiming the requested App + WhatsApp demo complete: configure and connect OpenWA, prove one real-phone receipt, and prove the day-7/day-10 follow-up path with configured delivery.
- Required before a clean-database payment demo: enter selling prices for the intended demo strings. The payment engine itself is complete.
- Decision needed: booking-scoped human support currently prevents a player with no booking from starting a human conversation. Accept this scope or add general support.
- Verification still missing: physical Expo Go/device smoke for camera QR and key player/admin flows. Native JS bundles pass, but no installed-device run was performed.
- External production boundaries, not automatically FYP blockers: real payment gateway/webhook, SMS/WhatsApp password-reset delivery, EAS/App Store build identifiers and project setup, multi-worker notification scheduler/queue.
- Security action: rotate the DeepSeek key previously pasted into chat, then update only the ignored backend environment.

- Current player allowlist contains 10 tools.
- FYP-active player capabilities need only exact-run context, string details, What-if preview, and in-stock alternatives.
- Current admin allowlist contains 5 tools; only the operations summary remains active.
- The mobile Admin Agent can currently execute three confirmed writes through existing APIs.
- The shared answer card currently shows sources and suggested questions; these are presentation extras, not required for the reduced FYP scope.
- Feedback follow-ups are deterministic notification automation, not DeepSeek Agent behavior, so they are outside this change.
- The exact recommendation surface preloads its owned run and string detail, so those readers do not need to remain model-callable.
- The reduced player model-call allowlist can be limited to string detail, What-if preview, and in-stock alternatives.
- A central action allowlist is required because handoff and payment-navigation actions can otherwise pass validation without a verified resource ID.
- Existing Agent tests exercise deferred store lookup and admin inventory writes; they must be rewritten to assert the new active allowlists while keeping implementation-level tests for preserved tools.
- The active model-call list is now three player tools and one admin summary tool; exact-run and string context still preload server-side for the explanation surface.
- Only `open_string` remains an active Agent action, which is required for verified replacement-string navigation.
- Mobile handlers for booking, handoff, admin navigation, and confirmed writes remain preserved but are unreachable from the reduced backend action allowlist.
- Guided selection must allow a no-tool first response while collecting its four answers; forcing a tool call only worked previously because the now-deferred preference tool was available.
- Browser evidence shows the player surface contains one starter, asks one playing-style question, and does not render source or suggested-question chips.
- Browser evidence shows the admin surface contains one summary starter and renders no navigation or write-action buttons.
- Page review: `/player/profile/edit` loaded the persisted display name and profile choices into a three-step editor. All three steps (identity, setup, six recommendation priorities) advanced normally; saving unchanged values returned to `/player/profile` with the correct persisted identity.
- Page review defect: `/player/rackets` reports the fixture racket as `0 lbs`, `No completed services yet`, and `0 services`, while `/player/rackets/88de6422-d69e-4d69-9bfe-745537aafde1` correctly shows one completed Kumpoo JS-63 service at 25 lbs plus 5/5 feedback. The list/detail summary is inconsistent and needs source tracing.
- Page review: the racket detail page itself renders identity, current setup, completed-service history, feedback, trends, and book/edit/delete actions correctly. Its console reported one warning that still needs inspection.
- Racket-summary root cause confirmed: `GET /api/rackets` returns only `RacketOut`, while the mobile mapper assigns an empty `serviceHistory` whenever `service_history` is absent. The list screen then derives tension/service count from that empty array. `GET /api/rackets/{id}` independently queries completed bookings and is therefore correct.
- The racket-detail warning is the same route-transition accessibility issue already seen elsewhere: the pressed list button retains focus inside a newly `aria-hidden` route ancestor. It is not page-specific business logic.
- Page review: `/player/rackets/new` loads the standard-model identity choices and optional specs correctly. Selecting a standard model hides the manual brand/model fields and accepts a complete temporary review record; persistence is being tested next.
- Racket create path passed: the page created `Temporary Review Racket`, navigated to its generated detail URL, and displayed the selected Yonex Arcsaber 11 Pro identity and specs. The empty service-history state is truthful.
- Racket edit mode opens inline on the detail page with every saved value prefilled and a dedicated save action.
- Racket update path passed: changing only the temporary record's nickname persisted immediately and returned to read mode with the new heading.
- Racket deletion correctly requires confirmation before mutating data; confirmation/persistence is being completed against only the temporary record.
- Page review defect: racket deletion is not functional on Expo Web. Clicking `Delete passport` invokes React Native `Alert.alert` with a destructive callback, but no actionable confirmation UI/dialog remains and no DELETE request is sent. The temporary record stays intact. Other multi-button `Alert.alert` confirmation flows must be checked for the same platform gap.
- Page review: the valid recommendation explanation route is `/player/recommend/explain/{catalogId}?runId={runId}`. An intentionally malformed run-id-as-path URL correctly renders `Explanation unavailable` and is not a product defect.
- Recommendation explanation passed on a newly generated run (`e93df854-1fea-4633-8306-8ad6cad9f886`): result ranking, 94% score, saved reasons, score breakdown, review support, trade-off, booking action, and verified string action all loaded. The automatic and follow-up DeepSeek answers were concise, grounded, contained neither algorithm terminology nor raw `**`, and the follow-up form successfully replaced the answer with the requested main trade-off.
- A stale/invalidated run still degrades to empty evidence while the Agent may answer from the supplied run context; this is an expected stale-link condition, not counted as a current-page failure after the real generated-link flow passed.
- Page review: `/player/settings` correctly loads account identity, password update, notification navigation, three privacy choices, deletion request, version, and logout. Anonymous-analytics was toggled Off then back On and both writes were reflected immediately, restoring the fixture.
- Settings password form enables only after both password fields are filled; a wrong-current-password rejection is being used to verify the failure path without changing credentials.
- Page review defect: submitting a wrong current password makes `POST /api/auth/change-password` correctly return 401, but the mobile global auth handling treats that domain validation response as an expired access token, clears the session, and redirects to `/auth/login`. Credentials remain unchanged, but the user should stay on Settings and see a password-specific error.
- Page review: `/player/strings/gosen-ryzonic-65` correctly renders catalog identity, specs, performance chart, tension fit, feedback/local-feedback empty states, booking, compare, and share actions. Minor data-copy defect: the generated description contains `resin..` (double period).
- String-detail `Compare` is a state-selection action rather than navigation and gives no text confirmation; the selected state will be verified by adding a second string and opening the compare page.
- Compare flow passed through the intended in-app path: catalog buttons changed to `Compared`, the floating `Shortlist Ready` tray appeared at two selections, and its Compare action opened `/player/strings/compare` without losing state. The page rendered both products, radar/metric comparison, specs, prices, booking-fit fallback, detail actions, and clear action. Clearing immediately returned the truthful “select at least two” state.
- A hard browser reload of `/player/strings/compare` loses the in-memory shortlist and shows the empty state. This matches the current non-persisted design; normal in-app flow is functional.
- Page review: `/player/tools` renders 10 role-appropriate destinations grouped into Play, Service, and Account. The Wallet action was clicked and routed correctly; the remaining destinations point to pages independently reviewed in this pass.
- Page review: `/player/wallet` correctly shows RM0 verified balance, RM25 pending verification from the fixture, lifetime top-up, the no-transaction state, top-up action, and checkout guidance.
- Page review: `/player/wallet/top-up` clearly explains shop verification, offers presets/custom amount and three external methods. A real RM20 request succeeded and returned to Wallet, where pending verification increased from RM25 to RM45 while verified balance stayed RM0.
- Page review defect: the UI-created booking's `Cancel booking` action has the same Expo Web multi-button `Alert.alert` failure as racket deletion. Clicking it sends no cancellation request and leaves the booking active, so Web users cannot complete cancellation from the visible action.
- Booking-scoped human handoff passed on the UI-created booking: `Message shop` created/opened `/player/chat/e875d9cf-922f-4956-8fb1-ad9ca07d3254`, showed Waiting Admin with an empty thread, and a real player message persisted and appeared with timestamp.
- Player logout and administrator authentication passed. `/admin/dashboard` reflects the isolated fixture (1 bench job, 2 awaiting), shows the actionable check-in prompt, searchable 11-tool workspace, role tabs, and read-only Admin AI entry.
- Page review: `/admin/bookings` correctly shows the four isolated bookings, counts/statuses, price states, next actions, filters, search, and navigation.
- Page review: `/admin/bookings/e875...` renders workflow gates, expected-completion controls, customer/contact/racket/string summary, feedback state, and service log. The player's newly sent chat message appeared immediately as a `Player note`, confirming cross-role persistence.
- Admin booking mutation passed: an admin note persisted with timestamp, the next-state selector enforced sequential workflow, the Web confirmation dialog was actionable, and accepting it changed ORD-E875D from Awaiting Dropoff to In Progress. This confirms not every Alert-style confirmation is broken; the failing player cancellation/racket deletion paths use a different handling path.
- Page review: `/admin/inventory` correctly reports 12 items, 1 low-stock item, 10 missing prices, 11 attention items, and exposes search/filter/sort plus stock/price/detail/note actions. Gosen and Kumpoo fixture price/stock states match player pages.
- Page review: `/admin/inventory/gosen-ryzonic-65` loads the full editable catalog, five performance scores, media controls, pricing mode, price, stock, availability, and shop notes with existing values. It also exposes the same source-data `resin..` double-period issue seen on the player detail.
- Admin inventory mutation passed and was restored: Gosen stock changed 8→9 via `PUT .../editor`, refreshed as Stock 9, then changed back to 8 and refreshed correctly. No fixture drift remains.
- Page review: `/admin/chat` correctly lists the new Waiting Admin thread and existing Admin Joined thread with filters, previews, and timestamps. `/admin/chat/e875...` shows player identity, booking/string context, persisted message, admin composer, and resolve/close actions.
- Admin chat mutations passed: sending a reply persisted it with `Admin / Shop admin`, automatically changed Waiting Admin to Admin Joined, and Resolve changed the thread to Resolved. This confirms the human-handoff operational path is present end to end for booking-scoped users.
- Page review: `/admin/analytics` matches fixture state: four weekly bookings, three pending payments, zero revenue, 5/5 feedback, the 26/25/27/22-lb distribution, Gosen 3 vs Kumpoo 1 demand, and Mon 7 PM busy slot.
- Page review: `/admin/assistant` exposes only the read-only operations-summary starter plus free-text summary prompt, with no write actions visible.
- Admin AI live call passed: DeepSeek returned a concise current-operations summary (1 completed, 2 in progress, 3 pending payments, 1 low-stock item) with no raw `**` and no navigation/write action controls.
- Page review: `/admin/business-hours` loads all seven open 09:00–21:00 schedules, 15:00–16:00 breaks, 30-minute slots, capacity 3, and special closed dates. A Monday capacity 3→4 save showed explicit success and was then restored 4→3 with a second successful save.
- Page review: `/admin/check-in` correctly shows one awaiting-today booking after the prior status update, order search, QR scan entry, next shortcut, matched player/racket/string/tension data, and three-item checklist. Submitting without checks was safely blocked with `Complete the counter checklist`, proving validation without mutating the booking.
- Page review: `/admin/feedback` correctly shows the one 5/5 completed-booking record, structured scores/comments, global versus exact-racket feedback evidence, filters, date range, refresh, and V11 read-only influence. `Export CSV` downloaded `stringsense-feedback.csv` successfully.
- Page review: `/admin/notifications` loads the fixture recipient, five categories, composer, delivery log, retry action, and previous failed remote delivery. A real system notification persisted in-app and appeared in the log; remote delivery truthfully failed with `No active device token`. The success banner still labels this specifically as `WhatsApp delivery: failed` even though OpenWA is disabled, matching the previously noted copy/config mismatch.
- Page review: `/admin/payments` correctly shows three pending requests (two top-ups and one booking payment), distinguishes wallet-credit versus booking-payment effects, and requires irreversible-action confirmation. Verifying the task-created RM20 top-up displayed an explicit confirmation, reduced pending count to two, marked it Paid, and is expected to credit the player wallet exactly once.
- Page review: `/admin/recommendations` lists all three saved runs with player/time/top result/result count and search. Latest `/admin/recommendations/e93d...` correctly preserves the request, resolved profile, exact three ranked rows, score components, rationale, feedback/CF audit fields, and racket context.
- The admin recommendation audit intentionally remains highly technical and displays algorithm/version names, internal UUIDs, hashes, and raw JSON. This does not leak onto the player explanation, but it would conflict if the earlier “do not mention algorithm” requirement was intended system-wide rather than player-facing only.
- Page review: `/admin/service-queue` correctly reflects one Awaiting and two In Progress jobs after the admin mutation, assigns lane-local queue positions, and keeps Ready empty.
- Page review: `/admin/settings` loads public store details, support/policy copy, RM0 service fee, five category templates, admin password, and homepage string selection. Fresh-install configuration gaps are visible: contact/address are `Not configured` and Trending Strings is 0/5.
- Admin store-settings no-change save passed and displayed explicit confirmation without altering fixture values.
- Cross-role persistence passed after fresh player login: Home now shows the admin-updated ORD-E875D as In Progress with the correct Gosen/22-lb next step, and the empty Trending Strings state matches admin 0/5 configuration.
- Cross-role wallet persistence passed: the admin-verified RM20 top-up appears as RM20 available/lifetime balance, leaves the unrelated RM25 request pending, and creates one +RM20 ledger entry with Online Banking provenance.
- Cross-role notification persistence passed: player feed contains the manual `Admin page review`, wallet verification, new shop reply, stringing-in-progress, and admin booking-note events.
- Cross-role chat persistence passed: player thread shows both messages, status Resolved, and composer is removed with `This conversation is closed for player replies.`
- Role guard passed in the player→admin direction: a logged-in player navigating directly to `/admin/dashboard` was replaced with `/player/home` and no admin data rendered.
- Confirmation root cause is source-confirmed: player booking cancellation and racket deletion call multi-button React Native `Alert.alert` directly on all platforms, whereas working admin booking/payment confirmations branch on `Platform.OS === 'web'` and use `globalThis.confirm` before the API call.
- Remaining route guards passed: unauthenticated `/player/wallet` redirects to `/auth/login`, and an administrator navigating to `/player/home` is replaced with `/admin/dashboard`.

## Current page-review conclusion

- All 51 renderable pages were reviewed at 390x844 with live backend data.
- 47 pages passed without a confirmed functional defect; four player pages contain the confirmed defects documented in `docs/page-review-2026-08-17.md`.
- All 18 admin pages passed their main operational flow.
- Final rerun passed: backend Ruff/format/Mypy, 148 backend tests with 2 normal-suite skips, 10 mobile tests, mobile lint/TypeScript, 43 NLP tests, and `git diff --check`.
- The two PostgreSQL-only tests had already passed separately against a disposable migrated database during this same audit.
- Screenshot evidence is preserved under `output/playwright/`; the isolated page-review database, temporary files, browser, backend, web server, and PostgreSQL service were removed/stopped.

## Follow-up fix evidence — 2026-08-17

- The booking-only human-support boundary is resolved with a separate general-support schema and API path. Browser smoke created a no-booking player thread, showed it in the admin queue, and persisted an admin reply back to the player.
- The four initial page-review defects were repaired: Web confirmation callbacks, wrong-password session handling, racket list summaries, and catalog/deep-link/copy issues.
- The authoritative catalog audit is recorded in `docs/catalog-data-audit-2026-08-17.md`; product metadata exists, but source-backed official performance ratings are not populated.
