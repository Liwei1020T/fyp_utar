from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
from time import perf_counter

import nbformat
from nbclient import NotebookClient


WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH / "src"))

from stringsense_nlp.boundary import assert_inputs_unchanged  # noqa: E402
from stringsense_nlp.boundary import fingerprint_inputs  # noqa: E402
from stringsense_nlp.boundary import fingerprint_protected_assets  # noqa: E402
from stringsense_nlp.boundary import read_json  # noqa: E402
from stringsense_nlp.boundary import run_root  # noqa: E402
from stringsense_nlp.boundary import sha256_file  # noqa: E402
from stringsense_nlp.boundary import utc_now  # noqa: E402
from stringsense_nlp.boundary import validate_run_id  # noqa: E402
from stringsense_nlp.boundary import write_json_exclusive  # noqa: E402


NOTEBOOKS = (
    "stringsense_absa_labeling_notebook_latest.ipynb",
    "stringsense_complete_absa_pipeline_notebook_latest.ipynb",
)


def execute_notebook(source: Path, destination: Path, kernel_name: str) -> None:
    with source.open("r", encoding="utf-8") as handle:
        notebook = nbformat.read(handle, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=3600,
        kernel_name=kernel_name,
        allow_errors=False,
        shutdown_kernel="immediate",
    )
    client.execute(cwd=str(WORKBENCH))
    with destination.open("x", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)


def execute_run(run_id: str, kernel_name: str) -> dict[str, object]:
    before = fingerprint_inputs(WORKBENCH)
    protected_before = fingerprint_protected_assets(WORKBENCH)
    started_at = utc_now()
    started = perf_counter()
    previous_run_id = os.environ.get("STRINGSENSE_NLP_RUN_ID")
    os.environ["STRINGSENSE_NLP_RUN_ID"] = run_id
    try:
        labeling_source = WORKBENCH / NOTEBOOKS[0]
        execute_notebook(
            labeling_source,
            run_root(WORKBENCH, run_id) / "labeling/executed_notebook.ipynb",
            kernel_name,
        )
        pipeline_source = WORKBENCH / NOTEBOOKS[1]
        execute_notebook(
            pipeline_source,
            run_root(WORKBENCH, run_id) / "pipeline/executed_notebook.ipynb",
            kernel_name,
        )
    finally:
        if previous_run_id is None:
            os.environ.pop("STRINGSENSE_NLP_RUN_ID", None)
        else:
            os.environ["STRINGSENSE_NLP_RUN_ID"] = previous_run_id

    after = fingerprint_inputs(WORKBENCH)
    assert_inputs_unchanged(before, after)
    protected_after = fingerprint_protected_assets(WORKBENCH)
    assert_inputs_unchanged(protected_before, protected_after)
    root = run_root(WORKBENCH, run_id)
    report = {
        "run_id": run_id,
        "status": "completed",
        "started_at": started_at,
        "completed_at": utc_now(),
        "elapsed_seconds": round(perf_counter() - started, 3),
        "kernel_name": kernel_name,
        "python_executable": sys.executable,
        "protected_inputs_unchanged": True,
        "input_fingerprints": before,
        "protected_assets_unchanged": True,
        "protected_asset_fingerprints": protected_before,
        "executed_notebooks": [
            {
                "path": "labeling/executed_notebook.ipynb",
                "sha256": sha256_file(root / "labeling/executed_notebook.ipynb"),
            },
            {
                "path": "pipeline/executed_notebook.ipynb",
                "sha256": sha256_file(root / "pipeline/executed_notebook.ipynb"),
            },
        ],
    }
    write_json_exclusive(root / "execution_report.json", report)
    return report


def reproducibility_signature(run_id: str) -> dict[str, object]:
    manifest = read_json(run_root(WORKBENCH, run_id) / "run_manifest.json")
    csv_hashes = {
        str(artifact["path"]): str(artifact["sha256"])
        for artifact in manifest["artifacts"]
        if str(artifact["path"]).endswith(".csv")
    }
    return {
        "metrics": manifest["stages"]["pipeline"]["summary"]["metrics"],
        "csv_hashes": csv_hashes,
    }


def parse_args() -> argparse.Namespace:
    default_run_id = datetime.now(UTC).strftime("run-%Y%m%dT%H%M%SZ")
    parser = argparse.ArgumentParser(
        description="Execute the canonical StringSense NLP notebooks in immutable runs."
    )
    parser.add_argument("--run-id", default=default_run_id)
    parser.add_argument("--repeat", type=int, choices=(1, 2), default=1)
    parser.add_argument("--kernel", default="stringsense-nlp")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_run_id(args.run_id)
    kernel_path = WORKBENCH / ".venv/share/jupyter"
    existing_jupyter_path = os.environ.get("JUPYTER_PATH")
    os.environ["JUPYTER_PATH"] = os.pathsep.join(
        value for value in (str(kernel_path), existing_jupyter_path) if value
    )
    run_ids = (
        [args.run_id]
        if args.repeat == 1
        else [f"{args.run_id}-r1", f"{args.run_id}-r2"]
    )
    reports = [execute_run(run_id, args.kernel) for run_id in run_ids]
    result: dict[str, object] = {"runs": reports}
    if len(run_ids) == 2:
        signatures = [reproducibility_signature(run_id) for run_id in run_ids]
        reproducible = signatures[0] == signatures[1]
        reproducibility_report = {
            "schema_version": "stringsense.nlp-reproducibility.v1",
            "run_ids": run_ids,
            "created_at": utc_now(),
            "metrics_and_csv_hashes_match": reproducible,
            "signatures": signatures,
        }
        report_path = WORKBENCH / "output/runs" / f"{args.run_id}-reproducibility.json"
        write_json_exclusive(report_path, reproducibility_report)
        result["reproducibility_report"] = str(report_path)
        result["reproducible"] = reproducible
        if not reproducible:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
