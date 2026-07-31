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

### Persisted Media

- `GET /api/media/{media_path}`

This route requires an unexpired `exp` value and matching HMAC `sig` query
parameter. Booking and catalog DTOs generate these time-limited URLs; callers
cannot retrieve an arbitrary upload path.

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
    "external_auth_id": null,
    "is_active": true
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

The backend owns code generation, expiry, attempt limits, one-time use, and the
password update. Each request replaces the prior unused code for that phone
number. A successful reset invalidates every bearer token issued before the
password change. It does not currently send the code through SMS or WhatsApp.
`PASSWORD_RESET_DEV_PREVIEW_ENABLED` is local-development support only; keep it
disabled outside an explicitly controlled development session. Production
self-service reset requires a selected delivery provider and credentials.

### Profile

- `GET /api/profile`
- `PUT /api/profile`

`GET /api/profile` returns `200` with `null` until a newly registered player
saves their profile. Profile absence is an onboarding state, not an API error.

Example profile request:

```json
{
  "skill_level": "intermediate",
  "playing_style": "attacking",
  "budget_tier": "between_30_50",
  "preferred_tension": 25,
  "game_type": "doubles",
  "frequency_per_week": 3,
  "preferred_feel": "crisp",
  "recent_goal": "I want a sharper attacking setup for doubles.",
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

### Notifications

- `GET /api/notifications`
- `PATCH /api/notifications/read`
- `GET /api/notifications/preferences`
- `PUT /api/notifications/preferences`
- `POST /api/devices/push-token`
- `GET /api/admin/device-tokens`
- `GET /api/admin/notifications`
- `POST /api/admin/notifications`
- `POST /api/admin/notifications/{notification_id}/resend`

Preferences are stored per authenticated user and contain boolean `booking`,
`payment`, `service`, `chat`, `recommendation`, and `system` fields. The feed
derives owned operational events and includes persisted admin deliveries before
applying those preferences. Read event IDs are persisted per user.

Device registration stores only the authenticated user's Expo token. Admin
delivery always creates an in-app notification record; remote Expo delivery is
attempted only when `EXPO_PUSH_ENABLED=true`.

### Account Security and Privacy

- `POST /api/auth/change-password`
- `POST /api/auth/delete-account-request`
- `GET /api/profile/privacy`
- `PUT /api/profile/privacy`

Password changes verify the current password and invalidate every previously
issued bearer token, including the token used for the change; clients must log
in again. Account deletion is an auditable request, not an immediate destructive
delete. Privacy settings store analytics, personalization, and marketing consent
independently from the recommendation profile.

### Booking Support Conversations

- `GET /api/conversations`
- `POST /api/bookings/{booking_id}/support`
- `GET /api/conversations/{conversation_id}`
- `POST /api/conversations/{conversation_id}/messages`
- `POST /api/conversations/{conversation_id}/read`
- `GET /api/admin/conversations`
- `GET /api/admin/conversations/{conversation_id}`
- `POST /api/admin/conversations/{conversation_id}/messages`
- `POST /api/admin/conversations/{conversation_id}/read`
- `POST /api/admin/conversations/{conversation_id}/resolve`
- `POST /api/admin/conversations/{conversation_id}/close`

Conversation IDs equal their booking IDs. Only explicitly requested booking
support threads are listed. State is persisted as `waiting_admin`,
`admin_joined`, `resolved`, or `closed`; messages remain attached to the
booking update history with a dedicated conversation channel.

### Rackets and Feedback

- `GET /api/rackets`
- `POST /api/rackets`
- `GET /api/rackets/{racket_id}`
- `PATCH /api/rackets/{racket_id}`
- `DELETE /api/rackets/{racket_id}`
- `GET /api/rackets/{racket_id}/history`
- `GET /api/bookings/{booking_id}/feedback`
- `POST /api/bookings/{booking_id}/feedback`
- `GET /api/admin/feedback`
- `GET /api/admin/feedback/export`

Rackets are owned physical records with stable IDs. A booking may reference an
owned racket and keeps the racket brand/model snapshot used at booking time.
Racket detail history includes only completed bookings for that racket.
Structured feedback is allowed once per owned completed booking, with a
1-to-5 overall rating plus optional relevance, string, tension, comfort,
control, repulsion, and durability ratings. Admins can filter the persisted
records by `booking_id`, string, rating, or date, page them with `limit` and
`offset`, and export the same fields as CSV.

### Payments and Wallet

- `GET /api/payments`
- `GET /api/payments/bookings/{booking_id}/quote`
- `POST /api/payments/bookings/{booking_id}`
- `GET /api/wallet`
- `POST /api/wallet/top-ups`
- `GET /api/admin/payments`
- `PATCH /api/admin/payments/{payment_id}`

External card, online-banking, and e-wallet records start as `pending`. The
admin endpoint verifies them as `paid`, `failed`, or `cancelled`. Wallet top-up
credit is written only when the admin verifies the associated payment.

`wallet_balance` booking payments are server-validated against the persisted
ledger and complete immediately only when sufficient balance exists.

The quote endpoint returns the server-owned current amount, wallet balance, and
any active payment so checkout never trusts a stale catalog snapshot.

### Strings

- `GET /api/strings`
- `GET /api/strings/{id}`
- `GET /api/admin/strings`
- `POST /api/admin/strings`
- `PUT /api/admin/strings/{id}`
- `DELETE /api/admin/strings/{id}`
- `POST /api/admin/strings/{id}/image`
- `DELETE /api/admin/strings/{id}/image`
- `GET /api/admin/inventory/strings`
- `GET /api/admin/inventory/strings/{id}`
- `PATCH /api/admin/inventory/strings/{id}`
- `PUT /api/admin/inventory/strings/{id}/editor`
- `GET /api/admin/inventory/strings/{id}/movements`
- `GET /api/admin/strings/{id}/official-performance`
- `PUT /api/admin/strings/{id}/official-performance`
- `GET /api/admin/strings/{id}/recommendation-matrix`
- `POST /api/admin/recommendation-matrix/import`
- `GET /api/admin/business-hours`
- `PUT /api/admin/business-hours`
- `GET /api/slots`
- `GET /api/store-settings`
- `GET /api/admin/slots`
- `GET /api/admin/check-in/lookup`
- `POST /api/admin/check-in`
- `POST /api/admin/check-in/lookup`
- `POST /api/admin/check-in/confirm`
- `GET /api/admin/service-queue`
- `GET /api/admin/store-settings`
- `PUT /api/admin/store-settings`
- `GET /api/admin/analytics/summary`
- `GET /api/admin/analytics/popular-strings`

Only approved catalog strings from `backend/data/string_catalog_db_ready.json` can be created or updated.

Admin string image upload accepts `multipart/form-data`:

- `photo`: required JPG, PNG, or WEBP image up to 5 MB
- response: updated `StringOut`
- replacing an existing image deletes the prior stored file after the catalog update succeeds

`DELETE /api/admin/strings/{id}/image` clears the catalog image URL, deletes the stored file when present, and returns the updated `StringOut`.

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
- `pricing_mode` (`fixed_price`, `quoted_at_shop`, `price_pending`)
- `availability_status` (`in_stock`, `low_stock`, `out_of_stock`)
- `availability` (`in_stock`, `low_stock`, `out_of_stock`)
- `admin_note`

The editor endpoint updates catalog master fields, official performance, and
inventory in one transaction. Product image upload/removal remains a separate
media operation so the UI can report a structured-save success independently
from a media failure.

Catalog string responses also include admin-editor fields such as:

- `category`
- `main_trait`
- `tension_min_lbs`
- `tension_max_lbs`
- `image_url`

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
  - each row exposes `source_version`, `source_generated_at`, and `review_count_snapshot` when the source provides them

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

The default runtime import source is the V9 workbook at `../ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`.

Store-ops responses add:

- business hours day configs in snake_case (`is_open`, `open_time`, `slot_duration_minutes`, `max_bookings_per_slot`)
- generated slot rows with `booked_count` and `available_spots`
- service queue lanes grouped by booking status
- single-store settings payloads for support/policy copy,
  `default_service_price`, notification templates, and `trending_string_ids`;
  player clients read this through `GET /api/store-settings`
- analytics summary with store-local `today_bookings`, repeat customers,
  feedback completion, average service time, tension distribution, and popular
  string aggregates

Booking creation accepts `service_method` as `counter_dropoff` or
`pickup_request`. Players may cancel through
`POST /api/bookings/{booking_id}/cancel` while the domain transition policy
still permits cancellation.

`POST /api/bookings/{booking_id}/check-in-token` creates a ten-minute,
single-use QR token and revokes the booking's prior active token. Only its
SHA-256 digest is persisted. The secure admin
lookup/confirm endpoints accept that raw token; the older ID/reference
check-in endpoints remain available for manual counter fallback.

### Recommendations

- `POST /api/recommendations/preview`
- `POST /api/recommendations/profile`
- `POST /api/recommendations/generate`
- `GET /api/recommendations/{user_id}`
- `GET /api/recommendations/{user_id}/{catalog_id}`
- `GET /api/admin/recommendations/logs`
- `GET /api/admin/recommendations/runs`
- `GET /api/admin/recommendations/runs/{run_id}`

Direct preview request:

```json
{
  "skill_level": "intermediate",
  "playing_style": "attacking",
  "budget_tier": "between_30_50",
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
  "algorithm_version": "fyp1_similarity_confidence_rule_budget_tier_v5",
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
        "repulsion": 0.81,
        "control": 0.72,
        "durability": 0.61,
        "comfort": 0.58,
        "sound": 0.84,
        "elasticity": 0.76,
        "tension_retention": 0.69,
        "string_movement": 0.63
      },
      "reasons": [
        "matches your power and rebound preference",
        "mid-price tier strongly fits your budget tier",
        "fits your attacking playing style"
      ],
      "score_breakdown": {
        "preference_match": 0.82,
        "rule_fit": 0.61,
        "budget_fit": 1.0,
        "confidence_score": 0.72,
        "nlp_review_score": 0.71,
        "final_score": 0.84
      },
      "rationale_payload": {
        "algorithm_family": "rule_enhanced_confidence_aware_content_based_official_nlp_budget_tier",
        "collaborative_filtering_used": false,
        "matrix_version": "latest_practical_string_feature_matrix_v9_v8dict",
        "feature_source_version": "latest_practical_string_feature_matrix_v9_v8dict",
        "feature_source_generated_at": "2026-04-12T13:55:00+00:00",
        "feature_sources": {
          "repulsion": "nlp_review",
          "control": "nlp_review"
        },
        "feature_evidence": [
          {
            "feature_key": "repulsion",
            "display_label": "Repulsion",
            "effective_score": 0.81,
            "preference_weight": 0.1935,
            "source": "official_performance+nlp_review",
            "official_score": 0.77,
            "nlp_review_score": 0.88,
            "nlp_confidence": 1.0,
            "nlp_influence": 0.46,
            "fusion_confidence": 0.79,
            "source_version": "latest_practical_string_feature_matrix_v9_v8dict",
            "source_generated_at": "2026-04-12T13:55:00+00:00",
            "source_ref": "https://example.invalid/source",
            "review_count_snapshot": 3109
          }
        ],
        "nlp_review_signal_count": 2,
        "nlp_review_summary": "Review-derived signals reinforce repulsion and sound for this profile.",
        "user_preference_vector": [
          { "feature_key": "repulsion", "raw_score": 6, "preference_weight": 0.15 },
          { "feature_key": "elasticity", "raw_score": 5, "preference_weight": 0.125 },
          { "feature_key": "tension_retention", "raw_score": 4, "preference_weight": 0.10 },
          { "feature_key": "string_movement", "raw_score": 4, "preference_weight": 0.10 }
        ],
        "budget": {
          "price_rm": 45.0,
          "budget_tier": "between_30_50",
          "item_price_tier": "mid",
          "budget_tier_bounds_rm": {
            "min_rm": 30.0,
            "max_rm": 50.0
          }
        },
        "profile_context": {
          "skill_level": "intermediate",
          "playing_style": "attacking",
          "budget_tier": "between_30_50"
        },
        "rule_events": []
      },
      "generated_at": "2026-04-12T14:10:00+00:00"
    }
  ]
}
```

`budget_fit` reflects price alignment against the user's selected `budget_tier`. It is not derived from a separate `value_for_money` runtime score.

`nlp_review_score` is an explanation-facing score that shows how strongly review-derived matrix signals support the user's weighted priorities. It does not replace `preference_match` or change the final weighting formula.
The FYP1 recommender is rule-enhanced, confidence-aware, content-based recommendation with official performance + NLP review feature fusion + budget-tier fit. It does not use collaborative filtering, matrix factorization, embeddings, or interaction-history scoring.

`POST /api/recommendations/generate` uses the current authenticated user's saved profile, writes `user_preference_matrix`, caches the ranked rows in `recommendation_score_cache`, persists a historical run in `recommendation_runs` and `recommendation_run_items`, and returns the same response shape. The persisted `profile_snapshot` is the saved backend profile context, not just a copy of the request payload. The `/profile` route is retained as a compatibility alias.

`GET /api/recommendations/{user_id}` returns the latest cached recommendation set. Customers may use their own user id or `me`; admins may inspect any user id.

`GET /api/recommendations/{user_id}/{catalog_id}` returns one cached recommendation result with the full rationale payload.
The returned `algorithm_version` is read from the cached recommendation row, not inferred from the currently deployed code version.

`GET /api/admin/recommendations/runs` returns persisted recommendation run history with item-level score rows.

`GET /api/admin/recommendations/runs/{run_id}` returns one persisted recommendation run with its full item-level score rows and rationale payloads.

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
