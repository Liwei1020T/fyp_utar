# Appendix E: Key Source Code Extracts

This appendix identifies representative code sections that are suitable for inclusion in the report. Full source code should not be pasted into the report; use short excerpts that demonstrate architecture, control flow, and important logic.

## Mobile Application

| Area | File | Suggested Lines / Function | Why Include |
| --- | --- | --- | --- |
| App bootstrap | `mobile/app/_layout.tsx` | `BackendSessionBootstrap`, root providers | Shows app initialization, HeroUI Native, native/current-tab session restoration, and `/auth/me` revalidation. |
| Role routing | `mobile/components/roles/RoleGuard.tsx` | `RoleGuard` | Demonstrates player/admin route protection. |
| Backend API client | `mobile/services/backendApi.ts` | `requestJson`, `requestFormJson`, `backendApi` methods | Shows typed frontend-backend communication and error handling. |
| Recommendation screen | `mobile/app/player/(tabs)/recommend.tsx` | `handleGenerate` | Shows how the mobile app triggers backend recommendation generation. |
| State management | `mobile/store/appStore.ts` | session, successful API snapshots, and transient drafts | Shows backend-authoritative writes without a mock business-data fallback. |

## Backend Application

| Area | File | Suggested Lines / Function | Why Include |
| --- | --- | --- | --- |
| FastAPI bootstrap | `backend/app/main.py` | app creation, middleware, exception handlers, health endpoint | Shows backend runtime setup. |
| API router | `backend/app/entrypoints/api/router.py` | router composition | Shows modular endpoint organization. |
| Recommendation scorer | `backend/app/domain/recommendation/scoring.py` | score weights and `score_candidates` | Shows the core algorithm. |
| Recommendation use case | `backend/app/use_cases/recommendation/generate_recommendation.py` | `_execute` | Shows orchestration, persistence, caching, and logging. |
| Booking policy | `backend/app/domain/booking/policies.py` | `BOOKING_STATUS_TRANSITIONS` | Shows business rule enforcement. |

## Suggested Code Extracts for Report

### Recommendation Score Weights

```python
FINAL_SCORE_WEIGHTS = {
    "preference_match": 0.60,
    "rule_fit": 0.15,
    "budget_fit": 0.15,
    "confidence_score": 0.10,
}
```

### Booking Status Transition Policy

```python
BOOKING_STATUS_TRANSITIONS = {
    "awaiting_dropoff": {"in_progress", "rejected", "cancelled"},
    "in_progress": {"ready_for_collection", "cancelled"},
    "ready_for_collection": {"completed"},
    "completed": set(),
    "cancelled": set(),
    "rejected": set(),
}
```

### Mobile Recommendation Trigger

```typescript
const response = await backendApi.generateRecommendations(token, 3);
setLiveRecommendationResults(
  mapRecommendationResponse(response, availableStrings),
);
router.push('/player/results');
```

## Notes

- Keep excerpts short.
- Do not include secrets, `.env` values, generated caches, or full source files.
- Use screenshots plus code excerpts together: screenshots prove UI behavior, while code excerpts prove implementation logic.
