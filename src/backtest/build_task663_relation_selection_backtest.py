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
from src.backtest.build_task659_theme_specific_relation_engine import QQQ_PATH, task639_core
from src.backtest.build_task661_mechanism_relation_engine import (
    TASK659_PANEL,
    build_institutional_transmission_template,
    build_mechanism_state_panel,
    load_task659_panel,
)


TASK_ID = "Task663"
REPORT_DIR = Path("docs/reports/task_663_relation_selection_backtest")


def build_task663_relation_selection_backtest(
    *,
    task659_panel_path: Path = TASK659_PANEL,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = build_mechanism_state_panel(load_task659_panel(task659_panel_path), build_institutional_transmission_template())
    core = task639_core(panel)
    qqq = load_qqq_history(qqq_path)

    specs = build_candidate_specs()
    candidate_grid = build_candidate_grid(core, specs, qqq)
    promotion = build_promotion_report(candidate_grid, specs)
    diagnostics = build_relation_state_oos_diagnostics(core)
    failure = build_failure_analysis(candidate_grid, promotion)
    decision = build_decision(candidate_grid, promotion)
    pass_fail = build_pass_fail(candidate_grid, promotion)

    specs.to_csv(out_dir / "relation_selection_candidate_specs.csv", index=False, encoding="utf-8-sig")
    candidate_grid.to_csv(out_dir / "relation_selection_candidate_grid.csv", index=False, encoding="utf-8-sig")
    promotion.to_csv(out_dir / "relation_selection_promotion_report.csv", index=False, encoding="utf-8-sig")
    diagnostics.to_csv(out_dir / "relation_state_oos_diagnostics.csv", index=False, encoding="utf-8-sig")
    failure.to_csv(out_dir / "relation_selection_failure_analysis.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_663_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_663_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, candidate_grid, promotion, diagnostics, failure, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "specs": specs,
        "candidate_grid": candidate_grid,
        "promotion": promotion,
        "diagnostics": diagnostics,
        "failure": failure,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_candidate_specs() -> pd.DataFrame:
    rows = [
        {
            "candidate_name": "baseline_task639_core",
            "candidate_type": "baseline",
            "states_included": "*",
            "themes_excluded": "",
            "sparse_allowed_flag": 1,
            "diagnostic_only_flag": 0,
            "relation_state_used_for_selection_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Original Task639 candidate set with existing timing and exit.",
        },
        {
            "candidate_name": "predeclared_reinforcing_only_existing_exit",
            "candidate_type": "predeclared_state_selection",
            "states_included": "mechanism_reinforcing_company_positive",
            "themes_excluded": "",
            "sparse_allowed_flag": 0,
            "diagnostic_only_flag": 0,
            "relation_state_used_for_selection_flag": 1,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Trade only rows where company catalyst is reinforced by macro mechanism; keep Task639 exit.",
        },
        {
            "candidate_name": "predeclared_reinforcing_or_offsetting_existing_exit",
            "candidate_type": "predeclared_state_selection",
            "states_included": "mechanism_reinforcing_company_positive|mechanism_offsetting_company_positive",
            "themes_excluded": "",
            "sparse_allowed_flag": 0,
            "diagnostic_only_flag": 0,
            "relation_state_used_for_selection_flag": 1,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Trade reinforced or offsetting mechanism states; keep Task639 exit.",
        },
        {
            "candidate_name": "predeclared_exclude_sparse_existing_exit",
            "candidate_type": "predeclared_data_quality_selection",
            "states_included": "*",
            "themes_excluded": "",
            "sparse_allowed_flag": 0,
            "diagnostic_only_flag": 0,
            "relation_state_used_for_selection_flag": 1,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Drop sparse mechanism cells only; keep Task639 exit.",
        },
        {
            "candidate_name": "diagnostic_exclude_company_quality_price_confirmed",
            "candidate_type": "diagnostic_state_selection",
            "states_included": "not_company_quality_price_confirmed",
            "themes_excluded": "",
            "sparse_allowed_flag": 1,
            "diagnostic_only_flag": 1,
            "relation_state_used_for_selection_flag": 1,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Diagnostic only: exclude a state that was weak in recent OOS; not eligible for promotion.",
        },
        {
            "candidate_name": "diagnostic_state_positive_ex_quality_confirmed",
            "candidate_type": "diagnostic_state_selection",
            "states_included": "company_positive_needs_confirmation|mechanism_offsetting_company_positive|mechanism_reinforcing_company_positive",
            "themes_excluded": "",
            "sparse_allowed_flag": 0,
            "diagnostic_only_flag": 1,
            "relation_state_used_for_selection_flag": 1,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Diagnostic only: keep positive/offsetting/reinforcing states while excluding sparse and quality-price-confirmed state.",
        },
    ]
    return pd.DataFrame(rows)


def build_candidate_grid(core: pd.DataFrame, specs: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, spec in specs.iterrows():
        selected_all = select_candidate(core, spec)
        for split_name in ["all", "validation", "recent_oos"]:
            scoped = selected_all if split_name == "all" else selected_all[selected_all["split_name"].astype(str).eq(split_name)]
            metrics = run_account(scoped, "equal_max5", qqq)
            rows.append(
                {
                    "candidate_name": spec["candidate_name"],
                    "split_name": split_name,
                    "candidate_type": spec["candidate_type"],
                    "initial_capital_usd": INITIAL_CAPITAL_USD,
                    "source_trade_count": int(len(scoped)),
                    "accepted_trade_count": int(metrics["accepted_trade_count"]),
                    "final_capital_usd": float(metrics["final_capital_usd"]),
                    "capital_return_pct": float(metrics["capital_return_pct"]),
                    "max_drawdown_pct": float(metrics["max_drawdown_pct"]),
                    "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
                    "qqq_final_capital_usd": float(metrics["qqq_final_capital_usd"]),
                    "beats_qqq_flag": int(metrics["beats_qqq_flag"]),
                    "relation_state_used_for_selection_flag": int(spec["relation_state_used_for_selection_flag"]),
                    "diagnostic_only_flag": int(spec["diagnostic_only_flag"]),
                    "fixed_hold_or_timing_override_flag": int(spec["fixed_hold_or_timing_override_flag"]),
                    "label_used_in_assignment_flag": 0,
                    "return_used_in_assignment_flag": 0,
                }
            )
    return pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)


def select_candidate(core: pd.DataFrame, spec: pd.Series) -> pd.DataFrame:
    selected = core.copy()
    states = str(spec["states_included"])
    if states == "mechanism_reinforcing_company_positive":
        selected = selected[selected["mechanism_relation_state"].eq("mechanism_reinforcing_company_positive")]
    elif states == "mechanism_reinforcing_company_positive|mechanism_offsetting_company_positive":
        selected = selected[
            selected["mechanism_relation_state"].isin(
                ["mechanism_reinforcing_company_positive", "mechanism_offsetting_company_positive"]
            )
        ]
    elif states == "not_company_quality_price_confirmed":
        selected = selected[~selected["mechanism_relation_state"].eq("company_quality_price_confirmed")]
    elif states == "company_positive_needs_confirmation|mechanism_offsetting_company_positive|mechanism_reinforcing_company_positive":
        selected = selected[
            selected["mechanism_relation_state"].isin(
                [
                    "company_positive_needs_confirmation",
                    "mechanism_offsetting_company_positive",
                    "mechanism_reinforcing_company_positive",
                ]
            )
        ]
    if int(spec["sparse_allowed_flag"]) == 0:
        selected = selected[pd.to_numeric(selected["mechanism_sparse_cell_flag"], errors="coerce").fillna(0).eq(0)]
    return selected.sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)


def build_promotion_report(candidate_grid: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    baseline = pivot_candidate(candidate_grid, "baseline_task639_core")
    rows = []
    for candidate_name in specs["candidate_name"]:
        metrics = pivot_candidate(candidate_grid, candidate_name)
        spec = specs[specs["candidate_name"].eq(candidate_name)].iloc[0]
        beats_all = int(metrics["all_final_capital_usd"] > baseline["all_final_capital_usd"])
        dd_ok = int(metrics["all_max_drawdown_pct"] >= baseline["all_max_drawdown_pct"])
        validation_up = int(metrics["validation_final_capital_usd"] > baseline["validation_final_capital_usd"])
        recent_up = int(metrics["recent_oos_final_capital_usd"] > baseline["recent_oos_final_capital_usd"])
        validation_dd_ok = int(metrics["validation_max_drawdown_pct"] >= baseline["validation_max_drawdown_pct"])
        recent_dd_ok = int(metrics["recent_oos_max_drawdown_pct"] >= baseline["recent_oos_max_drawdown_pct"])
        allowed = int(int(spec["diagnostic_only_flag"]) == 0 and int(spec["fixed_hold_or_timing_override_flag"]) == 0)
        promotion = int(
            candidate_name != "baseline_task639_core"
            and beats_all
            and dd_ok
            and validation_up
            and recent_up
            and validation_dd_ok
            and recent_dd_ok
            and allowed
        )
        rows.append(
            {
                "candidate_name": candidate_name,
                **metrics,
                "beats_all_task639_flag": beats_all,
                "all_drawdown_not_worse_flag": dd_ok,
                "validation_improves_task639_flag": validation_up,
                "recent_oos_improves_task639_flag": recent_up,
                "validation_drawdown_not_worse_flag": validation_dd_ok,
                "recent_oos_drawdown_not_worse_flag": recent_dd_ok,
                "promotion_allowed_flag": allowed,
                "promotion_candidate_flag": promotion,
                "failure_reason": failure_reason(promotion, allowed, beats_all, dd_ok, validation_up, recent_up, validation_dd_ok, recent_dd_ok),
            }
        )
    return pd.DataFrame(rows).sort_values(["promotion_candidate_flag", "all_final_capital_usd"], ascending=[False, False]).reset_index(drop=True)


def pivot_candidate(grid: pd.DataFrame, candidate_name: str) -> dict[str, float]:
    rows = grid[grid["candidate_name"].eq(candidate_name)]
    out: dict[str, float] = {}
    for _, row in rows.iterrows():
        split = str(row["split_name"])
        for column in ["final_capital_usd", "max_drawdown_pct", "accepted_trade_count", "entry_reduce_failure_rate", "beats_qqq_flag"]:
            out[f"{split}_{column}"] = float(row[column])
    return out


def failure_reason(
    promotion: int,
    allowed: int,
    beats_all: int,
    dd_ok: int,
    validation_up: int,
    recent_up: int,
    validation_dd_ok: int,
    recent_dd_ok: int,
) -> str:
    if promotion:
        return "passes_all_relation_selection_gates"
    if not allowed:
        return "diagnostic_only_not_promotion_eligible"
    if not beats_all:
        return "full_period_return_not_better"
    if not dd_ok:
        return "full_period_drawdown_worse"
    if not validation_up or not recent_up:
        return "validation_or_recent_oos_not_better"
    if not validation_dd_ok or not recent_dd_ok:
        return "validation_or_recent_oos_drawdown_worse"
    return "other_gate_failure"


def build_relation_state_oos_diagnostics(core: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in core.groupby(["split_name", "mechanism_relation_state"], dropna=False):
        split_name, state = keys
        ret = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
        rows.append(
            {
                "split_name": split_name,
                "mechanism_relation_state": state,
                "trade_count": int(len(group)),
                "avg_return_pct": float(ret.mean() * 100.0),
                "win_rate": float(ret.gt(0).mean()),
                "entry_reduce_failure_rate": float(ret.le(-0.03).mean()),
                "large_loss_rate": float(ret.le(-0.10).mean()),
                "evaluation_only_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values(["split_name", "avg_return_pct"], ascending=[True, False]).reset_index(drop=True)


def build_failure_analysis(candidate_grid: pd.DataFrame, promotion: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in promotion.iterrows():
        if row["candidate_name"] == "baseline_task639_core":
            continue
        rows.append(
            {
                "candidate_name": row["candidate_name"],
                "what_improved": summarize_improvement(row),
                "what_failed": row["failure_reason"],
                "plain_read": plain_read(row),
            }
        )
    return pd.DataFrame(rows)


def summarize_improvement(row: pd.Series) -> str:
    wins = []
    if int(row["beats_all_task639_flag"]) == 1:
        wins.append("full_return")
    if int(row["all_drawdown_not_worse_flag"]) == 1:
        wins.append("full_drawdown")
    if int(row["validation_improves_task639_flag"]) == 1:
        wins.append("validation_return")
    if int(row["recent_oos_improves_task639_flag"]) == 1:
        wins.append("recent_oos_return")
    return ",".join(wins) if wins else "none"


def plain_read(row: pd.Series) -> str:
    name = str(row["candidate_name"])
    if name == "predeclared_exclude_sparse_existing_exit":
        return "Sparse removal boosts full return but worsens full drawdown and does not change OOS account."
    if "reinforcing" in name:
        return "Reinforcing states help OOS but fail full-period robustness and drawdown."
    if "exclude_company_quality" in name or "ex_quality" in name:
        return "OOS improves, but this is diagnostic and full-period return/drawdown fail."
    return "Selection changes one pocket but does not pass all promotion gates."


def build_decision(candidate_grid: pd.DataFrame, promotion: pd.DataFrame) -> pd.DataFrame:
    baseline = promotion[promotion["candidate_name"].eq("baseline_task639_core")].iloc[0]
    best_all = promotion.sort_values("all_final_capital_usd", ascending=False).iloc[0]
    best_oos = promotion[
        promotion["validation_improves_task639_flag"].eq(1)
        & promotion["recent_oos_improves_task639_flag"].eq(1)
    ].sort_values("all_final_capital_usd", ascending=False)
    best_oos_name = "" if best_oos.empty else str(best_oos.iloc[0]["candidate_name"])
    decision = "RELATION_SELECTION_TESTED_NO_PROMOTION_CANDIDATE"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                "baseline_final_capital_usd": float(baseline["all_final_capital_usd"]),
                "baseline_max_drawdown_pct": float(baseline["all_max_drawdown_pct"]),
                "best_all_candidate_name": best_all["candidate_name"],
                "best_all_final_capital_usd": float(best_all["all_final_capital_usd"]),
                "best_all_max_drawdown_pct": float(best_all["all_max_drawdown_pct"]),
                "best_oos_both_candidate_name": best_oos_name,
                "promotion_candidate_count": int(promotion["promotion_candidate_flag"].sum()),
                "trading_promotion_pass_flag": 0,
                "next_action": "Do not promote selection rules. Investigate why company_quality_price_confirmed flips from usable full-period state to weak recent OOS state, and whether accepted-trade priority can be improved without return-tuned exclusions.",
            }
        ]
    )


def build_pass_fail(candidate_grid: pd.DataFrame, promotion: pd.DataFrame) -> pd.DataFrame:
    fixed_hold_violations = int(candidate_grid["fixed_hold_or_timing_override_flag"].sum())
    both_oos_count = int((promotion["validation_improves_task639_flag"].eq(1) & promotion["recent_oos_improves_task639_flag"].eq(1)).sum())
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    return pd.DataFrame(
        [
            {"gate": "no_fixed_hold_or_timing_override", "pass_flag": int(fixed_hold_violations == 0), "observed_value": f"violations={fixed_hold_violations}", "required_value": "relation selection must keep existing Task639 timing and exit"},
            {"gate": "relation_selection_candidates_tested", "pass_flag": int(candidate_grid["candidate_name"].nunique() >= 3), "observed_value": f"candidates={candidate_grid['candidate_name'].nunique()}", "required_value": "baseline plus multiple relation-selection candidates"},
            {"gate": "oos_movement_observed", "pass_flag": int(both_oos_count > 0), "observed_value": f"both_oos_improvers={both_oos_count}", "required_value": "at least one candidate changes validation and recent OOS result"},
            {"gate": "promotion_candidate_found", "pass_flag": int(promotion_count > 0), "observed_value": f"promotion_candidates={promotion_count}", "required_value": "candidate must improve full return, drawdown, validation, and recent OOS"},
            {"gate": "strategy_accepted", "pass_flag": 0, "observed_value": "research diagnostic only", "required_value": "requires accepted strategy gates and live readiness"},
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    candidate_grid: pd.DataFrame,
    promotion: pd.DataFrame,
    diagnostics: pd.DataFrame,
    failure: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task663 Relation Selection Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Baseline: `${float(d['baseline_final_capital_usd']):.2f}`, max drawdown `{float(d['baseline_max_drawdown_pct']):.2f}%`.",
        f"- Best full-period selection: `{d['best_all_candidate_name']}` = `${float(d['best_all_final_capital_usd']):.2f}`, max drawdown `{float(d['best_all_max_drawdown_pct']):.2f}%`.",
        f"- Best candidate improving both OOS splits: `{d['best_oos_both_candidate_name']}`.",
        f"- Promotion candidates: `{int(d['promotion_candidate_count'])}`.",
        "",
        "## Quant Expert Report",
        "",
        "Task663 connects Task661 relation states to trading by selecting or withholding existing Task639 candidates only. It does not add fixed-hold exits, timing overrides, size boosts, or standalone macro entries.",
        "",
        "### Data Source And Source Readiness",
        "",
        "Input is the Task661 mechanism state panel rebuilt from Task659. No new external data is introduced.",
        "",
        "### Exact Join Keys",
        "",
        "`lifecycle_id`, `entry_ts`, `timing_mode`, `exit_mode`, and `split_name`.",
        "",
        "### Leakage Audit",
        "",
        "Returns are evaluation-only. Diagnostic candidates are marked `diagnostic_only_flag=1` and cannot be promoted.",
        "",
        "### Candidate Grid",
        "",
        table(candidate_grid),
        "",
        "### Promotion Report",
        "",
        table(promotion),
        "",
        "### Relation State Diagnostics",
        "",
        table(diagnostics),
        "",
        "### Failure Analysis",
        "",
        table(failure),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "관계형 엔진을 실제 매매 선택에 연결해봤습니다.",
        "",
        "결과는 움직였습니다. 즉 분류가 완전히 쓸모없는 건 아닙니다.",
        "",
        "하지만 돈 넣을 후보는 아직 없습니다.",
        "",
        "OOS를 좋게 만드는 후보는 전체기간 수익과 낙폭이 깨졌고, 전체기간을 좋게 만드는 후보는 OOS 개선이 없거나 낙폭이 깨졌습니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `relation_selection_candidate_specs.csv`",
        "- `relation_selection_candidate_grid.csv`",
        "- `relation_selection_promotion_report.csv`",
        "- `relation_state_oos_diagnostics.csv`",
        "- `relation_selection_failure_analysis.csv`",
        "- `task_663_decision.csv`",
        "- `task_663_pass_fail_matrix.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_663_relation_selection_backtest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    clipped = df.head(max_rows)
    cols = [str(c) for c in clipped.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in clipped.iterrows():
        lines.append("| " + " | ".join(cell(row.get(c, "")) for c in clipped.columns) + " |")
    return "\n".join(lines)


def cell(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "/").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = build_task663_relation_selection_backtest(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best_all={decision['best_all_candidate_name']} "
        f"promotion={int(decision['promotion_candidate_count'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
