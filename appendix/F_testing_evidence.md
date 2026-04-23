# Appendix F: Testing Evidence

The backend test suite verifies core FYP1 flows using FastAPI `TestClient` and database fixtures.

Source files:

- `backend/tests/test_unified_backend_flows.py`
- `backend/tests/test_recommendation_use_case.py`
- `backend/tests/test_booking_policies.py`
- `backend/tests/test_recommendation_matrix_import.py`
- `backend/tests/test_sqlalchemy_repositories.py`

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

## Suggested Validation Commands

```bash
cd backend
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/mypy app ai_service tests
./.venv/bin/pytest -v
```

For mobile validation:

```bash
cd mobile
nvm use
npx tsc --noEmit
```

## Report Notes

- Testing evidence should focus on implemented FYP1 scope only.
- Do not claim automated tests for FYP2 deferred features such as chat, wallet, payment, or notifications unless those features are explicitly tested and included in scope.
- If screenshots are used as UI evidence, pair them with at least one test table to show functional validation beyond visual output.

