# Appendix F: Testing Evidence

The backend test suite verifies the FYP1 core and the current persisted FYP2
modules using FastAPI `TestClient`, database fixtures, and one optional real
PostgreSQL concurrency test.

Source files:

- `backend/tests/test_unified_backend_flows.py`
- `backend/tests/test_recommendation_use_case.py`
- `backend/tests/test_booking_policies.py`
- `backend/tests/test_recommendation_matrix_import.py`
- `backend/tests/test_sqlalchemy_repositories.py`
- `backend/tests/test_booking_conversations.py`
- `backend/tests/test_commerce_quote.py`
- `backend/tests/test_notifications.py`
- `backend/tests/test_rackets_feedback.py`
- `backend/tests/test_store_analytics.py`

## Recommended Test Evidence Table

| Test Case | Source | What It Verifies |
| --- | --- | --- |
| Customer auth, profile, booking, and admin status flow | `test_auth_profile_booking_and_admin_status_flow` | Player registration, profile update, booking creation, admin booking lookup, and booking status update. |
| Customer cannot access admin booking routes | `test_customer_cannot_access_admin_booking_routes` | Role-based access control returns forbidden response for non-admin user. |
| Recommendation logs and admin string controls | `test_recommendations_logs_and_admin_string_controls` | Recommendation generation, score breakdown, cached results, admin recommendation logs, and catalog update/deactivation. |
| Admin inventory update controls public availability | `test_admin_inventory_string_update_controls_public_availability` | Inventory stock updates affect public catalog visibility. |
| Public string filters expose normalized catalog fields | `test_public_string_filters_expose_normalized_catalog_fields` | Catalog filtering by hybrid flag, brand, and gauge. |
| Admin can persist official performance and inventory history | `test_admin_can_persist_official_performance_and_inventory_history` | Manual performance values and inventory movements are persisted. |
| Admin can persist catalog editor fields and string image | `test_admin_can_persist_catalog_editor_fields_and_string_image` | Product image upload and admin catalog editing. |
| Booking policy validation | `test_booking_policies.py` | Invalid status transitions and terminal-status note rules. |
| Recommendation matrix import | `test_recommendation_matrix_import.py` | Import of NLP/review feature matrix into backend feature store. |
| Booking support lifecycle and authorization | `test_booking_conversations.py` | Thread ownership, admin role, messages, read state, resolve/close lifecycle, and closed-thread guards. |
| Payment quote ownership | `test_commerce_quote.py` | Server-owned booking amount and active-ledger quote behavior. |
| Notification ownership/preferences/read state | `test_notifications.py` | Owned event derivation, category filtering, persistent reads, and foreign-ID rejection. |
| Racket Passport and feedback | `test_rackets_feedback.py` | Physical-racket ownership/snapshots plus one feedback record per completed owned booking. |
| Persisted analytics | `test_store_analytics.py` | Payment-backed revenue/workload and store-local day boundaries. |
| Notification and wallet payment flow | `test_notification_preferences_and_verified_wallet_payment_flow` | Admin verification, one-time wallet credit, balance-backed booking payment, and preference persistence. |

## Suggested Validation Commands

```bash
cd backend
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/mypy app tests
./.venv/bin/pytest -v
```

For mobile validation:

```bash
cd mobile
nvm use
npx tsc --noEmit
npm run lint -- --max-warnings=0
npx expo export --platform web --output-dir /tmp/stringsense-web-export
```

## Report Notes

- Label evidence as FYP1 or current FYP2 scope. Do not backdate current
  chat/wallet/payment/notification tests as proof that those features belonged
  to the original FYP1 deliverable.
- If screenshots are used as UI evidence, pair them with at least one test table to show functional validation beyond visual output.
- Current customer and administrator browser coverage is recorded in
  `docs/customer-admin-acceptance-2026-07-24.md`.
