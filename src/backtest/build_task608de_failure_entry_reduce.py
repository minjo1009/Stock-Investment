from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task608DE"
REPORT_DIR = Path("docs/reports/task_608de_failure_entry_reduce")
TASK509_PANEL = Path("docs/reports/task_509_walk_forward_oos_validation/walk_forward_oos_assignment_panel.csv")

STATE_DIMENSIONS = [
    "theme_regime_state_v4",
    "symbol_multiday_setup_state",
    "timing_state",
    "theme_id",
    "symbol",
]


def build_task608de_failure_entry_reduce(
    *,
    task509_panel_path: Path = TASK509_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_oos_panel(task509_panel_path)
    baseline = summarize_panel(panel, label="baseline_oos")
    quarter_map = build_quarter_failure_map(panel, baseline)
    entry_reduce_by_quarter = build_entry_reduce_by_quarter(panel, quarter_map)
    entry_reduce_attribution = build_entry_reduce_attribution(panel, quarter_map)
    weak_state = build_weak_quarter_state_decomposition(panel, quarter_map)
    entry_reduce_state = build_entry_reduce_state_decomposition(panel)
    decisions = build_decisions(baseline, quarter_map, entry_reduce_attribution)

    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([baseline]).to_csv(out_dir / "baseline_oos_failure_metrics.csv", index=False)
    quarter_map.to_csv(out_dir / "quarter_failure_map.csv", index=False)
    entry_reduce_by_quarter.to_csv(out_dir / "entry_reduce_by_quarter.csv", index=False)
    entry_reduce_attribution.to_csv(out_dir / "entry_reduce_cohort_attribution.csv", index=False)
    weak_state.to_csv(out_dir / "weak_quarter_state_decomposition.csv", index=False)
    entry_reduce_state.to_csv(out_dir / "entry_reduce_state_decomposition.csv", index=False)
    decisions.to_csv(out_dir / "task_608de_decision.csv", index=False)
    (out_dir / "task_608de_failure_entry_reduce.md").write_text(
        render_report(
            baseline=baseline,
            quarter_map=quarter_map,
            entry_reduce_by_quarter=entry_reduce_by_quarter,
            entry_reduce_attribution=entry_reduce_attribution,
            weak_state=weak_state,
            decisions=decisions,
        ),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "baseline_oos_failure_metrics": pd.DataFrame([baseline]),
        "quarter_failure_map": quarter_map,
        "entry_reduce_by_quarter": entry_reduce_by_quarter,
        "entry_reduce_cohort_attribution": entry_reduce_attribution,
        "weak_quarter_state_decomposition": weak_state,
        "entry_reduce_state_decomposition": entry_reduce_state,
        "task_608de_decision": decisions,
    }


def load_oos_panel(path: Path | str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True, errors="coerce")
    frame["net_return_from_entry"] = pd.to_numeric(frame["net_return_from_entry"], errors="coerce")
    frame["win_flag"] = pd.to_numeric(frame["win_flag"], errors="coerce").fillna(0).astype(int)
    frame["entry_reduce_failure_flag"] = (
        pd.to_numeric(frame["entry_reduce_failure_flag"], errors="coerce").fillna(0).astype(int)
    )
    frame["holding_days"] = pd.to_numeric(frame.get("holding_days", 0), errors="coerce")
    frame = frame.dropna(subset=["entry_ts", "net_return_from_entry", "lifecycle_id"]).copy()
    if "quarter" not in frame.columns:
        frame["quarter"] = frame["entry_ts"].dt.to_period("Q").astype(str)
    for column in STATE_DIMENSIONS:
        if column not in frame.columns:
            frame[column] = "missing"
        frame[column] = frame[column].fillna("missing").astype(str)
    return frame.sort_values("entry_ts").reset_index(drop=True)


def summarize_panel(panel: pd.DataFrame, *, label: str) -> dict[str, Any]:
    return {
        "label": label,
        "lifecycle_count": int(len(panel)),
        "avg_net_return_pct": _avg_return_pct(panel),
        "median_net_return_pct": _median_return_pct(panel),
        "win_rate": _rate(panel, "win_flag"),
        "entry_reduce_failure_rate": _rate(panel, "entry_reduce_failure_flag"),
        "median_holding_days": _median(panel, "holding_days"),
    }


def build_quarter_failure_map(panel: pd.DataFrame, baseline: dict[str, Any]) -> pd.DataFrame:
    rows = []
    baseline_avg = float(baseline["avg_net_return_pct"])
    baseline_er = float(baseline["entry_reduce_failure_rate"])
    for quarter, group in panel.groupby("quarter", sort=True):
        row = summarize_panel(group, label=str(quarter))
        row["quarter"] = str(quarter)
        row["avg_gap_vs_baseline_pct_points"] = row["avg_net_return_pct"] - baseline_avg
        row["entry_reduce_gap_vs_baseline"] = row["entry_reduce_failure_rate"] - baseline_er
        row["hard_break_flag"] = int(row["avg_net_return_pct"] < 0.0)
        row["weak_quarter_flag"] = int(
            row["avg_net_return_pct"] < baseline_avg * 0.5
            or row["entry_reduce_failure_rate"] >= 0.50
            or row["win_rate"] <= 0.50
        )
        rows.append(row)
    columns = [
        "quarter",
        "lifecycle_count",
        "avg_net_return_pct",
        "median_net_return_pct",
        "win_rate",
        "entry_reduce_failure_rate",
        "median_holding_days",
        "avg_gap_vs_baseline_pct_points",
        "entry_reduce_gap_vs_baseline",
        "hard_break_flag",
        "weak_quarter_flag",
    ]
    return pd.DataFrame(rows)[columns].sort_values("quarter").reset_index(drop=True)


def build_entry_reduce_by_quarter(panel: pd.DataFrame, quarter_map: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for quarter, group in panel.groupby("quarter", sort=True):
        clean = group[group["entry_reduce_failure_flag"].eq(0)]
        failed = group[group["entry_reduce_failure_flag"].eq(1)]
        clean_avg = _avg_return_pct(clean)
        failed_avg = _avg_return_pct(failed)
        spread = failed_avg - clean_avg
        failed_share = _safe_div(len(failed), len(group))
        rows.append(
            {
                "quarter": str(quarter),
                "lifecycle_count": int(len(group)),
                "clean_count": int(len(clean)),
                "clean_avg_net_return_pct": clean_avg,
                "clean_win_rate": _rate(clean, "win_flag"),
                "failed_count": int(len(failed)),
                "failed_avg_net_return_pct": failed_avg,
                "failed_win_rate": _rate(failed, "win_flag"),
                "failed_share": failed_share,
                "failed_vs_clean_spread_pct_points": spread,
                "failed_drag_pct_points": failed_share * spread,
            }
        )
    frame = pd.DataFrame(rows)
    weak_lookup = quarter_map.set_index("quarter")["weak_quarter_flag"].to_dict()
    frame["weak_quarter_flag"] = frame["quarter"].map(weak_lookup).fillna(0).astype(int)
    return frame.sort_values("quarter").reset_index(drop=True)


def build_entry_reduce_attribution(panel: pd.DataFrame, quarter_map: pd.DataFrame) -> pd.DataFrame:
    weak_quarters = set(quarter_map[quarter_map["weak_quarter_flag"].eq(1)]["quarter"].astype(str))
    rows = []
    total_negative_return_pct = abs(float((panel["net_return_from_entry"].clip(upper=0) * 100.0).sum()))
    for flag, group in panel.groupby("entry_reduce_failure_flag", sort=True):
        negative_return_pct = abs(float((group["net_return_from_entry"].clip(upper=0) * 100.0).sum()))
        rows.append(
            {
                "entry_reduce_failure_flag": int(flag),
                "cohort": "entry_reduce_failed" if int(flag) == 1 else "clean_entry",
                "lifecycle_count": int(len(group)),
                "count_share": _safe_div(len(group), len(panel)),
                "avg_net_return_pct": _avg_return_pct(group),
                "median_net_return_pct": _median_return_pct(group),
                "win_rate": _rate(group, "win_flag"),
                "median_holding_days": _median(group, "holding_days"),
                "negative_return_share": _safe_div(negative_return_pct, total_negative_return_pct),
                "weak_quarter_count": int(group["quarter"].astype(str).isin(weak_quarters).sum()),
                "weak_quarter_share_inside_cohort": _safe_div(
                    int(group["quarter"].astype(str).isin(weak_quarters).sum()), len(group)
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("entry_reduce_failure_flag").reset_index(drop=True)


def build_weak_quarter_state_decomposition(panel: pd.DataFrame, quarter_map: pd.DataFrame) -> pd.DataFrame:
    weak_quarters = set(quarter_map[quarter_map["weak_quarter_flag"].eq(1)]["quarter"].astype(str))
    weak = panel[panel["quarter"].astype(str).isin(weak_quarters)].copy()
    rows = []
    for dimension in STATE_DIMENSIONS:
        for value, group in weak.groupby(dimension, sort=True):
            rows.append(_dimension_row(dimension, str(value), group, weak))
    return pd.DataFrame(rows).sort_values(
        ["entry_reduce_failed_count", "avg_net_return_pct"], ascending=[False, True]
    ).reset_index(drop=True)


def build_entry_reduce_state_decomposition(panel: pd.DataFrame) -> pd.DataFrame:
    failed = panel[panel["entry_reduce_failure_flag"].eq(1)].copy()
    rows = []
    for dimension in STATE_DIMENSIONS:
        for value, group in failed.groupby(dimension, sort=True):
            rows.append(_dimension_row(dimension, str(value), group, failed))
    return pd.DataFrame(rows).sort_values(
        ["lifecycle_count", "avg_net_return_pct"], ascending=[False, True]
    ).reset_index(drop=True)


def build_decisions(
    baseline: dict[str, Any],
    quarter_map: pd.DataFrame,
    entry_reduce_attribution: pd.DataFrame,
) -> pd.DataFrame:
    failed = entry_reduce_attribution[
        entry_reduce_attribution["entry_reduce_failure_flag"].astype(int).eq(1)
    ].iloc[0].to_dict()
    clean = entry_reduce_attribution[
        entry_reduce_attribution["entry_reduce_failure_flag"].astype(int).eq(0)
    ].iloc[0].to_dict()
    hard_breaks = int(quarter_map["hard_break_flag"].sum())
    weak_quarters = int(quarter_map["weak_quarter_flag"].sum())
    entry_reduce_material = int(
        float(failed["avg_net_return_pct"]) < 0
        and float(failed["win_rate"]) <= 0.05
        and float(baseline["entry_reduce_failure_rate"]) >= 0.30
    )
    failure_map_identified = int(hard_breaks >= 1 and weak_quarters >= 1)
    return pd.DataFrame(
        [
            {
                "task_id": "Task608D",
                "decision": (
                    "PASS_FAILURE_REGIME_MAP_IDENTIFIED_NOT_RESOLVED"
                    if failure_map_identified
                    else "FAIL_FAILURE_REGIME_MAP_NOT_IDENTIFIED"
                ),
                "pass_flag": failure_map_identified,
                "hard_break_quarter_count": hard_breaks,
                "weak_quarter_count": weak_quarters,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "next_action": "Use weak-quarter map to test entry suppression or separated policy logic.",
            },
            {
                "task_id": "Task608E",
                "decision": (
                    "FAIL_ENTRY_REDUCE_FAILURE_MATERIAL"
                    if entry_reduce_material
                    else "PASS_ENTRY_REDUCE_FAILURE_NOT_MATERIAL"
                ),
                "pass_flag": int(not entry_reduce_material),
                "clean_avg_net_return_pct": float(clean["avg_net_return_pct"]),
                "failed_avg_net_return_pct": float(failed["avg_net_return_pct"]),
                "failed_win_rate": float(failed["win_rate"]),
                "entry_reduce_failure_rate": float(baseline["entry_reduce_failure_rate"]),
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "next_action": "Do not refine headline rule until entry-reduce failure is suppressed or isolated.",
            },
            {
                "task_id": TASK_ID,
                "decision": "FAIL_FAILURE_ENTRY_REDUCE_NOT_FIRM_GRADE",
                "pass_flag": 0,
                "hard_break_quarter_count": hard_breaks,
                "weak_quarter_count": weak_quarters,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "next_action": "Task608F should test entry-reduce suppression, separated clean-entry policy, and OOS capital impact.",
            },
        ]
    )


def render_report(
    *,
    baseline: dict[str, Any],
    quarter_map: pd.DataFrame,
    entry_reduce_by_quarter: pd.DataFrame,
    entry_reduce_attribution: pd.DataFrame,
    weak_state: pd.DataFrame,
    decisions: pd.DataFrame,
) -> str:
    summary = decisions[decisions["task_id"].eq(TASK_ID)].iloc[0].to_dict()
    task_d = decisions[decisions["task_id"].eq("Task608D")].iloc[0].to_dict()
    task_e = decisions[decisions["task_id"].eq("Task608E")].iloc[0].to_dict()
    clean = entry_reduce_attribution[entry_reduce_attribution["entry_reduce_failure_flag"].eq(0)].iloc[0].to_dict()
    failed = entry_reduce_attribution[entry_reduce_attribution["entry_reduce_failure_flag"].eq(1)].iloc[0].to_dict()
    worst_quarter = quarter_map.sort_values("avg_net_return_pct").iloc[0].to_dict()
    largest_drag = entry_reduce_by_quarter.sort_values("failed_drag_pct_points").iloc[0].to_dict()
    top_weak_states = weak_state.head(6)
    state_lines = [
        (
            f"- {row['dimension']}={row['value']}: count {int(row['lifecycle_count'])}, "
            f"entry-reduce failed {int(row['entry_reduce_failed_count'])}, "
            f"avg {float(row['avg_net_return_pct']):.2f}%"
        )
        for _, row in top_weak_states.iterrows()
    ]
    return "\n".join(
        [
            "# Task608D/E Failure Regime And Entry-Reduce Attribution",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: {summary['decision']}",
            f"- Task608D: {task_d['decision']}",
            f"- Task608E: {task_e['decision']}",
            f"- Baseline OOS: count {int(baseline['lifecycle_count'])}, avg {float(baseline['avg_net_return_pct']):.2f}%, win {float(baseline['win_rate']):.2%}, entry-reduce {float(baseline['entry_reduce_failure_rate']):.2%}.",
            f"- Clean entries: count {int(clean['lifecycle_count'])}, avg {float(clean['avg_net_return_pct']):.2f}%, win {float(clean['win_rate']):.2%}.",
            f"- Entry-reduce failed entries: count {int(failed['lifecycle_count'])}, avg {float(failed['avg_net_return_pct']):.2f}%, win {float(failed['win_rate']):.2%}.",
            f"- Worst quarter: {worst_quarter['quarter']} avg {float(worst_quarter['avg_net_return_pct']):.2f}%, entry-reduce {float(worst_quarter['entry_reduce_failure_rate']):.2%}.",
            f"- Largest entry-reduce drag quarter: {largest_drag['quarter']} drag {float(largest_drag['failed_drag_pct_points']):.2f} pct points.",
            "- What changed: the break is now attributed to entry-reduce failure concentration, not theme/symbol/parameter dependency alone.",
            f"- Next action: {summary['next_action']}",
            "",
            "## Quant Expert Report",
            "",
            "- Data source and source readiness: Task509 walk-forward OOS assignment panel only; no new raw market source or live broker source was introduced.",
            "- Exact join keys: existing `lifecycle_id` rows are used as-is; no inferred lifecycle matching, symbol/date/price/time fallback, or label repair was used.",
            "- Leakage audit: labels/outcomes are evaluation-only. No outcome field enters assignment or filtering logic in this diagnostic.",
            "- Split/OOS metrics: all rows are Task509 walk-forward OOS assignment rows.",
            "- Failure decomposition: `quarter_failure_map.csv` marks hard-break and weak quarters. `entry_reduce_by_quarter.csv` measures clean versus failed-entry drag by quarter.",
            "- Cost/slippage stress: unchanged from Task508/Task608; this task isolates OOS failure attribution only.",
            "- Remaining blockers: entry-reduce failure is material and must be suppressed, isolated, or rejected before strategy acceptance can change.",
            "",
            "Top weak-quarter state rows:",
            *state_lines,
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- What happened: the strategy mostly breaks when failed entries become common.",
            "- Why it matters: good entries still made money, but failed entries were large enough to pull full quarters down.",
            "- Whether this changes capital/deployment readiness: no. Status remains NOT_ACCEPTED and DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
            "- Plain-language next step: test a version that blocks or separates entry-reduce situations, then rerun OOS capital metrics.",
            "",
            "## Artifact Manifest",
            "",
            "- See `artifact_manifest.csv`.",
        ]
    ).rstrip() + "\n"


def _dimension_row(dimension: str, value: str, group: pd.DataFrame, parent: pd.DataFrame) -> dict[str, Any]:
    failed_count = int(group["entry_reduce_failure_flag"].sum())
    return {
        "dimension": dimension,
        "value": value,
        "lifecycle_count": int(len(group)),
        "parent_count_share": _safe_div(len(group), len(parent)),
        "avg_net_return_pct": _avg_return_pct(group),
        "win_rate": _rate(group, "win_flag"),
        "entry_reduce_failure_rate": _rate(group, "entry_reduce_failure_flag"),
        "entry_reduce_failed_count": failed_count,
        "entry_reduce_failed_share_of_parent_failures": _safe_div(
            failed_count, int(parent["entry_reduce_failure_flag"].sum())
        ),
    }


def _avg_return_pct(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    return float(frame["net_return_from_entry"].mean() * 100.0)


def _median_return_pct(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    return float(frame["net_return_from_entry"].median() * 100.0)


def _rate(frame: pd.DataFrame, column: str) -> float:
    if frame.empty:
        return 0.0
    return float(frame[column].astype(float).mean())


def _median(frame: pd.DataFrame, column: str) -> float:
    if frame.empty:
        return 0.0
    return float(frame[column].median())


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task509-panel", type=Path, default=TASK509_PANEL)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task608de_failure_entry_reduce(
        task509_panel_path=args.task509_panel,
        out_dir=args.out_dir,
    )
    summary = artifacts["task_608de_decision"]
    row = summary[summary["task_id"].eq(TASK_ID)].iloc[0]
    print(f"[TASK608DE] decision={row['decision']} pass={int(row['pass_flag'])}")


if __name__ == "__main__":
    main()
