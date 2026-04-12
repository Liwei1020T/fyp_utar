# API Contract

## Response Shape

Successful requests return direct typed JSON resources or pagination objects.

Paginated endpoints use:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

Error responses use:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Validation error",
    "details": {}
  }
}
```

## Public Endpoints

### Health

- `GET /health`
- `GET /api/health`

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/forgot-password/request-code`
- `POST /api/auth/forgot-password/reset`
- `GET /api/auth/me`

Example register request:

```json
{
  "username": "tanweijie",
  "phone_number": "+60123456789",
  "password": "secret123"
}
```

Example login response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "role": "customer",
  "phone_number": "+60123456789",
  "user_id": "uuid",
  "user": {
    "id": "uuid",
    "username": "tanweijie",
    "phone_number": "+60123456789",
    "role": "customer",
    "auth_provider": "local",
    "external_auth_id": null
  }
}
```

Example forgot-password request:

```json
{
  "phone_number": "+60123456789"
}
```

Example forgot-password reset request:

```json
{
  "phone_number": "+60123456789",
  "verification_code": "123456",
  "new_password": "newsecret123"
}
```

### Profile

- `GET /api/profile`
- `PUT /api/profile`

Example profile request:

```json
{
  "skill_level": "intermediate",
  "playing_style": "attacking",
  "budget_min": 40,
  "budget_max": 80,
  "preferred_tension": 25,
  "game_type": "doubles",
  "frequency_per_week": 3,
  "pref_attack": 5,
  "pref_comfort": 3,
  "pref_control": 4,
  "pref_durability": 4,
  "pref_elasticity": 5,
  "pref_sound": 3,
  "pref_string_movement": 4,
  "pref_tension_retention": 4,
  "pref_value_for_money": 3
}
```

### Strings

- `GET /api/strings`
- `GET /api/strings/{id}`
- `GET /api/admin/strings`
- `POST /api/admin/strings`
- `PUT /api/admin/strings/{id}`
- `DELETE /api/admin/strings/{id}`
- `GET /api/admin/inventory/strings`
- `GET /api/admin/inventory/strings/{id}`
- `PATCH /api/admin/inventory/strings/{id}`
- `GET /api/admin/inventory/strings/{id}/movements`
- `GET /api/admin/strings/{id}/official-performance`
- `PUT /api/admin/strings/{id}/official-performance`
- `GET /api/admin/strings/{id}/recommendation-matrix`
- `POST /api/admin/recommendation-matrix/import`
- `GET /api/admin/business-hours`
- `PUT /api/admin/business-hours`
- `GET /api/slots`
- `GET /api/admin/slots`
- `GET /api/admin/check-in/lookup`
- `POST /api/admin/check-in`
- `GET /api/admin/service-queue`
- `GET /api/admin/store-settings`
- `PUT /api/admin/store-settings`
- `GET /api/admin/analytics/summary`
- `GET /api/admin/analytics/popular-strings`

Only approved catalog strings from `backend/data/string_catalog_db_ready.json` can be created or updated.

Public string listing now supports:

- `brand`
- `series`
- `gauge_min`
- `gauge_max`
- `is_hybrid`
- `search`

Inventory responses extend the base string shape with:

- `stock_level`
- `current_stock`
- `reserved_stock`
- `available_stock`
- `reorder_level`
- `reorder_quantity`
- `cost_price`
- `selling_price`
- `availability` (`in_stock`, `low_stock`, `out_of_stock`)
- `admin_note`

Official performance responses include:

- `source_type`
- `source_name`
- `source_url`
- `source_region`
- `category`
- `feature`
- `feel`
- `repulsion_power`
- `durability`
- `hitting_sound`
- `shock_absorption`
- `control`
- `notes`
- `status`

Recommendation matrix inspection responses include:

- `effective_scores`
  - the current collapsed item-side scores after source-layer priority is applied
- `official_performance`
  - still returned separately from matrix rows
- `matrix_by_source`
  - raw matrix rows grouped by source layer such as `nlp_review` and `hybrid_derived`

Recommendation matrix import responses include:

- `csv_path`
- `source_layer`
- `total_csv_rows`
- `matched_strings`
- `unmatched_strings`
- `inserted_entries`
- `updated_entries`
- `unchanged_entries`
- `matched_by`
- `warnings`

Store-ops responses add:

- business hours day configs in snake_case (`is_open`, `open_time`, `slot_duration_minutes`, `max_bookings_per_slot`)
- generated slot rows with `booked_count` and `available_spots`
- service queue lanes grouped by booking status
- single-store settings payloads for support/policy copy
- analytics summary and popular string aggregates for the admin dashboard

### Recommendations

- `POST /api/recommendations/preview`
- `POST /api/recommendations/profile`
- `POST /api/recommendations/generate`
- `GET /api/recommendations/{user_id}`
- `GET /api/recommendations/{user_id}/{catalog_id}`
- `GET /api/admin/recommendations/logs`

Direct preview request:

```json
{
  "skill_level": "intermediate",
  "playing_style": "attacking",
  "budget_min": 40,
  "budget_max": 80,
  "preferred_tension": 25,
  "game_type": "doubles",
  "frequency_per_week": 3,
  "pref_attack": 5,
  "pref_comfort": 3,
  "pref_control": 4,
  "pref_durability": 4,
  "pref_elasticity": 5,
  "pref_sound": 3,
  "pref_string_movement": 4,
  "pref_tension_retention": 4,
  "pref_value_for_money": 3,
  "top_n": 5
}
```

Profile recommendation request:

```json
{
  "top_n": 5
}
```

Recommendation response:

```json
{
  "algorithm_version": "hybrid_preference_rule_budget_nlp_v1",
  "generated_at": "2026-04-12T14:10:00+00:00",
  "results": [
    {
      "rank": 1,
      "catalog_id": "yonex-bg80",
      "string_name": "Yonex BG80",
      "brand": "Yonex",
      "model_name": "BG80",
      "score": 0.84,
      "price_rm": 45.0,
      "aspect_scores": {
        "attack": 0.81,
        "comfort": 0.58,
        "control": 0.72,
        "durability": 0.61,
        "elasticity": 0.79,
        "sound": 0.84,
        "string_movement": 0.67,
        "tension_retention": 0.63,
        "value_for_money": 0.59
      },
      "reasons": [
        "matches your attack preference",
        "within your budget range",
        "fits your attacking playing style"
      ],
      "score_breakdown": {
        "preference_match": 0.82,
        "rule_fit": 0.75,
        "budget_fit": 0.93,
        "nlp_review_score": 0.81,
        "final_score": 0.84
      },
      "rationale_payload": {
        "feature_sources": {
          "attack": "nlp_review",
          "control": "nlp_review"
        },
        "profile_context": {
          "skill_level": "intermediate",
          "playing_style": "attacking"
        },
        "rule_events": []
      },
      "generated_at": "2026-04-12T14:10:00+00:00"
    }
  ]
}
```

`POST /api/recommendations/generate` uses the current authenticated user's saved profile, writes `user_preference_matrix`, caches the ranked rows in `recommendation_score_cache`, and returns the same response shape. The `/profile` route is retained as a compatibility alias.

`GET /api/recommendations/{user_id}` returns the latest cached recommendation set. Customers may use their own user id or `me`; admins may inspect any user id.

`GET /api/recommendations/{user_id}/{catalog_id}` returns one cached recommendation result with the full rationale payload.
The returned `algorithm_version` is read from the cached recommendation row, not inferred from the currently deployed code version.

### Bookings

- `POST /api/bookings`
- `GET /api/bookings`
- `GET /api/bookings/{id}`
- `POST /api/bookings/{id}/updates`
- `GET /api/admin/bookings`
- `GET /api/admin/bookings/{id}`
- `PATCH /api/admin/bookings/{id}/status`
- `POST /api/admin/bookings/{id}/updates`
- `POST /api/admin/bookings/{id}/photos`

Canonical booking statuses:

- `awaiting_dropoff`
- `in_progress`
- `ready_for_collection`
- `completed`
- `cancelled`
- `rejected`

Example booking request:

```json
{
  "string_id": "uuid",
  "racket_brand": "Yonex",
  "racket_model": "Astrox 88D",
  "requested_tension": 25,
  "drop_off_datetime": "2026-04-03T10:00:00Z",
  "notes": "Customer prefers a crisp feel."
}
```

Customer-created bookings now start in `awaiting_dropoff`.

Example admin status update request:

```json
{
  "status": "rejected",
  "note": "Requested slot is outside current store operating hours."
}
```

`note` is optional for forward progress updates and required for `cancelled` or `rejected`.

Booking update endpoints accept `multipart/form-data` with at least one of:

- `comment`: optional text comment
- `photo`: optional JPG, PNG, or WEBP image up to 5 MB
- `photo_type`: optional `racket`, `service_progress`, or `other`

Admin photo uploads may also use `POST /api/admin/bookings/{id}/photos` with:

- `photo`: required JPG, PNG, or WEBP image up to 5 MB
- `comment`: optional admin note
- `photo_type`: optional `racket`, `service_progress`, or `other`; defaults to `racket`

Booking responses include:

- `updates`: booking comments/photos from player or admin users
- `photo_url`: relative media URL such as `/media/booking-updates/<file>`
- `photo_type`: optional photo category for uploaded booking photos
