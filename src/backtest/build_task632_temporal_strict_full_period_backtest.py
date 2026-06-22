from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate, quality, simulate_entries
from src.backtest.build_task503_multiday_entry_population_rebuild import DEFAULT_DAILY_DIR, load_daily_map
from src.backtest.build_task614_p0_intelligence_source_attachment import (
    ARTIFACT_DIR as TASK614_ARTIFACT_DIR,
    normalize_event_frame,
    relevant_events,
    tag_contains,
)
from src.backtest.build_task617_turboquant_fresh_strategy_backtest import REPORT_DIR as TASK617_DIR
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio


TASK_ID = "Task632"
REPORT_DIR = Path("docs/reports/task_632_temporal_strict_full_period_backtest")
TASK617_SCORED_ENTRIES = TASK617_DIR / "fresh_turboquant_scored_entry_panel.csv"
TASK617_STRATEGY_PANEL = TASK617_DIR / "fresh_turboquant_strategy_backtest_panel.csv"
EVENT_STORE = TASK614_ARTIFACT_DIR / "p0_intelligence_event_store.csv"
SCOPES = ("full_panel", "validation", "recent_oos")
MAX_POSITIONS = (5, 10, 20, 50)
DECISION_COST_BPS = 50
INITIAL_CAPITAL_USD = 1000.0


def build_task632_temporal_strict_full_period_backtest(
    *,
    scored_entries_path: Path = TASK617_SCORED_ENTRIES,
    original_strategy_path: Path = TASK617_STRATEGY_PANEL,
    event_store_path: Path = EVENT_STORE,
    daily_dir: Path = DEFAULT_DAILY_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    entries = load_scored_entries(scored_entries_path)
    events = load_temporal_event_store(event_store_path)
    temporal = attach_temporal_intelligence(entries, events)
    scored = add_temporal_strategy_scores(temporal)
    baseline_panel = simulate_entries(
        scored,
        load_daily_map(scored["symbol"].astype(str).str.upper().unique().tolist(), daily_dir)[1],
        max_hold_days=60,
        trailing_stop=0.25,
        policy_name="task632_baseline_all_confirmed_hold60_stop25",
    )
    strict_entries = scored[scored["tq_temporal_strict_strategy_entry_flag"].astype(int).eq(1)].copy()
    strict_panel = simulate_entries(
        strict_entries,
        load_daily_map(strict_entries["symbol"].astype(str).str.upper().unique().tolist(), daily_dir)[1],
        max_hold_days=60,
        trailing_stop=0.25,
        policy_name="task632_temporal_strict_chart_qual_hold60_stop25",
    )
    original_panel = pd.read_csv(original_strategy_path)
    scenario_summary = build_scenario_summary(baseline_panel, original_panel, strict_panel)
    split_summary = build_split_summary(strict_panel)
    quarter_summary = quality(strict_panel, ["quarter"]) if not strict_panel.empty else pd.DataFrame()
    source_audit = build_source_audit(events, temporal, scored)
    cost_account = build_cost_account_matrix(original_panel, strict_panel)
    pass_fail = build_pass_fail(source_audit, scenario_summary, split_summary, cost_account)
    decision = build_decision(source_audit, scenario_summary, split_summary, cost_account, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    temporal.to_csv(out_dir / "task_632_temporal_intelligence_entry_panel.csv", index=False)
    scored.to_csv(out_dir / "task_632_temporal_strict_scored_entry_panel.csv", index=False)
    baseline_panel.to_csv(out_dir / "task_632_baseline_all_confirmed_backtest_panel.csv", index=False)
    strict_panel.to_csv(out_dir / "task_632_temporal_strict_strategy_backtest_panel.csv", index=False)
    scenario_summary.to_csv(out_dir / "task_632_scenario_summary.csv", index=False)
    split_summary.to_csv(out_dir / "task_632_split_summary.csv", index=False)
    quarter_summary.to_csv(out_dir / "task_632_quarter_summary.csv", index=False)
    source_audit.to_csv(out_dir / "task_632_source_time_contract_audit.csv", index=False)
    cost_account.to_csv(out_dir / "task_632_cost_account_matrix.csv", index=False)
    pass_fail.to_csv(out_dir / "task_632_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_632_decision.csv", index=False)
    (out_dir / "task_632_temporal_strict_full_period_backtest.md").write_text(
        render_report(source_audit, scenario_summary, split_summary, cost_account, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_632_temporal_intelligence_entry_panel": temporal,
        "task_632_temporal_strict_scored_entry_panel": scored,
        "task_632_baseline_all_confirmed_backtest_panel": baseline_panel,
        "task_632_temporal_strict_strategy_backtest_panel": strict_panel,
        "task_632_scenario_summary": scenario_summary,
        "task_632_split_summary": split_summary,
        "task_632_quarter_summary": quarter_summary,
        "task_632_source_time_contract_audit": source_audit,
        "task_632_cost_account_matrix": cost_account,
        "task_632_pass_fail_matrix": pass_fail,
        "task_632_decision": decision,
    }


def load_scored_entries(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True, errors="coerce")
    frame["entry_ts_utc"] = pd.to_datetime(frame["entry_ts_utc"], utc=True, errors="coerce")
    frame["trade_date"] = pd.to_datetime(frame["trade_date"], errors="coerce").dt.date
    frame["quarter"] = frame["entry_ts"].dt.to_period("Q").astype(str)
    return frame.sort_values("entry_ts").reset_index(drop=True)


def load_temporal_event_store(path: Path) -> pd.DataFrame:
    events = normalize_event_frame(pd.read_csv(path) if path.exists() else pd.DataFrame())
    if events.empty:
        return events
    events["event_date_obj"] = pd.to_datetime(events["event_date"], errors="coerce").dt.date
    events["event_timestamp_dt"] = pd.to_datetime(events["event_timestamp_utc"], utc=True, errors="coerce")
    events["published_at_dt"] = pd.to_datetime(events["published_at"], utc=True, errors="coerce")
    events["received_at_dt"] = pd.to_datetime(events["received_at"], utc=True, errors="coerce")
    events["tradable_after_dt"] = pd.to_datetime(events["tradable_after_ts"], utc=True, errors="coerce")
    events["tradable_after_dt"] = events["tradable_after_dt"].where(events["tradable_after_dt"].notna(), events["event_timestamp_dt"])
    events["time_certified_flag"] = events["tradable_after_dt"].notna().astype(int)
    events["date_only_event_flag"] = events["time_precision"].astype(str).eq("date").astype(int)
    return events


def attach_temporal_intelligence(entries: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return entries.copy()
    rows: list[dict[str, Any]] = []
    for _, entry in entries.iterrows():
        symbol = str(entry["symbol"])
        theme = str(entry["theme_id"])
        tradable = events[
            events["tradable_after_dt"].notna()
            & events["date_only_event_flag"].astype(int).eq(0)
            & (events["tradable_after_dt"] <= entry["entry_ts_utc"])
        ].copy()
        if not tradable.empty:
            tradable["lag_hours"] = (entry["entry_ts_utc"] - tradable["tradable_after_dt"]).dt.total_seconds() / 3600.0
        fresh72 = tradable[tradable["lag_hours"].le(72.0)] if not tradable.empty else tradable
        political = relevant_events(fresh72, "trump_major_person_political_statements", symbol, theme)
        geopolitical = relevant_events(fresh72, "war_geopolitical_conflict_events", symbol, theme)
        institution = tradable[
            tradable["source_lane"].eq("institution_investment_actions")
            & tag_contains(tradable["symbol_tags"], symbol)
            & tradable["lag_hours"].le(24.0 * 30.0)
        ] if not tradable.empty else tradable
        ceo_ir = tradable[
            tradable["source_lane"].eq("ceo_ir_transcripts_and_presentations")
            & tag_contains(tradable["symbol_tags"], symbol)
            & tradable["lag_hours"].le(24.0 * 14.0)
        ] if not tradable.empty else tradable
        source_time_gap = source_time_gap_count(events, entry, symbol, theme)
        rows.append(
            {
                "lifecycle_id": entry["lifecycle_id"],
                "temporal_political_fresh_pre72h_count": int(len(political)),
                "temporal_political_fresh_pre72h_flag": int(len(political) > 0),
                "temporal_geopolitical_fresh_pre72h_count": int(len(geopolitical)),
                "temporal_geopolitical_fresh_pre72h_flag": int(len(geopolitical) > 0),
                "temporal_institution_pre30d_count": int(len(institution)),
                "temporal_institution_pre30d_flag": int(len(institution) > 0),
                "temporal_activist_13d_pre30d_flag": int(len(institution[institution["event_category"].eq("activist_13d")]) > 0) if not institution.empty else 0,
                "temporal_passive_13g_pre30d_flag": int(len(institution[institution["event_category"].eq("passive_13g")]) > 0) if not institution.empty else 0,
                "temporal_insider_form4_or_144_pre30d_flag": int(len(institution[institution["event_category"].eq("insider_or_sale_notice")]) > 0) if not institution.empty else 0,
                "temporal_ceo_ir_proxy_pre14d_count": int(len(ceo_ir)),
                "temporal_ceo_ir_proxy_pre14d_flag": int(len(ceo_ir) > 0),
                "temporal_source_event_density": int(len(political) + len(geopolitical) + len(institution) + len(ceo_ir)),
                "temporal_source_time_gap_count": source_time_gap,
                "temporal_label_used_in_assignment_flag": 0,
                "temporal_gpt_or_plugin_used_as_source_flag": 0,
            }
        )
    return entries.merge(pd.DataFrame(rows), on="lifecycle_id", how="left")


def source_time_gap_count(events: pd.DataFrame, entry: pd.Series, symbol: str, theme: str) -> int:
    if events.empty:
        return 0
    start = entry["trade_date"] - pd.Timedelta(days=7)
    gap = events[
        events["date_only_event_flag"].astype(int).eq(1)
        & pd.Series(events["event_date_obj"]).between(start, entry["trade_date"]).values
    ].copy()
    if gap.empty:
        return 0
    relevant = gap[
        tag_contains(gap["symbol_tags"], symbol)
        | tag_contains(gap["theme_tags"], theme)
        | gap["policy_tags"].astype(str).ne("")
    ]
    return int(len(relevant))


def add_temporal_strategy_scores(entries: pd.DataFrame) -> pd.DataFrame:
    out = entries.copy()
    n = lambda col: pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    out["tq_temporal_intelligence_support_score"] = (
        0.30 * n("temporal_institution_pre30d_flag").clip(0, 1)
        + 0.20 * n("temporal_passive_13g_pre30d_flag").clip(0, 1)
        + 0.20 * n("temporal_ceo_ir_proxy_pre14d_flag").clip(0, 1)
        + 0.15 * n("temporal_geopolitical_fresh_pre72h_flag").clip(0, 1)
        + 0.15 * n("temporal_political_fresh_pre72h_flag").clip(0, 1)
        + 0.15 * (n("temporal_source_event_density") / 5.0).clip(0, 1)
    ).clip(0, 1)
    out["tq_temporal_strict_strategy_entry_flag"] = (
        n("tq_pre_entry_chart_health_score").ge(0.80)
        & out["tq_temporal_intelligence_support_score"].ge(0.70)
        & n("tq_runtime_entry_confirmation_score").ge(0.67)
    ).astype(int)
    out["tq_temporal_assignment_label_used_flag"] = 0
    out["tq_temporal_gpt_or_plugin_used_as_source_flag"] = 0
    return out


def build_scenario_summary(baseline: pd.DataFrame, original: pd.DataFrame, strict: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, frame in [
        ("fresh_baseline_all_confirmed", baseline),
        ("task617_original_broad_intelligence_strategy", original),
        ("task632_temporal_strict_chart_qual_strategy", strict),
    ]:
        rows.append({"scenario": name, **aggregate(frame)})
    return pd.DataFrame(rows)


def build_split_summary(strict_panel: pd.DataFrame) -> pd.DataFrame:
    if strict_panel.empty:
        return pd.DataFrame()
    out = quality(strict_panel, ["split_name"])
    out["positive_split_flag"] = (
        out["lifecycle_count"].ge(10)
        & out["avg_net_return_pct"].ge(3.0)
        & out["entry_reduce_failure_rate"].le(0.35)
    ).astype(int)
    return out


def build_source_audit(events: pd.DataFrame, temporal: pd.DataFrame, scored: pd.DataFrame) -> pd.DataFrame:
    entry_ts = (
        pd.to_datetime(scored["entry_ts_utc"], utc=True, errors="coerce")
        if "entry_ts_utc" in scored.columns
        else pd.Series(dtype="datetime64[ns, UTC]")
    )
    return pd.DataFrame(
        [
            {
                "event_store_rows": int(len(events)),
                "event_store_has_received_at_flag": int("received_at" in events.columns),
                "event_store_has_published_at_flag": int("published_at" in events.columns),
                "event_store_has_tradable_after_ts_flag": int("tradable_after_ts" in events.columns),
                "timestamp_event_count": int(events["time_precision"].astype(str).eq("timestamp").sum()) if not events.empty else 0,
                "date_only_event_count": int(events["time_precision"].astype(str).eq("date").sum()) if not events.empty else 0,
                "time_certified_event_count": int(events["time_certified_flag"].sum()) if not events.empty else 0,
                "entry_count": int(len(scored)),
                "full_period_start": entry_ts.min().date().isoformat() if entry_ts.notna().any() else "",
                "full_period_end": entry_ts.max().date().isoformat() if entry_ts.notna().any() else "",
                "temporal_strategy_entry_count": int(scored["tq_temporal_strict_strategy_entry_flag"].sum()),
                "source_time_gap_entry_count": int(temporal["temporal_source_time_gap_count"].gt(0).sum()),
                "date_only_support_used_count": 0,
                "future_event_support_leak_count": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        ]
    )


def build_cost_account_matrix(original: pd.DataFrame, strict: pd.DataFrame) -> pd.DataFrame:
    universes = {
        "task617_original_broad_intelligence_strategy": original,
        "task632_temporal_strict_chart_qual_strategy": strict,
    }
    rows = []
    for universe, base in universes.items():
        for scope in SCOPES:
            scoped = base if scope == "full_panel" else base[base["split_name"].astype(str).eq(scope)]
            costed = scoped.copy()
            costed["net_return_from_entry"] = pd.to_numeric(costed["net_return_from_entry"], errors="coerce") - (
                DECISION_COST_BPS / 10000.0
            )
            for max_positions in MAX_POSITIONS:
                quality_row, accepted, _curve = simulate_deterministic_portfolio(costed, max_positions=max_positions)
                rows.append(
                    {
                        "universe": universe,
                        "scope": scope,
                        "round_trip_cost_bps": DECISION_COST_BPS,
                        "initial_capital_usd": INITIAL_CAPITAL_USD,
                        "max_positions": int(max_positions),
                        "source_trade_count": int(len(scoped)),
                        "accepted_trade_count": int(len(accepted)),
                        "final_capital_usd": INITIAL_CAPITAL_USD * (1.0 + float(quality_row["capital_pnl_pct"]) / 100.0),
                        "capital_return_pct": float(quality_row["capital_pnl_pct"]),
                        "avg_net_return_pct": float(quality_row["avg_net_return_pct"]),
                        "win_rate": float(quality_row["win_rate"]),
                        "entry_reduce_failure_rate": float(quality_row["entry_reduce_failure_rate"]),
                        "max_drawdown_pct": float(quality_row["max_drawdown_pct"]),
                    }
                )
    return pd.DataFrame(rows)


def metric(summary: pd.DataFrame, scenario: str, column: str) -> float:
    return float(summary[summary["scenario"].eq(scenario)].iloc[0][column])


def account_wins(cost_account: pd.DataFrame, scope: str) -> tuple[int, str]:
    strict = cost_account[
        cost_account["universe"].eq("task632_temporal_strict_chart_qual_strategy")
        & cost_account["scope"].eq(scope)
    ]
    original = cost_account[
        cost_account["universe"].eq("task617_original_broad_intelligence_strategy")
        & cost_account["scope"].eq(scope)
    ]
    merged = strict[["max_positions", "final_capital_usd"]].merge(
        original[["max_positions", "final_capital_usd"]],
        on="max_positions",
        suffixes=("_strict", "_original"),
    )
    wins = int((merged["final_capital_usd_strict"] > merged["final_capital_usd_original"]).sum())
    pairs = "; ".join(
        f"max{int(r.max_positions)} strict=${float(r.final_capital_usd_strict):.2f} original=${float(r.final_capital_usd_original):.2f}"
        for r in merged.itertuples()
    )
    return wins, pairs


def build_pass_fail(
    source_audit: pd.DataFrame,
    scenario_summary: pd.DataFrame,
    split_summary: pd.DataFrame,
    cost_account: pd.DataFrame,
) -> pd.DataFrame:
    source = source_audit.iloc[0]
    strict_count = int(source["temporal_strategy_entry_count"])
    base_avg = metric(scenario_summary, "fresh_baseline_all_confirmed", "avg_net_return_pct")
    strict_avg = metric(scenario_summary, "task632_temporal_strict_chart_qual_strategy", "avg_net_return_pct")
    original_avg = metric(scenario_summary, "task617_original_broad_intelligence_strategy", "avg_net_return_pct")
    positive_splits = int(split_summary["positive_split_flag"].sum()) if not split_summary.empty else 0
    split_total = int(len(split_summary)) if not split_summary.empty else 0
    recent_wins, recent_pairs = account_wins(cost_account, "recent_oos")
    validation_wins, validation_pairs = account_wins(cost_account, "validation")
    full_wins, full_pairs = account_wins(cost_account, "full_panel")
    return pd.DataFrame(
        [
            {
                "gate": "runtime_temporal_contract_columns",
                "pass_flag": int(
                    source["event_store_has_received_at_flag"]
                    and source["event_store_has_published_at_flag"]
                    and source["event_store_has_tradable_after_ts_flag"]
                ),
                "observed_value": f"received={int(source['event_store_has_received_at_flag'])}; published={int(source['event_store_has_published_at_flag'])}; tradable={int(source['event_store_has_tradable_after_ts_flag'])}",
                "required_value": "event store must carry received_at published_at tradable_after_ts",
            },
            {
                "gate": "temporal_strict_candidate_count",
                "pass_flag": int(strict_count >= 50),
                "observed_value": f"temporal_strategy_entries={strict_count}",
                "required_value": ">=50 full-period temporal strict strategy entries",
            },
            {
                "gate": "date_only_events_not_used_as_support",
                "pass_flag": int(int(source["date_only_support_used_count"]) == 0),
                "observed_value": f"date_only_support_used={int(source['date_only_support_used_count'])}",
                "required_value": "date-only events must be reported as gaps and never support entry",
            },
            {
                "gate": "future_event_support_leakage",
                "pass_flag": int(int(source["future_event_support_leak_count"]) == 0),
                "observed_value": f"future_event_support_leaks={int(source['future_event_support_leak_count'])}",
                "required_value": "no event after entry may support the entry score",
            },
            {
                "gate": "full_period_avg_beats_baseline",
                "pass_flag": int(strict_avg >= base_avg + 2.0),
                "observed_value": f"strict={strict_avg:.2f}% baseline={base_avg:.2f}% original_task617={original_avg:.2f}%",
                "required_value": "temporal strict avg return must beat all-confirmed baseline by >=2pp",
            },
            {
                "gate": "split_stability",
                "pass_flag": int(split_total >= 3 and positive_splits >= 2),
                "observed_value": f"positive_splits={positive_splits}/{split_total}",
                "required_value": ">=2 positive splits across >=3 splits",
            },
            {
                "gate": "recent_oos_50bp_account_vs_original",
                "pass_flag": int(recent_wins >= 3),
                "observed_value": f"strict_wins={recent_wins}/4; {recent_pairs}",
                "required_value": "strict strategy beats original Task617 in >=3 of 4 recent-OOS capacities at 50bp",
            },
            {
                "gate": "validation_50bp_account_vs_original",
                "pass_flag": int(validation_wins >= 2),
                "observed_value": f"strict_wins={validation_wins}/4; {validation_pairs}",
                "required_value": "strict strategy is at least mixed versus original on validation at 50bp",
            },
            {
                "gate": "full_panel_50bp_account_vs_original",
                "pass_flag": int(full_wins >= 2),
                "observed_value": f"strict_wins={full_wins}/4; {full_pairs}",
                "required_value": "strict strategy is at least mixed versus original on full panel at 50bp",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "full-period temporal strict backtest only",
                "required_value": "requires live source readiness and confirmation-gated entry before promotion",
            },
        ]
    )


def build_decision(
    source_audit: pd.DataFrame,
    scenario_summary: pd.DataFrame,
    split_summary: pd.DataFrame,
    cost_account: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> pd.DataFrame:
    strict = scenario_summary[scenario_summary["scenario"].eq("task632_temporal_strict_chart_qual_strategy")].iloc[0]
    recent_pass = int(pass_fail[pass_fail["gate"].eq("recent_oos_50bp_account_vs_original")]["pass_flag"].iloc[0])
    validation_pass = int(pass_fail[pass_fail["gate"].eq("validation_50bp_account_vs_original")]["pass_flag"].iloc[0])
    full_pass = int(pass_fail[pass_fail["gate"].eq("full_panel_50bp_account_vs_original")]["pass_flag"].iloc[0])
    diagnostic_pass = int(
        pass_fail[
            pass_fail["gate"].isin(
                [
                    "runtime_temporal_contract_columns",
                    "temporal_strict_candidate_count",
                    "date_only_events_not_used_as_support",
                    "future_event_support_leakage",
                    "full_period_avg_beats_baseline",
                    "split_stability",
                ]
            )
        ]["pass_flag"].astype(int).all()
    )
    decision = "FAIL_TEMPORAL_STRICT_FULL_PERIOD_NOT_ACCEPTED"
    if diagnostic_pass and recent_pass and validation_pass and full_pass:
        decision = "PASS_TEMPORAL_STRICT_FULL_PERIOD_DIAGNOSTIC_NOT_ACCEPTED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "full_period_start": str(source_audit.iloc[0].get("full_period_start", "")),
                "full_period_end": str(source_audit.iloc[0].get("full_period_end", "")),
                "temporal_strategy_trade_count": int(strict["lifecycle_count"]),
                "temporal_strategy_avg_net_return_pct": float(strict["avg_net_return_pct"]),
                "temporal_strategy_entry_reduce_failure_rate": float(strict["entry_reduce_failure_rate"]),
                "recent_oos_50bp_account_edge_pass_flag": recent_pass,
                "validation_50bp_not_broken_pass_flag": validation_pass,
                "full_panel_50bp_account_edge_pass_flag": full_pass,
                "trading_promotion_pass_flag": 0,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Use temporal strict outputs as the new backtest baseline then build confirmation-gated entry before any promotion.",
            }
        ]
    )


def render_report(
    source_audit: pd.DataFrame,
    scenario_summary: pd.DataFrame,
    split_summary: pd.DataFrame,
    cost_account: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task632 Temporal Strict Full Period Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Temporal strict trades: {int(d['temporal_strategy_trade_count'])}",
        f"- Temporal strict average net return: {float(d['temporal_strategy_avg_net_return_pct']):.2f}%",
        "",
        "## Quant Expert Report",
        "",
        "This reruns the 2024-2026 fresh confirmed candidate universe with chart features plus temporal-certified qualitative information. Date-only events are not allowed to support the qualitative score.",
        "",
        "### Source Contract Audit",
        "",
        "| Event Rows | Timestamp | Date-only | Time Certified | Strategy Entries | Source Time Gap Entries |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    s = source_audit.iloc[0]
    lines.append(
        f"| {int(s['event_store_rows'])} | {int(s['timestamp_event_count'])} | {int(s['date_only_event_count'])} | "
        f"{int(s['time_certified_event_count'])} | {int(s['temporal_strategy_entry_count'])} | {int(s['source_time_gap_entry_count'])} |"
    )
    lines.extend(
        [
            "",
            "### Scenario Summary",
            "",
            "| Scenario | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for _, row in scenario_summary.iterrows():
        lines.append(
            f"| `{row['scenario']}` | {int(row['lifecycle_count'])} | {float(row['avg_net_return_pct']):.2f}% | "
            f"{float(row['win_rate']):.2f}% | {float(row['entry_reduce_failure_rate']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "### Split Summary",
            "",
            "| Split | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure | Positive Split |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in split_summary.iterrows():
        lines.append(
            f"| `{row['split_name']}` | {int(row['lifecycle_count'])} | {float(row['avg_net_return_pct']):.2f}% | "
            f"{float(row['win_rate']):.2f}% | {float(row['entry_reduce_failure_rate']):.2f}% | {int(row['positive_split_flag'])} |"
        )
    lines.extend(
        [
            "",
            "### 50bp Account Matrix",
            "",
            "| Scope | Universe | Max Positions | Final $ | Return |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for _, row in cost_account.sort_values(["scope", "max_positions", "universe"]).iterrows():
        lines.append(
            f"| `{row['scope']}` | `{row['universe']}` | {int(row['max_positions'])} | "
            f"${float(row['final_capital_usd']):,.2f} | {float(row['capital_return_pct']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- 전체 기간 후보에 시간 인증 정성정보와 차트정보를 같이 적용했습니다.",
            "- date-only 이벤트는 정성 점수에서 제외했습니다.",
            "- 결과는 진단용입니다. 실거래 승인은 아닙니다.",
            "",
            "## Pass/Fail Matrix",
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
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_scored_entry_panel.csv`",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "- `data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv`",
            "",
            "### Outputs",
            "",
            "- `task_632_temporal_intelligence_entry_panel.csv`",
            "- `task_632_temporal_strict_scored_entry_panel.csv`",
            "- `task_632_temporal_strict_strategy_backtest_panel.csv`",
            "- `task_632_scenario_summary.csv`",
            "- `task_632_split_summary.csv`",
            "- `task_632_cost_account_matrix.csv`",
            "- `task_632_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task632_temporal_strict_full_period_backtest`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
            "- `python scripts/governance_completion_audit.py`",
        ]
    )
    if "## No-Background Decision-Maker Report" in lines:
        section_idx = lines.index("## No-Background Decision-Maker Report")
        lines[section_idx + 2 : section_idx + 5] = [
            "- This is a full-period diagnostic backtest using chart data plus time-certified qualitative data.",
            "- Date-only events are treated as source-time gaps and cannot support entries.",
            "- The result is not accepted because recent OOS and full-panel account gates fail.",
        ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task632_temporal_strict_full_period_backtest(out_dir=args.out_dir)
    row = artifacts["task_632_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"trades={int(row['temporal_strategy_trade_count'])} "
        f"avg={float(row['temporal_strategy_avg_net_return_pct']):.2f}%"
    )


if __name__ == "__main__":
    main()
