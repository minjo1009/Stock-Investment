from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.continuation_lifecycle import build_continuation_lifecycle_diagnostics
from src.backtest.analysis_structural_breakout_shadow_integration_360 import generate_shadow_artifacts
from src.risk.add_relay_diagnostics import build_add_relay_diagnostics


DEFAULT_OUT_DIR = Path("docs/reports/task_363_add_relay_lifecycle")


def _healthy_trace(relay_trace_df: pd.DataFrame) -> pd.DataFrame:
    return relay_trace_df[relay_trace_df["participation_quality_label"].astype(str) == "HEALTHY_EXPANSION"].copy()


def _summary(
    shadow_log: pd.DataFrame,
    healthy_trace_df: pd.DataFrame,
    gate_dropoff_df: pd.DataFrame,
    lifecycle_df: pd.DataFrame,
    lifecycle_summary_df: pd.DataFrame,
) -> pd.DataFrame:
    healthy_total = int(len(healthy_trace_df))
    healthy_lifecycle_count = int(lifecycle_df["has_healthy_expansion"].fillna(False).astype(bool).sum()) if not lifecycle_df.empty else 0
    healthy_pnl_share = 0.0
    baseline_total = float(pd.to_numeric(shadow_log["baseline_realized_R"], errors="coerce").fillna(0.0).sum()) if not shadow_log.empty else 0.0
    if baseline_total != 0.0 and healthy_total:
        healthy_pnl_share = float(pd.to_numeric(healthy_trace_df["baseline_realized_R"], errors="coerce").fillna(0.0).sum()) / baseline_total

    healthy_gate = gate_dropoff_df[gate_dropoff_df["quality_label"].astype(str) == "HEALTHY_EXPANSION"].copy()
    dominant_gate = "none"
    if not healthy_gate.empty:
        ordered = healthy_gate.sort_values(["block_count", "gate_name"], ascending=[False, True]).reset_index(drop=True)
        dominant_gate = str(ordered.loc[0, "gate_name"])
    staged_row = healthy_gate[healthy_gate["gate_name"].astype(str) == "staged_gate"]
    staged_block_rate = float(staged_row["block_count"].iloc[0] / max(staged_row["input_count"].iloc[0], 1)) if not staged_row.empty else 0.0

    old_add = int(pd.to_numeric(lifecycle_df["add_allowed_count_old_shadow"], errors="coerce").fillna(0.0).sum()) if not lifecycle_df.empty else 0
    quality_add = int(pd.to_numeric(lifecycle_df["add_allowed_count_quality_aware"], errors="coerce").fillna(0.0).sum()) if not lifecycle_df.empty else 0
    healthy_add = int(pd.to_numeric(lifecycle_df["add_allowed_count_healthy_aggressive"], errors="coerce").fillna(0.0).sum()) if not lifecycle_df.empty else 0

    multi_row_share = 0.0
    if not lifecycle_df.empty:
        multi_row_share = float((pd.to_numeric(lifecycle_df["row_count"], errors="coerce").fillna(0.0) > 1).mean())

    return pd.DataFrame(
        [
            {
                "healthy_row_count": healthy_total,
                "healthy_lifecycle_count": healthy_lifecycle_count,
                "healthy_baseline_pnl_share": round(healthy_pnl_share, 6),
                "dominant_failing_gate": dominant_gate,
                "healthy_staged_gate_block_rate": round(staged_block_rate, 6),
                "old_shadow_add_count": old_add,
                "quality_aware_add_count": quality_add,
                "healthy_aggressive_add_count": healthy_add,
                "multi_row_lifecycle_share": round(multi_row_share, 6),
            }
        ]
    )


def _answers(summary_df: pd.DataFrame, gate_dropoff_df: pd.DataFrame, lifecycle_df: pd.DataFrame) -> tuple[str, str, str, str, str]:
    row = summary_df.iloc[0]
    q1 = str(row["dominant_failing_gate"])
    q2 = "YES" if int(row["healthy_row_count"]) < 25 or float(row["healthy_baseline_pnl_share"]) < 0.10 else "NO"
    healthy_stage = gate_dropoff_df[
        (gate_dropoff_df["quality_label"].astype(str) == "HEALTHY_EXPANSION")
        & (gate_dropoff_df["gate_name"].astype(str) == "staged_gate")
    ]
    q3 = "YES" if not healthy_stage.empty and int(healthy_stage["block_count"].iloc[0]) > 0 else "NO"
    q4 = "YES" if int(row["healthy_aggressive_add_count"]) > int(row["quality_aware_add_count"]) else "NO"

    healthy_lifecycles = lifecycle_df[lifecycle_df["has_healthy_expansion"].fillna(False).astype(bool)].copy()
    row_proxy_insufficient = (
        not healthy_lifecycles.empty
        and float((pd.to_numeric(healthy_lifecycles["row_count"], errors="coerce").fillna(0.0) > 1).mean()) >= 0.50
        and float(pd.to_numeric(healthy_lifecycles["add_allowed_count_healthy_aggressive"], errors="coerce").fillna(0.0).mean()) <= 1.0
    )
    q5 = "YES" if row_proxy_insufficient else "NO"
    return q1, q2, q3, q4, q5


def _report(
    out_dir: Path,
    summary_df: pd.DataFrame,
    healthy_trace_df: pd.DataFrame,
    gate_dropoff_df: pd.DataFrame,
    blocking_reasons_df: pd.DataFrame,
    lifecycle_df: pd.DataFrame,
    lifecycle_summary_df: pd.DataFrame,
) -> None:
    q1, q2, q3, q4, q5 = _answers(summary_df, gate_dropoff_df, lifecycle_df)
    lines = [
        "# Task 363 - Healthy Continuation Add-Relay & Lifecycle Replay Foundation",
        "",
        "## Core Answers",
        f"1. Where does HEALTHY_EXPANSION add activation fail? {q1}",
        f"2. Is the classifier too conservative? {q2}",
        f"3. Is staged gate blocking too much? {q3}",
        f"4. Is healthy-aggressive policy actually more aggressive after all gates? {q4}",
        f"5. Does lifecycle grouping suggest row-level proxy is insufficient? {q5}",
        "",
        "## Add Relay Summary",
        *(_markdown_table(summary_df)),
        "",
        "## HEALTHY_EXPANSION Relay Trace",
        *(_markdown_table(healthy_trace_df.head(25))),
        "",
        "## Gate Drop-Off Summary",
        *(_markdown_table(gate_dropoff_df)),
        "",
        "## Blocking Reasons",
        *(_markdown_table(blocking_reasons_df.head(25))),
        "",
        "## Lifecycle Quality Summary",
        *(_markdown_table(lifecycle_summary_df)),
    ]
    (out_dir / "task_363_add_relay_lifecycle.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 363: add relay diagnostics and lifecycle replay foundation")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts = generate_shadow_artifacts(enable_shadow_state_engine=True)
    shadow_log = artifacts.shadow_log.copy()
    relay_trace_df, gate_dropoff_df, blocking_reasons_df = build_add_relay_diagnostics(shadow_log)
    healthy_trace_df = _healthy_trace(relay_trace_df)
    lifecycle_df, lifecycle_summary_df = build_continuation_lifecycle_diagnostics(shadow_log)
    summary_df = _summary(shadow_log, healthy_trace_df, gate_dropoff_df, lifecycle_df, lifecycle_summary_df)

    summary_df.to_csv(out_dir / "task_363_add_relay_summary.csv", index=False)
    healthy_trace_df.to_csv(out_dir / "task_363_healthy_expansion_relay_trace.csv", index=False)
    gate_dropoff_df.to_csv(out_dir / "task_363_gate_dropoff_summary.csv", index=False)
    blocking_reasons_df.to_csv(out_dir / "task_363_blocking_reasons.csv", index=False)
    lifecycle_df.to_csv(out_dir / "task_363_lifecycle_diagnostics.csv", index=False)
    lifecycle_summary_df.to_csv(out_dir / "task_363_lifecycle_quality_summary.csv", index=False)
    _report(out_dir, summary_df, healthy_trace_df, gate_dropoff_df, blocking_reasons_df, lifecycle_df, lifecycle_summary_df)


if __name__ == "__main__":
    main()
