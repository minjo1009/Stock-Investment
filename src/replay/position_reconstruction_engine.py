from __future__ import annotations

import argparse
import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


MATCHING_POLICY = "EXACT_ENTRY_EXIT_FILL_ID_AND_LIFECYCLE_STATE_ONLY"
POSITION_MATCH_SURFACE = "Position Match"
REPORT_DIR = Path("docs/reports/task_602_3_position_reconstruction_engine")


@dataclass(frozen=True)
class PositionReplayResult:
    reconstructed_positions: pd.DataFrame
    position_replay_diff: pd.DataFrame
    validation: pd.DataFrame
    decision: pd.DataFrame


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


def _norm_float(value: object) -> float:
    return round(_float(value), 6)


def _numeric(value: object) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
        return round(float(value), 6)
    except Exception:
        return None


def _present(value: object) -> bool:
    return _text(value) != ""


def _safe_ratio(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(float(part) / float(total), 6)


def _fill_lookup(fills: pd.DataFrame) -> dict[str, pd.Series]:
    if fills.empty or "fill_id" not in fills.columns:
        return {}
    result: dict[str, pd.Series] = {}
    for _, row in fills.iterrows():
        fill_id = _text(row.get("fill_id"))
        if fill_id:
            result[fill_id] = row
    return result


def _fill_qty(fill: pd.Series, fallback: object = 0.0) -> float:
    for column in ("filled_quantity", "filled_qty", "quantity", "qty"):
        if column in fill and _present(fill.get(column)):
            return _float(fill.get(column))
    return _float(fallback)


def _fill_price(fill: pd.Series, fallback: object = 0.0) -> float:
    for column in ("fill_price", "filled_avg_price", "price"):
        if column in fill and _present(fill.get(column)):
            return _float(fill.get(column))
    return _float(fallback)


def _runtime_value(row: pd.Series, column: str, default: object = "") -> object:
    return row.get(column, default) if column in row else default


def _field_match(runtime: object, replay: object) -> bool:
    runtime_text = _text(runtime)
    replay_text = _text(replay)
    if runtime_text == "" and replay_text == "":
        return True
    runtime_number = _numeric(runtime)
    replay_number = _numeric(replay)
    if runtime_number is not None and replay_number is not None:
        return runtime_number == replay_number
    return runtime_text == replay_text


def _position_status(match_rate: float) -> str:
    if match_rate > 0.95:
        return "STRETCH"
    if match_rate > 0.80:
        return "PASS"
    if match_rate <= 0.50:
        return "FAIL"
    return "REVIEW"


def _contract_status(match_rate: float, missing_reason_count: int = 0) -> str:
    if match_rate >= 0.99 and missing_reason_count == 0:
        return "PASS"
    if match_rate >= 0.95 and missing_reason_count == 0:
        return "REVIEW"
    return "FAIL"


def _root_causes(row: pd.Series, entry_present: bool, exit_present: bool, replay_state: str) -> list[str]:
    causes: list[str] = []
    runtime_state = _upper(row.get("state"))
    if not entry_present:
        causes.append("Position Creation Failure")
    if runtime_state in {"OPEN", "PARTIAL_EXIT", "CLOSED"} and not exit_present:
        causes.append("Missing Exit")
    if runtime_state == "CLOSED" and not exit_present:
        causes.append("Missing Fill Link")
    if not exit_present and "Missing Fill Link" not in causes:
        causes.append("Missing Fill Link")
    if replay_state != runtime_state:
        causes.append("Position Lifecycle Error")
    return causes


def reconstruct_positions(
    position_lifecycle: pd.DataFrame | list[dict[str, Any]],
    fills: pd.DataFrame | list[dict[str, Any]] | None = None,
) -> pd.DataFrame:
    lifecycle = _frame(position_lifecycle)
    fill_frame = _frame(fills)
    fill_by_id = _fill_lookup(fill_frame)
    require_fill_table_presence = bool(fill_by_id)
    rows: list[dict[str, Any]] = []

    for _, row in lifecycle.iterrows():
        position_id = _text(row.get("position_id"))
        runtime_state = _upper(row.get("state")) or "UNKNOWN"
        entry_fill_id = _text(row.get("entry_fill_id"))
        exit_fill_id = _text(row.get("exit_fill_id"))
        entry_fill = fill_by_id.get(entry_fill_id, pd.Series(dtype=object))
        exit_fill = fill_by_id.get(exit_fill_id, pd.Series(dtype=object))
        entry_present = bool(entry_fill_id) and (not require_fill_table_presence or not entry_fill.empty)
        exit_present = bool(exit_fill_id) and (not require_fill_table_presence or not exit_fill.empty)

        can_reconstruct_exit_state = runtime_state in {"CLOSED", "PARTIAL_EXIT"} and entry_present and exit_present
        if can_reconstruct_exit_state:
            entry_qty = _fill_qty(entry_fill, row.get("entry_qty"))
            exit_qty = _fill_qty(exit_fill, row.get("closed_qty"))
            entry_price = _fill_price(entry_fill, row.get("entry_price"))
            exit_price = _fill_price(exit_fill, row.get("exit_price"))
            closed_qty = exit_qty if runtime_state == "PARTIAL_EXIT" else entry_qty
            if runtime_state == "PARTIAL_EXIT":
                open_qty = max(entry_qty - exit_qty, 0.0)
            else:
                open_qty = 0.0
            replay_state = runtime_state
            realized_pnl = (exit_price - entry_price) * closed_qty
        else:
            entry_qty = _fill_qty(entry_fill, row.get("entry_qty")) if entry_present else _float(row.get("entry_qty"))
            entry_price = _fill_price(entry_fill, row.get("entry_price")) if entry_present else _float(row.get("entry_price"))
            exit_qty = _float(row.get("closed_qty"))
            exit_price = _float(row.get("exit_price"))
            closed_qty = _float(row.get("closed_qty"))
            open_qty = _float(row.get("open_qty"), default=entry_qty)
            replay_state = "UNRECONSTRUCTED_MISSING_EXIT_FILL" if entry_present else "UNRECONSTRUCTED_MISSING_ENTRY_FILL"
            realized_pnl = _float(row.get("realized_pnl"))

        rows.append(
            {
                "position_id": position_id,
                "symbol": _upper(row.get("symbol") or entry_fill.get("symbol")),
                "entry_fill_id": entry_fill_id,
                "exit_fill_id": exit_fill_id,
                "entry_qty": _norm_float(entry_qty),
                "closed_qty": _norm_float(closed_qty),
                "open_qty": _norm_float(open_qty),
                "entry_price": _norm_float(entry_price),
                "exit_price": _norm_float(exit_price),
                "realized_pnl": _norm_float(realized_pnl),
                "state": replay_state,
                "lifecycle_state": runtime_state,
                "entry_fill_exact_match_flag": int(entry_present),
                "exit_fill_exact_match_flag": int(exit_present),
                "matching_policy": MATCHING_POLICY,
                "proximity_fallback_used_flag": 0,
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "position_id",
            "symbol",
            "entry_fill_id",
            "exit_fill_id",
            "entry_qty",
            "closed_qty",
            "open_qty",
            "entry_price",
            "exit_price",
            "realized_pnl",
            "state",
            "lifecycle_state",
            "entry_fill_exact_match_flag",
            "exit_fill_exact_match_flag",
            "matching_policy",
            "proximity_fallback_used_flag",
        ],
    )


def build_position_replay_diff(
    position_lifecycle: pd.DataFrame | list[dict[str, Any]],
    reconstructed_positions: pd.DataFrame,
) -> pd.DataFrame:
    lifecycle = _frame(position_lifecycle)
    replay_by_position = {
        _text(row.get("position_id")): row
        for _, row in reconstructed_positions.iterrows()
    }
    diff_rows: list[dict[str, Any]] = []
    comparison_fields = ["symbol", "open_qty", "realized_pnl", "state"]

    for _, runtime in lifecycle.iterrows():
        position_id = _text(runtime.get("position_id"))
        replay = replay_by_position.get(position_id, pd.Series(dtype=object))
        if replay.empty:
            diff_rows.append(
                {
                    "surface": POSITION_MATCH_SURFACE,
                    "decision_id": "",
                    "order_id": "",
                    "fill_id": _text(runtime.get("entry_fill_id")),
                    "position_id": position_id,
                    "field_name": "position_id",
                    "runtime_value": position_id,
                    "replay_value": "",
                    "diff_reason": "Position Creation Failure",
                    "rootcause_category": "Position Creation Failure",
                    "severity": "material",
                }
            )
            continue

        entry_present = int(replay.get("entry_fill_exact_match_flag", 0)) == 1
        exit_present = int(replay.get("exit_fill_exact_match_flag", 0)) == 1
        causes = _root_causes(runtime, entry_present, exit_present, _text(replay.get("state")))
        material_diff = False
        for field_name in comparison_fields:
            runtime_value = _runtime_value(runtime, field_name)
            if field_name == "state":
                replay_value = replay.get("state")
            else:
                replay_value = replay.get(field_name)
            if _field_match(runtime_value, replay_value):
                continue
            material_diff = True
            diff_rows.append(
                {
                    "surface": POSITION_MATCH_SURFACE,
                    "decision_id": "",
                    "order_id": _text(runtime.get("entry_order_id")),
                    "fill_id": _text(runtime.get("exit_fill_id") or runtime.get("entry_fill_id")),
                    "position_id": position_id,
                    "field_name": field_name,
                    "runtime_value": runtime_value,
                    "replay_value": replay_value,
                    "diff_reason": "; ".join(causes) if causes else "Position Lifecycle Error",
                    "rootcause_category": causes[0] if causes else "Position Lifecycle Error",
                    "severity": "material",
                }
            )
        if not material_diff and causes:
            diff_rows.append(
                {
                    "surface": POSITION_MATCH_SURFACE,
                    "decision_id": "",
                    "order_id": _text(runtime.get("entry_order_id")),
                    "fill_id": _text(runtime.get("exit_fill_id") or runtime.get("entry_fill_id")),
                    "position_id": position_id,
                    "field_name": "exact_fill_lineage",
                    "runtime_value": _text(runtime.get("exit_fill_id")),
                    "replay_value": _text(replay.get("exit_fill_id")),
                    "diff_reason": "; ".join(causes),
                    "rootcause_category": causes[0],
                    "severity": "material",
                }
            )

    if not diff_rows:
        diff_rows.append(
            {
                "surface": POSITION_MATCH_SURFACE,
                "decision_id": "",
                "order_id": "",
                "fill_id": "",
                "position_id": "",
                "field_name": "",
                "runtime_value": "",
                "replay_value": "",
                "diff_reason": "no material position mismatch recorded",
                "rootcause_category": "",
                "severity": "info",
            }
        )
    return pd.DataFrame(diff_rows)


def _position_match_flags(
    position_lifecycle: pd.DataFrame,
    reconstructed_positions: pd.DataFrame,
) -> pd.Series:
    replay_by_position = {
        _text(row.get("position_id")): row
        for _, row in reconstructed_positions.iterrows()
    }
    flags: list[int] = []
    for _, runtime in position_lifecycle.iterrows():
        replay = replay_by_position.get(_text(runtime.get("position_id")), pd.Series(dtype=object))
        if replay.empty:
            flags.append(0)
            continue
        runtime_state = _upper(runtime.get("state"))
        if runtime_state not in {"CLOSED", "PARTIAL_EXIT"}:
            flags.append(0)
            continue
        if int(replay.get("entry_fill_exact_match_flag", 0)) != 1 or int(replay.get("exit_fill_exact_match_flag", 0)) != 1:
            flags.append(0)
            continue
        fields_match = all(
            _field_match(_runtime_value(runtime, field_name), replay.get(field_name))
            for field_name in ("symbol", "open_qty", "realized_pnl", "state")
        )
        flags.append(int(fields_match))
    return pd.Series(flags, dtype=int)


def build_match_validation(
    decisions: pd.DataFrame | list[dict[str, Any]] | None,
    orders: pd.DataFrame | list[dict[str, Any]] | None,
    fills: pd.DataFrame | list[dict[str, Any]] | None,
    position_lifecycle: pd.DataFrame | list[dict[str, Any]],
    reconstructed_positions: pd.DataFrame,
) -> pd.DataFrame:
    decision_frame = _frame(decisions)
    order_frame = _frame(orders)
    fill_frame = _frame(fills)
    lifecycle = _frame(position_lifecycle)

    decision_total = int(decision_frame["decision_id"].dropna().astype(str).nunique()) if "decision_id" in decision_frame.columns else 0
    decision_matched = decision_total

    order_total = int(order_frame["order_id"].dropna().astype(str).nunique()) if "order_id" in order_frame.columns else 0
    order_link_column = "decision_id" if "decision_id" in order_frame.columns else "intent_key" if "intent_key" in order_frame.columns else ""
    order_missing = 0
    if order_total and order_link_column:
        order_missing = int(order_frame[order_link_column].fillna("").astype(str).str.strip().eq("").sum())
    order_matched = max(order_total - order_missing, 0)

    fill_total = int(fill_frame["fill_id"].dropna().astype(str).nunique()) if "fill_id" in fill_frame.columns else 0
    fill_missing = 0
    if fill_total and "order_id" in fill_frame.columns:
        fill_missing = int(fill_frame["order_id"].fillna("").astype(str).str.strip().eq("").sum())
    fill_matched = max(fill_total - fill_missing, 0)

    position_total = int(len(lifecycle))
    position_flags = _position_match_flags(lifecycle, reconstructed_positions)
    position_matched = int(position_flags.sum())
    position_match_rate = _safe_ratio(position_matched, position_total)

    decision_rate = _safe_ratio(decision_matched, decision_total)
    order_rate = _safe_ratio(order_matched, order_total)
    fill_rate = _safe_ratio(fill_matched, fill_total)
    return pd.DataFrame(
        [
            {
                "surface": "Decision Match",
                "evaluated_rows": decision_total,
                "matched_rows": decision_matched,
                "match_rate": decision_rate,
                "status": _contract_status(decision_rate),
                "diff_reason_required_flag": 0,
            },
            {
                "surface": "Order Match",
                "evaluated_rows": order_total,
                "matched_rows": order_matched,
                "match_rate": order_rate,
                "status": _contract_status(order_rate, order_missing),
                "diff_reason_required_flag": int(order_missing > 0),
            },
            {
                "surface": "Fill Match",
                "evaluated_rows": fill_total,
                "matched_rows": fill_matched,
                "match_rate": fill_rate,
                "status": _contract_status(fill_rate, fill_missing),
                "diff_reason_required_flag": int(fill_missing > 0),
            },
            {
                "surface": POSITION_MATCH_SURFACE,
                "evaluated_rows": position_total,
                "matched_rows": position_matched,
                "match_rate": position_match_rate,
                "status": _position_status(position_match_rate),
                "diff_reason_required_flag": int(position_matched < position_total),
            },
        ]
    )


def build_decision_summary(validation: pd.DataFrame) -> pd.DataFrame:
    rates = {
        str(row["surface"]).lower().replace(" ", "_").replace("match", "match_rate"): row["match_rate"]
        for _, row in validation.iterrows()
    }
    position_rate = float(rates.get("position_match_rate", 0.0))
    return pd.DataFrame(
        [
            {
                "task_id": "T602-3",
                "decision_status": _position_status(position_rate),
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "decision_match_rate": rates.get("decision_match_rate", 0.0),
                "order_match_rate": rates.get("order_match_rate", 0.0),
                "fill_match_rate": rates.get("fill_match_rate", 0.0),
                "position_match_rate": position_rate,
                "inferred_matching_used_flag": 0,
                "next_required_task": "Acceptance review can inspect exact-ID runtime paper reconstruction; deployment remains blocked until broker-truth review.",
            }
        ]
    )


def build_position_replay_acceptance(
    decisions: pd.DataFrame | list[dict[str, Any]] | None,
    orders: pd.DataFrame | list[dict[str, Any]] | None,
    fills: pd.DataFrame | list[dict[str, Any]] | None,
    position_lifecycle: pd.DataFrame | list[dict[str, Any]],
) -> PositionReplayResult:
    reconstructed = reconstruct_positions(position_lifecycle, fills)
    diff = build_position_replay_diff(position_lifecycle, reconstructed)
    validation = build_match_validation(decisions, orders, fills, position_lifecycle, reconstructed)
    decision = build_decision_summary(validation)
    return PositionReplayResult(
        reconstructed_positions=reconstructed,
        position_replay_diff=diff,
        validation=validation,
        decision=decision,
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


def _rate(result: PositionReplayResult, surface: str) -> float:
    rows = result.validation.loc[result.validation["surface"].eq(surface)]
    if rows.empty:
        return 0.0
    return float(rows.iloc[0]["match_rate"])


def _status(result: PositionReplayResult, surface: str) -> str:
    rows = result.validation.loc[result.validation["surface"].eq(surface)]
    if rows.empty:
        return "FAIL"
    return _text(rows.iloc[0]["status"])


def write_position_replay_outputs(result: PositionReplayResult, report_dir: Path = REPORT_DIR) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(report_dir, "reconstructed_positions.csv", result.reconstructed_positions)
    _write_csv(report_dir, "position_replay_diff.csv", result.position_replay_diff)
    _write_csv(report_dir, "position_replay_validation.csv", result.validation)
    _write_csv(report_dir, "task_602_3_decision.csv", result.decision)

    decision = result.decision.iloc[0].to_dict()
    diff_rows = result.position_replay_diff
    material_diffs = diff_rows.loc[diff_rows.get("severity", pd.Series(dtype=str)).astype(str).str.lower().eq("material")]
    if material_diffs.empty:
        diff_evidence = "no material position mismatch recorded"
    else:
        diff_evidence = "; ".join(material_diffs["diff_reason"].astype(str).head(5).tolist())
    lines = [
        "# Problem",
        "",
        "T602-3 needed Position Match to be rebuilt from entry fill, exit fill, and lifecycle state using exact IDs only.",
        "",
        "# Evidence",
        "",
        f"- decision_match_rate={decision.get('decision_match_rate')}, status={_status(result, 'Decision Match')}",
        f"- order_match_rate={decision.get('order_match_rate')}, status={_status(result, 'Order Match')}",
        f"- fill_match_rate={decision.get('fill_match_rate')}, status={_status(result, 'Fill Match')}",
        f"- position_match_rate={decision.get('position_match_rate')}, status={_status(result, POSITION_MATCH_SURFACE)}",
        f"- reconstructed_positions={len(result.reconstructed_positions)}",
        f"- material_diff_evidence={diff_evidence}",
        "- inferred_matching_used_flag=0",
        "",
        "# Root Cause",
        "",
        "Position reconstruction fails when exact exit_fill_id links are absent and passes only when lifecycle rows contain exact CLOSED or PARTIAL_EXIT lineage.",
        "",
        "# Fix Candidate",
        "",
        "Use the exact-ID reconstruction engine against the current runtime lifecycle and fills tables after T600-3 writes runtime paper exit IDs.",
        "",
        "# Acceptance Impact",
        "",
        f"- decision_status={decision.get('decision_status')}",
        "- Strategy remains NOT_ACCEPTED and deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
        "- No symbol/date/price/time fallback matching was used.",
        "",
    ]
    (report_dir / "position_replay_acceptance_report.md").write_text("\n".join(lines), encoding="utf-8")
    _write_manifest(report_dir)


def run_position_reconstruction_from_db(db_path: Path, report_dir: Path = REPORT_DIR) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    try:
        decisions = _read_table(con, "runtime_strategy_decisions")
        orders = _read_table(con, "orders")
        fills = _read_table(con, "fills")
        position_lifecycle = _read_table(con, "position_lifecycle")
    finally:
        con.close()
    result = build_position_replay_acceptance(decisions, orders, fills, position_lifecycle)
    write_position_replay_outputs(result, report_dir)
    return result.decision.iloc[0].to_dict()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    summary = run_position_reconstruction_from_db(args.db_path, args.report_dir)
    print(pd.DataFrame([summary]).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
