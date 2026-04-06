# NLP Workbench

This folder keeps the notebook-driven ABSA pipeline used to generate recommendation artifacts for the backend.

## Inputs

- `data/归档.zip`
- `data/domain_dictionary_optimized_v6.csv`
- `data/normalization_rules_v6.csv`
- `data/nlp_absa_long_dataset_latest.csv`
- `data/nlp_absa_high_confidence_latest.csv`

## Generated Outputs Used by the Backend

- `outputs/patched_practical_string_feature_matrix.csv`
- `outputs/rule_based_review_aspect_signals.csv`

The backend reads these files through `AI_MATRIX_CSV_PATH` and `AI_REVIEW_ASPECT_CSV_PATH`.

## Run

```bash
python3 -m pip install -r requirements.txt
jupyter lab
```

Open `stringsense_complete_absa_pipeline_notebook.ipynb` and run it from top to bottom. Generated files should stay inside `outputs/`.
