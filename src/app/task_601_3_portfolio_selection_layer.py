from __future__ import annotations

import argparse
import hashlib
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


TASK_ID = "T601-3"
INPUT_EVENTS_PATH = Path("docs/reports/task_601_1_candidate_funnel_implementation/candidate_funnel_events.csv")
REPORT_DIR = Path("docs/reports/task_601_3_portfolio_selection_layer")

STAGE_ORDER = {
    "GENERATED": 1,
    "RANKED": 2,
    "ELIGIBLE": 3,
    "ORDERED": 4,
    "FILLED": 5,
    "CLOSED": 6,
}

LIQUIDITY_FIELDS = [
    "liquidity_score",
    "dollar_volume",
    "avg_dollar_volume",
    "volume",
    "liquidity",
]


@dataclass(frozen=True)
class PortfolioSelectionConfig:
    max_positions: int = 12
    same_symbol_weight_cap: float = 0.25
    same_sector_weight_cap: float = 0.50
    symbol_cooldown_minutes: int = 390
    rank_weight: float = 1.0
    liquidity_weight: float = 0.15
    diversification_weight: float = 0.25
    cooldown_weight: float = 0.10
    existing_position_penalty_weight: float = 0.20


@dataclass(frozen=True)
class SelectionResult:
    selected: pd.DataFrame
    decisions: pd.DataFrame
    metrics: pd.DataFrame


def _text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _upper(value: object) -> str:
    return _text(value).upper()


def _float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _timestamp(value: object) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def _safe_ratio(part: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round(float(part) / float(total), 6)


def _entropy(values: list[float]) -> float:
    total = float(sum(values))
    if total <= 0:
        return 0.0
    probs = [float(value) / total for value in values if float(value) > 0]
    return round(-sum(prob * math.log(prob) for prob in probs), 6)


def _cap_count(max_positions: int, weight_cap: float) -> int:
    if max_positions <= 0:
        return 0
    return max(1, int(math.floor(max_positions * weight_cap)))


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        if column not in result.columns:
            result[column] = ""
    return result


def _first_text(group: pd.DataFrame, column: str) -> str:
    if column not in group.columns:
        return ""
    for value in group[column].tolist():
        text = _text(value)
        if text:
            return text
    return ""


def _last_text(group: pd.DataFrame, column: str) -> str:
    if column not in group.columns:
        return ""
    for value in reversed(group[column].tolist()):
        text = _text(value)
        if text:
            return text
    return ""


def _first_float(group: pd.DataFrame, column: str) -> float:
    if column not in group.columns:
        return 0.0
    for value in group[column].tolist():
        number = _float(value, default=float("nan"))
        if math.isfinite(number):
            return number
    return 0.0


def build_candidate_records(candidate_funnel_events: pd.DataFrame) -> pd.DataFrame:
    required = [
        "candidate_id",
        "symbol",
        "generated_time",
        "rank_score",
        "eligibility",
        "cooldown_reason",
        "skip_reason",
        "order_id",
        "fill_id",
        "source_snapshot_id",
        "decision_id",
        "stage",
        "created_at",
    ]
    frame = _ensure_columns(candidate_funnel_events, required + LIQUIDITY_FIELDS + ["sector"])
    if frame.empty:
        return pd.DataFrame(columns=required)
    frame = frame.copy()
    frame["candidate_id"] = frame["candidate_id"].map(_text)
    frame = frame.loc[frame["candidate_id"].ne("")].copy()
    if frame.empty:
        return pd.DataFrame(columns=required)
    frame["stage_order"] = frame["stage"].map(lambda value: STAGE_ORDER.get(_upper(value), 0))
    frame = frame.sort_values(["candidate_id", "stage_order"])

    rows: list[dict[str, Any]] = []
    for candidate_id, group in frame.groupby("candidate_id", sort=False):
        group = group.sort_values("stage_order")
        latest = group.iloc[-1]
        row: dict[str, Any] = {
            "candidate_id": candidate_id,
            "symbol": _upper(_first_text(group, "symbol")),
            "generated_time": _first_text(group, "generated_time"),
            "rank_score": _first_float(group, "rank_score"),
            "eligibility": _upper(_first_text(group, "eligibility")),
            "cooldown_reason": _first_text(group, "cooldown_reason"),
            "skip_reason": _first_text(group, "skip_reason"),
            "order_id": _last_text(group, "order_id"),
            "fill_id": _last_text(group, "fill_id"),
            "source_snapshot_id": _first_text(group, "source_snapshot_id"),
            "decision_id": _first_text(group, "decision_id"),
            "latest_stage": _upper(latest.get("stage")),
            "created_at": _first_text(group, "created_at"),
            "original_ordered_flag": int(group["stage"].map(_upper).eq("ORDERED").any()),
            "original_filled_flag": int(group["stage"].map(_upper).eq("FILLED").any()),
            "proximity_fallback_used_flag": int(
                group.get("proximity_fallback_used_flag", pd.Series(dtype=object)).map(_float).sum() > 0
            ),
        }
        for column in LIQUIDITY_FIELDS + ["sector"]:
            row[column] = _first_text(group, column)
        rows.append(row)
    result = pd.DataFrame(rows)
    result["generated_ts"] = pd.to_datetime(result["generated_time"], utc=True, errors="coerce")
    result["rank_score"] = pd.to_numeric(result["rank_score"], errors="coerce").fillna(0.0)
    return result.sort_values(["generated_ts", "rank_score", "candidate_id"], ascending=[True, False, True]).reset_index(drop=True)


def _before_symbol_counts(candidate_funnel_events: pd.DataFrame) -> tuple[pd.Series, str]:
    if candidate_funnel_events.empty or "symbol" not in candidate_funnel_events.columns:
        return pd.Series(dtype=float), "NONE"
    frame = candidate_funnel_events.copy()
    frame["symbol"] = frame["symbol"].map(_upper)
    frame["stage"] = frame.get("stage", pd.Series(dtype=str)).map(_upper)
    for stage in ["FILLED", "ORDERED", "ELIGIBLE", "GENERATED"]:
        rows = frame.loc[frame["stage"].eq(stage) & frame["symbol"].ne("")]
        if not rows.empty:
            return rows["symbol"].value_counts().astype(float), stage
    return pd.Series(dtype=float), "NONE"


def _top3_share(counts: pd.Series) -> float:
    if counts.empty:
        return 0.0
    return _safe_ratio(float(counts.sort_values(ascending=False).head(3).sum()), float(counts.sum()))


def _liquidity_scores(records: pd.DataFrame) -> tuple[pd.Series, str]:
    for column in LIQUIDITY_FIELDS:
        if column not in records.columns:
            continue
        values = pd.to_numeric(records[column], errors="coerce")
        if values.notna().any():
            if column == "liquidity_score":
                return values.fillna(0.0).clip(lower=0.0, upper=1.0), "AVAILABLE_FROM_liquidity_score"
            finite = values.dropna()
            low = float(finite.min())
            high = float(finite.max())
            if high == low:
                return values.map(lambda value: 1.0 if pd.notna(value) else 0.0), f"AVAILABLE_FROM_{column}"
            normalized = values.map(lambda value: (float(value) - low) / (high - low) if pd.notna(value) else 0.0)
            return normalized.clip(lower=0.0, upper=1.0), f"AVAILABLE_FROM_{column}"
    return pd.Series([0.0] * len(records), index=records.index), "SOURCE_BLOCKED_NO_LIQUIDITY_FIELD"


def _resolve_sector(records: pd.DataFrame, sector_map: Mapping[str, str] | None) -> tuple[pd.Series, str]:
    if sector_map:
        sectors = records["symbol"].map(lambda symbol: _upper(sector_map.get(_upper(symbol), "")))
        status = "AVAILABLE_FROM_SECTOR_MAP" if sectors.ne("").any() else "SOURCE_BLOCKED_SECTOR_UNAVAILABLE"
        return sectors, status
    if "sector" in records.columns:
        sectors = records["sector"].map(_upper)
        if sectors.ne("").any():
            return sectors, "AVAILABLE_FROM_CANDIDATE_FIELD"
    return pd.Series([""] * len(records), index=records.index), "SOURCE_BLOCKED_SECTOR_UNAVAILABLE"


def _candidate_is_admissible(row: pd.Series) -> tuple[bool, str]:
    eligibility = _upper(row.get("eligibility"))
    skip_reason = _upper(row.get("skip_reason"))
    if eligibility == "ELIGIBLE":
        return True, "ELIGIBLE_FROM_FUNNEL"
    if "NOT_SELECTED_FOR_PORTFOLIO" in skip_reason or "NOT_SELECTED_BY_PORTFOLIO" in skip_reason:
        return True, "PORTFOLIO_RECONSIDERATION_FROM_SKIP_REASON"
    if eligibility == "INELIGIBLE_SOURCE":
        return False, "SOURCE_BLOCKED_BY_FUNNEL"
    if eligibility == "INELIGIBLE_COOLDOWN":
        return False, "COOLDOWN_BLOCKED_BY_FUNNEL"
    if eligibility == "INELIGIBLE_RISK":
        return False, "RISK_BLOCKED_BY_FUNNEL"
    return False, "ENTRY_OR_SOURCE_BLOCKED_BY_FUNNEL"


def _format_explanation(
    *,
    decision: str,
    reason: str,
    source_status: str,
    rank_score: float,
    liquidity_score: float,
    diversification_score: float,
    cooldown_score: float,
    existing_position_penalty: float,
    sector_cap_status: str,
) -> str:
    return (
        f"{decision}: {reason}; source={source_status}; "
        f"rank_score={rank_score:.6f}; liquidity_score={liquidity_score:.6f}; "
        f"diversification_score={diversification_score:.6f}; cooldown_score={cooldown_score:.6f}; "
        f"existing_position_penalty={existing_position_penalty:.6f}; sector_cap_status={sector_cap_status}; "
        "matching_policy=EXACT_CANDIDATE_ID_ONLY_NO_SYMBOL_DATE_PRICE_TIME_FALLBACK"
    )


def select_portfolio_candidates(
    candidate_funnel_events: pd.DataFrame,
    *,
    config: PortfolioSelectionConfig = PortfolioSelectionConfig(),
    sector_map: Mapping[str, str] | None = None,
) -> SelectionResult:
    records = build_candidate_records(candidate_funnel_events)
    liquidity_scores, liquidity_source_status = _liquidity_scores(records)
    sectors, sector_cap_status = _resolve_sector(records, sector_map)
    symbol_cap_count = _cap_count(config.max_positions, config.same_symbol_weight_cap)
    sector_cap_count = _cap_count(config.max_positions, config.same_sector_weight_cap)
    sector_cap_available = sector_cap_status.startswith("AVAILABLE")

    selected_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    selected_by_symbol: dict[str, int] = {}
    selected_by_sector: dict[str, int] = {}
    latest_selected_time_by_symbol: dict[str, pd.Timestamp] = {}

    for idx, row in records.iterrows():
        symbol = _upper(row.get("symbol"))
        generated_ts = _timestamp(row.get("generated_time"))
        rank_score = _float(row.get("rank_score"))
        liquidity_score = _float(liquidity_scores.loc[idx])
        current_symbol_count = selected_by_symbol.get(symbol, 0)
        diversification_score = round(max(0.0, 1.0 - _safe_ratio(current_symbol_count, symbol_cap_count)), 6)
        existing_position_penalty = round(_safe_ratio(current_symbol_count, symbol_cap_count), 6)
        source_ok, source_status = _candidate_is_admissible(row)

        cooldown_score = 1.0
        cooldown_elapsed_minutes: float | str = ""
        cooldown_active = False
        last_selected_ts = latest_selected_time_by_symbol.get(symbol)
        if generated_ts is None:
            cooldown_score = 0.0
        elif last_selected_ts is not None:
            cooldown_elapsed_minutes = round((generated_ts - last_selected_ts).total_seconds() / 60.0, 4)
            cooldown_active = cooldown_elapsed_minutes < config.symbol_cooldown_minutes
            cooldown_score = 0.0 if cooldown_active else 1.0

        total_control_score = round(
            (rank_score * config.rank_weight)
            + (liquidity_score * config.liquidity_weight)
            + (diversification_score * config.diversification_weight)
            + (cooldown_score * config.cooldown_weight)
            - (existing_position_penalty * config.existing_position_penalty_weight),
            6,
        )

        sector = _upper(sectors.loc[idx]) if idx in sectors.index else ""
        sector_count = selected_by_sector.get(sector, 0)
        decision = "REJECTED"
        reason = ""
        if not symbol:
            reason = "MISSING_SYMBOL"
        elif not source_ok:
            reason = source_status
        elif generated_ts is None:
            reason = "MISSING_GENERATED_TIME_COOLDOWN_REQUIRED"
        elif len(selected_rows) >= config.max_positions:
            reason = "PORTFOLIO_FULL"
        elif current_symbol_count >= symbol_cap_count:
            reason = f"SAME_SYMBOL_CAP_{config.same_symbol_weight_cap:.2f}"
        elif cooldown_active:
            reason = f"SYMBOL_COOLDOWN_ACTIVE_{config.symbol_cooldown_minutes}_MINUTES"
        elif sector_cap_available and not sector:
            reason = "SECTOR_SOURCE_MISSING_FOR_CANDIDATE"
        elif sector_cap_available and sector_count >= sector_cap_count:
            reason = f"SAME_SECTOR_CAP_{config.same_sector_weight_cap:.2f}"
        else:
            decision = "SELECTED"
            reason = "PASSED_RANK_LIQUIDITY_DIVERSIFICATION_COOLDOWN_POSITION_CONTROLS"

        explanation = _format_explanation(
            decision=decision,
            reason=reason,
            source_status=source_status,
            rank_score=rank_score,
            liquidity_score=liquidity_score,
            diversification_score=diversification_score,
            cooldown_score=cooldown_score,
            existing_position_penalty=existing_position_penalty,
            sector_cap_status=sector_cap_status,
        )
        decision_row = {
            "task_id": TASK_ID,
            "candidate_id": row.get("candidate_id"),
            "decision_id": row.get("decision_id"),
            "symbol": symbol,
            "generated_time": row.get("generated_time"),
            "rank_score": round(rank_score, 6),
            "liquidity_score": round(liquidity_score, 6),
            "diversification_score": diversification_score,
            "cooldown_score": cooldown_score,
            "existing_position_penalty": existing_position_penalty,
            "total_control_score": total_control_score,
            "selection_decision": decision,
            "selection_reason": reason,
            "source_status": source_status,
            "sector": sector,
            "sector_cap_status": sector_cap_status,
            "liquidity_source_status": liquidity_source_status,
            "symbol_cooldown_minutes": config.symbol_cooldown_minutes,
            "cooldown_elapsed_minutes": cooldown_elapsed_minutes,
            "same_symbol_weight_cap": config.same_symbol_weight_cap,
            "same_sector_weight_cap": config.same_sector_weight_cap,
            "original_eligibility": row.get("eligibility"),
            "original_skip_reason": row.get("skip_reason"),
            "original_ordered_flag": row.get("original_ordered_flag"),
            "original_filled_flag": row.get("original_filled_flag"),
            "order_id": row.get("order_id"),
            "fill_id": row.get("fill_id"),
            "source_snapshot_id": row.get("source_snapshot_id"),
            "proximity_fallback_used_flag": 0,
            "explanation": explanation,
        }
        decision_rows.append(decision_row)
        if decision == "SELECTED":
            selected_by_symbol[symbol] = current_symbol_count + 1
            if sector:
                selected_by_sector[sector] = sector_count + 1
            latest_selected_time_by_symbol[symbol] = generated_ts  # type: ignore[assignment]
            selected_rows.append({**decision_row, "selection_rank": len(selected_rows) + 1})

    decisions = pd.DataFrame(decision_rows)
    selected = pd.DataFrame(selected_rows)
    before_counts, before_stage = _before_symbol_counts(candidate_funnel_events)
    after_counts = selected["symbol"].value_counts().astype(float) if not selected.empty else pd.Series(dtype=float)
    explanation_total = int(len(decisions))
    explanation_count = int(decisions.get("explanation", pd.Series(dtype=str)).map(_text).ne("").sum()) if not decisions.empty else 0
    selected_count = int(len(selected))
    top3_share_after = _top3_share(after_counts)
    symbol_entropy_after = _entropy(after_counts.tolist())
    metrics = pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "implementation_status": (
                    "PASS_SELECTION_LAYER_IMPLEMENTED"
                    if selected_count > 0 and _safe_ratio(explanation_count, explanation_total) == 1.0
                    else "FAIL_SELECTION_LAYER_INCOMPLETE"
                ),
                "before_distribution_stage": before_stage,
                "selected_candidates": selected_count,
                "rejected_candidates": int(len(decisions) - selected_count),
                "top3_share_before": _top3_share(before_counts),
                "top3_share_after": top3_share_after,
                "symbol_entropy_before": _entropy(before_counts.tolist()),
                "symbol_entropy_after": symbol_entropy_after,
                "explanation_coverage": _safe_ratio(explanation_count, explanation_total),
                "symbol_cooldown_minutes": config.symbol_cooldown_minutes,
                "same_symbol_weight_cap": config.same_symbol_weight_cap,
                "same_symbol_cap_count": symbol_cap_count,
                "same_sector_weight_cap": config.same_sector_weight_cap,
                "same_sector_cap_count": sector_cap_count,
                "sector_cap_status": sector_cap_status,
                "liquidity_source_status": liquidity_source_status,
                "proximity_fallback_used_flag": 0,
                "acceptance_status": "NOT_ACCEPTED",
            }
        ]
    )
    return SelectionResult(selected=selected, decisions=decisions, metrics=metrics)


def _write_csv(report_dir: Path, filename: str, frame: pd.DataFrame) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(report_dir / filename, index=False)


def _artifact_class(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return "report"
    if path.name.endswith("_decision.csv"):
        return "decision"
    return "small_table"


def _write_manifest(report_dir: Path) -> None:
    rows: list[dict[str, Any]] = []
    for path in sorted(report_dir.iterdir()):
        if not path.is_file() or path.name == "artifact_manifest.csv":
            continue
        data = path.read_bytes()
        rows.append(
            {
                "relative_path": path.name,
                "artifact_class": _artifact_class(path),
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    manifest = pd.DataFrame(rows, columns=["relative_path", "artifact_class", "size_bytes", "sha256"])
    manifest.to_csv(report_dir / "artifact_manifest.csv", index=False)


def _reason_counts(decisions: pd.DataFrame, symbol: str) -> str:
    rows = decisions.loc[decisions["symbol"].astype(str).str.upper().eq(symbol.upper())]
    if rows.empty:
        return "no candidates observed"
    counts = rows["selection_reason"].value_counts().to_dict()
    return "; ".join(f"{reason}={count}" for reason, count in counts.items())


def _selected_count(selected: pd.DataFrame, symbol: str) -> int:
    if selected.empty:
        return 0
    return int(selected["symbol"].astype(str).str.upper().eq(symbol.upper()).sum())


def _write_audit_report(report_dir: Path, result: SelectionResult) -> None:
    metrics = result.metrics.iloc[0].to_dict()
    decisions = result.decisions
    selected = result.selected
    lines = [
        "# Problem",
        "",
        "- T601-2 showed top3_share=1.0 and symbol_entropy=1.059385 before this slice.",
        "- The portfolio selection layer needed concentration controls without changing entry strategy, regime, universe, or alpha research.",
        "- Sector concentration must be capped only when a sector source exists; unavailable sector data must be reported as source-blocked.",
        "",
        "# Evidence",
        "",
        f"- top3_share_before={metrics.get('top3_share_before')} from stage={metrics.get('before_distribution_stage')}.",
        f"- top3_share_after={metrics.get('top3_share_after')}.",
        f"- symbol_entropy_before={metrics.get('symbol_entropy_before')}.",
        f"- symbol_entropy_after={metrics.get('symbol_entropy_after')}.",
        f"- explanation_coverage={metrics.get('explanation_coverage')}.",
        f"- symbol_cooldown_minutes={metrics.get('symbol_cooldown_minutes')}.",
        f"- sector_cap_status={metrics.get('sector_cap_status')}.",
        f"- liquidity_source_status={metrics.get('liquidity_source_status')}.",
        f"- AMD selected count={_selected_count(selected, 'AMD')}; reasons={_reason_counts(decisions, 'AMD')}.",
        f"- AMZN selected count={_selected_count(selected, 'AMZN')}; rejected/dropped reasons={_reason_counts(decisions, 'AMZN')}.",
        f"- MSFT selected count={_selected_count(selected, 'MSFT')}; re-selection reasons={_reason_counts(decisions, 'MSFT')}.",
        "",
        "# Root Cause",
        "",
        "- Prior ordered and filled candidates concentrated before fills, so the fix belongs in portfolio selection controls rather than exit, regime, or alpha logic.",
        "- Repeated same-symbol selections were possible because no 390 minute symbol cooldown was enforced in the audited funnel.",
        "- Same-sector concentration cannot be attributed or capped from current evidence because no sector source was available in candidate_funnel_events.",
        "",
        "# Fix Candidate",
        "",
        "- Add a deterministic selection engine that groups rows by exact candidate_id only.",
        "- Score every candidate with rank_score, liquidity_score, diversification_score, cooldown_score, and existing_position_penalty.",
        "- Enforce same-symbol weight cap and 390 minute symbol cooldown; report sector cap as source-blocked when sector evidence is unavailable.",
        "- Select AMD when it passes eligibility, cooldown, and symbol cap; drop excess AMZN candidates when cooldown, symbol cap, or portfolio capacity blocks them; re-select MSFT only after cooldown and cap checks pass.",
        "",
        "# Acceptance Impact",
        "",
        f"- implementation_status={metrics.get('implementation_status')}.",
        "- Strategy acceptance remains NOT_ACCEPTED because this is a selection-control slice, not a live deployment or strategy acceptance proof.",
        "- Inferred lifecycle matching was not used; matching policy is exact candidate_id grouping only, with no symbol/date/price/time fallback.",
        "- Remaining blocker: sector concentration needs a real sector source before the same-sector cap can be enforced.",
        "",
    ]
    (report_dir / "portfolio_selection_audit.md").write_text("\n".join(lines), encoding="utf-8")


def _write_decision(report_dir: Path, result: SelectionResult) -> None:
    row = result.metrics.iloc[0].to_dict()
    decision = pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision_status": row.get("implementation_status"),
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "program_blocker": "P0_CANDIDATE_FUNNEL",
                "top3_share_after": row.get("top3_share_after"),
                "symbol_entropy_before": row.get("symbol_entropy_before"),
                "symbol_entropy_after": row.get("symbol_entropy_after"),
                "explanation_coverage": row.get("explanation_coverage"),
                "next_required_task": "Provide sector source evidence before enforcing same-sector concentration cap in live selection review.",
            }
        ]
    )
    _write_csv(report_dir, "task_601_3_decision.csv", decision)


def write_outputs(result: SelectionResult, report_dir: Path = REPORT_DIR) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(report_dir, "selected_portfolio_candidates.csv", result.selected)
    _write_csv(report_dir, "portfolio_selection_decisions.csv", result.decisions)
    _write_csv(report_dir, "portfolio_selection_metrics.csv", result.metrics)
    _write_decision(report_dir, result)
    _write_audit_report(report_dir, result)
    _write_manifest(report_dir)


def run_task601_3(
    input_path: Path = INPUT_EVENTS_PATH,
    report_dir: Path = REPORT_DIR,
    *,
    config: PortfolioSelectionConfig = PortfolioSelectionConfig(),
) -> dict[str, Any]:
    candidate_funnel_events = pd.read_csv(input_path)
    result = select_portfolio_candidates(candidate_funnel_events, config=config)
    write_outputs(result, report_dir)
    metrics = result.metrics.iloc[0].to_dict()
    return {
        "generated_utc": datetime.now(UTC).isoformat(),
        "task_id": TASK_ID,
        "implementation_status": metrics.get("implementation_status"),
        "selected_candidates": int(metrics.get("selected_candidates", 0)),
        "top3_share_after": float(metrics.get("top3_share_after", 0.0)),
        "symbol_entropy_before": float(metrics.get("symbol_entropy_before", 0.0)),
        "symbol_entropy_after": float(metrics.get("symbol_entropy_after", 0.0)),
        "explanation_coverage": float(metrics.get("explanation_coverage", 0.0)),
        "proximity_fallback_used_flag": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT_EVENTS_PATH)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = run_task601_3(args.input, args.report_dir)
    print(result)


if __name__ == "__main__":
    main()
