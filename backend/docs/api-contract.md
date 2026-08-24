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
password change. When OpenWA is enabled, the backend commits the new code before
sending it to the account's WhatsApp number. Unknown accounts and provider
failures keep the same generic response so the endpoint does not reveal account
existence.
`PASSWORD_RESET_DEV_PREVIEW_ENABLED` is local-development support only; keep it
disabled outside an explicitly controlled development session.

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
  "preferred_tension": 25,
  "frequency_per_week": 3,
  "preferred_feel": "medium",
  "preferred_gauge": "no_preference",
  "recent_goal": "power",
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
- `GET /api/admin/device-tokens`
- `GET /api/admin/notifications`
- `POST /api/admin/notifications`
- `POST /api/admin/notifications/{notification_id}/resend`

Preferences are stored per authenticated user and contain boolean `booking`,
`payment`, `service`, `chat`, `recommendation`, and `system` fields. The feed
derives owned operational events and includes persisted admin deliveries before
applying those preferences. Read event IDs are persisted per user.

The current mobile app does not register Expo device tokens. Existing
server-managed or legacy token rows remain visible to admins. Admin delivery
always creates an in-app notification record; remote Expo delivery is attempted
only for an existing enabled token when `EXPO_PUSH_ENABLED=true`. Production
startup also requires the server-only `EXPO_ACCESS_TOKEN`, which is sent to Expo
as a bearer token and must never be bundled into the mobile app.

Alternatively, `OPENWA_ENABLED=true` sends the same persisted delivery through
the configured self-hosted OpenWA session using the player's account phone
number. OpenWA and Expo cannot be enabled together; OpenWA requires a
server-only, session-scoped operator API key. A category disabled in the
player's notification preferences is neither shown in the in-app feed nor sent
through OpenWA.

Completed bookings with no feedback receive a persisted `service` notification
after 7 days and one final reminder after 10 days. Each notification links to
`/player/feedback/{booking_id}`, appears in the App feed, uses OpenWA when it is
enabled, and is not recreated by repeated scheduler runs. Any submitted feedback
stops later reminders.

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

### Human Support Conversations

- `GET /api/conversations`
- `POST /api/conversations/support`
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

Booking-linked conversation IDs equal their booking IDs. Booking-free support
uses its own conversation ID and one reusable thread per player. State is
persisted as `waiting_admin`, `admin_joined`, `resolved`, or `closed`; booking
messages remain in booking update history, while general messages use their own
message table.

### Rackets and Feedback

- `GET /api/racket-models`
- `GET /api/rackets`
- `POST /api/rackets`
- `GET /api/rackets/{racket_id}`
- `PATCH /api/rackets/{racket_id}`
- `DELETE /api/rackets/{racket_id}`
- `GET /api/bookings/{booking_id}/feedback`
- `POST /api/bookings/{booking_id}/feedback`
- `PATCH /api/bookings/{booking_id}/feedback`
- `GET /api/bookings/{booking_id}/feedback-eligibility`
- `GET /api/admin/feedback`
- `GET /api/admin/feedback/export`

Rackets are owned physical records with stable IDs. A booking may reference an
owned racket and keeps the racket brand/model snapshot used at booking time.
Racket detail includes its completed `service_history`; there is no separate
history endpoint.
Racket detail history includes only completed bookings for that racket.
The authenticated racket-model catalogue returns the six standard FYP
`key/brand/model` identities. Racket create/update accepts an optional
`model_key`: an unknown key returns `400`, a valid key makes the server's
canonical brand/model authoritative, and a custom model returns `model_key=null`
so recommendation uses global community evidence and no cross-model CF.
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

New external payment requests use `multipart/form-data` with either
`method=qr_transfer` or `method=cash`. QR transfer requires a JPG/PNG/WEBP
`proof` image up to 5 MB; cash requires neither QR configuration nor a proof.
Both start as `pending`. The admin endpoint verifies them as `paid`, `failed`,
or `cancelled`; QR responses include a short-lived `proof_url` for the
authenticated owner or admin. Historical card, online-banking, and e-wallet
records remain readable but are not accepted for new requests. Wallet top-up
credit is written only when the admin verifies the associated payment.

`POST /api/admin/store-settings/payment-qr` accepts a required `photo` image and
returns the updated settings with `payment_qr_url`. The delete endpoint clears
the active QR. New QR-transfer requests are rejected while no QR is configured.

`wallet_balance` booking payments use the same multipart route without a proof,
are server-validated against the persisted ledger, and complete immediately
only when sufficient balance exists.

The quote endpoint returns the server-owned current amount, wallet balance, and
any active payment so checkout never trusts a stale catalog snapshot.

### Strings

- `GET /api/strings`
- `POST /api/admin/strings/{id}/image`
- `DELETE /api/admin/strings/{id}/image`
- `GET /api/admin/inventory/strings`
- `GET /api/admin/inventory/strings/{id}`
- `PATCH /api/admin/inventory/strings/{id}`
- `PUT /api/admin/inventory/strings/{id}/editor`
- `GET /api/admin/strings/{id}/official-performance`
- `GET /api/admin/strings/{id}/recommendation-matrix`
- `POST /api/admin/recommendation-matrix/import`
- `GET /api/admin/business-hours`
- `PUT /api/admin/business-hours`
- `GET /api/slots`
- `GET /api/store-settings`
- `GET /api/admin/check-in/lookup`
- `POST /api/admin/check-in`
- `POST /api/admin/check-in/lookup`
- `POST /api/admin/check-in/confirm`
- `GET /api/admin/service-queue`
- `GET /api/admin/store-settings`
- `PUT /api/admin/store-settings`
- `POST /api/admin/store-settings/payment-qr`
- `DELETE /api/admin/store-settings/payment-qr`
- `GET /api/admin/analytics/summary`
- `GET /api/admin/analytics/popular-strings`

Only approved catalog strings from `backend/data/string_catalog_db_ready.json`
are exposed or updated. Admin catalog, official-performance, and inventory
changes use the atomic `/api/admin/inventory/strings/{id}/editor` endpoint.

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

Every public string response includes live `available_stock` and
`availability_status`, so player screens never infer inventory from catalog
activation.

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
  - each row exposes scoring values and optional evidence notes only

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

The default runtime import source is the independent MacBERT workbook at `../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx`; the protected V9 workbook is not merged or imported by default.

Store-ops responses add:

- business hours day configs in snake_case (`is_open`, `open_time`, `slot_duration_minutes`, `max_bookings_per_slot`)
- generated slot rows with `booked_count` and `available_spots`
- service queue lanes grouped by booking status
- single-store settings payloads for support/policy copy,
  `default_service_price`, notification templates, `trending_string_ids`, and
  optional `payment_qr_url`; player clients read these through
  `GET /api/store-settings`. QR upload/replace/delete is a separate admin
  multipart operation so text settings remain JSON
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

- `POST /api/recommendations/generate`
- `GET /api/recommendations/{user_id}`
- `GET /api/recommendations/{user_id}/{catalog_id}`
- `GET /api/admin/recommendations/runs`
- `GET /api/admin/recommendations/runs/{run_id}`

Generate recommendation request:

```json
{
  "top_n": 5
}
```

Recommendation response:

```json
{
  "algorithm_version": "fyp1_similarity_preferences_community_racket_cf_v11",
  "run_id": "recommendation-run-uuid",
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
        "supports your recent power goal",
        "fits your attacking playing style"
      ],
      "score_breakdown": {
        "preference_match": 0.82,
        "rule_fit": 0.61,
        "value_for_money": 0.68,
        "nlp_review_score": 0.71,
        "final_score": 0.84
      },
      "rationale_payload": {
        "algorithm_family": "community_calibrated_content_preferences",
        "community_calibration_used": true,
        "collaborative_filtering_used": false,
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
            "nlp_influence": 0.5
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
        "price_rm": 45.0,
        "profile_context": {
          "skill_level": "intermediate",
          "playing_style": "attacking",
          "preferred_feel": "medium",
          "preferred_gauge": "no_preference",
          "recent_goal": "power"
        },
        "rule_events": []
      },
      "generated_at": "2026-04-12T14:10:00+00:00"
    }
  ]
}
```

`value_for_money` is a review-derived feature and the ninth saved preference dimension. Catalog price is descriptive and does not affect ranking.

`nlp_review_score` is an explanation-facing score that shows how strongly review-derived matrix signals support the user's weighted priorities. It does not replace `preference_match` or change the final weighting formula.
The active FYP1 recommender is rule-enhanced content recommendation with fixed
official/NLP fusion and bounded, explicitly confirmed community-feedback
calibration. When `racket_id` is supplied, the racket must belong to the current
user. Racket-conditioned interaction-history CF is persisted as `cf_shadow` for
backward-compatible audit naming. It receives a non-zero weight only for a
candidate supported by at least three independent users on the exact normalized
racket model. Otherwise `cf_weight=0.0` and the v10 score is unchanged. Matrix
factorization, embeddings, review-count weighting, and historical catalog
community metrics are not ranking inputs.

`POST /api/recommendations/generate` uses the current authenticated user's saved profile, writes `user_preference_matrix`, caches the ranked rows in `recommendation_score_cache`, persists a historical run in `recommendation_runs` and `recommendation_run_items`, and returns the same response shape. The persisted `profile_snapshot` is the saved backend profile context, not just a copy of the request payload.

`GET /api/recommendations/{user_id}` returns the latest cached recommendation set. Customers may use their own user id or `me`; admins may inspect any user id.

`GET /api/recommendations/{user_id}/{catalog_id}` returns one cached recommendation result with the full rationale payload.
The returned `algorithm_version` is read from the cached recommendation row, not inferred from the currently deployed code version.

`GET /api/admin/recommendations/runs` returns persisted recommendation run history with item-level score rows.

`GET /api/admin/recommendations/runs/{run_id}` returns one persisted recommendation run with its full item-level score rows and rationale payloads.

### Grounded Player And Admin Agent

- `POST /api/agent/query`

This authenticated endpoint serves the player chatbot, recommendation
explanation page, and admin assistant. Recommendation explanation context requires
both the exact `run_id` and `catalog_id`; the backend rejects a run belonging to
another player.

```json
{
  "message": "Why was BG80 recommended to me?",
  "context": {
    "surface": "recommendation_explanation",
    "run_id": "recommendation-run-uuid",
    "catalog_id": "yonex-bg80"
  },
  "conversation_history": []
}
```

The response retains a validated answer, summary, evidence status, suggested
questions/actions, and a source list constructed by the backend. The reduced
mobile UI hides source and suggested-question chips, while server-side provenance
remains available for audit. DeepSeek output cannot supply or override the source
list, and resource actions with identifiers absent from verified data are dropped.

The active FYP player tools cover string details, V11 What-if previews, and
verified in-stock alternatives. Exact owned recommendation-run and string context
is preloaded by the backend for the explanation surface without exposing a
general run-lookup tool to the model. Guided previews may apply a temporary RM
budget and do not update the saved profile or recommendation cache. Completed
comparison, review, store, booking, latest-recommendation, and human-handoff code
remains preserved but inactive.

Provider configuration is server-only. With `AGENT_ENABLED=false` or a missing
key, the endpoint returns `503`; no model fallback invents an explanation.

An authenticated admin uses the same endpoint with:

```json
{
  "message": "Summarize today's operations.",
  "context": {"surface": "admin_assistant"},
  "conversation_history": []
}
```

Player and admin surfaces have separate role checks and tool allowlists. The
active admin allowlist exposes only the read-only current operations summary and
returns no actions. Completed booking, inventory, payment, and support lookup
tools plus booking-status, stock-count, and support-reply handlers remain
preserved behind commented inactive registrations. Re-enable all matching tool,
action, prompt, mobile, test, and documentation entries together.

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
