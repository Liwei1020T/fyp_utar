#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score


WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH / "src"))

from stringsense_nlp.bert import BERT_LABELS  # noqa: E402
from stringsense_nlp.bert import default_training_config  # noqa: E402
from stringsense_nlp.bert import validate_bert_pseudo_dataset  # noqa: E402
from stringsense_nlp.boundary import artifact_records  # noqa: E402
from stringsense_nlp.boundary import assert_inputs_unchanged  # noqa: E402
from stringsense_nlp.boundary import create_stage_directory  # noqa: E402
from stringsense_nlp.boundary import fingerprint_inputs  # noqa: E402
from stringsense_nlp.boundary import fingerprint_protected_assets  # noqa: E402
from stringsense_nlp.boundary import run_root  # noqa: E402
from stringsense_nlp.boundary import runtime_versions  # noqa: E402
from stringsense_nlp.boundary import sha256_file  # noqa: E402
from stringsense_nlp.boundary import utc_now  # noqa: E402
from stringsense_nlp.boundary import write_json_exclusive  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train an aspect-conditioned BERT classifier on run-scoped pseudo labels"
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--expected-dataset-sha256",
        default="",
        help=(
            "Require this dataset digest and use the portable dataset-only boundary "
            "instead of loading protected source assets"
        ),
    )
    parser.add_argument("--model-name", default="hfl/chinese-macbert-base")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--train-batch-size", type=int, default=8)
    parser.add_argument("--eval-batch-size", type=int, default=16)
    parser.add_argument(
        "--smoke-samples-per-split",
        type=int,
        default=0,
        help="Deterministically cap each split for a quick training smoke test",
    )
    return parser.parse_args()


def _require_training_dependencies() -> dict[str, Any]:
    try:
        import torch
        from torch.nn import functional as torch_functional
        from torch.utils.data import Dataset
        from transformers import AutoModelForSequenceClassification
        from transformers import AutoTokenizer
        from transformers import DataCollatorWithPadding
        from transformers import EarlyStoppingCallback
        from transformers import Trainer
        from transformers import TrainingArguments
    except ImportError as exc:
        raise SystemExit(
            "BERT dependencies are missing. Run ./scripts/bootstrap.sh after the "
            "requirements lock is updated."
        ) from exc
    return {
        "torch": torch,
        "torch_functional": torch_functional,
        "Dataset": Dataset,
        "AutoModelForSequenceClassification": AutoModelForSequenceClassification,
        "AutoTokenizer": AutoTokenizer,
        "DataCollatorWithPadding": DataCollatorWithPadding,
        "EarlyStoppingCallback": EarlyStoppingCallback,
        "Trainer": Trainer,
        "TrainingArguments": TrainingArguments,
    }


def _safe_dataset_path(path: Path) -> Path:
    resolved = path.resolve()
    runs_root = (WORKBENCH / "output/runs").resolve()
    if not resolved.is_relative_to(runs_root) or not resolved.is_file():
        raise ValueError("--dataset must be an existing file under output/runs/")
    return resolved


def _verify_dataset_sha256(path: Path, expected: str) -> str:
    actual = sha256_file(path)
    if expected and actual != expected:
        raise ValueError(
            f"Dataset SHA256 mismatch: expected {expected}, received {actual}"
        )
    return actual


def _limit_splits(frame: pd.DataFrame, size: int, seed: int) -> pd.DataFrame:
    if size <= 0:
        return frame
    return (
        frame.sample(frac=1, random_state=seed)
        .groupby("split", sort=True, group_keys=False)
        .head(size)
        .sort_values("sample_id")
        .reset_index(drop=True)
    )


def _metrics(predictions: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    predicted = predictions.argmax(axis=-1)
    true_mentions = labels != 0
    predicted_mentions = predicted != 0
    metrics = {
        "accuracy": float(accuracy_score(labels, predicted)),
        "macro_f1": float(
            f1_score(labels, predicted, average="macro", zero_division=0)
        ),
        "weighted_f1": float(
            f1_score(labels, predicted, average="weighted", zero_division=0)
        ),
        "mention_f1": float(
            f1_score(true_mentions, predicted_mentions, zero_division=0)
        ),
    }
    per_class_f1 = f1_score(
        labels,
        predicted,
        labels=range(len(BERT_LABELS)),
        average=None,
        zero_division=0,
    )
    metrics.update(
        {
            f"f1_{label}": float(score)
            for label, score in zip(BERT_LABELS, per_class_f1, strict=True)
        }
    )
    return metrics


def _confusion_matrix(predictions: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    predicted = predictions.argmax(axis=-1)
    return {
        "labels": list(BERT_LABELS),
        "rows_true_columns_predicted": confusion_matrix(
            labels,
            predicted,
            labels=range(len(BERT_LABELS)),
        ).tolist(),
    }


def main() -> int:
    args = parse_args()
    dependencies = _require_training_dependencies()
    torch = dependencies["torch"]
    Dataset = dependencies["Dataset"]
    Trainer = dependencies["Trainer"]
    dataset_path = _safe_dataset_path(args.dataset)
    dataset_sha256 = _verify_dataset_sha256(dataset_path, args.expected_dataset_sha256)
    portable = bool(args.expected_dataset_sha256)
    before = None if portable else fingerprint_inputs(WORKBENCH)
    protected = None if portable else fingerprint_protected_assets(WORKBENCH)

    frame = pd.read_csv(dataset_path, keep_default_na=False)
    validate_bert_pseudo_dataset(frame)
    frame = _limit_splits(frame, args.smoke_samples_per_split, args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    tokenizer = dependencies["AutoTokenizer"].from_pretrained(args.model_name)

    class TextDataset(Dataset):
        def __init__(self, rows: pd.DataFrame) -> None:
            self.texts = rows["model_input"].astype(str).tolist()
            self.labels = rows["bert_label_id"].astype(int).tolist()

        def __len__(self) -> int:
            return len(self.labels)

        def __getitem__(self, index: int) -> dict[str, Any]:
            encoded = tokenizer(
                self.texts[index], truncation=True, max_length=args.max_length
            )
            encoded["labels"] = self.labels[index]
            return encoded

    splits = {
        split: frame[frame["split"] == split].reset_index(drop=True)
        for split in ("train", "val", "test")
    }
    if any(split.empty for split in splits.values()):
        raise ValueError(
            "BERT dataset must contain non-empty train, val and test splits"
        )

    counts = (
        splits["train"]["bert_label_id"]
        .value_counts()
        .reindex(range(len(BERT_LABELS)), fill_value=0)
    )
    if (counts == 0).any():
        raise ValueError("Every BERT label must appear in the training split")
    weights = len(splits["train"]) / (len(BERT_LABELS) * counts.to_numpy())
    class_weights = torch.tensor(weights, dtype=torch.float32)

    model = dependencies["AutoModelForSequenceClassification"].from_pretrained(
        args.model_name,
        num_labels=len(BERT_LABELS),
        id2label=dict(enumerate(BERT_LABELS)),
        label2id={label: index for index, label in enumerate(BERT_LABELS)},
    )
    stage_dir = create_stage_directory(WORKBENCH, args.run_id, "bert_training")
    model_dir = stage_dir / "model"

    class WeightedTrainer(Trainer):
        def compute_loss(
            self,
            model: Any,
            inputs: dict[str, Any],
            return_outputs: bool = False,
            num_items_in_batch: Any = None,
        ) -> Any:
            del num_items_in_batch
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            loss = dependencies["torch_functional"].cross_entropy(
                outputs.logits,
                labels,
                weight=class_weights.to(outputs.logits.device),
            )
            return (loss, outputs) if return_outputs else loss

    training_args = dependencies["TrainingArguments"](
        output_dir=str(stage_dir / "checkpoints"),
        learning_rate=2e-5,
        per_device_train_batch_size=args.train_batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=100,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        save_total_limit=2,
        seed=args.seed,
        data_seed=args.seed,
        fp16=False,
        bf16=False,
        dataloader_pin_memory=False,
        report_to="none",
    )

    def compute_metrics(evaluation: Any) -> dict[str, float]:
        return _metrics(evaluation.predictions, evaluation.label_ids)

    trainer = WeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=TextDataset(splits["train"]),
        eval_dataset=TextDataset(splits["val"]),
        processing_class=tokenizer,
        data_collator=dependencies["DataCollatorWithPadding"](tokenizer),
        compute_metrics=compute_metrics,
        callbacks=[dependencies["EarlyStoppingCallback"](early_stopping_patience=2)],
    )
    train_result = trainer.train()
    trainer.save_model(model_dir)
    tokenizer.save_pretrained(model_dir)

    prediction = trainer.predict(TextDataset(splits["test"]))
    test_metrics = _metrics(prediction.predictions, prediction.label_ids)
    predicted_ids = prediction.predictions.argmax(axis=-1)
    predictions = splits["test"][
        ["sample_id", "review_id", "aspect", "bert_label"]
    ].copy()
    predictions["predicted_label"] = [BERT_LABELS[index] for index in predicted_ids]
    predictions_path = stage_dir / "test_predictions.csv"
    predictions.to_csv(predictions_path, index=False, encoding="utf-8-sig")

    metrics_path = stage_dir / "training_metrics.json"
    write_json_exclusive(
        metrics_path,
        {
            "train": {key: float(value) for key, value in train_result.metrics.items()},
            "test": test_metrics,
            "test_confusion_matrix": _confusion_matrix(
                prediction.predictions, prediction.label_ids
            ),
            "class_weights": dict(zip(BERT_LABELS, weights.tolist(), strict=True)),
            "evaluation_status": "pseudo_label_validation_only",
        },
    )
    config = default_training_config(args.model_name, args.seed)
    config.update(
        {
            "max_length": args.max_length,
            "epochs": args.epochs,
            "train_batch_size": args.train_batch_size,
            "eval_batch_size": args.eval_batch_size,
            "smoke_samples_per_split": args.smoke_samples_per_split,
        }
    )
    manifest_path = stage_dir / "manifest.json"
    artifacts = (predictions_path, metrics_path)
    manifest = {
        "run_id": args.run_id,
        "stage": "bert_training",
        "status": "completed_pseudo_label_training",
        "created_at": utc_now(),
        "dataset": {"path": str(dataset_path), "sha256": dataset_sha256},
        "input_boundary": {
            "mode": (
                "portable_dataset_sha256" if portable else "local_protected_assets"
            ),
            "protected_source_assets_uploaded": not portable,
        },
        "config": config,
        "split_rows": {key: len(value) for key, value in splits.items()},
        "split_label_rows": {
            split: {
                label: int((rows["bert_label"] == label).sum()) for label in BERT_LABELS
            }
            for split, rows in splits.items()
        },
        "runtime_versions": runtime_versions(("torch", "transformers", "accelerate")),
        "artifacts": artifact_records(artifacts, run_root(WORKBENCH, args.run_id)),
        "promotion": {"status": "not_promoted"},
        "gold_dataset_status": "not_available",
    }
    write_json_exclusive(manifest_path, manifest)
    write_json_exclusive(
        run_root(WORKBENCH, args.run_id) / "run_manifest.json",
        {**manifest, "stage_manifest": "bert_training/manifest.json"},
    )
    if before is not None and protected is not None:
        assert_inputs_unchanged(before, fingerprint_inputs(WORKBENCH))
        assert_inputs_unchanged(protected, fingerprint_protected_assets(WORKBENCH))
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
