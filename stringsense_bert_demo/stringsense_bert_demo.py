#!/usr/bin/env python3
"""One-file local web demo for nine-aspect StringSence review analysis."""

from __future__ import annotations

import argparse
import csv
from http.server import BaseHTTPRequestHandler, HTTPServer
import html
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable
from urllib.parse import urlsplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = PROJECT_ROOT / "macbert_demo_model"
DEFAULT_MODEL_LABEL = "bert-full-system12-longest-macbert-kaggle-20260903-v1"
COHORT_PATH = PROJECT_ROOT / "config/approved_string_cohort_v1.csv"
NORMALIZATION_PATH = (
    PROJECT_ROOT / "ml/nlp-workbench-latest/data/normalization_rules_v8.csv"
)
MAX_REVIEW_CHARS = 5_000
MAX_BODY_BYTES = 1_000_000
MAX_LENGTH = 128
BERT_LABELS = ("not_mentioned", "positive", "negative")
LABEL_NAMES = {
    "not_mentioned": "Not mentioned",
    "positive": "Positive",
    "negative": "Negative",
}
ASPECTS = (
    ("attack", "攻击性与弹射"),
    ("comfort", "舒适度"),
    ("control", "控制"),
    ("durability", "耐久性"),
    ("elasticity", "弹性"),
    ("sound", "击球声音"),
    ("string_movement", "走线"),
    ("tension_retention", "保磅性"),
    ("value_for_money", "性价比"),
)
ASPECT_DISPLAY_NAMES = {
    "attack": "Attack & Repulsion",
    "comfort": "Comfort",
    "control": "Control",
    "durability": "Durability",
    "elasticity": "Elasticity",
    "sound": "Sound",
    "string_movement": "String Movement",
    "tension_retention": "Tension Retention",
    "value_for_money": "Value for Money",
}


def load_string_names(path: Path) -> tuple[str, ...]:
    """Load the approved 12-string cohort without importing the workbench."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["catalog_id", "canonical_string_name"]:
            raise ValueError("The approved string cohort has an invalid schema")
        names = tuple(
            (row.get("canonical_string_name") or "").strip() for row in reader
        )
    if len(names) != 12 or len(set(names)) != 12 or any(not name for name in names):
        raise ValueError("The approved string cohort must contain 12 unique strings")
    return names


def load_normalizer(path: Path) -> Callable[[str], str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {"pattern", "replacement"}.issubset(
            reader.fieldnames
        ):
            raise ValueError("The normalization rules have an invalid schema")
        rules = [
            (row.get("pattern") or "", row.get("replacement") or "") for row in reader
        ]

    def normalize(text: str) -> str:
        normalized = str(text)
        for pattern, replacement in rules:
            normalized = re.sub(pattern, replacement, normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    return normalize


def resolve_device(torch: Any, requested: str) -> str:
    if requested not in {"auto", "cpu", "mps"}:
        raise ValueError("device must be auto, cpu or mps")
    if requested == "auto":
        return "mps" if torch.backends.mps.is_available() else "cpu"
    if requested == "mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS was requested but is unavailable")
    return requested


class ReviewAnalyzer:
    """Load one frozen local model and batch all nine aspect inputs per review."""

    def __init__(
        self,
        model_dir: Path,
        string_names: tuple[str, ...],
        *,
        device: str,
        model_label: str,
        normalizer: Callable[[str], str],
    ) -> None:
        try:
            import torch
            from transformers import AutoModelForSequenceClassification
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "BERT dependencies are missing; run the NLP workbench bootstrap first"
            ) from exc

        required = (
            "model.safetensors",
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json",
        )
        missing = [name for name in required if not (model_dir / name).is_file()]
        if missing:
            raise FileNotFoundError(
                f"The local model directory is incomplete: {', '.join(missing)}"
            )

        self.model_dir = model_dir.resolve()
        self.string_names = string_names
        self.model_label = model_label
        self.normalizer = normalizer
        self.torch = torch
        self.device = resolve_device(torch, device)
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_dir, local_files_only=True
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_dir, local_files_only=True
        )
        labels = tuple(
            self.model.config.id2label[index] for index in range(len(BERT_LABELS))
        )
        if labels != BERT_LABELS:
            raise ValueError(f"Model label order is incompatible: {labels}")
        self.model.to(self.device)
        self.model.eval()

    def analyze(self, string_name: str, review_text: str) -> dict[str, object]:
        if string_name not in self.string_names:
            raise ValueError("Please choose one of the approved 12 strings")
        raw_review = review_text.strip()
        if not raw_review:
            raise ValueError("Review text cannot be blank")
        if len(raw_review) > MAX_REVIEW_CHARS:
            raise ValueError(
                f"Review text is too long; maximum is {MAX_REVIEW_CHARS} characters"
            )
        review = self.normalizer(raw_review)
        if not review:
            raise ValueError("Review text becomes blank after normalization")

        model_inputs = [
            (f"目标球线：{string_name}\n评价方面：{aspect_name}\n评论：{review}")
            for _, aspect_name in ASPECTS
        ]
        encoded = self.tokenizer(
            model_inputs,
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        with self.torch.inference_mode():
            logits = self.model(**encoded).logits.float()
            probabilities = self.torch.softmax(logits, dim=-1).cpu().tolist()

        if len(probabilities) != len(ASPECTS) or any(
            len(row) != len(BERT_LABELS) for row in probabilities
        ):
            raise RuntimeError("The model returned an unexpected probability shape")

        results: list[dict[str, object]] = []
        for (aspect, aspect_name), values in zip(ASPECTS, probabilities, strict=True):
            predicted_id = max(range(len(values)), key=values.__getitem__)
            predicted_label = BERT_LABELS[predicted_id]
            results.append(
                {
                    "aspect": aspect,
                    "aspect_name": ASPECT_DISPLAY_NAMES[aspect],
                    "label": predicted_label,
                    "label_name": LABEL_NAMES[predicted_label],
                    "confidence": float(values[predicted_id]),
                    "probabilities": {
                        label: float(value)
                        for label, value in zip(BERT_LABELS, values, strict=True)
                    },
                }
            )
        return {
            "model": self.model_label,
            "device": self.device,
            "string_name": string_name,
            "review_text": raw_review,
            "aspect_count": len(results),
            "aspects": results,
        }


def render_page(string_names: tuple[str, ...], model_label: str) -> str:
    options = "\n".join(
        f'<option value="{html.escape(name, quote=True)}"'
        f"{' selected' if index == 0 else ''}>"
        f"{html.escape(name)}</option>"
        for index, name in enumerate(string_names)
    )
    page = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StringSence · Nine-aspect review analysis</title>
  <style>
    :root { color-scheme: light; --ink: #17221c; --muted: #647168; --line: #dce5df; --paper: #f6f8f5; --card: #ffffff; --accent: #177245; --accent-dark: #0e4d30; }
    * { box-sizing: border-box; }
    [hidden] { display: none !important; }
    body { margin: 0; min-height: 100vh; background: var(--paper); color: var(--ink); font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    .shell { width: min(1080px, calc(100% - 32px)); margin: 0 auto; padding: 48px 0 72px; }
    .eyebrow { margin: 0 0 8px; color: var(--accent); font-size: 12px; font-weight: 800; letter-spacing: .14em; }
    h1 { margin: 0; font-size: clamp(30px, 5vw, 52px); letter-spacing: -.04em; }
    .lead { max-width: 680px; margin: 14px 0 28px; color: var(--muted); }
    .grid { display: grid; grid-template-columns: minmax(260px, .8fr) minmax(0, 1.5fr); gap: 20px; align-items: start; }
    .card { background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 22px; box-shadow: 0 12px 30px rgba(23, 34, 28, .05); }
    label { display: block; margin: 0 0 16px; font-weight: 700; }
    select, textarea { width: 100%; margin-top: 8px; border: 1px solid var(--line); border-radius: 10px; background: #fbfdfb; color: var(--ink); font: inherit; padding: 11px 12px; }
    select:focus, textarea:focus { outline: 3px solid rgba(23, 114, 69, .18); border-color: var(--accent); }
    textarea { min-height: 160px; resize: vertical; }
    button { width: 100%; border: 0; border-radius: 10px; padding: 12px 16px; background: var(--accent); color: #fff; cursor: pointer; font: inherit; font-weight: 800; }
    button:hover { background: var(--accent-dark); }
    button:disabled { cursor: wait; opacity: .65; }
    .note, .status, .meta { color: var(--muted); font-size: 13px; }
    .note { margin: 16px 0 0; }
    .status { min-height: 22px; margin: 14px 0 0; }
    .status.error { color: #a13a2e; }
    .result-card { overflow: hidden; }
    .result-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; margin-bottom: 18px; }
    .result-head h2 { margin: 0; font-size: 22px; }
    .summary { margin: 0 0 16px; color: var(--muted); }
    .table-wrap { overflow-x: auto; }
    table { width: 100%; min-width: 620px; border-collapse: collapse; }
    th, td { padding: 12px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: middle; }
    th { color: var(--muted); font-size: 12px; font-weight: 800; letter-spacing: .04em; text-transform: uppercase; }
    .label { display: inline-block; border-radius: 999px; padding: 4px 9px; font-size: 13px; font-weight: 800; }
    .label-positive { background: #dcf4e6; color: #116239; }
    .label-negative { background: #fde5e1; color: #9b3227; }
    .label-not_mentioned { background: #edf0ee; color: #5d6961; }
    .probability { display: grid; grid-template-columns: 48px 1fr; gap: 8px; align-items: center; min-width: 120px; font-size: 12px; color: var(--muted); }
    .meter { height: 6px; overflow: hidden; border-radius: 99px; background: #edf1ee; }
    .meter i { display: block; height: 100%; border-radius: inherit; background: var(--accent); }
    .meter i.negative { background: #c95c4f; }
    .meter i.neutral { background: #89968d; }
    .empty { display: grid; min-height: 310px; place-items: center; color: var(--muted); text-align: center; }
    @media (max-width: 760px) { .shell { padding-top: 30px; } .grid { grid-template-columns: 1fr; } .card { padding: 18px; } }
  </style>
</head>
<body>
  <main class="shell">
    <p class="eyebrow">LOCAL OFFLINE MODEL</p>
    <h1>Analyze one review across nine aspects</h1>
    <p class="lead">Select a string and enter one review. StringSence will classify attack and repulsion, comfort, control, durability, elasticity, sound, string movement, tension retention, and value for money.</p>
    <div class="grid">
      <section class="card">
        <form id="analysis-form">
          <label for="string-name">String
            <select id="string-name" required>__OPTIONS__</select>
          </label>
          <label for="review-text">Review
            <textarea id="review-text" maxlength="5000" required>The string feels stable and comfortable, but durability is average.</textarea>
          </label>
          <button id="analyze-button" type="submit">Analyze all 9 aspects</button>
          <p class="status" id="status" role="status"></p>
          <p class="note">Model: __MODEL_LABEL__<br>Local offline inference; results are not written to the database or recommendation matrix.</p>
        </form>
      </section>
      <section class="card result-card" aria-live="polite">
        <div class="empty" id="empty-state">Submit a review to see results for all 9 aspects.</div>
        <div id="result-state" hidden>
          <div class="result-head">
            <h2>Analysis results</h2>
            <span class="meta" id="model-meta"></span>
          </div>
          <p class="summary" id="summary"></p>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Aspect</th><th>Prediction</th><th>Confidence</th><th>Positive</th><th>Negative</th><th>Not mentioned</th></tr></thead>
              <tbody id="result-rows"></tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  </main>
  <script>
    const form = document.getElementById("analysis-form");
    const button = document.getElementById("analyze-button");
    const status = document.getElementById("status");
    const emptyState = document.getElementById("empty-state");
    const resultState = document.getElementById("result-state");
    const rows = document.getElementById("result-rows");
    const summary = document.getElementById("summary");
    const modelMeta = document.getElementById("model-meta");

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (character) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
      }[character]));
    }

    function percentage(value) {
      return `${(Number(value) * 100).toFixed(1)}%`;
    }

    function width(value) {
      return Math.max(0, Math.min(100, Number(value) * 100)).toFixed(1);
    }

    function probabilityCell(value, tone) {
      return `<div class="probability"><span>${percentage(value)}</span><span class="meter"><i class="${tone}" style="width:${width(value)}%"></i></span></div>`;
    }

    function renderResults(data) {
      const counts = data.aspects.reduce((result, row) => {
        result[row.label_name] = (result[row.label_name] || 0) + 1;
        return result;
      }, {});
      summary.textContent = `${data.aspect_count} aspects: ${Object.entries(counts).map(([key, value]) => `${key} ${value}`).join(" · ")}`;
      modelMeta.textContent = `${data.device} · ${data.model}`;
      rows.innerHTML = data.aspects.map((row) => {
        const probabilities = row.probabilities;
        return `<tr>
          <td><strong>${escapeHtml(row.aspect_name)}</strong></td>
          <td><span class="label label-${escapeHtml(row.label)}">${escapeHtml(row.label_name)}</span></td>
          <td>${percentage(row.confidence)}</td>
          <td>${probabilityCell(probabilities.positive, "")}</td>
          <td>${probabilityCell(probabilities.negative, "negative")}</td>
          <td>${probabilityCell(probabilities.not_mentioned, "neutral")}</td>
        </tr>`;
      }).join("");
      emptyState.hidden = true;
      resultState.hidden = false;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      button.disabled = true;
      status.className = "status";
      status.textContent = "Analyzing with the model, please wait…";
      try {
        const response = await fetch("/api/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            string_name: document.getElementById("string-name").value,
            review_text: document.getElementById("review-text").value
          })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Analysis failed");
        renderResults(data);
        status.textContent = "Analysis complete.";
      } catch (error) {
        status.className = "status error";
        status.textContent = error.message || "Analysis failed; check the demo logs.";
      } finally {
        button.disabled = false;
      }
    });
  </script>
</body>
</html>
"""
    return page.replace("__OPTIONS__", options).replace(
        "__MODEL_LABEL__", html.escape(model_label)
    )


def build_handler(analyzer: ReviewAnalyzer) -> type[BaseHTTPRequestHandler]:
    class DemoHandler(BaseHTTPRequestHandler):
        server_version = "StringSenceBertDemo/1.0"

        def _send_bytes(self, status_code: int, content_type: str, body: bytes) -> None:
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            if content_type.startswith("text/html"):
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'",
                )
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send_bytes(status_code, "application/json; charset=utf-8", body)

        def _read_json(self) -> dict[str, object]:
            content_length = self.headers.get("Content-Length")
            if content_length is None:
                raise ValueError("Request body is required")
            try:
                body_size = int(content_length)
            except ValueError as exc:
                raise ValueError("Invalid request body") from exc
            if body_size < 0 or body_size > MAX_BODY_BYTES:
                raise ValueError("Request body is too large")
            try:
                payload = json.loads(self.rfile.read(body_size).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("Request body must be valid UTF-8 JSON") from exc
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            if path in {"/", "/index.html"}:
                body = render_page(analyzer.string_names, analyzer.model_label).encode(
                    "utf-8"
                )
                self._send_bytes(200, "text/html; charset=utf-8", body)
            elif path == "/health":
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "device": analyzer.device,
                        "aspect_count": len(ASPECTS),
                    },
                )
            else:
                self._send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            if urlsplit(self.path).path != "/api/analyze":
                self._send_json(404, {"error": "Not found"})
                return
            try:
                payload = self._read_json()
                string_name = payload.get("string_name")
                review_text = payload.get("review_text")
                if not isinstance(string_name, str) or not isinstance(review_text, str):
                    raise ValueError("string_name and review_text must be strings")
                result = analyzer.analyze(string_name, review_text)
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            except Exception as exc:
                print(f"inference error: {exc}", file=sys.stderr)
                self._send_json(
                    500, {"error": "Model inference failed; check the demo logs."}
                )
                return
            self._send_json(200, result)

    return DemoHandler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the one-file local StringSence nine-aspect BERT demo"
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=DEFAULT_MODEL_DIR,
        help="local Hugging Face model directory",
    )
    parser.add_argument(
        "--model-label",
        default=DEFAULT_MODEL_LABEL,
        help="label shown in the demo; does not change model loading",
    )
    parser.add_argument(
        "--cohort-path",
        type=Path,
        default=COHORT_PATH,
        help="approved string cohort CSV path",
    )
    parser.add_argument(
        "--normalization-path",
        type=Path,
        default=NORMALIZATION_PATH,
        help="normalization rules CSV path",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--device", choices=("auto", "cpu", "mps"), default="auto")
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="load the model and run one nine-aspect inference, then exit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        string_names = load_string_names(args.cohort_path)
        normalizer = load_normalizer(args.normalization_path)
        analyzer = ReviewAnalyzer(
            args.model_dir,
            string_names,
            device=args.device,
            model_label=args.model_label,
            normalizer=normalizer,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Unable to start demo: {exc}", file=sys.stderr)
        return 2

    if args.self_check:
        result = analyzer.analyze(
            string_names[0], "控球稳定，声音清脆，弹性不错，但耐久一般。"
        )
        assert result["aspect_count"] == len(ASPECTS)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "model": result["model"],
                    "device": result["device"],
                    "aspect_count": result["aspect_count"],
                },
                ensure_ascii=False,
            )
        )
        return 0

    handler = build_handler(analyzer)
    try:
        server = HTTPServer((args.host, args.port), handler)
    except OSError as exc:
        print(f"Unable to bind http://{args.host}:{args.port}: {exc}", file=sys.stderr)
        return 2

    print(f"Model loaded: {analyzer.model_dir}")
    print(f"Device: {analyzer.device}")
    print(f"Open: http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDemo stopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
