from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from src.risk.build_entry_risk_snapshot import (
    MATCHING_POLICY,
    REAL_CAPITAL_STATUS,
    REPORT_DIR,
    SNAPSHOT_TABLE,
    _read_table,
    _text,
)


VALIDATION_COLUMNS = [
    "task_id",
    "acceptance_status",
    "decision_status",
    "snapshot_coverage",
    "stop_price_populated",
    "take_profit_price_populated",
    "position_count",
    "snapshot_count",
    "exact_snapshot_count",
    "stop_price_populated_count",
    "take_profit_price_populated_count",
    "source_block_count",
    "atr_source_block_count",
    "stop_tp_source_block_count",
    "matching_policy",
    "real_capital_status",
]
DETAIL_COLUMNS = [
    "position_id",
    "symbol",
    "entry_time",
    "exact_snapshot_flag",
    "stop_price_populated_flag",
    "take_profit_price_populated_flag",
    "atr_source_status",
    "stop_tp_source_status",
    "source_block_reason",
]
TASK_ID = "T603-6"


def _safe_ratio(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(float(part) / float(total), 6)


def _position_scope(position_lifecycle: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(position_lifecycle).copy()
    if frame.empty or "position_id" not in frame.columns:
        return pd.DataFrame(columns=["position_id", "symbol", "entry_time"])
    frame["position_id"] = frame["position_id"].map(_text)
    frame = frame.loc[frame["position_id"].ne("")].copy()
    for column in ("symbol", "entry_time"):
        if column not in frame.columns:
            frame[column] = ""
    return frame[["position_id", "symbol", "entry_time"]].drop_duplicates("position_id").reset_index(drop=True)


def _snapshot_scope(entry_risk_snapshot: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(entry_risk_snapshot).copy()
    if frame.empty or "position_id" not in frame.columns:
        return pd.DataFrame(columns=["position_id"])
    frame["position_id"] = frame["position_id"].map(_text)
    return frame.loc[frame["position_id"].ne("")].reset_index(drop=True)


def validate_entry_risk_snapshot(
    position_lifecycle: pd.DataFrame | list[dict[str, Any]],
    entry_risk_snapshot: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, pd.DataFrame]:
    positions = _position_scope(position_lifecycle)
    snapshots = _snapshot_scope(entry_risk_snapshot)
    position_ids = set(positions["position_id"].tolist()) if not positions.empty else set()
    matched_snapshots = snapshots.loc[snapshots["position_id"].isin(position_ids)].copy() if not snapshots.empty else snapshots.copy()
    exact_snapshot_ids = set(matched_snapshots["position_id"].tolist()) if not matched_snapshots.empty else set()

    stop_ids = _populated_position_ids(matched_snapshots, "stop_price")
    tp_ids = _populated_position_ids(matched_snapshots, "take_profit_price")
    position_count = int(len(position_ids))
    exact_snapshot_count = int(len(exact_snapshot_ids))
    stop_count = int(len(stop_ids))
    tp_count = int(len(tp_ids))
    snapshot_coverage = _safe_ratio(exact_snapshot_count, position_count)
    stop_price_populated = _safe_ratio(stop_count, position_count)
    take_profit_price_populated = _safe_ratio(tp_count, position_count)
    source_block_count = _source_block_count(matched_snapshots)
    atr_source_block_count = _atr_source_block_count(matched_snapshots)
    stop_tp_source_block_count = _stop_tp_source_block_count(matched_snapshots)
    acceptance_status, decision_status = _decision_status(
        position_count=position_count,
        snapshot_coverage=snapshot_coverage,
        stop_price_populated=stop_price_populated,
        take_profit_price_populated=take_profit_price_populated,
        atr_source_block_count=atr_source_block_count,
        stop_tp_source_block_count=stop_tp_source_block_count,
    )
    summary = pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "acceptance_status": acceptance_status,
                "decision_status": decision_status,
                "snapshot_coverage": snapshot_coverage,
                "stop_price_populated": stop_price_populated,
                "take_profit_price_populated": take_profit_price_populated,
                "position_count": position_count,
                "snapshot_count": int(len(snapshots)),
                "exact_snapshot_count": exact_snapshot_count,
                "stop_price_populated_count": stop_count,
                "take_profit_price_populated_count": tp_count,
                "source_block_count": source_block_count,
                "atr_source_block_count": atr_source_block_count,
                "stop_tp_source_block_count": stop_tp_source_block_count,
                "matching_policy": MATCHING_POLICY,
                "real_capital_status": REAL_CAPITAL_STATUS,
            }
        ],
        columns=VALIDATION_COLUMNS,
    )
    detail = _validation_detail(positions, matched_snapshots, stop_ids, tp_ids)
    return {"entry_risk_snapshot_validation": summary, "entry_risk_snapshot_detail": detail}


def _populated_position_ids(snapshots: pd.DataFrame, column: str) -> set[str]:
    if snapshots.empty or column not in snapshots.columns:
        return set()
    values = pd.to_numeric(snapshots[column], errors="coerce")
    return set(snapshots.loc[values.notna(), "position_id"].astype(str).tolist())


def _source_block_count(snapshots: pd.DataFrame) -> int:
    if snapshots.empty or "source_block" not in snapshots.columns:
        return 0
    return int(pd.to_numeric(snapshots["source_block"], errors="coerce").fillna(0).astype(int).sum())


def _atr_source_block_count(snapshots: pd.DataFrame) -> int:
    if snapshots.empty or "atr_source_status" not in snapshots.columns:
        return 0
    statuses = snapshots["atr_source_status"].fillna("").astype(str)
    return int(statuses.ne("OK").sum())


def _stop_tp_source_block_count(snapshots: pd.DataFrame) -> int:
    if snapshots.empty or "stop_tp_source_status" not in snapshots.columns:
        return 0
    statuses = snapshots["stop_tp_source_status"].fillna("").astype(str)
    return int(statuses.ne("OK").sum())


def _decision_status(
    *,
    position_count: int,
    snapshot_coverage: float,
    stop_price_populated: float,
    take_profit_price_populated: float,
    atr_source_block_count: int,
    stop_tp_source_block_count: int,
) -> tuple[str, str]:
    if (
        position_count > 0
        and snapshot_coverage >= 1.0
        and stop_price_populated >= 1.0
        and take_profit_price_populated >= 1.0
    ):
        return "PASS", "PASS_ENTRY_RISK_SNAPSHOT_COVERAGE"
    if position_count <= 0:
        return "FAIL", "FAIL_NO_POSITION_LIFECYCLE_SOURCE"
    if snapshot_coverage < 1.0:
        return "FAIL", "FAIL_SNAPSHOT_COVERAGE"
    if (
        (atr_source_block_count > 0 or stop_tp_source_block_count > 0)
        and (stop_price_populated < 1.0 or take_profit_price_populated < 1.0)
    ):
        return "FAIL", "FAIL_STOP_TP_SOURCE_BLOCKED"
    return "FAIL", "FAIL_STOP_TP_COVERAGE"


def _validation_detail(
    positions: pd.DataFrame,
    snapshots: pd.DataFrame,
    stop_ids: set[str],
    tp_ids: set[str],
) -> pd.DataFrame:
    snapshot_by_position: dict[str, pd.Series] = {}
    if not snapshots.empty:
        for _, row in snapshots.iterrows():
            position_id = _text(row.get("position_id"))
            if position_id and position_id not in snapshot_by_position:
                snapshot_by_position[position_id] = row
    rows: list[dict[str, Any]] = []
    for _, position in positions.iterrows():
        position_id = _text(position.get("position_id"))
        snapshot = snapshot_by_position.get(position_id, pd.Series(dtype=object))
        rows.append(
            {
                "position_id": position_id,
                "symbol": _text(position.get("symbol")),
                "entry_time": _text(position.get("entry_time")),
                "exact_snapshot_flag": int(not snapshot.empty),
                "stop_price_populated_flag": int(position_id in stop_ids),
                "take_profit_price_populated_flag": int(position_id in tp_ids),
                "atr_source_status": _text(snapshot.get("atr_source_status")) if not snapshot.empty else "NO_EXACT_SNAPSHOT",
                "stop_tp_source_status": _text(snapshot.get("stop_tp_source_status")) if not snapshot.empty else "NO_EXACT_SNAPSHOT",
                "source_block_reason": _text(snapshot.get("source_block_reason")) if not snapshot.empty else "NO_EXACT_SNAPSHOT",
            }
        )
    return pd.DataFrame(rows, columns=DETAIL_COLUMNS)


def validate_entry_risk_snapshot_from_db(
    db_path: Path | str,
    *,
    report_dir: Path | None = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    con = sqlite3.connect(db_path)
    try:
        position_lifecycle = _read_table(con, "position_lifecycle")
        entry_risk_snapshot = _read_table(con, SNAPSHOT_TABLE)
    finally:
        con.close()
    artifacts = validate_entry_risk_snapshot(position_lifecycle, entry_risk_snapshot)
    if report_dir is not None:
        write_stop_tp_coverage_report(report_dir, artifacts)
    return artifacts


def write_stop_tp_coverage_report(report_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["entry_risk_snapshot_validation"]
    detail = artifacts["entry_risk_snapshot_detail"]
    row = summary.iloc[0].to_dict()
    blocker_lines = _blocker_lines(detail)
    lines = [
        "## Problem",
        "",
        "T603-6 Program B acceptance requires entry risk snapshots to cover exact runtime positions and populate STOP/TP thresholds from ATR14 without source approximation.",
        "The validator must report snapshot_coverage, stop_price_populated, and take_profit_price_populated against `position_lifecycle.position_id` only.",
        "",
        "## Evidence",
        "",
        f"- acceptance_status={row['acceptance_status']}",
        f"- decision_status={row['decision_status']}",
        f"- snapshot_coverage={row['snapshot_coverage']}",
        f"- stop_price_populated={row['stop_price_populated']}",
        f"- take_profit_price_populated={row['take_profit_price_populated']}",
        f"- position_count={row['position_count']}",
        f"- exact_snapshot_count={row['exact_snapshot_count']}",
        f"- source_block_count={row['source_block_count']}",
        f"- atr_source_block_count={row['atr_source_block_count']}",
        f"- stop_tp_source_block_count={row['stop_tp_source_block_count']}",
        f"- matching_policy={MATCHING_POLICY}",
        f"- real_capital_status={REAL_CAPITAL_STATUS}",
        "",
        "## Root Cause",
        "",
        "Coverage can fail only from missing exact position snapshots or from STOP/TP fields left null because ATR14 or entry-price source evidence is blocked.",
        "The validator does not use symbol/date/price/time proximity fallback and does not convert missing labels into negatives.",
        "",
        "## Fix Candidate",
        "",
        "If STOP/TP coverage fails, add real OHLC bars and exact entry-price source evidence before each entry, then rebuild `entry_risk_snapshot`; do not approximate ATR.",
        "If snapshot coverage fails, rebuild from `position_lifecycle` exact position IDs and inspect missing snapshot rows.",
        "",
        "## Acceptance Impact",
        "",
        f"- Current trading DB status: {row['acceptance_status']} ({row['decision_status']})",
        f"- Acceptance metrics: snapshot_coverage={row['snapshot_coverage']}, stop_price_populated={row['stop_price_populated']}, take_profit_price_populated={row['take_profit_price_populated']}",
        f"- Blockers: {'; '.join(blocker_lines) if blocker_lines else 'none'}",
        f"- Real Capital remains {REAL_CAPITAL_STATUS}; this task does not submit orders or change strategy/entry/universe/alpha logic.",
    ]
    (report_dir / "stop_tp_coverage_report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    _write_manifest(report_dir)


def _blocker_lines(detail: pd.DataFrame) -> list[str]:
    if detail.empty:
        return ["NO_POSITION_DETAIL_ROWS"]
    blockers = detail.loc[
        detail["exact_snapshot_flag"].astype(int).eq(0)
        | detail["stop_price_populated_flag"].astype(int).eq(0)
        | detail["take_profit_price_populated_flag"].astype(int).eq(0)
    ].copy()
    if blockers.empty:
        return []
    status_column = "stop_tp_source_status" if "stop_tp_source_status" in blockers.columns else "atr_source_status"
    counts = blockers[status_column].fillna("").astype(str).value_counts().sort_index()
    return [f"{status}={int(count)}" for status, count in counts.items() if status]


def _write_manifest(report_dir: Path) -> None:
    rows: list[dict[str, Any]] = []
    for path in sorted(report_dir.iterdir()):
        if not path.is_file() or path.name == "artifact_manifest.csv":
            continue
        rows.append(
            {
                "relative_path": path.name,
                "artifact_class": "report" if path.suffix.lower() == ".md" else "small_table",
                "row_count": "",
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    pd.DataFrame(rows).to_csv(report_dir / "artifact_manifest.csv", index=False, encoding="utf-8-sig")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = validate_entry_risk_snapshot_from_db(args.db_path, report_dir=args.report_dir)
    print(artifacts["entry_risk_snapshot_validation"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
