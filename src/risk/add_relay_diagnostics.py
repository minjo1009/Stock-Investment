from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


GATE_ORDER = (
    "participation_quality",
    "state_gate",
    "factor_budget",
    "exposure_gate",
    "staged_gate",
    "healthy_policy",
)

HEALTHY_CONFIDENCE_MIN = 0.50
LIFECYCLE_COLUMNS = ("lifecycle_group", "trade_count", "outcome_count", "blocked_trade_count")
REQUIRED_REPORT_FILES = (
    "task_363_add_relay_trace.csv",
    "task_363_add_relay_dropoff_summary.csv",
    "task_363_add_relay_blocking_reasons.csv",
    "task_363_add_relay_lifecycle_summary.csv",
    "task_363_add_relay_report.md",
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    if pd.isna(numeric):
        return float(default)
    return numeric


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _safe_text(value: Any, default: str = "") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    text = str(value).strip()
    return text if text else default


def _split_reason_text(value: Any) -> tuple[str, ...]:
    text = _safe_text(value)
    if not text:
        return ()
    if text.startswith(("(", "[", "{")) and text.endswith((")", "]", "}")):
        try:
            parsed = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            parsed = None
        if isinstance(parsed, (list, tuple, set)):
            return tuple(str(part).strip() for part in parsed if str(part).strip())
    if "," in text and "|" not in text:
        return tuple(part.strip() for part in text.split(",") if part.strip())
    return tuple(part for part in text.split("|") if part)


def _gate_decisions(row: pd.Series) -> list[tuple[str, bool, str | None]]:
    quality_label = _safe_text(row.get("participation_quality_label"), "UNKNOWN")
    confidence = _safe_float(row.get("participation_confidence"), 0.0)
    state_label = _safe_text(row.get("state_label"), "UNKNOWN")
    staged_gate_stage = _safe_text(row.get("staged_gate_stage"), "UNKNOWN")
    healthy_policy_label = _safe_text(row.get("healthy_aggressive_policy_label"), "UNKNOWN")

    quality_pass = quality_label == "HEALTHY_EXPANSION" and confidence >= HEALTHY_CONFIDENCE_MIN
    quality_reason = None
    if not quality_pass:
        if quality_label != "HEALTHY_EXPANSION":
            quality_reason = f"quality_label={quality_label}"
        else:
            quality_reason = "participation_confidence_below_threshold"

    state_pass = state_label != "DISLOCATION"
    state_reason = None if state_pass else "state_label=DISLOCATION"

    factor_pass = not _safe_bool(row.get("factor_exposure_violated"))
    violated_factors = _split_reason_text(row.get("violated_factors"))
    factor_reason = None if factor_pass else (
        f"factor_budget_violation={violated_factors[0]}" if violated_factors else "factor_budget_violation"
    )

    exposure_pass = _safe_bool(row.get("allow_add"))
    exposure_reason = None if exposure_pass else "exposure_allow_add_false"

    staged_pass = _safe_bool(row.get("staged_add_allowed"))
    staged_reason = None if staged_pass else f"staged_gate_stage={staged_gate_stage}"

    healthy_pass = _safe_bool(row.get("healthy_aggressive_final_add_allowed"))
    healthy_reason = None if healthy_pass else f"healthy_policy_label={healthy_policy_label}"

    return [
        ("participation_quality", quality_pass, quality_reason),
        ("state_gate", state_pass, state_reason),
        ("factor_budget", factor_pass, factor_reason),
        ("exposure_gate", exposure_pass, exposure_reason),
        ("staged_gate", staged_pass, staged_reason),
        ("healthy_policy", healthy_pass, healthy_reason),
    ]


def _legacy_outcome_fields(row: pd.Series, first_blocking_reason: str) -> tuple[str, str]:
    if not _safe_bool(row.get("allow_new_entry", True)):
        return "entry_blocked", "exposure_gate"
    if _safe_bool(row.get("factor_exposure_violated")):
        return "entry_blocked", "factor_budget"
    if not _safe_bool(row.get("allow_add")):
        return "probe_only", "exposure_add_gate"
    if not _safe_bool(row.get("staged_add_allowed")):
        return "probe_only", "staged_gate"
    if not _safe_bool(row.get("healthy_aggressive_final_add_allowed")):
        if first_blocking_reason.startswith("quality_label=") or first_blocking_reason == "participation_confidence_below_threshold":
            return "relay_drop_off", "participation_quality"
        if first_blocking_reason.startswith("state_label="):
            return "entry_blocked", "state_gate"
        return "probe_only", "healthy_policy"
    return "add_relay_pass", ""


def _lifecycle_group(row: pd.Series) -> str:
    first_reason = _safe_text(row.get("first_blocking_reason"))
    if first_reason.startswith("quality_label=") or first_reason == "participation_confidence_below_threshold":
        return "relay_drop_off"
    if first_reason.startswith("state_label=") or first_reason.startswith("factor_budget_violation="):
        return "entry_blocked"
    if first_reason in {"exposure_allow_add_false"} or first_reason.startswith("staged_gate_stage=") or first_reason.startswith("healthy_policy_label="):
        return "probe_only"
    final_add_allowed = _safe_bool(row.get("final_add_allowed"))
    if final_add_allowed:
        return "add_relay_pass"
    return "unclassified"


def _lifecycle_summary(trace_df: pd.DataFrame) -> pd.DataFrame:
    if trace_df.empty:
        return pd.DataFrame(columns=list(LIFECYCLE_COLUMNS))
    scoped = trace_df.copy()
    scoped["lifecycle_group"] = scoped.apply(_lifecycle_group, axis=1)
    summary = (
        scoped.groupby("lifecycle_group", dropna=False)
        .agg(
            trade_count=("trade_id", "nunique"),
            outcome_count=("trade_id", "size"),
            blocked_trade_count=("first_blocking_reason", lambda values: int(pd.Series(values).astype(str).str.len().gt(0).sum())),
        )
        .reset_index()
        .sort_values(["lifecycle_group"], kind="stable")
        .reset_index(drop=True)
    )
    return summary[list(LIFECYCLE_COLUMNS)]


def build_add_relay_diagnostics(
    shadow_log_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if shadow_log_df.empty:
        empty_trace = pd.DataFrame(
            columns=[
                "trade_id",
                "timestamp",
                "symbol",
                "participation_quality_label",
                "participation_expansion_score",
                "participation_fragility_score",
                "participation_confidence",
                "state_label",
                "continuation_risk_score",
                "factor_budget_allowed",
                "factor_budget_multiplier",
                "exposure_allow_add",
                "staged_gate_stage",
                "staged_add_allowed",
                "healthy_policy_label",
                "final_add_allowed",
                "final_size_multiplier",
                "baseline_realized_R",
                "shadow_realized_R_proxy",
                "quality_aware_realized_R_proxy",
                "healthy_aggressive_realized_R_proxy",
                "final_add_relay_outcome",
                "final_add_relay_block_stage",
                "first_blocking_reason",
                "all_blocking_reasons",
            ]
        )
        empty_gate = pd.DataFrame(columns=["quality_label", "gate_name", "stage_name", "input_count", "pass_count", "block_count", "pass_rate"])
        empty_reason = pd.DataFrame(
            columns=["quality_label", "gate_name", "blocking_reason", "block_count", "relay_stage", "reason", "reason_count", "trade_count"]
        )
        return empty_trace, empty_gate, empty_reason

    trace_rows: list[dict[str, Any]] = []
    reason_rows: list[dict[str, str]] = []

    for _, row in shadow_log_df.copy().iterrows():
        gate_decisions = _gate_decisions(row)
        blocking_reasons = [reason for _, passed, reason in gate_decisions if not passed and reason]
        first_blocking_reason = blocking_reasons[0] if blocking_reasons else ""
        legacy_outcome, legacy_block_stage = _legacy_outcome_fields(row, first_blocking_reason)

        for gate_name, passed, reason in gate_decisions:
            if not passed and reason:
                reason_rows.append(
                    {
                        "quality_label": _safe_text(row.get("participation_quality_label"), "UNKNOWN"),
                        "gate_name": gate_name,
                        "blocking_reason": reason,
                    }
                )

        trace_rows.append(
            {
                "trade_id": row.get("trade_id"),
                "timestamp": row.get("timestamp"),
                "symbol": row.get("symbol"),
                "participation_quality_label": _safe_text(row.get("participation_quality_label"), "UNKNOWN"),
                "participation_expansion_score": _safe_float(row.get("participation_expansion_score"), 0.0),
                "participation_fragility_score": _safe_float(row.get("participation_fragility_score"), 0.0),
                "participation_confidence": _safe_float(row.get("participation_confidence"), 0.0),
                "state_label": _safe_text(row.get("state_label"), "UNKNOWN"),
                "continuation_risk_score": _safe_float(row.get("continuation_risk_score"), 0.0),
                "factor_budget_allowed": not _safe_bool(row.get("factor_exposure_violated")),
                "factor_budget_multiplier": 0.0 if _safe_bool(row.get("factor_exposure_violated")) else 1.0,
                "exposure_allow_add": _safe_bool(row.get("allow_add")),
                "staged_gate_stage": _safe_text(row.get("staged_gate_stage"), "UNKNOWN"),
                "staged_add_allowed": _safe_bool(row.get("staged_add_allowed")),
                "healthy_policy_label": _safe_text(row.get("healthy_aggressive_policy_label"), "UNKNOWN"),
                "final_add_allowed": _safe_bool(row.get("healthy_aggressive_final_add_allowed")),
                "final_size_multiplier": _safe_float(row.get("healthy_aggressive_final_size_multiplier"), 0.0),
                "baseline_realized_R": _safe_float(row.get("baseline_realized_R"), 0.0),
                "shadow_realized_R_proxy": _safe_float(row.get("shadow_realized_R_proxy"), 0.0),
                "quality_aware_realized_R_proxy": _safe_float(row.get("quality_aware_realized_R_proxy"), 0.0),
                "healthy_aggressive_realized_R_proxy": _safe_float(row.get("healthy_aggressive_realized_R_proxy"), 0.0),
                "final_add_relay_outcome": legacy_outcome,
                "final_add_relay_block_stage": legacy_block_stage,
                "first_blocking_reason": first_blocking_reason,
                "all_blocking_reasons": "|".join(blocking_reasons),
            }
        )

    relay_trace_df = pd.DataFrame(trace_rows)
    gate_rows: list[dict[str, Any]] = []
    for quality_label, scoped in relay_trace_df.groupby("participation_quality_label", dropna=False):
        current = scoped.copy()
        for gate_name in GATE_ORDER:
            input_count = int(len(current))
            if gate_name == "participation_quality":
                passed_mask = current["first_blocking_reason"].astype(str).ne("quality_label=" + _safe_text(quality_label, "UNKNOWN"))
                passed_mask &= current["first_blocking_reason"].astype(str).ne("participation_confidence_below_threshold")
            elif gate_name == "state_gate":
                passed_mask = current["state_label"].astype(str).ne("DISLOCATION")
            elif gate_name == "factor_budget":
                passed_mask = current["factor_budget_allowed"].fillna(False).astype(bool)
            elif gate_name == "exposure_gate":
                passed_mask = current["exposure_allow_add"].fillna(False).astype(bool)
            elif gate_name == "staged_gate":
                passed_mask = current["staged_add_allowed"].fillna(False).astype(bool)
            else:
                passed_mask = current["final_add_allowed"].fillna(False).astype(bool)
            pass_count = int(passed_mask.sum())
            block_count = int(input_count - pass_count)
            gate_rows.append(
                {
                    "quality_label": quality_label,
                    "gate_name": gate_name,
                    "stage_name": "healthy_aggressive_gate" if gate_name == "healthy_policy" else gate_name,
                    "input_count": input_count,
                    "pass_count": pass_count,
                    "block_count": block_count,
                    "pass_rate": round(float(pass_count / input_count), 6) if input_count else 0.0,
                }
            )
            current = current[passed_mask].copy()
    gate_dropoff_df = pd.DataFrame(gate_rows)

    blocking_counter: Counter[tuple[str, str, str]] = Counter(
        (row["quality_label"], row["gate_name"], row["blocking_reason"]) for row in reason_rows
    )
    legacy_reason_rows: list[dict[str, str]] = []
    legacy_reason_columns = (
        ("state_engine", "shadow_reasons"),
        ("participation_quality", "participation_reasons"),
        ("quality_aware_policy", "quality_aware_reasons"),
        ("healthy_aggressive_policy", "healthy_aggressive_reasons"),
        ("factor_budget", "violated_factors"),
    )
    for _, row in shadow_log_df.copy().iterrows():
        quality_label = _safe_text(row.get("participation_quality_label"), "UNKNOWN")
        for relay_stage, column in legacy_reason_columns:
            for reason in _split_reason_text(row.get(column)):
                legacy_reason_rows.append(
                    {
                        "quality_label": quality_label,
                        "gate_name": relay_stage,
                        "blocking_reason": reason,
                    }
                )
        legacy_outcome, legacy_block_stage = _legacy_outcome_fields(row, "")
        _ = legacy_outcome
        if legacy_block_stage:
            legacy_reason_rows.append(
                {
                    "quality_label": quality_label,
                    "gate_name": "final_block_stage",
                    "blocking_reason": legacy_block_stage,
                }
            )
    for item in legacy_reason_rows:
        blocking_counter[(item["quality_label"], item["gate_name"], item["blocking_reason"])] += 1
    blocking_reasons_df = pd.DataFrame(
        [
            {
                "quality_label": quality_label,
                "gate_name": gate_name,
                "blocking_reason": blocking_reason,
                "block_count": count,
            }
            for (quality_label, gate_name, blocking_reason), count in blocking_counter.items()
        ]
    )
    if not blocking_reasons_df.empty:
        blocking_reasons_df = blocking_reasons_df.sort_values(
            ["quality_label", "gate_name", "block_count", "blocking_reason"],
            ascending=[True, True, False, True],
        ).reset_index(drop=True)
        blocking_reasons_df["relay_stage"] = blocking_reasons_df["gate_name"]
        blocking_reasons_df["reason"] = blocking_reasons_df["blocking_reason"]
        blocking_reasons_df["reason_count"] = blocking_reasons_df["block_count"]
        blocking_reasons_df["trade_count"] = blocking_reasons_df["block_count"]
    else:
        blocking_reasons_df = pd.DataFrame(
            columns=["quality_label", "gate_name", "blocking_reason", "block_count", "relay_stage", "reason", "reason_count", "trade_count"]
        )

    return relay_trace_df, gate_dropoff_df, blocking_reasons_df


def write_add_relay_report_artifacts(out_dir: Path | str, shadow_log_df: pd.DataFrame) -> dict[str, Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    relay_trace_df, gate_dropoff_df, blocking_reasons_df = build_add_relay_diagnostics(shadow_log_df)
    lifecycle_df = _lifecycle_summary(relay_trace_df)

    path_map = {
        "trace": target / REQUIRED_REPORT_FILES[0],
        "dropoff": target / REQUIRED_REPORT_FILES[1],
        "reasons": target / REQUIRED_REPORT_FILES[2],
        "lifecycle": target / REQUIRED_REPORT_FILES[3],
        "report": target / REQUIRED_REPORT_FILES[4],
    }
    relay_trace_df.to_csv(path_map["trace"], index=False)
    gate_dropoff_df.to_csv(path_map["dropoff"], index=False)
    blocking_reasons_df.to_csv(path_map["reasons"], index=False)
    lifecycle_df.to_csv(path_map["lifecycle"], index=False)
    path_map["report"].write_text(
        "\n".join(
            [
                "# Task 363 - Add Relay Lifecycle Diagnostics",
                "",
                "## Required Files",
                *[f"- {name}" for name in REQUIRED_REPORT_FILES],
            ]
        ),
        encoding="utf-8",
    )
    return path_map
