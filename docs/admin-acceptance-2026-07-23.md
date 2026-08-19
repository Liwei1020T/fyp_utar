# Administrator Acceptance Record

Date: 2026-07-23
Environment: Expo Web -> unified FastAPI backend -> local PostgreSQL
Viewport: 390 x 844

## Result

All administrator route pages loaded from the real backend, and every
administrator mutation exercised in the browser persisted after a page reload.
No runtime mock session or local business-data fallback was involved.

The browser reported zero application errors. Expo Web emitted one
dependency-level warning that `props.pointerEvents` is deprecated; it did not
break a route, request, or interaction.

## Browser Coverage

| Area | Browser acceptance | Persisted API boundary | Result |
| --- | --- | --- | --- |
| Authentication and route guard | Logged in through the admin role selector, reloaded and deep-linked while authenticated, then logged out and confirmed current-tab storage was empty; prior player-role probe was redirected away from admin routes. | `POST /api/auth/login`, `GET /api/auth/me` | Pass |
| Dashboard | Loaded live booking, queue, inventory, payment, and conversation summaries; refreshed counts after the audit booking completed. | Admin booking, inventory, payment, and conversation reads | Pass |
| Booking list | Loaded the full queue, filtered by order ID, and opened a real booking. | `GET /api/admin/bookings` | Pass |
| Booking detail | Added service notes and a racket photo, reloaded, and confirmed both in the service log. | `GET /api/admin/bookings/{id}`, `POST /api/admin/bookings/{id}/updates` | Pass |
| Booking lifecycle | Moved the audit booking through `awaiting_dropoff -> in_progress -> ready_for_collection -> completed`; terminal-state editing was then disabled. | `PATCH /api/admin/bookings/{id}/status` | Pass |
| Counter check-in | Looked up the audit order, completed the player/racket/setup checklist, and confirmed drop-off. | `GET /api/admin/check-in/lookup`, `POST /api/admin/check-in` | Pass |
| Service queue | Confirmed the audit order moved into the correct queue lane after its persisted status change. | `GET /api/admin/service-queue` | Pass |
| Payments | Verified one booking payment and one wallet top-up; reload showed both paid and no pending requests. | `GET /api/admin/payments`, `PATCH /api/admin/payments/{id}` | Pass |
| Support conversations | Opened the real support thread, sent an admin reply, resolved it, closed it, and reloaded the closed state. | Admin conversation read/message/read/resolve/close endpoints | Pass |
| Inventory list | Loaded 33 live items, searched/filtered the workbench, and confirmed `Price Missing` returned the one price-pending item. | `GET /api/admin/inventory/strings` | Pass |
| Inventory detail | Changed stock from 8 to 9, saved and reloaded, then restored and reloaded stock 8. | `GET /api/admin/inventory/strings/{id}`, `PUT /api/admin/inventory/strings/{id}/editor` | Pass |
| Inventory media | Uploaded an image to a no-photo item, saved and reloaded it, then removed it and confirmed the original no-photo state. | `POST /api/admin/strings/{id}/image`, `DELETE /api/admin/strings/{id}/image` | Pass |
| Business hours | Changed Monday capacity from 3 to 4, saved and reloaded, then restored and reloaded capacity 3. | `GET /api/admin/business-hours`, `PUT /api/admin/business-hours` | Pass |
| Store settings | Appended an acceptance marker to support text, saved and reloaded, then restored and reloaded the original text; five persisted trending strings also loaded. | `GET /api/admin/store-settings`, `PUT /api/admin/store-settings` | Pass |
| Analytics | Loaded persisted weekly bookings, payment workload, revenue, popular strings, and busy slots. | `GET /api/admin/analytics/summary`, `GET /api/admin/analytics/popular-strings` | Pass |
| Recommendation audit | Loaded saved runs, opened a run, and reviewed request/profile snapshots, algorithm and matrix versions, ranked scores, evidence counts, and rationales. | `GET /api/admin/recommendations/runs`, `GET /api/admin/recommendations/runs/{run_id}` | Pass |

## Acceptance Data and Restoration

The browser used a dedicated local acceptance booking, `ORD-C8111`.

- The booking is intentionally left `completed` after proving the full service
  lifecycle.
- Its booking payment and the associated acceptance wallet top-up are
  intentionally left `paid` after admin verification.
- Its support conversation is intentionally left `closed`.
- Acceptance notes, the admin reply, and the uploaded booking-update photo are
  retained as audit evidence.
- Inventory stock was restored to 8.
- The temporary catalog image was removed and the item returned to its original
  no-photo state.
- Monday capacity was restored to 3.
- Store support text was restored exactly.

Admin seeding remained operator-controlled. The acceptance backend used valid
process-only `SEED_ADMIN_*` values; no credential was added to the mobile app,
documentation, or committed environment files.

## Repository Quality Gates

Fresh checks after the browser acceptance:

- Backend Ruff and Ruff format checks passed (`219 files already formatted`).
- Backend Mypy passed for 193 source files.
- Backend Pytest collected 66 tests: `65 passed, 1 skipped`. The skipped test is
  the opt-in real-PostgreSQL concurrency test because
  `POSTGRES_TEST_DATABASE_URL` was not set for this run.
- Alembic current and heads both reported the single PostgreSQL head
  `20260723_0024`.
- Mobile used Node `24.18.0`; TypeScript and Expo lint with
  `--max-warnings=0` passed.
- Expo Web production export passed with 3,613 modules.
- `git diff --check` passed.
- All local Markdown links resolved, and all 71 live OpenAPI paths are present
  in the current backend/API appendix documentation.
- Runtime source scan found no `mock`, `fake`, `stub`, `frontend-only`,
  `local-only success`, or `quick demo` marker in the mobile/backend runtime
  source directories.

## External Payment Boundary

This acceptance proves the internal payment ledger and admin verification
workflow. It does not claim that StringSense talks to a card, online-banking, or
external e-wallet provider. Those methods remain pending until manual shop
verification unless a future provider redirect/webhook replaces that boundary.
