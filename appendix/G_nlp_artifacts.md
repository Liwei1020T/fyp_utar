# Appendix G: NLP and Recommendation Artifacts

The recommendation system uses offline NLP workbench artifacts as item-side feature signals. These artifacts support the backend recommender but are not a separate public runtime service in FYP1.

Canonical source folder:

- `ml/nlp-workbench-latest/`
- `ml/nlp-workbench-latest/data/`
- `ml/nlp-workbench-latest/output/`

## Main Artifacts

| Artifact | Path | Purpose |
| --- | --- | --- |
| Complete ABSA pipeline notebook | `ml/nlp-workbench-latest/stringsense_complete_absa_pipeline_notebook_latest.ipynb` | Documents the end-to-end NLP pipeline used to create recommendation signals. |
| ABSA labeling notebook | `ml/nlp-workbench-latest/stringsense_absa_labeling_notebook_latest.ipynb` | Supports review/aspect labeling workflow. |
| Domain dictionary | `ml/nlp-workbench-latest/data/domain_dictionary_optimized_v8.csv` | Stores badminton-string domain terms and feature mappings. |
| Normalization rules | `ml/nlp-workbench-latest/data/normalization_rules_v8.csv` | Stores text normalization rules for NLP preprocessing. |
| High-confidence ABSA data | `ml/nlp-workbench-latest/data/nlp_absa_high_confidence_latest.csv` | Historical pre-boundary output retained for audit; not the current training input. |
| Long ABSA dataset | `ml/nlp-workbench-latest/data/nlp_absa_long_dataset_latest.csv` | Historical pre-boundary output retained for audit; not the current training input. |
| Approved system/BERT cohort | `config/approved_string_cohort_v1.csv` | Defines the 12 active strings shared by runtime filtering and BERT preparation. |
| BERT preparation run | `ml/nlp-workbench-latest/output/runs/bert-prep-system12-high3-20260810-v1/` | Contains the frozen 130,421-row, high-confidence three-class Silver dataset and provenance. |
| BERT training runs | `ml/nlp-workbench-latest/output/runs/<bert-training-run-id>/bert_training/` | Contains run-scoped model, metrics, predictions, and `not_promoted` manifests. |
| Practical feature matrix CSV | `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v8_v6dict.csv` | Preserved historical/compatibility artifact; not imported by the current runtime. |
| Practical feature matrix XLSX | `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx` | Preserved legacy V9 artifact; not imported by the current runtime. |
| Current recommendation matrix | `ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx` | Current 12-string MacBERT `nlp_review` source imported by the backend. |

## Backend Integration

The backend imports the practical matrix into `string_recommendation_matrix`, especially under source layer `nlp_review`.

Current runtime feature keys include:

- `repulsion`
- `comfort`
- `control`
- `durability`
- `elasticity`
- `sound`
- `string_movement`
- `tension_retention`
- `value_for_money`

The BERT classifier uses all nine review aspects. In the recommender,
`value_for_money` is an auxiliary budget/value signal while the other eight are
the required core NLP feature set.

## Current BERT Boundary

- Model: `hfl/chinese-macbert-base`
- Input: target string, one requested aspect, and review text
- Labels: `not_mentioned`, `positive`, `negative`
- Training source: high-confidence, rule-based Silver only
- Excluded: `mentioned`, `mixed`, zero-shot NLI, and any human-Gold claim
- Scope: 12 approved strings by 9 aspects
- Runtime state: offline/run-scoped and `not_promoted`

Metrics against the pseudo-labeled validation/test partitions validate pipeline
behavior only. They do not establish human-ground-truth accuracy.

## Feedback Linkage

The existing feedback flow can enrich a future 12-by-9 matrix without putting
MacBERT inside the synchronous API request:

1. `POST /api/bookings/{booking_id}/feedback` persists `string_feedback` and
   structured ratings against a completed booking whose `string_id` is known.
2. `GET /api/admin/feedback/export` provides an auditable batch input.
3. Offline inference evaluates each non-blank string comment against the nine
   aspect prompts and retains probabilities and model/run provenance.
4. Aggregation combines confident text signals with available structured
   comfort, control, repulsion, durability, and tension ratings for the 12
   approved strings.
5. A versioned matrix is reviewed, then imported through
   `POST /api/admin/recommendation-matrix/import` only after explicit promotion
   approval.

New feedback must not automatically retrain the model or overwrite the current
backend matrix. Batch inference and manual import are sufficient for the FYP
scope and keep every score traceable.

## Suggested Appendix Use

Include:

1. A screenshot or exported table preview of the matrix columns.
2. A short explanation of how review-derived features become recommendation inputs.
3. The recommender formula from Appendix D.
4. A note that BERT is offline review understanding, not a deployed deep-learning ranking service.
