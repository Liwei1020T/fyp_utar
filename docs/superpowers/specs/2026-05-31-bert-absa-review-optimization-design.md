# BERT ABSA Review Optimization Design

## Status

Approved for planning.

## Goal

Improve badminton string review understanding and recommendation reliability by
adding a raw-first, BERT-enhanced ABSA pipeline. The pipeline should produce a
backend-compatible recommendation matrix while preserving the current
confidence-aware backend recommender.

The primary outcome is a repeatable FYP-ready workflow:

1. Load raw badminton string reviews.
2. Build better preprocessing and annotation data.
3. Train and evaluate two-stage Chinese BERT/MacBERT ABSA models.
4. Generate a `v10` hybrid recommendation matrix.
5. Compare review understanding and recommendation output against existing
   rule/TF-IDF/v9 baselines.

## Current Context

The active recommendation runtime imports review-derived features from:

- `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`

The backend imports that matrix into `string_recommendation_matrix` with
`source_layer="nlp_review"`. The scorer then fuses NLP review scores with
official performance, feature priors, budget fit, rules, and confidence.

The new work should not rewrite the backend recommender. It should improve the
offline ABSA layer and keep the output compatible with the existing importer.

## Important Inputs

### Raw Source

- `ml/nlp-workbench-latest/data/archive_latest/badminton_strings_data.json`

This is the source of truth for raw review text and metadata. It contains 33
strings and 22,250 reviews.

Use these fields:

- string metadata: `eid`, `name`, `brand`, `series`, `rating`, `price`, `gauge`,
  `material`, `source_url`
- review metadata: `review_id`, `content`, `rating_label`, `likes`, `comments`,
  `not_helpful`, `review_date`, `source_url`, `full_review_url`

Do not export personal fields such as `username` or `user_profile_url` into
training artifacts, reports, or model outputs.

### Weak Labels

- `ml/nlp-workbench-latest/data/nlp_absa_high_confidence_latest.csv`

This file is the main weak-label training source. It contains high-confidence
`not_mentioned`, `positive`, and `negative` rows with `needs_manual_review=0`.

### Difficult-Case Pool

- `ml/nlp-workbench-latest/data/nlp_absa_long_dataset_latest.csv`

This file is the sampling pool for difficult cases and the manual gold set. It
includes `mentioned`, `mixed`, and `needs_manual_review=1` rows that should not
be blindly treated as high-confidence training labels.

### Preprocessing Resources

- `ml/nlp-workbench-latest/data/domain_dictionary_optimized_v8.csv`
- `ml/nlp-workbench-latest/data/normalization_rules_v8.csv`

Use these as the starting domain vocabulary and normalization rules. The v8
dictionary has 320 terms across 9 aspects, and the v8 normalization file has 27
rules.

### Baselines

- `ml/nlp-workbench-latest/data/latest_tfidf_string_feature_matrix.csv`
- `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`

Use these for matrix-level and recommendation-level before/after comparison.

### Backend Compatibility Inputs

- `backend/data/string_catalog_db_ready.json`
- `backend/app/adapters/persistence/sqlalchemy/recommendation_matrix_import.py`
- `backend/tests/test_recommendation_matrix_import.py`

The v10 matrix must match all 33 catalog items. Current raw JSON, v9 workbook,
and backend catalog review counts align.

## Data And Annotation Design

Create a manual gold set of 900 to 1,500 review-aspect samples.

Use stratified sampling across all 9 aspects:

- `attack`
- `comfort`
- `control`
- `durability`
- `elasticity`
- `sound`
- `string_movement`
- `tension_retention`
- `value_for_money`

Each aspect should include:

- clear positive examples
- clear negative examples
- mixed examples
- not-mentioned examples
- difficult cases with negation, contrast, metaphor, tension/price references,
  or aspect overlap

Use two-stage gold labels:

- `gold_mentioned`: `yes` or `no`
- `gold_sentiment`: `positive`, `negative`, `mixed`, or `neutral`

`gold_sentiment` is required only when `gold_mentioned=yes`.

The gold set is for validation, test reporting, and error analysis. The main
training set can use weak labels, but model claims should be reported on the
manual gold set.

Suggested path:

- `ml/nlp-workbench-latest/annotations/absa_gold_set_v1.csv`

## Preprocessing Design

Build preprocessing from raw reviews, not from already-expanded ABSA CSV rows.

The preprocessing layer should:

- normalize whitespace, repeated punctuation, full-width/half-width variants,
  and common typo variants
- preserve meaningful sentiment and aspect cues such as `不`, `没`, `无`, `太`,
  `很`, `有点`, `稍微`, `但是`, and `不过`
- protect brand/model tokens such as `BG80`, `BG-80`, `66UM`, `EXBOLT`, and
  `AEROBITE`
- apply `normalization_rules_v8.csv`
- use `domain_dictionary_optimized_v8.csv` for vocabulary, evidence extraction,
  and hybrid fallback
- split clauses by punctuation and contrast words such as `但是`, `但`, `不过`,
  `然而`, `只是`, and `可惜`
- emit diagnostic tags such as `has_negation`, `has_contrast`, `has_tension`,
  `has_price`, `has_metaphor`, and `has_multiple_aspects`

BERT input should be aspect-aware:

```text
评论：<normalized review or clause>
方面：<Chinese aspect description + aspect key>
```

## Model Design

Use a two-stage Chinese BERT/MacBERT ABSA design.

Recommended model:

- `hfl/chinese-macbert-base`

Execution split:

- local machine: small smoke test for data loading, preprocessing, inference,
  and matrix generation
- Colab/Kaggle: full GPU training and evaluation

### Task A: Aspect Mention Detection

Input:

- normalized review or clause
- aspect prompt

Output:

- `mentioned=yes/no`

Training labels:

- high-confidence `positive` and `negative` -> `mentioned=yes`
- high-confidence `not_mentioned` -> `mentioned=no`
- `mentioned` and `mixed` from the long CSV should mainly feed the gold/difficult
  pool unless manually verified

Controls:

- split by `review_id` group to avoid leakage
- downsample or class-weight the dominant `not_mentioned` class
- report accuracy, macro F1, mentioned F1, and per-aspect F1

### Task B: Aspect Sentiment Classification

Input:

- normalized review or clause
- aspect prompt
- only samples with `mentioned=yes`

Output:

- `positive`, `negative`, `mixed`, or `neutral`

Training labels:

- first version uses high-confidence positive/negative weak labels
- mixed and neutral quality comes from manual gold set and difficult-case review

Controls:

- report macro F1 and per-class F1
- report per-aspect sentiment F1
- inspect confusion between overlapping aspects such as `attack` and
  `elasticity`, or `durability` and `tension_retention`

## Hybrid Decision Design

The BERT model should not discard the existing dictionary/rule layer.

Hybrid behavior:

- BERT and dictionary agree: increase confidence
- BERT high confidence, dictionary silent: accept BERT as model-only evidence
- dictionary high confidence, BERT low confidence: keep rule fallback
- BERT and dictionary conflict: lower confidence and write an error-analysis row
- mixed evidence: pull score toward the middle and reduce confidence

Weight aggregation by:

- BERT probability
- log-scaled `likes`
- optional recency signal from `review_date`
- dictionary agreement
- consistency among reviews for the same string/aspect

## Review-Count Policy

Keep all 33 strings in the v10 matrix and backend import.

Use review-count-aware confidence:

- `review_count >= 100`: core evaluation set, normal NLP confidence
- `review_count < 100`: low-evidence set, NLP confidence discounted and fallback
  used more aggressively

Current low-evidence strings:

- `JS-69`: 81 reviews
- `JS-67`: 78 reviews
- `雷鸣69`: 44 reviews

Main FYP recommendation comparison should report the 30-string core set with
`review_count >= 100`. The 3 low-evidence strings remain in catalog and matrix
outputs but are excluded from headline metrics or clearly marked as low
evidence.

An optional stricter analysis can report the 22-string subset with
`review_count >= 200`.

## Matrix Generation Design

Generate:

- `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v10_bert_hybrid.xlsx`

Keep v9-compatible columns:

- `string_id`
- `string_name`
- `brand`
- `series`
- `gauge_mm`
- `material`
- `price_rm`
- `rating`
- `review_count`
- `budget_tier`
- `source_url`
- `attack`
- `comfort`
- `control`
- `durability`
- `elasticity`
- `sound`
- `string_movement`
- `tension_retention`
- `value_for_money`
- `<aspect>_100`
- `<aspect>_confidence`
- `<aspect>_review_raw`

Add analysis columns where useful. The backend importer ignores unknown columns:

- `<aspect>_mentions`
- `<aspect>_positive`
- `<aspect>_negative`
- `<aspect>_mixed`
- `<aspect>_evidence`
- `<aspect>_fallback`

Special handling:

- `attack` remains the matrix column name; backend maps it to runtime
  `repulsion`
- `string_movement` must score "less movement / does not run" as better
- `tension_retention` must score `掉磅快` as negative and `保磅好` as positive
- `value_for_money` should combine review sentiment with price/affordability
- low evidence should fall back to v9, official scores, or priors with lower
  confidence

## Backend Integration Design

Do not rewrite the backend scorer.

Integration steps:

1. Generate the v10 workbook.
2. Import it through the existing admin import path or by setting
   `RECOMMENDATION_MATRIX_SOURCE_PATH`.
3. Confirm all 33 rows match backend catalog items.
4. Add or adjust a backend import test for the v10 workbook.
5. Compare recommendation runs against v9 using existing admin run-audit pages.

Expected backend checks:

- `matched_strings = 33`
- `unmatched_strings = 0`
- `source_layer = "nlp_review"`
- core features and support features are imported for all catalog rows

## Evaluation Design

### ABSA Evaluation

Compare on the manual gold set:

1. rule-based labels
2. TF-IDF baseline
3. BERT/MacBERT
4. BERT + dictionary hybrid

Mention metrics:

- accuracy
- macro F1
- mentioned F1
- per-aspect F1

Sentiment metrics:

- macro F1
- positive/negative/mixed/neutral F1
- per-aspect sentiment F1
- confusion matrix

### Matrix Evaluation

Compare:

- v9 practical matrix
- TF-IDF matrix
- v10 BERT hybrid matrix

Outputs:

- `ml/nlp-workbench-latest/output/bert_absa_v1/matrix_comparison.csv`
- `ml/nlp-workbench-latest/output/bert_absa_v1/aspect_shift_report.csv`

Track:

- score deltas
- confidence deltas
- evidence counts
- positive/negative/mixed counts
- fallback ratio

### Recommendation Evaluation

Use fixed player profiles:

- attacking player
- control player
- beginner/value player
- high-tension player
- frequent breaker / durability-focused player

Compare:

- v9 top 5
- v10 top 5
- score breakdown
- confidence score
- top reasons
- whether the recommendation better matches the profile

Suggested output:

- `ml/nlp-workbench-latest/output/bert_absa_v1/recommendation_comparison.md`

## Known Risks

- Existing complete ABSA notebooks contain a syntax issue in the TF-IDF input
  cell. Implementation should script or repair the pipeline before relying on
  notebook execution.
- The latest labeling notebook contains a bare `pip install` cell. Setup should
  move to requirements/docs or use notebook-safe shell syntax.
- Weak labels may encode the old dictionary's biases. Manual gold evaluation is
  required before claiming BERT improves accuracy.
- Mixed and neutral labels are sparse and need careful manual review.
- Colab/Kaggle training must export artifacts back into this workspace with
  stable paths and version names.
- Generated model artifacts and large outputs should not be committed unless the
  user explicitly asks to version them.

## Done Criteria

- Raw review extraction is repeatable from `badminton_strings_data.json`.
- Gold set CSV exists with 900 to 1,500 two-stage labels.
- Preprocessing is repeatable and preserves key badminton-domain cues.
- Local smoke test can run on a small sample.
- Colab/Kaggle training workflow can train the full model.
- ABSA metrics are reported on the manual gold set.
- v10 BERT hybrid matrix is generated.
- Backend import matches 33 of 33 strings.
- Recommendation comparison is produced for fixed player profiles.
- The final report clearly separates raw source, weak labels, gold labels,
  baselines, model outputs, and backend runtime artifacts.
