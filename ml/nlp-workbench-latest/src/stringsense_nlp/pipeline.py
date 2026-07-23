from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable

import joblib
import jieba
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

from .boundary import RUN_SCHEMA_VERSION
from .boundary import artifact_records
from .boundary import assert_inputs_unchanged
from .boundary import assert_zero_leakage
from .boundary import create_stage_directory
from .boundary import fingerprint_inputs
from .boundary import fingerprint_protected_assets
from .boundary import leakage_report
from .boundary import read_json
from .boundary import resolve_workbench
from .boundary import run_root
from .boundary import runtime_versions
from .boundary import sha256_file
from .boundary import utc_now
from .boundary import write_json_exclusive
from .labeling import build_aspect_lexicon
from .labeling import build_normalizer
from .labeling import load_dictionary_and_rules
from .labeling import register_custom_terms
from .labeling import split_into_clauses


RANDOM_STATE = 42
MODEL_PACKAGES = (
    "pandas",
    "numpy",
    "jieba",
    "scikit-learn",
    "joblib",
    "openpyxl",
)


def _load_raw_data(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("strings"), list):
        raise ValueError("Raw review source must contain a top-level strings array")
    return payload


def _parse_price(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return np.nan
    return parsed if parsed > 0 else np.nan


def _review_id(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("Every raw review must have a stable review_id")
    return raw if raw.startswith("R") else f"R{raw}"


def build_review_frame(
    raw_data: dict[str, Any],
    normalize_text: Callable[[str], str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for item in raw_data["strings"]:
        for review in item.get("reviews", []):
            review_text = str(review.get("content") or "").strip()
            if not review_text:
                continue
            normalized_text = normalize_text(review_text)
            rows.append(
                {
                    "string_name": str(item.get("name") or "").strip(),
                    "brand": str(item.get("brand") or "").strip(),
                    "price_rm": _parse_price(item.get("price")),
                    "review_id": _review_id(review.get("review_id")),
                    "review_text": review_text,
                    "normalized_text": normalized_text,
                    "clauses": split_into_clauses(normalized_text),
                    "likes_count": review.get("likes", 0) or 0,
                    "rating_label": review.get("rating_label", ""),
                }
            )
    frame = pd.DataFrame(rows)
    if frame["review_id"].duplicated().any():
        duplicate = frame.loc[frame["review_id"].duplicated(), "review_id"].iloc[0]
        raise ValueError(f"Duplicate raw review_id: {duplicate}")
    return frame


def build_rule_signals(
    reviews: pd.DataFrame,
    lexicon: dict[str, dict[str, set[str]]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for review in reviews.itertuples(index=False):
        for clause in review.clauses:
            for aspect, terms in lexicon.items():
                aspect_hits = sorted(
                    term for term in terms["aspect_terms"] if term in clause
                )
                positive_hits = sorted(
                    term for term in terms["positive_terms"] if term in clause
                )
                negative_hits = sorted(
                    term for term in terms["negative_terms"] if term in clause
                )
                if not (aspect_hits or positive_hits or negative_hits):
                    continue
                if len(positive_hits) > len(negative_hits):
                    polarity = "positive"
                elif len(negative_hits) > len(positive_hits):
                    polarity = "negative"
                else:
                    polarity = "neutral"
                rows.append(
                    {
                        "string_name": review.string_name,
                        "brand": review.brand,
                        "price_rm": review.price_rm,
                        "review_id": review.review_id,
                        "likes_count": review.likes_count,
                        "rating_label": review.rating_label,
                        "clause": clause,
                        "aspect": aspect,
                        "polarity": polarity,
                        "aspect_hits": "|".join(aspect_hits),
                        "positive_hits": "|".join(positive_hits),
                        "negative_hits": "|".join(negative_hits),
                    }
                )
    return pd.DataFrame(rows)


def _evidence_weight(likes_count: object) -> float:
    return 1.0 + (0.12 * math.log1p(float(likes_count)))


def build_practical_matrix(
    signals: pd.DataFrame,
    reviews: pd.DataFrame,
    aspects: list[str],
) -> pd.DataFrame:
    priors: dict[str, float] = {}
    for aspect in aspects:
        subset = signals[signals["aspect"] == aspect]
        positive = int((subset["polarity"] == "positive").sum())
        negative = int((subset["polarity"] == "negative").sum())
        priors[aspect] = (
            (positive + 1.0) / (positive + negative + 2.0)
            if positive + negative > 0
            else 0.5
        )

    rows: list[dict[str, object]] = []
    for string_name, string_signals in signals.groupby("string_name"):
        output: dict[str, object] = {"string_name": string_name}
        prices = reviews.loc[
            reviews["string_name"] == string_name,
            "price_rm",
        ].dropna()
        output["price_rm"] = float(prices.iloc[0]) if not prices.empty else np.nan
        for aspect in aspects:
            aspect_signals = string_signals[string_signals["aspect"] == aspect].copy()
            if aspect_signals.empty:
                raw_score = priors[aspect]
                confidence = 0.0
            else:
                aspect_signals["weight"] = aspect_signals["likes_count"].apply(
                    _evidence_weight
                )
                positive_weight = aspect_signals.loc[
                    aspect_signals["polarity"] == "positive",
                    "weight",
                ].sum()
                negative_weight = aspect_signals.loc[
                    aspect_signals["polarity"] == "negative",
                    "weight",
                ].sum()
                evidence = positive_weight + negative_weight
                alpha = (
                    6.0
                    if aspect in {"attack", "control", "elasticity", "sound"}
                    else 8.0
                )
                raw_score = (
                    (positive_weight + (alpha * priors[aspect])) / (evidence + alpha)
                    if evidence > 0
                    else priors[aspect]
                )
                confidence = min(1.0, evidence / 25.0)
            output[f"{aspect}_review_raw"] = float(raw_score)
            output[f"{aspect}_confidence"] = float(confidence)
        rows.append(output)

    matrix = pd.DataFrame(rows)
    if "string_movement_review_raw" in matrix:
        matrix["string_movement_review_raw"] = (
            1.0 - matrix["string_movement_review_raw"]
        )
    if "value_for_money_review_raw" in matrix:
        known_prices = matrix["price_rm"].dropna()
        if not known_prices.empty and known_prices.max() > known_prices.min():
            affordability = 1.0 - (
                (matrix["price_rm"] - known_prices.min())
                / (known_prices.max() - known_prices.min())
            )
            matrix["value_for_money"] = 0.75 * matrix[
                "value_for_money_review_raw"
            ] + 0.25 * affordability.fillna(0.5)
        else:
            matrix["value_for_money"] = matrix["value_for_money_review_raw"]
    for aspect in aspects:
        if aspect != "value_for_money":
            matrix[aspect] = matrix[f"{aspect}_review_raw"]
    matrix["beginner_fit_score"] = (
        0.35 * matrix.get("comfort", 0.5)
        + 0.25 * matrix.get("control", 0.5)
        + 0.20 * matrix.get("durability", 0.5)
        + 0.20 * matrix.get("value_for_money", 0.5)
    )
    matrix["stability_score"] = matrix.get("string_movement", 0.5)
    all_round_columns = [
        column
        for column in (
            "attack",
            "comfort",
            "control",
            "durability",
            "elasticity",
            "sound",
            "stability_score",
            "tension_retention",
            "value_for_money",
        )
        if column in matrix
    ]
    matrix["all_round_score"] = matrix[all_round_columns].mean(axis=1)
    return matrix.sort_values("string_name").reset_index(drop=True)


def build_model_input_factory(
    normalize_text: Callable[[str], str],
) -> Callable[[str, str], str]:
    stopwords = {
        "这个",
        "那个",
        "真的",
        "感觉",
        "觉得",
        "还是",
        "就是",
        "因为",
        "然后",
        "而且",
        "如果",
        "所以",
        "但是",
        "不过",
        "一个",
        "一种",
        "一下",
        "一些",
        "没有",
        "不是",
        "比较",
        "非常",
        "特别",
        "很多",
        "有点",
        "一点",
        "已经",
        "时候",
        "东西",
        "问题",
        "方面",
        "可能",
        "这样",
        "那样",
        "我们",
        "你们",
        "他们",
    }
    single_character_whitelist = {
        "脆",
        "响",
        "闷",
        "弹",
        "硬",
        "软",
        "稳",
        "顶",
        "炸",
    }
    cache: dict[str, str] = {}

    def tokenized(text: str) -> str:
        if text not in cache:
            tokens = []
            for token in jieba.lcut(normalize_text(text)):
                token = token.strip()
                if not token or token in stopwords or token.isdigit():
                    continue
                if len(token) == 1 and token not in single_character_whitelist:
                    continue
                tokens.append(token)
            cache[text] = " ".join(tokens)
        return cache[text]

    def build(review_text: str, aspect: str) -> str:
        return f"aspect: {aspect} [SEP] {tokenized(str(review_text))}"

    return build


def _model_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    token_pattern=r"(?u)\b\w+\b",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=30000,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    solver="liblinear",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def _evaluate(
    model: Pipeline,
    frame: pd.DataFrame,
    target: str,
) -> dict[str, dict[str, float | int]]:
    metrics: dict[str, dict[str, float | int]] = {}
    for split in ("val", "test"):
        subset = frame[frame["split"] == split]
        if subset.empty:
            raise ValueError(f"Evaluation split is empty: {split}")
        predictions = model.predict(subset["text_input"].tolist())
        expected = subset[target].astype(int).tolist()
        metrics[split] = {
            "rows": int(len(subset)),
            "accuracy": float(accuracy_score(expected, predictions)),
            "macro_f1": float(f1_score(expected, predictions, average="macro")),
        }
    return metrics


def train_models(
    mention_data: pd.DataFrame,
    sentiment_data: pd.DataFrame,
    build_model_input: Callable[[str, str], str],
) -> tuple[Pipeline, Pipeline, dict[str, object]]:
    mention = mention_data.copy()
    mention["text_input"] = [
        build_model_input(row.review_text, row.aspect)
        for row in mention.itertuples(index=False)
    ]
    mention_train = mention[mention["split"] == "train"]
    mention_model = _model_pipeline()
    mention_model.fit(
        mention_train["text_input"].tolist(),
        mention_train["mention_flag"].astype(int).tolist(),
    )

    sentiment = sentiment_data[
        (sentiment_data["mention_flag"] == 1)
        & sentiment_data["sentiment_id"].isin([-1.0, 1.0])
    ].copy()
    sentiment["target"] = sentiment["sentiment_id"].map({-1.0: 0, 1.0: 1})
    sentiment["text_input"] = [
        build_model_input(row.review_text, row.aspect)
        for row in sentiment.itertuples(index=False)
    ]
    sentiment_train = sentiment[sentiment["split"] == "train"]
    sentiment_model = _model_pipeline()
    sentiment_model.fit(
        sentiment_train["text_input"].tolist(),
        sentiment_train["target"].astype(int).tolist(),
    )

    return (
        mention_model,
        sentiment_model,
        {
            "mention": _evaluate(mention_model, mention, "mention_flag"),
            "sentiment": _evaluate(sentiment_model, sentiment, "target"),
        },
    )


def run_full_inference(
    reviews: pd.DataFrame,
    aspects: list[str],
    build_model_input: Callable[[str, str], str],
    mention_model: Pipeline,
    sentiment_model: Pipeline,
) -> pd.DataFrame:
    rows = []
    for review in reviews.itertuples(index=False):
        for aspect in aspects:
            rows.append(
                {
                    "string_name": review.string_name,
                    "brand": review.brand,
                    "price_rm": review.price_rm,
                    "review_id": review.review_id,
                    "review_text": review.normalized_text,
                    "likes_count": review.likes_count,
                    "aspect": aspect,
                    "text_input": build_model_input(review.normalized_text, aspect),
                }
            )
    output = pd.DataFrame(rows)
    output["mention_pred"] = mention_model.predict(output["text_input"].tolist())
    sentiment_predictions = np.full(len(output), np.nan)
    mentioned = output["mention_pred"] == 1
    sentiment_predictions[mentioned] = sentiment_model.predict(
        output.loc[mentioned, "text_input"].tolist()
    )
    output["sentiment_pred"] = sentiment_predictions
    return output.drop(columns=["text_input"])


def build_tfidf_matrix(
    predictions: pd.DataFrame,
    reviews: pd.DataFrame,
    practical_matrix: pd.DataFrame,
    aspects: list[str],
) -> pd.DataFrame:
    rows = []
    for string_name, string_predictions in predictions.groupby("string_name"):
        output: dict[str, object] = {"string_name": string_name}
        prices = reviews.loc[
            reviews["string_name"] == string_name,
            "price_rm",
        ].dropna()
        output["price_rm"] = float(prices.iloc[0]) if not prices.empty else np.nan
        for aspect in aspects:
            subset = string_predictions[
                (string_predictions["aspect"] == aspect)
                & (string_predictions["mention_pred"] == 1)
            ]
            positive = int((subset["sentiment_pred"] == 1).sum())
            negative = int((subset["sentiment_pred"] == 0).sum())
            output[aspect] = (
                (positive + 1.0) / (positive + negative + 2.0)
                if positive + negative > 0
                else 0.5
            )
        output["string_movement"] = 1.0 - float(output["string_movement"])
        known_prices = practical_matrix["price_rm"].dropna()
        if (
            pd.notna(output["price_rm"])
            and not known_prices.empty
            and known_prices.max() > known_prices.min()
        ):
            affordability = 1.0 - (
                (float(output["price_rm"]) - known_prices.min())
                / (known_prices.max() - known_prices.min())
            )
            output["value_for_money"] = (
                0.75 * float(output["value_for_money"]) + 0.25 * affordability
            )
        rows.append(output)
    return pd.DataFrame(rows).sort_values("string_name").reset_index(drop=True)


def _implementation_fingerprints(workbench: Path) -> list[dict[str, object]]:
    files = (
        workbench / "src/stringsense_nlp/boundary.py",
        workbench / "src/stringsense_nlp/labeling.py",
        workbench / "src/stringsense_nlp/pipeline.py",
        workbench / "stringsense_absa_labeling_notebook_latest.ipynb",
        workbench / "stringsense_complete_absa_pipeline_notebook_latest.ipynb",
    )
    return [
        {
            "path": path.relative_to(workbench).as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in files
    ]


def run_pipeline(run_id: str, start: Path | None = None) -> dict[str, object]:
    workbench = resolve_workbench(start)
    root = run_root(workbench, run_id)
    labeling_manifest_path = root / "labeling/manifest.json"
    if not labeling_manifest_path.is_file():
        raise FileNotFoundError(
            "Run the labeling notebook with the same STRINGSENSE_NLP_RUN_ID first"
        )
    before = fingerprint_inputs(workbench)
    protected_before = fingerprint_protected_assets(workbench)
    stage_dir = create_stage_directory(workbench, run_id, "pipeline")
    labeling_manifest = read_json(labeling_manifest_path)
    mention_path = root / "labeling/nlp_absa_long_dataset.csv"
    sentiment_path = root / "labeling/nlp_absa_high_confidence.csv"
    mention_data = pd.read_csv(mention_path)
    sentiment_data = pd.read_csv(sentiment_path)
    mention_leakage = leakage_report(mention_data)
    sentiment_leakage = leakage_report(sentiment_data)
    assert_zero_leakage(mention_leakage)
    assert_zero_leakage(sentiment_leakage)

    dictionary, rules = load_dictionary_and_rules(workbench)
    register_custom_terms(dictionary)
    normalize_text = build_normalizer(rules)
    lexicon = build_aspect_lexicon(dictionary)
    aspects = sorted(lexicon)
    raw_data = _load_raw_data(
        workbench / "data/archive_latest/badminton_strings_data.json"
    )
    reviews = build_review_frame(raw_data, normalize_text)
    signals = build_rule_signals(reviews, lexicon)
    practical_matrix = build_practical_matrix(signals, reviews, aspects)

    build_model_input = build_model_input_factory(normalize_text)
    mention_model, sentiment_model, metrics = train_models(
        mention_data,
        sentiment_data,
        build_model_input,
    )
    predictions = run_full_inference(
        reviews,
        aspects,
        build_model_input,
        mention_model,
        sentiment_model,
    )
    tfidf_matrix = build_tfidf_matrix(
        predictions,
        reviews,
        practical_matrix,
        aspects,
    )
    comparison = practical_matrix[
        ["string_name", *[aspect for aspect in aspects if aspect in practical_matrix]]
    ].merge(
        tfidf_matrix[["string_name", *aspects]],
        on="string_name",
        suffixes=("_practical", "_tfidf"),
    )
    for aspect in aspects:
        comparison[f"{aspect}_abs_diff"] = (
            comparison[f"{aspect}_practical"] - comparison[f"{aspect}_tfidf"]
        ).abs()
    comparison = comparison.sort_values(
        f"{aspects[0]}_abs_diff",
        ascending=False,
    ).reset_index(drop=True)

    artifact_paths = {
        "rule_signals": stage_dir / "rule_based_review_aspect_signals.csv",
        "practical_csv": stage_dir / "practical_string_feature_matrix.csv",
        "practical_xlsx": stage_dir / "practical_string_feature_matrix.xlsx",
        "mention_model": stage_dir / "tfidf_mention_model.joblib",
        "sentiment_model": stage_dir / "tfidf_sentiment_model.joblib",
        "predictions": stage_dir / "tfidf_full_review_aspect_predictions.csv",
        "tfidf_csv": stage_dir / "tfidf_string_feature_matrix.csv",
        "tfidf_xlsx": stage_dir / "tfidf_string_feature_matrix.xlsx",
        "comparison": stage_dir / "practical_vs_tfidf_comparison.csv",
    }
    signals.to_csv(artifact_paths["rule_signals"], index=False, encoding="utf-8-sig")
    practical_matrix.to_csv(
        artifact_paths["practical_csv"], index=False, encoding="utf-8-sig"
    )
    practical_matrix.to_excel(artifact_paths["practical_xlsx"], index=False)
    joblib.dump(mention_model, artifact_paths["mention_model"])
    joblib.dump(sentiment_model, artifact_paths["sentiment_model"])
    predictions.to_csv(artifact_paths["predictions"], index=False, encoding="utf-8-sig")
    tfidf_matrix.to_csv(artifact_paths["tfidf_csv"], index=False, encoding="utf-8-sig")
    tfidf_matrix.to_excel(artifact_paths["tfidf_xlsx"], index=False)
    comparison.to_csv(artifact_paths["comparison"], index=False, encoding="utf-8-sig")

    summary = {
        "strings_count": int(len(raw_data["strings"])),
        "raw_reviews_count": int(len(reviews)),
        "rule_based_signal_rows": int(len(signals)),
        "practical_matrix_rows": int(len(practical_matrix)),
        "tfidf_full_rows": int(len(predictions)),
        "tfidf_matrix_rows": int(len(tfidf_matrix)),
        "metrics": metrics,
        "random_state": RANDOM_STATE,
    }
    summary_path = stage_dir / "run_summary.json"
    write_json_exclusive(summary_path, summary)
    all_artifacts = [*artifact_paths.values(), summary_path]
    pipeline_manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "pipeline",
        "status": "completed",
        "created_at": utc_now(),
        "inputs": before,
        "protected_assets": protected_before,
        "training_data": {
            "labeling_manifest_sha256": sha256_file(labeling_manifest_path),
            "mention_dataset_sha256": sha256_file(mention_path),
            "sentiment_dataset_sha256": sha256_file(sentiment_path),
            "leakage": {
                "mention": mention_leakage,
                "sentiment": sentiment_leakage,
            },
        },
        "configuration": {
            "random_state": RANDOM_STATE,
            "classifier": "LogisticRegression(liblinear,class_weight=balanced)",
            "tfidf": {
                "ngram_range": [1, 2],
                "min_df": 2,
                "max_features": 30000,
            },
        },
        "summary": summary,
        "runtime_versions": runtime_versions(MODEL_PACKAGES),
        "artifacts": artifact_records(all_artifacts, root),
    }
    pipeline_manifest_path = stage_dir / "manifest.json"
    write_json_exclusive(pipeline_manifest_path, pipeline_manifest)

    after = fingerprint_inputs(workbench)
    assert_inputs_unchanged(before, after)
    protected_after = fingerprint_protected_assets(workbench)
    assert_inputs_unchanged(protected_before, protected_after)
    run_manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "status": "completed",
        "created_at": utc_now(),
        "inputs": before,
        "protected_assets": protected_before,
        "implementation": _implementation_fingerprints(workbench),
        "stages": {
            "labeling": {
                "manifest": "labeling/manifest.json",
                "manifest_sha256": sha256_file(labeling_manifest_path),
                "dataset": labeling_manifest["dataset"],
                "leakage": labeling_manifest["leakage"],
            },
            "pipeline": {
                "manifest": "pipeline/manifest.json",
                "manifest_sha256": sha256_file(pipeline_manifest_path),
                "summary": summary,
            },
        },
        "artifacts": [
            *labeling_manifest["artifacts"],
            *pipeline_manifest["artifacts"],
        ],
        "promotion": {
            "status": "not_promoted",
            "requires_human_approval": True,
            "canonical_backend_artifact": (
                "output/latest_practical_string_feature_matrix_v9_v8dict.xlsx"
            ),
            "canonical_artifact_modified": False,
        },
    }
    run_manifest_path = root / "run_manifest.json"
    write_json_exclusive(run_manifest_path, run_manifest)
    return {
        "run_id": run_id,
        "run_root": str(root),
        "run_manifest_path": str(run_manifest_path),
        "pipeline_manifest_path": str(pipeline_manifest_path),
        "summary": summary,
        "promotion": run_manifest["promotion"],
    }
