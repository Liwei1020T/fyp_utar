# Appendix B: Backend API Endpoint Summary

The StringSense backend is implemented with FastAPI and exposes REST endpoints
under `/api`. The mobile application uses these endpoints for authentication,
profiles, catalog and recommendation, booking/service history, notifications,
support conversations, commerce, rackets/feedback, and admin operations.

Source files:

- `backend/app/main.py`
- `backend/app/entrypoints/api/router.py`
- `backend/app/entrypoints/api/routes/*.py`
- `backend/README.md`

## Public and Player Endpoints

| Module | Endpoint | Method | Purpose |
| --- | --- | --- | --- |
| Health | `/health`, `/api/health` | GET | Verify backend and database connectivity. |
| Auth | `/api/auth/register` | POST | Register a new player account using phone number and password. |
| Auth | `/api/auth/login` | POST | Authenticate player or admin and return access token. |
| Auth | `/api/auth/forgot-password/request-code` | POST | Request password reset code. |
| Auth | `/api/auth/forgot-password/reset` | POST | Reset password with verification code. |
| Auth | `/api/auth/me` | GET | Fetch the current authenticated user. |
| Profile | `/api/profile` | GET | Retrieve current player profile. |
| Profile | `/api/profile` | PUT | Create or update player recommendation profile. |
| Catalog | `/api/strings` | GET | Browse active badminton strings. |
| Recommendation | `/api/recommendations/generate` | POST | Generate and persist profile-based recommendation results. |
| Recommendation | `/api/recommendations/{user_id}` | GET | Retrieve cached recommendation results; the mobile app uses `me` for the current player. |
| Recommendation | `/api/recommendations/{user_id}/{catalog_id}` | GET | Retrieve explanation details for one cached recommended string. |
| Booking | `/api/bookings` | POST | Create a stringing booking. |
| Booking | `/api/bookings` | GET | List current player's bookings. |
| Booking | `/api/bookings/{id}` | GET | View player booking detail. |
| Booking | `/api/bookings/{id}/updates` | POST | Add player comment or optional booking photo. |
| Support | `/api/bookings/{id}/support` | POST | Open the owned booking-support thread. |
| Support | `/api/conversations`, `/api/conversations/{id}` | GET | List or inspect owned support threads. |
| Support | `/api/conversations/{id}/messages` | POST | Send a player support message. |
| Support | `/api/conversations/{id}/read` | POST | Persist player read state. |
| Notifications | `/api/notifications` | GET | Derive the owned event feed. |
| Notifications | `/api/notifications/read` | PATCH | Persist read event IDs. |
| Notifications | `/api/notifications/preferences` | GET/PUT | Read or update event-category preferences. |
| Commerce | `/api/payments` | GET | List owned persisted payments. |
| Commerce | `/api/payments/bookings/{id}/quote` | GET | Read the server-owned booking amount and active payment. |
| Commerce | `/api/payments/bookings/{id}` | POST | Create or complete an owned booking payment. |
| Wallet | `/api/wallet` | GET | Read balance derived from the append-only ledger. |
| Wallet | `/api/wallet/top-ups` | POST | Create a pending top-up for admin verification. |
| Rackets | `/api/rackets`, `/api/rackets/{id}` | GET/POST/PATCH | Manage owned physical racket passports. |
| Feedback | `/api/bookings/{id}/feedback` | GET/POST | Read or create one completed-service feedback record. |
| Media | `/api/media/{media_path}` | GET | Serve a time-limited signed booking/catalog media URL. |
| Store | `/api/slots` | GET | Generate booking slots from business hours. |
| Store | `/api/store-settings` | GET | Read public store settings. |

## Admin Endpoints

| Module | Endpoint | Method | Purpose |
| --- | --- | --- | --- |
| Admin Catalog | `/api/admin/strings/{id}/image` | POST/DELETE | Upload or remove string product image. |
| Admin Inventory | `/api/admin/inventory/strings` | GET | List store inventory. |
| Admin Inventory | `/api/admin/inventory/strings/{id}` | GET/PATCH | View or update inventory price, stock, status, and notes. |
| Admin Inventory | `/api/admin/inventory/strings/{id}/editor` | PUT | Atomically update catalog, official performance, and inventory sections. |
| Admin Evidence | `/api/admin/strings/{id}/official-performance` | GET | Inspect official/manual performance. |
| Admin Evidence | `/api/admin/strings/{id}/recommendation-matrix` | GET | Inspect effective and source-layer recommendation features. |
| Admin Evidence | `/api/admin/recommendation-matrix/import` | POST | Re-import the configured recommendation matrix and report matched/updated/unmatched rows. |
| Admin Booking | `/api/admin/bookings` | GET | List all bookings for admin. |
| Admin Booking | `/api/admin/bookings/{id}` | GET | View booking detail. |
| Admin Booking | `/api/admin/bookings/{id}/status` | PATCH | Update booking status and expected completion time. |
| Admin Booking | `/api/admin/bookings/{id}/updates` | POST | Add admin comment or photo to booking. |
| Admin Booking | `/api/admin/bookings/{id}/photos` | POST | Upload a dedicated admin booking-update photo. |
| Admin Counter | `/api/admin/check-in/lookup` | GET | Find a booking by order ID for counter handover. |
| Admin Counter | `/api/admin/check-in` | POST | Confirm checklist and move an awaiting booking to in progress. |
| Admin Queue | `/api/admin/service-queue` | GET | Group active bookings by persisted service state. |
| Admin Commerce | `/api/admin/payments`, `/api/admin/payments/{id}` | GET/PATCH | Monitor and verify payments or wallet top-ups. |
| Admin Support | `/api/admin/conversations`, `/api/admin/conversations/{id}` | GET | List or inspect booking-support threads. |
| Admin Support | `/api/admin/conversations/{id}/messages` | POST | Send an admin support reply. |
| Admin Support | `/api/admin/conversations/{id}/read` | POST | Persist admin read state. |
| Admin Support | `/api/admin/conversations/{id}/resolve` | POST | Mark a support thread resolved. |
| Admin Support | `/api/admin/conversations/{id}/close` | POST | Close a support thread. |
| Admin Store | `/api/admin/business-hours` | GET/PUT | Read or update business hours and slot rules. |
| Admin Store | `/api/admin/store-settings` | GET/PUT | Read or update limited store settings. |
| Admin Analytics | `/api/admin/analytics/summary` | GET | Read persisted operations/payment metrics. |
| Admin Analytics | `/api/admin/analytics/popular-strings` | GET | Read popular-string aggregates. |
| Admin Recommendation | `/api/admin/recommendations/runs` | GET | View persisted recommendation runs and ranked items. |
| Admin Recommendation | `/api/admin/recommendations/runs/{run_id}` | GET | Inspect one run with request/profile snapshots and score evidence. |

## Notes for Report

- Role-based access control prevents customers from accessing admin endpoints.
- The backend returns structured error payloads for validation, permission, and conflict errors.
- The public recommendation logic is called in-process instead of through a
  separate public AI service.
- The original FYP1 claim boundary remains documented separately; the endpoint
  inventory above reflects the current implementation, including completed FYP2
  persistence modules.
