FROM python:3.13-slim

WORKDIR /app

ENV HF_HUB_OFFLINE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_OFFLINE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir torch==2.9.0 \
    && pip install --no-cache-dir \
        transformers==4.57.6 \
    && python -c "import torch, transformers; print(torch.__version__, transformers.__version__)"

COPY stringsense_bert_demo.py /app/stringsense_bert_demo.py

EXPOSE 7860

CMD ["python", "/app/stringsense_bert_demo.py", "--host", "0.0.0.0", "--port", "7860", "--device", "cpu", "--model-dir", "/app/macbert_demo_model", "--cohort-path", "/app/config/approved_string_cohort_v1.csv", "--normalization-path", "/app/config/normalization_rules_v8.csv"]
