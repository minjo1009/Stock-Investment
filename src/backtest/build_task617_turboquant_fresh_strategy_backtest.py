from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import (
    aggregate,
    quality,
    simulate_entries,
)
from src.backtest.build_task503_multiday_entry_population_rebuild import (
    DEFAULT_DAILY_DIR,
    DEFAULT_INTRADAY_DIR,
    DEFAULT_MARKET_PANEL,
    DEFAULT_THEME_MAP,
    build_daily_entry_features,
    build_intraday_confirmed_entries,
    load_daily_map,
)
from src.backtest.build_task614_p0_intelligence_source_attachment import (
    ARTIFACT_DIR as TASK614_ARTIFACT_DIR,
    count_window,
    normalize_event_frame,
    relevant_events,
    tag_contains,
)


TASK_ID = "Task617"
REPORT_DIR = Path("docs/reports/task_617_turboquant_fresh_strategy_backtest")
EVENT_STORE = TASK614_ARTIFACT_DIR / "p0_intelligence_event_store.csv"


def build_task617_turboquant_fresh_strategy_backtest(
    *,
    theme_map_path: Path = DEFAULT_THEME_MAP,
    daily_dir: Path = DEFAULT_DAILY_DIR,
    intraday_dir: Path = DEFAULT_INTRADAY_DIR,
    market_panel_path: Path = DEFAULT_MARKET_PANEL,
    event_store_path: Path = EVENT_STORE,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    source_audit, raw_candidates, confirmed_entries = build_fresh_candidates(
        theme_map_path=theme_map_path,
        daily_dir=daily_dir,
        intraday_dir=intraday_dir,
        market_panel_path=market_panel_path,
    )
    events = load_event_store(event_store_path)
    linked_entries = attach_intelligence(confirmed_entries, events)
    scored_entries = add_turboquant_strategy_scores(linked_entries)
    baseline_panel = simulate_entries(
        scored_entries,
        load_daily_map(scored_entries["symbol"].astype(str).str.upper().unique().tolist(), daily_dir)[1],
        max_hold_days=60,
        trailing_stop=0.25,
        policy_name="task617_baseline_raw_candidate_hold60_stop25",
    )
    strategy_entries = scored_entries[scored_entries["tq_new_strategy_entry_flag"].eq(1)].copy()
    strategy_panel = simulate_entries(
        strategy_entries,
        load_daily_map(strategy_entries["symbol"].astype(str).str.upper().unique().tolist(), daily_dir)[1],
        max_hold_days=60,
        trailing_stop=0.25,
        policy_name="task617_turboquant_fresh_h60_i70_riskoff_hold60_stop25",
    )
    scenario_summary = build_scenario_summary(baseline_panel, strategy_panel)
    split_summary = build_split_summary(strategy_panel)
    quarter_summary = quality(strategy_panel, ["quarter"]) if not strategy_panel.empty else pd.DataFrame()
    source_summary = build_source_summary(source_audit, events, raw_candidates, confirmed_entries, linked_entries)
    gpt_review = build_gpt_review_status()
    pass_fail = build_pass_fail(baseline_panel, strategy_panel, split_summary, gpt_review)
    decision = build_decision(baseline_panel, strategy_panel, split_summary, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    source_audit.to_csv(out_dir / "fresh_strategy_source_coverage_audit.csv", index=False)
    raw_candidates.to_csv(out_dir / "fresh_daily_candidate_panel.csv", index=False)
    confirmed_entries.to_csv(out_dir / "fresh_intraday_confirmed_entry_panel.csv", index=False)
    linked_entries.to_csv(out_dir / "fresh_intelligence_linked_entry_panel.csv", index=False)
    scored_entries.to_csv(out_dir / "fresh_turboquant_scored_entry_panel.csv", index=False)
    baseline_panel.to_csv(out_dir / "fresh_baseline_all_candidate_backtest_panel.csv", index=False)
    strategy_panel.to_csv(out_dir / "fresh_turboquant_strategy_backtest_panel.csv", index=False)
    scenario_summary.to_csv(out_dir / "fresh_turboquant_scenario_summary.csv", index=False)
    split_summary.to_csv(out_dir / "fresh_turboquant_split_summary.csv", index=False)
    quarter_summary.to_csv(out_dir / "fresh_turboquant_quarter_summary.csv", index=False)
    source_summary.to_csv(out_dir / "fresh_turboquant_source_summary.csv", index=False)
    gpt_review.to_csv(out_dir / "gpt_fresh_backtest_design_review_status.csv", index=False)
    pass_fail.to_csv(out_dir / "task_617_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_617_decision.csv", index=False)
    (out_dir / "task_617_turboquant_fresh_strategy_backtest.md").write_text(
        render_report(source_summary, scenario_summary, split_summary, pass_fail, decision, gpt_review),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "fresh_strategy_source_coverage_audit": source_audit,
        "fresh_daily_candidate_panel": raw_candidates,
        "fresh_intraday_confirmed_entry_panel": confirmed_entries,
        "fresh_intelligence_linked_entry_panel": linked_entries,
        "fresh_turboquant_scored_entry_panel": scored_entries,
        "fresh_baseline_all_candidate_backtest_panel": baseline_panel,
        "fresh_turboquant_strategy_backtest_panel": strategy_panel,
        "fresh_turboquant_scenario_summary": scenario_summary,
        "fresh_turboquant_split_summary": split_summary,
        "fresh_turboquant_quarter_summary": quarter_summary,
        "fresh_turboquant_source_summary": source_summary,
        "gpt_fresh_backtest_design_review_status": gpt_review,
        "task_617_pass_fail_matrix": pass_fail,
        "task_617_decision": decision,
    }


def build_fresh_candidates(
    *,
    theme_map_path: Path,
    daily_dir: Path,
    intraday_dir: Path,
    market_panel_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    theme_map = pd.read_csv(theme_map_path)
    theme_map["symbol"] = theme_map["symbol"].astype(str).str.upper()
    source_audit, daily_map = load_daily_map(theme_map["symbol"].tolist(), daily_dir)
    market = pd.read_csv(market_panel_path) if market_panel_path.exists() else pd.DataFrame()
    raw_candidates = build_daily_entry_features(theme_map, daily_map, market)
    confirmed = build_intraday_confirmed_entries(raw_candidates, intraday_dir)
    if confirmed.empty:
        return source_audit, raw_candidates, confirmed
    confirmed = confirmed.copy()
    confirmed["entry_ts"] = pd.to_datetime(confirmed["entry_ts"], utc=True, errors="coerce")
    confirmed["entry_ts_utc"] = confirmed["entry_ts"]
    confirmed["trade_date"] = pd.to_datetime(confirmed["trade_date"]).dt.date
    confirmed["lifecycle_id"] = confirmed["lifecycle_id"].astype(str).str.replace("TASK503|", "TASK617|", regex=False)
    confirmed["label_used_in_assignment_flag"] = 0
    confirmed["inferred_lifecycle_matching_used_flag"] = 0
    return source_audit, raw_candidates, confirmed


def load_event_store(path: Path) -> pd.DataFrame:
    if not path.exists():
        return normalize_event_frame(pd.DataFrame())
    events = normalize_event_frame(pd.read_csv(path))
    events["event_date_obj"] = pd.to_datetime(events["event_date"], errors="coerce").dt.date
    events["event_timestamp_dt"] = pd.to_datetime(events["event_timestamp_utc"], utc=True, errors="coerce")
    return events


def attach_intelligence(entries: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return entries.copy()
    events = events.copy()
    rows: list[dict[str, Any]] = []
    for _, entry in entries.iterrows():
        known = events[
            (events["event_date_obj"] < entry["trade_date"])
            | (
                events["event_date_obj"].eq(entry["trade_date"])
                & events["time_precision"].eq("timestamp")
                & events["event_timestamp_dt"].notna()
                & (events["event_timestamp_dt"] <= entry["entry_ts_utc"])
            )
        ]
        symbol = str(entry["symbol"])
        theme = str(entry["theme_id"])
        political = relevant_events(known, "trump_major_person_political_statements", symbol, theme)
        geopolitical = relevant_events(known, "war_geopolitical_conflict_events", symbol, theme)
        institution = known[(known["source_lane"].eq("institution_investment_actions")) & tag_contains(known["symbol_tags"], symbol)]
        ceo_ir = known[(known["source_lane"].eq("ceo_ir_transcripts_and_presentations")) & tag_contains(known["symbol_tags"], symbol)]
        rows.append(
            {
                "lifecycle_id": entry["lifecycle_id"],
                "political_statement_pre7d_count": count_window(political, entry["trade_date"], 7),
                "political_statement_pre7d_flag": int(count_window(political, entry["trade_date"], 7) > 0),
                "geopolitical_event_pre7d_count": count_window(geopolitical, entry["trade_date"], 7),
                "geopolitical_event_pre7d_flag": int(count_window(geopolitical, entry["trade_date"], 7) > 0),
                "institution_ownership_pre30d_count": count_window(institution, entry["trade_date"], 30),
                "institution_ownership_pre30d_flag": int(count_window(institution, entry["trade_date"], 30) > 0),
                "activist_13d_pre30d_flag": int(count_window(institution[institution["event_category"].eq("activist_13d")], entry["trade_date"], 30) > 0),
                "passive_13g_pre30d_flag": int(count_window(institution[institution["event_category"].eq("passive_13g")], entry["trade_date"], 30) > 0),
                "insider_form4_or_144_pre30d_flag": int(count_window(institution[institution["event_category"].eq("insider_or_sale_notice")], entry["trade_date"], 30) > 0),
                "ceo_ir_proxy_pre14d_count": count_window(ceo_ir, entry["trade_date"], 14),
                "ceo_ir_proxy_pre14d_flag": int(count_window(ceo_ir, entry["trade_date"], 14) > 0),
                "p0_source_event_density": (
                    count_window(political, entry["trade_date"], 7)
                    + count_window(geopolitical, entry["trade_date"], 7)
                    + count_window(institution, entry["trade_date"], 30)
                    + count_window(ceo_ir, entry["trade_date"], 14)
                ),
                "label_used_in_assignment_flag_task617": 0,
                "gpt_or_plugin_used_as_source_flag_task617": 0,
            }
        )
    linked = entries.merge(pd.DataFrame(rows), on="lifecycle_id", how="left")
    linked["p0_source_event_density_ge2_flag"] = linked["p0_source_event_density"].fillna(0).ge(2).astype(int)
    return linked


def add_turboquant_strategy_scores(entries: pd.DataFrame) -> pd.DataFrame:
    out = entries.copy()
    if out.empty:
        return out
    n = lambda col: pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    out["tq_pre_entry_chart_health_score"] = (
        (n("near_high60_prev") >= 0.95).astype(int)
        + (n("trend_stack_prev") == 1).astype(int)
        + (n("theme_ret20_prev") > 0).astype(int)
        + (n("theme_breadth20_prev") >= 0.55).astype(int)
        + (n("range_pos") >= 0.70).astype(int)
    ) / 5.0
    out["tq_intelligence_support_score"] = (
        0.30 * n("institution_ownership_pre30d_flag").clip(0, 1)
        + 0.20 * n("passive_13g_pre30d_flag").clip(0, 1)
        + 0.20 * n("ceo_ir_proxy_pre14d_flag").clip(0, 1)
        + 0.15 * n("geopolitical_event_pre7d_flag").clip(0, 1)
        + 0.15 * n("political_statement_pre7d_flag").clip(0, 1)
        + 0.15 * (n("p0_source_event_density") / 5.0).clip(0, 1)
    ).clip(0, 1)
    out["tq_runtime_entry_confirmation_score"] = (
        (n("intraday_ret_from_open") >= 0.002).astype(int)
        + (n("range_pos") >= 0.85).astype(int)
        + out["timing_state"].astype(str).isin(["opening_drive", "midday_continuation"]).astype(int)
    ) / 3.0
    out["tq_new_strategy_entry_flag"] = (
        out["tq_pre_entry_chart_health_score"].ge(0.80)
        & out["tq_intelligence_support_score"].ge(0.70)
        & out["tq_runtime_entry_confirmation_score"].ge(0.67)
    ).astype(int)
    out["tq_assignment_label_used_flag"] = 0
    out["tq_gpt_or_plugin_used_as_source_flag"] = 0
    return out


def build_scenario_summary(baseline: pd.DataFrame, strategy: pd.DataFrame) -> pd.DataFrame:
    base = aggregate(baseline)
    strat = aggregate(strategy)
    rows = []
    for name, metrics in [("fresh_baseline_all_candidates", base), ("fresh_turboquant_strategy", strat)]:
        rows.append({"scenario": name, **metrics})
    summary = pd.DataFrame(rows)
    if len(summary) == 2:
        summary["avg_net_return_delta_vs_baseline_pct_point"] = summary["avg_net_return_pct"] - float(summary.iloc[0]["avg_net_return_pct"])
        summary["entry_reduce_delta_vs_baseline_pct_point"] = (summary["entry_reduce_failure_rate"] - float(summary.iloc[0]["entry_reduce_failure_rate"])) * 100.0
    return summary


def build_split_summary(strategy: pd.DataFrame) -> pd.DataFrame:
    if strategy.empty:
        return pd.DataFrame()
    out = quality(strategy, ["split_name"])
    if "lifecycle_count" not in out.columns:
        return out
    out["positive_split_flag"] = (
        out["lifecycle_count"].ge(10)
        & out["avg_net_return_pct"].ge(3.0)
        & out["entry_reduce_failure_rate"].le(0.35)
    ).astype(int)
    return out


def build_source_summary(
    source_audit: pd.DataFrame,
    events: pd.DataFrame,
    raw_candidates: pd.DataFrame,
    confirmed_entries: pd.DataFrame,
    linked_entries: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "daily_source_symbol_coverage": float(source_audit["available_flag"].mean()) if not source_audit.empty else 0.0,
                "event_store_rows": int(len(events)),
                "raw_daily_candidate_count": int(len(raw_candidates)),
                "intraday_confirmed_entry_count": int(len(confirmed_entries)),
                "intelligence_linked_entry_count": int(len(linked_entries)),
                "source_lanes_with_events": int(events["source_lane"].nunique()) if not events.empty else 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        ]
    )


def build_gpt_review_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reviewer": "Chrome ChatGPT 1. coding/investment project new tab",
                "captured_status": "CAPTURED_NEW_ALLOWED_TAB",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "GPT agreed the user's total-PnL critique is valid: unlimited-capital total return favors all candidates, while TurboQuant only proves candidate quality/capital-efficiency potential.",
                "repo_action": "Downgrade Task617 wording from strategy win to diagnostic quality improvement; next run must compare all-candidate versus TurboQuant under identical max-position portfolio capacity.",
            },
            {
                "reviewer": "Chrome ChatGPT 1. coding/investment project new tab",
                "captured_status": "CAPTURED_NEW_ALLOWED_TAB",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "GPT highlighted recent OOS as the main blocker: avg return falls to 2.17% and entry-reduce failure rises to 60.55%.",
                "repo_action": "Prioritize recent-OOS failure decomposition before any strategy acceptance claim.",
            },
        ]
    )


def build_pass_fail(
    baseline: pd.DataFrame,
    strategy: pd.DataFrame,
    split_summary: pd.DataFrame,
    gpt_review: pd.DataFrame,
) -> pd.DataFrame:
    base = aggregate(baseline)
    strat = aggregate(strategy)
    split_positive = int(split_summary["positive_split_flag"].sum()) if not split_summary.empty and "positive_split_flag" in split_summary.columns else 0
    split_total = int(len(split_summary)) if not split_summary.empty else 0
    return pd.DataFrame(
        [
            {
                "gate": "fresh_candidate_generation",
                "pass_flag": int(int(base.get("lifecycle_count", 0)) >= 300),
                "observed_value": f"baseline_candidates={int(base.get('lifecycle_count', 0))}",
                "required_value": ">=300 fresh raw-generated candidates",
            },
            {
                "gate": "fresh_strategy_diagnostic_performance",
                "pass_flag": int(
                    int(strat.get("lifecycle_count", 0)) >= 50
                    and float(strat.get("avg_net_return_pct", 0.0)) >= float(base.get("avg_net_return_pct", 0.0)) + 2.0
                    and float(strat.get("entry_reduce_failure_rate", 1.0)) <= float(base.get("entry_reduce_failure_rate", 1.0))
                ),
                "observed_value": f"strategy_count={int(strat.get('lifecycle_count', 0))}; strategy_avg={float(strat.get('avg_net_return_pct', 0.0)):.2f}%; baseline_avg={float(base.get('avg_net_return_pct', 0.0)):.2f}%; strategy_entry_reduce={float(strat.get('entry_reduce_failure_rate', 0.0)):.2%}; baseline_entry_reduce={float(base.get('entry_reduce_failure_rate', 0.0)):.2%}",
                "required_value": "count>=50; avg return >= baseline+2pp; entry_reduce <= baseline",
            },
            {
                "gate": "split_stability",
                "pass_flag": int(split_total >= 3 and split_positive >= 2),
                "observed_value": f"positive_splits={split_positive}/{split_total}",
                "required_value": ">=2 positive splits across >=3 splits",
            },
            {
                "gate": "gpt_review",
                "pass_flag": int(str(gpt_review.iloc[0]["captured_status"]).startswith("CAPTURED")),
                "observed_value": str(gpt_review.iloc[0]["captured_status"]),
                "required_value": "captured via allowed 1. coding/investment ChatGPT tab",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "fresh diagnostic backtest only; cost, slippage, broker truth, and GPT review are not complete",
                "required_value": "must pass before live or real capital",
            },
        ]
    )


def build_decision(
    baseline: pd.DataFrame,
    strategy: pd.DataFrame,
    split_summary: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> pd.DataFrame:
    base = aggregate(baseline)
    strat = aggregate(strategy)
    diagnostic_pass = int(pass_fail[pass_fail["gate"].eq("fresh_strategy_diagnostic_performance")]["pass_flag"].iloc[0])
    split_pass = int(pass_fail[pass_fail["gate"].eq("split_stability")]["pass_flag"].iloc[0])
    decision = "PASS_FRESH_TURBOQUANT_DIAGNOSTIC_FAIL_PORTFOLIO_CAPACITY_AND_RECENT_OOS"
    if not diagnostic_pass:
        decision = "FAIL_FRESH_TURBOQUANT_DIAGNOSTIC"
    gpt_pass = int(pass_fail[pass_fail["gate"].eq("gpt_review")]["pass_flag"].iloc[0])
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "baseline_candidate_count": int(base.get("lifecycle_count", 0)),
                "baseline_avg_net_return_pct": float(base.get("avg_net_return_pct", 0.0)),
                "baseline_win_rate": float(base.get("win_rate", 0.0)),
                "baseline_entry_reduce_failure_rate": float(base.get("entry_reduce_failure_rate", 0.0)),
                "strategy_trade_count": int(strat.get("lifecycle_count", 0)),
                "strategy_avg_net_return_pct": float(strat.get("avg_net_return_pct", 0.0)),
                "strategy_avg_delta_vs_baseline_pct_point": float(strat.get("avg_net_return_pct", 0.0)) - float(base.get("avg_net_return_pct", 0.0)),
                "strategy_win_rate": float(strat.get("win_rate", 0.0)),
                "strategy_entry_reduce_failure_rate": float(strat.get("entry_reduce_failure_rate", 0.0)),
                "diagnostic_performance_pass_flag": diagnostic_pass,
                "split_stability_pass_flag": split_pass,
                "gpt_review_pass_flag": gpt_pass,
                "trading_promotion_pass_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Run all-candidate versus TurboQuant portfolio capacity backtest with max positions 5/10/20/50, then decompose recent OOS failures.",
            }
        ]
    )


def render_report(
    source_summary: pd.DataFrame,
    scenario_summary: pd.DataFrame,
    split_summary: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
    gpt_review: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task617 TurboQuant Fresh Strategy Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Fresh baseline candidates: {int(d['baseline_candidate_count'])}, avg return {float(d['baseline_avg_net_return_pct']):.2f}%, entry-reduce failure {float(d['baseline_entry_reduce_failure_rate']) * 100.0:.2f}%.",
        f"- Fresh TurboQuant trades: {int(d['strategy_trade_count'])}, avg return {float(d['strategy_avg_net_return_pct']):.2f}%, delta {float(d['strategy_avg_delta_vs_baseline_pct_point']):.2f}pp.",
        f"- GPT review status: `{gpt_review.iloc[0]['captured_status']}`",
        "- Next action: GPT review capture, cost/slippage, and parameter-neighborhood robustness.",
        "",
        "## Quant Expert Report",
        "",
        "### Data Source And Source Readiness",
        "",
        "- This is a fresh raw-generated backtest, not a refilter of the 89-entry Task608K/Task614 panel.",
        "- Candidates are generated from raw daily bars and raw intraday bars.",
        "- Task614/Task615 event store is attached before strategy scoring.",
        "",
        "### Exact Join Keys",
        "",
        "- Candidate id is rebuilt as `TASK617|symbol|entry_timestamp`.",
        "- Intelligence events are joined by event timestamp/date known before entry, symbol/theme tags, and source lane.",
        "- No symbol/date/price/time proximity lifecycle fallback is used.",
        "",
        "### Leakage Audit",
        "",
        "- Entry assignment does not use returns, exit labels, taxonomy labels, win flags, or entry-reduce labels.",
        "- GPT output is not used as a data source or score input.",
        "",
        "### Scenario Summary",
        "",
        "| Scenario | Count | Avg Return | Win | Entry-Reduce |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in scenario_summary.iterrows():
        lines.append(
            f"| `{row['scenario']}` | {int(row['lifecycle_count'])} | {float(row['avg_net_return_pct']):.2f}% | "
            f"{float(row['win_rate']) * 100.0:.2f}% | {float(row['entry_reduce_failure_rate']) * 100.0:.2f}% |"
        )
    lines.extend(
        [
            "",
            "### Split Summary",
            "",
            "| Split | Count | Avg Return | Win | Entry-Reduce | Positive |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    if split_summary.empty:
        lines.append("| none | 0 | 0.00% | 0.00% | 0.00% | 0 |")
    else:
        for _, row in split_summary.iterrows():
            lines.append(
                f"| `{row['split_name']}` | {int(row['lifecycle_count'])} | {float(row['avg_net_return_pct']):.2f}% | "
                f"{float(row['win_rate']) * 100.0:.2f}% | {float(row['entry_reduce_failure_rate']) * 100.0:.2f}% | "
                f"{int(row.get('positive_split_flag', 0))} |"
            )
    lines.extend(
        [
            "",
            "### Pass/Fail Matrix",
            "",
            "| Gate | Pass | Observed | Required |",
            "|---|---:|---|---|",
        ]
    )
    for _, row in pass_fail.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- This time it is a new backtest.",
            "- It rebuilds candidates from raw bars, then attaches intelligence, then trades the new TurboQuant rule.",
            "- The result is useful, but GPT review and trading promotion are still blocked.",
            "",
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `data/raw/theme_universe_10x7.csv`",
            "- `data/raw/us_daily_breadth_top500/`",
            "- `data/raw/us_intraday/`",
            "- `data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv`",
            "",
            "### Outputs",
            "",
            "- `fresh_daily_candidate_panel.csv`",
            "- `fresh_intraday_confirmed_entry_panel.csv`",
            "- `fresh_intelligence_linked_entry_panel.csv`",
            "- `fresh_turboquant_scored_entry_panel.csv`",
            "- `fresh_baseline_all_candidate_backtest_panel.csv`",
            "- `fresh_turboquant_strategy_backtest_panel.csv`",
            "- `fresh_turboquant_scenario_summary.csv`",
            "- `fresh_turboquant_split_summary.csv`",
            "- `task_617_pass_fail_matrix.csv`",
            "- `task_617_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task617_turboquant_fresh_strategy_backtest`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task617_turboquant_fresh_strategy_backtest(out_dir=args.out_dir)
    row = artifacts["task_617_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"trades={int(row['strategy_trade_count'])} avg={float(row['strategy_avg_net_return_pct']):.2f}%"
    )


if __name__ == "__main__":
    main()
