#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys


WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH / "src"))

from stringsense_nlp.bert import run_bert_preparation  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare leakage-safe high-confidence three-class Silver pseudo labels "
            "for BERT training"
        )
    )
    parser.add_argument(
        "--run-id",
        default=datetime.now(UTC).strftime("bert-prep-%Y%m%dT%H%M%SZ"),
    )
    parser.add_argument("--model-name", default="hfl/chinese-macbert-base")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_bert_preparation(
        args.run_id,
        model_name=args.model_name,
        seed=args.seed,
        start=WORKBENCH,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
