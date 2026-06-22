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


TASK_ID = "Task657"
REPORT_DIR = Path("docs/reports/task_657_soft_macro_relation_backtest")
EXECUTION_PANEL = Path("docs/reports/task_638_content_signal_refinement/task_638_timing_exit_execution_panel.csv")
MACRO_CONTEXT = Path("docs/reports/task_655_macro_asof_release_repair/task_655_macro_asof_context_panel.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
TASK656_PERMISSION = Path("docs/reports/task_656_macro_pragmatic_policy/task_656_relation_permission_matrix.csv")
QQQ_PATH = Path("data/raw/us_daily_breadth_top500/QQQ.csv")


def build_task657_soft_macro_relation_backtest(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    macro_context_path: Path = MACRO_CONTEXT,
    task639_decision_path: Path = TASK639_DECISION,
    task656_permission_path: Path = TASK656_PERMISSION,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    execution = load_execution_panel(execution_panel_path)
    macro = load_macro_context(macro_context_path)
    tagged = attach_macro(execution, macro)
    baseline = task639_core(tagged)
    qqq = load_qqq_history(qqq_path)
    task639 = pd.read_csv(task639_decision_path).iloc[0]
    permission = pd.read_csv(task656_permission_path)

    candidate_grid = build_candidate_grid(tagged, qqq)
    split_grid = build_split_grid(tagged, qqq)
    diagnostics = build_macro_diagnostics(baseline)
    permission_audit = build_permission_audit(candidate_grid, permission)
    promotion = build_promotion_report(candidate_grid, split_grid, task639, permission_audit)
    pass_fail = build_pass_fail(candidate_grid, split_grid, promotion, permission_audit)
    decision = build_decision(candidate_grid, split_grid, promotion, task639)

    tagged.to_csv(out_dir / "task_657_macro_tagged_execution_panel.csv", index=False, encoding="utf-8-sig")
    candidate_grid.to_csv(out_dir / "task_657_candidate_account_grid.csv", index=False, encoding="utf-8-sig")
    split_grid.to_csv(out_dir / "task_657_split_account_grid.csv", index=False, encoding="utf-8-sig")
    diagnostics.to_csv(out_dir / "task_657_macro_diagnostics.csv", index=False, encoding="utf-8-sig")
    permission_audit.to_csv(out_dir / "task_657_permission_audit.csv", index=False, encoding="utf-8-sig")
    promotion.to_csv(out_dir / "task_657_promotion_report.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_657_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_657_decision.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, candidate_grid, split_grid, diagnostics, promotion, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "tagged": tagged,
        "candidate_grid": candidate_grid,
        "split_grid": split_grid,
        "diagnostics": diagnostics,
        "permission_audit": permission_audit,
        "promotion": promotion,
        "pass_fail": pass_fail,
        "decision": decision,
    }


def load_execution_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        if column in panel.columns:
            panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    numeric_cols = [
        "positive_contract_customer_count",
        "content_supply_demand_flag",
        "net_return_from_entry",
        "holding_days",
        "same_day_exit_flag",
        "entry_reduce_failure_flag",
    ]
    for column in numeric_cols:
        if column in panel.columns:
            panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def load_macro_context(path: Path) -> pd.DataFrame:
    macro = pd.read_csv(path)
    for column in ["entry_ts"]:
        if column in macro.columns:
            macro[column] = pd.to_datetime(macro[column], utc=True, errors="coerce")
    for column in [
        "macro_series_available_count",
        "macro_release_timestamp_repaired_flag",
        "macro_asof_provisional_for_diagnostic_flag",
    ]:
        if column in macro.columns:
            macro[column] = pd.to_numeric(macro[column], errors="coerce").fillna(0)
    keep = [
        "lifecycle_id",
        "timing_mode",
        "exit_mode",
        "macro_series_available_count",
        "macro_employment_state",
        "macro_inflation_state",
        "macro_rates_state",
        "macro_dollar_state",
        "macro_oil_state",
        "macro_credit_state",
        "macro_liquidity_state",
        "macro_overall_state",
        "macro_action_modifier",
        "macro_release_timestamp_repaired_flag",
        "macro_asof_provisional_for_diagnostic_flag",
    ]
    return macro[[c for c in keep if c in macro.columns]].drop_duplicates(["lifecycle_id", "timing_mode", "exit_mode"]).copy()


def attach_macro(execution: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    out = execution.merge(macro, on=["lifecycle_id", "timing_mode", "exit_mode"], how="left")
    out["macro_overall_state"] = out["macro_overall_state"].fillna("macro_source_gap")
    out["macro_action_modifier"] = out["macro_action_modifier"].fillna("macro_source_gap")
    out["macro_release_timestamp_repaired_flag"] = pd.to_numeric(out.get("macro_release_timestamp_repaired_flag"), errors="coerce").fillna(0).astype(int)
    out["macro_asof_provisional_for_diagnostic_flag"] = pd.to_numeric(out.get("macro_asof_provisional_for_diagnostic_flag"), errors="coerce").fillna(0).astype(int)
    out["macro_pressure_score"] = out.apply(macro_pressure_score, axis=1)
    out["macro_support_score"] = out.apply(macro_support_score, axis=1)
    out["soft_macro_state"] = out.apply(soft_macro_state, axis=1)
    return out


def macro_pressure_score(row: pd.Series) -> int:
    states = [
        row.get("macro_employment_state"),
        row.get("macro_inflation_state"),
        row.get("macro_rates_state"),
        row.get("macro_dollar_state"),
        row.get("macro_oil_state"),
        row.get("macro_credit_state"),
        row.get("macro_liquidity_state"),
    ]
    pressure = {
        "growth_weakening",
        "inflation_pressure",
        "rates_pressure",
        "dollar_pressure",
        "oil_pressure",
        "credit_stress",
        "liquidity_tightening",
    }
    return int(sum(str(x) in pressure for x in states))


def macro_support_score(row: pd.Series) -> int:
    states = [
        row.get("macro_employment_state"),
        row.get("macro_inflation_state"),
        row.get("macro_rates_state"),
        row.get("macro_dollar_state"),
        row.get("macro_oil_state"),
        row.get("macro_credit_state"),
        row.get("macro_liquidity_state"),
    ]
    support = {
        "growth_supportive",
        "inflation_cooling",
        "rates_easing",
        "dollar_easing",
        "oil_easing",
        "credit_supportive",
        "liquidity_supportive",
    }
    return int(sum(str(x) in support for x in states))


def soft_macro_state(row: pd.Series) -> str:
    if int(row.get("macro_asof_provisional_for_diagnostic_flag", 0) or 0) == 0:
        return "macro_missing"
    if str(row.get("macro_overall_state")) == "macro_hostile" or int(row.get("macro_pressure_score", 0) or 0) >= 3:
        return "macro_pressure"
    if str(row.get("macro_overall_state")) == "macro_supportive" or int(row.get("macro_support_score", 0) or 0) >= 3:
        return "macro_supportive"
    return "macro_mixed"


def task639_core(panel: pd.DataFrame) -> pd.DataFrame:
    mask = (
        pd.to_numeric(panel.get("positive_contract_customer_count"), errors="coerce").fillna(0).gt(0)
        | pd.to_numeric(panel.get("content_supply_demand_flag"), errors="coerce").fillna(0).eq(1)
    )
    return panel[mask & panel["timing_mode"].eq("delay1d") & panel["exit_mode"].eq("existing_exit")].copy()


def build_candidate_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, selected in candidate_panels(panel).items():
        metrics = run_account(selected, "equal_max5", qqq)
        rows.append(row_from_metrics(name, "all", selected, metrics))
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def build_split_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows = []
    candidates = candidate_panels(panel)
    for split_name in ["validation", "recent_oos"]:
        split_panel = panel[panel["split_name"].astype(str).eq(split_name)].copy()
        for name, selected in candidate_panels(split_panel).items():
            metrics = run_account(selected, "equal_max5", qqq)
            rows.append(row_from_metrics(name, split_name, selected, metrics))
    return pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)


def candidate_panels(panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = task639_core(panel)
    if base.empty:
        return {"baseline_task639_core": base}
    by_lifecycle = base.set_index("lifecycle_id", drop=False)
    pressure_ids = set(base[base["soft_macro_state"].eq("macro_pressure")]["lifecycle_id"].astype(str))
    mixed_ids = set(base[base["soft_macro_state"].eq("macro_mixed")]["lifecycle_id"].astype(str))
    support_ids = set(base[base["soft_macro_state"].eq("macro_supportive")]["lifecycle_id"].astype(str))
    candidates = {"baseline_task639_core": base}
    candidates["soft_skip_macro_pressure"] = base[~base["lifecycle_id"].astype(str).isin(pressure_ids)].copy()
    candidates["soft_keep_supportive_mixed_only"] = base[base["lifecycle_id"].astype(str).isin(mixed_ids | support_ids)].copy()
    candidates["soft_supportive_only"] = base[base["lifecycle_id"].astype(str).isin(support_ids)].copy()
    candidates["soft_delay_pressure_1d_to_60m"] = replace_rows(base, panel, pressure_ids, "delay60m", "existing_exit")
    candidates["soft_delay_pressure_1d_to_vwap"] = replace_rows(base, panel, pressure_ids, "vwap_reclaim", "existing_exit")
    candidates["soft_pressure_hold5"] = replace_rows(base, panel, pressure_ids, "delay1d", "hold5")
    candidates["soft_pressure_hold10"] = replace_rows(base, panel, pressure_ids, "delay1d", "hold10")
    return candidates


def replace_rows(base: pd.DataFrame, panel: pd.DataFrame, lifecycle_ids: set[str], timing_mode: str, exit_mode: str) -> pd.DataFrame:
    keep = base[~base["lifecycle_id"].astype(str).isin(lifecycle_ids)].copy()
    replacements = panel[
        panel["lifecycle_id"].astype(str).isin(lifecycle_ids)
        & panel["timing_mode"].eq(timing_mode)
        & panel["exit_mode"].eq(exit_mode)
    ].copy()
    if replacements.empty:
        return keep
    return pd.concat([keep, replacements], ignore_index=True).sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)


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
        "beats_qqq_flag": int(metrics["beats_qqq_flag"]),
        "label_used_in_assignment_flag": 0,
        "return_used_in_assignment_flag": 0,
    }


def build_macro_diagnostics(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for state, group in base.groupby("soft_macro_state", dropna=False):
        ret = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
        rows.append(
            {
                "soft_macro_state": state,
                "row_count": int(len(group)),
                "avg_return_pct": float(ret.mean() * 100.0) if ret.notna().any() else 0.0,
                "win_rate": float(ret.gt(0).mean()) if ret.notna().any() else 0.0,
                "entry_reduce_failure_rate": float(ret.le(-0.03).mean()) if ret.notna().any() else 0.0,
                "large_loss_rate": float(ret.le(-0.10).mean()) if ret.notna().any() else 0.0,
                "evaluation_only_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("row_count", ascending=False).reset_index(drop=True)


def build_permission_audit(candidate_grid: pd.DataFrame, permission: pd.DataFrame) -> pd.DataFrame:
    allowed = permission[permission["permission"].isin(["ALLOWED_FOR_BACKTEST", "ALLOWED"])]["relation_use"].astype(str).tolist()
    rows = []
    for _, row in candidate_grid.iterrows():
        name = str(row["candidate_name"])
        forbidden = int(any(token in name for token in ["boost", "full_entry", "hard_block", "standalone"]))
        rows.append(
            {
                "candidate_name": name,
                "uses_only_soft_macro_permission_flag": int(forbidden == 0),
                "allowed_permission_basis": ",".join(allowed),
                "forbidden_macro_authority_used_flag": forbidden,
            }
        )
    return pd.DataFrame(rows)


def build_promotion_report(candidate_grid: pd.DataFrame, split_grid: pd.DataFrame, task639: pd.Series, permission_audit: pd.DataFrame) -> pd.DataFrame:
    baseline = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    rows = []
    for _, row in candidate_grid.iterrows():
        name = str(row["candidate_name"])
        validation = split_grid[split_grid["candidate_name"].eq(name) & split_grid["split_name"].eq("validation")].iloc[0]
        recent = split_grid[split_grid["candidate_name"].eq(name) & split_grid["split_name"].eq("recent_oos")].iloc[0]
        permission_ok = int(permission_audit[permission_audit["candidate_name"].eq(name)]["uses_only_soft_macro_permission_flag"].iloc[0])
        beats_baseline = int(float(row["final_capital_usd"]) > float(baseline["final_capital_usd"]))
        dd_better = int(float(row["max_drawdown_pct"]) > float(baseline["max_drawdown_pct"]))
        promotion = int(
            name != "baseline_task639_core"
            and beats_baseline
            and dd_better
            and int(validation["beats_qqq_flag"]) == 1
            and int(recent["beats_qqq_flag"]) == 1
            and permission_ok == 1
        )
        rows.append(
            {
                "candidate_name": name,
                "final_capital_usd": float(row["final_capital_usd"]),
                "max_drawdown_pct": float(row["max_drawdown_pct"]),
                "beats_task639_baseline_flag": beats_baseline,
                "drawdown_better_than_task639_flag": dd_better,
                "validation_beats_qqq_flag": int(validation["beats_qqq_flag"]),
                "recent_oos_beats_qqq_flag": int(recent["beats_qqq_flag"]),
                "soft_permission_pass_flag": permission_ok,
                "promotion_candidate_flag": promotion,
                "task639_reference_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "task639_reference_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
            }
        )
    return pd.DataFrame(rows).sort_values(["promotion_candidate_flag", "final_capital_usd"], ascending=[False, False]).reset_index(drop=True)


def build_pass_fail(candidate_grid: pd.DataFrame, split_grid: pd.DataFrame, promotion: pd.DataFrame, permission_audit: pd.DataFrame) -> pd.DataFrame:
    baseline = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    best_nonbase = candidate_grid[~candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    forbidden_count = int(permission_audit["forbidden_macro_authority_used_flag"].sum())
    return pd.DataFrame(
        [
            {"gate": "baseline_built", "pass_flag": int(len(baseline) > 0), "observed_value": f"baseline=${float(baseline['final_capital_usd']):.2f}", "required_value": "Task639 baseline must be present"},
            {"gate": "soft_macro_candidates_built", "pass_flag": int(len(candidate_grid) > 1), "observed_value": f"candidates={len(candidate_grid)}", "required_value": "multiple soft macro candidates"},
            {"gate": "permission_audit_pass", "pass_flag": int(forbidden_count == 0), "observed_value": f"forbidden={forbidden_count}", "required_value": "no hard block/full entry/size boost/standalone macro authority"},
            {"gate": "best_soft_candidate_beats_task639_return", "pass_flag": int(float(best_nonbase["final_capital_usd"]) > float(baseline["final_capital_usd"])), "observed_value": f"best_soft=${float(best_nonbase['final_capital_usd']):.2f}; baseline=${float(baseline['final_capital_usd']):.2f}", "required_value": "soft candidate must beat Task639 return"},
            {"gate": "best_soft_candidate_improves_drawdown", "pass_flag": int(float(best_nonbase["max_drawdown_pct"]) > float(baseline["max_drawdown_pct"])), "observed_value": f"best_soft_dd={float(best_nonbase['max_drawdown_pct']):.2f}; baseline_dd={float(baseline['max_drawdown_pct']):.2f}", "required_value": "soft candidate must improve drawdown"},
            {"gate": "promotion_candidate_found", "pass_flag": int(promotion_count > 0), "observed_value": f"promotion_candidates={promotion_count}", "required_value": "must beat baseline return/drawdown plus validation/recent QQQ and permission gates"},
            {"gate": "trading_promotion", "pass_flag": 0, "observed_value": "research backtest only", "required_value": "requires acceptance gates and live readiness"},
        ]
    )


def build_decision(candidate_grid: pd.DataFrame, split_grid: pd.DataFrame, promotion: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    baseline = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    best = candidate_grid.iloc[0]
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    verdict = "NO_SOFT_MACRO_RELATION_UPGRADE_KEEP_TASK639_BASELINE"
    if promotion_count > 0:
        verdict = "SOFT_MACRO_RELATION_RESEARCH_CANDIDATE_FOUND_NOT_ACCEPTED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": verdict,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                "task639_baseline_final_capital_usd": float(baseline["final_capital_usd"]),
                "task639_baseline_max_drawdown_pct": float(baseline["max_drawdown_pct"]),
                "best_candidate_name": best["candidate_name"],
                "best_candidate_final_capital_usd": float(best["final_capital_usd"]),
                "best_candidate_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "promotion_candidate_count": promotion_count,
                "task639_reference_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "task639_reference_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
                "trading_promotion_pass_flag": 0,
                "next_action": "Keep Task639 unless a soft macro candidate passes promotion. Use diagnostics to inspect whether macro_pressure should change confirmation or exit rules.",
            }
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    candidate_grid: pd.DataFrame,
    split_grid: pd.DataFrame,
    diagnostics: pd.DataFrame,
    promotion: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task657 Soft Macro Relation Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Task639 baseline: ${float(d['task639_baseline_final_capital_usd']):.2f}, max drawdown {float(d['task639_baseline_max_drawdown_pct']):.2f} percent.",
        f"- Best candidate: `{d['best_candidate_name']}` = ${float(d['best_candidate_final_capital_usd']):.2f}, max drawdown {float(d['best_candidate_max_drawdown_pct']):.2f} percent.",
        f"- Promotion candidates: {int(d['promotion_candidate_count'])}.",
        "- What changed: Task656 pragmatic macro context was retested as soft relation modifiers only.",
        "",
        "## Quant Expert Report",
        "",
        "Task657 joins Task638 execution variants with Task655 release-time repaired macro context. It tests only Task656-allowed soft uses: skip/confirm/delay/shorter-hold style candidates. It does not use macro for standalone entries, hard blocks, full entry, or size boosts.",
        "",
        "### Data Source And Source Readiness",
        "",
        "Macro context comes from Task655 and is release-time repaired but latest-vintage caveated. Therefore it is soft modifier only.",
        "",
        "### Exact Join Keys",
        "",
        "`lifecycle_id`, `timing_mode`, and `exit_mode`.",
        "",
        "### Leakage Audit",
        "",
        "Labels and realized returns are not used for assignment. Returns are used only in evaluation tables.",
        "",
        "### Split/OOS Metrics",
        "",
        table(split_grid),
        "",
        "### Failure Decomposition",
        "",
        table(diagnostics),
        "",
        "### Candidate Grid",
        "",
        table(candidate_grid),
        "",
        "### Promotion Eligibility",
        "",
        table(promotion),
        "",
        "### Remaining Blockers",
        "",
        table(pass_fail),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We reran the relation engine with macro attached.",
        "",
        "Macro was allowed to be careful, not powerful.",
        "",
        "The result tells us whether being more careful around bad macro helped more than it hurt.",
        "",
        "## Artifact Manifest",
        "",
        "- `task_657_macro_tagged_execution_panel.csv`",
        "- `task_657_candidate_account_grid.csv`",
        "- `task_657_split_account_grid.csv`",
        "- `task_657_macro_diagnostics.csv`",
        "- `task_657_permission_audit.csv`",
        "- `task_657_promotion_report.csv`",
        "- `task_657_pass_fail_matrix.csv`",
        "- `task_657_decision.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_657_soft_macro_relation_backtest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    result = build_task657_soft_macro_relation_backtest(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best={decision['best_candidate_name']} "
        f"final={float(decision['best_candidate_final_capital_usd']):.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
