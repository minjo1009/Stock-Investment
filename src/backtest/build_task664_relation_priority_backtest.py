from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import (
    INITIAL_CAPITAL_USD,
    load_qqq_history,
    qqq_final_for_period,
)
from src.backtest.build_task659_theme_specific_relation_engine import QQQ_PATH, task639_core
from src.backtest.build_task661_mechanism_relation_engine import (
    TASK659_PANEL,
    build_institutional_transmission_template,
    build_mechanism_state_panel,
    load_task659_panel,
)


TASK_ID = "Task664"
REPORT_DIR = Path("docs/reports/task_664_relation_priority_backtest")
MAX_POSITIONS = 5
COST_BPS = 50


def build_task664_relation_priority_backtest(
    *,
    task659_panel_path: Path = TASK659_PANEL,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = build_mechanism_state_panel(load_task659_panel(task659_panel_path), build_institutional_transmission_template())
    core = task639_core(panel)
    qqq = load_qqq_history(qqq_path)

    specs = build_priority_specs()
    ladder = build_priority_ladder()
    candidate_grid = build_candidate_grid(core, specs, qqq)
    accepted_delta = build_accepted_priority_delta(core, specs)
    collision_audit = build_slot_collision_audit(core)
    promotion = build_promotion_report(candidate_grid, specs)
    decision = build_decision(promotion)
    pass_fail = build_pass_fail(candidate_grid, promotion, accepted_delta, specs)

    specs.to_csv(out_dir / "relation_priority_candidate_specs.csv", index=False, encoding="utf-8-sig")
    ladder.to_csv(out_dir / "relation_priority_ladder.csv", index=False, encoding="utf-8-sig")
    candidate_grid.to_csv(out_dir / "relation_priority_candidate_grid.csv", index=False, encoding="utf-8-sig")
    accepted_delta.to_csv(out_dir / "accepted_priority_delta.csv", index=False, encoding="utf-8-sig")
    collision_audit.to_csv(out_dir / "slot_collision_audit.csv", index=False, encoding="utf-8-sig")
    promotion.to_csv(out_dir / "relation_priority_promotion_report.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_664_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_664_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, candidate_grid, accepted_delta, collision_audit, promotion, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "specs": specs,
        "ladder": ladder,
        "candidate_grid": candidate_grid,
        "accepted_delta": accepted_delta,
        "collision_audit": collision_audit,
        "promotion": promotion,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_priority_specs() -> pd.DataFrame:
    rows = [
        {
            "candidate_name": "baseline_chronological",
            "candidate_type": "baseline",
            "priority_rule": "entry_ts_then_lifecycle_id",
            "diagnostic_only_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "return_tuned_flag": 0,
            "description": "Original Task639 ordering.",
        },
        {
            "candidate_name": "predeclared_relation_ladder",
            "candidate_type": "predeclared_priority",
            "priority_rule": "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse",
            "diagnostic_only_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "return_tuned_flag": 0,
            "description": "Prioritize stronger economic relation states within the same entry timestamp only.",
        },
        {
            "candidate_name": "predeclared_catalyst_price_ladder",
            "candidate_type": "predeclared_priority",
            "priority_rule": "catalyst_quality_then_price_acceptance_then_relation",
            "diagnostic_only_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "return_tuned_flag": 0,
            "description": "Prioritize catalyst quality and price acceptance before relation state.",
        },
        {
            "candidate_name": "diagnostic_recent_weak_state_last",
            "candidate_type": "diagnostic_priority",
            "priority_rule": "company_quality_price_confirmed_last",
            "diagnostic_only_flag": 1,
            "fixed_hold_or_timing_override_flag": 0,
            "return_tuned_flag": 1,
            "description": "Diagnostic only: pushes the recent OOS weak state later. Not eligible for promotion.",
        },
    ]
    return pd.DataFrame(rows)


def build_priority_ladder() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"priority_rule": "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse", "rank": 1, "condition": "mechanism_reinforcing_company_positive", "promotion_eligible_flag": 1},
            {"priority_rule": "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse", "rank": 2, "condition": "mechanism_offsetting_company_positive", "promotion_eligible_flag": 1},
            {"priority_rule": "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse", "rank": 3, "condition": "company_positive_needs_confirmation", "promotion_eligible_flag": 1},
            {"priority_rule": "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse", "rank": 4, "condition": "company_quality_price_confirmed", "promotion_eligible_flag": 1},
            {"priority_rule": "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse", "rank": 5, "condition": "sparse_mechanism_cell", "promotion_eligible_flag": 1},
            {"priority_rule": "catalyst_quality_then_price_acceptance_then_relation", "rank": 1, "condition": "very_strong_or_strong_catalyst plus strong/accepted price", "promotion_eligible_flag": 1},
            {"priority_rule": "company_quality_price_confirmed_last", "rank": 99, "condition": "company_quality_price_confirmed forced last from observed recent OOS weakness", "promotion_eligible_flag": 0},
        ]
    )


def build_candidate_grid(core: pd.DataFrame, specs: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, spec in specs.iterrows():
        ranked = add_priority(core, str(spec["priority_rule"]))
        for split_name in ["all", "validation", "recent_oos"]:
            scoped = ranked if split_name == "all" else ranked[ranked["split_name"].astype(str).eq(split_name)].copy()
            quality, accepted = simulate_priority_account(scoped)
            qqq_final = qqq_final_for_period(qqq, scoped)
            final = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
            rows.append(
                {
                    "candidate_name": spec["candidate_name"],
                    "split_name": split_name,
                    "candidate_type": spec["candidate_type"],
                    "initial_capital_usd": INITIAL_CAPITAL_USD,
                    "source_trade_count": int(len(scoped)),
                    "accepted_trade_count": int(len(accepted)),
                    "final_capital_usd": float(final),
                    "capital_return_pct": float(quality["capital_pnl_pct"]),
                    "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                    "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                    "qqq_final_capital_usd": float(qqq_final),
                    "beats_qqq_flag": int(final > qqq_final),
                    "diagnostic_only_flag": int(spec["diagnostic_only_flag"]),
                    "fixed_hold_or_timing_override_flag": int(spec["fixed_hold_or_timing_override_flag"]),
                    "return_tuned_flag": int(spec["return_tuned_flag"]),
                    "label_used_in_assignment_flag": 0,
                    "return_used_in_assignment_flag": 0,
                }
            )
    return pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)


def add_priority(frame: pd.DataFrame, rule: str) -> pd.DataFrame:
    out = frame.copy()
    out["priority_rank"] = out.apply(lambda row: priority_rank(row, rule), axis=1)
    out["priority_rule"] = rule
    return out


def priority_rank(row: pd.Series, rule: str) -> int:
    state = str(row.get("mechanism_relation_state", ""))
    if rule == "entry_ts_then_lifecycle_id":
        return 50
    if rule == "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse":
        return {
            "mechanism_reinforcing_company_positive": 10,
            "mechanism_offsetting_company_positive": 20,
            "company_positive_needs_confirmation": 30,
            "company_quality_price_confirmed": 40,
            "sparse_mechanism_cell": 90,
        }.get(state, 80)
    if rule == "catalyst_quality_then_price_acceptance_then_relation":
        catalyst = str(row.get("catalyst_quality_tier", ""))
        price = str(row.get("price_acceptance_state", ""))
        score = 50
        if catalyst == "very_strong_catalyst":
            score -= 20
        elif catalyst == "strong_catalyst":
            score -= 15
        elif catalyst == "medium_catalyst":
            score -= 5
        if price == "price_acceptance_strong":
            score -= 10
        elif price == "price_acceptance_accepted":
            score -= 5
        if state == "mechanism_reinforcing_company_positive":
            score -= 5
        if state == "sparse_mechanism_cell":
            score += 20
        return int(score)
    if rule == "company_quality_price_confirmed_last":
        if state == "company_quality_price_confirmed":
            return 90
        return priority_rank(row, "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse")
    return 50


def simulate_priority_account(panel: pd.DataFrame) -> tuple[dict[str, object], pd.DataFrame]:
    if panel.empty:
        return empty_quality(), panel.copy()
    ordered = panel.sort_values(["entry_ts", "priority_rank", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    ordered["net_return_from_entry"] = pd.to_numeric(ordered["net_return_from_entry"], errors="coerce") - COST_BPS / 10000.0
    equity = 1.0
    peak = 1.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []
    drawdowns = [0.0]

    def close_positions_until(current_ts: pd.Timestamp) -> None:
        nonlocal equity, peak, open_positions
        still_open = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= current_ts:
                equity += float(pos["capital"]) * float(pos["return"])
                peak = max(peak, equity)
                drawdowns.append((equity / max(peak, 1e-9) - 1.0) * 100.0)
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_positions_until(entry_ts)
        if len(open_positions) >= MAX_POSITIONS:
            continue
        capital = equity / float(MAX_POSITIONS)
        open_positions.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_from_entry"],
            }
        )
        accepted = dict(row)
        accepted["priority_accepted_flag"] = 1
        accepted["priority_position_slot_cap"] = MAX_POSITIONS
        accepted_rows.append(accepted)
    close_positions_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    if accepted.empty:
        return empty_quality(), accepted
    returns = pd.to_numeric(accepted["net_return_from_entry"], errors="coerce")
    quality = {
        "avg_net_return_pct": float(returns.mean() * 100.0),
        "win_rate": float(returns.gt(0).mean()),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
        "max_drawdown_pct": float(min(drawdowns) if drawdowns else 0.0),
        "capital_pnl_pct": float((equity - 1.0) * 100.0),
    }
    return quality, accepted


def empty_quality() -> dict[str, object]:
    return {
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "max_drawdown_pct": 0.0,
        "capital_pnl_pct": 0.0,
    }


def build_accepted_priority_delta(core: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    baseline = add_priority(core, "entry_ts_then_lifecycle_id")
    rows = []
    for split_name in ["all", "validation", "recent_oos"]:
        base_scoped = baseline if split_name == "all" else baseline[baseline["split_name"].astype(str).eq(split_name)]
        _, base_acc = simulate_priority_account(base_scoped)
        base_ids = accepted_id_set(base_acc)
        for _, spec in specs.iterrows():
            if spec["candidate_name"] == "baseline_chronological":
                continue
            ranked = add_priority(core, str(spec["priority_rule"]))
            scoped = ranked if split_name == "all" else ranked[ranked["split_name"].astype(str).eq(split_name)]
            _, acc = simulate_priority_account(scoped)
            ids = accepted_id_set(acc)
            rows.append(
                {
                    "candidate_name": spec["candidate_name"],
                    "split_name": split_name,
                    "baseline_accepted_count": int(len(base_ids)),
                    "candidate_accepted_count": int(len(ids)),
                    "common_accepted_count": int(len(base_ids.intersection(ids))),
                    "added_accepted_count": int(len(ids - base_ids)),
                    "removed_accepted_count": int(len(base_ids - ids)),
                    "accepted_set_changed_flag": int(ids != base_ids),
                    "diagnostic_only_flag": int(spec["diagnostic_only_flag"]),
                    "return_tuned_flag": int(spec["return_tuned_flag"]),
                }
            )
    return pd.DataFrame(rows)


def accepted_id_set(frame: pd.DataFrame) -> set[str]:
    if frame.empty:
        return set()
    return set(frame["lifecycle_id"].astype(str))


def build_slot_collision_audit(core: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = core.groupby(["split_name", "entry_ts"], dropna=False)
    for (split_name, entry_ts), group in grouped:
        if len(group) <= MAX_POSITIONS:
            continue
        rows.append(
            {
                "split_name": split_name,
                "entry_ts": entry_ts,
                "candidate_count_same_ts": int(len(group)),
                "max_positions": MAX_POSITIONS,
                "relation_state_count": int(group["mechanism_relation_state"].nunique()),
                "reinforcing_count": int(group["mechanism_relation_state"].eq("mechanism_reinforcing_company_positive").sum()),
                "offsetting_count": int(group["mechanism_relation_state"].eq("mechanism_offsetting_company_positive").sum()),
                "quality_confirmed_count": int(group["mechanism_relation_state"].eq("company_quality_price_confirmed").sum()),
                "sparse_count": int(group["mechanism_relation_state"].eq("sparse_mechanism_cell").sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["split_name", "candidate_count_same_ts"], ascending=[True, False]).reset_index(drop=True)


def build_promotion_report(candidate_grid: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    baseline = pivot_candidate(candidate_grid, "baseline_chronological")
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
        allowed = int(int(spec["diagnostic_only_flag"]) == 0 and int(spec["return_tuned_flag"]) == 0 and int(spec["fixed_hold_or_timing_override_flag"]) == 0)
        promotion = int(
            candidate_name != "baseline_chronological"
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
        return "passes_all_relation_priority_gates"
    if not allowed:
        return "diagnostic_or_return_tuned_not_promotion_eligible"
    if not beats_all:
        return "full_period_return_not_better"
    if not dd_ok:
        return "full_period_drawdown_worse"
    if not validation_up or not recent_up:
        return "validation_or_recent_oos_not_better"
    if not validation_dd_ok or not recent_dd_ok:
        return "validation_or_recent_oos_drawdown_worse"
    return "other_gate_failure"


def build_decision(promotion: pd.DataFrame) -> pd.DataFrame:
    baseline = promotion[promotion["candidate_name"].eq("baseline_chronological")].iloc[0]
    best = promotion.sort_values("all_final_capital_usd", ascending=False).iloc[0]
    decision = "RELATION_PRIORITY_TESTED_NO_PROMOTION_CANDIDATE"
    if int(promotion["promotion_candidate_flag"].sum()) > 0:
        decision = "RELATION_PRIORITY_PROMOTION_CANDIDATE_FOUND_NOT_ACCEPTED"
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
                "best_candidate_name": best["candidate_name"],
                "best_candidate_final_capital_usd": float(best["all_final_capital_usd"]),
                "best_candidate_max_drawdown_pct": float(best["all_max_drawdown_pct"]),
                "promotion_candidate_count": int(promotion["promotion_candidate_flag"].sum()),
                "trading_promotion_pass_flag": 0,
                "next_action": "If priority fails, inspect accepted trade deltas by same timestamp and design non-return-tuned risk caps rather than changing exits.",
            }
        ]
    )


def build_pass_fail(
    candidate_grid: pd.DataFrame,
    promotion: pd.DataFrame,
    accepted_delta: pd.DataFrame,
    specs: pd.DataFrame,
) -> pd.DataFrame:
    fixed_hold_violations = int(specs["fixed_hold_or_timing_override_flag"].sum())
    priority_changed = int(accepted_delta["accepted_set_changed_flag"].sum())
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    return pd.DataFrame(
        [
            {"gate": "no_fixed_hold_or_timing_override", "pass_flag": int(fixed_hold_violations == 0), "observed_value": f"violations={fixed_hold_violations}", "required_value": "priority test must keep existing Task639 timing and exit"},
            {"gate": "priority_changes_accepted_set", "pass_flag": int(priority_changed > 0), "observed_value": f"changed_rows={priority_changed}", "required_value": "priority should affect max5 accepted trades"},
            {"gate": "no_return_tuned_promotion", "pass_flag": int(promotion[promotion["promotion_candidate_flag"].eq(1)]["candidate_name"].isin(specs[specs["return_tuned_flag"].eq(1)]["candidate_name"]).sum() == 0), "observed_value": "return-tuned promotion count=0", "required_value": "return-tuned diagnostic candidates cannot be promoted"},
            {"gate": "promotion_candidate_found", "pass_flag": int(promotion_count > 0), "observed_value": f"promotion_candidates={promotion_count}", "required_value": "candidate must improve full return, drawdown, validation, and recent OOS"},
            {"gate": "strategy_accepted", "pass_flag": 0, "observed_value": "research diagnostic only", "required_value": "requires accepted strategy gates and live readiness"},
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    candidate_grid: pd.DataFrame,
    accepted_delta: pd.DataFrame,
    collision_audit: pd.DataFrame,
    promotion: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task664 Relation Priority Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Baseline: `${float(d['baseline_final_capital_usd']):.2f}`, max drawdown `{float(d['baseline_max_drawdown_pct']):.2f}%`.",
        f"- Best priority candidate: `{d['best_candidate_name']}` = `${float(d['best_candidate_final_capital_usd']):.2f}`, max drawdown `{float(d['best_candidate_max_drawdown_pct']):.2f}%`.",
        f"- Promotion candidates: `{int(d['promotion_candidate_count'])}`.",
        "",
        "## Quant Expert Report",
        "",
        "Task664 connects relation states to max5 capacity by changing only the ordering of same-entry-timestamp candidates. It does not change entry timing, exits, sizing, or create standalone macro entries.",
        "",
        "### Data Source And Source Readiness",
        "",
        "Input is the Task661 mechanism state panel rebuilt from Task659. No new data source is introduced.",
        "",
        "### Exact Join Keys",
        "",
        "`lifecycle_id`, `entry_ts`, `simulated_exit_ts`, and `split_name`.",
        "",
        "### Leakage Audit",
        "",
        "Predeclared candidates use relation, catalyst, and price acceptance fields only. The recent-weak-state candidate is marked diagnostic and return-tuned, so it cannot promote.",
        "",
        "### Candidate Grid",
        "",
        table(candidate_grid),
        "",
        "### Accepted Priority Delta",
        "",
        table(accepted_delta),
        "",
        "### Slot Collision Audit",
        "",
        table(collision_audit),
        "",
        "### Promotion Report",
        "",
        table(promotion),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "관계형 엔진을 매매 슬롯 우선순위에 연결했습니다.",
        "",
        "기존 진입과 청산은 그대로입니다.",
        "",
        "같은 시간에 후보가 몰릴 때 어떤 종목이 max5 슬롯을 먼저 차지할지만 바꿨습니다.",
        "",
        "결과가 좋아지면 relation state가 실제 돈으로 연결되는 것입니다. 아니면 아직 슬롯 우선순위로는 부족한 것입니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `relation_priority_candidate_specs.csv`",
        "- `relation_priority_ladder.csv`",
        "- `relation_priority_candidate_grid.csv`",
        "- `accepted_priority_delta.csv`",
        "- `slot_collision_audit.csv`",
        "- `relation_priority_promotion_report.csv`",
        "- `task_664_decision.csv`",
        "- `task_664_pass_fail_matrix.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_664_relation_priority_backtest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    result = build_task664_relation_priority_backtest(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best={decision['best_candidate_name']} "
        f"promotion={int(decision['promotion_candidate_count'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
