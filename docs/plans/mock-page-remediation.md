# Mock Page Remediation

## Definition

In this record, mock data means customer, booking, payment, wallet,
notification, conversation, racket, inventory, analytics, recommendation, or
store data that a mobile page hard-codes or seeds locally instead of loading
from the backend.

Input placeholders, UI option lists, transient form drafts, and records already
persisted in the local acceptance database are not page-level mock business
data.

## Audit Result

The mobile app contained **17 actual mock-first UI pages**:

- Player: 12 pages
- Admin: 5 pages

`/player/chatbot` is an additional compatibility route that redirects to
`/player/chat`; it is not a separate UI page.

## Resolved Pages

| Domain | Pages | Live source |
| --- | ---: | --- |
| Booking support chat | 4 | Persisted per-booking conversation state, messages, and read timestamps |
| Payment and wallet | 5 | Server quote, persisted payment records, admin verification, and wallet ledger |
| Notifications | 2 | Owned backend events, persisted read IDs, and applied preferences |
| Racket Passport | 2 | Stable physical racket records and completed linked service history |
| Player check-in | 1 | Deterministic check-in reference returned by the booking API |
| Player feedback | 1 | One structured feedback record per completed booking |
| Admin analytics and service queue | 2 | Persisted payment analytics and backend queue ordering |
| **Total** | **17** | |

The route guards that previously redirected these pages have been removed.
Backend sessions fail closed on API errors and do not fall back to mock
records.

## Runtime Mock Removal

The explicit local mock session has also been removed:

- `mobile/mocks/` contains no source files, and
  `mobile/services/mockAppService.ts` no longer exists.
- `store/appStore.ts` contains only authenticated backend sessions, API
  response snapshots, and transient UI drafts/selections.
- Route pages do not import `MOCK_*`, perform local business writes, or report
  success before the backend confirms a mutation.
- Missing/expired tokens and failed API calls fail closed with a retry or
  sign-in message.

## Verification Evidence

Verified again on 2026-07-24:

- Runtime source scan found no `mock`, `fake`, `demo`, `stub`, local-workspace,
  or frontend-only business fallback in `mobile/app`, `mobile/components`,
  `mobile/services`, `mobile/store`, or `backend/app`.
- `mobile/mocks/` has no files and `mobile/services/mockAppService.ts` is
  removed.
- Fresh backend initialization no longer writes the legacy `Apex String Lab`
  identity, fabricated contact/address, or a fixed expired special-closure
  date. Unknown contact/address values are explicit unconfigured states.
- Mobile passes `npx tsc --noEmit`, zero-warning Expo lint, and a production
  Web export.
- Backend passes Ruff, format check, and Mypy. The complete suite ran with the
  real-PostgreSQL concurrency URL enabled and reported 66 passed.
- Local PostgreSQL is at the single Alembic head `20260723_0024`.
- The app has 46 real UI pages: 4 shared authentication pages, 27 customer
  pages, and 15 administrator pages. Redirect-only compatibility routes are not
  counted as pages.
- Live OpenAPI exposes 71 paths. All 62 unique path templates used by
  `mobile/services/backendApi.ts` match that contract; zero frontend API paths
  are unmatched.
- Browser acceptance created real player records and exercised profile save
  and refresh recovery, catalog and slots, booking and payment requests,
  booking support chat, check-in reference, notification preferences, racket
  create/update, wallet top-up, notifications, recommendation generation, and
  cached-result deep links. All observed API requests completed successfully
  and the browser reported zero application errors.
- A second, full administrator browser acceptance used valid process-only seed
  settings and covered login/session restoration, dashboard, booking
  search/detail, complete booking lifecycle, notes and photo upload, check-in,
  service queue, payment verification, support reply/resolve/close, inventory
  filtering/edit/media upload/remove, business hours, store settings,
  analytics, and recommendation run list/detail.
- Administrator writes were reloaded from PostgreSQL. Reversible inventory,
  media, business-hours, and settings probes were restored to their original
  values. The dedicated audit order was intentionally completed and its audit
  evidence retained.
- Final administrator requests returned successful responses and the browser
  reported zero application errors. The only remaining console message is the
  Expo Web dependency warning that `props.pointerEvents` is deprecated.
- The same reviewed order was then reopened as the customer. Its verified
  payment, credited wallet balance, administrator chat reply, notifications,
  completed timeline, submitted feedback, and racket service history all
  survived reloads.
- Customer home and administrator dashboard were rechecked at 390 x 844 with
  no horizontal document overflow.
- The current store schedule's two expired local acceptance closed dates were
  cleared through the administrator API and the empty value survived reload.

Admin account seeding remains operator-controlled and requires valid
`SEED_ADMIN_*` companion values. Credentials are not bundled into the mobile
app or documentation. Full current browser evidence is recorded in
[`docs/customer-admin-acceptance-2026-07-24.md`](../customer-admin-acceptance-2026-07-24.md).
The earlier administrator-only record remains in
[`docs/admin-acceptance-2026-07-23.md`](../admin-acceptance-2026-07-23.md).

## Acceptance Database Boundary

Local PostgreSQL retains acceptance/test rows created through real API calls,
including completed bookings and recommendation history from earlier reviews.
They are persisted backend data, not frontend mock data. This remediation does
not delete those rows without a separate, explicit cleanup request. Use a fresh
database when a clean demo dataset is required. Expired special-closure
settings were separately cleared because they were obsolete configuration, not
acceptance business records.

## Page Entry Points

- Player home notification bell shows a real unread indicator.
- Player profile links to notification preferences, Racket Passport, and Wallet.
- Player booking detail links to its payment, check-in reference, support chat,
  tracking, and completed-service feedback.
- Racket Passport adds a real registration/edit screen, and new bookings can
  select an owned saved racket instead of duplicating frame identity.
- Admin tabs expose chat and analytics; the dashboard exposes check-in, service
  queue, and payment verification.

## Payment Boundary

This implementation does not pretend to be an external payment gateway.

- Card, online-banking, and external e-wallet requests are persisted as
  `pending` until the shop admin verifies the real transfer.
- Wallet top-ups remain pending and do not increase balance until admin
  verification.
- Wallet booking payments complete only when the server confirms sufficient
  persisted balance.
- Checkout first loads a server quote and submits that expected amount. A
  concurrent price change returns a conflict and forces a fresh quote.
- The ledger uses row-level locks around booking, account, and payment state to
  prevent duplicate active payments and wallet overspend.

Add a payment-provider webhook only when a provider and credentials are
selected; it should replace admin verification, not create a second ledger.

## Deliberate External Boundary

StringSense does not claim to process card, online-banking, or external
e-wallet transfers. Those methods create a pending ledger request for manual
shop verification. A payment-provider redirect/webhook requires a selected
provider and credentials and must replace that manual verification boundary,
not create a second source of truth.

The password-reset APIs and verification-code rules use the configured OpenWA
session. Codes are committed before provider I/O, and provider failures retain
the generic anti-enumeration response. A connected session and real-phone
receipt are still required before claiming live external delivery.
