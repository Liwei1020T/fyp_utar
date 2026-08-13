# Recommendation Design (FYP1)

## 1. Scope

This document describes the current recommendation runtime in `backend/app/domain/recommendation/scoring.py`.

Algorithm version:

- `fyp1_similarity_preferences_community_racket_cf_v11`

Design style:

- Content-based scoring as the main signal
- Rule-based adjustments for profile-context constraints
- Gauge, feel, tension, frequency, and recent-goal rule adjustments
- Fixed official/NLP feature fusion without confidence or review-count weighting
- Bounded structured-feedback calibration, preferring exact racket-model evidence
- Racket-conditioned collaborative filtering with a three-user activation gate

Collaborative evidence is observable and persisted. It receives a non-zero,
shrunk weight only when one candidate has at least three independent supporting
users on the exact normalized racket model. Sparse cases preserve the v10 score.

## 2. End-to-End Runtime Flow

```mermaid
flowchart TD
    A[Client Request: preview/profile] --> B[GenerateRecommendationUseCase]
    B --> C[Load Owned Racket Context]
    C --> D[Build Community Snapshot + CF Shadow]
    D --> E[Load String Item + Official Performance + Matrix Entries]
    E --> F[Fyp1ContentRecommendationScorer]
    F --> G[Per-Candidate Scoring]
    G --> H[Rank + Top N]
    H --> I[Persist Run + Log]
    I --> J{Request Type}
    J -->|profile| K[Persist Preference Vector + Score Cache]
    J -->|preview| L[Skip Profile Persistence]
    K --> M[API Response]
    L --> M
```

Primary orchestration lives in `app/use_cases/recommendation/generate_recommendation.py`.

## 3. Data Inputs and Signal Layers

### 3.1 User-side inputs

- Profile context: `skill_level`, `playing_style`, `preferred_tension`, `frequency_per_week`, `preferred_feel`, `preferred_gauge`, and `recent_goal`.
- Preference sliders (1-10): `pref_attack`, `pref_control`, `pref_durability`, `pref_comfort`, `pref_sound`, `pref_elasticity`, `pref_tension_retention`, `pref_string_movement`, `pref_value_for_money`.

Note:

- `pref_value_for_money` is the ninth dimension in the normalized preference vector used by `PreferenceMatch`.

### 3.2 Item-side inputs

- Official/manual performance (`string_official_performance`) for core dimensions.
- Matrix rows (`string_recommendation_matrix`) by `source_layer`, especially:
    - `nlp_review` (primary matrix source used by core-feature fusion)
    - `hybrid_derived` (used in auxiliary/support feature fallback)
    - `community_signal` (optional auxiliary/support feature fallback)
    - `catalog_structured` (metadata-oriented; generally not used directly in core content fusion)

### 3.3 Feature mapping note

- CSV `attack` is mapped into runtime feature key `repulsion`.
- This is why "power" behavior is represented through `repulsion` in scorer logic.

## 4. Content-Based Design

### 4.1 Core feature space

Content matching is built around 9 core dimensions:

- `repulsion`
- `control`
- `durability`
- `comfort`
- `sound`
- `elasticity`
- `tension_retention`
- `string_movement`
- `value_for_money`

### 4.2 Preference vector construction

Raw user sliders are normalized into preference weights:

$$
w_i = \frac{r_i}{\sum_j r_j}
$$

Where:

- $r_i$ is the raw slider value for core feature $i$
- $w_i$ is the normalized preference weight

### 4.3 Fixed per-feature fusion

For each core feature, scorer combines official signal, NLP signal, and prior fallback without evidence-confidence metadata.

```mermaid
flowchart LR
    A[Core Feature k] --> B{Official Score Exists?}
    A --> C{NLP Score Exists?}
    B -->|Yes| D[official_value]
    C -->|Yes| E[nlp_value]
    D --> F{Both Exist?}
    E --> F
    F -->|Yes| G[Equal Average]
    F -->|One Only| H[Use Available Source]
    F -->|Neither| I[Use Prior]
    G --> J[effective_score]
    H --> J
    I --> J
```

High-level behavior:

- If official and NLP both exist: equal average.
- If only one side exists: use that side directly.
- If both missing: fallback to feature prior.

Official coverage caveat:

- Official mapping currently covers 5 core dimensions directly: `repulsion`, `comfort`, `control`, `durability`, `sound`.
- `elasticity`, `tension_retention`, and `string_movement` mainly rely on NLP matrix signals or prior fallback.

Catalog review counts are not recommendation inputs.

### 3.4 Runtime learning signals

- Explicitly confirmed structured feedback is averaged per user before aggregation.
- Exact normalized racket-model evidence is preferred; global string evidence is
  the fallback. Influence is shrunk with `K=10` and capped at `0.30` per feature.
- Completed bookings from similar users on the exact racket model produce a
  tension-aware CF shadow score. Its runtime weight remains `0.0`.
- Snapshot/source hashes are stored in rationale and checked on cached reads.

### 4.4 PreferenceMatch calculation

PreferenceMatch combines:

- weighted shape similarity between user vector and item feature shape
- top-priority feature alignment

High-level composition:

$$
\text{PreferenceMatch} = 0.75 \cdot \text{ShapeSimilarity} + 0.25 \cdot \text{TopAlignment}
$$

## 5. Rule-Based Design

RuleFit starts from baseline `0.55` and applies incremental deltas based on profile context and item behavior.

### 5.1 Rule categories

1. Skill-level rules
2. Frequency rules
3. Tension rules
4. Playing-style rules
5. Preferred feel, preferred gauge, and structured recent-goal rules

### 5.2 Rule table (current runtime)

| Category | Condition | Delta |
| --- | --- | --- |
| Gauge context | beginner without tension/frequency override and thin gauge | +0.07 |
| Gauge context | tension <= 23, tension >= 27, or frequency >= 3 and thick gauge | +0.07 |
| Preferred gauge | exact match / mismatch | +0.05 / -0.025 |
| Preferred feel | soft/medium/hard exact match / mismatch | +0.06 / -0.03 |
| Beginner | (comfort + durability)/2 >= 0.65 | +0.06 |
| Frequent play | frequency_per_week >= 3 and durability < 0.50 | -0.08 |
| Frequent play | frequency_per_week >= 3 and durability >= 0.68 | +0.05 |
| High tension | preferred_tension >= 27 and tension_retention >= 0.68 | +0.06 |
| High tension | preferred_tension >= 27 and tension_retention < 0.55 | -0.06 |
| Low tension | preferred_tension <= 23 and comfort >= 0.66 | +0.04 |
| Attacking style | 0.6*repulsion + 0.4*elasticity >= 0.72 | +0.07 |
| Attacking style | repulsion < 0.55 | -0.05 |
| Control style | 0.55*control + 0.45*string_movement >= 0.68 | +0.07 |
| Control style | string_movement < 0.50 | -0.05 |
| Balanced style | mean(repulsion, control, durability, comfort, elasticity, tension_retention, string_movement) >= 0.66 | +0.05 |
| Recent goal | selected feature >= 0.68 / <= 0.48 | +0.06 / -0.04 |

All deltas are clamped into `[0,1]` after each update.

### 5.3 Rule decision map

```mermaid
flowchart TD
    A[RuleFit baseline = 0.55] --> B{Skill Level}
    B -->|beginner| C[Gauge + Comfort/Durability checks]
    B -->|other| D[Skip beginner rules]
    C --> E{Frequency >= 3}
    D --> E
    E --> F[Durability checks]
    F --> G{Preferred Tension}
    G --> H[High/Low tension checks]
    H --> I{Playing Style}
    I --> J[Attacking or Control or Balanced checks]
    J --> K{Feel, gauge, recent goal}
    K --> L[Soft preference checks]
    L --> M[Final RuleFit]
```

## 6. Setup Preference Design

Gauge, feel, and recent goal are RuleFit inputs. They add a bounded bonus or
penalty but never filter candidates.

- Gauge categories: thin `<= 0.64 mm`, medium `<= 0.67 mm`, otherwise thick.
- Setup context prefers thick gauge at `<= 23 lbs`, `>= 27 lbs`, or at least
  three sessions per week; otherwise beginner prefers thin gauge.
- Official feel values map to soft `<= 4`, medium `<= 6.5`, otherwise hard.
- Recent goal is one of balanced, power, control, durability, comfort,
  tension retention, or value for money.

Catalog price remains available for display but is not a ranking input.

## 8. Final Score and Ranking

Final score preserves the previous 5:1 preference-to-rule ratio and normalizes
the two ranking components back to the 0-to-1 range:

$$
\text{FinalScore} =
\frac{0.75 \cdot \text{PreferenceMatch}
+ 0.15 \cdot \text{RuleFit}}{0.90}
$$

Ranking is then sorted by:

1. `FinalScore` descending
2. `brand`
3. `model_name` (or fallback to display name)

Top `N` is returned.

## 9. Explainability and Persistence

For each result, scorer stores:

- score breakdown (`preference_match`, `rule_fit`, descriptive `value_for_money`, optional `nlp_review_score`)
- top reasons and rule events
- feature evidence rows with official value, NLP value, fixed NLP contribution, and effective score
- community scope, counts, bounded weight, and source/snapshot versions
- selected racket context and gated CF evidence with base/final score audit fields

Persistence behavior by request type:

- Always persisted (preview and profile):
    - recommendation run snapshots (`recommendation_runs`, `recommendation_run_items`)
    - recommendation log payloads (`recommendation_logs`)
- Profile only:
    - normalized user preference vector (`user_preference_matrix`, source `profile`)
    - per-item score cache (`recommendation_score_cache`)

## 10. Design Summary

The current design is a hybrid recommender:

- Content-based is the primary decision engine
- Rule-based enforces profile-aware domain constraints
- Value for money is a first-class weighted preference
- Official and NLP feature values use fixed, inspectable fusion
- Eligible community feedback calibrates features within a fixed bound
- Racket-conditioned CF is auditable and affects ranking only after its support gate

This keeps recommendations explainable, tunable, and stable for FYP use while still allowing NLP-derived signals to improve personalization dynamically.
