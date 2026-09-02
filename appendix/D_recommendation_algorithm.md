# Appendix D: Recommendation Algorithm

This appendix describes the current runtime recommender. The original FYP1
claim boundary is retained at the end; it must not be confused with the
current FYP2 feedback, personal-history, and racket-conditioned evidence layers.

Source files:

- `backend/docs/recommendation-design.md`
- `backend/app/domain/recommendation/scoring.py`
- `backend/app/use_cases/recommendation/generate_recommendation.py`
- `ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx`

## Algorithm Version

`fyp1_weighted_preferences_feedback_racket_cf_personal_v14`

## Input Features

User-side profile inputs:

- `skill_level`
- `playing_style`
- `preferred_tension`
- `frequency_per_week`
- `preferred_feel`
- `preferred_gauge`
- `recent_goal`
- `pref_attack`, `pref_control`, `pref_durability`, `pref_comfort`
- `pref_sound`, `pref_elasticity`, `pref_tension_retention`
- `pref_string_movement`, `pref_value_for_money`

Item-side inputs:

- official/manual performance values from `string_official_performance`;
- the independent 12-string MacBERT review matrix in
  `string_recommendation_matrix` with `source_layer='nlp_review'`;
- approved catalog and inventory fields such as gauge, price, stock, and
  availability.

Only the 12 IDs in `config/approved_string_cohort_v1.csv` are active
recommendation candidates.

## Core Recommendation Dimensions

The preference vector has nine dimensions:

| Feature Key | Meaning |
| --- | --- |
| `repulsion` | Power and rebound |
| `control` | Control and touch |
| `durability` | Durability |
| `comfort` | Comfort |
| `sound` | Hitting sound |
| `elasticity` | Elastic rebound |
| `tension_retention` | Tension retention |
| `string_movement` | String movement control |
| `value_for_money` | Value signal |

Raw player sliders are normalized as:

```text
weight_i = raw_score_i / sum(all_raw_scores)
```

## Score Layers

The base score is:

```text
BaseScore = (0.75 * PreferenceMatch + 0.15 * RuleFit) / 0.90
```

- `PreferenceMatch` is the preference-weighted mean of effective item feature
  values.
- Official and `nlp_review` values use fixed, inspectable fusion; a missing
  source falls back to the available source or the feature prior.
- `RuleFit` applies profile-context rules for skill, style, tension, frequency,
  gauge, feel, and recent goal.
- Price is descriptive. There is no active `budget_fit_score` ranking field.
  The Agent may apply a temporary RM budget filter during a What-if preview.

The base score then receives two bounded evidence layers:

1. The current player's completed-booking feedback is applied as a separate
   personal-history rerank, preferring the exact physical racket, then exact
   racket model, then global string history.
2. Racket-conditioned collaborative evidence can blend into the result only
   after at least three independent supporters exist for the exact normalized
   racket model. Sparse cases keep the base score unchanged.

The rationale records the base score, personalized score, final score, support
counts, fallback reason, and the evidence snapshot versions used for the run.

## Explainability Output

Each persisted profile result includes:

- rank and final score;
- score breakdown and top reasons;
- effective feature scores and source evidence;
- user preference vector;
- feedback and personal-history evidence when actually used;
- racket context and collaborative support when actually used;
- algorithm version and rationale payload.

## Persistence Boundary

- `POST /api/recommendations/generate` reads the saved profile, writes
  `user_preference_matrix`, replaces the user's `recommendation_score_cache`,
  and persists `recommendation_runs` plus `recommendation_run_items`.
- The internal Agent `execute_preview` path returns an ephemeral `run_id` for
  the current answer only. It writes no run, run item, cache, preference
  vector, or profile change.
- Admin recommendation history therefore contains persisted profile-generation
  audits only, not What-if previews.

## Important FYP1 Claim Boundary

For the original FYP1 report, describe the system as a rule-enhanced,
content-based recommender using player preference weights, official/manual
signals, and review-derived item features. Do not use this appendix as evidence
of human-ground-truth accuracy, expert Gold labels, or production ranking
effectiveness. The current FYP2 evidence layers do not change that academic
claim boundary.
