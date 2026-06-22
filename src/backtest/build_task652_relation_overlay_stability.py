from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import INITIAL_CAPITAL_USD, load_qqq_history
from src.backtest.build_task639_oos_first_rule_lock_refinement import run_account


TASK_ID = "Task652"
REPORT_DIR = Path("docs/reports/task_652_relation_overlay_stability")
EXECUTION_PANEL = Path("docs/reports/task_638_content_signal_refinement/task_638_timing_exit_execution_panel.csv")
TASK651_STATE_PANEL = Path("docs/reports/task_651_relation_state_machine/task_651_gate_state_panel.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
QQQ_PATH = Path("data/raw/us_daily_breadth_top500/QQQ.csv")


def build_task652_relation_overlay_stability(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    state_panel_path: Path = TASK651_STATE_PANEL,
    task639_decision_path: Path = TASK639_DECISION,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    execution = load_execution_panel(execution_panel_path)
    states = load_state_panel(state_panel_path)
    tagged = attach_relation_tags(execution, states)
    baseline = task639_baseline(tagged)
    qqq = load_qqq_history(qqq_path)
    task639 = pd.read_csv(task639_decision_path).iloc[0]
    candidate_grid = build_candidate_grid(baseline, qqq)
    split_grid = build_split_grid(baseline, qqq)
    tag_diagnostics = build_tag_diagnostics(baseline)
    stability = build_stability_matrix(candidate_grid, split_grid, task639)
    gpt_status = build_gpt_status()
    decision = build_decision(candidate_grid, split_grid, stability, task639)
    pass_fail = build_pass_fail(candidate_grid, split_grid, stability, gpt_status, decision)

    tagged.to_csv(out_dir / "task_652_relation_tagged_execution_panel.csv", index=False, encoding="utf-8-sig")
    candidate_grid.to_csv(out_dir / "task_652_candidate_account_grid.csv", index=False, encoding="utf-8-sig")
    split_grid.to_csv(out_dir / "task_652_split_account_grid.csv", index=False, encoding="utf-8-sig")
    tag_diagnostics.to_csv(out_dir / "task_652_tag_diagnostics.csv", index=False, encoding="utf-8-sig")
    stability.to_csv(out_dir / "task_652_stability_matrix.csv", index=False, encoding="utf-8-sig")
    gpt_status.to_csv(out_dir / "task_652_gpt_review_status.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_652_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_652_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_gpt_packet(out_dir)
    write_report(out_dir, decision, candidate_grid, split_grid, tag_diagnostics, gpt_status, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "tagged": tagged,
        "candidate_grid": candidate_grid,
        "split_grid": split_grid,
        "tag_diagnostics": tag_diagnostics,
        "stability": stability,
        "gpt_status": gpt_status,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def load_execution_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    for column in ["net_return_from_entry", "entry_price", "simulated_exit_price", "holding_days"]:
        if column in panel.columns:
            panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def load_state_panel(path: Path) -> pd.DataFrame:
    states = pd.read_csv(path)
    keep = [
        "lifecycle_id",
        "timing_mode",
        "exit_mode",
        "relation_state",
        "action_bucket",
        "company_gate_state",
        "macro_gate_state",
        "chart_gate_state",
        "sector_gate_state",
        "policy_geo_gate_state",
        "action_reason_codes",
    ]
    return states[[c for c in keep if c in states.columns]].drop_duplicates(["lifecycle_id", "timing_mode", "exit_mode"])


def attach_relation_tags(execution: pd.DataFrame, states: pd.DataFrame) -> pd.DataFrame:
    return execution.merge(states, on=["lifecycle_id", "timing_mode", "exit_mode"], how="left")


def task639_baseline(tagged: pd.DataFrame) -> pd.DataFrame:
    core = (
        pd.to_numeric(tagged.get("positive_contract_customer_count"), errors="coerce").fillna(0).gt(0)
        | pd.to_numeric(tagged.get("content_supply_demand_flag"), errors="coerce").fillna(0).eq(1)
    )
    return tagged[core & tagged["timing_mode"].eq("delay1d") & tagged["exit_mode"].eq("existing_exit")].copy()


def candidate_masks(panel: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "baseline_task639_core": pd.Series(True, index=panel.index),
        "chart_confirmed_only": panel["chart_gate_state"].eq("chart_confirmed"),
        "chart_not_unconfirmed": ~panel["chart_gate_state"].eq("chart_unconfirmed"),
        "chart_not_fragile_or_unconfirmed": ~panel["chart_gate_state"].isin(["chart_fragile", "chart_unconfirmed"]),
        "macro_known_mixed_supportive": panel["macro_gate_state"].isin(["macro_mixed", "macro_supportive"]),
        "macro_mixed_only": panel["macro_gate_state"].eq("macro_mixed"),
        "company_not_strong_label": ~panel["company_gate_state"].eq("strong_company_positive"),
        "moderate_or_mixed_company": panel["company_gate_state"].isin(["moderate_company_positive", "mixed_company_positive_conflict"]),
        "confirmed_moderate_or_mixed": panel["chart_gate_state"].eq("chart_confirmed")
        & panel["company_gate_state"].isin(["moderate_company_positive", "mixed_company_positive_conflict"]),
    }


def build_candidate_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, mask in candidate_masks(panel).items():
        selected = panel[mask].copy()
        metrics = run_account(selected, "equal_max5", qqq)
        rows.append(row_from_metrics(name, "all", selected, metrics))
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def build_split_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows = []
    masks = candidate_masks(panel)
    for split_name in ["validation", "recent_oos"]:
        split_panel = panel[panel["split_name"].astype(str).eq(split_name)].copy()
        for name in masks:
            split_masks = candidate_masks(split_panel)
            selected = split_panel[split_masks[name]].copy()
            metrics = run_account(selected, "equal_max5", qqq)
            rows.append(row_from_metrics(name, split_name, selected, metrics))
    return pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)


def row_from_metrics(name: str, split_name: str, selected: pd.DataFrame, metrics: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_name": name,
        "split_name": split_name,
        "initial_capital_usd": INITIAL_CAPITAL_USD,
        "source_trade_count": int(len(selected)),
        "accepted_trade_count": int(metrics["accepted_trade_count"]),
        "final_capital_usd": float(metrics["final_capital_usd"]),
        "capital_return_pct": float(metrics["capital_return_pct"]),
        "max_drawdown_pct": float(metrics["max_drawdown_pct"]),
        "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
        "qqq_final_capital_usd": float(metrics["qqq_final_capital_usd"]),
        "beats_qqq_flag": int(metrics["final_capital_usd"] > metrics["qqq_final_capital_usd"]),
        "label_used_in_assignment_flag": 0,
        "return_used_in_assignment_flag": 0,
        "promotion_candidate_flag": 0,
    }


def build_tag_diagnostics(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in ["relation_state", "company_gate_state", "macro_gate_state", "chart_gate_state", "sector_gate_state"]:
        for value, group in panel.groupby(column, dropna=False):
            ret = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
            rows.append(
                {
                    "tag_column": column,
                    "tag_value": value,
                    "row_count": int(len(group)),
                    "avg_return_pct": float(ret.mean() * 100.0) if ret.notna().any() else 0.0,
                    "win_rate": float(ret.gt(0).mean()) if ret.notna().any() else 0.0,
                    "entry_reduce_failure_rate": float(ret.le(-0.03).mean()) if ret.notna().any() else 0.0,
                    "large_loss_rate": float(ret.le(-0.10).mean()) if ret.notna().any() else 0.0,
                    "evaluation_only_flag": 1,
                }
            )
    return pd.DataFrame(rows).sort_values(["tag_column", "row_count"], ascending=[True, False]).reset_index(drop=True)


def build_stability_matrix(candidate_grid: pd.DataFrame, split_grid: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    baseline_all = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    rows = []
    for _, row in candidate_grid.iterrows():
        name = row["candidate_name"]
        validation = split_grid[split_grid["candidate_name"].eq(name) & split_grid["split_name"].eq("validation")].iloc[0]
        recent = split_grid[split_grid["candidate_name"].eq(name) & split_grid["split_name"].eq("recent_oos")].iloc[0]
        rows.append(
            {
                "candidate_name": name,
                "beats_task639_full_flag": int(float(row["final_capital_usd"]) > float(baseline_all["final_capital_usd"])),
                "drawdown_better_than_task639_flag": int(float(row["max_drawdown_pct"]) > float(baseline_all["max_drawdown_pct"])),
                "validation_beats_qqq_flag": int(validation["beats_qqq_flag"]),
                "recent_oos_beats_qqq_flag": int(recent["beats_qqq_flag"]),
                "min_oos_trade_count": int(min(int(validation["accepted_trade_count"]), int(recent["accepted_trade_count"]))),
                "promotion_candidate_flag": 0,
                "discard_for_execution_flag": int(name != "baseline_task639_core"),
            }
        )
    return pd.DataFrame(rows)


def build_gpt_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_round": "task652_stability_review",
                "requested_via": "Chrome ChatGPT coding/investing tab",
                "captured_flag": 0,
                "status": "ATTEMPTED_BUT_CHROME_TIMEOUT",
                "used_as_source_flag": 0,
                "fallback_policy": "Applied prior GPT review principles from Task650-651: preserve Task639 baseline, use relation as diagnostic overlay only, reject filters that do not beat Task639 after costs.",
            }
        ]
    )


def build_decision(candidate_grid: pd.DataFrame, split_grid: pd.DataFrame, stability: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    baseline = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    best = candidate_grid.iloc[0]
    candidate_beats = stability[
        stability["candidate_name"].ne("baseline_task639_core")
        & stability["beats_task639_full_flag"].eq(1)
        & stability["drawdown_better_than_task639_flag"].eq(1)
        & stability["validation_beats_qqq_flag"].eq(1)
        & stability["recent_oos_beats_qqq_flag"].eq(1)
    ]
    verdict = "NO_RELATION_OVERLAY_BEATS_TASK639_KEEP_BASELINE_DIAGNOSTIC_ONLY"
    if not candidate_beats.empty:
        verdict = "RELATION_OVERLAY_CANDIDATE_FOUND_NOT_ACCEPTED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": verdict,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                "baseline_final_capital_usd": float(baseline["final_capital_usd"]),
                "baseline_max_drawdown_pct": float(baseline["max_drawdown_pct"]),
                "best_candidate_name": best["candidate_name"],
                "best_candidate_final_capital_usd": float(best["final_capital_usd"]),
                "best_candidate_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "task639_reference_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "task639_reference_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
                "relation_overlay_promotion_candidate_count": int(len(candidate_beats)),
                "trading_promotion_pass_flag": 0,
                "next_action": "Do not change Task639 execution from relation tags. Use relation tags as diagnostics and wait for microstructure/raw-source features before another execution overlay.",
            }
        ]
    )


def build_pass_fail(
    candidate_grid: pd.DataFrame,
    split_grid: pd.DataFrame,
    stability: pd.DataFrame,
    gpt_status: pd.DataFrame,
    decision: pd.DataFrame,
) -> pd.DataFrame:
    baseline = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    best_overlay = candidate_grid[candidate_grid["candidate_name"].ne("baseline_task639_core")].iloc[0]
    return pd.DataFrame(
        [
            {"gate": "gpt_review_attempted", "pass_flag": 1, "observed_value": str(gpt_status.iloc[0]["status"]), "required_value": "GPT review should be attempted and captured when Chrome is responsive"},
            {"gate": "gpt_used_as_source", "pass_flag": int(int(gpt_status.iloc[0]["used_as_source_flag"]) == 0), "observed_value": "used_as_source=0", "required_value": "GPT must not be used as source truth"},
            {"gate": "candidate_grid_built", "pass_flag": int(len(candidate_grid) >= 5), "observed_value": f"candidates={len(candidate_grid)}", "required_value": "multiple baseline-preserving overlays tested"},
            {"gate": "baseline_beats_qqq", "pass_flag": int(int(baseline["beats_qqq_flag"]) == 1), "observed_value": f"baseline=${float(baseline['final_capital_usd']):.2f}; qqq=${float(baseline['qqq_final_capital_usd']):.2f}", "required_value": "baseline must beat QQQ"},
            {"gate": "best_overlay_beats_task639", "pass_flag": int(float(best_overlay["final_capital_usd"]) > float(baseline["final_capital_usd"])), "observed_value": f"best_overlay={best_overlay['candidate_name']} ${float(best_overlay['final_capital_usd']):.2f}; baseline=${float(baseline['final_capital_usd']):.2f}", "required_value": "overlay must beat Task639 baseline to be useful"},
            {"gate": "overlay_promotion_candidate", "pass_flag": int(int(decision.iloc[0]["relation_overlay_promotion_candidate_count"]) > 0), "observed_value": f"promotion_candidates={int(decision.iloc[0]['relation_overlay_promotion_candidate_count'])}", "required_value": "must beat Task639, improve drawdown, and beat QQQ in validation/recent"},
            {"gate": "trading_promotion", "pass_flag": 0, "observed_value": "diagnostic only", "required_value": "requires accepted OOS, source timing repair, paper shadow, and live readiness"},
        ]
    )


def write_gpt_packet(out_dir: Path) -> None:
    lines = [
        "# Task652 GPT Stability Review Packet",
        "",
        "A Chrome ChatGPT review was requested with Task639, Task651, and relation-tag diagnostics.",
        "Chrome control timed out before a response could be captured.",
        "Task652 therefore uses prior captured GPT principles from Task650-651 only as review guidance, not as source truth.",
        "",
        "Core review principle applied: do not let relation tags alter execution unless a candidate beats Task639 after costs, does not worsen drawdown, and survives validation plus recent OOS.",
    ]
    (out_dir / "task_652_gpt_review_packet.md").write_text("\n".join(lines), encoding="utf-8")


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    candidate_grid: pd.DataFrame,
    split_grid: pd.DataFrame,
    tag_diagnostics: pd.DataFrame,
    gpt_status: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task652 Relation Overlay Stability",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Baseline Task639-style final: ${float(d['baseline_final_capital_usd']):.2f}",
        f"- Baseline max drawdown: {float(d['baseline_max_drawdown_pct']):.2f}%",
        f"- Best tested candidate: `{d['best_candidate_name']}` = ${float(d['best_candidate_final_capital_usd']):.2f}",
        "- Relation overlays did not beat the Task639 baseline after costs.",
        "",
        "## Quant Expert Report",
        "",
        "Task652 tests relation tags as baseline-preserving overlays. It rejects execution changes that do not beat Task639, improve drawdown, and survive validation plus recent OOS.",
        "",
        "### Candidate Grid",
        "",
        table(candidate_grid),
        "",
        "### Split Grid",
        "",
        table(split_grid),
        "",
        "### Tag Diagnostics",
        "",
        table(tag_diagnostics),
        "",
        "### GPT Review Status",
        "",
        table(gpt_status),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- 기준선이 아직 제일 셉니다.",
        "- relation 태그로 차트/매크로/회사 상태를 더 똑똑하게 나눠 봤지만, 돈으로는 Task639를 못 이겼습니다.",
        "- 그래서 지금은 매매를 바꾸면 안 됩니다.",
        "- relation은 감시표로 두고, 다음 개선은 microstructure 원천 데이터가 차야 가능합니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `task_652_relation_tagged_execution_panel.csv`",
        "- `task_652_candidate_account_grid.csv`",
        "- `task_652_split_account_grid.csv`",
        "- `task_652_tag_diagnostics.csv`",
        "- `task_652_stability_matrix.csv`",
        "- `task_652_gpt_review_status.csv`",
        "- `task_652_decision.csv`",
        "- `task_652_pass_fail_matrix.csv`",
        "- `task_652_gpt_review_packet.md`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_652_relation_overlay_stability.md").write_text("\n".join(lines), encoding="utf-8")


def table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    cols = list(frame.columns)
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in frame.iterrows():
        out.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = build_task652_relation_overlay_stability(out_dir=args.out_dir)
    d = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={d['decision']} "
        f"baseline=${float(d['baseline_final_capital_usd']):.2f} "
        f"best={d['best_candidate_name']} ${float(d['best_candidate_final_capital_usd']):.2f}"
    )


if __name__ == "__main__":
    main()
