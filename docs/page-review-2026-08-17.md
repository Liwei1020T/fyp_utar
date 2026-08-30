# StringSense Page-by-Page Functional Review

Date: 2026-08-17
Viewport: Expo Web, 390 × 844
Runtime: FastAPI + isolated PostgreSQL database + production Expo Web export
Scope: 51 renderable pages (3 auth, 30 player, 18 admin). Redirect-only routes and layouts are excluded.

## Follow-up fixes — 2026-08-17

The findings below were repaired after the initial pass:

- Human support now has a booking-free conversation path. The player entry
  creates one reusable general thread, and the admin queue/detail screens can
  reply to it.
- Web confirmation now works for player booking cancellation, racket deletion,
  account-deletion requests, and the high-tension profile warning.
- A rejected password change no longer expires the whole player session.
- Racket list responses now include completed-service summaries, matching the
  detail page.
- Catalog descriptions are normalized to remove duplicated punctuation, and
  notification copy no longer claims a specific WhatsApp provider when the
  configured remote channel is disabled.
- A booking deep link waits for catalog hydration before showing an unavailable
  string error.

The follow-up browser smoke used a fresh no-booking player: the player opened
`Contact human support`, entered `General support`, and the admin queue displayed
and replied to the same persisted thread. Screenshots are in
`output/playwright/general-support-player.png`,
`output/playwright/general-support-admin-queue.png`, and
`output/playwright/general-support-admin-detail.png`.

## Result

- 51/51 pages rendered under the intended authentication role.
- 47/51 pages passed their primary flow without a functional defect in the
  initial pass; the four confirmed defects are now repaired.
- All administrator pages passed their main operational paths.
- Player/admin state synchronized for booking status, support chat, notifications, and wallet credit.
- The initial review used an isolated database; follow-up fixes and browser
  smoke stayed within the existing worktree.

## Initial functional defects — repaired

| Severity | Page | Finding | Evidence / root cause |
| --- | --- | --- | --- |
| High for Web | `/player/bookings/[id]` | `Cancel booking` does not cancel on Expo Web; no API request is sent. | The player page calls multi-button React Native `Alert.alert` without a Web `globalThis.confirm` branch. |
| High for Web | `/player/rackets/[id]` | `Delete passport` does not delete on Expo Web; no API request is sent. | Same confirmation-boundary root cause as booking cancellation. |
| Medium | `/player/rackets` | A racket with one completed 25-lb service is shown as `0 lbs`, `No completed services yet`, and `0 services`. | `GET /api/rackets` returns base racket rows without `service_history`; the mapper converts the missing history to an empty list. The detail endpoint independently loads the correct completed history. |
| Medium | `/player/settings` | A wrong current password logs the user out instead of showing a password-specific error. | `/api/auth/change-password` correctly returns 401, but global session handling treats the domain validation 401 as an expired access token. |

## Lower-severity findings

- Route transitions can log an accessibility warning because the pressed button retains focus inside a new `aria-hidden` route ancestor.
- A hard refresh of `/player/bookings/new` can briefly show `String unavailable` before catalog hydration; normal in-app navigation is correct.
- Some booking cards say `Vendor quote` or `Price pending` without clearly explaining why the catalog price is not being used.
- Gosen RYZONIC 65 description contains `resin..`.
- Admin notification success copy says `WhatsApp delivery: failed` when OpenWA is disabled and no device token exists; persistence is still correct.
- Fresh-install demo configuration still needs public contact/address, selected homepage strings, and prices for the other ten strings.

## Authentication pages

| Page | Result | Functional evidence |
| --- | --- | --- |
| `/auth/login` | Pass | Valid player/admin routing, invalid-credential message, logout/session restore. |
| `/auth/register` | Pass | Full form renders; mismatched confirmation is blocked before API submission. |
| `/auth/forgot-password` | Pass (live receipt pending) | Request, WhatsApp provider handoff, development preview, reset, and return-to-login are implemented. Automated tests prove persist-before-send and generic provider-failure handling; a real-phone receipt still requires a connected OpenWA session. |

## Player pages

| Page | Result | Functional evidence |
| --- | --- | --- |
| `/player/home` | Pass | Live user, unread state, quick actions, active booking, and admin-updated status. |
| `/player/strings` | Pass | All 12 approved strings, search, filters, price states, and compare selection. |
| `/player/recommend` | Pass | Saved profile/racket context and real recommendation generation. |
| `/player/results` | Pass | Three ranked results, booking, explanation, and compare actions. |
| `/player/bookings` | Pass with copy note | Live list, search/status filters, and persisted states. |
| `/player/chat` | Pass | Booking-linked and booking-free human-support thread list and entry. |
| `/player/profile` | Pass | Identity, activity, saved preferences, settings, and logout. |
| `/player/bookings/[id]` | Defect | Detail and related actions load, but Web cancellation is non-functional. |
| `/player/bookings/[id]/tracking` | Pass | Correct lifecycle timeline. |
| `/player/bookings/new` | Pass with transient note | 14-day availability, capacity, racket, tension, slot, and price; hard-refresh flash noted above. |
| `/player/bookings/summary` | Pass | Draft summary and real confirmation created a persisted booking. |
| `/player/chat/[id]` | Pass | Player message persisted; admin reply and Resolved state returned cross-role. |
| `/player/chatbot` | Pass | Reduced guided Agent starts with one short question and retains human-support entry. |
| `/player/check-in` | Pass | Secure 10-minute QR, countdown, and refresh. |
| `/player/feedback/[bookingId]` | Pass | Saved structured ratings/comments and delayed durability boundary. |
| `/player/notifications` | Pass | Booking, recommendation, wallet, service, system, and chat events persist. |
| `/player/notifications/preferences` | Pass | Category switch persisted Off and restored On. |
| `/player/payments/[bookingId]` | Pass | Server quote, four methods, and duplicate-pending protection. |
| `/player/payments/[bookingId]/result` | Pass | Verification-pending state and return links. |
| `/player/profile/edit` | Pass | Three steps restore saved values; same-value save persisted and returned to Profile. |
| `/player/rackets` | Defect | List renders but completed-service summary is inaccurate. |
| `/player/rackets/[id]` | Defect | Correct detail/history/edit; Web deletion is non-functional. |
| `/player/rackets/new` | Pass | Standard model selection and real create path. |
| `/player/recommend/explain/[id]` | Pass | Exact-run reasons/scores/trade-off plus concise DeepSeek initial and follow-up explanations; no algorithm wording or raw `**`. |
| `/player/settings` | Defect | Privacy toggles persist, but wrong current password forces logout. |
| `/player/strings/[id]` | Pass with copy note | Specs, chart, evidence, booking, compare, and share actions; double period noted above. |
| `/player/strings/compare` | Pass | Two-item in-app shortlist, radar/spec/price view, details, and clear state. |
| `/player/tools` | Pass | Ten player destinations grouped and routed correctly. |
| `/player/wallet` | Pass | Admin-verified RM20 appears exactly once with RM25 still pending. |
| `/player/wallet/top-up` | Pass | Preset/custom amount, method, real RM20 pending request, and return-to-wallet. |

## Administrator pages

| Page | Result | Functional evidence |
| --- | --- | --- |
| `/admin/dashboard` | Pass | Live queue counts, attention item, searchable 11-tool workspace. |
| `/admin/bookings` | Pass | Four bookings, counts, filters, next actions, and detail navigation. |
| `/admin/inventory` | Pass | 12 items, attention counts, stock/price states, filters, and actions. |
| `/admin/chat` | Pass | Waiting/Admin Joined threads, filters, previews, timestamps. |
| `/admin/analytics` | Pass | Booking/payment/revenue/feedback/tension/demand/busy-slot metrics match fixture. |
| `/admin/assistant` | Pass | Read-only DeepSeek operations summary; no write actions or raw `**`. |
| `/admin/bookings/[id]` | Pass | Sequential workflow, confirmation, note persistence, and status update. |
| `/admin/business-hours` | Pass | Seven-day schedule; capacity 3→4→3 save/restore succeeded. |
| `/admin/chat/[id]` | Pass | Reply changed Waiting Admin to Admin Joined; Resolve persisted. |
| `/admin/check-in` | Pass | Search/shortcut/checklist; incomplete checklist is safely blocked. |
| `/admin/feedback` | Pass | Structured record, feedback calibration evidence, filters, and CSV download. |
| `/admin/inventory/[id]` | Pass | Full editor; stock 8→9→8 save/restore succeeded. |
| `/admin/notifications` | Pass with delivery boundary | In-app send persisted; remote failed truthfully because no active provider/device. |
| `/admin/payments` | Pass | Irreversible confirmation; RM20 top-up verification credited wallet exactly once. |
| `/admin/recommendations` | Pass | Saved run list/search and current top results. |
| `/admin/recommendations/[runId]` | Pass (technical admin surface) | Exact request/profile/ranked rows/score/audit metadata retained. |
| `/admin/service-queue` | Pass | One Awaiting, two In Progress, lane positions, empty Ready lane. |
| `/admin/settings` | Pass with configuration note | Store/policy/templates/password/trending controls load; no-change save confirmed. |

## Cross-role and security checks

- Player message → admin queue/detail: passed.
- Admin reply/resolve → player thread and notification: passed.
- Admin booking status/note → player home/feed: passed.
- Admin top-up verification → player wallet ledger: passed exactly once.
- Unauthenticated player route → login: passed.
- Player admin-route attempt → player home: passed.
- Admin player-route attempt → admin dashboard: passed.
- Human handoff supports both booking-linked and booking-free threads; the
  follow-up smoke confirmed a no-booking player can reach the admin queue.

## Automated validation

- Backend Ruff: pass.
- Backend format check: 248 files formatted.
- Backend Mypy: pass, 214 source files.
- Backend Pytest: 149 passed, 2 skipped in the normal suite.
- The two opt-in PostgreSQL concurrency tests were run separately against a disposable migrated database and both passed.
- Mobile ESLint: pass.
- Mobile TypeScript: pass.
- Mobile policy tests: 10 passed.
- NLP tests: 43 passed.
- Expo Web production export: pass, 3,676 modules.
- Native JavaScript exports from the preceding delivery audit: iOS 4,196 modules; Android 4,193 modules.
- `git diff --check`: pass.

## Screenshot evidence

- `output/playwright/page-review-admin-dashboard.png`
- `output/playwright/page-review-player-home.png`
- `output/playwright/page-review-player-wallet.png`
- `output/playwright/page-review-recommendation-explanation.png`
- `output/playwright/page-review-racket-list-defect.png`
- `output/playwright/page-review-booking-new-20260817.png`
- `output/playwright/page-review-booking-new-bottom-20260817.png`
- `output/playwright/general-support-player.png`
- `output/playwright/general-support-admin-queue.png`
- `output/playwright/general-support-admin-detail.png`
- `output/playwright/settings-wrong-password-stays-signed-in.png`

## Remaining low-risk follow-ups

1. The React Navigation Web route-transition focus warning remains a minor
   accessibility follow-up; it does not block the reviewed flows.
2. Fresh demo databases now restore the configured store address, business
   hours, and trending strings from the checked-in store seed.
3. Real OpenWA/Expo delivery and external payment gateway receipts remain
   provider/device boundaries, not local page defects.
