# NLP Workbench Latest — Canonical Root

This is the approved canonical NLP root for the unified StringSence workspace.
It is an offline notebook, dataset, and artifact workflow, not a public runtime
service or an installable Python package.

## Included files

- `data/archive_latest.zip`
- `data/archive_latest/` extracted source data
- `data/domain_dictionary_optimized_v8.csv`
- `data/normalization_rules_v8.csv`
- `data/nlp_absa_long_dataset_latest.csv`
- `data/nlp_absa_high_confidence_latest.csv`
- `data/latest_practical_string_feature_matrix_v8_v6dict.csv`
- `data/latest_tfidf_string_feature_matrix.csv`
- `output/latest_practical_string_feature_matrix_v8_v6dict.csv`
- `output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`
- `stringsense_complete_absa_pipeline_notebook_latest.ipynb`
- `stringsense_absa_labeling_notebook_latest.ipynb`
- `requirements.txt`

## Runtime handoff

The unified backend uses the V9 workbook as its public recommendation source:

```text
output/latest_practical_string_feature_matrix_v9_v8dict.xlsx
```

The standalone `ai_service` compatibility loader uses the latest CSV export:

```text
output/latest_practical_string_feature_matrix_v8_v6dict.csv
```

The notebook can also generate optional compatibility files under `output/`,
including `rule_based_review_aspect_signals.csv`.

## Run the notebooks

From this directory:

```bash
python3 -m pip install -r requirements.txt
jupyter lab
```

Run either latest notebook from top to bottom. The notebooks use local relative
paths and write generated artifacts to this directory's `output/` folder.

When launched from the repository root, the notebooks automatically resolve
`ml/nlp-workbench-latest` as their working directory when
`data/archive_latest.zip` is not present in the current directory.

## Data boundary

The archive and extracted source data are read-only inputs. Do not overwrite
the original source data or process later modeling stages without a separate
task decision. Generated outputs should remain versioned and clearly named.

## Dataset summary

```json
{
  "strings_count": 33,
  "aspects_count": 9,
  "long_dataset_rows": 200250,
  "high_confidence_rows": 178219,
  "long_label_distribution": {
    "not_mentioned": 130296,
    "positive": 38712,
    "mentioned": 17441,
    "negative": 9211,
    "mixed": 4590
  },
  "high_label_distribution": {
    "not_mentioned": 130296,
    "positive": 38712,
    "negative": 9211
  }
}
```
