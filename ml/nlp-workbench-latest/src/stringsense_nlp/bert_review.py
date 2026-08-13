from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
import math
from pathlib import Path
import sys

import pandas as pd

from .bert import ASPECT_DISPLAY_NAMES
from .bert_inference import aggregate_candidate_cells
from .bert_inference import build_candidate_matrix
from .bert_inference import build_current_comparison
from .bert_inference import choose_pilot_threshold
from .bert_inference import load_inference_catalog
from .bert_inference import mark_aggregation_status
from .bert_inference import threshold_analysis
from .boundary import RUN_SCHEMA_VERSION
from .boundary import artifact_records
from .boundary import assert_inputs_unchanged
from .boundary import create_stage_directory
from .boundary import fingerprint_inputs
from .boundary import fingerprint_protected_assets
from .boundary import read_json
from .boundary import resolve_workbench
from .boundary import run_root
from .boundary import runtime_versions
from .boundary import sha256_file
from .boundary import utc_now
from .boundary import write_json_exclusive
from .foundation import load_string_mappings
from .foundation import normalize_string_name


REVIEW_SCHEMA_VERSION = "stringsense.bert-candidate-review.v2"
SENSITIVITY_SCHEMA_VERSION = "stringsense.bert-threshold-sensitivity.v1"
RECOMMENDATION_OPTIMIZATION_SCHEMA_VERSION = (
    "stringsense.bert-recommendation-optimization.v1"
)
SYSTEM_CATALOG_SNAPSHOT_SCHEMA_VERSION = (
    "stringsense.recommendation-catalog-snapshot.v1"
)
REVIEWED_VERDICTS = {"model_supported", "silver_supported", "ambiguous"}
REVIEW_THRESHOLDS = (0.99, 0.995)
DESCRIPTIVE_NEAR_TIE_EPSILON = 0.005
OPTIMIZED_PREFERENCE_WEIGHT_EXPONENT = 2.0
SUPPORT_FEATURES = (
    "stability_score",
    "all_round_score",
    "attacking_fit_score",
    "control_fit_score",
)
FIXED_PROFILES = (
    {
        "profile_id": "beginner_comfort_durability",
        "skill_level": "beginner",
        "playing_style": "balanced",
        "preferred_tension": 22,
        "frequency_per_week": 1,
        "preferred_feel": "soft",
        "preferred_gauge": "thin",
        "recent_goal": "comfort",
        "pref_attack": 3,
        "pref_comfort": 9,
        "pref_control": 6,
        "pref_durability": 9,
        "pref_elasticity": 5,
        "pref_sound": 3,
        "pref_string_movement": 6,
        "pref_tension_retention": 7,
        "pref_value_for_money": 9,
    },
    {
        "profile_id": "advanced_attacking",
        "skill_level": "advanced",
        "playing_style": "attacking",
        "preferred_tension": 28,
        "frequency_per_week": 4,
        "preferred_feel": "hard",
        "preferred_gauge": "thick",
        "recent_goal": "power",
        "pref_attack": 10,
        "pref_comfort": 3,
        "pref_control": 6,
        "pref_durability": 5,
        "pref_elasticity": 9,
        "pref_sound": 8,
        "pref_string_movement": 5,
        "pref_tension_retention": 7,
        "pref_value_for_money": 3,
    },
    {
        "profile_id": "control_defensive",
        "skill_level": "intermediate",
        "playing_style": "control_defensive",
        "preferred_tension": 26,
        "frequency_per_week": 3,
        "preferred_feel": "medium",
        "preferred_gauge": "medium",
        "recent_goal": "control",
        "pref_attack": 5,
        "pref_comfort": 6,
        "pref_control": 10,
        "pref_durability": 6,
        "pref_elasticity": 6,
        "pref_sound": 4,
        "pref_string_movement": 10,
        "pref_tension_retention": 8,
        "pref_value_for_money": 5,
    },
    {
        "profile_id": "frequent_durability",
        "skill_level": "intermediate",
        "playing_style": "balanced",
        "preferred_tension": 25,
        "frequency_per_week": 5,
        "preferred_feel": "medium",
        "preferred_gauge": "thick",
        "recent_goal": "durability",
        "pref_attack": 5,
        "pref_comfort": 7,
        "pref_control": 6,
        "pref_durability": 10,
        "pref_elasticity": 5,
        "pref_sound": 4,
        "pref_string_movement": 7,
        "pref_tension_retention": 10,
        "pref_value_for_money": 8,
    },
    {
        "profile_id": "all_round",
        "skill_level": "intermediate",
        "playing_style": "balanced",
        "preferred_tension": 25,
        "frequency_per_week": 2,
        "preferred_feel": "medium",
        "preferred_gauge": "no_preference",
        "recent_goal": "balanced",
        "pref_attack": 7,
        "pref_comfort": 7,
        "pref_control": 7,
        "pref_durability": 7,
        "pref_elasticity": 7,
        "pref_sound": 7,
        "pref_string_movement": 7,
        "pref_tension_retention": 7,
        "pref_value_for_money": 7,
    },
    {
        "profile_id": "comfort_sound_recreational",
        "skill_level": "intermediate",
        "playing_style": "balanced",
        "preferred_tension": 22,
        "frequency_per_week": 1,
        "preferred_feel": "soft",
        "preferred_gauge": "thick",
        "recent_goal": "comfort",
        "pref_attack": 2,
        "pref_comfort": 10,
        "pref_control": 6,
        "pref_durability": 2,
        "pref_elasticity": 6,
        "pref_sound": 10,
        "pref_string_movement": 2,
        "pref_tension_retention": 2,
        "pref_value_for_money": 3,
    },
    {
        "profile_id": "fast_repulsion_elasticity",
        "skill_level": "advanced",
        "playing_style": "attacking",
        "preferred_tension": 24,
        "frequency_per_week": 3,
        "preferred_feel": "hard",
        "preferred_gauge": "medium",
        "recent_goal": "power",
        "pref_attack": 10,
        "pref_comfort": 2,
        "pref_control": 4,
        "pref_durability": 2,
        "pref_elasticity": 10,
        "pref_sound": 8,
        "pref_string_movement": 2,
        "pref_tension_retention": 2,
        "pref_value_for_money": 3,
    },
    {
        "profile_id": "high_tension_retention",
        "skill_level": "advanced",
        "playing_style": "control_defensive",
        "preferred_tension": 29,
        "frequency_per_week": 4,
        "preferred_feel": "hard",
        "preferred_gauge": "thick",
        "recent_goal": "tension_retention",
        "pref_attack": 4,
        "pref_comfort": 4,
        "pref_control": 8,
        "pref_durability": 7,
        "pref_elasticity": 4,
        "pref_sound": 3,
        "pref_string_movement": 8,
        "pref_tension_retention": 10,
        "pref_value_for_money": 5,
    },
    {
        "profile_id": "value_durability",
        "skill_level": "intermediate",
        "playing_style": "balanced",
        "preferred_tension": 23,
        "frequency_per_week": 4,
        "preferred_feel": "medium",
        "preferred_gauge": "thick",
        "recent_goal": "value_for_money",
        "pref_attack": 3,
        "pref_comfort": 6,
        "pref_control": 5,
        "pref_durability": 10,
        "pref_elasticity": 3,
        "pref_sound": 2,
        "pref_string_movement": 5,
        "pref_tension_retention": 8,
        "pref_value_for_money": 10,
    },
    {
        "profile_id": "movement_control_specialist",
        "skill_level": "intermediate",
        "playing_style": "control_defensive",
        "preferred_tension": 25,
        "frequency_per_week": 2,
        "preferred_feel": "medium",
        "preferred_gauge": "medium",
        "recent_goal": "control",
        "pref_attack": 3,
        "pref_comfort": 4,
        "pref_control": 10,
        "pref_durability": 4,
        "pref_elasticity": 3,
        "pref_sound": 2,
        "pref_string_movement": 10,
        "pref_tension_retention": 4,
        "pref_value_for_money": 5,
    },
)


def build_threshold_comparison(
    evidence: pd.DataFrame,
    candidates: Iterable[float] = REVIEW_THRESHOLDS,
) -> pd.DataFrame:
    tables = []
    for split in ("val", "test"):
        table = threshold_analysis(evidence, candidates=candidates, split=split)
        table = table.rename(columns={"silver_test_rows": "silver_rows"})
        table.insert(0, "split", split)
        selected = choose_pilot_threshold(table)
        table["selected_under_existing_policy"] = table["confidence_threshold"].eq(
            selected
        )
        tables.append(table)
    return pd.concat(tables, ignore_index=True)


def build_operational_review(
    evidence: pd.DataFrame,
    decisions: pd.DataFrame,
    threshold: float,
) -> pd.DataFrame:
    required = {
        "source_sample_id",
        "assistant_operational_verdict",
        "error_type",
        "review_note",
    }
    missing = sorted(required.difference(decisions.columns))
    if missing:
        raise ValueError(f"Operational review decisions are missing columns: {missing}")
    invalid = sorted(
        set(decisions["assistant_operational_verdict"]).difference(REVIEWED_VERDICTS)
    )
    if invalid:
        raise ValueError(f"Unsupported operational review verdicts: {invalid}")
    if decisions["source_sample_id"].duplicated().any():
        raise ValueError("Operational review decisions contain duplicate sample IDs")

    silver_present = evidence["source_silver_label"].notna() & evidence[
        "source_silver_label"
    ].ne("")
    mismatches = evidence[
        evidence["split"].eq("test")
        & silver_present
        & evidence["confidence"].ge(threshold)
        & evidence["predicted_label"].ne("not_mentioned")
        & evidence["predicted_label"].ne(evidence["source_silver_label"])
    ].copy()
    expected_ids = set(mismatches["source_sample_id"])
    decision_ids = set(decisions["source_sample_id"])
    if expected_ids != decision_ids:
        raise ValueError(
            "Operational review decisions must cover exactly the accepted test "
            f"disagreements; missing={sorted(expected_ids - decision_ids)}, "
            f"unexpected={sorted(decision_ids - expected_ids)}"
        )

    reviewed = mismatches.merge(decisions, on="source_sample_id", validate="one_to_one")
    reviewed.insert(0, "review_status", "codex_assisted_pending_owner_approval")
    reviewed.insert(1, "human_gold", False)
    reviewed.insert(2, "kappa_eligible", False)
    return reviewed.sort_values(["aspect", "source_sample_id"]).reset_index(drop=True)


def build_cell_stability(cells: pd.DataFrame) -> pd.DataFrame:
    output = cells.copy()
    bounds = [
        _wilson_interval(
            int(row.positive_evidence_count), int(row.accepted_evidence_count)
        )
        for row in output.itertuples()
    ]
    output["positive_share_wilson_95_lower"] = [value[0] for value in bounds]
    output["positive_share_wilson_95_upper"] = [value[1] for value in bounds]
    output["positive_share_wilson_95_width"] = (
        output["positive_share_wilson_95_upper"]
        - output["positive_share_wilson_95_lower"]
    )
    output["score_1_to_5_wilson_95_lower"] = 1 + (
        4 * output["positive_share_wilson_95_lower"]
    )
    output["score_1_to_5_wilson_95_upper"] = 1 + (
        4 * output["positive_share_wilson_95_upper"]
    )
    output["interval_assumption"] = "independent_binomial_directional_mentions"
    return output


def build_evidence_status_delta(
    evidence: pd.DataFrame,
    threshold: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sensitivity = mark_aggregation_status(evidence, threshold)
    delta = sensitivity.copy()
    delta.insert(
        delta.columns.get_loc("aggregation_status"),
        "source_aggregation_status",
        evidence["aggregation_status"].to_numpy(),
    )
    delta = delta.rename(
        columns={"aggregation_status": "sensitivity_aggregation_status"}
    )
    changed = delta[
        delta["source_aggregation_status"].ne(delta["sensitivity_aggregation_status"])
    ].copy()
    return sensitivity, changed


def compare_candidate_cells(
    sensitivity: pd.DataFrame,
    confirmed: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "canonical_string_name",
        "aspect",
        "accepted_evidence_count",
        "positive_evidence_count",
        "negative_evidence_count",
        "normalized_score_0_to_1",
        "score_1_to_5",
    ]
    comparison = confirmed[columns].merge(
        sensitivity[columns],
        on=["canonical_string_name", "aspect"],
        suffixes=("_confirmed", "_sensitivity"),
        validate="one_to_one",
    )
    comparison["accepted_evidence_added"] = (
        comparison["accepted_evidence_count_sensitivity"]
        - comparison["accepted_evidence_count_confirmed"]
    )
    comparison["normalized_score_delta"] = (
        comparison["normalized_score_0_to_1_sensitivity"]
        - comparison["normalized_score_0_to_1_confirmed"]
    )
    comparison["score_1_to_5_delta"] = (
        comparison["score_1_to_5_sensitivity"] - comparison["score_1_to_5_confirmed"]
    )
    return comparison


def _wilson_interval(positive: int, total: int) -> tuple[float, float]:
    if total <= 0:
        return (math.nan, math.nan)
    z = 1.959963984540054
    share = positive / total
    denominator = 1 + (z**2 / total)
    center = (share + (z**2 / (2 * total))) / denominator
    half_width = (
        z
        * math.sqrt((share * (1 - share) / total) + (z**2 / (4 * total**2)))
        / denominator
    )
    return (center - half_width, center + half_width)


def build_followup_sample(
    evidence: pd.DataFrame,
    cells: pd.DataFrame,
    comparison: pd.DataFrame,
    reviewed_ids: set[str],
) -> pd.DataFrame:
    selected: list[pd.DataFrame] = []
    high_delta = comparison.assign(
        absolute_difference=comparison["candidate_minus_current"].abs()
    ).nlargest(10, "absolute_difference")[["canonical_string_name", "aspect"]]
    low_evidence = cells.nsmallest(5, "accepted_evidence_count")[
        ["canonical_string_name", "aspect"]
    ]
    for reason, targets in (
        ("high_matrix_delta", high_delta),
        ("low_accepted_evidence", low_evidence),
    ):
        for target in targets.itertuples(index=False):
            group = evidence[
                evidence["canonical_string_name"].eq(target.canonical_string_name)
                & evidence["aspect"].eq(target.aspect)
                & evidence["aggregation_status"].eq("accepted_directional")
                & ~evidence["source_sample_id"].isin(reviewed_ids)
            ]
            sample = (
                group.sort_values("confidence", ascending=False)
                .groupby("predicted_label", sort=False)
                .head(1)
                .copy()
            )
            sample.insert(0, "selection_reason", reason)
            selected.append(sample)
    if not selected:
        return pd.DataFrame()
    output = pd.concat(selected, ignore_index=True)
    output = output.drop_duplicates("source_sample_id", keep="first")
    output.insert(0, "review_status", "pending_owner_operational_review")
    return output.sort_values(["selection_reason", "aspect", "source_sample_id"])


def build_fixed_profile_comparison(
    *,
    workbench: Path,
    cells: pd.DataFrame,
    system_facts: dict[str, dict[str, object]] | None = None,
    preference_weight_exponent: float = 1.0,
    active_only: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    components = _load_backend_components(workbench)
    catalog = _load_catalog_records(workbench)
    current = _load_current_matrix(workbench, set(catalog))
    candidates = {
        matrix_name: _build_candidates(
            catalog,
            current,
            cells,
            matrix_name=matrix_name,
            components=components,
            system_facts=system_facts,
        )
        for matrix_name in ("current_v9", "macbert_candidate")
    }
    if active_only:
        candidates = {
            matrix_name: [
                candidate for candidate in matrix_candidates if candidate.item.is_active
            ]
            for matrix_name, matrix_candidates in candidates.items()
        }

    rankings: list[dict[str, object]] = []
    scorer = components["scorer"](preference_weight_exponent=preference_weight_exponent)
    request_model = components["request_model"]
    for profile in FIXED_PROFILES:
        request = request_model(
            user_id=f"offline-{profile['profile_id']}",
            top_n=len(catalog),
            **{key: value for key, value in profile.items() if key != "profile_id"},
        )
        for matrix_name, matrix_candidates in candidates.items():
            scored = scorer.score_candidates(
                candidates=matrix_candidates,
                request=request,
                top_n=len(matrix_candidates),
            )
            for entry in scored:
                result = entry.result
                breakdown = result.score_breakdown or {}
                rankings.append(
                    {
                        "profile_id": profile["profile_id"],
                        "matrix": matrix_name,
                        "rank": result.rank,
                        "catalog_id": result.catalog_id,
                        "string_name": result.string_name,
                        "final_score": result.score,
                        "preference_match": breakdown.get("preference_match"),
                        "rule_fit": breakdown.get("rule_fit"),
                        "value_for_money": breakdown.get("value_for_money"),
                        "nlp_review_score": breakdown.get("nlp_review_score"),
                    }
                )
    ranking_table = pd.DataFrame(rankings)
    movements, summary = summarize_profile_movements(ranking_table)
    return ranking_table, movements, summary, str(components["algorithm_version"])


def summarize_profile_movements(
    rankings: pd.DataFrame,
    *,
    baseline_matrix: str = "current_v9",
    candidate_matrix: str = "macbert_candidate",
    baseline_label: str = "current_v9",
    candidate_label: str = "candidate",
    score_delta_column: str = "score_delta_candidate_minus_v9",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline = rankings[rankings["matrix"].eq(baseline_matrix)].drop(columns="matrix")
    candidate = rankings[rankings["matrix"].eq(candidate_matrix)].drop(columns="matrix")
    movements = baseline.merge(
        candidate,
        on=["profile_id", "catalog_id", "string_name"],
        suffixes=(f"_{baseline_label}", f"_{candidate_label}"),
        validate="one_to_one",
    )
    baseline_rank = f"rank_{baseline_label}"
    candidate_rank = f"rank_{candidate_label}"
    rank_change = f"rank_improvement_{candidate_label}"
    score_delta = score_delta_column
    movements[rank_change] = movements[baseline_rank] - movements[candidate_rank]
    movements[score_delta] = (
        movements[f"final_score_{candidate_label}"]
        - movements[f"final_score_{baseline_label}"]
    )

    rows = []
    for profile_id, group in movements.groupby("profile_id", sort=False):
        baseline_top = group.nsmallest(5, baseline_rank)
        candidate_top = group.nsmallest(5, candidate_rank)
        baseline_ids = baseline_top.sort_values(baseline_rank)["catalog_id"].tolist()
        candidate_ids = candidate_top.sort_values(candidate_rank)["catalog_id"].tolist()
        rows.append(
            {
                "profile_id": profile_id,
                f"{baseline_label}_top_ids": "|".join(map(str, baseline_ids)),
                f"{candidate_label}_top_ids": "|".join(map(str, candidate_ids)),
                "top1_changed": baseline_ids[0] != candidate_ids[0],
                "top5_overlap": len(set(baseline_ids).intersection(candidate_ids)),
                "maximum_absolute_rank_change": int(group[rank_change].abs().max()),
                "mean_absolute_score_delta": float(group[score_delta].abs().mean()),
            }
        )
    return movements, pd.DataFrame(rows)


def build_profile_audit(
    rankings: pd.DataFrame,
    *,
    matrix_name: str = "macbert_candidate",
    near_tie_epsilon: float = DESCRIPTIVE_NEAR_TIE_EPSILON,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = rankings[rankings["matrix"].eq(matrix_name)].copy()
    if selected.empty:
        raise ValueError(f"Profile rankings do not contain matrix: {matrix_name}")

    outcomes = []
    for profile_id, group in selected.groupby("profile_id", sort=False):
        ordered = group.sort_values("rank")
        if len(ordered) < 2:
            raise ValueError(f"Profile requires at least two candidates: {profile_id}")
        top = ordered.iloc[0]
        runner_up = ordered.iloc[1]
        margin = round(float(top["final_score"] - runner_up["final_score"]), 4)
        outcomes.append(
            {
                "profile_id": profile_id,
                "top1_catalog_id": top["catalog_id"],
                "top1_string_name": top["string_name"],
                "top1_score": float(top["final_score"]),
                "runner_up_catalog_id": runner_up["catalog_id"],
                "runner_up_string_name": runner_up["string_name"],
                "runner_up_score": float(runner_up["final_score"]),
                "top1_margin": margin,
                "descriptive_near_tie": margin <= near_tie_epsilon,
                "near_tie_epsilon": near_tie_epsilon,
                "top3_catalog_ids": "|".join(ordered.head(3)["catalog_id"].astype(str)),
            }
        )

    selected["top1"] = selected["rank"].le(1)
    selected["top3"] = selected["rank"].le(3)
    selected["top5"] = selected["rank"].le(5)
    coverage = (
        selected.groupby(["catalog_id", "string_name"], as_index=False)
        .agg(
            top1_appearances=("top1", "sum"),
            top3_appearances=("top3", "sum"),
            top5_appearances=("top5", "sum"),
            best_rank=("rank", "min"),
            mean_rank=("rank", "mean"),
            mean_final_score=("final_score", "mean"),
        )
        .sort_values(
            ["top3_appearances", "top5_appearances", "mean_rank"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)
    )
    coverage.insert(0, "profiles_evaluated", selected["profile_id"].nunique())
    coverage["mean_rank"] = coverage["mean_rank"].round(2)
    coverage["mean_final_score"] = coverage["mean_final_score"].round(4)
    coverage["appears_in_top5"] = coverage["top5_appearances"].gt(0)
    return pd.DataFrame(outcomes), coverage


def load_system_catalog_snapshot(
    path: Path,
    approved_ids: set[str],
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    payload = read_json(path)
    if payload.get("schema_version") != SYSTEM_CATALOG_SNAPSHOT_SCHEMA_VERSION:
        raise ValueError("Unsupported system catalog snapshot schema")
    rows = payload.get("catalog")
    if not isinstance(rows, list):
        raise ValueError("System catalog snapshot must contain a catalog list")
    facts = {
        str(row["catalog_id"]): row
        for row in rows
        if isinstance(row, dict) and row.get("catalog_id")
    }
    if len(facts) != len(rows):
        raise ValueError("System catalog snapshot contains duplicate or invalid rows")
    if set(facts) != approved_ids:
        raise ValueError(
            "System catalog snapshot must match the approved cohort; "
            f"missing={sorted(approved_ids - set(facts))}, "
            f"unexpected={sorted(set(facts) - approved_ids)}"
        )
    return payload, facts


def _load_backend_components(workbench: Path) -> dict[str, object]:
    backend = workbench.parents[1] / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    from app.domain.catalog.entities import InventorySnapshot
    from app.domain.catalog.entities import StringItem
    from app.domain.catalog.entities import StringOfficialPerformance
    from app.domain.recommendation.entities import RecommendationCandidateModel
    from app.domain.recommendation.entities import RecommendationFeatureSignalModel
    from app.domain.recommendation.entities import RecommendationRequestModel
    from app.domain.recommendation.scoring import ALGORITHM_VERSION
    from app.domain.recommendation.scoring import Fyp1ContentRecommendationScorer

    return {
        "algorithm_version": ALGORITHM_VERSION,
        "candidate_model": RecommendationCandidateModel,
        "request_model": RecommendationRequestModel,
        "scorer": Fyp1ContentRecommendationScorer,
        "signal_model": RecommendationFeatureSignalModel,
        "string_item": StringItem,
        "official_performance": StringOfficialPerformance,
        "inventory": InventorySnapshot,
    }


def _load_catalog_records(workbench: Path) -> dict[str, dict[str, object]]:
    approved = pd.read_csv(
        workbench.parents[1] / "config/approved_string_cohort_v1.csv",
        keep_default_na=False,
    )
    approved_ids = set(approved["catalog_id"])
    source = read_json(
        workbench.parents[1] / "backend/data/string_catalog_db_ready.json"
    )
    records = {
        str(row["catalog_id"]): row
        for row in source["strings"]
        if row["catalog_id"] in approved_ids
    }
    if set(records) != approved_ids:
        raise ValueError(
            f"Catalog metadata is missing approved IDs: {approved_ids - set(records)}"
        )
    return records


def _load_current_matrix(
    workbench: Path,
    approved_ids: set[str],
) -> pd.DataFrame:
    current = pd.read_excel(
        workbench / "output/latest_practical_string_feature_matrix_v9_v8dict.xlsx"
    )
    mappings = load_string_mappings(workbench / "config/string_name_aliases.csv")
    aliases = {
        row.normalized_name: row.canonical_name
        for row in mappings[mappings["review_status"].eq("confirmed")].itertuples()
    }
    cohort = pd.read_csv(
        workbench.parents[1] / "config/approved_string_cohort_v1.csv",
        keep_default_na=False,
    )
    id_by_name = dict(
        zip(cohort["canonical_string_name"], cohort["catalog_id"], strict=True)
    )
    current["canonical_string_name"] = current["string_name"].map(
        lambda value: aliases.get(normalize_string_name(value), "")
    )
    current["catalog_id"] = current["canonical_string_name"].map(id_by_name)
    current = current[current["catalog_id"].isin(approved_ids)].copy()
    if set(current["catalog_id"]) != approved_ids:
        raise ValueError(
            "Current V9 matrix does not contain the approved 12-string cohort"
        )
    return current


def _parse_optional_datetime(value: object) -> datetime | None:
    return datetime.fromisoformat(value) if isinstance(value, str) and value else None


def _build_candidates(
    catalog: dict[str, dict[str, object]],
    current: pd.DataFrame,
    cells: pd.DataFrame,
    *,
    matrix_name: str,
    components: dict[str, object],
    system_facts: dict[str, dict[str, object]] | None = None,
) -> list[object]:
    candidate_model = components["candidate_model"]
    signal_model = components["signal_model"]
    by_name = {
        name: group.set_index("aspect")
        for name, group in cells.groupby("canonical_string_name")
    }
    output = []
    for row in current.itertuples(index=False):
        record = catalog[str(row.catalog_id)]
        fact = (system_facts or {}).get(str(row.catalog_id), {})
        official_data = fact.get("official_performance")
        official = None
        if (
            isinstance(official_data, dict)
            and official_data.get("status") == "manual_reviewed"
            and all(
                official_data.get(key) is not None
                for key in (
                    "repulsion_power",
                    "durability",
                    "hitting_sound",
                    "shock_absorption",
                    "control",
                )
            )
        ):
            official = components["official_performance"](
                catalog_id=str(row.catalog_id),
                source_type=official_data.get("source_type"),
                source_name=official_data.get("source_name"),
                source_url=official_data.get("source_url"),
                source_region=official_data.get("source_region"),
                category=(
                    float(official_data["category"])
                    if official_data.get("category") is not None
                    else None
                ),
                feature=(
                    float(official_data["feature"])
                    if official_data.get("feature") is not None
                    else None
                ),
                feel=(
                    float(official_data["feel"])
                    if official_data.get("feel") is not None
                    else None
                ),
                repulsion_power=float(official_data["repulsion_power"]),
                durability=float(official_data["durability"]),
                hitting_sound=float(official_data["hitting_sound"]),
                shock_absorption=float(official_data["shock_absorption"]),
                control=float(official_data["control"]),
                notes=None,
                status=str(official_data.get("status") or "unknown"),
                updated_at=_parse_optional_datetime(official_data.get("updated_at")),
            )
        inventory_data = fact.get("inventory")
        inventory = None
        if isinstance(inventory_data, dict):
            inventory = components["inventory"](
                inventory_id=str(inventory_data["inventory_id"]),
                current_stock=int(inventory_data.get("current_stock") or 0),
                reserved_stock=int(inventory_data.get("reserved_stock") or 0),
                available_stock=int(inventory_data.get("available_stock") or 0),
                reorder_level=int(inventory_data.get("reorder_level") or 0),
                reorder_quantity=int(inventory_data.get("reorder_quantity") or 0),
                cost_price=None,
                selling_price=(
                    float(inventory_data["selling_price"])
                    if inventory_data.get("selling_price") is not None
                    else None
                ),
                pricing_mode=str(inventory_data.get("pricing_mode") or "price_pending"),
                availability_status=str(
                    inventory_data.get("availability_status") or "out_of_stock"
                ),
                is_active=bool(inventory_data.get("is_active", False)),
                latest_note=None,
                updated_at=_parse_optional_datetime(inventory_data.get("updated_at")),
            )
        values: dict[str, object] = {}
        for aspect in ASPECT_DISPLAY_NAMES:
            score = float(getattr(row, aspect))
            if matrix_name == "macbert_candidate":
                score = float(
                    by_name[str(row.canonical_string_name)].loc[
                        aspect, "normalized_score_0_to_1"
                    ]
                )
            values[aspect] = signal_model(
                normalized_score=score,
            )
        for feature in SUPPORT_FEATURES:
            value = getattr(row, feature, None)
            if pd.notna(value):
                values[feature.removesuffix("_score")] = float(value)
        item = components["string_item"](
            id=str(record["catalog_id"]),
            brand=str(record["brand_name"]),
            brand_code=str(record["brand_code"]),
            display_name=str(record["display_name"]),
            model_name=str(record["model_name"]),
            normalized_name=str(record["display_name"]).lower(),
            series_key=record.get("series_key"),
            series_label=record.get("series_label"),
            is_hybrid=bool(record["is_hybrid"]),
            gauge_main_mm=record.get("gauge_main_mm"),
            gauge_cross_mm=record.get("gauge_cross_mm"),
            gauge_label=record.get("gauge_label"),
            category=None,
            main_trait=None,
            tension_min_lbs=None,
            tension_max_lbs=None,
            material_summary_en=record.get("material_summary_en"),
            image_url=None,
            color_options_en=list(record.get("color_options_en", [])),
            short_description=str(record.get("short_description", "")),
            full_description=str(record.get("full_description", "")),
            official_performance_status=str(
                fact.get("official_performance_status")
                or record["official_performance_status"]
            ),
            source_dataset_url=record.get("source_dataset_url"),
            source_language=record.get("source_language"),
            original_name=record.get("original_name"),
            original_brand_label=record.get("original_brand_label"),
            original_series=record.get("original_series"),
            original_material=record.get("original_material"),
            original_color=record.get("original_color"),
            community_rating=record.get("community_rating"),
            want_count=int(record.get("want_count", 0)),
            used_count=int(record.get("used_count", 0)),
            review_count=int(record["review_count"]),
            tags=[],
            official_performance=official,
            inventory=inventory,
            aspect_scores={},
            is_active=bool(fact.get("is_active", record["is_active"])),
            created_at=None,
            updated_at=None,
        )
        output.append(
            candidate_model(item=item, matrix_by_source={"nlp_review": values})
        )
    return output


def _report(
    *,
    run_id: str,
    source_run_id: str,
    source_threshold: float,
    operational_review: pd.DataFrame,
    threshold_comparison: pd.DataFrame,
    stability: pd.DataFrame,
    profile_summary: pd.DataFrame,
    profile_outcomes: pd.DataFrame,
    profile_coverage: pd.DataFrame,
    followup: pd.DataFrame,
    algorithm_version: str,
) -> str:
    verdicts = (
        operational_review["assistant_operational_verdict"]
        .value_counts()
        .rename_axis("verdict")
        .reset_index(name="rows")
    )
    widest = stability.nlargest(8, "positive_share_wilson_95_width")[
        [
            "canonical_string_name",
            "aspect",
            "accepted_evidence_count",
            "normalized_score_0_to_1",
            "positive_share_wilson_95_lower",
            "positive_share_wilson_95_upper",
        ]
    ]
    return "\n".join(
        [
            "# MacBERT Candidate Operational Review",
            "",
            f"- Review run: `{run_id}`",
            f"- Source inference run: `{source_run_id}`",
            f"- Source candidate threshold retained: `{source_threshold:g}`",
            f"- Backend scorer: `{algorithm_version}`",
            "- Threshold decision: `pending_owner_approval`",
            "- Promotion: `not_promoted`",
            "",
            "## Claim boundary",
            "",
            "The disagreement review is Codex-assisted operational error analysis",
            "pending project-owner confirmation. It is not human Gold, accuracy,",
            "probability calibration, or Cohen's Kappa. The fixed-profile comparison",
            "disables official performance and uses neutral unknown prices so that ranking",
            "changes isolate the nine candidate aspect scores. It is not a live backend",
            "import.",
            "",
            "## Operational disagreement review",
            "",
            "```csv",
            verdicts.to_csv(index=False).strip(),
            "```",
            f"Owner follow-up sample rows: `{len(followup)}`.",
            "",
            "## Validation/test threshold comparison",
            "",
            "```csv",
            threshold_comparison.to_csv(index=False).strip(),
            "```",
            "No threshold was changed by this review run.",
            "",
            "## Candidate cell stability",
            "",
            "Wilson intervals are descriptive only and assume independent directional",
            "mentions. They are not a new minimum-evidence or promotion rule.",
            "",
            "```csv",
            widest.to_csv(index=False).strip(),
            "```",
            "",
            "## Fixed-profile ranking comparison",
            "",
            "```csv",
            profile_summary.to_csv(index=False).strip(),
            "```",
            "",
            "## Virtual-person candidate outcomes",
            "",
            "The near-tie flag is descriptive only and does not rerank candidates.",
            "Budget fit remains neutral because verified prices are not available in",
            "this offline comparison.",
            "",
            "```csv",
            profile_outcomes.to_csv(index=False).strip(),
            "```",
            "",
            "## Approved-cohort recommendation coverage",
            "",
            "Coverage describes whether each approved string appears across the virtual",
            "profiles. It is not a target that forces lower-scoring strings into Top 5.",
            "",
            "```csv",
            profile_coverage.to_csv(index=False).strip(),
            "```",
            "",
            "## Decision",
            "",
            "Keep the candidate run-scoped and `not_promoted`. The project owner must",
            "confirm the operational verdicts and separately approve any threshold,",
            "aggregation, minimum-evidence, backend-import, or promotion change.",
            "",
        ]
    )


def run_candidate_review(
    run_id: str,
    source_run_id: str,
    decisions_path: Path,
    *,
    start: Path | None = None,
) -> dict[str, object]:
    workbench = resolve_workbench(start)
    source_root = run_root(workbench, source_run_id)
    source_manifest_path = source_root / "run_manifest.json"
    source_manifest = read_json(source_manifest_path)
    if source_manifest.get("status") != "completed_candidate_not_promoted":
        raise ValueError("Source inference run is not a completed unpromoted candidate")
    source_stage = source_root / "bert_inference"
    evidence_path = source_stage / "macbert_review_aspect_evidence.csv"
    cells_path = source_stage / "candidate_matrix_cells.csv"
    comparison_path = source_stage / "candidate_vs_current_v9.csv"
    decision_path = source_stage / "pilot_decision.json"
    for path in (
        evidence_path,
        cells_path,
        comparison_path,
        decision_path,
        decisions_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(f"Candidate review input is missing: {path}")

    before = fingerprint_inputs(workbench)
    protected_before = fingerprint_protected_assets(workbench)
    evidence = pd.read_csv(evidence_path, keep_default_na=False)
    cells = pd.read_csv(cells_path, keep_default_na=False)
    comparison = pd.read_csv(comparison_path, keep_default_na=False)
    pilot_decision = read_json(decision_path)
    source_threshold = float(pilot_decision["confidence_threshold"])
    decisions = pd.read_csv(decisions_path, keep_default_na=False)

    operational_review = build_operational_review(evidence, decisions, source_threshold)
    thresholds = build_threshold_comparison(evidence)
    stability = build_cell_stability(cells)
    followup = build_followup_sample(
        evidence,
        cells,
        comparison,
        set(operational_review["source_sample_id"]),
    )
    rankings, movements, profile_summary, algorithm_version = (
        build_fixed_profile_comparison(
            workbench=workbench,
            cells=cells,
        )
    )
    profile_outcomes, profile_coverage = build_profile_audit(rankings)

    stage_dir = create_stage_directory(workbench, run_id, "bert_candidate_review")
    paths = {
        "operational_review": stage_dir / "operational_disagreement_review.csv",
        "followup": stage_dir / "operational_followup_sample.csv",
        "thresholds": stage_dir / "val_test_threshold_comparison.csv",
        "stability": stage_dir / "candidate_cell_stability.csv",
        "profiles": stage_dir / "fixed_profiles.json",
        "rankings": stage_dir / "fixed_profile_rankings.csv",
        "movements": stage_dir / "fixed_profile_rank_movements.csv",
        "profile_summary": stage_dir / "fixed_profile_comparison.csv",
        "profile_outcomes": stage_dir / "virtual_person_outcomes.csv",
        "profile_coverage": stage_dir / "profile_string_coverage.csv",
        "decision": stage_dir / "review_decision.json",
        "report": stage_dir / "report.md",
    }
    operational_review.to_csv(
        paths["operational_review"], index=False, encoding="utf-8-sig"
    )
    followup.to_csv(paths["followup"], index=False, encoding="utf-8-sig")
    thresholds.to_csv(paths["thresholds"], index=False, encoding="utf-8-sig")
    stability.to_csv(paths["stability"], index=False, encoding="utf-8-sig")
    rankings.to_csv(paths["rankings"], index=False, encoding="utf-8-sig")
    movements.to_csv(paths["movements"], index=False, encoding="utf-8-sig")
    profile_summary.to_csv(paths["profile_summary"], index=False, encoding="utf-8-sig")
    profile_outcomes.to_csv(
        paths["profile_outcomes"], index=False, encoding="utf-8-sig"
    )
    profile_coverage.to_csv(
        paths["profile_coverage"], index=False, encoding="utf-8-sig"
    )
    write_json_exclusive(
        paths["profiles"],
        {
            "comparison_boundary": (
                "matrix_only_v9_confidence_support_held_constant_"
                "no_official_performance_neutral_unknown_price"
            ),
            "profiles": list(FIXED_PROFILES),
            "descriptive_near_tie_epsilon": DESCRIPTIVE_NEAR_TIE_EPSILON,
        },
    )
    review_decision = {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "source_candidate_threshold": source_threshold,
        "thresholds_compared": list(REVIEW_THRESHOLDS),
        "threshold_change_status": "pending_owner_approval",
        "operational_review_status": "codex_assisted_pending_owner_approval",
        "claim_boundary": "operational_review_only_not_human_gold_no_kappa",
        "promotion": {"status": "not_promoted"},
        "descriptive_near_tie_epsilon": DESCRIPTIVE_NEAR_TIE_EPSILON,
    }
    write_json_exclusive(paths["decision"], review_decision)
    paths["report"].write_text(
        _report(
            run_id=run_id,
            source_run_id=source_run_id,
            source_threshold=source_threshold,
            operational_review=operational_review,
            threshold_comparison=thresholds,
            stability=stability,
            profile_summary=profile_summary,
            profile_outcomes=profile_outcomes,
            profile_coverage=profile_coverage,
            followup=followup,
            algorithm_version=algorithm_version,
        ),
        encoding="utf-8",
    )

    after = fingerprint_inputs(workbench)
    protected_after = fingerprint_protected_assets(workbench)
    assert_inputs_unchanged(before, after)
    assert_inputs_unchanged(protected_before, protected_after)
    artifacts = artifact_records(paths.values(), run_root(workbench, run_id))
    manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "bert_candidate_review",
        "status": "completed_operational_review_not_promoted",
        "created_at": utc_now(),
        "source_inference_run": {
            "run_id": source_run_id,
            "manifest_path": source_manifest_path.relative_to(workbench).as_posix(),
            "manifest_sha256": sha256_file(source_manifest_path),
            "evidence_sha256": sha256_file(evidence_path),
            "cells_sha256": sha256_file(cells_path),
            "comparison_sha256": sha256_file(comparison_path),
        },
        "operational_decisions": {
            "path": decisions_path.relative_to(workbench).as_posix(),
            "sha256": sha256_file(decisions_path),
            "reviewer_type": "codex_assisted_pending_project_owner_confirmation",
        },
        "backend_scorer": {
            "algorithm_version": algorithm_version,
            "path": "../backend/app/domain/recommendation/scoring.py",
            "sha256": sha256_file(
                workbench.parents[1] / "backend/app/domain/recommendation/scoring.py"
            ),
            "execution_boundary": (
                "pure_domain_scorer_no_database_no_backend_import_"
                "neutral_unknown_price_no_official_performance"
            ),
        },
        "summary": {
            "operational_disagreements_reviewed": int(len(operational_review)),
            "owner_followup_sample_rows": int(len(followup)),
            "candidate_cells_with_intervals": int(len(stability)),
            "fixed_profiles": len(FIXED_PROFILES),
            "top1_changes": int(profile_summary["top1_changed"].sum()),
            "candidate_strings_in_coverage": int(len(profile_coverage)),
            "candidate_strings_appearing_top5": int(
                profile_coverage["appears_in_top5"].sum()
            ),
            "candidate_near_tie_profiles": int(
                profile_outcomes["descriptive_near_tie"].sum()
            ),
        },
        "inputs": before,
        "protected_assets": protected_before,
        "artifacts": artifacts,
        "runtime_versions": runtime_versions(("pandas", "numpy", "openpyxl")),
        "decision": review_decision,
        "promotion": {
            "status": "not_promoted",
            "requires_separate_human_approval": True,
            "canonical_backend_artifact_modified": False,
            "backend_imported": False,
        },
        "gold_dataset_status": "not_available",
        "evaluation_status": "operational_review_only_not_human_gold",
    }
    manifest_path = stage_dir / "manifest.json"
    write_json_exclusive(manifest_path, manifest)
    write_json_exclusive(
        run_root(workbench, run_id) / "run_manifest.json",
        {**manifest, "stage_manifest": "bert_candidate_review/manifest.json"},
    )
    return {
        "run_id": run_id,
        "run_root": str(run_root(workbench, run_id)),
        "summary": manifest["summary"],
        "promotion": manifest["promotion"],
        "threshold_change_status": "pending_owner_approval",
    }


def _recommendation_optimization_report(
    *,
    run_id: str,
    source_run_id: str,
    source_threshold: float,
    preference_weight_exponent: float,
    summary: dict[str, object],
    profile_summary: pd.DataFrame,
    optimized_outcomes: pd.DataFrame,
    optimized_coverage: pd.DataFrame,
    stability: pd.DataFrame,
) -> str:
    widest = stability.nlargest(10, "positive_share_wilson_95_width")[
        [
            "canonical_string_name",
            "aspect",
            "accepted_evidence_count",
            "normalized_score_0_to_1",
            "positive_share_wilson_95_width",
        ]
    ]
    return "\n".join(
        [
            "# MacBERT Recommendation Optimization Shadow Review",
            "",
            f"- Optimization run: `{run_id}`",
            f"- Source inference run: `{source_run_id}`",
            f"- Source threshold retained: `{source_threshold:g}`",
            f"- Candidate preference exponent: `{preference_weight_exponent:g}`",
            "- Selection: `comparison_only_not_selected`",
            "- Promotion: `not_promoted`",
            "",
            "## Claim boundary",
            "",
            "This run audits the active v6 preference policy against a read-only",
            "snapshot of reviewed catalog facts and official performance; catalog",
            "price is descriptive and is not scored. The exponent comparison does not",
            "change the backend Matrix, protected V9 workbook, or promotion status.",
            "The results are virtual-person shadow evaluation, not human Gold or Kappa.",
            "",
            "## Summary",
            "",
            "```csv",
            pd.DataFrame([summary]).to_csv(index=False).strip(),
            "```",
            "",
            "## Preference-weight ranking changes",
            "",
            "```csv",
            profile_summary.to_csv(index=False).strip(),
            "```",
            "",
            "## Squared-weight virtual-person outcomes",
            "",
            "Near-tie flags are descriptive only and do not rerank candidates.",
            "",
            "```csv",
            optimized_outcomes.to_csv(index=False).strip(),
            "```",
            "",
            "## Squared-weight active-catalog coverage",
            "",
            "```csv",
            optimized_coverage.to_csv(index=False).strip(),
            "```",
            "",
            "## Evidence review priority",
            "",
            "These are the widest descriptive Wilson intervals; they do not create a",
            "new evidence threshold or promotion rule.",
            "",
            "```csv",
            widest.to_csv(index=False).strip(),
            "```",
            "",
            "## Decision boundary",
            "",
            "Keep both variants run-scoped and unselected. Choosing a new preference",
            "exponent or importing any Matrix requires separate project-owner approval.",
            "",
        ]
    )


def run_recommendation_optimization(
    run_id: str,
    source_run_id: str,
    catalog_snapshot_path: Path,
    *,
    start: Path | None = None,
) -> dict[str, object]:
    preference_weight_exponent = OPTIMIZED_PREFERENCE_WEIGHT_EXPONENT
    workbench = resolve_workbench(start)
    source_root = run_root(workbench, source_run_id)
    source_manifest_path = source_root / "run_manifest.json"
    source_manifest = read_json(source_manifest_path)
    if source_manifest.get("status") != "completed_candidate_not_promoted":
        raise ValueError("Source inference run is not a completed unpromoted candidate")
    source_stage = source_root / "bert_inference"
    cells_path = source_stage / "candidate_matrix_cells.csv"
    decision_path = source_stage / "pilot_decision.json"
    for path in (cells_path, decision_path, catalog_snapshot_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"Recommendation optimization input is missing: {path}"
            )

    before = fingerprint_inputs(workbench)
    protected_before = fingerprint_protected_assets(workbench)
    cells = pd.read_csv(cells_path, keep_default_na=False)
    source_threshold = float(read_json(decision_path)["confidence_threshold"])
    catalog_records = _load_catalog_records(workbench)
    snapshot, system_facts = load_system_catalog_snapshot(
        catalog_snapshot_path,
        set(catalog_records),
    )

    baseline_rankings, _, _, algorithm_version = build_fixed_profile_comparison(
        workbench=workbench,
        cells=cells,
        system_facts=system_facts,
        preference_weight_exponent=1.0,
        active_only=True,
    )
    optimized_rankings, _, _, _ = build_fixed_profile_comparison(
        workbench=workbench,
        cells=cells,
        system_facts=system_facts,
        preference_weight_exponent=preference_weight_exponent,
        active_only=True,
    )
    baseline_rankings = baseline_rankings.copy()
    baseline_rankings["matrix"] = baseline_rankings["matrix"].replace(
        {
            "current_v9": "current_v9_system_facts_power_1",
            "macbert_candidate": "macbert_system_facts_power_1",
        }
    )
    optimized_rankings = optimized_rankings[
        optimized_rankings["matrix"].eq("macbert_candidate")
    ].copy()
    optimized_rankings["matrix"] = "macbert_system_facts_power_2"
    rankings = pd.concat([baseline_rankings, optimized_rankings], ignore_index=True)

    movements, profile_summary = summarize_profile_movements(
        rankings,
        baseline_matrix="macbert_system_facts_power_1",
        candidate_matrix="macbert_system_facts_power_2",
        baseline_label="power_1",
        candidate_label="power_2",
        score_delta_column="score_delta_power_2_minus_power_1",
    )
    movements["score_delta_power_2_minus_power_1"] = movements[
        "score_delta_power_2_minus_power_1"
    ].round(4)
    profile_summary["mean_absolute_score_delta"] = profile_summary[
        "mean_absolute_score_delta"
    ].round(4)
    baseline_outcomes, baseline_coverage = build_profile_audit(
        rankings,
        matrix_name="macbert_system_facts_power_1",
    )
    optimized_outcomes, optimized_coverage = build_profile_audit(
        rankings,
        matrix_name="macbert_system_facts_power_2",
    )
    stability = build_cell_stability(cells).sort_values(
        ["positive_share_wilson_95_width", "accepted_evidence_count"],
        ascending=[False, True],
    )

    official_count = sum(
        isinstance(fact.get("official_performance"), dict)
        and fact["official_performance"].get("status") == "manual_reviewed"
        and all(
            fact["official_performance"].get(key) is not None
            for key in (
                "repulsion_power",
                "durability",
                "hitting_sound",
                "shock_absorption",
                "control",
            )
        )
        for fact in system_facts.values()
    )
    price_count = sum(
        isinstance(fact.get("inventory"), dict)
        and fact["inventory"].get("selling_price") is not None
        for fact in system_facts.values()
    )
    feel_values = [
        float(fact["official_performance"]["feel"])
        for fact in system_facts.values()
        if isinstance(fact.get("official_performance"), dict)
        and fact["official_performance"].get("feel") is not None
    ]
    feel_counts = {
        "soft": sum(value <= 4 for value in feel_values),
        "medium": sum(4 < value <= 6.5 for value in feel_values),
        "hard": sum(value > 6.5 for value in feel_values),
    }
    active_count = sum(bool(fact.get("is_active")) for fact in system_facts.values())
    inactive_ids = sorted(
        catalog_id
        for catalog_id, fact in system_facts.items()
        if not fact.get("is_active")
    )

    def top1_concentration(outcomes: pd.DataFrame) -> float:
        return round(
            float(outcomes["top1_catalog_id"].value_counts(normalize=True).max()),
            4,
        )

    summary = {
        "virtual_profiles": len(FIXED_PROFILES),
        "approved_strings": len(system_facts),
        "active_strings": active_count,
        "inactive_catalog_ids": "|".join(inactive_ids),
        "official_performance_complete": official_count,
        "official_feel_complete": len(feel_values),
        "official_feel_distribution": "|".join(
            f"{key}:{value}" for key, value in feel_counts.items()
        ),
        "selling_price_available": price_count,
        "top1_changes_power_2_vs_power_1": int(profile_summary["top1_changed"].sum()),
        "unique_top1_power_1": int(baseline_outcomes["top1_catalog_id"].nunique()),
        "unique_top1_power_2": int(optimized_outcomes["top1_catalog_id"].nunique()),
        "max_top1_concentration_power_1": top1_concentration(baseline_outcomes),
        "max_top1_concentration_power_2": top1_concentration(optimized_outcomes),
        "near_tie_profiles_power_1": int(
            baseline_outcomes["descriptive_near_tie"].sum()
        ),
        "near_tie_profiles_power_2": int(
            optimized_outcomes["descriptive_near_tie"].sum()
        ),
        "strings_appearing_top5_power_1": int(
            baseline_coverage["appears_in_top5"].sum()
        ),
        "strings_appearing_top5_power_2": int(
            optimized_coverage["appears_in_top5"].sum()
        ),
    }
    decision = {
        "schema_version": RECOMMENDATION_OPTIMIZATION_SCHEMA_VERSION,
        "selection_status": "comparison_only_not_selected",
        "preference_weight_exponents_compared": [1.0, preference_weight_exponent],
        "descriptive_near_tie_epsilon": DESCRIPTIVE_NEAR_TIE_EPSILON,
        "claim_boundary": "virtual_person_shadow_only_not_human_gold_no_kappa",
        "candidate_boundary": "system_catalog_is_active_true",
        "preference_policy": {
            "game_type": "removed",
            "budget": "removed",
            "value_for_money": "ninth_weighted_preference_feature",
            "gauge": (
                "soft_rule_thin_for_beginner_except_thick_for_tension_le_23_"
                "or_tension_ge_27_or_frequency_ge_3"
            ),
            "preferred_gauge": "soft_bonus_or_penalty_no_candidate_filter",
            "preferred_feel": "soft_medium_hard_official_category_rule",
            "recent_goal": "structured_option_rule",
        },
        "acceptance_gates": {
            "official_performance_coverage": f"{official_count}/{len(system_facts)}",
            "official_feel_coverage": f"{len(feel_values)}/{len(system_facts)}",
            "selling_price_coverage": f"{price_count}/{len(system_facts)}",
            "active_catalog_coverage": f"{active_count}/{len(system_facts)}",
            "human_gold": "not_available",
            "backend_import": "requires_separate_approval",
            "promotion": "requires_separate_approval",
        },
        "promotion": {"status": "not_promoted"},
    }

    stage_dir = create_stage_directory(
        workbench,
        run_id,
        "bert_recommendation_optimization",
    )
    paths = {
        "snapshot": stage_dir / "system_catalog_snapshot.json",
        "profiles": stage_dir / "fixed_profiles.json",
        "rankings": stage_dir / "preference_weight_rankings.csv",
        "movements": stage_dir / "preference_weight_rank_movements.csv",
        "profile_summary": stage_dir / "preference_weight_comparison.csv",
        "baseline_outcomes": stage_dir / "power_1_virtual_person_outcomes.csv",
        "optimized_outcomes": stage_dir / "power_2_virtual_person_outcomes.csv",
        "baseline_coverage": stage_dir / "power_1_profile_string_coverage.csv",
        "optimized_coverage": stage_dir / "power_2_profile_string_coverage.csv",
        "stability": stage_dir / "candidate_cell_stability.csv",
        "decision": stage_dir / "optimization_decision.json",
        "report": stage_dir / "report.md",
    }
    write_json_exclusive(paths["snapshot"], snapshot)
    write_json_exclusive(
        paths["profiles"],
        {
            "profiles": list(FIXED_PROFILES),
            "descriptive_near_tie_epsilon": DESCRIPTIVE_NEAR_TIE_EPSILON,
        },
    )
    rankings.to_csv(paths["rankings"], index=False, encoding="utf-8-sig")
    movements.to_csv(paths["movements"], index=False, encoding="utf-8-sig")
    profile_summary.to_csv(paths["profile_summary"], index=False, encoding="utf-8-sig")
    baseline_outcomes.to_csv(
        paths["baseline_outcomes"], index=False, encoding="utf-8-sig"
    )
    optimized_outcomes.to_csv(
        paths["optimized_outcomes"], index=False, encoding="utf-8-sig"
    )
    baseline_coverage.to_csv(
        paths["baseline_coverage"], index=False, encoding="utf-8-sig"
    )
    optimized_coverage.to_csv(
        paths["optimized_coverage"], index=False, encoding="utf-8-sig"
    )
    stability.to_csv(paths["stability"], index=False, encoding="utf-8-sig")
    write_json_exclusive(paths["decision"], decision)
    paths["report"].write_text(
        _recommendation_optimization_report(
            run_id=run_id,
            source_run_id=source_run_id,
            source_threshold=source_threshold,
            preference_weight_exponent=preference_weight_exponent,
            summary=summary,
            profile_summary=profile_summary,
            optimized_outcomes=optimized_outcomes,
            optimized_coverage=optimized_coverage,
            stability=stability,
        ),
        encoding="utf-8",
    )

    after = fingerprint_inputs(workbench)
    protected_after = fingerprint_protected_assets(workbench)
    assert_inputs_unchanged(before, after)
    assert_inputs_unchanged(protected_before, protected_after)
    artifacts = artifact_records(paths.values(), run_root(workbench, run_id))
    manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "optimization_schema_version": RECOMMENDATION_OPTIMIZATION_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "bert_recommendation_optimization",
        "status": "completed_shadow_optimization_not_promoted",
        "created_at": utc_now(),
        "source_inference_run": {
            "run_id": source_run_id,
            "manifest_path": source_manifest_path.relative_to(workbench).as_posix(),
            "manifest_sha256": sha256_file(source_manifest_path),
            "cells_sha256": sha256_file(cells_path),
            "confidence_threshold": source_threshold,
        },
        "system_catalog_snapshot_input": {
            "path": str(catalog_snapshot_path),
            "sha256": sha256_file(catalog_snapshot_path),
            "transaction_mode": "read_only",
            "official_performance_complete": official_count,
            "official_feel_complete": len(feel_values),
            "official_feel_distribution": feel_counts,
            "selling_price_available": price_count,
            "active_strings": active_count,
            "inactive_catalog_ids": inactive_ids,
        },
        "backend_scorer": {
            "algorithm_version": algorithm_version,
            "preference_weight_exponents_compared": [
                1.0,
                preference_weight_exponent,
            ],
            "live_default_unchanged": True,
            "path": "../backend/app/domain/recommendation/scoring.py",
            "sha256": sha256_file(
                workbench.parents[1] / "backend/app/domain/recommendation/scoring.py"
            ),
        },
        "summary": summary,
        "decision": decision,
        "inputs": before,
        "protected_assets": protected_before,
        "artifacts": artifacts,
        "runtime_versions": runtime_versions(("pandas", "numpy", "openpyxl")),
        "promotion": {
            "status": "not_promoted",
            "requires_separate_human_approval": True,
            "canonical_backend_artifact_modified": False,
            "backend_imported": False,
        },
        "gold_dataset_status": "not_available",
        "evaluation_status": "virtual_person_shadow_only_not_human_gold",
    }
    manifest_path = stage_dir / "manifest.json"
    write_json_exclusive(manifest_path, manifest)
    write_json_exclusive(
        run_root(workbench, run_id) / "run_manifest.json",
        {
            **manifest,
            "stage_manifest": "bert_recommendation_optimization/manifest.json",
        },
    )
    return {
        "run_id": run_id,
        "run_root": str(run_root(workbench, run_id)),
        "summary": summary,
        "selection_status": "comparison_only_not_selected",
        "promotion": manifest["promotion"],
    }


def _sensitivity_report(
    *,
    run_id: str,
    source_run_id: str,
    threshold: float,
    source_threshold: float,
    threshold_metrics: pd.DataFrame,
    evidence_delta: pd.DataFrame,
    cell_comparison: pd.DataFrame,
    profile_v9_summary: pd.DataFrame,
    profile_threshold_summary: pd.DataFrame,
) -> str:
    threshold_label = f"{threshold:g}"
    source_threshold_label = f"{source_threshold:g}"
    status_changes = (
        evidence_delta.groupby(
            ["source_aggregation_status", "sensitivity_aggregation_status"]
        )
        .size()
        .rename("rows")
        .reset_index()
    )
    largest_cell_changes = cell_comparison.assign(
        absolute_score_delta=cell_comparison["normalized_score_delta"].abs()
    ).nlargest(10, "absolute_score_delta")[
        [
            "canonical_string_name",
            "aspect",
            "accepted_evidence_added",
            "normalized_score_0_to_1_confirmed",
            "normalized_score_0_to_1_sensitivity",
            "normalized_score_delta",
        ]
    ]
    return "\n".join(
        [
            "# MacBERT Threshold Sensitivity Pilot",
            "",
            f"- Sensitivity run: `{run_id}`",
            f"- Source inference run: `{source_run_id}`",
            f"- Sensitivity threshold: `{threshold_label}`",
            f"- Confirmed pilot threshold retained: `{source_threshold_label}`",
            "- Sensitivity status: `comparison_only_not_selected`",
            "- Promotion: `not_promoted`",
            "",
            "## Claim boundary",
            "",
            "This run reuses the frozen class probabilities and changes only the",
            "aggregation threshold. It does not rerun or retrain MacBERT, overwrite the",
            "confirmed pilot, import the backend Matrix, or modify protected V9. Silver",
            "disagreement is not human error, Gold accuracy, calibration, or Kappa.",
            "",
            "## Validation/test threshold metrics",
            "",
            "```csv",
            threshold_metrics.to_csv(index=False).strip(),
            "```",
            "",
            "## Full-corpus evidence status changes",
            "",
            "```csv",
            status_changes.to_csv(index=False).strip(),
            "```",
            "",
            f"## Largest {threshold_label} versus confirmed "
            f"{source_threshold_label} cell changes",
            "",
            "```csv",
            largest_cell_changes.to_csv(index=False).strip(),
            "```",
            "",
            f"## Fixed profiles: {threshold_label} versus current V9",
            "",
            "```csv",
            profile_v9_summary.to_csv(index=False).strip(),
            "```",
            "",
            f"## Fixed profiles: {threshold_label} versus confirmed "
            f"{source_threshold_label}",
            "",
            "```csv",
            profile_threshold_summary.to_csv(index=False).strip(),
            "```",
            "",
            "## Decision boundary",
            "",
            f"The `{threshold_label}` result remains a sensitivity candidate. Replacing",
            f"the confirmed `{source_threshold_label}` pilot requires a separate",
            "project-owner decision after reviewing",
            "these evidence, cell, and fixed-profile differences.",
            "",
        ]
    )


def run_threshold_sensitivity(
    run_id: str,
    source_run_id: str,
    owner_confirmation_run_id: str,
    confidence_threshold: float,
    *,
    start: Path | None = None,
) -> dict[str, object]:
    workbench = resolve_workbench(start)
    source_root = run_root(workbench, source_run_id)
    source_manifest_path = source_root / "run_manifest.json"
    source_manifest = read_json(source_manifest_path)
    if source_manifest.get("status") != "completed_candidate_not_promoted":
        raise ValueError("Source inference run is not a completed unpromoted candidate")

    confirmation_manifest_path = (
        run_root(workbench, owner_confirmation_run_id) / "run_manifest.json"
    )
    confirmation_manifest = read_json(confirmation_manifest_path)
    if confirmation_manifest.get("status") != (
        "completed_owner_confirmation_not_promoted"
    ):
        raise ValueError("Owner confirmation run is not completed and unpromoted")
    review_manifest_path = workbench / str(
        confirmation_manifest["source_review_run"]["manifest_path"]
    )
    review_manifest = read_json(review_manifest_path)
    if review_manifest["source_inference_run"]["run_id"] != source_run_id:
        raise ValueError(
            "Owner confirmation does not belong to the source inference run"
        )

    source_stage = source_root / "bert_inference"
    evidence_path = source_stage / "macbert_review_aspect_evidence.csv"
    source_cells_path = source_stage / "candidate_matrix_cells.csv"
    source_decision_path = source_stage / "pilot_decision.json"
    for path in (evidence_path, source_cells_path, source_decision_path):
        if not path.is_file():
            raise FileNotFoundError(f"Threshold sensitivity input is missing: {path}")
    source_decision = read_json(source_decision_path)
    source_threshold = float(source_decision["confidence_threshold"])
    minimum_evidence = int(source_decision["minimum_evidence"])
    confirmed_threshold = float(confirmation_manifest["decision"]["pilot_threshold"])
    if confirmed_threshold != source_threshold:
        raise ValueError(
            "Owner confirmation threshold does not match the source inference run"
        )
    if not 0 < confidence_threshold < source_threshold:
        raise ValueError(
            "Sensitivity threshold must be greater than zero and lower than the "
            f"confirmed source threshold {source_threshold:g}"
        )

    before = fingerprint_inputs(workbench)
    protected_before = fingerprint_protected_assets(workbench)
    evidence = pd.read_csv(evidence_path, keep_default_na=False)
    source_cells = pd.read_csv(source_cells_path, keep_default_na=False)
    sensitivity_evidence, evidence_delta = build_evidence_status_delta(
        evidence, confidence_threshold
    )
    raw_cells = aggregate_candidate_cells(sensitivity_evidence)
    catalog = load_inference_catalog(
        workbench.parents[1] / "config/approved_string_cohort_v1.csv"
    )
    cells, matrix = build_candidate_matrix(raw_cells, catalog, minimum_evidence)
    comparison_v9 = build_current_comparison(
        cells,
        workbench / "output/latest_practical_string_feature_matrix_v9_v8dict.xlsx",
        workbench / "config/string_name_aliases.csv",
    )
    comparison_confirmed = compare_candidate_cells(cells, source_cells)
    threshold_metrics = build_threshold_comparison(
        evidence,
        candidates=tuple(
            sorted({confidence_threshold, *REVIEW_THRESHOLDS, source_threshold})
        ),
    )
    stability = build_cell_stability(cells)

    sensitivity_rankings, sensitivity_movements, sensitivity_v9_summary, algorithm = (
        build_fixed_profile_comparison(
            workbench=workbench,
            cells=cells,
        )
    )
    confirmed_rankings, _, _, _ = build_fixed_profile_comparison(
        workbench=workbench,
        cells=source_cells,
    )
    confirmed_label = f"confirmed_{source_threshold:g}".replace(".", "_")
    sensitivity_label = f"sensitivity_{confidence_threshold:g}".replace(".", "_")
    threshold_rankings = pd.concat(
        [
            confirmed_rankings[
                confirmed_rankings["matrix"].eq("macbert_candidate")
            ].assign(matrix=confirmed_label),
            sensitivity_rankings[
                sensitivity_rankings["matrix"].eq("macbert_candidate")
            ].assign(matrix=sensitivity_label),
        ],
        ignore_index=True,
    )
    threshold_movements, threshold_profile_summary = summarize_profile_movements(
        threshold_rankings,
        baseline_matrix=confirmed_label,
        candidate_matrix=sensitivity_label,
        baseline_label=confirmed_label,
        candidate_label=sensitivity_label,
        score_delta_column=(f"score_delta_{sensitivity_label}_minus_{confirmed_label}"),
    )

    stage_dir = create_stage_directory(workbench, run_id, "bert_threshold_sensitivity")
    paths = {
        "evidence_delta": stage_dir / "evidence_status_delta.csv",
        "cells": stage_dir / "candidate_matrix_cells.csv",
        "matrix_csv": stage_dir / "candidate_matrix_12x9.csv",
        "matrix_xlsx": stage_dir / "candidate_matrix_12x9.xlsx",
        "comparison_v9": stage_dir / "candidate_vs_current_v9.csv",
        "comparison_confirmed": stage_dir / "candidate_vs_confirmed_0_995.csv",
        "threshold_metrics": stage_dir / "val_test_threshold_comparison.csv",
        "stability": stage_dir / "candidate_cell_stability.csv",
        "profile_rankings": stage_dir / "fixed_profile_rankings.csv",
        "profile_movements": stage_dir / "fixed_profile_v9_rank_movements.csv",
        "profile_v9_summary": stage_dir / "fixed_profile_v9_comparison.csv",
        "threshold_movements": stage_dir / "fixed_profile_threshold_rank_movements.csv",
        "threshold_profile_summary": stage_dir
        / "fixed_profile_threshold_comparison.csv",
        "decision": stage_dir / "sensitivity_decision.json",
        "report": stage_dir / "report.md",
    }
    for key, frame in (
        ("evidence_delta", evidence_delta),
        ("cells", cells),
        ("matrix_csv", matrix),
        ("comparison_v9", comparison_v9),
        ("comparison_confirmed", comparison_confirmed),
        ("threshold_metrics", threshold_metrics),
        ("stability", stability),
        ("profile_rankings", sensitivity_rankings),
        ("profile_movements", sensitivity_movements),
        ("profile_v9_summary", sensitivity_v9_summary),
        ("threshold_movements", threshold_movements),
        ("threshold_profile_summary", threshold_profile_summary),
    ):
        frame.to_csv(paths[key], index=False, encoding="utf-8-sig")
    matrix.to_excel(paths["matrix_xlsx"], index=False)
    sensitivity_decision = {
        "schema_version": SENSITIVITY_SCHEMA_VERSION,
        "sensitivity_threshold": confidence_threshold,
        "confirmed_pilot_threshold": source_threshold,
        "minimum_evidence_retained": minimum_evidence,
        "selection_status": "comparison_only_not_selected",
        "claim_boundary": "silver_sensitivity_only_not_human_gold_no_kappa",
        "promotion": {"status": "not_promoted"},
    }
    write_json_exclusive(paths["decision"], sensitivity_decision)
    paths["report"].write_text(
        _sensitivity_report(
            run_id=run_id,
            source_run_id=source_run_id,
            threshold=confidence_threshold,
            source_threshold=source_threshold,
            threshold_metrics=threshold_metrics,
            evidence_delta=evidence_delta,
            cell_comparison=comparison_confirmed,
            profile_v9_summary=sensitivity_v9_summary,
            profile_threshold_summary=threshold_profile_summary,
        ),
        encoding="utf-8",
    )

    after = fingerprint_inputs(workbench)
    protected_after = fingerprint_protected_assets(workbench)
    assert_inputs_unchanged(before, after)
    assert_inputs_unchanged(protected_before, protected_after)
    artifacts = artifact_records(paths.values(), run_root(workbench, run_id))
    newly_accepted = int(
        evidence_delta["sensitivity_aggregation_status"]
        .eq("accepted_directional")
        .sum()
    )
    manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "sensitivity_schema_version": SENSITIVITY_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "bert_threshold_sensitivity",
        "status": "completed_threshold_sensitivity_not_promoted",
        "created_at": utc_now(),
        "source_inference_run": {
            "run_id": source_run_id,
            "manifest_path": source_manifest_path.relative_to(workbench).as_posix(),
            "manifest_sha256": sha256_file(source_manifest_path),
            "evidence_sha256": sha256_file(evidence_path),
            "cells_sha256": sha256_file(source_cells_path),
        },
        "owner_confirmation_run": {
            "run_id": owner_confirmation_run_id,
            "manifest_path": confirmation_manifest_path.relative_to(
                workbench
            ).as_posix(),
            "manifest_sha256": sha256_file(confirmation_manifest_path),
            "confirmed_threshold": confirmed_threshold,
        },
        "backend_scorer": {
            "algorithm_version": algorithm,
            "path": "../backend/app/domain/recommendation/scoring.py",
            "sha256": sha256_file(
                workbench.parents[1] / "backend/app/domain/recommendation/scoring.py"
            ),
            "execution_boundary": (
                "pure_domain_scorer_no_database_no_backend_import_"
                "neutral_unknown_price_no_official_performance"
            ),
        },
        "configuration": sensitivity_decision,
        "summary": {
            "prediction_rows_reused": int(len(evidence)),
            "evidence_status_changes": int(len(evidence_delta)),
            "newly_accepted_directional_rows": newly_accepted,
            "candidate_cells": int(
                cells["matrix_status"].eq("candidate_available").sum()
            ),
            "maximum_absolute_normalized_cell_delta_vs_confirmed": float(
                comparison_confirmed["normalized_score_delta"].abs().max()
            ),
            "mean_absolute_normalized_cell_delta_vs_confirmed": float(
                comparison_confirmed["normalized_score_delta"].abs().mean()
            ),
            "fixed_profile_top1_changes_vs_confirmed": int(
                threshold_profile_summary["top1_changed"].sum()
            ),
        },
        "inputs": before,
        "protected_assets": protected_before,
        "artifacts": artifacts,
        "runtime_versions": runtime_versions(("pandas", "numpy", "openpyxl")),
        "promotion": {
            "status": "not_promoted",
            "requires_separate_human_approval": True,
            "canonical_backend_artifact_modified": False,
            "backend_imported": False,
        },
        "gold_dataset_status": "not_available",
        "evaluation_status": "threshold_sensitivity_only_not_human_gold",
    }
    manifest_path = stage_dir / "manifest.json"
    write_json_exclusive(manifest_path, manifest)
    write_json_exclusive(
        run_root(workbench, run_id) / "run_manifest.json",
        {**manifest, "stage_manifest": "bert_threshold_sensitivity/manifest.json"},
    )
    return {
        "run_id": run_id,
        "run_root": str(run_root(workbench, run_id)),
        "summary": manifest["summary"],
        "selection_status": "comparison_only_not_selected",
        "promotion": manifest["promotion"],
    }
