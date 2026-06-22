from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.replay.order_reconstruction_engine import build_order_replay_acceptance


REPORT_DIR = Path("docs/reports/task_603_6_acceptance_promotion_program/program_c_replay_completeness")
TASK_ID = "T603-6"
SURFACE_WEIGHTS = {
    "Decision Match": 0.2,
    "Order Match": 0.2,
    "Fill Match": 0.2,
    "Position Match": 0.2,
    "Lineage Match": 0.2,
}
PROGRAM_A_SUMMARY_TABLES = (
    "program_a_replay_summary",
    "program_a_summary",
    "program_a_replay_completeness_summary",
    "replay_promotion_program_a_summary",
)
PROGRAM_A_RATE_COLUMNS = (
    "lineage_rate",
    "lineage_match_rate",
    "lineage_complete_rate",
    "broker_trade_lineage_rate",
)
PROGRAM_A_PERCENT_RATE_COLUMNS = (
    "broker_fill_linkage",
    "lineage_coverage",
)
PROGRAM_A_SUMMARY_FILES = (
    Path("docs/reports/task_603_6_acceptance_promotion_program/program_a_broker_truth/broker_trade_lineage_summary.csv"),
    Path("docs/reports/task_603_6_acceptance_promotion_program/program_a_broker_truth/broker_trade_lineage_validation.csv"),
)
LINEAGE_COMPLETE_STATUS_VALUES = {
    "COMPLETE",
    "PASS",
    "PASSED",
    "LINEAGE_COMPLETE",
    "SOURCE_LINKED",
    "SOURCE_TRUTH",
}


@dataclass(frozen=True)
class ReplayCompletenessResult:
    validation: pd.DataFrame
    gap_breakdown: pd.DataFrame
    decision: pd.DataFrame
    order_replay_diff: pd.DataFrame


def _frame(value: pd.DataFrame | list[dict[str, Any]] | None) -> pd.DataFrame:
    if value is None:
        return pd.DataFrame()
    if isinstance(value, pd.DataFrame):
        return value.copy()
    return pd.DataFrame(value)


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


def _int(value: object, default: int = 0) -> int:
    try:
        if value is None or pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_ratio(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(float(part) / float(total), 6)


def _surface_status(rate: float, *, source_blocked: bool = False) -> str:
    if source_blocked:
        return "SOURCE_BLOCK"
    if rate > 0.99:
        return "PASS"
    return "FAIL"


def _validation_lookup(validation: pd.DataFrame) -> dict[str, pd.Series]:
    if validation.empty or "surface" not in validation.columns:
        return {}
    return {
        _text(row.get("surface")): row
        for _, row in validation.iterrows()
    }


def _validation_surface_row(validation: pd.DataFrame, surface: str) -> dict[str, Any]:
    row = _validation_lookup(validation).get(surface, pd.Series(dtype=object))
    evaluated = _int(row.get("evaluated_rows")) if not row.empty else 0
    matched = _int(row.get("matched_rows")) if not row.empty else 0
    rate = _float(row.get("match_rate")) if not row.empty else 0.0
    diff_required = _int(row.get("diff_reason_required_flag")) if not row.empty else int(rate < 1.0)
    return {
        "surface": surface,
        "evaluated_rows": evaluated,
        "matched_rows": matched,
        "match_rate": round(rate, 6),
        "weight": SURFACE_WEIGHTS[surface],
        "weighted_score": round(rate * SURFACE_WEIGHTS[surface], 6),
        "status": _surface_status(rate),
        "source_name": "replay_acceptance_validation",
        "source_status": "AVAILABLE" if evaluated > 0 else "SOURCE_BLOCK",
        "diff_reason_required_flag": diff_required,
        "source_blocked_flag": int(evaluated <= 0),
        "matching_policy": "EXACT_REPLAY_SURFACE_FROM_ORDER_MATCH_VALIDATOR",
    }


def _complete_flag_rate(frame: pd.DataFrame, column: str) -> tuple[int, int]:
    values = pd.to_numeric(frame[column], errors="coerce").fillna(0)
    total = int(len(frame))
    matched = int(values.eq(1).sum())
    return matched, total


def _status_rate(frame: pd.DataFrame, column: str) -> tuple[int, int]:
    statuses = frame[column].fillna("").astype(str).str.strip().str.upper()
    total = int(len(frame))
    matched = int(statuses.isin(LINEAGE_COMPLETE_STATUS_VALUES).sum())
    return matched, total


def _exact_id_lineage_rate(frame: pd.DataFrame) -> tuple[int, int] | None:
    source_column = ""
    for candidate in ("decision_id", "signal_id", "source_signal_id", "candidate_id"):
        if candidate in frame.columns:
            source_column = candidate
            break
    required = ["order_id", "fill_id"]
    lifecycle_column = "position_id" if "position_id" in frame.columns else "lifecycle_id" if "lifecycle_id" in frame.columns else ""
    if not source_column or not all(column in frame.columns for column in required) or not lifecycle_column:
        return None
    columns = [source_column, *required, lifecycle_column]
    present = pd.Series(True, index=frame.index)
    for column in columns:
        present = present & frame[column].fillna("").astype(str).str.strip().ne("")
    return int(present.sum()), int(len(frame))


def _broker_fill_linkage_rate(frame: pd.DataFrame) -> tuple[int, int] | None:
    if "broker_fill_id" not in frame.columns:
        return None
    required = ["position_id", "order_id", "fill_id", "broker_fill_id"]
    if any(column not in frame.columns for column in required):
        return None
    present = pd.Series(True, index=frame.index)
    for column in required:
        present = present & frame[column].fillna("").astype(str).str.strip().ne("")
    return int(present.sum()), int(len(frame))


def _lineage_from_broker_table(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return _lineage_source_block("broker_trade_lineage table is empty", "broker_trade_lineage")

    if "lineage_complete_flag" in frame.columns:
        matched, total = _complete_flag_rate(frame, "lineage_complete_flag")
        policy = "BROKER_TRADE_LINEAGE_COMPLETE_FLAG"
    elif "lineage_status" in frame.columns:
        matched, total = _status_rate(frame, "lineage_status")
        policy = "BROKER_TRADE_LINEAGE_STATUS"
    elif "status" in frame.columns:
        matched, total = _status_rate(frame, "status")
        policy = "BROKER_TRADE_LINEAGE_STATUS"
    elif "broker_fill_id" in frame.columns:
        broker_fill_rate = _broker_fill_linkage_rate(frame)
        if broker_fill_rate is None:
            return _lineage_source_block(
                "broker_trade_lineage has broker_fill_id but lacks required exact position/order/fill columns",
                "broker_trade_lineage",
            )
        matched, total = broker_fill_rate
        policy = "BROKER_TRADE_LINEAGE_BROKER_FILL_ID"
    else:
        exact_rate = _exact_id_lineage_rate(frame)
        if exact_rate is None:
            return _lineage_source_block(
                "broker_trade_lineage lacks lineage_complete_flag, lineage_status, broker_fill_id, or exact id columns",
                "broker_trade_lineage",
            )
        matched, total = exact_rate
        policy = "BROKER_TRADE_LINEAGE_EXACT_ID_COLUMNS"

    rate = _safe_ratio(matched, total)
    return {
        "surface": "Lineage Match",
        "evaluated_rows": total,
        "matched_rows": matched,
        "match_rate": rate,
        "weight": SURFACE_WEIGHTS["Lineage Match"],
        "weighted_score": round(rate * SURFACE_WEIGHTS["Lineage Match"], 6),
        "status": _surface_status(rate),
        "source_name": "broker_trade_lineage",
        "source_status": "AVAILABLE",
        "diff_reason_required_flag": int(matched < total),
        "source_blocked_flag": 0,
        "matching_policy": policy,
    }


def _program_a_rate_from_surface_rows(frame: pd.DataFrame) -> float | None:
    if "surface" not in frame.columns or "match_rate" not in frame.columns:
        return None
    surface = frame["surface"].fillna("").astype(str).str.strip().str.lower()
    rows = frame.loc[surface.str.contains("lineage")]
    if rows.empty:
        return None
    rate = _float(rows.iloc[0].get("match_rate"), default=-1.0)
    if 0.0 <= rate <= 1.0:
        return rate
    return None


def _program_a_rate_from_columns(frame: pd.DataFrame) -> float | None:
    if frame.empty:
        return None
    row = frame.iloc[0]
    for column in PROGRAM_A_RATE_COLUMNS:
        if column not in frame.columns:
            continue
        rate = _float(row.get(column), default=-1.0)
        if 0.0 <= rate <= 1.0:
            return rate
    for column in PROGRAM_A_PERCENT_RATE_COLUMNS:
        if column not in frame.columns:
            continue
        rate = _float(row.get(column), default=-1.0)
        if 0.0 <= rate <= 100.0:
            return round(rate / 100.0, 6)
    return None


def _lineage_from_program_a_summary(frame: pd.DataFrame, source_name: str) -> dict[str, Any]:
    if frame.empty:
        return _lineage_source_block(f"{source_name} table is empty", source_name)
    rate = _program_a_rate_from_surface_rows(frame)
    if rate is None:
        rate = _program_a_rate_from_columns(frame)
    if rate is None:
        return _lineage_source_block(f"{source_name} has no approved lineage rate column", source_name)
    row = frame.iloc[0]
    evaluated = _int(row.get("lineage_evaluated_rows"), default=0)
    if evaluated <= 0:
        evaluated = _int(row.get("runtime_sell_trade_count"), default=0)
    if evaluated <= 0:
        evaluated = _int(row.get("lineage_rows"), default=1)
    if evaluated <= 0:
        evaluated = 1
    matched = _int(row.get("lineage_matched_rows"), default=-1)
    if matched < 0 and "broker_fill_linked_rows" in frame.columns:
        matched = _int(row.get("broker_fill_linked_rows"), default=-1)
    if matched < 0 and "exact_local_lineage_rows" in frame.columns and "broker_fill_linkage" not in frame.columns:
        matched = _int(row.get("exact_local_lineage_rows"), default=-1)
    if matched < 0:
        matched = int(round(rate * evaluated))
    return {
        "surface": "Lineage Match",
        "evaluated_rows": evaluated,
        "matched_rows": matched,
        "match_rate": round(rate, 6),
        "weight": SURFACE_WEIGHTS["Lineage Match"],
        "weighted_score": round(rate * SURFACE_WEIGHTS["Lineage Match"], 6),
        "status": _surface_status(rate),
        "source_name": source_name,
        "source_status": "AVAILABLE",
        "diff_reason_required_flag": int(rate < 1.0),
        "source_blocked_flag": 0,
        "matching_policy": "PROGRAM_A_SUMMARY_LINEAGE_RATE",
    }


def _lineage_source_block(reason: str, source_name: str = "broker_trade_lineage_or_program_a_summary") -> dict[str, Any]:
    return {
        "surface": "Lineage Match",
        "evaluated_rows": 0,
        "matched_rows": 0,
        "match_rate": 0.0,
        "weight": SURFACE_WEIGHTS["Lineage Match"],
        "weighted_score": 0.0,
        "status": "SOURCE_BLOCK",
        "source_name": source_name,
        "source_status": "SOURCE_BLOCK",
        "diff_reason_required_flag": 1,
        "source_blocked_flag": 1,
        "matching_policy": "SOURCE_BLOCK_NO_APPROXIMATION",
        "source_block_reason": reason,
    }


def build_lineage_validation(
    broker_trade_lineage: pd.DataFrame | list[dict[str, Any]] | None = None,
    program_a_summary: pd.DataFrame | list[dict[str, Any]] | None = None,
    *,
    program_a_source_name: str = "program_a_summary",
) -> dict[str, Any]:
    broker_frame = _frame(broker_trade_lineage)
    if broker_trade_lineage is not None:
        return _lineage_from_broker_table(broker_frame)

    program_a_frame = _frame(program_a_summary)
    if program_a_summary is not None:
        return _lineage_from_program_a_summary(program_a_frame, program_a_source_name)

    return _lineage_source_block("broker_trade_lineage table and Program A summary are absent")


def _gap_template(surface: str) -> dict[str, str]:
    if surface == "Decision Match":
        return {
            "root_cause": "runtime decision evidence is missing or not replayed as an exact decision surface",
            "fix_candidate": "restore runtime_strategy_decisions evidence before replay promotion",
        }
    if surface == "Order Match":
        return {
            "root_cause": "exact order_id/run_id/status reconstruction is incomplete",
            "fix_candidate": "repair order capture or order lifecycle rows using exact order_id evidence only",
        }
    if surface == "Fill Match":
        return {
            "root_cause": "fill rows are missing exact order_id links",
            "fix_candidate": "repair fill capture so fill.order_id links to orders.order_id exactly",
        }
    if surface == "Position Match":
        return {
            "root_cause": "position lifecycle lacks exact entry/exit fill closure for replay",
            "fix_candidate": "write exact CLOSED or PARTIAL_EXIT lifecycle rows with entry_fill_id and exit_fill_id",
        }
    return {
        "root_cause": "broker trade lineage source is missing or lacks complete broker_fill_id linkage",
        "fix_candidate": "provide broker_fill_id-linked broker_trade_lineage rows or Program A lineage summary with approved lineage rate evidence",
    }


def build_gap_breakdown(validation: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in validation.iterrows():
        rate = _float(row.get("match_rate"))
        source_blocked = _int(row.get("source_blocked_flag")) == 1
        gap_rows = max(_int(row.get("evaluated_rows")) - _int(row.get("matched_rows")), 0)
        if rate >= 1.0 and not source_blocked:
            continue
        surface = _text(row.get("surface"))
        template = _gap_template(surface)
        if source_blocked:
            gap_type = "SOURCE_BLOCK"
            evidence = _text(row.get("source_block_reason")) or f"{surface} source unavailable"
            acceptance_impact = "Replay completeness cannot pass because missing sources are reported, not approximated."
        else:
            gap_type = "MATCH_GAP"
            evidence = f"{surface} matched {_int(row.get('matched_rows'))}/{_int(row.get('evaluated_rows'))}; match_rate={rate}"
            acceptance_impact = "Replay completeness cannot pass until this surface is above 0.99."
        rows.append(
            {
                "surface": surface,
                "gap_type": gap_type,
                "gap_rows": gap_rows,
                "evidence": evidence,
                "root_cause": template["root_cause"],
                "fix_candidate": template["fix_candidate"],
                "acceptance_impact": acceptance_impact,
            }
        )
    if not rows:
        rows.append(
            {
                "surface": "All Surfaces",
                "gap_type": "NO_MATERIAL_GAP",
                "gap_rows": 0,
                "evidence": "all five replay completeness surfaces scored 1.0",
                "root_cause": "no replay completeness gap observed in fixture",
                "fix_candidate": "none",
                "acceptance_impact": "Replay completeness gate passes when position_match_rate also exceeds 0.99.",
            }
        )
    return pd.DataFrame(rows)


def build_decision_summary(validation: pd.DataFrame, gap_breakdown: pd.DataFrame) -> pd.DataFrame:
    score = round(float(validation["weighted_score"].sum()), 6) if "weighted_score" in validation.columns else 0.0
    rates = {
        _text(row.get("surface")).lower().replace(" ", "_").replace("match", "match_rate"): _float(row.get("match_rate"))
        for _, row in validation.iterrows()
    }
    position_rate = rates.get("position_match_rate", 0.0)
    accepted = bool(score > 0.99 and position_rate > 0.99)
    source_block_count = int(validation.get("source_blocked_flag", pd.Series(dtype=int)).astype(int).sum())
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision_status": "PASS" if accepted else "FAIL",
                "replay_acceptance_status": "PASS" if accepted else "FAIL",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "replay_completeness_score": score,
                "decision_match_rate": rates.get("decision_match_rate", 0.0),
                "order_match_rate": rates.get("order_match_rate", 0.0),
                "fill_match_rate": rates.get("fill_match_rate", 0.0),
                "position_match_rate": position_rate,
                "lineage_match_rate": rates.get("lineage_match_rate", 0.0),
                "source_block_count": source_block_count,
                "gap_surface_count": int(len(gap_breakdown.loc[~gap_breakdown["gap_type"].eq("NO_MATERIAL_GAP")])),
                "inferred_matching_used_flag": 0,
                "real_capital_used_flag": 0,
                "acceptance_rule": "PASS iff replay_completeness_score > 0.99 and position_match_rate > 0.99",
                "next_required_task": "Clear source blocks and exact replay gaps before replay promotion.",
            }
        ]
    )


def build_replay_completeness_acceptance(
    decisions: pd.DataFrame | list[dict[str, Any]] | None,
    orders: pd.DataFrame | list[dict[str, Any]],
    fills: pd.DataFrame | list[dict[str, Any]] | None,
    position_lifecycle: pd.DataFrame | list[dict[str, Any]] | None,
    broker_trade_lineage: pd.DataFrame | list[dict[str, Any]] | None = None,
    program_a_summary: pd.DataFrame | list[dict[str, Any]] | None = None,
    events: pd.DataFrame | list[dict[str, Any]] | None = None,
    *,
    program_a_source_name: str = "program_a_summary",
) -> ReplayCompletenessResult:
    order_result = build_order_replay_acceptance(decisions, orders, fills, position_lifecycle, events)
    validation_rows = [
        _validation_surface_row(order_result.validation, "Decision Match"),
        _validation_surface_row(order_result.validation, "Order Match"),
        _validation_surface_row(order_result.validation, "Fill Match"),
        _validation_surface_row(order_result.validation, "Position Match"),
        build_lineage_validation(
            broker_trade_lineage,
            program_a_summary,
            program_a_source_name=program_a_source_name,
        ),
    ]
    validation = pd.DataFrame(validation_rows)
    gap_breakdown = build_gap_breakdown(validation)
    decision = build_decision_summary(validation, gap_breakdown)
    return ReplayCompletenessResult(
        validation=validation,
        gap_breakdown=gap_breakdown,
        decision=decision,
        order_replay_diff=order_result.order_replay_diff,
    )


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _read_table(con: sqlite3.Connection, table: str) -> pd.DataFrame:
    if not _table_exists(con, table):
        return pd.DataFrame()
    return pd.read_sql_query(f"SELECT * FROM {table}", con)


def _read_program_a_summary(
    con: sqlite3.Connection,
    summary_paths: tuple[Path, ...] = PROGRAM_A_SUMMARY_FILES,
) -> tuple[pd.DataFrame | None, str]:
    for table in PROGRAM_A_SUMMARY_TABLES:
        if _table_exists(con, table):
            return _read_table(con, table), table
    for path in summary_paths:
        if path.exists():
            return pd.read_csv(path), str(path)
    return None, ""


def _write_csv(report_dir: Path, filename: str, frame: pd.DataFrame) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(report_dir / filename, index=False, encoding="utf-8-sig")


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
    pd.DataFrame(rows, columns=["relative_path", "artifact_class", "size_bytes", "sha256"]).to_csv(
        report_dir / "artifact_manifest.csv",
        index=False,
    )


def _metric_line(validation: pd.DataFrame, surface: str) -> str:
    rows = validation.loc[validation["surface"].eq(surface)]
    if rows.empty:
        return f"- {surface}: match_rate=0.0 status=SOURCE_BLOCK"
    row = rows.iloc[0]
    return (
        f"- {surface}: matched={row['matched_rows']}/{row['evaluated_rows']} "
        f"match_rate={row['match_rate']} weight={row['weight']} status={row['status']}"
    )


def _material_gap_lines(gap_breakdown: pd.DataFrame) -> list[str]:
    return [
        f"- {row['surface']}: {row['gap_type']} gap_rows={row['gap_rows']} evidence={row['evidence']}"
        for _, row in gap_breakdown.iterrows()
    ]


def _write_completeness_report(result: ReplayCompletenessResult, report_dir: Path) -> None:
    decision = result.decision.iloc[0].to_dict()
    metric_lines = [_metric_line(result.validation, surface) for surface in SURFACE_WEIGHTS]
    lines = [
        "# Problem",
        "",
        "Program C replay promotion needs one score that weighs Decision, Order, Fill, Position, and Lineage at 20 percent each, without strategy, entry, universe, alpha, or real-capital changes.",
        "",
        "# Evidence",
        "",
        f"- replay_completeness_score={decision.get('replay_completeness_score')}",
        f"- decision_status={decision.get('decision_status')}",
        *metric_lines,
        f"- inferred_matching_used_flag={decision.get('inferred_matching_used_flag')}",
        f"- real_capital_used_flag={decision.get('real_capital_used_flag')}",
        "",
        "# Root Cause",
        "",
        "Replay completeness is blocked when any exact replay surface is below threshold or when broker trade lineage evidence is absent or incomplete. Missing sources are reported as source blocks and are not approximated.",
        "",
        "# Fix Candidate",
        "",
        "Keep using exact replay validation for Decision, Order, Fill, and Position, then add broker_fill_id-linked broker_trade_lineage rows or an approved Program A lineage summary before promotion review.",
        "",
        "# Acceptance Impact",
        "",
        f"- Acceptance rule: {decision.get('acceptance_rule')}.",
        f"- Current replay acceptance status: {decision.get('replay_acceptance_status')}.",
        "- Strategy acceptance remains NOT_ACCEPTED and deployment readiness remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
        "- No symbol/date/price/time proximity fallback was used.",
        "",
    ]
    (report_dir / "replay_completeness_report.md").write_text("\n".join(lines), encoding="utf-8")


def _write_gap_report(result: ReplayCompletenessResult, report_dir: Path) -> None:
    decision = result.decision.iloc[0].to_dict()
    gap_lines = _material_gap_lines(result.gap_breakdown)
    root_causes = sorted({_text(row.get("root_cause")) for _, row in result.gap_breakdown.iterrows() if _text(row.get("root_cause"))})
    fix_candidates = sorted({_text(row.get("fix_candidate")) for _, row in result.gap_breakdown.iterrows() if _text(row.get("fix_candidate"))})
    lines = [
        "# Problem",
        "",
        "Replay promotion needs an explicit gap breakdown so missing lifecycle or lineage evidence cannot be hidden inside a blended score.",
        "",
        "# Evidence",
        "",
        *gap_lines,
        "",
        "# Root Cause",
        "",
        *(f"- {cause}" for cause in root_causes),
        "",
        "# Fix Candidate",
        "",
        *(f"- {candidate}" for candidate in fix_candidates),
        "",
        "# Acceptance Impact",
        "",
        f"- replay_completeness_score={decision.get('replay_completeness_score')}",
        f"- position_match_rate={decision.get('position_match_rate')}",
        f"- replay_acceptance_status={decision.get('replay_acceptance_status')}",
        "- Acceptance remains blocked unless replay_completeness_score > 0.99 and position_match_rate > 0.99.",
        "- Missing raw sources are reported, not approximated.",
        "",
    ]
    (report_dir / "replay_gap_breakdown.md").write_text("\n".join(lines), encoding="utf-8")


def write_replay_completeness_outputs(result: ReplayCompletenessResult, report_dir: Path = REPORT_DIR) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(report_dir, "replay_completeness_validation.csv", result.validation)
    _write_csv(report_dir, "replay_gap_breakdown.csv", result.gap_breakdown)
    _write_csv(report_dir, "task_603_6_decision.csv", result.decision)
    _write_completeness_report(result, report_dir)
    _write_gap_report(result, report_dir)
    _write_manifest(report_dir)


def run_replay_completeness_from_db(
    db_path: Path,
    report_dir: Path = REPORT_DIR,
    *,
    program_a_summary_paths: tuple[Path, ...] = PROGRAM_A_SUMMARY_FILES,
) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    try:
        decisions = _read_table(con, "runtime_strategy_decisions")
        orders = _read_table(con, "orders")
        fills = _read_table(con, "fills")
        position_lifecycle = _read_table(con, "position_lifecycle")
        events = _read_table(con, "paper_order_execution_events")
        broker_trade_lineage = _read_table(con, "broker_trade_lineage") if _table_exists(con, "broker_trade_lineage") else None
        program_a_summary, program_a_source_name = _read_program_a_summary(con, program_a_summary_paths)
    finally:
        con.close()

    result = build_replay_completeness_acceptance(
        decisions,
        orders,
        fills,
        position_lifecycle,
        broker_trade_lineage,
        program_a_summary,
        events,
        program_a_source_name=program_a_source_name or "program_a_summary",
    )
    write_replay_completeness_outputs(result, report_dir)
    return result.decision.iloc[0].to_dict()
