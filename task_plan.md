# Agent Scope Simplification Plan

## Goal

Keep only the FYP-focused Agent scope while preserving completed code for later re-enablement.

## Active Scope

- Player guided string selection.
- Player comparison of two or three approved strings.
- Exact recommendation explanation.
- Verified in-stock alternatives.
- Live customer-facing store information.
- Admin read-only operations summary plus booking and inventory queries.

## Deferred Scope

- Player review Q&A, booking queries, saved/latest recommendation queries, and Agent-created handoff.
- Admin payment and support searches.
- Admin booking, inventory, and support write proposals.
- Source chips and suggested-question chips in the Agent answer card.

Deferred implementations remain in the repository and are disabled at their registration or UI exposure points with re-enable comments.

## Phases

### Phase 1 — Agent registration audit

**Status:** complete

### Phase 2 — Backend Agent simplification

**Status:** complete

### Phase 3 — Mobile Agent simplification

**Status:** complete

### Phase 4 — Agent documentation

**Status:** complete

### Phase 5 — Agent validation

**Status:** complete

### Phase 6 — Complete FYP2 delivery audit

**Status:** complete

### Phase 7 — Fresh validation and acceptance

**Status:** complete

### Phase 8 — Final completion classification

**Status:** complete

### Phase 9 — Current page inventory and isolated acceptance fixture

**Status:** complete

### Phase 10 — Authentication and player page-by-page acceptance

**Status:** complete

### Phase 11 — Admin page-by-page acceptance

**Status:** complete

### Phase 12 — Cross-role mutations, failure states, and persistence

**Status:** complete

### Phase 13 — Fresh quality gates and final page matrix

**Status:** complete

### Phase 14 — General human-support conversation scope

**Status:** complete

### Phase 15 — Repair confirmed page-review defects and copy issues

**Status:** complete

### Phase 16 — Verify official string data and schema/runtime provenance

**Status:** complete

### Phase 17 — Full regression, browser acceptance, and handoff

**Status:** complete

### Phase 18 — QR transfer and payment-proof implementation plan

**Status:** complete

### Phase 19 — QR transfer and payment-proof implementation

**Status:** complete

### Phase 20 — Cash payment option

**Status:** complete

### Phase 21 — WhatsApp live delivery and database synchronization

**Status:** in_progress

### Phase 22 — Current system string inventory

**Status:** complete

### Phase 23 — Archive non-approved runtime strings

**Status:** complete

### Phase 24 — Restrict active runtime database to approved cohort

**Status:** complete

### Phase 25 — Clarify password delivery, service fee, and commit handoff

**Status:** complete

### Phase 26 — Deliver password-reset codes through WhatsApp

**Status:** complete

### Phase 27 — Re-enable string comparison and complete Agent validation

**Status:** complete

## Decisions

- Keep the admin Agent read-only; allow booking and inventory queries while all
  admin Agent writes remain disabled.
- Re-enable player string comparison using the preserved backend tool without
  adding a new RAG service or changing V11 ranking ownership.
- Leave day-7/day-10 notification automation unchanged because it is not an Agent capability.
- Preserve authentication, ownership checks, output validation, rate limiting, and evidence grounding.
- Treat manual admin payment verification as the completed FYP payment design; a real gateway is an optional external integration unless the assessment explicitly requires it.
- Treat in-app notification delivery as complete and real WhatsApp receipt as incomplete until OpenWA is configured and verified on a phone.
- Treat fresh-database price setup, physical-phone smoke, and the booking-only human-support boundary as demo-readiness items that must be resolved or explicitly accepted.
- Use one isolated PostgreSQL database for the full page review; never mutate the retained demo database.
- Review only real renderable pages. Layout files, AppleDouble metadata, and redirect-only index routes are inventoried separately and are not counted as data pages.
- Report defects without changing product behavior unless the user separately asks for fixes.
- Keep booking-linked support and booking-free support as separate persisted
  records; reuse one general thread per player and route both through the same
  player/admin chat UI.
- Treat catalog source URLs and official-performance evidence as separate
  provenance layers; do not promote seeded feel values to official ratings.
- Keep manual admin verification as the payment owner. Replace placeholder
  external methods with one QR-transfer path and attach immutable evidence to
  the existing payment record rather than creating a second ledger.
- Let Admin Settings upload, preview, replace, and delete the active payment QR;
  never seed or fabricate one.
- Require explicit approval before migration `20260818_0032` or any runtime
  implementation begins. Approval was received on 2026-08-18.
- Reuse the existing pending/admin-review ledger for cash booking payments and
  wallet top-ups. Cash needs no QR or screenshot, and wallet credit remains
  blocked until admin approval.
- Reuse the existing OpenWA notification provider and persisted-first delivery
  contract; do not add Expo Push or a second WhatsApp integration.
- Upgrade the retained PostgreSQL database through the existing Alembic chain
  without resetting its volume, then list the approved runtime string cohort
  from the synchronized database.
- Preserve the original 33-string source and protected NLP artifacts, create a
  verified versioned PostgreSQL backup, then use existing active/availability
  fields to archive non-approved runtime strings without breaking history.
- Do not prune any non-approved row that is referenced by user/business history
  until the dependency is understood and included in the recovery design.
- Commit only the scoped notification-test isolation, catalog-archive evidence,
  and planning records; exclude secrets, private backups, generated Graphify,
  Playwright state, and output artifacts.
- Password-reset requests must keep a generic response for unknown accounts and
  provider failures, persist the code before provider I/O, never log or expose
  the code outside development preview, and use the existing session-scoped
  OpenWA configuration.

## Errors Encountered

| Error | Attempt | Resolution |
|---|---:|---|
| First live comparison returned no data for existing BG80/BG65 rows | 1 | Identified a display-name versus catalog-ID tool contract mismatch; resolve identifiers at the shared comparison boundary. |
| Isolated SQLite catalog query guessed `strings.id` | 1 | Schema inspection showed the real primary key is `catalog_id`; the corrected read confirmed both requested strings exist. |
| First Phase 27 live-findings patch had an invalid hunk separator | 1 | No files changed; reapplied the same notes with valid file-scoped hunks. |
| Inventory-test search used unmatched zsh globs | 1 | No files changed; use explicit files or `rg --glob` for the next lookup. |
| Static server returned 404 for direct `/player/chatbot` deep link | 1 | Re-entered through the production SPA root and used the real Home Ask AI navigation path; the route then loaded and passed. |
| Phase 27 planning patch assumed `findings.md` was titled `Findings` | 1 | The patch was rejected atomically; reread the exact heading and split the planning updates. |
| `react/no-unescaped-entities` on the Admin AI heading | 1 | Escaped the JSX apostrophe and reran mobile validation. |
| Browser acceptance backend could not connect to PostgreSQL on port 55432 | 1 | Start the repository `postgres` service, verify health, then retry the backend. |
| Docker Desktop opened but its engine/socket remained unavailable | 2 | Use an isolated temporary SQLite database for UI acceptance without touching project data. |
| Admin Dashboard still described confirmed Agent actions | 1 | Updated the entry copy to describe the active read-only summary. |
| Playwright wrapper hit a root-owned user npm cache temp entry | 1 | Use an isolated npm cache under `/private/tmp` for remaining browser commands. |
| Fresh Playwright daemon could not write the macOS `ms-playwright` cache | 2 | Stop retrying global cache access; verify the final copy in the successful static export plus lint and TypeScript. |
| Docker Desktop quit request did not return | 1 | Stopped the waiting AppleScript; all task-owned backend and web-server processes were stopped. |
| Authenticated audit catalog read initially returned 401 | 1 | Reused the temporary player's bearer token without printing it; authenticated read returned 12 items. |
| Shell-local token assignment expanded before the curl header | 1 | Used direct command substitution from the task-owned temporary login response; token remained out of tool output. |
| Planning completion checker reported `8/0` because the older inline phase format lacked supported headings | 1 | Converted the plan to the skill's supported phase-heading and status format. |
| Expo Web dev server could not write the user-level `.expo/native-modules-cache` | 1 | Use the already validated production export and a task-owned stdlib SPA-rewrite server for direct route acceptance. |
| Mobile test command `npm run test:run` did not exist | 1 | Read `package.json` and ran the repository-defined `npm test`; all 10 tests passed. |
| Initial QR backend batch patch did not match the current upload-storage context | 1 | Split the backend changes into smaller file-scoped patches after rereading the exact function bodies. |
| Mobile type patch used one incorrect workspace path | 1 | No files changed; rerun the same patch with the verified `/Volumes/TLW/Utar/FYP/UI/StringSence` root. |
| Admin Settings QR patch included a stale context line | 1 | No files changed; split imports/state/handlers/render edits into smaller patches. |
| Alembic migration smoke loaded a null-byte AppleDouble sidecar for the new revision | 1 | Identified `._20260818_0032_qr_payment_proofs.py` as task-created metadata; remove only that sidecar and retry. |
| Targeted pytest selector referenced a non-existent notification test name | 1 | No tests ran; rerun the complete notification module and the actual unified-flow selector. |
| Documentation batch patch used a stale API-contract context | 1 | No documentation files changed; patch each contract section against the exact current text. |
| Playwright smoke could not launch because the local Chromium executable is not installed | 1 | Static Expo export passed; leave browser smoke `unverified` rather than downloading a browser during this task. |
| Alembic heads was invoked from the repository root without backend config | 1 | The root command failed with missing `script_location`; the earlier backend-directory check already confirmed `20260818_0032 (head)`. |
| Initial fixture recommendation cache was invalidated by later feedback creation | 1 | Regenerated the player's recommendation after all feedback writes; this is expected cache invalidation, not a page defect. |
| Phase 21 planning patch assumed the wrong `findings.md` title | 1 | The patch was rejected atomically; reread the file headings and split the update against exact context. |
| Pre-upgrade string detail SQL used stale `brand` and `model` columns | 1 | The count query succeeded and the detail query was read-only; inspected the ORM and switched to `brand_code`, `model_name`, and `display_name`. |
| Migration inspection used an incorrect guessed filename for revision `0031` | 1 | No mutation occurred; located the revision by ID and read `20260817_0031_clean_catalog_descriptions.py`. |
| Initial OpenWA `docker run` did not finish pulling within the 30-second tool window | 1 | No container or complete image exists; split image pull from container creation and keep the returned Docker session ID for polling. |
| Process inspection with `ps` was denied by the macOS sandbox | 1 | Docker state checks were sufficient; do not treat the denied process query as evidence about the pull. |
| Second OpenWA container creation raced with the first pull/run and hit a name conflict | 1 | Preserved the already-created target container; it was healthy and attached to the intended persistent volume. |
| First admin-key rotation validated a POST-only endpoint with GET and exited after creating an orphan key | 1 | Inspected OpenAPI, revoked the orphan, created a fresh admin key, validated with POST, replaced the persisted key file, and revoked the exposed default key. |
| WhatsApp session poll used zsh read-only variable `status` | 1 | The command stopped before changing state; renamed it to `session_state` and resumed polling. |
| Notification tests inherited live `OPENWA_ENABLED=true` and routed an Expo test to OpenWA | 1 | Made both Expo-specific tests explicitly disable OpenWA, matching the existing OpenWA tests that explicitly disable Expo. |
| Initial non-approved dependency count assumed `bookings.catalog_id` | 1 | The read-only query failed without mutation; introspection showed the real column is `bookings.string_id`, so counts will use actual constraints and table columns. |
| Revised dependency count included nonexistent `recommendation_logs.catalog_id` | 1 | ORM inspection confirmed catalog IDs live in `recommendation_run_items`, not the legacy JSON log table; removed that union branch before retrying. |
| Scoped `git add` could not create `.git/index.lock` under the read-only sandbox | 1 | No files were staged; retry the same five explicit paths with authorized Git index access. |
