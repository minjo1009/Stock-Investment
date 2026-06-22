from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_OUT_DIR = Path("docs/reports/task_377_lifecycle_coverage_expansion")
TASK_376_EVALUATION_PATH = Path("docs/reports/task_376_persistence_universe_rebuild/persistence_universe_evaluation_panel.csv")
THEME_LEADER_SYMBOLS = {"AMD", "NVDA", "AVGO", "QCOM", "AAPL", "MSFT", "GOOGL", "META", "AMZN", "COST"}
SEMIS_SYMBOLS = {"AMD", "NVDA", "AVGO", "QCOM"}
PLATFORM_SYMBOLS = {"AAPL", "MSFT", "GOOGL", "META", "AMZN", "COST"}


@dataclass(frozen=True)
class LifecycleCoverage377Artifacts:
    coverage_gap_audit: pd.DataFrame
    anchored_oos_core_miss_audit: pd.DataFrame
    theme_leader_miss_audit: pd.DataFrame
    recovery_priority_queue: pd.DataFrame
    summary_decision: pd.DataFrame


def _safe_numeric(series: pd.Series | None, index: pd.Index, default: float = 0.0) -> pd.Series:
    if series is None:
        return pd.Series(default, index=index, dtype=float)
    return pd.to_numeric(series, errors="coerce").fillna(default)


def _load_evaluation_panel() -> pd.DataFrame:
    return pd.read_csv(TASK_376_EVALUATION_PATH, encoding="utf-8-sig")


def _theme_group(symbol: Any) -> str:
    text = str(symbol).upper()
    if text in SEMIS_SYMBOLS:
        return "semis_leader"
    if text in PLATFORM_SYMBOLS:
        return "platform_quality_leader"
    return "non_theme"


def _core_miss_reasons(row: pd.Series) -> str:
    bucket = str(row.get("persistence_universe_bucket", ""))
    if bucket == "persistence_core":
        return "already_core"
    reasons: list[str] = []
    if str(row.get("risk_gate_v1", "")) == "fail":
        reasons.append("risk_gate_fail")
    if float(pd.to_numeric(pd.Series([row.get("data_leadership_gate_v1")]), errors="coerce").fillna(0).iloc[0]) < 1.0:
        reasons.append("data_leadership_gate_fail")
    if str(row.get("market_breadth_state", "")) != "broad":
        reasons.append("breadth_not_broad")
    if str(row.get("sector_leadership_state", "")) not in {"broad_led", "risk_on"}:
        reasons.append("sector_leadership_not_broad_led_or_risk_on")
    if float(pd.to_numeric(pd.Series([row.get("tech_led_narrow_flag")]), errors="coerce").fillna(0).iloc[0]) > 0:
        reasons.append("tech_led_narrow")
    if float(pd.to_numeric(pd.Series([row.get("theme_prior_v1")]), errors="coerce").fillna(0).iloc[0]) < 1.0:
        reasons.append("theme_prior_not_core")
    if str(row.get("forward_breakout_bucket", "")) not in {"high_quality", "mixed_quality"}:
        reasons.append("forward_bucket_not_core_eligible")
    if float(pd.to_numeric(pd.Series([row.get("forward_persistence_score")]), errors="coerce").fillna(0).iloc[0]) < 0.66:
        reasons.append("score_below_core_threshold")
    return "|".join(reasons) if reasons else "other_core_miss"


def _coverage_gap_class(row: pd.Series) -> str:
    covered = int(float(pd.to_numeric(pd.Series([row.get("lifecycle_coverage_flag")]), errors="coerce").fillna(0).iloc[0]))
    if covered > 0:
        return "covered"
    split = str(row.get("current_split", ""))
    bucket = str(row.get("persistence_universe_bucket", ""))
    theme = _theme_group(row.get("symbol"))
    if split == "anchored_oos" and bucket in {"persistence_core", "qualified_watchlist"}:
        return "anchored_oos_core_or_watchlist_missing"
    if split == "anchored_oos":
        return "anchored_oos_suppressed_missing"
    if bucket == "persistence_core":
        return "core_missing"
    if bucket == "qualified_watchlist":
        return "watchlist_missing"
    if theme != "non_theme":
        return "theme_leader_missing"
    if bucket == "suppressed_crowding_risk":
        return "suppressed_missing_low_priority"
    return "missing_lifecycle_join"


def _coverage_status(row: pd.Series) -> str:
    covered = int(float(pd.to_numeric(pd.Series([row.get("lifecycle_coverage_flag")]), errors="coerce").fillna(0).iloc[0]))
    return "covered" if covered > 0 else "coverage_missing"


def _theme_audit_status(row: pd.Series) -> str:
    bucket = str(row.get("persistence_universe_bucket", ""))
    covered = _coverage_status(row) == "covered"
    if bucket == "persistence_core":
        return "theme_core_covered" if covered else "theme_core_coverage_missing"
    if bucket == "qualified_watchlist":
        return "theme_watchlist_covered" if covered else "theme_watchlist_coverage_missing"
    if str(row.get("risk_gate_v1", "")) == "fail":
        return "theme_suppressed_by_risk"
    if float(pd.to_numeric(pd.Series([row.get("data_leadership_gate_v1")]), errors="coerce").fillna(0).iloc[0]) < 1.0:
        return "theme_suppressed_by_data_leadership"
    if str(row.get("forward_breakout_bucket", "")) not in {"high_quality", "mixed_quality"}:
        return "theme_suppressed_by_forward_quality"
    return "theme_prior_not_core_by_design"


def _priority_score(row: pd.Series) -> int:
    score = 0
    gap_class = str(row.get("coverage_gap_class", ""))
    if gap_class == "anchored_oos_core_or_watchlist_missing":
        score += 100
    elif gap_class == "core_missing":
        score += 80
    elif gap_class == "watchlist_missing":
        score += 60
    elif gap_class == "theme_leader_missing":
        score += 25
    elif gap_class == "anchored_oos_suppressed_missing":
        score += 20
    if str(row.get("risk_gate_v1", "")) == "fail":
        score -= 20
    score += int(float(pd.to_numeric(pd.Series([row.get("forward_persistence_score")]), errors="coerce").fillna(0).iloc[0]) * 10)
    return score


def _base_columns() -> list[str]:
    return [
        "trade_id",
        "symbol",
        "current_split",
        "persistence_universe_bucket",
        "lifecycle_coverage_flag",
        "stateful_persistence_target_v1",
        "target_reason",
        "target_confidence",
        "risk_gate_v1",
        "data_leadership_gate_v1",
        "market_breadth_state",
        "sector_leadership_state",
        "tech_led_narrow_flag",
        "theme_prior_v1",
        "forward_breakout_bucket",
        "forward_persistence_score",
    ]


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = np.nan
    return out


def _coverage_gap_audit(evaluation: pd.DataFrame) -> pd.DataFrame:
    frame = _ensure_columns(evaluation, _base_columns())
    frame["coverage_gap_class"] = frame.apply(_coverage_gap_class, axis=1)
    frame["theme_group"] = frame["symbol"].map(_theme_group)
    missing = frame[frame["lifecycle_coverage_flag"].fillna(0).astype(int).eq(0)].copy()
    return missing[[*_base_columns(), "theme_group", "coverage_gap_class"]].sort_values(
        ["current_split", "coverage_gap_class", "symbol", "trade_id"], kind="stable"
    ).reset_index(drop=True)


def _anchored_oos_core_miss_audit(evaluation: pd.DataFrame) -> pd.DataFrame:
    frame = _ensure_columns(evaluation, _base_columns())
    anchored = frame[frame["current_split"].astype(str).eq("anchored_oos")].copy()
    anchored["core_miss_reasons"] = anchored.apply(_core_miss_reasons, axis=1)
    anchored["theme_group"] = anchored["symbol"].map(_theme_group)
    anchored["coverage_status"] = anchored.apply(_coverage_status, axis=1)
    return anchored[[*_base_columns(), "theme_group", "coverage_status", "core_miss_reasons"]].sort_values(
        ["persistence_universe_bucket", "symbol", "trade_id"], kind="stable"
    ).reset_index(drop=True)


def _theme_leader_miss_audit(evaluation: pd.DataFrame) -> pd.DataFrame:
    frame = _ensure_columns(evaluation, _base_columns())
    frame["theme_group"] = frame["symbol"].map(_theme_group)
    theme = frame[frame["theme_group"].ne("non_theme")].copy()
    theme["core_miss_reasons"] = theme.apply(_core_miss_reasons, axis=1)
    theme["theme_audit_status"] = theme.apply(_theme_audit_status, axis=1)
    return theme[[*_base_columns(), "theme_group", "theme_audit_status", "core_miss_reasons"]].sort_values(
        ["symbol", "current_split", "trade_id"], kind="stable"
    ).reset_index(drop=True)


def _recovery_priority_queue(coverage_gap: pd.DataFrame) -> pd.DataFrame:
    queue = coverage_gap.copy()
    if queue.empty:
        return queue.assign(recovery_priority_score=pd.Series(dtype=int), recovery_priority_tier=pd.Series(dtype=str))
    queue["recovery_priority_score"] = queue.apply(_priority_score, axis=1)
    queue["recovery_priority_tier"] = np.select(
        [
            queue["coverage_gap_class"].isin({"anchored_oos_core_or_watchlist_missing", "core_missing"}),
            queue["coverage_gap_class"].isin({"watchlist_missing", "theme_leader_missing"}),
            queue["coverage_gap_class"].eq("anchored_oos_suppressed_missing"),
        ],
        ["p0_anchored_or_core", "p1_watchlist_or_theme", "p2_standard"],
        default="p3_low_priority",
    )
    return queue.sort_values(["recovery_priority_score", "current_split", "symbol"], ascending=[False, True, True], kind="stable").reset_index(drop=True)


def _summary_decision(
    evaluation: pd.DataFrame,
    coverage_gap: pd.DataFrame,
    anchored_audit: pd.DataFrame,
    theme_audit: pd.DataFrame,
    queue: pd.DataFrame,
) -> pd.DataFrame:
    total = int(len(evaluation))
    missing = int(len(coverage_gap))
    anchored = evaluation[evaluation["current_split"].astype(str).eq("anchored_oos")]
    anchored_missing = int((anchored["lifecycle_coverage_flag"].fillna(0).astype(int) == 0).sum()) if "lifecycle_coverage_flag" in anchored.columns else 0
    core_missing = int(
        (
            coverage_gap["persistence_universe_bucket"].astype(str).isin({"persistence_core", "qualified_watchlist"})
        ).sum()
    ) if not coverage_gap.empty else 0
    theme_missing = int((coverage_gap["theme_group"].astype(str).ne("non_theme")).sum()) if not coverage_gap.empty else 0
    return pd.DataFrame(
        [
            {
                "task_377_verdict": "COMPLETE_PASS",
                "next_priority": "lifecycle_coverage_expansion",
                "strategy_acceptance_status": "UNCHANGED_EXPANDED_SAMPLE_REQUIRED",
                "total_candidates": total,
                "coverage_missing_count": missing,
                "coverage_missing_share": round(missing / total, 6) if total else 0.0,
                "anchored_oos_missing_count": anchored_missing,
                "core_or_watchlist_missing_count": core_missing,
                "theme_leader_missing_count": theme_missing,
                "anchored_core_miss_rows": int(len(anchored_audit)),
                "theme_leader_audit_rows": int(len(theme_audit)),
                "recovery_queue_rows": int(len(queue)),
            }
        ]
    )


def build_lifecycle_coverage_expansion_377(
    *,
    evaluation_panel_df: pd.DataFrame | None = None,
) -> LifecycleCoverage377Artifacts:
    evaluation = evaluation_panel_df.copy() if evaluation_panel_df is not None else _load_evaluation_panel()
    coverage_gap = _coverage_gap_audit(evaluation)
    anchored_audit = _anchored_oos_core_miss_audit(evaluation)
    theme_audit = _theme_leader_miss_audit(evaluation)
    queue = _recovery_priority_queue(coverage_gap)
    decision = _summary_decision(evaluation, coverage_gap, anchored_audit, theme_audit, queue)
    return LifecycleCoverage377Artifacts(
        coverage_gap_audit=coverage_gap,
        anchored_oos_core_miss_audit=anchored_audit,
        theme_leader_miss_audit=theme_audit,
        recovery_priority_queue=queue,
        summary_decision=decision,
    )


def write_lifecycle_coverage_expansion_377(
    artifacts: LifecycleCoverage377Artifacts,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.coverage_gap_audit.to_csv(out_dir / "task_377_coverage_gap_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.anchored_oos_core_miss_audit.to_csv(out_dir / "task_377_anchored_oos_core_miss_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.theme_leader_miss_audit.to_csv(out_dir / "task_377_theme_leader_miss_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.recovery_priority_queue.to_csv(out_dir / "task_377_recovery_priority_queue.csv", index=False, encoding="utf-8-sig")
    artifacts.summary_decision.to_csv(out_dir / "task_377_summary_decision.csv", index=False, encoding="utf-8-sig")
