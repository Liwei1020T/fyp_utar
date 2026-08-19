# Customer and Administrator Acceptance Record

Date: 2026-07-24
Environment: Expo Web -> unified FastAPI backend -> local PostgreSQL
Responsive smoke viewport: 390 x 844

## Result

The customer and administrator runtimes contain no page-level mock business
data. Every authenticated page reads its business records from the unified API
or from backend-derived persisted state, and every exercised write was
confirmed again after a reload.

For this review, **mock data** means a customer, booking, payment, wallet
balance, notification, conversation, racket, inventory record, analytics
number, recommendation result, or store setting that is hard-coded or locally
seeded inside the mobile runtime instead of being returned by the backend.

The following are not classified as mock business data:

- input placeholders, filter options, status labels, and empty/loading states;
- transient form drafts and compare selections that are not business records;
- catalog and store defaults that the backend imports into PostgreSQL;
- retained local acceptance records created through real API calls.

## Page Inventory

| Surface | Real UI pages | Notes |
| --- | ---: | --- |
| Shared authentication | 4 | Welcome, login, registration, and password reset |
| Customer | 27 | Home, catalog, recommendation, booking, payment, wallet, notification, chat, racket, feedback, profile, and tracking flows |
| Administrator | 15 | Dashboard, bookings, check-in, queue, payments, chat, inventory, business hours, settings, analytics, and recommendation audit |
| **Total** | **46** | Layout files and redirect-only routes are not counted |

`/player` redirects to `/player/home`, `/admin` redirects to
`/admin/dashboard`, and `/player/chatbot` is a compatibility redirect to
`/player/chat`. These routes do not render separate data pages.

## Runtime Data Audit

- `mobile/mocks/` has no runtime source files and
  `mobile/services/mockAppService.ts` is removed.
- `mobile/store/appStore.ts` initializes business collections empty. It stores
  authenticated API snapshots plus transient drafts/selections, not seeded
  customers, orders, payments, chats, inventory, analytics, or notifications.
- Fresh backend databases no longer seed the legacy `Apex String Lab` identity,
  fabricated contact/address, or a fixed expired special-closure date.
  Unconfigured contact/address fields are explicit, while product/store
  configuration remains editable through the administrator API.
- Runtime pages and components have no import from the removed mock session.
- The only remaining mock-like search matches in mobile runtime source are UI
  `placeholder` props and example input hints.
- No screen or store performs a local-only business success when an API request
  fails.
- All direct backend requests are owned by `mobile/services/backendApi.ts`;
  route pages and components do not maintain a second API or local-data path.
- The service contains 62 unique frontend API path templates. All 62 match the
  current live OpenAPI contract, which exposes 71 paths.

## Customer Browser Coverage

| Area | Acceptance evidence | Result |
| --- | --- | --- |
| Authentication | Registered a new player, verified duplicate-phone rejection, logged in, restored the session, checked role guards, and logged out. | Pass |
| Profile | Saved the onboarding profile, reloaded it, edited player data, and confirmed persisted profile-derived summaries. | Pass |
| Recommendation | Generated a ranked recommendation, opened an explanation, and recovered the cached result after a hard reload/deep link. | Pass |
| String catalog | Loaded the live catalog, opened detail pages, and completed an in-app two-string comparison. | Pass |
| Racket Passport | Created and edited an owned racket, then reloaded it. After service completion, the racket showed the persisted string, tension, service history, and feedback. | Pass |
| Booking and check-in | Created a real slot-backed booking, opened summary/detail/tracking, and displayed its backend-generated check-in reference. | Pass |
| Payment | Loaded a server quote, created a pending online-banking ledger request, and later observed the administrator-verified `paid` result. | Pass |
| Wallet | Requested a RM20 top-up, observed pending verification, and later observed a persisted RM20 balance and verified transaction. | Pass |
| Support chat | Created a booking support thread, sent a player message, and later observed the persisted administrator reply and closed state. | Pass |
| Notifications | Loaded backend-derived booking, payment, wallet, chat, and recommendation events; marked one read and persisted preference changes. | Pass |
| Tracking and feedback | Observed every service milestone through `completed`, submitted one 5/5 feedback record, and recovered it after reload. | Pass |

## Administrator Browser Coverage

| Area | Acceptance evidence | Result |
| --- | --- | --- |
| Authentication and guard | Logged in through the admin role, deep-linked while authenticated, logged out, and confirmed unauthenticated admin access redirects to authentication. | Pass |
| Dashboard and analytics | Loaded persisted operational counts, revenue, payment workload, popular strings, and busy slots; counts changed after the reviewed booking advanced. | Pass |
| Bookings and check-in | Searched the reviewed order, inspected its exact player/racket/string data, persisted an admin note, completed the counter checklist, and checked it in. | Pass |
| Service lifecycle | Moved the booking through `awaiting_dropoff -> in_progress -> ready_for_collection -> completed`; terminal-state editing was then locked. | Pass |
| Service queue | Confirmed the booking appeared in the correct active queue lane after check-in. | Pass |
| Payments | Verified the booking payment and wallet top-up; reload showed both paid and no pending requests. | Pass |
| Support chat | Replied, resolved, closed, and reloaded the same persisted conversation. | Pass |
| Inventory | Loaded 33 persisted items, exercised search/filtering, changed stock 8 -> 9, reloaded, restored 8, and reloaded again. | Pass |
| Business hours | Changed Monday capacity 3 -> 4, reloaded, restored 3, and reloaded again. The two expired local acceptance closed dates were then cleared through the administrator API and the empty value survived reload. | Pass |
| Store settings | Changed the persisted address, reloaded it, restored `Utar Kampar`, and reloaded again. | Pass |
| Recommendation audit | Opened the newly generated player run and inspected its saved request, profile snapshot, matrix/algorithm versions, ranked scores, evidence, and rationales. | Pass |

Both customer home and administrator dashboard were rechecked at 390 x 844.
Neither produced horizontal document overflow. Browser acceptance reported zero
application errors. Expo Web emitted the dependency-level
`props.pointerEvents` deprecation warning; it did not affect a route, request,
or interaction.

## Cross-Role Persistence Proof

The reviewed order, `ORD-CF951`, was intentionally left completed as acceptance
evidence:

- its RM40 booking payment is paid;
- its RM20 wallet top-up is paid and credited once;
- its check-in and full service timeline are persisted;
- its support conversation contains both roles and is closed;
- its 5/5 service feedback is persisted;
- its saved racket now contains the completed service history.

The local PostgreSQL database also retains earlier acceptance/test records from
previous runs. Those rows are real database records created through the API,
not frontend mock data. They were not deleted because this review did not
authorize destructive cleanup. A clean demo dataset should use a separate
fresh database or an explicitly approved cleanup task.

Two expired special-closure settings (`2026-04-14` and `2026-04-21`) were not
business records and were safely cleared from the current store schedule. The
configured store identity/contact/address and all acceptance transactions were
left intact.

## Repository Quality Gates

- Backend Ruff and Ruff format checks passed (`219 files already formatted`).
- Backend Mypy passed for 193 source files.
- The complete backend suite ran with the real-PostgreSQL concurrency URL
  enabled and reported `66 passed`.
- Alembic current and heads both report the single PostgreSQL head
  `20260723_0024`.
- Mobile TypeScript and Expo lint with `--max-warnings=0` passed under the
  project-pinned Node 24 runtime.
- Expo Web production export passed with 3,613 modules.
- `git diff --check` passed.
- The live OpenAPI comparison reported 71 backend paths, 62 frontend path
  templates, and zero unmatched frontend paths.

## Deliberate External Boundaries

### External payments

The application has a real internal quote, payment, wallet, and verification
ledger. Card, online-banking, and external e-wallet requests intentionally
remain pending until the administrator verifies receipt. No external payment
gateway is claimed. A future provider redirect/webhook must replace this manual
verification step for that provider.

### Password-reset delivery

The request-code and reset APIs, expiry, attempt limit, single-use code, and
password update are implemented and tested. However, no SMS or WhatsApp
delivery provider is configured. With
`PASSWORD_RESET_DEV_PREVIEW_ENABLED=false`, a real user cannot automatically
receive the generated code. This is an external integration boundary, not mock
page data, and must not be described as a completed production delivery flow
until a provider and credentials are selected.

## Final Classification

- Page-level hard-coded/sample business data: **none found**
- Customer/admin page-to-API coverage: **complete for the current 46 UI pages**
- Frontend API paths missing from live OpenAPI: **0**
- External payment provider integration: **not selected; manual verification is intentional**
- Password-reset code delivery provider: **not integrated**
