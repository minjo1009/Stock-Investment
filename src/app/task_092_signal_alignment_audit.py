from __future__ import annotations

import argparse
import glob
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from backtest import engine_full
from backtest.data_loader import DEFAULT_BASE_DIR, load_daily_bars
from portfolio.allocator import AllocationConfig, allocate_equal_weight
from sector.sector_model import map_symbol_to_sector
from strategy.conditions import condition_snapshot, prepare_condition_frame
from universe.ranking import rank_universe
from universe.universe_selector import build_universe_snapshot, filter_universe_snapshot


def _load_qualifying_evidence_run(runs_glob: str) -> tuple[Path, dict[str, Any]]:
    for path in sorted(glob.glob(runs_glob), reverse=True):
        p = Path(path)
        payload = json.loads(p.read_text(encoding="utf-8"))
        if (
            int(payload.get("signal_generated_run", 0)) == 1
            and float(payload.get("data_fresh_ratio", 0.0)) == 1.0
            and float(payload.get("missing_bar_ratio", 1.0)) == 0.0
        ):
            return p, payload
    raise RuntimeError("No qualifying task_087 evidence run found")


def _load_runtime_snapshot(db_path: str, cutoff_ts: str) -> tuple[str, list[dict[str, Any]]]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        latest = con.execute(
            "SELECT MAX(created_at) AS c FROM indicator_snapshots WHERE created_at <= ?",
            (cutoff_ts,),
        ).fetchone()
        snapshot_ts = str(latest["c"] if latest else "" or "")
        if not snapshot_ts:
            latest2 = con.execute("SELECT MAX(created_at) AS c FROM indicator_snapshots").fetchone()
            snapshot_ts = str(latest2["c"] if latest2 else "" or "")
        if not snapshot_ts:
            raise RuntimeError("No indicator snapshots found")

        rows = con.execute(
            """
            SELECT symbol, bar_end_ts, close, ma20, ma50, ma200, breakout_high_20,
                   breakout_condition, ma_condition, entry_allowed, data_fresh,
                   action, side, reason, score, candidate_rank,
                   COALESCE(selected_for_portfolio, 0) AS selected_for_portfolio
            FROM indicator_snapshots
            WHERE created_at = ?
            ORDER BY candidate_rank ASC, symbol ASC
            """,
            (snapshot_ts,),
        ).fetchall()
    finally:
        con.close()
    return snapshot_ts, [dict(r) for r in rows]


def _backtest_reconstruct(runtime_symbols: list[str], cutoff_ts: str, max_positions: int = 3) -> dict[str, Any]:
    cutoff = pd.Timestamp(cutoff_ts)
    frames: dict[str, pd.DataFrame] = {}
    cond_frames: dict[str, pd.DataFrame] = {}
    eval_rows: list[dict[str, Any]] = []

    for symbol in runtime_symbols:
        frame = load_daily_bars(symbol, base_dir=DEFAULT_BASE_DIR)
        frame = frame[frame["timestamp"] <= cutoff].copy()
        if frame.empty:
            continue
        frames[symbol] = frame
        cond = prepare_condition_frame(frame)
        if cond.empty:
            continue
        cond_frames[symbol] = cond
        i = len(cond) - 1
        snap = condition_snapshot(cond, i)
        row = cond.iloc[i]
        eval_rows.append(
            {
                "symbol": symbol,
                "close": float(row.get("close")),
                "ma20": float(row.get("ma20")) if pd.notna(row.get("ma20")) else None,
                "ma50": float(row.get("ma50")) if pd.notna(row.get("ma50")) else None,
                "ma200": float(row.get("ma200")) if pd.notna(row.get("ma200")) else None,
                "breakout_high_20": float(row.get("breakout_high_20")) if pd.notna(row.get("breakout_high_20")) else None,
                "breakout_condition": bool(snap.get("breakout_condition") is True),
                "ma_condition": bool(snap.get("ma_condition") is True),
                "sector": map_symbol_to_sector(symbol),
            }
        )

    snapshot = build_universe_snapshot(frames)
    filtered = filter_universe_snapshot(snapshot)
    ranked = rank_universe(filtered)
    selected_symbols = ranked["symbol"].head(max(1, int(max_positions))).tolist() if not ranked.empty else []
    if not selected_symbols:
        selected_symbols = sorted(frames.keys())[: max(1, int(max_positions))]

    allocations = allocate_equal_weight(
        selected_symbols,
        config=AllocationConfig(max_positions=max_positions, max_exposure_per_symbol=1.0),
    )
    alloc_map = {str(item["symbol"]): float(item["allocation_pct"]) for item in allocations}

    signal_symbols: list[str] = []
    for symbol in selected_symbols:
        cond = cond_frames.get(symbol)
        if cond is None or cond.empty:
            continue
        i = len(cond) - 1
        equity = 100_000.0 * float(alloc_map.get(symbol, 1.0))
        if engine_full._entry_signal(i=i, frame=cond, equity=equity) is not None:
            signal_symbols.append(symbol)

    return {
        "rows": eval_rows,
        "selected_symbols": selected_symbols,
        "selected_sectors": sorted({map_symbol_to_sector(s) for s in selected_symbols}),
        "signal_type": "BUY" if signal_symbols else "NONE",
        "signal_symbol": signal_symbols[0] if signal_symbols else None,
    }


def _compare(runtime_rows: list[dict[str, Any]], backtest_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    table: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    rt_by = {str(r["symbol"]): r for r in runtime_rows}
    bt_by = {str(r["symbol"]): r for r in backtest_rows}

    def add(layer: str, field: str, rv: Any, bv: Any, status: str, cause: str = "", impact: str = "") -> None:
        table.append({"Layer": layer, "Field": field, "Runtime": rv, "Backtest": bv, "Status": status})
        if status != "MATCH":
            mismatches.append(
                {
                    "layer": layer,
                    "field": field,
                    "runtime": rv,
                    "backtest": bv,
                    "severity": "minor" if status == "MINOR_DIFF" else "major",
                    "cause": cause,
                    "impact": impact,
                }
            )

    for symbol in sorted(set(rt_by.keys()) & set(bt_by.keys())):
        rr = rt_by[symbol]
        bb = bt_by[symbol]
        for feature in ("close", "ma20", "ma50", "ma200", "breakout_high_20"):
            rv = rr.get(feature)
            bv = bb.get(feature)
            if rv is None or bv is None:
                add("Data Layer", f"{symbol}.{feature}", rv, bv, "MAJOR_DIFF", "missing feature", "incomplete signal context")
                continue
            rel = abs(float(rv) - float(bv)) / max(abs(float(bv)), 1e-9)
            if rel < 1e-6:
                add("Data Layer", f"{symbol}.{feature}", rv, bv, "MATCH")
            elif rel < 1e-3:
                add("Data Layer", f"{symbol}.{feature}", rv, bv, "MINOR_DIFF", "float/rounding", "no threshold impact expected")
            else:
                add(
                    "Data Layer",
                    f"{symbol}.{feature}",
                    rv,
                    bv,
                    "MAJOR_DIFF",
                    "time window/source mismatch",
                    "indicator/condition divergence",
                )
        for cond in ("breakout_condition", "ma_condition"):
            rv = bool(int(rr.get(cond) or 0))
            bv = bool(bb.get(cond) is True)
            add(
                "Feature Layer",
                f"{symbol}.{cond}",
                rv,
                bv,
                "MATCH" if rv == bv else "MAJOR_DIFF",
                "condition mismatch" if rv != bv else "",
                "entry trigger diverges" if rv != bv else "",
            )

    return table, mismatches


def _to_markdown(out: dict[str, Any]) -> str:
    rows = out["comparison_rows"]
    mismatches = out["mismatches"]
    lines: list[str] = []
    lines.append("# Task T092 - Signal Alignment Audit")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- total comparisons: {out['total_cases']}")
    lines.append(f"- match / minor / major: {out['match_count']} / {out['minor_diff_count']} / {out['major_diff_count']}")
    lines.append(f"- final status: {out['status']}")
    lines.append("")
    lines.append("## 2. Test Snapshot")
    lines.append(f"- evidence run: {out['runtime_snapshot']['evidence_run']}")
    lines.append(f"- runtime snapshot timestamp: {out['runtime_snapshot']['snapshot_created_at']}")
    lines.append(f"- comparison cutoff timestamp: {out['runtime_snapshot']['evidence_started_at']}")
    lines.append(f"- symbols: {', '.join(out['runtime_snapshot']['symbols'])}")
    lines.append("")
    lines.append("## 3. Runtime Signal")
    lines.append(f"- selected symbols: {out['runtime_snapshot']['selected_symbols']}")
    lines.append(f"- selected sectors: {out['runtime_snapshot']['selected_sectors']}")
    lines.append(f"- signal decision: {out['runtime_snapshot']['signal']['type']} ({out['runtime_snapshot']['signal']['symbol']})")
    lines.append("")
    lines.append("## 4. Backtest Signal")
    lines.append(f"- selected symbols: {out['backtest_snapshot']['selected_symbols']}")
    lines.append(f"- selected sectors: {out['backtest_snapshot']['selected_sectors']}")
    lines.append(f"- signal decision: {out['backtest_snapshot']['signal']['type']} ({out['backtest_snapshot']['signal']['symbol']})")
    lines.append("")
    lines.append("## 5. Detailed Comparison")
    lines.append("")
    lines.append("| Layer | Field | Runtime | Backtest | Status |")
    lines.append("|------|------|--------|----------|--------|")
    for r in rows:
        lines.append(f"| {r['Layer']} | {r['Field']} | {r['Runtime']} | {r['Backtest']} | {r['Status']} |")
    lines.append("")
    lines.append("## 6. Mismatch Analysis")
    if mismatches:
        for idx, m in enumerate(mismatches, start=1):
            lines.append(f"{idx}. `{m['layer']} / {m['field']}`")
            lines.append(f"   - cause: {m['cause']}")
            lines.append(f"   - impact: {m['impact']}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## 7. Root Cause Categories")
    roots = out.get("root_cause_categories", [])
    if roots:
        for root in roots:
            lines.append(f"- {root}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## 8. Decision")
    lines.append(f"- {out['status']}")
    lines.append("")
    lines.append("## 9. Final Answer")
    lines.append(f"- Is runtime executing the same strategy as backtest? {out['answer']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Task T092: runtime/backtest signal alignment audit")
    parser.add_argument("--db-path", type=str, default=os.environ.get("TRADING_DB_PATH", "trading.db"))
    parser.add_argument("--evidence-glob", type=str, default="docs/reports/task_087/runs/*.json")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_092/task_092_signal_alignment.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_092/task_092_signal_alignment.md")
    parser.add_argument("--max-positions", type=int, default=3)
    args = parser.parse_args()

    evidence_path, evidence = _load_qualifying_evidence_run(args.evidence_glob)
    snapshot_ts, runtime_rows = _load_runtime_snapshot(args.db_path, evidence["started_at"])
    runtime_symbols = [str(r["symbol"]) for r in runtime_rows]

    runtime_selected_symbols = [str(r["symbol"]) for r in runtime_rows if int(r.get("selected_for_portfolio", 0)) == 1]
    runtime_selected_sectors = sorted({map_symbol_to_sector(s) for s in runtime_selected_symbols})
    runtime_signal_rows = [
        r
        for r in runtime_rows
        if int(r.get("entry_allowed", 0)) == 1
        and int(r.get("data_fresh", 0)) == 1
        and int(r.get("selected_for_portfolio", 0)) == 1
    ]
    runtime_signal_rows.sort(key=lambda x: (float(x.get("score") or 0.0), str(x.get("symbol"))), reverse=True)
    runtime_signal_type = "BUY" if runtime_signal_rows else "NONE"
    runtime_signal_symbol = str(runtime_signal_rows[0]["symbol"]) if runtime_signal_rows else None

    backtest = _backtest_reconstruct(runtime_symbols, evidence["started_at"], max_positions=max(1, int(args.max_positions)))
    table, mismatches = _compare(runtime_rows, backtest["rows"])

    def add_layer_compare(layer: str, field: str, rv: Any, bv: Any, major_cause: str) -> None:
        status = "MATCH" if rv == bv else "MAJOR_DIFF"
        row = {"Layer": layer, "Field": field, "Runtime": rv, "Backtest": bv, "Status": status}
        table.append(row)
        if status != "MATCH":
            mismatches.append(
                {
                    "layer": layer,
                    "field": field,
                    "runtime": rv,
                    "backtest": bv,
                    "severity": "major",
                    "cause": major_cause,
                    "impact": "signal/selection mismatch",
                }
            )

    add_layer_compare("Selection Layer", "selected_symbols", runtime_selected_symbols, backtest["selected_symbols"], "selection inconsistency")
    add_layer_compare("Selection Layer", "selected_sectors", runtime_selected_sectors, backtest["selected_sectors"], "selection inconsistency")
    add_layer_compare("Signal Layer", "signal_type", runtime_signal_type, backtest["signal_type"], "signal mismatch")
    add_layer_compare("Signal Layer", "signal_symbol", runtime_signal_symbol, backtest["signal_symbol"], "signal mismatch")

    match_count = sum(1 for r in table if r["Status"] == "MATCH")
    minor_count = sum(1 for r in table if r["Status"] == "MINOR_DIFF")
    major_count = sum(1 for r in table if r["Status"] == "MAJOR_DIFF")
    status = "FAIL" if major_count > 0 else ("WARNING" if minor_count > 0 else "PASS")
    answer = "NO" if major_count > 0 else "YES"

    out = {
        "status": status,
        "answer": answer,
        "total_cases": len(table),
        "match_count": match_count,
        "minor_diff_count": minor_count,
        "major_diff_count": major_count,
        "runtime_snapshot": {
            "evidence_run": evidence_path.name,
            "evidence_started_at": evidence["started_at"],
            "snapshot_created_at": snapshot_ts,
            "symbols": runtime_symbols,
            "selected_symbols": runtime_selected_symbols,
            "selected_sectors": runtime_selected_sectors,
            "signal": {"type": runtime_signal_type, "symbol": runtime_signal_symbol},
        },
        "backtest_snapshot": {
            "data_cutoff": str(evidence["started_at"]),
            "symbols": sorted({r["symbol"] for r in backtest["rows"]}),
            "selected_symbols": backtest["selected_symbols"],
            "selected_sectors": backtest["selected_sectors"],
            "signal": {"type": backtest["signal_type"], "symbol": backtest["signal_symbol"]},
        },
        "mismatches": mismatches,
        "comparison_rows": table,
        "root_cause_categories": sorted({m.get("cause", "") for m in mismatches if m.get("cause")}),
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(_to_markdown(out), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={status}")
    print(f"answer={answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
