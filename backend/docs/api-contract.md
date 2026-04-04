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
- `GET /api/v1/health`

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

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

### Profile

- `GET /api/v1/profile`
- `PUT /api/v1/profile`

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

- `GET /api/v1/strings`
- `GET /api/v1/strings/{id}`
- `GET /api/v1/admin/strings`
- `POST /api/v1/admin/strings`
- `PUT /api/v1/admin/strings/{id}`
- `DELETE /api/v1/admin/strings/{id}`

Only approved catalog strings can be created or updated.

### Recommendations

- `POST /api/v1/recommendations/preview`
- `POST /api/v1/recommendations/profile`
- `GET /api/v1/admin/recommendations/logs`

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
  "algorithm_version": "unified_python_rule_engine_v1",
  "results": [
    {
      "rank": 1,
      "string_name": "Yonex BG80",
      "brand": "Yonex",
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
        "Matches your attacking playing style",
        "Falls within your budget range",
        "Strong sound and elasticity scores"
      ]
    }
  ]
}
```

### Bookings

- `POST /api/v1/bookings`
- `GET /api/v1/bookings`
- `GET /api/v1/bookings/{id}`
- `GET /api/v1/admin/bookings`
- `GET /api/v1/admin/bookings/{id}`
- `PATCH /api/v1/admin/bookings/{id}/status`

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
