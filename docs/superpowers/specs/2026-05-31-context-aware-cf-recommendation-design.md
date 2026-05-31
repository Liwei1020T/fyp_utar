# Context-Aware CF Recommendation Design

## 1. Goal

Upgrade the StringSence recommendation design from the current FYP1
content-and-rules recommender into a thesis-ready and implementation-ready
hybrid recommender.

The upgraded recommendation module should combine:

- content-based scoring from string features, review-derived feature signals,
  and official performance data
- badminton-specific rule scoring
- context-aware item-based collaborative filtering from completed booking
  history
- racket brand/model similarity
- preferred and historical tension fit

This is a recommendation-system and classical machine-learning design. It is not
deep learning unless a future neural collaborative filtering model is added.
BERT remains part of review understanding and feature extraction, not the CF
algorithm itself.

## 2. Current Baseline

The current runtime recommender is an explainable, rule-enhanced,
confidence-aware content-based recommender.

Current baseline signals:

- user profile fields and preference sliders
- string feature matrix entries, especially review-derived NLP matrix rows
- official/manual string performance values
- badminton domain rules
- budget fit
- evidence confidence

Current recommendation persistence already records recommendation runs, run
items, request snapshots, profile snapshots, score breakdowns, user preference
vectors, and cached recommendation scores.

The upgrade should not replace this baseline. It should add a behavior-learning
layer that only becomes active when enough completed booking history exists.

## 3. Formal Positioning

Recommended thesis wording:

> The recommendation module adopts a hybrid architecture combining
> content-based filtering, rule-based badminton domain constraints, and
> context-aware item-based collaborative filtering based on completed booking
> history.

Short name:

> Hybrid Recommendation with Context-Aware Item-Based Collaborative Filtering

This means:

- `content-based` explains whether a string's features match the user's stated
  preferences
- `rule-based` applies domain constraints such as skill level, play style,
  budget, and tension behavior
- `collaborative filtering` learns from completed booking history across users
- `context-aware` means CF support is adjusted by user preference similarity,
  racket brand/model similarity, and tension fit

## 4. Data Signals

Only completed bookings are used as CF training behavior.

Valid behavior signal:

```text
booking.status = completed
```

Excluded statuses:

```text
awaiting_dropoff
in_progress
ready_for_collection
cancelled
rejected
```

Each completed booking contributes:

```text
user_id
catalog_id / string_id
racket_brand
racket_model
requested_tension
created_at
updated_at or completion timestamp if available
```

Profile data remains important, but it is used as preference/context data rather
than as the primary CF interaction:

```text
skill_level
playing_style
budget_tier
preferred_tension
pref_attack
pref_control
pref_durability
pref_comfort
pref_elasticity
pref_sound
pref_string_movement
pref_tension_retention
pref_value_for_money
```

## 5. User Preference Similarity

CF support should be weighted by how similar another user's profile is to the
current user's profile.

Preference similarity uses the full profile preference:

```text
PreferenceSimilarity(current_user, other_user) =
  0.50 * SliderVectorSimilarity
+ 0.20 * PlayingStyleMatch
+ 0.15 * SkillLevelMatch
+ 0.10 * TensionPreferenceSimilarity
+ 0.05 * BudgetTierMatch
```

Slider vector dimensions:

```text
pref_attack
pref_control
pref_durability
pref_comfort
pref_elasticity
pref_sound
pref_string_movement
pref_tension_retention
```

`pref_value_for_money` can remain a budget/value context signal instead of part
of the eight-dimensional core similarity vector.

## 6. Item-Based Collaborative Filtering

The CF layer is item-based.

Base interaction matrix:

```text
interaction(user, string) = 1
if the user has at least one completed booking for that string
```

Item similarity can be computed with Jaccard or cosine similarity over completed
booking users.

Conceptually:

```text
ItemSimilarity(string_A, string_B) =
similarity between users who completed A and users who completed B
```

For a current user and candidate string:

```text
UserHistoryItemSimilarity(candidate_string) =
similarity between candidate_string
and strings completed by the current user
```

Preference-weighted CF support:

```text
PreferenceWeightedCFScore(candidate_string) =
weighted support from users who completed candidate_string,
where each supporting user is weighted by PreferenceSimilarity
to the current user
```

This prevents the CF layer from over-recommending generally popular strings that
were completed by users with very different preferences.

## 7. Racket Similarity

Racket similarity is based on booking text fields only. No racket metadata
database is required for the first implementation.

Normalized comparison:

```text
same normalized brand + exact normalized model      = 1.00
same brand + high model text similarity             = 0.80
same brand only                                     = 0.45
missing / different                                 = 0.00
```

This signal is used as context. It should not override the content/rule baseline
or CF support by itself.

## 8. Tension Fit

Tension fit uses both stated profile preference and completed booking history.

Effective tension:

```text
EffectiveTension =
  history_weight * MedianCompletedBookingTension
+ (1 - history_weight) * ProfilePreferredTension
```

Suggested history weights:

```text
0 completed bookings  -> 0.00
1 completed booking   -> 0.40
2 completed bookings  -> 0.60
3+ completed bookings -> 0.75
```

Candidate tension fit should be high when `EffectiveTension` is inside or near
the recommended tension range for the string. If explicit recommended tension
range is unavailable, use tension-retention feature evidence and confidence as a
fallback.

## 9. Final Scoring

The new scoring layer should blend with the current content-and-rules baseline.

Conceptual score:

```text
FinalScore =
  0.45 * ExistingContentRuleScore
+ 0.25 * PreferenceWeightedCFScore
+ 0.10 * UserHistoryItemSimilarity
+ 0.10 * RacketSimilarityScore
+ 0.10 * TensionFitScore
```

`ExistingContentRuleScore` represents the current recommender's final
content/rule/budget/confidence score before CF is applied.

The exact weights can be tuned during implementation, but the principle should
remain:

- content and rules stay the stable baseline
- CF adds behavior learning
- racket and tension are context signals
- cold-start users should still receive useful recommendations

## 10. Cold-Start And Fallback

The CF/context weights must reduce when evidence is insufficient.

Recommended fallback behavior:

```text
No completed booking history:
  CF weights = 0
  racket history weight = 0
  tension uses profile preferred_tension
  return weight to ExistingContentRuleScore

Some completed booking history:
  enable tension history gradually
  enable user-history item similarity
  enable preference-weighted CF only if enough other-user support exists

Insufficient similar users:
  lower PreferenceWeightedCFScore confidence
  use content/BERT feature similarity as fallback
```

This keeps the recommender reliable for new users and small FYP datasets.

## 11. Explanation And Admin Audit

Player-facing explanations should stay simple.

Example player explanation:

> Recommended based on your saved preferences, completed stringing history,
> similar player preferences, racket model, and preferred tension.

Admin audit should expose detailed scoring evidence through the existing
recommendation-run audit flow:

```text
content_rule_score
preference_weighted_cf_score
user_history_item_similarity
racket_similarity_score
tension_fit_score
confidence_score
final_score
cf_neighbor_count
completed_booking_count
similar_user_count
fallback_used
```

The recommendation rationale should also record whether the CF layer was used.

## 12. Evaluation

Recommended evaluation metrics:

```text
Top-K Hit Rate:
  whether the user's completed booking string appears in the recommendation top K

Booking Conversion Match:
  whether a completed booking came from a previously recommended string

Cold-Start Handling:
  whether recommendations remain available without completed booking history

Explainability Coverage:
  whether each recommendation has content/rule/CF/context breakdowns

Admin Auditability:
  whether admin can inspect scoring evidence and fallback state
```

For FYP demonstration, the easiest outcome to explain is:

> After a user completes more bookings, the recommendation ranking changes based
> on users with similar preferences, racket model context, and tension behavior.

## 13. Implementation Boundaries

In scope for implementation planning:

- derive CF and context signals from completed bookings
- compare full profile preferences across users
- compute item-based CF support
- compute racket brand/model text similarity
- compute effective tension and tension fit
- blend new scores with the current recommender
- store score breakdowns in recommendation rationale/cache
- expose detailed breakdowns to admin audit

Out of scope:

- neural collaborative filtering
- deep learning ranking
- new full racket metadata database
- training CF from incomplete bookings
- treating cancelled or rejected bookings as positive behavior
- replacing the current content/rule scorer

## 14. Design Summary

The upgraded recommendation design is:

```text
Hybrid Recommendation =
  Content-Based Filtering
+ Rule-Based Domain Scoring
+ Preference-Weighted Item-Based Collaborative Filtering
+ Racket Model Context
+ Tension Fit Context
+ Cold-Start Fallback
```

This design lets StringSence claim a classical machine-learning recommender
component through collaborative filtering while preserving the explainability and
stability of the current FYP1 content-and-rules recommendation runtime.
