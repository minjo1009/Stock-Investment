from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest import build_task678_active_cap3_winner_archetype as t678
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio
from src.backtest.build_task697_tiny_candidate_pnl_test import INITIAL_CAPITAL_USD, QQQ_DAILY, ROUND_TRIP_COST_BPS, load_qqq_daily


TASK636_DIR = Path("docs/reports/task_636_full_period_content_prediction_backtest")
BASELINE_PANEL = Path(
    "docs/reports/task_633_qqq_benchmark_full_period_refresh/"
    "task632_temporal_strict_refresh/task_632_baseline_all_confirmed_backtest_panel.csv"
)
TASK684_PANEL = Path("docs/reports/task_684_interaction_context_prediction_stack/task684_interaction_stack_panel.csv")
TASK704_PRICE_CONTEXT_PANEL = Path("docs/reports/task_704_price_context_backfill/task704_price_context_panel.csv")
TASK703_DIR = Path("docs/reports/task_703_event_linked_source_axis_backtest")

SIGNAL_FAMILIES = [
    "contract_signal_v2",
    "customer_signal_v2",
    "order_backlog_signal_v2",
    "revenue_signal_v2",
    "guidance_signal_v2",
    "margin_signal_v2",
    "supply_demand_signal_v2",
]
TASK636_SIGNAL_FAMILIES = {
    "customer": ["content_named_customer_or_counterparty"],
    "revenue_backlog": ["content_revenue_or_backlog_signal"],
    "guidance_margin": ["content_guidance_or_margin_signal"],
    "supply_demand": ["content_supply_demand_signal"],
    "regulatory_policy": ["content_regulatory_or_policy_transmission"],
}
FINANCING_PATTERN = re.compile(
    r"private offering|convertible senior notes|senior notes due|indenture and notes|"
    r"capped call|note purchase agreement|convertible notes|aggregate principal amount",
    flags=re.IGNORECASE,
)
REAFFIRM_PATTERN = re.compile(
    r"\breaffirm(?:s|ed|ing)?\b|unauthorized interview|previously issued guidance|reaffirmed guidance",
    flags=re.IGNORECASE,
)
RAISE_PATTERN = re.compile(
    r"(raise|raises|raised|raising|increase|increases|increased|higher|above|upgrade|upward).{0,100}"
    r"(guidance|outlook|forecast)|(guidance|outlook|forecast).{0,100}"
    r"(raise|raises|raised|increase|higher|above|upgrade|upward)",
    flags=re.IGNORECASE,
)
SOFT_PATTERN = re.compile(
    r"(lower|lowers|lowered|reduce|reduced|cut|cuts|below).{0,100}(guidance|outlook|forecast)|"
    r"(guidance|outlook|forecast).{0,100}(lower|lowers|lowered|reduce|reduced|cut|below)",
    flags=re.IGNORECASE,
)
CONTEXT_COLUMNS = [
    "lifecycle_id",
    "symbol",
    "price_acceptance_score",
    "price_chart_acceptance_state",
    "volume_ratio_prev",
]
BASELINE_OUTCOME_COLUMNS = [
    "lifecycle_id",
    "symbol",
    "theme_id",
    "entry_ts",
    "entry_price",
    "split_name",
    "simulated_exit_ts",
    "simulated_exit_price",
    "exit_reason",
    "net_return_from_entry",
    "win_flag",
    "add_scale_success_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
    "holding_days",
    "same_day_exit_flag",
]


def build_task703_program(
    *,
    task636_dir: Path = TASK636_DIR,
    baseline_panel_path: Path = BASELINE_PANEL,
    task684_panel_path: Path = TASK684_PANEL,
    task704_price_context_path: Path = TASK704_PRICE_CONTEXT_PANEL,
    qqq_daily_path: Path = QQQ_DAILY,
    out_dir: Path = TASK703_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    links = pd.read_csv(task636_dir / "task_636_entry_event_links.csv")
    predictions = pd.read_csv(task636_dir / "task_636_event_content_predictions.csv")
    baseline = pd.read_csv(baseline_panel_path, usecols=BASELINE_OUTCOME_COLUMNS)
    context = load_price_context(task684_panel_path, task704_price_context_path)
    qqq = load_qqq_daily(qqq_daily_path)

    gpt_status = build_gpt_review_status(out_dir)
    axis_freeze = build_axis_freeze(baseline, links, predictions, context)
    axis_eval = build_axis_eval(axis_freeze, baseline, qqq)
    action_summary = build_action_summary(axis_eval)
    split_summary = build_split_summary(axis_eval)
    portfolio_comparison = build_portfolio_comparison(axis_eval, qqq)
    audit = build_audit(axis_freeze, axis_eval, action_summary, portfolio_comparison, gpt_status)
    pass_fail = audit.copy()
    decision = build_decision(axis_freeze, action_summary, split_summary, portfolio_comparison, audit, gpt_status)
    write_outputs(out_dir, axis_freeze, axis_eval, action_summary, split_summary, portfolio_comparison, gpt_status, audit, pass_fail, decision)
    return {
        "task703_axis_freeze_panel": axis_freeze,
        "task703_axis_eval_panel": axis_eval,
        "task703_action_summary": action_summary,
        "task703_split_summary": split_summary,
        "task703_portfolio_comparison": portfolio_comparison,
        "task703_gpt_review_status": gpt_status,
        "task703_integrity_audit": audit,
        "task_703_pass_fail_matrix": pass_fail,
        "task_703_decision": decision,
    }


def load_price_context(task684_panel_path: Path, task704_price_context_path: Path) -> pd.DataFrame:
    if task704_price_context_path.exists():
        cols = [
            "lifecycle_id",
            "symbol",
            "price_context_available_flag",
            "price_context_source",
            "price_acceptance_score",
            "price_chart_acceptance_state",
            "volume_ratio_prev",
        ]
        return pd.read_csv(task704_price_context_path, usecols=cols)
    context = pd.read_csv(task684_panel_path, usecols=CONTEXT_COLUMNS)
    context["price_context_available_flag"] = (
        pd.to_numeric(context["price_acceptance_score"], errors="coerce").fillna(0).gt(0)
        | context["price_chart_acceptance_state"].fillna("").astype(str).ne("")
        | pd.to_numeric(context["volume_ratio_prev"], errors="coerce").fillna(0).gt(0)
    ).astype(int)
    context["price_context_source"] = "task684_legacy_context"
    return context


def build_gpt_review_status(out_dir: Path) -> pd.DataFrame:
    raw_path = out_dir / "gpt_review_raw.md"
    return pd.DataFrame(
        [
            {
                "gpt_review_required_flag": 1,
                "gpt_review_complete_flag": int(raw_path.exists() and raw_path.stat().st_size > 0),
                "gpt_review_path": str(raw_path),
                "gpt_used_as_source_flag": 0,
                "gpt_role": "external_design_reviewer_only",
                "review_scope": "full event-linked source-axis parser before final full-period backtest",
            }
        ]
    )


def build_axis_freeze(
    baseline: pd.DataFrame,
    links: pd.DataFrame,
    predictions: pd.DataFrame,
    context: pd.DataFrame,
) -> pd.DataFrame:
    identity = baseline[["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]].drop_duplicates()
    event_axes = build_event_axes(links, predictions)
    out = identity.merge(event_axes, on=["lifecycle_id", "symbol"], how="left").merge(context, on=["lifecycle_id", "symbol"], how="left")
    out["source_event_available_flag"] = pd.to_numeric(out["source_event_available_flag"], errors="coerce").fillna(0).astype(int)
    for col in [
        "linked_event_count",
        "direct_event_count",
        "manual_event_count",
        "noise_event_count",
        "noise_ratio",
        "direct_signal_family_count",
        "manual_signal_family_count",
        "financing_overhang_flag",
        "high_noise_thin_signal_flag",
        "price_acceptance_score",
        "volume_ratio_prev",
        "price_context_available_flag",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    out["price_context_source"] = out["price_context_source"].fillna("missing_price_context")
    out["guidance_quality_axis"] = out["guidance_quality_axis"].fillna("no_source_packet")
    out["information_novelty_axis"] = out["information_novelty_axis"].fillna("no_source_packet")
    out["price_absorption_confirmation_flag"] = (
        out["price_acceptance_score"].ge(6)
        & out["volume_ratio_prev"].ge(1.0)
        & out["price_chart_acceptance_state"].astype(str).str.contains("price_confirmed", na=False)
    ).astype(int)
    out["full_event_axis_action"] = out.apply(classify_action, axis=1)
    out["full_event_axis_eligible_flag"] = out["full_event_axis_action"].eq("ELIGIBLE_RULE_CANDIDATE").astype(int)
    out["outcome_used_for_selection_flag"] = 0
    out["future_price_used_for_selection_flag"] = 0
    out["allocation_approved_flag"] = 0
    out["paper_or_live_trade_approved_flag"] = 0
    columns = [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "entry_ts",
        "split_name",
        "source_event_available_flag",
        "linked_event_count",
        "direct_event_count",
        "manual_event_count",
        "noise_event_count",
        "noise_ratio",
        "direct_signal_family_count",
        "manual_signal_family_count",
        "financing_overhang_flag",
        "guidance_quality_axis",
        "information_novelty_axis",
        "high_noise_thin_signal_flag",
        "price_acceptance_score",
        "price_chart_acceptance_state",
        "volume_ratio_prev",
        "price_context_available_flag",
        "price_context_source",
        "price_absorption_confirmation_flag",
        "full_event_axis_action",
        "full_event_axis_eligible_flag",
        "outcome_used_for_selection_flag",
        "future_price_used_for_selection_flag",
        "allocation_approved_flag",
        "paper_or_live_trade_approved_flag",
    ]
    return out[columns].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def build_event_axes(links: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    event_packet = links.merge(predictions, on="event_id", how="left", suffixes=("_link", ""))
    rows = []
    for (lifecycle_id, symbol), group in event_packet.groupby(["lifecycle_id", "symbol"], dropna=False):
        rows.append(classify_lifecycle_events(lifecycle_id, symbol, group))
    return pd.DataFrame(rows)


def classify_lifecycle_events(lifecycle_id: str, symbol: str, group: pd.DataFrame) -> dict[str, object]:
    direct = group[group.apply(is_direct_event, axis=1)]
    manual = group[group.apply(is_manual_event, axis=1)]
    base_text_rows = direct if len(direct) else manual
    focused_text = " ".join(
        base_text_rows[["event_title", "content_interpretation_evidence_span"]]
        .fillna("")
        .astype(str)
        .to_numpy()
        .ravel()
        .tolist()
    )
    full_text = focused_text
    for path_value in group["raw_text_path"].dropna().unique():
        path = Path(str(path_value))
        if not path.is_absolute():
            path = ROOT / path
        try:
            full_text += " " + path.read_text(encoding="utf-8", errors="ignore")[:50000]
        except OSError:
            pass
    direct_family_count = count_signal_families(direct) if len(direct) else 0
    manual_family_count = count_signal_families(manual) if len(manual) else 0
    guidance_count = int(signal_sum(direct, "guidance_signal_v2") + signal_sum(manual, "guidance_signal_v2"))
    noise_count = int(group.apply(is_noise_event, axis=1).sum())
    linked_event_count = int(len(group))
    financing = bool(FINANCING_PATTERN.search(full_text))
    reaffirm = bool(REAFFIRM_PATTERN.search(full_text))
    soft = bool(SOFT_PATTERN.search(focused_text))
    raised = bool(RAISE_PATTERN.search(focused_text)) and not reaffirm and not soft
    return {
        "lifecycle_id": lifecycle_id,
        "symbol": symbol,
        "source_event_available_flag": 1,
        "linked_event_count": linked_event_count,
        "direct_event_count": int(len(direct)),
        "manual_event_count": int(len(manual)),
        "noise_event_count": noise_count,
        "noise_ratio": noise_count / linked_event_count if linked_event_count else 0.0,
        "direct_signal_family_count": int(direct_family_count),
        "manual_signal_family_count": int(manual_family_count),
        "financing_overhang_flag": int(financing),
        "guidance_quality_axis": classify_guidance_quality(financing, reaffirm, soft, raised, guidance_count),
        "information_novelty_axis": classify_information_novelty(
            financing, reaffirm, len(direct), direct_family_count, len(manual), manual_family_count
        ),
        "high_noise_thin_signal_flag": int((noise_count / linked_event_count if linked_event_count else 0.0) >= 0.75 and len(direct) <= 1),
    }


def is_direct_event(row: pd.Series) -> bool:
    causal = str(row.get("content_stock_specific_causal_link", "")).lower()
    causal_direct = causal in {
        "company_direct_economic_update",
        "theme_policy_possible_tailwind",
        "financing_or_dilution_risk",
    }
    if not causal_direct:
        return False
    if int_safe(row.get("source_text_certified_flag", 0)) <= 0:
        return False
    if is_noise_event(row):
        return False
    return (
        int_safe(row.get("content_named_customer_or_counterparty", 0))
        + int_safe(row.get("content_revenue_or_backlog_signal", 0))
        + int_safe(row.get("content_guidance_or_margin_signal", 0))
        + int_safe(row.get("content_supply_demand_signal", 0))
        + int_safe(row.get("content_regulatory_or_policy_transmission", 0))
        > 0
    )


def is_manual_event(row: pd.Series) -> bool:
    if int_safe(row.get("source_text_certified_flag", 0)) <= 0 or is_noise_event(row):
        return False
    return (
        int_safe(row.get("content_revenue_or_backlog_signal", 0))
        + int_safe(row.get("content_guidance_or_margin_signal", 0))
        + int_safe(row.get("content_supply_demand_signal", 0))
        + int_safe(row.get("content_regulatory_or_policy_transmission", 0))
        > 0
    )


def is_noise_event(row: pd.Series) -> bool:
    category = str(row.get("event_category", "")).lower()
    title = str(row.get("event_title", "")).lower()
    if category in {"insider_or_sale_notice", "passive_13g", "activist_13d"}:
        return True
    return any(term in title for term in ["form 4", " 144", "schedule 13g", "13g/a", "13d/a"])


def count_signal_families(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    hits = 0
    available = [col for col in SIGNAL_FAMILIES if col in frame.columns]
    if available:
        hits += int((frame[available].sum() > 0).sum())
    for columns in TASK636_SIGNAL_FAMILIES.values():
        present = [col for col in columns if col in frame.columns]
        if present and pd.to_numeric(frame[present].sum(axis=1), errors="coerce").fillna(0).sum() > 0:
            hits += 1
    return int(hits)


def signal_sum(frame: pd.DataFrame, signal_col: str) -> int:
    if frame.empty:
        return 0
    if signal_col in frame.columns:
        return int(pd.to_numeric(frame[signal_col], errors="coerce").fillna(0).sum())
    # Task636 uses combined guidance/margin fields.
    if signal_col == "guidance_signal_v2" and "content_guidance_or_margin_signal" in frame.columns:
        return int(pd.to_numeric(frame["content_guidance_or_margin_signal"], errors="coerce").fillna(0).sum())
    return 0


def classify_guidance_quality(financing: bool, reaffirm: bool, soft: bool, raised: bool, guidance_count: int) -> str:
    if financing:
        return "financing_conflict"
    if reaffirm:
        return "reaffirm"
    if guidance_count and soft:
        return "soft_or_cut"
    if guidance_count and raised:
        return "raise_or_positive_change"
    if guidance_count:
        return "guidance_present_quality_unclear"
    return "no_guidance_signal"


def classify_information_novelty(
    financing: bool,
    reaffirm: bool,
    direct_count: int,
    direct_family_count: int,
    manual_count: int,
    manual_family_count: int,
) -> str:
    if financing:
        return "conflicted_by_financing"
    if reaffirm:
        return "not_new_reaffirmation"
    if direct_count > 0 and direct_family_count >= 3:
        return "new_multi_family_direct"
    if direct_count > 0:
        return "new_thin_direct"
    if manual_count > 0 and manual_family_count >= 2:
        return "manual_indirect_economic_terms"
    return "not_enough_source_novelty"


def classify_action(row: pd.Series) -> str:
    if int(row["source_event_available_flag"]) == 0:
        return "RESEARCH_ONLY_NO_SOURCE_PACKET"
    if int(row["financing_overhang_flag"]) == 1:
        return "CONFIRMATION_REQUIRED_FINANCING"
    if row["guidance_quality_axis"] in {"reaffirm", "soft_or_cut"}:
        return "CONFIRMATION_REQUIRED_GUIDANCE_WEAK"
    if row["information_novelty_axis"] in {"not_new_reaffirmation", "not_enough_source_novelty"}:
        return "RESEARCH_ONLY_LOW_NOVELTY"
    if int(row["high_noise_thin_signal_flag"]) == 1 and int(row["price_absorption_confirmation_flag"]) == 0:
        return "CONFIRMATION_REQUIRED_HIGH_NOISE"
    if int(row["price_absorption_confirmation_flag"]) == 0:
        return "CONFIRMATION_REQUIRED_PRICE"
    return "ELIGIBLE_RULE_CANDIDATE"


def build_axis_eval(axis_freeze: pd.DataFrame, baseline: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    joined = axis_freeze.merge(baseline, on=["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"], how="left", indicator=True)
    if not joined["_merge"].eq("both").all():
        raise ValueError("Task703 all frozen rows must join baseline outcomes exactly.")
    joined = joined.drop(columns=["_merge"])
    joined["net_return_from_entry_gross"] = pd.to_numeric(joined["net_return_from_entry"], errors="coerce")
    joined["net_return_from_entry"] = joined["net_return_from_entry_gross"] - ROUND_TRIP_COST_BPS / 10000.0
    joined["costed_return_pct"] = joined["net_return_from_entry"] * 100.0
    joined["qqq_costed_return_pct"] = joined.apply(lambda row: qqq_return_for_row(qqq, row), axis=1)
    joined["excess_vs_qqq_costed_pct"] = joined["costed_return_pct"] - joined["qqq_costed_return_pct"]
    joined["beats_qqq_same_window_flag"] = (joined["excess_vs_qqq_costed_pct"] > 0).astype(int)
    joined["outcome_used_for_evaluation_flag"] = 1
    return joined


def qqq_return_for_row(qqq: pd.DataFrame, row: pd.Series) -> float:
    entry_date = pd.to_datetime(row["entry_ts"], utc=True).date()
    exit_date = pd.to_datetime(row["simulated_exit_ts"], utc=True).date()
    entry = qqq[qqq["date"].ge(entry_date)].head(1)
    exit_ = qqq[qqq["date"].ge(exit_date)].head(1)
    if entry.empty or exit_.empty:
        return float("nan")
    gross = float(exit_.iloc[0]["close"]) / float(entry.iloc[0]["close"]) - 1.0
    return (gross - ROUND_TRIP_COST_BPS / 10000.0) * 100.0


def build_action_summary(axis_eval: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for action, group in axis_eval.groupby("full_event_axis_action", dropna=False):
        costed = group["costed_return_pct"].astype(float)
        rows.append(
            {
                "full_event_axis_action": action,
                "candidate_count": int(len(group)),
                "source_event_count": int(group["source_event_available_flag"].sum()),
                "symbols_sample": "|".join(group["symbol"].astype(str).head(40).tolist()),
                "avg_costed_return_pct": float(costed.mean()),
                "median_costed_return_pct": float(costed.median()),
                "win_rate": float((costed > 0).mean()),
                "avg_excess_vs_qqq_costed_pct": float(group["excess_vs_qqq_costed_pct"].astype(float).mean()),
                "outcome_used_for_selection_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("avg_costed_return_pct", ascending=False).reset_index(drop=True)


def build_split_summary(axis_eval: pd.DataFrame) -> pd.DataFrame:
    eligible = axis_eval[axis_eval["full_event_axis_eligible_flag"].eq(1)]
    rows = []
    for split_name, group in eligible.groupby("split_name", dropna=False):
        costed = group["costed_return_pct"].astype(float)
        rows.append(
            {
                "split_name": split_name,
                "eligible_count": int(len(group)),
                "avg_costed_return_pct": float(costed.mean()),
                "median_costed_return_pct": float(costed.median()),
                "win_rate": float((costed > 0).mean()),
                "avg_excess_vs_qqq_costed_pct": float(group["excess_vs_qqq_costed_pct"].astype(float).mean()),
            }
        )
    if not rows:
        return pd.DataFrame(
            [
                {
                    "split_name": "NO_ELIGIBLE",
                    "eligible_count": 0,
                    "avg_costed_return_pct": 0.0,
                    "median_costed_return_pct": 0.0,
                    "win_rate": 0.0,
                    "avg_excess_vs_qqq_costed_pct": 0.0,
                }
            ]
        )
    return pd.DataFrame(rows).sort_values("split_name").reset_index(drop=True)


def build_portfolio_comparison(axis_eval: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    full = axis_eval.copy()
    event_linked = axis_eval[axis_eval["source_event_available_flag"].eq(1)].copy()
    eligible = axis_eval[axis_eval["full_event_axis_eligible_flag"].eq(1)].copy()
    qqq_final = qqq_buyhold_final(axis_eval, qqq)
    rows = []
    for cohort_name, panel in [
        ("all_5265_baseline_costed", full),
        ("event_linked_2445_costed", event_linked),
        ("full_event_axis_eligible", eligible),
    ]:
        sim = panel.copy()
        for max_positions in [5, 10, 20]:
            quality, accepted, _curve = simulate_deterministic_portfolio(sim, max_positions=max_positions)
            final_capital = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
            rows.append(
                {
                    "portfolio_cohort": cohort_name,
                    "max_positions": int(max_positions),
                    "source_candidate_count": int(len(sim)),
                    "accepted_trade_count": int(len(accepted)),
                    "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
                    "initial_capital_usd": INITIAL_CAPITAL_USD,
                    "final_capital_usd": final_capital,
                    "capital_return_pct": float(quality["capital_pnl_pct"]),
                    "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                    "qqq_buyhold_final_capital_usd": qqq_final,
                    "beats_qqq_flag": int(final_capital > qqq_final),
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "real_capital_status": "FORBIDDEN",
                }
            )
    rows.append(
        {
            "portfolio_cohort": "QQQ_buy_and_hold_same_horizon",
            "max_positions": 1,
            "source_candidate_count": 1,
            "accepted_trade_count": 1,
            "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
            "initial_capital_usd": INITIAL_CAPITAL_USD,
            "final_capital_usd": qqq_final,
            "capital_return_pct": (qqq_final / INITIAL_CAPITAL_USD - 1.0) * 100.0,
            "max_drawdown_pct": 0.0,
            "qqq_buyhold_final_capital_usd": qqq_final,
            "beats_qqq_flag": 0,
            "strategy_acceptance_status": "BENCHMARK",
            "real_capital_status": "N/A",
        }
    )
    return pd.DataFrame(rows)


def qqq_buyhold_final(axis_eval: pd.DataFrame, qqq: pd.DataFrame) -> float:
    start = pd.to_datetime(axis_eval["entry_ts"], utc=True).min().date()
    end = pd.to_datetime(axis_eval["simulated_exit_ts"], utc=True).max().date()
    start_row = qqq[qqq["date"].ge(start)].head(1)
    end_row = qqq[qqq["date"].le(end)].tail(1)
    if start_row.empty or end_row.empty:
        return float("nan")
    gross = float(end_row.iloc[0]["close"]) / float(start_row.iloc[0]["close"])
    return INITIAL_CAPITAL_USD * (gross - ROUND_TRIP_COST_BPS / 10000.0)


def build_audit(
    axis_freeze: pd.DataFrame,
    axis_eval: pd.DataFrame,
    action_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    gpt_status: pd.DataFrame,
) -> pd.DataFrame:
    eligible_count = int(axis_freeze["full_event_axis_eligible_flag"].sum())
    return pd.DataFrame(
        [
            gate("freeze_scope_5265", len(axis_freeze) == 5265, f"rows={len(axis_freeze)}", "full baseline candidate scope"),
            gate(
                "event_linked_scope_2445",
                int(axis_freeze["source_event_available_flag"].sum()) == 2445,
                f"event_linked={int(axis_freeze['source_event_available_flag'].sum())}",
                "Task636 event-linked lifecycle coverage",
            ),
            gate("eligible_nonzero", eligible_count > 0, f"eligible={eligible_count}", "parser should produce eligible candidates"),
            gate(
                "price_context_full_coverage",
                int(axis_freeze["price_context_available_flag"].sum()) == len(axis_freeze),
                f"price_context={int(axis_freeze['price_context_available_flag'].sum())}/{len(axis_freeze)}",
                "Task704 as-of-entry price context should cover the full freeze scope",
            ),
            gate(
                "gpt_review_complete_before_report",
                int(gpt_status.iloc[0]["gpt_review_complete_flag"]) == 1,
                f"gpt_review_complete={int(gpt_status.iloc[0]['gpt_review_complete_flag'])}",
                "GPT review artifact must exist before final Task703 report",
            ),
            gate(
                "eval_rows_complete",
                len(axis_eval) == len(axis_freeze) and int(axis_eval["outcome_used_for_evaluation_flag"].sum()) == len(axis_freeze),
                f"eval_rows={len(axis_eval)}",
                "evaluation attaches outcomes after freeze",
            ),
            gate(
                "portfolio_comparison_present",
                {"all_5265_baseline_costed", "event_linked_2445_costed", "full_event_axis_eligible", "QQQ_buy_and_hold_same_horizon"}.issubset(
                    set(portfolio_comparison["portfolio_cohort"])
                ),
                "|".join(sorted(set(portfolio_comparison["portfolio_cohort"]))),
                "portfolio cohorts and QQQ benchmark present",
            ),
            gate(
                "no_strategy_or_trade_promotion",
                int(axis_freeze["allocation_approved_flag"].sum()) == 0
                and int(axis_freeze["paper_or_live_trade_approved_flag"].sum()) == 0,
                "allocation_approved=0; paper_or_live_trade_approved=0",
                "Task703 is research-only",
            ),
        ]
    )


def build_decision(
    axis_freeze: pd.DataFrame,
    action_summary: pd.DataFrame,
    split_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    audit: pd.DataFrame,
    gpt_status: pd.DataFrame,
) -> pd.DataFrame:
    eligible_summary = action_summary[action_summary["full_event_axis_action"].eq("ELIGIBLE_RULE_CANDIDATE")].iloc[0]
    eligible_max5 = portfolio_row(portfolio_comparison, "full_event_axis_eligible", 5)
    event_linked_max5 = portfolio_row(portfolio_comparison, "event_linked_2445_costed", 5)
    baseline_max5 = portfolio_row(portfolio_comparison, "all_5265_baseline_costed", 5)
    qqq_row = portfolio_comparison[portfolio_comparison["portfolio_cohort"].eq("QQQ_buy_and_hold_same_horizon")].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": "Task703",
                "verdict": "EVENT_LINKED_SOURCE_AXIS_FULL_PERIOD_BACKTEST_COMPLETE_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "freeze_count": int(len(axis_freeze)),
                "event_linked_count": int(axis_freeze["source_event_available_flag"].sum()),
                "eligible_count": int(axis_freeze["full_event_axis_eligible_flag"].sum()),
                "eligible_avg_costed_return_pct": float(eligible_summary["avg_costed_return_pct"]),
                "eligible_win_rate": float(eligible_summary["win_rate"]),
                "eligible_max5_final_capital_usd": float(eligible_max5["final_capital_usd"]),
                "eligible_max5_return_pct": float(eligible_max5["capital_return_pct"]),
                "eligible_max5_mdd_pct": float(eligible_max5["max_drawdown_pct"]),
                "event_linked_max5_final_capital_usd": float(event_linked_max5["final_capital_usd"]),
                "baseline_max5_final_capital_usd": float(baseline_max5["final_capital_usd"]),
                "qqq_buyhold_final_capital_usd": float(qqq_row["final_capital_usd"]),
                "gpt_review_complete_flag": int(gpt_status.iloc[0]["gpt_review_complete_flag"]),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "The five-axis parser was moved upstream to all Task636 event-linked candidates and backtested over the full baseline horizon.",
                "research_caveat": "The parser improves source interpretation coverage but remains research-only until larger OOS and parser-source certification are audited.",
                "next_action": "Diagnose eligible split/OOS durability and compare against Task639 before any promotion discussion.",
            }
        ]
    )


def portfolio_row(portfolio_comparison: pd.DataFrame, cohort: str, max_positions: int) -> pd.Series:
    return portfolio_comparison[
        portfolio_comparison["portfolio_cohort"].eq(cohort) & portfolio_comparison["max_positions"].eq(max_positions)
    ].iloc[0]


def write_outputs(
    out_dir: Path,
    axis_freeze: pd.DataFrame,
    axis_eval: pd.DataFrame,
    action_summary: pd.DataFrame,
    split_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    gpt_status: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> None:
    outputs = {
        "task703_axis_freeze_panel.csv": axis_freeze,
        "task703_axis_eval_panel.csv": axis_eval,
        "task703_action_summary.csv": action_summary,
        "task703_split_summary.csv": split_summary,
        "task703_portfolio_comparison.csv": portfolio_comparison,
        "task703_gpt_review_status.csv": gpt_status,
        "task703_integrity_audit.csv": audit,
        "task_703_pass_fail_matrix.csv": pass_fail,
        "task_703_decision.csv": decision,
    }
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    (out_dir / "task_703_event_linked_source_axis_backtest.md").write_text(
        render_report(axis_freeze, axis_eval, action_summary, split_summary, portfolio_comparison, gpt_status, audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def render_report(
    axis_freeze: pd.DataFrame,
    axis_eval: pd.DataFrame,
    action_summary: pd.DataFrame,
    split_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    gpt_status: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    portfolio_view = portfolio_comparison[
        [
            "portfolio_cohort",
            "max_positions",
            "source_candidate_count",
            "accepted_trade_count",
            "final_capital_usd",
            "capital_return_pct",
            "max_drawdown_pct",
            "beats_qqq_flag",
        ]
    ]
    return f"""# Task703 Event-Linked Source Axis Full-Period Backtest

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Scope: full baseline {int(d["freeze_count"])} rows, event-linked {int(d["event_linked_count"])} rows.
- Eligible count: {int(d["eligible_count"])}.
- Key $1,000 max5: eligible ${float(d["eligible_max5_final_capital_usd"]):,.2f}; event-linked ${float(d["event_linked_max5_final_capital_usd"]):,.2f}; baseline ${float(d["baseline_max5_final_capital_usd"]):,.2f}; QQQ ${float(d["qqq_buyhold_final_capital_usd"]):,.2f}.
- GPT review complete flag: {int(d["gpt_review_complete_flag"])}.
- Main finding: {d["primary_result"]}
- Next action: {d["next_action"]}

## Quant Expert Report

### Parser Scope

- Parser moved from Task702 19 source-packet rows to Task636 2,445 event-linked lifecycles.
- Full freeze scope remains the 5,265 baseline candidates.
- Price context uses Task704 raw daily plus intraday as-of-entry backfill when available.
- Outcomes are attached only after freeze.

### GPT Review

{t678.markdown_table(gpt_status)}

### Action Summary

{t678.markdown_table(action_summary)}

### Split Summary For Eligible Candidates

{t678.markdown_table(split_summary)}

### Portfolio Comparison

{t678.markdown_table(portfolio_view)}

### Interpretation

- The five-axis parser now has materially broader coverage.
- This is still research-only because parser quality, OOS durability, and source certification need separate audit.

## No-Background Decision-Maker Report

- What happened: the parser moved upstream to all event-linked candidates.
- What changed: full-period backtest now covers 5,265 baseline candidates and 2,445 event-linked candidates.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task636 links/predictions, Task633/632 full baseline backtest panel, Task704 price context, Task684 legacy fallback context, QQQ daily.
- Outputs: freeze panel, eval panel, summaries, portfolio comparison, GPT review status, audit, decision, pass/fail, manifest.
- Row counts: freeze {len(axis_freeze)}, eval {len(axis_eval)}, action summary {len(action_summary)}.
- Validation commands: `python src/backtest/build_task703_event_linked_source_axis_backtest.py`; `python -m unittest tests.test_task703_event_linked_source_axis_backtest`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def int_safe(value: object) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task636-dir", type=Path, default=TASK636_DIR)
    parser.add_argument("--baseline-panel", type=Path, default=BASELINE_PANEL)
    parser.add_argument("--task684-panel", type=Path, default=TASK684_PANEL)
    parser.add_argument("--task704-price-context", type=Path, default=TASK704_PRICE_CONTEXT_PANEL)
    parser.add_argument("--qqq-daily", type=Path, default=QQQ_DAILY)
    parser.add_argument("--out-dir", type=Path, default=TASK703_DIR)
    args = parser.parse_args()
    build_task703_program(
        task636_dir=args.task636_dir,
        baseline_panel_path=args.baseline_panel,
        task684_panel_path=args.task684_panel,
        task704_price_context_path=args.task704_price_context,
        qqq_daily_path=args.qqq_daily,
        out_dir=args.out_dir,
    )
    print(f"[Task703] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
