# Appendix D: Recommendation Algorithm

The FYP1 recommender is a rule-enhanced, confidence-aware, content-based recommendation module. It uses player preference weights, official/manual performance signals, NLP review-derived feature signals, rule fit, budget fit, and confidence scoring.

Source files:

- `backend/docs/recommendation-design.md`
- `backend/app/domain/recommendation/scoring.py`
- `backend/app/use_cases/recommendation/generate_recommendation.py`
- `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`

## Algorithm Version

`fyp1_similarity_confidence_rule_budget_tier_v5`

## Input Features

User-side profile inputs:

- `skill_level`
- `playing_style`
- `budget_tier`
- `preferred_tension`
- `game_type`
- `frequency_per_week`
- `pref_attack`
- `pref_control`
- `pref_durability`
- `pref_comfort`
- `pref_sound`
- `pref_elasticity`
- `pref_tension_retention`
- `pref_string_movement`
- `pref_value_for_money`

Item-side feature inputs:

- Official/manual performance values from `string_official_performance`
- NLP/review matrix values from `string_recommendation_matrix`
- Catalog and inventory fields such as gauge, price, stock, and active status

## Core Recommendation Dimensions

The main feature space contains eight dimensions:

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

## Preference Vector

Raw user sliders are normalized into weights:

```text
weight_i = raw_score_i / sum(all_raw_scores)
```

This allows the recommender to compare the shape of the user's preferences against each string's feature profile.

## Final Score Formula

```text
FinalScore =
  0.60 * PreferenceMatch
+ 0.15 * RuleFit
+ 0.15 * BudgetFit
+ 0.10 * ConfidenceScore
```

Where:

- `PreferenceMatch` compares user preference weights with effective item feature scores.
- `RuleFit` applies badminton-specific rules based on skill, tension, playing style, frequency, and gauge.
- `BudgetFit` checks whether the string price matches the user's selected budget tier.
- `ConfidenceScore` estimates reliability based on source coverage, fusion confidence, NLP influence, and fallback usage.

## Explainability Output

Each generated recommendation stores:

- Rank
- Final score
- Score breakdown
- Top reasons
- Effective feature scores
- Feature source evidence
- NLP review signals
- User preference vector
- Matrix version
- Algorithm version

## Important FYP1 Claim Boundary

This FYP1 recommender is not deployed collaborative filtering and not deep-learning ranking. It should be described as content-based recommendation enhanced with rules, confidence scoring, and NLP/review-derived item features.

