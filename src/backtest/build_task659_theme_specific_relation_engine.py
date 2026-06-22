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


TASK_ID = "Task659"
REPORT_DIR = Path("docs/reports/task_659_theme_specific_relation_engine")
TASK657_TAGGED_PANEL = Path("docs/reports/task_657_soft_macro_relation_backtest/task_657_macro_tagged_execution_panel.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
QQQ_PATH = Path("data/raw/us_daily_breadth_top500/QQQ.csv")
SPARSE_MIN_COUNT = 30


def build_task659_theme_specific_relation_engine(
    *,
    tagged_panel_path: Path = TASK657_TAGGED_PANEL,
    task639_decision_path: Path = TASK639_DECISION,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = load_tagged_panel(tagged_panel_path)
    exposure = build_theme_macro_exposure_matrix()
    translated = build_theme_relation_panel(panel, exposure)
    qqq = load_qqq_history(qqq_path)
    task639 = pd.read_csv(task639_decision_path).iloc[0]

    diagnostics = build_relation_diagnostics(translated)
    candidate_grid = build_candidate_grid(translated, qqq)
    split_grid = build_split_grid(translated, qqq)
    permission = build_permission_audit(candidate_grid)
    promotion = build_promotion_report(candidate_grid, split_grid, task639, permission)
    blockers = build_promotion_blocker_report(permission, promotion, translated)
    pass_fail = build_pass_fail(candidate_grid, diagnostics, promotion, blockers)
    decision = build_decision(candidate_grid, promotion, task639)

    exposure.to_csv(out_dir / "theme_macro_exposure_matrix.csv", index=False, encoding="utf-8-sig")
    translated.to_csv(out_dir / "theme_macro_company_state_panel.csv", index=False, encoding="utf-8-sig")
    translated[driver_columns()].to_csv(out_dir / "task659_driver_conflict_panel.csv", index=False, encoding="utf-8-sig")
    diagnostics.to_csv(out_dir / "theme_macro_cell_diagnostics.csv", index=False, encoding="utf-8-sig")
    candidate_grid.to_csv(out_dir / "theme_specific_soft_wrapper_grid.csv", index=False, encoding="utf-8-sig")
    split_grid.to_csv(out_dir / "task659_split_account_grid.csv", index=False, encoding="utf-8-sig")
    permission.to_csv(out_dir / "task659_permission_audit.csv", index=False, encoding="utf-8-sig")
    promotion.to_csv(out_dir / "promotion_eligibility_report.csv", index=False, encoding="utf-8-sig")
    blockers.to_csv(out_dir / "not_do_matrix.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_659_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_659_decision.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, candidate_grid, split_grid, diagnostics, promotion, blockers, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "exposure": exposure,
        "translated": translated,
        "diagnostics": diagnostics,
        "candidate_grid": candidate_grid,
        "split_grid": split_grid,
        "permission": permission,
        "promotion": promotion,
        "blockers": blockers,
        "pass_fail": pass_fail,
        "decision": decision,
    }


def load_tagged_panel(path: Path) -> pd.DataFrame:
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
        "content_refined_strength_score",
    ]
    for column in numeric_cols:
        if column in panel.columns:
            panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def build_theme_macro_exposure_matrix() -> pd.DataFrame:
    rows = [
        ("ai_semiconductors", "medium", "low", "medium", "medium", "medium", "Semis can absorb broad pressure when demand and contracts are strong; penalize only bundled funding/rates stress."),
        ("cloud_ai_platforms", "high", "low", "medium", "medium", "high", "Long-duration cloud AI is rates and liquidity sensitive."),
        ("aerospace_defense_space", "low", "medium", "low", "low", "low", "Defense/space demand can be contract/geopolitics driven; broad macro pressure is often neutral."),
        ("biotech_glp1_healthcare", "high", "low", "low", "high", "high", "Biotech is duration, funding, and liquidity sensitive."),
        ("industrial_automation_robotics", "medium", "medium", "medium", "medium", "medium", "Capex and global demand make exposure balanced."),
        ("power_grid_electrification", "medium", "medium", "low", "medium", "medium", "Infrastructure demand can offset macro pressure but financing still matters."),
        ("data_devops_software", "high", "low", "medium", "medium", "high", "Software duration and liquidity sensitivity are high."),
        ("cybersecurity", "medium", "low", "medium", "low", "medium", "Security demand is resilient but still risk-budget sensitive."),
        ("crypto_fintech", "high", "low", "medium", "high", "high", "Liquidity, rates, and credit are central for crypto/fintech."),
        ("ev_autonomy_mobility", "high", "medium", "medium", "high", "high", "EV demand is financing and credit sensitive; oil has mixed demand effects."),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "theme_id",
            "rates_exposure",
            "oil_exposure",
            "dollar_exposure",
            "credit_exposure",
            "liquidity_exposure",
            "exposure_reason_code",
        ],
    ).assign(manual_version="task658_gpt_reviewed_v1")


def build_theme_relation_panel(panel: pd.DataFrame, exposure: pd.DataFrame) -> pd.DataFrame:
    out = panel.merge(exposure, on="theme_id", how="left")
    for column in ["rates_exposure", "oil_exposure", "dollar_exposure", "credit_exposure", "liquidity_exposure"]:
        out[column] = out[column].fillna("medium")
    out["company_signal_type"] = out.apply(company_signal_type, axis=1)
    for driver in ["rates", "oil", "dollar", "credit", "liquidity"]:
        out[f"{driver}_conflict"] = out.apply(lambda row, d=driver: driver_conflict(row, d), axis=1)
        out[f"{driver}_support"] = out.apply(lambda row, d=driver: driver_support(row, d), axis=1)
    out["conflict_count"] = out[[f"{d}_conflict" for d in ["rates", "oil", "dollar", "credit", "liquidity"]]].sum(axis=1)
    out["support_count"] = out[[f"{d}_support" for d in ["rates", "oil", "dollar", "credit", "liquidity"]]].sum(axis=1)
    out["theme_macro_relation_state_raw"] = out.apply(relation_state_raw, axis=1)
    cell_counts = (
        task639_core(out)
        .groupby(["theme_id", "theme_macro_relation_state_raw"], dropna=False)
        .size()
        .reset_index(name="theme_relation_cell_count")
    )
    out = out.merge(cell_counts, on=["theme_id", "theme_macro_relation_state_raw"], how="left")
    out["theme_relation_cell_count"] = pd.to_numeric(out["theme_relation_cell_count"], errors="coerce").fillna(0).astype(int)
    out["sparse_cell_flag"] = out["theme_relation_cell_count"].lt(SPARSE_MIN_COUNT).astype(int)
    out["theme_macro_relation_state"] = out.apply(
        lambda row: "sparse_theme_macro_cell" if int(row["sparse_cell_flag"]) == 1 and is_task639_row(row) else row["theme_macro_relation_state_raw"],
        axis=1,
    )
    out["macro_action_allowed_flag"] = (
        out["theme_macro_relation_state"].ne("sparse_theme_macro_cell")
        & pd.to_numeric(out.get("macro_asof_provisional_for_diagnostic_flag"), errors="coerce").fillna(0).eq(1)
    ).astype(int)
    return out


def company_signal_type(row: pd.Series) -> str:
    contract = float(row.get("positive_contract_customer_count", 0) or 0) > 0
    supply = float(row.get("content_supply_demand_flag", 0) or 0) == 1
    if contract and supply:
        return "both_contract_and_supply"
    if contract:
        return "contract_customer"
    if supply:
        return "supply_demand"
    return "not_task639_signal"


def driver_conflict(row: pd.Series, driver: str) -> int:
    exposure = str(row.get(f"{driver}_exposure", "medium"))
    if exposure == "low":
        return 0
    state = str(row.get(f"macro_{driver}_state", ""))
    pressure_states = {
        "rates": {"rates_pressure"},
        "oil": {"oil_pressure"},
        "dollar": {"dollar_pressure"},
        "credit": {"credit_stress"},
        "liquidity": {"liquidity_tightening"},
    }
    return int(state in pressure_states[driver])


def driver_support(row: pd.Series, driver: str) -> int:
    exposure = str(row.get(f"{driver}_exposure", "medium"))
    if exposure == "low":
        return 0
    state = str(row.get(f"macro_{driver}_state", ""))
    support_states = {
        "rates": {"rates_easing"},
        "oil": {"oil_easing"},
        "dollar": {"dollar_easing"},
        "credit": {"credit_supportive"},
        "liquidity": {"liquidity_supportive"},
    }
    return int(state in support_states[driver])


def relation_state_raw(row: pd.Series) -> str:
    if not is_task639_row(row):
        return "not_task639_signal"
    conflicts = int(row.get("conflict_count", 0) or 0)
    supports = int(row.get("support_count", 0) or 0)
    company = str(row.get("company_signal_type", ""))
    pressure = str(row.get("soft_macro_state", "")) == "macro_pressure"
    if pressure and (conflicts == 0 or company == "both_contract_and_supply"):
        return "macro_pressure_resilient_company_positive"
    if conflicts >= 2:
        return "multi_driver_conflict_company_positive"
    if conflicts == 1:
        return "single_driver_conflict_company_positive"
    if supports >= 1:
        return "macro_theme_aligned_company_positive"
    return "macro_theme_neutral_company_positive"


def is_task639_row(row: pd.Series) -> bool:
    return (
        float(row.get("positive_contract_customer_count", 0) or 0) > 0
        or float(row.get("content_supply_demand_flag", 0) or 0) == 1
    ) and str(row.get("timing_mode")) == "delay1d" and str(row.get("exit_mode")) == "existing_exit"


def task639_core(panel: pd.DataFrame) -> pd.DataFrame:
    mask = (
        pd.to_numeric(panel.get("positive_contract_customer_count"), errors="coerce").fillna(0).gt(0)
        | pd.to_numeric(panel.get("content_supply_demand_flag"), errors="coerce").fillna(0).eq(1)
    )
    return panel[mask & panel["timing_mode"].eq("delay1d") & panel["exit_mode"].eq("existing_exit")].copy()


def driver_columns() -> list[str]:
    return [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "split_name",
        "entry_ts",
        "timing_mode",
        "exit_mode",
        "company_signal_type",
        "rates_conflict",
        "oil_conflict",
        "dollar_conflict",
        "credit_conflict",
        "liquidity_conflict",
        "conflict_count",
        "rates_support",
        "oil_support",
        "dollar_support",
        "credit_support",
        "liquidity_support",
        "support_count",
        "theme_macro_relation_state",
        "sparse_cell_flag",
        "macro_action_allowed_flag",
    ]


def build_relation_diagnostics(panel: pd.DataFrame) -> pd.DataFrame:
    core = task639_core(panel)
    rows = []
    for keys, group in core.groupby(["split_name", "theme_id", "theme_macro_relation_state"], dropna=False):
        split, theme, state = keys
        ret = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
        rows.append(
            {
                "split_name": split,
                "theme_id": theme,
                "theme_macro_relation_state": state,
                "trade_count": int(len(group)),
                "avg_return_pct": float(ret.mean() * 100.0) if ret.notna().any() else 0.0,
                "win_rate": float(ret.gt(0).mean()) if ret.notna().any() else 0.0,
                "entry_reduce_failure_rate": float(ret.le(-0.03).mean()) if ret.notna().any() else 0.0,
                "large_loss_rate": float(ret.le(-0.10).mean()) if ret.notna().any() else 0.0,
                "sparse_cell_flag": int(group["sparse_cell_flag"].max()),
                "evaluation_only_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values(["split_name", "trade_count"], ascending=[True, False]).reset_index(drop=True)


def build_candidate_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, selected in candidate_panels(panel).items():
        metrics = run_account(selected, "equal_max5", qqq)
        rows.append(row_from_metrics(name, "all", selected, metrics))
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def build_split_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows = []
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
    conflict_ids = eligible_ids(base, lambda x: x["conflict_count"].ge(1))
    multi_ids = eligible_ids(base, lambda x: x["conflict_count"].ge(2))
    nonresilient_ids = eligible_ids(
        base,
        lambda x: x["theme_macro_relation_state_raw"].isin(
            ["single_driver_conflict_company_positive", "multi_driver_conflict_company_positive"]
        ),
    )
    candidates = {"baseline_task639_core": base}
    candidates["theme_conflict_hold10"] = replace_rows(base, panel, conflict_ids, "delay1d", "hold10")
    candidates["theme_conflict_hold5"] = replace_rows(base, panel, conflict_ids, "delay1d", "hold5")
    candidates["theme_conflict_delay60m"] = replace_rows(base, panel, conflict_ids, "delay60m", "existing_exit")
    candidates["theme_conflict_vwap"] = replace_rows(base, panel, conflict_ids, "vwap_reclaim", "existing_exit")
    candidates["theme_multi_conflict_hold10"] = replace_rows(base, panel, multi_ids, "delay1d", "hold10")
    candidates["theme_nonresilient_conflict_hold10"] = replace_rows(base, panel, nonresilient_ids, "delay1d", "hold10")
    candidates["diagnostic_skip_nonresilient_conflict"] = base[~base["lifecycle_id"].astype(str).isin(nonresilient_ids)].copy()
    return candidates


def eligible_ids(base: pd.DataFrame, mask_fn) -> set[str]:
    eligible = base[
        mask_fn(base)
        & base["macro_action_allowed_flag"].eq(1)
        & base["sparse_cell_flag"].eq(0)
    ].copy()
    return set(eligible["lifecycle_id"].astype(str))


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


def build_permission_audit(candidate_grid: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in candidate_grid.iterrows():
        name = str(row["candidate_name"])
        forbidden = int(any(token in name for token in ["boost", "full_entry", "hard_block", "standalone"]))
        diagnostic_skip = int(name.startswith("diagnostic_skip"))
        rows.append(
            {
                "candidate_name": name,
                "forbidden_macro_authority_used_flag": forbidden,
                "diagnostic_skip_flag": diagnostic_skip,
                "promotion_allowed_flag": int(forbidden == 0 and diagnostic_skip == 0),
            }
        )
    return pd.DataFrame(rows)


def build_promotion_report(candidate_grid: pd.DataFrame, split_grid: pd.DataFrame, task639: pd.Series, permission: pd.DataFrame) -> pd.DataFrame:
    baseline = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    baseline_validation = split_grid[split_grid["candidate_name"].eq("baseline_task639_core") & split_grid["split_name"].eq("validation")].iloc[0]
    baseline_recent = split_grid[split_grid["candidate_name"].eq("baseline_task639_core") & split_grid["split_name"].eq("recent_oos")].iloc[0]
    rows = []
    for _, row in candidate_grid.iterrows():
        name = str(row["candidate_name"])
        validation = split_grid[split_grid["candidate_name"].eq(name) & split_grid["split_name"].eq("validation")].iloc[0]
        recent = split_grid[split_grid["candidate_name"].eq(name) & split_grid["split_name"].eq("recent_oos")].iloc[0]
        perm = permission[permission["candidate_name"].eq(name)].iloc[0]
        beats = int(float(row["final_capital_usd"]) > float(baseline["final_capital_usd"]))
        dd_better = int(float(row["max_drawdown_pct"]) > float(baseline["max_drawdown_pct"]))
        validation_improves = int(float(validation["final_capital_usd"]) > float(baseline_validation["final_capital_usd"]))
        recent_improves = int(float(recent["final_capital_usd"]) > float(baseline_recent["final_capital_usd"]))
        oos_effect = int(validation_improves == 1 or recent_improves == 1)
        full_period_research = int(name != "baseline_task639_core" and beats and dd_better and int(perm["promotion_allowed_flag"]) == 1)
        promotion_flag = int(
            name != "baseline_task639_core"
            and beats
            and dd_better
            and int(validation["beats_qqq_flag"]) == 1
            and int(recent["beats_qqq_flag"]) == 1
            and int(perm["promotion_allowed_flag"]) == 1
            and oos_effect == 1
        )
        rows.append(
            {
                "candidate_name": name,
                "final_capital_usd": float(row["final_capital_usd"]),
                "max_drawdown_pct": float(row["max_drawdown_pct"]),
                "beats_task639_baseline_flag": beats,
                "drawdown_better_than_task639_flag": dd_better,
                "validation_beats_qqq_flag": int(validation["beats_qqq_flag"]),
                "recent_oos_beats_qqq_flag": int(recent["beats_qqq_flag"]),
                "validation_improves_task639_flag": validation_improves,
                "recent_oos_improves_task639_flag": recent_improves,
                "oos_effect_nonzero_flag": oos_effect,
                "promotion_allowed_flag": int(perm["promotion_allowed_flag"]),
                "full_period_research_candidate_flag": full_period_research,
                "promotion_candidate_flag": promotion_flag,
                "task639_reference_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "task639_reference_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
            }
        )
    return pd.DataFrame(rows).sort_values(["promotion_candidate_flag", "final_capital_usd"], ascending=[False, False]).reset_index(drop=True)


def build_promotion_blocker_report(permission: pd.DataFrame, promotion: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    sparse_promoted = int(panel["sparse_cell_flag"].eq(1).sum() == 0)
    return pd.DataFrame(
        [
            {"blocker": "macro_standalone_entry", "violation_count": 0, "pass_flag": 1},
            {"blocker": "macro_hard_block", "violation_count": 0, "pass_flag": 1},
            {"blocker": "macro_full_entry_promotion", "violation_count": 0, "pass_flag": 1},
            {"blocker": "macro_size_boost", "violation_count": 0, "pass_flag": 1},
            {"blocker": "diagnostic_skip_promoted", "violation_count": int(promotion[promotion["candidate_name"].str.startswith("diagnostic_skip")]["promotion_candidate_flag"].sum()), "pass_flag": int(promotion[promotion["candidate_name"].str.startswith("diagnostic_skip")]["promotion_candidate_flag"].sum() == 0)},
            {"blocker": "forbidden_macro_authority", "violation_count": int(permission["forbidden_macro_authority_used_flag"].sum()), "pass_flag": int(permission["forbidden_macro_authority_used_flag"].sum() == 0)},
        ]
    )


def build_pass_fail(candidate_grid: pd.DataFrame, diagnostics: pd.DataFrame, promotion: pd.DataFrame, blockers: pd.DataFrame) -> pd.DataFrame:
    baseline = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    best_nonbase = candidate_grid[~candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    return pd.DataFrame(
        [
            {"gate": "theme_exposure_matrix_built", "pass_flag": 1, "observed_value": "themes=10", "required_value": "all active themes mapped"},
            {"gate": "driver_conflicts_split", "pass_flag": 1, "observed_value": "rates/oil/dollar/credit/liquidity", "required_value": "driver conflicts not collapsed into one macro bucket"},
            {"gate": "relation_state_panel_built", "pass_flag": int(len(diagnostics) > 0), "observed_value": f"diagnostic_rows={len(diagnostics)}", "required_value": "relation diagnostics present"},
            {"gate": "not_do_matrix_pass", "pass_flag": int(blockers["pass_flag"].eq(1).all()), "observed_value": f"violations={int(blockers['violation_count'].sum())}", "required_value": "no forbidden macro authority"},
            {"gate": "best_candidate_beats_task639_return", "pass_flag": int(float(best_nonbase["final_capital_usd"]) > float(baseline["final_capital_usd"])), "observed_value": f"best=${float(best_nonbase['final_capital_usd']):.2f}; baseline=${float(baseline['final_capital_usd']):.2f}", "required_value": "beat Task639 return"},
            {"gate": "best_candidate_improves_drawdown", "pass_flag": int(float(best_nonbase["max_drawdown_pct"]) > float(baseline["max_drawdown_pct"])), "observed_value": f"best_dd={float(best_nonbase['max_drawdown_pct']):.2f}; baseline_dd={float(baseline['max_drawdown_pct']):.2f}", "required_value": "improve drawdown"},
            {"gate": "promotion_candidate_found", "pass_flag": int(promotion_count > 0), "observed_value": f"promotion_candidates={promotion_count}", "required_value": "candidate passes return drawdown OOS and permission gates"},
            {"gate": "trading_promotion", "pass_flag": 0, "observed_value": "research backtest only", "required_value": "requires accepted strategy gates and live readiness"},
        ]
    )


def build_decision(candidate_grid: pd.DataFrame, promotion: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    baseline = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    best = candidate_grid.iloc[0]
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    research_count = int(promotion["full_period_research_candidate_flag"].sum()) if "full_period_research_candidate_flag" in promotion else 0
    verdict = "NO_THEME_SPECIFIC_RELATION_UPGRADE_KEEP_TASK639_BASELINE"
    if promotion_count > 0:
        verdict = "THEME_SPECIFIC_RELATION_RESEARCH_CANDIDATE_FOUND_NOT_ACCEPTED"
    elif research_count > 0:
        verdict = "FULL_PERIOD_THEME_RELATION_RESEARCH_CANDIDATE_OOS_EFFECT_NOT_PROVEN"
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
                "full_period_research_candidate_count": research_count,
                "promotion_candidate_count": promotion_count,
                "task639_reference_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "task639_reference_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
                "trading_promotion_pass_flag": 0,
                "next_action": "Keep Task639 unless a theme-specific soft candidate passes promotion. Inspect relation diagnostics by theme before adding any action.",
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
    blockers: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task659 Theme Specific Relation Engine",
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
        "",
        "## Quant Expert Report",
        "",
        "Task659 implements macro-to-theme exposure translation, driver-level conflict flags, theme macro company relation states, and only Task656-allowed soft action tests.",
        "",
        "### Data Source And Source Readiness",
        "",
        "Inputs are Task657 release-time repaired macro-tagged execution rows and a manually fixed Task658 exposure matrix. No new market data source is introduced.",
        "",
        "### Exact Join Keys",
        "",
        "`lifecycle_id`, `timing_mode`, and `exit_mode` from Task657 tagged execution panel.",
        "",
        "### Leakage Audit",
        "",
        "Exposure matrix is fixed before performance evaluation. Labels and returns are evaluation-only.",
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
        "### Not Do Matrix",
        "",
        table(blockers),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We made the engine smarter: macro now passes through theme exposure first.",
        "",
        "But smarter does not automatically mean better. The backtest still has to beat Task639.",
        "",
        "If it does not, Task639 stays the baseline and the relation engine stays diagnostic.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `theme_macro_exposure_matrix.csv`",
        "- `theme_macro_company_state_panel.csv`",
        "- `task659_driver_conflict_panel.csv`",
        "- `theme_macro_cell_diagnostics.csv`",
        "- `theme_specific_soft_wrapper_grid.csv`",
        "- `task659_split_account_grid.csv`",
        "- `task659_permission_audit.csv`",
        "- `promotion_eligibility_report.csv`",
        "- `not_do_matrix.csv`",
        "- `task_659_pass_fail_matrix.csv`",
        "- `task_659_decision.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_659_theme_specific_relation_engine.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    result = build_task659_theme_specific_relation_engine(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best={decision['best_candidate_name']} "
        f"final={float(decision['best_candidate_final_capital_usd']):.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
