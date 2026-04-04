# StringSense NLP Jupyter Notebook Full Package

This package is self-contained for the complete ABSA pipeline notebook.

## Included files

- `stringsense_complete_absa_pipeline_notebook.ipynb`
- `requirements.txt`
- `data/归档.zip`
- `data/domain_dictionary_optimized_v6.csv`
- `data/normalization_rules_v6.csv`
- `data/nlp_absa_long_dataset.csv`
- `data/nlp_absa_high_confidence.csv`

## What the notebook includes

- `jieba` setup
- custom dictionary loading
- normalization rules
- latest archive loading
- rule-based aspect signal extraction
- patched practical matrix generation
- TF-IDF mention model training
- TF-IDF sentiment model training
- full-corpus inference
- TF-IDF matrix generation
- comparison between the practical matrix and the TF-IDF matrix

## How to run

1. Extract the ZIP file.
2. Open the extracted folder in Jupyter Notebook or JupyterLab.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Open `stringsense_complete_absa_pipeline_notebook.ipynb`.
5. Run the notebook from top to bottom.

## Output location

All generated outputs will be written into the local `outputs/` folder inside the extracted package.
