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
| Practical feature matrix CSV | `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v8_v6dict.csv` | Compatibility CSV for the optional standalone AI-service path. |
| Practical feature matrix XLSX | `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx` | Current default backend recommendation matrix source. |

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

## Suggested Appendix Use

Include:

1. A screenshot or exported table preview of the matrix columns.
2. A short explanation of how review-derived features become recommendation inputs.
3. The recommender formula from Appendix D.
4. A note that FYP1 uses NLP-derived feature signals, not a deployed deep learning ranking service.
