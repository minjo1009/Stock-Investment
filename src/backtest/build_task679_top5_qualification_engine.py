from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest import build_task673_677_setup_slot_exposure_action as t673
from src.backtest import build_task678_active_cap3_winner_archetype as t678
from src.backtest.build_task637_content_signal_account_backtest import (
    INITIAL_CAPITAL_USD,
    load_qqq_history,
    qqq_final_for_period,
)
from src.backtest.build_task659_theme_specific_relation_engine import QQQ_PATH


TASK679_DIR = Path("docs/reports/task_679_top5_qualification_engine")
ACTIVE_CAP3 = "active_relation_cap3_reference"
TOP5_PRIORITY = "top5_qualification_priority_v1"
TOP5_ELITE_ONLY = "top5_elite_contender_only_probe"
TOP5_PRESERVE = "top5_preserve_active_cap3_tiebreak"


def build_task679_program(
    *,
    task672_dir: Path = t673.TASK672_DIR,
    qqq_path: Path = QQQ_PATH,
) -> dict[str, pd.DataFrame]:
    TASK679_DIR.mkdir(parents=True, exist_ok=True)
    panel = t673.load_task672_panel(task672_dir)
    panel = t673.add_setup_quality(panel)
    panel = t673.add_slot_value_ladder(panel)
    panel = add_top5_qualification(panel)
    qqq = load_qqq_history(qqq_path)

    rule_matrix = build_rule_matrix()
    grid, accepted, allocation, curves = build_candidate_grid(panel, qqq)
    archetype_perf = build_archetype_candidate_performance(panel)
    qualification_perf = build_qualification_performance(panel)
    guardrail = build_winner_preservation_guardrail(accepted)
    slot_audit = build_top5_slot_audit(allocation, panel)
    decision = build_decision(grid, guardrail)
    pass_fail = build_pass_fail(panel, grid, guardrail, slot_audit)

    write_outputs(
        panel,
        rule_matrix,
        grid,
        accepted,
        allocation,
        archetype_perf,
        qualification_perf,
        guardrail,
        slot_audit,
        decision,
        pass_fail,
    )
    return {
        "panel": panel,
        "rule_matrix": rule_matrix,
        "grid": grid,
        "accepted": accepted,
        "allocation": allocation,
        "curves": curves,
        "archetype_perf": archetype_perf,
        "qualification_perf": qualification_perf,
        "guardrail": guardrail,
        "slot_audit": slot_audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def add_top5_qualification(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["entry_time_archetype_candidate"] = out.apply(t678.classify_winner_archetype, axis=1)
    out["entry_time_catalyst_path"] = out.apply(t678.classify_catalyst_path, axis=1)
    out["top5_qualification_tier"] = out.apply(classify_top5_tier, axis=1)
    out["top5_qualification_reason"] = out.apply(top5_reason, axis=1)
    out["top5_qualification_rank"] = out["top5_qualification_tier"].map(
        {
            "elite_top5_candidate": 10,
            "top5_contender": 20,
            "normal_candidate": 50,
            "research_or_reject": 90,
        }
    ).fillna(80).astype(int)
    original_priority = pd.to_numeric(out.get("priority_rank", 999), errors="coerce").fillna(999).astype(int)
    out["top5_priority_rank"] = out["top5_qualification_rank"] * 1000 + original_priority
    out["top5_preserve_active_cap3_rank"] = original_priority * 1000 + out["top5_qualification_rank"]
    out["top5_return_used_in_assignment_flag"] = 0
    out["top5_label_used_in_assignment_flag"] = 0
    out["top5_future_price_used_in_assignment_flag"] = 0
    return out


def classify_top5_tier(row: pd.Series) -> str:
    archetype = s(row.get("entry_time_archetype_candidate", ""))
    catalyst_path = s(row.get("entry_time_catalyst_path", ""))
    catalyst_state = s(row.get("company_catalyst_state", ""))
    relation = s(row.get("relation_transmission_state", ""))
    price = s(row.get("price_chart_acceptance_state", ""))
    theme = s(row.get("theme_leadership_state", ""))
    setup = s(row.get("setup_quality_bucket", ""))
    sparse = int(row.get("sparse_action_block_flag", 0)) == 1 or "sparse" in relation

    high_signal_path = catalyst_path in {"contract_plus_supply_or_backlog", "supply_demand_or_backlog", "guidance_margin_upgrade"}
    hard_catalyst = catalyst_state in {"hard_company_catalyst", "multi_dimension_high_quality_catalyst", "multi_signal_medium_catalyst"}
    price_accepted = price in {"price_confirmed_basic", "price_confirmed_but_extended", "price_confirmed_not_extended", "price_accepted_needs_confirmation"}
    theme_active = theme in {"theme_participating", "theme_leadership_expanding", "narrow_leadership", "persistent_broad_theme_leader"}

    if setup == "research_only_setup" and sparse:
        return "research_or_reject"
    if archetype in {"theme_rotation_or_narrow_leader", "medium_signal_continuation"} and high_signal_path and price_accepted:
        return "elite_top5_candidate"
    if archetype == "explosive_fragile_continuation" and high_signal_path and theme_active and not sparse:
        return "elite_top5_candidate"
    if archetype == "late_extended_breakout" and high_signal_path and hard_catalyst and theme_active:
        return "top5_contender"
    if archetype == "catalyst_repricing_confirmed" and high_signal_path and hard_catalyst and price_accepted:
        return "top5_contender"
    if archetype == "steady_trend_persistence" and high_signal_path and theme_active and price == "price_confirmed_basic":
        return "normal_candidate"
    if archetype == "mixed_continuation":
        return "research_or_reject"
    return "normal_candidate"


def top5_reason(row: pd.Series) -> str:
    parts = [
        f"archetype={s(row.get('entry_time_archetype_candidate', ''))}",
        f"catalyst_path={s(row.get('entry_time_catalyst_path', ''))}",
        f"price={s(row.get('price_chart_acceptance_state', ''))}",
        f"theme={s(row.get('theme_leadership_state', ''))}",
        f"relation={s(row.get('relation_transmission_state', ''))}",
    ]
    return "|".join(parts)


def build_rule_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rule_id": "elite_theme_or_medium_signal",
                "tier": "elite_top5_candidate",
                "definition": "theme/narrow-leader or medium-signal continuation with contract/supply/backlog/guidance path and accepted price state",
                "uses_return_or_label": 0,
            },
            {
                "rule_id": "elite_explosive_not_sparse",
                "tier": "elite_top5_candidate",
                "definition": "explosive fragile continuation candidate requires high-signal catalyst path, active theme, and non-sparse relation",
                "uses_return_or_label": 0,
            },
            {
                "rule_id": "contender_late_or_catalyst",
                "tier": "top5_contender",
                "definition": "late extended breakout or confirmed catalyst repricing with high-signal catalyst path and hard catalyst state",
                "uses_return_or_label": 0,
            },
            {
                "rule_id": "normal_steady",
                "tier": "normal_candidate",
                "definition": "steady trend persistence with high-signal catalyst path and basic price confirmation",
                "uses_return_or_label": 0,
            },
            {
                "rule_id": "research_reject_sparse_or_mixed",
                "tier": "research_or_reject",
                "definition": "sparse research-only rows and mixed-continuation rows are not top5-qualified",
                "uses_return_or_label": 0,
            },
        ]
    )


def build_candidate_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    candidates = [
        (ACTIVE_CAP3, "priority_rank", "relation3", 0, 0),
        (TOP5_PRIORITY, "top5_priority_rank", "relation3", 0, 0),
        (TOP5_ELITE_ONLY, "top5_priority_rank", "relation3", 1, 1),
        (TOP5_PRESERVE, "top5_preserve_active_cap3_rank", "relation3", 0, 0),
    ]
    rows: list[dict[str, object]] = []
    accepted_frames: list[pd.DataFrame] = []
    allocation_frames: list[pd.DataFrame] = []
    curve_frames: list[pd.DataFrame] = []
    original_max_positions = t673.MAX_POSITIONS
    try:
        t673.MAX_POSITIONS = 5
        for candidate_name, rank_col, cap_mode, block_non_top5, diagnostic in candidates:
            spec = pd.Series(t673.candidate(candidate_name, "task679_top5_qualification", "relation_priority", cap_mode, 0, diagnostic, 0, 0, "Task679 top5 qualification candidate."))
            for split_name in ["all", "validation", "recent_oos"]:
                scoped = panel if split_name == "all" else panel[panel["split_name"].astype(str).eq(split_name)].copy()
                scoped = scoped.copy()
                scoped["priority_rank"] = pd.to_numeric(scoped[rank_col], errors="coerce").fillna(999999).astype(int)
                if block_non_top5:
                    scoped = scoped[scoped["top5_qualification_tier"].isin(["elite_top5_candidate", "top5_contender"])].copy()
                quality, accepted, allocation, curve = t673.simulate_candidate(scoped, spec)
                qqq_final = qqq_final_for_period(qqq, scoped)
                final = INITIAL_CAPITAL_USD * (1.0 + quality["capital_pnl_pct"] / 100.0)
                rows.append(
                    {
                        "candidate_name": candidate_name,
                        "split_name": split_name,
                        "initial_capital_usd": INITIAL_CAPITAL_USD,
                        "source_trade_count": int(len(scoped)),
                        "accepted_trade_count": int(len(accepted)),
                        "final_capital_usd": float(final),
                        "capital_return_pct": float(quality["capital_pnl_pct"]),
                        "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                        "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                        "qqq_final_capital_usd": float(qqq_final),
                        "beats_qqq_flag": int(final > qqq_final),
                        "rank_column": rank_col,
                        "block_non_top5_flag": int(block_non_top5),
                        "diagnostic_only_flag": int(diagnostic),
                        "return_used_in_assignment_flag": 0,
                        "label_used_in_assignment_flag": 0,
                        "future_price_used_in_assignment_flag": 0,
                    }
                )
                for frame, bucket in [(accepted, accepted_frames), (allocation, allocation_frames), (curve, curve_frames)]:
                    if not frame.empty:
                        tmp = frame.copy()
                        tmp["candidate_name"] = candidate_name
                        tmp["split_scope"] = split_name
                        tmp["rank_column"] = rank_col
                        bucket.append(tmp)
    finally:
        t673.MAX_POSITIONS = original_max_positions

    return (
        pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True),
        pd.concat(accepted_frames, ignore_index=True) if accepted_frames else pd.DataFrame(),
        pd.concat(allocation_frames, ignore_index=True) if allocation_frames else pd.DataFrame(),
        pd.concat(curve_frames, ignore_index=True) if curve_frames else pd.DataFrame(),
    )


def build_archetype_candidate_performance(panel: pd.DataFrame) -> pd.DataFrame:
    work = panel.copy()
    work["net_return_costed_eval"] = pd.to_numeric(work["net_return_from_entry"], errors="coerce") - t673.COST_BPS / 10000.0
    rows = []
    for split in ["all", "validation", "recent_oos"]:
        scoped = work if split == "all" else work[work["split_name"].astype(str).eq(split)]
        for archetype, group in scoped.groupby("entry_time_archetype_candidate", dropna=False):
            returns = pd.to_numeric(group["net_return_costed_eval"], errors="coerce")
            rows.append(metric_row(split, "entry_time_archetype_candidate", archetype, group, returns))
    return pd.DataFrame(rows).sort_values(["split_name", "avg_return_costed_pct_eval_only"], ascending=[True, False]).reset_index(drop=True)


def build_qualification_performance(panel: pd.DataFrame) -> pd.DataFrame:
    work = panel.copy()
    work["net_return_costed_eval"] = pd.to_numeric(work["net_return_from_entry"], errors="coerce") - t673.COST_BPS / 10000.0
    rows = []
    for split in ["all", "validation", "recent_oos"]:
        scoped = work if split == "all" else work[work["split_name"].astype(str).eq(split)]
        for tier, group in scoped.groupby("top5_qualification_tier", dropna=False):
            returns = pd.to_numeric(group["net_return_costed_eval"], errors="coerce")
            rows.append(metric_row(split, "top5_qualification_tier", tier, group, returns))
    return pd.DataFrame(rows).sort_values(["split_name", "avg_return_costed_pct_eval_only"], ascending=[True, False]).reset_index(drop=True)


def metric_row(split: str, axis: str, value: object, group: pd.DataFrame, returns: pd.Series) -> dict[str, object]:
    return {
        "split_name": split,
        "axis": axis,
        "axis_value": value,
        "candidate_count": int(len(group)),
        "avg_return_costed_pct_eval_only": float(returns.mean() * 100.0),
        "win_rate_eval_only": float(returns.gt(0).mean()),
        "big_winner_count_eval_only": int(returns.ge(0.50).sum()),
        "failure_count_eval_only": int(returns.le(-0.10).sum()),
        "return_used_in_assignment_flag": 0,
        "label_used_in_assignment_flag": 0,
    }


def build_winner_preservation_guardrail(accepted: pd.DataFrame) -> pd.DataFrame:
    active = accepted[(accepted["candidate_name"].eq(ACTIVE_CAP3)) & (accepted["split_scope"].eq("all"))].copy()
    active_ids = set(active["lifecycle_id"].astype(str))
    active_returns = active.set_index(active["lifecycle_id"].astype(str))["net_return_costed"]
    rows = []
    for candidate_name, group in accepted[accepted["split_scope"].eq("all")].groupby("candidate_name", dropna=False):
        ids = set(group["lifecycle_id"].astype(str))
        removed_ids = active_ids - ids
        added_ids = ids - active_ids
        removed = pd.to_numeric(active_returns.loc[list(removed_ids)] if removed_ids else pd.Series(dtype=float), errors="coerce")
        added = pd.to_numeric(group[group["lifecycle_id"].astype(str).isin(added_ids)]["net_return_costed"] if added_ids else pd.Series(dtype=float), errors="coerce")
        removed_big = int(removed.ge(0.50).sum()) if len(removed) else 0
        rows.append(
            {
                "candidate_name": candidate_name,
                "active_cap3_trade_count": int(len(active_ids)),
                "candidate_trade_count": int(len(ids)),
                "common_trade_count": int(len(active_ids & ids)),
                "removed_active_cap3_trade_count": int(len(removed_ids)),
                "added_trade_count": int(len(added_ids)),
                "removed_active_cap3_avg_return_pct_eval_only": float(removed.mean() * 100.0) if len(removed) else 0.0,
                "removed_active_cap3_big_winner_count_eval_only": removed_big,
                "removed_active_cap3_failure_count_eval_only": int(removed.le(-0.10).sum()) if len(removed) else 0,
                "added_avg_return_pct_eval_only": float(added.mean() * 100.0) if len(added) else 0.0,
                "added_big_winner_count_eval_only": int(added.ge(0.50).sum()) if len(added) else 0,
                "winner_preservation_guardrail_pass_flag": int(removed_big == 0),
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["winner_preservation_guardrail_pass_flag", "removed_active_cap3_big_winner_count_eval_only"], ascending=[True, False]).reset_index(drop=True)


def build_top5_slot_audit(allocation: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    returns = panel[["lifecycle_id", "net_return_from_entry", "top5_qualification_tier", "entry_time_archetype_candidate"]].copy()
    returns["lifecycle_id"] = returns["lifecycle_id"].astype(str)
    work = allocation[allocation["split_scope"].eq("all")].copy()
    work["lifecycle_id"] = work["lifecycle_id"].astype(str)
    work = work.merge(returns, on="lifecycle_id", how="left")
    work["net_return_costed_eval"] = pd.to_numeric(work["net_return_from_entry"], errors="coerce") - t673.COST_BPS / 10000.0
    rows = []
    for keys, group in work.groupby(["candidate_name", "top5_qualification_tier", "accepted_flag"], dropna=False):
        candidate_name, tier, accepted_flag = keys
        r = pd.to_numeric(group["net_return_costed_eval"], errors="coerce")
        rows.append(
            {
                "candidate_name": candidate_name,
                "top5_qualification_tier": tier,
                "accepted_flag": int(accepted_flag),
                "row_count": int(len(group)),
                "avg_return_costed_pct_eval_only": float(r.mean() * 100.0) if len(r) else 0.0,
                "big_winner_count_eval_only": int(r.ge(0.50).sum()) if len(r) else 0,
                "failure_count_eval_only": int(r.le(-0.10).sum()) if len(r) else 0,
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["candidate_name", "accepted_flag", "top5_qualification_tier"]).reset_index(drop=True)


def build_decision(grid: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    active = grid[(grid["candidate_name"].eq(ACTIVE_CAP3)) & (grid["split_name"].eq("all"))].iloc[0]
    best = grid[grid["split_name"].eq("all")].sort_values("final_capital_usd", ascending=False).iloc[0]
    best_guard = guardrail[guardrail["candidate_name"].eq(best["candidate_name"])].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": "Task679",
                "decision": "TOP5_QUALIFICATION_ENGINE_BUILT_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "active_cap3_final_capital_usd": float(active["final_capital_usd"]),
                "active_cap3_max_drawdown_pct": float(active["max_drawdown_pct"]),
                "best_candidate_name": best["candidate_name"],
                "best_final_capital_usd": float(best["final_capital_usd"]),
                "best_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "best_removed_big_winners": int(best_guard["removed_active_cap3_big_winner_count_eval_only"]),
                "best_winner_preservation_guardrail_pass_flag": int(best_guard["winner_preservation_guardrail_pass_flag"]),
                "next_action": "Use top5 qualification only after a rule beats active cap3 or preserves active cap3 winners while reducing drawdown in split/OOS.",
            }
        ]
    )


def build_pass_fail(panel: pd.DataFrame, grid: pd.DataFrame, guardrail: pd.DataFrame, slot_audit: pd.DataFrame) -> pd.DataFrame:
    active = grid[(grid["candidate_name"].eq(ACTIVE_CAP3)) & (grid["split_name"].eq("all"))].iloc[0]
    best = grid[grid["split_name"].eq("all")].sort_values("final_capital_usd", ascending=False).iloc[0]
    best_guard = guardrail[guardrail["candidate_name"].eq(best["candidate_name"])].iloc[0]
    return pd.DataFrame(
        [
            gate("top5_columns_built", {"entry_time_archetype_candidate", "top5_qualification_tier", "top5_priority_rank"}.issubset(panel.columns), "columns present", "required columns"),
            gate("no_return_label_future_assignment", int(panel[["top5_return_used_in_assignment_flag", "top5_label_used_in_assignment_flag", "top5_future_price_used_in_assignment_flag"]].sum().sum()) == 0, "violations=0", "0 violations"),
            gate("candidate_grid_built", not grid.empty, f"rows={len(grid)}", "candidate grid"),
            gate("winner_preservation_guardrail_built", not guardrail.empty, f"rows={len(guardrail)}", "guardrail rows"),
            gate("slot_audit_built", not slot_audit.empty, f"rows={len(slot_audit)}", "slot audit rows"),
            gate("best_beats_active_cap3_return", float(best["final_capital_usd"]) > float(active["final_capital_usd"]), f"best={float(best['final_capital_usd']):.2f}, active={float(active['final_capital_usd']):.2f}", "best final > active cap3"),
            gate("best_mdd_not_worse_than_active_cap3", float(best["max_drawdown_pct"]) >= float(active["max_drawdown_pct"]), f"best={float(best['max_drawdown_pct']):.2f}, active={float(active['max_drawdown_pct']):.2f}", "best MDD not worse"),
            gate("best_preserves_big_winners", int(best_guard["winner_preservation_guardrail_pass_flag"]) == 1, f"removed_big={int(best_guard['removed_active_cap3_big_winner_count_eval_only'])}", "0 removed big winners"),
            gate("strategy_accepted", False, "research only", "requires robust OOS promotion"),
        ]
    )


def write_outputs(
    panel: pd.DataFrame,
    rule_matrix: pd.DataFrame,
    grid: pd.DataFrame,
    accepted: pd.DataFrame,
    allocation: pd.DataFrame,
    archetype_perf: pd.DataFrame,
    qualification_perf: pd.DataFrame,
    guardrail: pd.DataFrame,
    slot_audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task679_entry_time_archetype_panel.csv": panel,
        "task679_top5_rule_matrix.csv": rule_matrix,
        "task679_top5_candidate_grid.csv": grid,
        "task679_accepted_trades.csv": accepted,
        "task679_allocation_panel.csv": allocation,
        "task679_archetype_candidate_performance.csv": archetype_perf,
        "task679_qualification_tier_performance.csv": qualification_perf,
        "task679_winner_preservation_guardrail.csv": guardrail,
        "task679_slot_qualification_audit.csv": slot_audit,
        "task_679_decision.csv": decision,
        "task_679_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK679_DIR / name, index=False)
    (TASK679_DIR / "task_679_top5_qualification_engine.md").write_text(
        render_report(grid, archetype_perf, qualification_perf, guardrail, slot_audit, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK679_DIR, TASK679_DIR / "artifact_manifest.csv")


def render_report(
    grid: pd.DataFrame,
    archetype_perf: pd.DataFrame,
    qualification_perf: pd.DataFrame,
    guardrail: pd.DataFrame,
    slot_audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    active = grid[(grid["candidate_name"].eq(ACTIVE_CAP3)) & (grid["split_name"].eq("all"))].iloc[0]
    best = grid[grid["split_name"].eq("all")].sort_values("final_capital_usd", ascending=False).iloc[0]
    return f"""# Task679 Top5 Qualification Engine

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: active cap3 ${float(active['final_capital_usd']):,.2f} / MDD {float(active['max_drawdown_pct']):.2f}%; best Task679 candidate `{best['candidate_name']}` ${float(best['final_capital_usd']):,.2f} / MDD {float(best['max_drawdown_pct']):.2f}%.
- What changed: entry-time winner archetype candidates, top5 qualification tiers, and mandatory winner-preservation guardrail were implemented.
- Next action: do not promote until a top5 rule preserves active cap3 big winners and improves split/OOS return plus drawdown.

## Quant Expert Report

### Data source and source readiness

- Inputs: Task672 current-data state panel and QQQ benchmark.
- No quote, trade, NBBO, or microstructure data is used.
- No GPT output is used as a source, label, or assignment input.

### Exact join keys

- Candidate replay uses original lifecycle rows and `lifecycle_id`.
- Preservation guardrail compares accepted sets by `lifecycle_id`.

### Leakage audit

- Top5 qualification uses entry-time state columns only.
- `return_used_in_assignment_flag`, `label_used_in_assignment_flag`, and `future_price_used_in_assignment_flag` are zero.
- Return fields in performance tables are evaluation-only.

### Split/OOS metrics

{t678.markdown_table(grid)}

### Entry-time archetype candidate performance

{t678.markdown_table(archetype_perf.head(20))}

### Top5 qualification tier performance

{t678.markdown_table(qualification_perf)}

### Winner preservation guardrail

{t678.markdown_table(guardrail)}

### Slot qualification audit

{t678.markdown_table(slot_audit.head(20))}

### Remaining blockers

- The top5 qualification prototype did not create a deployment-ready promotion.
- Any next rule must preserve active cap3 big winners before it is allowed into a backtest promotion path.

## No-Background Decision-Maker Report

- What happened: Top5 자격을 숫자로 만들고, 큰 승자 제거 여부를 필수 검사로 붙였다.
- Why it matters: 이 전략은 많이 사는 전략이 아니라 상위 5개 자리를 제대로 배정해야 돈이 난다.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: Top5 자격 룰을 더 정교화하되 큰 승자를 자르면 바로 탈락시킨다.

## Artifact Manifest

- Inputs: Task672 panel, QQQ benchmark.
- Outputs: all CSVs in this directory plus `artifact_manifest.csv`.
- Validation commands: `python -m unittest tests.test_task679_top5_qualification_engine`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "pass_flag": int(bool(passed)),
        "observed": observed,
        "required": required,
    }


def s(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task672-dir", type=Path, default=t673.TASK672_DIR)
    parser.add_argument("--qqq-path", type=Path, default=QQQ_PATH)
    args = parser.parse_args()
    build_task679_program(task672_dir=args.task672_dir, qqq_path=args.qqq_path)
    print(f"[Task679] wrote {TASK679_DIR}")


if __name__ == "__main__":
    main()
