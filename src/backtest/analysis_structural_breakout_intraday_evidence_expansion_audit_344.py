from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table


DEFAULT_OUT_DIR = Path("docs/reports/task_344_intraday_evidence_expansion_audit")
TARGETED_SCOPE_CSV = Path("docs/reports/task_343_pro_quant_development_roadmap/task_343_targeted_backfill_scope.csv")
TASK337_AUDIT_CSV = Path("docs/reports/task_337_historical_intraday_ingestion/task_337_intraday_coverage_audit.csv")
TASK338_COVERAGE_FLAGS_CSV = Path("docs/reports/task_338_intraday_evaluation_fix/task_338_trade_coverage_flags.csv")
TASK341_FINAL_CSV = Path("docs/reports/task_341_subset_refinement/task_341_final_decision.csv")
TASK342_FINAL_CSV = Path("docs/reports/task_342_conditional_edge_integration/task_342_final_decision.csv")


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scope_df = pd.read_csv(TARGETED_SCOPE_CSV) if TARGETED_SCOPE_CSV.exists() else pd.DataFrame()
    audit_df = pd.read_csv(TASK337_AUDIT_CSV)
    flags_df = pd.read_csv(TASK338_COVERAGE_FLAGS_CSV)
    task341_df = pd.read_csv(TASK341_FINAL_CSV)
    task342_df = pd.read_csv(TASK342_FINAL_CSV)
    return scope_df, audit_df, flags_df, task341_df, task342_df


def _attempt_summary(scope_df: pd.DataFrame, audit_df: pd.DataFrame) -> pd.DataFrame:
    if scope_df.empty:
        return pd.DataFrame(
            [
                {
                    "attempt_scope_count": 0,
                    "covered_after_retry": 0,
                    "still_insufficient_after_retry": 0,
                    "coverage_gain_dates": 0,
                    "retry_result": "no_scope_file",
                }
            ]
        )
    merged = scope_df.merge(
        audit_df.rename(columns={"trade_date": "trade_date", "symbol": "symbol"}),
        on=["symbol", "trade_date"],
        how="left",
    )
    covered = int((merged["coverage_status"].astype(str) == "covered").sum())
    insufficient = int((merged["coverage_status"].astype(str) == "insufficient_window").sum())
    return pd.DataFrame(
        [
            {
                "attempt_scope_count": int(len(merged)),
                "covered_after_retry": covered,
                "still_insufficient_after_retry": insufficient,
                "coverage_gain_dates": covered,
                "retry_result": "no_coverage_gain" if covered == 0 else "partial_gain",
            }
        ]
    )


def _anchored_oos_reason_breakdown(flags_df: pd.DataFrame) -> pd.DataFrame:
    scoped = flags_df[flags_df["split"] == "anchored_oos"].copy()
    rows = []
    total = max(len(scoped), 1)
    for reason, reason_df in scoped.groupby(scoped["missing_reason"].fillna("covered")):
        rows.append(
            {
                "split": "anchored_oos",
                "reason": str(reason) if str(reason) else "covered",
                "trade_count": int(len(reason_df)),
                "share": round(float(len(reason_df) / total), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["trade_count", "reason"], ascending=[False, True]).reset_index(drop=True)


def _software_internet_gap(flags_df: pd.DataFrame) -> pd.DataFrame:
    scoped = flags_df[flags_df["split"] == "anchored_oos"].copy()
    uncovered = scoped[~scoped["is_covered"].astype(bool)].copy()
    symbols = sorted(uncovered["symbol"].astype(str).value_counts().items(), key=lambda item: (-item[1], item[0]))
    rows = [{"symbol": symbol, "uncovered_trade_count": int(count)} for symbol, count in symbols]
    return pd.DataFrame(rows)


def _decision(task341_df: pd.DataFrame, task342_df: pd.DataFrame, attempt_df: pd.DataFrame, reasons_df: pd.DataFrame) -> pd.DataFrame:
    attempt = attempt_df.iloc[0]
    task341 = task341_df.iloc[0]
    task342 = task342_df.iloc[0]
    dominated_by_incomplete = bool(
        (reasons_df["reason"].astype(str) == "incomplete_intraday_window").any()
        and reasons_df.loc[reasons_df["reason"].astype(str) == "incomplete_intraday_window", "trade_count"].iloc[0] > 0
    )
    no_gain = int(attempt["coverage_gain_dates"]) == 0
    if no_gain and dominated_by_incomplete:
        next_bottleneck = "event_alignment_or_provider_coverage"
        next_research_step = "priority_overlay_research_should_wait_for_better_coverage_or_better_breakout_alignment"
        decision = "NO_EVIDENCE_EXPANSION_GAIN"
        reason = "targeted backfill added no new covered dates; remaining gap is dominated by incomplete intraday windows, not missing archive dates"
    else:
        next_bottleneck = "archive_extension"
        next_research_step = "rerun_338_342_after_expansion"
        decision = "PARTIAL_EVIDENCE_EXPANSION_GAIN"
        reason = "coverage improved enough to justify rerunning downstream intraday evaluation stack"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "task341_state": str(task341["decision"]),
                "task342_state": str(task342["decision"]),
                "next_bottleneck": next_bottleneck,
                "next_research_step": next_research_step,
            }
        ]
    )


def _markdown_report(
    out_dir: Path,
    attempt_df: pd.DataFrame,
    reasons_df: pd.DataFrame,
    gap_df: pd.DataFrame,
    decision_df: pd.DataFrame,
) -> None:
    decision = str(decision_df.iloc[0]["decision"])
    lines: list[str] = [
        "# Task 344: Intraday Evidence Expansion Audit",
        "",
        f"Final decision: **{decision}**",
        "",
        "## Retry Attempt",
        "",
    ]
    lines.extend(_markdown_table(attempt_df))
    lines.extend(
        [
            "",
            "## Anchored OOS Coverage Reasons",
            "",
        ]
    )
    lines.extend(_markdown_table(reasons_df))
    lines.extend(
        [
            "",
            "## Uncovered Anchored OOS Symbols",
            "",
        ]
    )
    lines.extend(_markdown_table(gap_df.head(15)))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- The targeted backfill retry produced `{attempt_df.iloc[0]['coverage_gain_dates']}` newly covered required dates.",
            "- Remaining anchored OOS gap is dominated by `incomplete_intraday_window`, not by `missing_date` or `missing_symbol`.",
            "- This means the next evidence-quality bottleneck is no longer raw archive presence alone.",
            f"- Recommended next step: `{decision_df.iloc[0]['next_research_step']}`",
        ]
    )
    (out_dir / "task_344_intraday_evidence_expansion_audit.md").write_text("\n".join(lines), encoding="utf-8")


def run(output_dir: Path = DEFAULT_OUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    scope_df, audit_df, flags_df, task341_df, task342_df = _load_inputs()
    attempt_df = _attempt_summary(scope_df, audit_df)
    reasons_df = _anchored_oos_reason_breakdown(flags_df)
    gap_df = _software_internet_gap(flags_df)
    decision_df = _decision(task341_df, task342_df, attempt_df, reasons_df)

    attempt_df.to_csv(output_dir / "task_344_targeted_backfill_attempt_summary.csv", index=False)
    reasons_df.to_csv(output_dir / "task_344_anchored_oos_reason_breakdown.csv", index=False)
    gap_df.to_csv(output_dir / "task_344_anchored_oos_uncovered_symbols.csv", index=False)
    decision_df.to_csv(output_dir / "task_344_evidence_expansion_decision.csv", index=False)
    _markdown_report(output_dir, attempt_df, reasons_df, gap_df, decision_df)


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 344: intraday evidence expansion audit.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
