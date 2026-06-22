from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import INITIAL_CAPITAL_USD, load_qqq_history, qqq_final_for_period
from src.backtest.build_task638_content_signal_refinement import DAILY_DIRS, QQQ_PATH, costed, load_daily_maps


TASK_ID = "Task644"
REPORT_DIR = Path("docs/reports/task_644_firm_grade_conditional_wrapper")
TASK643_EXECUTION_PANEL = Path("docs/reports/task_643_entry_risk_tier_turnover_backtest/task_643_execution_variant_panel.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
TASK644_GPT_DESIGN = Path("docs/reports/task_644_firm_grade_conditional_wrapper/task_644_gpt_design_response.md")
ROUND_TRIP_COST_BPS = 50
MAX_POSITIONS = 5

ENTRY_WRAPPERS = (
    "base",
    "supply_badvol_confirm_vwap_or_volume",
    "weak_badvol_confirm_vwap_rs",
    "noncontract_badvol_confirm_strict",
)
SIZING_WRAPPERS = ("equal", "soft_tier", "quality_vol", "quality_vol_tier")
EXIT_WRAPPERS = ("existing", "weak_hold20", "weak_trail10", "partial20_half", "partial30_third", "badvol_partial20_half")


def build_task644_firm_grade_conditional_wrapper(
    *,
    execution_panel_path: Path = TASK643_EXECUTION_PANEL,
    task639_decision_path: Path = TASK639_DECISION,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    execution = load_execution_panel(execution_panel_path)
    task639 = pd.read_csv(task639_decision_path).iloc[0]
    daily_maps = load_daily_maps(sorted(execution["symbol"].astype(str).str.upper().unique()))
    selected = build_conditional_candidate_panel(execution, daily_maps)
    account = build_account_grid(selected, qqq_path)
    oos = build_oos_grid(selected, qqq_path)
    source_audit = build_source_audit(execution, selected)
    pass_fail = build_pass_fail(account, oos, source_audit, task639)
    decision = build_decision(account, oos, pass_fail, task639)

    out_dir.mkdir(parents=True, exist_ok=True)
    selected.to_csv(out_dir / "task_644_conditional_candidate_panel.csv", index=False)
    account.to_csv(out_dir / "task_644_account_grid.csv", index=False)
    oos.to_csv(out_dir / "task_644_oos_grid.csv", index=False)
    source_audit.to_csv(out_dir / "task_644_source_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_644_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_644_decision.csv", index=False)
    (out_dir / "task_644_firm_grade_conditional_wrapper.md").write_text(
        render_report(account, oos, source_audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_644_conditional_candidate_panel": selected,
        "task_644_account_grid": account,
        "task_644_oos_grid": oos,
        "task_644_source_audit": source_audit,
        "task_644_pass_fail_matrix": pass_fail,
        "task_644_decision": decision,
    }


def load_execution_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    for column in ["net_return_from_entry", "entry_price", "simulated_exit_price", "atr20_pct", "gap_pct", "range_pos"]:
        if column in panel.columns:
            panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def build_conditional_candidate_panel(execution: pd.DataFrame, daily_maps: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    base_lifecycles = execution[execution["entry_policy"].eq("base_delay1d_open")]["lifecycle_id"].drop_duplicates().tolist()
    indexed = {
        (str(row["lifecycle_id"]), str(row["entry_policy"]), str(row["exit_policy"])): row
        for row in execution.to_dict(orient="records")
    }
    for entry_wrapper in ENTRY_WRAPPERS:
        for exit_wrapper in EXIT_WRAPPERS:
            for lifecycle_id in base_lifecycles:
                base = indexed.get((str(lifecycle_id), "base_delay1d_open", "existing_exit"))
                if base is None:
                    continue
                chosen_entry = choose_entry_policy(base, entry_wrapper)
                chosen_exit = choose_exit_policy(base, exit_wrapper)
                row = indexed.get((str(lifecycle_id), chosen_entry, chosen_exit))
                if row is None:
                    if chosen_entry != "base_delay1d_open":
                        continue
                    row = indexed.get((str(lifecycle_id), "base_delay1d_open", chosen_exit))
                if row is None:
                    continue
                out = dict(row)
                out["entry_wrapper"] = entry_wrapper
                out["exit_wrapper"] = exit_wrapper
                out["required_confirmation_entry_policy"] = chosen_entry
                out["conditional_exit_policy"] = chosen_exit
                add_partial_exit_fields(out, daily_maps, exit_wrapper)
                rows.append(out)
    return pd.DataFrame(rows).sort_values(["entry_wrapper", "exit_wrapper", "entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)


def choose_entry_policy(row: dict[str, object], entry_wrapper: str) -> str:
    if entry_wrapper == "base":
        return "base_delay1d_open"
    tier = str(row.get("signal_tier", "supply_only"))
    badvol = is_bad_vol(row)
    if entry_wrapper == "supply_badvol_confirm_vwap_or_volume":
        return "vwap_or_volume_confirm_60m" if tier == "supply_only" and badvol else "base_delay1d_open"
    if entry_wrapper == "weak_badvol_confirm_vwap_rs":
        return "vwap_rs_confirm_60m" if tier in {"supply_only", "both_contract_and_supply"} and badvol else "base_delay1d_open"
    if entry_wrapper == "noncontract_badvol_confirm_strict":
        return "strict_or_vwap_rs_volume_60m" if tier != "contract_only" and badvol else "base_delay1d_open"
    return "base_delay1d_open"


def choose_exit_policy(row: dict[str, object], exit_wrapper: str) -> str:
    if exit_wrapper in {"existing", "partial20_half", "partial30_third", "badvol_partial20_half"}:
        return "existing_exit"
    tier = str(row.get("signal_tier", "supply_only"))
    badvol = is_bad_vol(row)
    if exit_wrapper == "weak_hold20":
        return "hold20" if tier == "supply_only" and badvol else "existing_exit"
    if exit_wrapper == "weak_trail10":
        return "trail10_hold20" if tier == "supply_only" and badvol else "existing_exit"
    return "existing_exit"


def is_bad_vol(row: dict[str, object]) -> bool:
    atr = float(row.get("atr20_pct", 0.0) or 0.0)
    gap = abs(float(row.get("gap_pct", 0.0) or 0.0))
    range_pos = float(row.get("range_pos", 0.0) or 0.0)
    return bool(atr >= 0.07 or gap >= 0.06 or range_pos >= 0.98)


def add_partial_exit_fields(row: dict[str, object], daily_maps: dict[str, pd.DataFrame], exit_wrapper: str) -> None:
    row["partial_exit_enabled_flag"] = 0
    row["partial_exit_fraction"] = 0.0
    row["partial_exit_return"] = 0.0
    row["partial_exit_ts"] = ""
    if exit_wrapper not in {"partial20_half", "partial30_third", "badvol_partial20_half"}:
        return
    if exit_wrapper == "badvol_partial20_half" and not is_bad_vol(row):
        return
    threshold = 0.20 if exit_wrapper in {"partial20_half", "badvol_partial20_half"} else 0.30
    fraction = 0.50 if exit_wrapper in {"partial20_half", "badvol_partial20_half"} else 1.0 / 3.0
    symbol = str(row["symbol"]).upper()
    daily = daily_maps.get(symbol)
    if daily is None or daily.empty:
        return
    entry_ts = pd.Timestamp(row["entry_ts"])
    exit_ts = pd.Timestamp(row["simulated_exit_ts"])
    entry_date = entry_ts.tz_convert("America/New_York").date()
    exit_date = exit_ts.tz_convert("America/New_York").date()
    future = daily[(daily["trade_date"].ge(entry_date)) & (daily["trade_date"].le(exit_date))].copy()
    if future.empty:
        return
    hit = future[(future["close"] / max(float(row["entry_price"]), 1e-9) - 1.0).ge(threshold)].head(1)
    if hit.empty:
        return
    row["partial_exit_enabled_flag"] = 1
    row["partial_exit_fraction"] = fraction
    row["partial_exit_return"] = threshold
    row["partial_exit_ts"] = pd.Timestamp(hit.iloc[0]["timestamp"])


def build_account_grid(panel: pd.DataFrame, qqq_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    qqq = load_qqq_history(qqq_path)
    for entry_wrapper in ENTRY_WRAPPERS:
        for exit_wrapper in EXIT_WRAPPERS:
            selected = panel[panel["entry_wrapper"].eq(entry_wrapper) & panel["exit_wrapper"].eq(exit_wrapper)].copy()
            if selected.empty:
                continue
            for sizing_wrapper in SIZING_WRAPPERS:
                metrics, accepted = run_account(selected, sizing_wrapper)
                qqq_final = qqq_final_for_period(qqq, selected)
                rows.append(account_row("all", entry_wrapper, exit_wrapper, sizing_wrapper, selected, accepted, metrics, qqq_final))
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def build_oos_grid(panel: pd.DataFrame, qqq_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    qqq = load_qqq_history(qqq_path)
    for split_name in ["validation", "recent_oos"]:
        split = panel[panel["split_name"].astype(str).eq(split_name)].copy()
        for entry_wrapper in ENTRY_WRAPPERS:
            for exit_wrapper in EXIT_WRAPPERS:
                selected = split[split["entry_wrapper"].eq(entry_wrapper) & split["exit_wrapper"].eq(exit_wrapper)].copy()
                if selected.empty:
                    continue
                for sizing_wrapper in SIZING_WRAPPERS:
                    metrics, accepted = run_account(selected, sizing_wrapper)
                    qqq_final = qqq_final_for_period(qqq, selected)
                    rows.append(account_row(split_name, entry_wrapper, exit_wrapper, sizing_wrapper, selected, accepted, metrics, qqq_final))
    return pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)


def run_account(panel: pd.DataFrame, sizing_wrapper: str) -> tuple[dict[str, object], pd.DataFrame]:
    test = costed(panel, ROUND_TRIP_COST_BPS)
    ordered = test.sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    equity_value = 1.0
    peak = 1.0
    max_dd = 0.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []

    def close_until(ts: pd.Timestamp) -> None:
        nonlocal equity_value, peak, max_dd, open_positions
        still_open = []
        for pos in open_positions:
            partial_ts = pos.get("partial_ts")
            if partial_ts and not pos["partial_done"] and pd.Timestamp(partial_ts) <= ts:
                frac = float(pos["partial_fraction"])
                equity_value += float(pos["capital"]) * frac * float(pos["partial_return"])
                pos["capital"] = float(pos["capital"]) * (1.0 - frac)
                pos["partial_done"] = True
            if pd.Timestamp(pos["exit_ts"]) <= ts:
                equity_value += float(pos["capital"]) * float(pos["return"])
                peak = max(peak, equity_value)
                max_dd = min(max_dd, (equity_value / max(peak, 1e-9) - 1.0) * 100.0)
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_until(entry_ts)
        if len(open_positions) >= MAX_POSITIONS:
            continue
        weight = position_weight(row, sizing_wrapper)
        capital = equity_value * weight
        if capital <= 0:
            continue
        open_positions.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_from_entry"],
                "partial_ts": row.get("partial_exit_ts") or "",
                "partial_fraction": row.get("partial_exit_fraction", 0.0) or 0.0,
                "partial_return": row.get("partial_exit_return", 0.0) or 0.0,
                "partial_done": False,
            }
        )
        accepted = dict(row)
        accepted["position_weight"] = weight
        accepted_rows.append(accepted)
    close_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    if accepted.empty:
        return empty_quality(), accepted
    returns = pd.to_numeric(accepted["net_return_from_entry"], errors="coerce")
    return {
        "accepted_trade_count": int(len(accepted)),
        "final_capital_usd": float(INITIAL_CAPITAL_USD * equity_value),
        "capital_return_pct": float((equity_value - 1.0) * 100.0),
        "avg_net_return_pct": float(returns.mean() * 100.0),
        "win_rate": float(returns.gt(0).mean()),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
        "max_drawdown_pct": float(max_dd),
        "partial_exit_count": int(pd.to_numeric(accepted.get("partial_exit_enabled_flag", 0), errors="coerce").fillna(0).sum()),
    }, accepted


def position_weight(row: dict[str, object], sizing_wrapper: str) -> float:
    if sizing_wrapper == "equal":
        return 0.20
    tier = str(row.get("signal_tier", "supply_only"))
    badvol = is_bad_vol(row)
    if sizing_wrapper == "soft_tier":
        return {"both_contract_and_supply": 0.21, "contract_only": 0.20, "supply_only": 0.18}.get(tier, 0.18)
    if sizing_wrapper == "quality_vol":
        if badvol and tier == "supply_only":
            return 0.16
        if badvol:
            return 0.19
        return 0.21
    if badvol and tier == "supply_only":
        return 0.15
    if tier == "both_contract_and_supply":
        return 0.22 if not badvol else 0.20
    if tier == "contract_only":
        return 0.20
    return 0.18


def empty_quality() -> dict[str, object]:
    return {
        "accepted_trade_count": 0,
        "final_capital_usd": INITIAL_CAPITAL_USD,
        "capital_return_pct": 0.0,
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "max_drawdown_pct": 0.0,
        "partial_exit_count": 0,
    }


def account_row(
    split_name: str,
    entry_wrapper: str,
    exit_wrapper: str,
    sizing_wrapper: str,
    selected: pd.DataFrame,
    accepted: pd.DataFrame,
    metrics: dict[str, object],
    qqq_final: float,
) -> dict[str, object]:
    final = float(metrics["final_capital_usd"])
    return {
        "split_name": split_name,
        "entry_wrapper": entry_wrapper,
        "exit_wrapper": exit_wrapper,
        "sizing_wrapper": sizing_wrapper,
        "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
        "source_trade_count": int(len(selected)),
        "accepted_trade_count": int(len(accepted)),
        "partial_exit_count": int(metrics["partial_exit_count"]),
        "final_capital_usd": final,
        "capital_return_pct": float(metrics["capital_return_pct"]),
        "avg_net_return_pct": float(metrics["avg_net_return_pct"]),
        "win_rate": float(metrics["win_rate"]),
        "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
        "max_drawdown_pct": float(metrics["max_drawdown_pct"]),
        "qqq_final_capital_usd": float(qqq_final),
        "beats_qqq_flag": int(final > qqq_final),
        "label_used_in_assignment_flag": 0,
        "symbol_blacklist_used_flag": 0,
        "theme_blacklist_used_flag": 0,
    }


def build_source_audit(execution: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "task643_execution_rows": int(len(execution)),
                "conditional_candidate_rows": int(len(selected)),
                "gpt_design_captured_flag": int(TASK644_GPT_DESIGN.exists()),
                "label_used_in_assignment_flag": 0,
                "symbol_blacklist_used_flag": 0,
                "theme_blacklist_used_flag": 0,
                "global_confirmation_only_flag": 0,
                "atr_only_sizing_only_flag": 0,
            }
        ]
    )


def build_pass_fail(account: pd.DataFrame, oos: pd.DataFrame, source_audit: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    best = account.iloc[0]
    base_final = float(task639["best_50bp_final_capital_usd"])
    base_dd = float(task639["best_50bp_max_drawdown_pct"])
    final_eps = 0.01
    dd_eps = 0.01
    validation = matching_oos(oos, best, "validation")
    recent = matching_oos(oos, best, "recent_oos")
    oos_pass = int(
        not validation.empty
        and not recent.empty
        and float(validation.iloc[0]["final_capital_usd"]) > float(validation.iloc[0]["qqq_final_capital_usd"])
        and float(recent.iloc[0]["final_capital_usd"]) > float(recent.iloc[0]["qqq_final_capital_usd"])
    )
    return pd.DataFrame(
        [
            {
                "gate": "gpt_design_captured",
                "pass_flag": int(source_audit.iloc[0]["gpt_design_captured_flag"]),
                "observed_value": f"captured={int(source_audit.iloc[0]['gpt_design_captured_flag'])}",
                "required_value": "GPT design review must be captured as review-only input",
            },
            {
                "gate": "best_candidate_beats_task639_return",
                "pass_flag": int(float(best["final_capital_usd"]) > base_final + final_eps),
                "observed_value": f"best=${float(best['final_capital_usd']):.2f}; task639=${base_final:.2f}",
                "required_value": "best final capital must exceed Task639",
            },
            {
                "gate": "best_candidate_reduces_task639_drawdown",
                "pass_flag": int(float(best["max_drawdown_pct"]) > base_dd + dd_eps),
                "observed_value": f"best_dd={float(best['max_drawdown_pct']):.2f}%; task639_dd={base_dd:.2f}%",
                "required_value": "best drawdown must be less severe than Task639",
            },
            {
                "gate": "same_config_validation_and_recent_beat_qqq",
                "pass_flag": oos_pass,
                "observed_value": oos_observed(validation, recent),
                "required_value": "same config must beat QQQ in validation and recent OOS",
            },
            {
                "gate": "no_shortcut_blacklist_or_label",
                "pass_flag": 1,
                "observed_value": "symbol_blacklist=0; theme_blacklist=0; label_assignment=0",
                "required_value": "no blacklist or after-the-fact label shortcut",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "research backtest only",
                "required_value": "requires live rule lock, latency audit, source readiness, and paper-shadow replay",
            },
        ]
    )


def matching_oos(oos: pd.DataFrame, best: pd.Series, split_name: str) -> pd.DataFrame:
    return oos[
        oos["split_name"].eq(split_name)
        & oos["entry_wrapper"].eq(best["entry_wrapper"])
        & oos["exit_wrapper"].eq(best["exit_wrapper"])
        & oos["sizing_wrapper"].eq(best["sizing_wrapper"])
    ].copy()


def oos_observed(validation: pd.DataFrame, recent: pd.DataFrame) -> str:
    if validation.empty or recent.empty:
        return "missing matching OOS rows"
    v = validation.iloc[0]
    r = recent.iloc[0]
    return f"validation=${float(v['final_capital_usd']):.2f}/QQQ ${float(v['qqq_final_capital_usd']):.2f}; recent=${float(r['final_capital_usd']):.2f}/QQQ ${float(r['qqq_final_capital_usd']):.2f}"


def build_decision(account: pd.DataFrame, oos: pd.DataFrame, pass_fail: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    best = account.iloc[0]
    validation = matching_oos(oos, best, "validation")
    recent = matching_oos(oos, best, "recent_oos")
    gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}
    full_pass = int(
        gates["best_candidate_beats_task639_return"] == 1
        and gates["best_candidate_reduces_task639_drawdown"] == 1
        and gates["same_config_validation_and_recent_beat_qqq"] == 1
    )
    return pd.DataFrame(
        [
            {
                "decision": "PASS_FIRM_GRADE_CONDITIONAL_WRAPPER_CANDIDATE_NOT_ACCEPTED" if full_pass else "FAIL_NO_FIRM_GRADE_CONDITIONAL_WRAPPER_OVER_TASK639",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "best_entry_wrapper": str(best["entry_wrapper"]),
                "best_exit_wrapper": str(best["exit_wrapper"]),
                "best_sizing_wrapper": str(best["sizing_wrapper"]),
                "best_final_capital_usd": float(best["final_capital_usd"]),
                "best_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "task639_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "task639_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
                "best_validation_final_capital_usd": 0.0 if validation.empty else float(validation.iloc[0]["final_capital_usd"]),
                "best_validation_qqq_final_capital_usd": 0.0 if validation.empty else float(validation.iloc[0]["qqq_final_capital_usd"]),
                "best_recent_final_capital_usd": 0.0 if recent.empty else float(recent.iloc[0]["final_capital_usd"]),
                "best_recent_qqq_final_capital_usd": 0.0 if recent.empty else float(recent.iloc[0]["qqq_final_capital_usd"]),
                "next_action": "If no wrapper passes, stop wrapper over-optimization and return to source/content interpretation or build deeper live microstructure evidence.",
            }
        ]
    )


def render_report(account: pd.DataFrame, oos: pd.DataFrame, source_audit: pd.DataFrame, pass_fail: pd.DataFrame, decision: pd.DataFrame) -> str:
    dec = decision.iloc[0]
    return "\n".join(
        [
            "# Task644 Firm-Grade Conditional Wrapper",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: `{dec['decision']}`",
            "- Strategy acceptance: `NOT_ACCEPTED`",
            "- Real capital: `FORBIDDEN`",
            f"- Best config: `{dec['best_entry_wrapper']}` / `{dec['best_exit_wrapper']}` / `{dec['best_sizing_wrapper']}`",
            f"- Best final: ${float(dec['best_final_capital_usd']):.2f}",
            f"- Best DD: {float(dec['best_max_drawdown_pct']):.2f}%",
            f"- Task639: ${float(dec['task639_final_capital_usd']):.2f}, DD {float(dec['task639_max_drawdown_pct']):.2f}%",
            "",
            "## Quant Expert Report",
            "",
            "Task644 implements the GPT-reviewed firm-grade redesign: conditional confirmation, signal-quality-aware volatility sizing, soft tier sizing, and partial capital recycling.",
            "",
            "### Source Audit",
            "",
            table(source_audit),
            "",
            "### Top Full-Period Candidates",
            "",
            table(account.head(25)),
            "",
            "### Top OOS Rows",
            "",
            table(oos.head(40)),
            "",
            "### Pass/Fail Matrix",
            "",
            table(pass_fail),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- We avoided global filters, ATR-only sizing, short-exit-only logic, blacklists, and loser labels.",
            "- Conditional wrappers are tested against Task639 using the same $1000 account and 50bp cost.",
            "- Real trading remains forbidden even if a research candidate passes.",
            "",
            "## Artifact Manifest",
            "",
            "- `task_644_gpt_design_packet.txt`",
            "- `task_644_gpt_design_response.md`",
            "- `task_644_gpt_result_packet.txt`",
            "- `task_644_gpt_result_response.md`",
            "- `task_644_conditional_candidate_panel.csv`",
            "- `task_644_account_grid.csv`",
            "- `task_644_oos_grid.csv`",
            "- `task_644_source_audit.csv`",
            "- `task_644_pass_fail_matrix.csv`",
            "- `task_644_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
        ]
    )


def table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    safe = frame.copy().where(pd.notna(frame), "")
    columns = [str(column) for column in safe.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in safe.astype(str).to_dict(orient="records"):
        lines.append("| " + " | ".join(row[column] for column in safe.columns) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    build_task644_firm_grade_conditional_wrapper(out_dir=args.out_dir)


if __name__ == "__main__":
    main()
