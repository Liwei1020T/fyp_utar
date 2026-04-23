# Appendix B: Backend API Endpoint Summary

The StringSense backend is implemented with FastAPI and exposes REST endpoints under `/api`. The mobile application uses these endpoints for authentication, profile management, string catalog browsing, recommendation generation, booking flow, and admin operations.

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
| Catalog | `/api/strings/{id}` | GET | View string details. |
| Recommendation | `/api/recommendations/generate` | POST | Generate and persist profile-based recommendation results. |
| Recommendation | `/api/recommendations/me` | GET | Retrieve cached recommendation results for current user. |
| Recommendation | `/api/recommendations/me/{catalog_id}` | GET | Retrieve explanation details for one recommended string. |
| Booking | `/api/bookings` | POST | Create a stringing booking. |
| Booking | `/api/bookings` | GET | List current player's bookings. |
| Booking | `/api/bookings/{id}` | GET | View player booking detail. |
| Booking | `/api/bookings/{id}/updates` | POST | Add player comment or optional booking photo. |
| Store | `/api/slots` | GET | Generate booking slots from business hours. |
| Store | `/api/store-settings` | GET | Read public store settings. |

## Admin Endpoints

| Module | Endpoint | Method | Purpose |
| --- | --- | --- | --- |
| Admin Catalog | `/api/admin/strings` | GET/POST | List or create catalog strings. |
| Admin Catalog | `/api/admin/strings/{id}` | PUT/DELETE | Update or deactivate catalog string. |
| Admin Catalog | `/api/admin/strings/{id}/image` | POST/DELETE | Upload or remove string product image. |
| Admin Inventory | `/api/admin/inventory/strings` | GET | List store inventory. |
| Admin Inventory | `/api/admin/inventory/strings/{id}` | GET/PATCH | View or update inventory price, stock, status, and notes. |
| Admin Inventory | `/api/admin/inventory/strings/{id}/movements` | GET | View inventory movement history. |
| Admin Booking | `/api/admin/bookings` | GET | List all bookings for admin. |
| Admin Booking | `/api/admin/bookings/{id}` | GET | View booking detail. |
| Admin Booking | `/api/admin/bookings/{id}/status` | PATCH | Update booking status and expected completion time. |
| Admin Booking | `/api/admin/bookings/{id}/updates` | POST | Add admin comment or photo to booking. |
| Admin Store | `/api/admin/business-hours` | GET/PUT | Read or update business hours and slot rules. |
| Admin Store | `/api/admin/store-settings` | GET/PUT | Read or update limited store settings. |
| Admin Recommendation | `/api/admin/recommendations/logs` | GET | View recommendation request/response logs. |
| Admin Recommendation | `/api/admin/recommendations/runs` | GET | View persisted recommendation runs and ranked items. |

## Notes for Report

- Role-based access control prevents customers from accessing admin endpoints.
- The backend returns structured error payloads for validation, permission, and conflict errors.
- FYP1 uses a unified Python backend; the AI logic is called in-process instead of through a separate public AI service.

