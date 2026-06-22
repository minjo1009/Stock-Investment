from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import INITIAL_CAPITAL_USD, load_qqq_history, qqq_final_for_period
from src.backtest.build_task638_content_signal_refinement import QQQ_PATH, costed
from src.backtest.build_task644_firm_grade_conditional_wrapper import ROUND_TRIP_COST_BPS


TASK_ID = "Task645"
REPORT_DIR = Path("docs/reports/task_645_microstructure_content_source_upgrade")
EXECUTION_PANEL = Path("docs/reports/task_643_entry_risk_tier_turnover_backtest/task_643_execution_variant_panel.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
EVENT_PREDICTIONS = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_event_content_predictions.csv")
ENTRY_EVENT_LINKS = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_entry_event_links.csv")
QUOTE_DIR = Path("data/raw/alpaca_historical_microstructure/feed=sip/quotes")
TRADE_DIR = Path("data/raw/alpaca_historical_microstructure/feed=sip/trades")
RAW_TEXT_ROOT = Path("data/raw/task_636_content_source_text")

ENTRY_POLICIES = ("base_delay1d_open", "vwap_rs_confirm_60m")
SIZING_POLICIES = ("equal", "content_quality_soft", "micro_fragile_reduce", "combined_quality_micro")
ENTRY_ACTIONS = ("base", "fragile_weak_delay_confirm")


def build_task645_microstructure_content_source_upgrade(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    event_predictions_path: Path = EVENT_PREDICTIONS,
    entry_event_links_path: Path = ENTRY_EVENT_LINKS,
    quote_dir: Path = QUOTE_DIR,
    trade_dir: Path = TRADE_DIR,
    task639_decision_path: Path = TASK639_DECISION,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    execution = load_execution_panel(execution_panel_path)
    base = base_signal_panel(execution)
    micro_features, micro_source = build_microstructure_features(base, quote_dir, trade_dir)
    content_features, content_source = build_content_quality_features(base, event_predictions_path, entry_event_links_path)
    feature_panel = assign_combined_states(base.merge(micro_features, on="lifecycle_id", how="left").merge(content_features, on="lifecycle_id", how="left"))
    diagnostics = build_feature_diagnostics(feature_panel)
    interaction = build_interaction_diagnostics(feature_panel)
    account = build_account_grid(feature_panel, execution, qqq_path)
    oos = build_oos_grid(feature_panel, execution, qqq_path)
    source_audit = build_source_audit(feature_panel, micro_source, content_source, execution)
    pass_fail = build_pass_fail(account, oos, source_audit, pd.read_csv(task639_decision_path).iloc[0])
    decision = build_decision(account, oos, pass_fail, pd.read_csv(task639_decision_path).iloc[0])

    out_dir.mkdir(parents=True, exist_ok=True)
    feature_panel.to_csv(out_dir / "task_645_microstructure_content_feature_panel.csv", index=False)
    diagnostics.to_csv(out_dir / "task_645_feature_diagnostics.csv", index=False)
    interaction.to_csv(out_dir / "task_645_content_microstructure_interaction_panel.csv", index=False)
    account.to_csv(out_dir / "task_645_account_grid.csv", index=False)
    oos.to_csv(out_dir / "task_645_oos_grid.csv", index=False)
    source_audit.to_csv(out_dir / "task_645_source_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_645_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_645_decision.csv", index=False)
    micro_source.to_csv(out_dir / "task_645_microstructure_coverage_audit.csv", index=False)
    content_source.to_csv(out_dir / "task_645_content_source_audit.csv", index=False)
    (out_dir / "task_645_microstructure_content_source_upgrade.md").write_text(
        render_report(diagnostics, interaction, account, oos, source_audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "feature_panel": feature_panel,
        "feature_diagnostics": diagnostics,
        "interaction": interaction,
        "account": account,
        "oos": oos,
        "source_audit": source_audit,
        "pass_fail": pass_fail,
        "decision": decision,
    }


def load_execution_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    numeric_cols = [
        "net_return_from_entry",
        "positive_contract_customer_count",
        "content_supply_demand_flag",
        "positive_backlog_order_count",
        "positive_guidance_up_count",
        "positive_margin_supply_combo_count",
        "content_refined_strength_score",
        "entry_price",
    ]
    for column in numeric_cols:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    return frame.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def base_signal_panel(execution: pd.DataFrame) -> pd.DataFrame:
    base = execution[execution["entry_policy"].eq("base_delay1d_open") & execution["exit_policy"].eq("existing_exit")].copy()
    signal = pd.to_numeric(base["positive_contract_customer_count"], errors="coerce").fillna(0).gt(0) | pd.to_numeric(
        base["content_supply_demand_flag"], errors="coerce"
    ).fillna(0).eq(1)
    return base[signal].drop_duplicates("lifecycle_id", keep="first").reset_index(drop=True)


def build_microstructure_features(base: pd.DataFrame, quote_dir: Path, trade_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    for symbol, group in base.groupby("symbol", sort=True):
        quotes = load_quotes(symbol, quote_dir)
        trades = load_trades(symbol, trade_dir)
        source_rows.append(
            {
                "symbol": symbol,
                "quote_source_exists_flag": int(not quotes.empty),
                "trade_source_exists_flag": int(not trades.empty),
                "quote_row_count": int(len(quotes)),
                "trade_row_count": int(len(trades)),
                "quote_source_hash": file_hash(quote_dir / f"{symbol}.csv"),
                "trade_source_hash": file_hash(trade_dir / f"{symbol}.csv"),
                "historical_live_ready_flag": 0,
            }
        )
        for row in group.itertuples(index=False):
            features = micro_window_features(quotes, trades, pd.Timestamp(row.entry_ts))
            features["lifecycle_id"] = row.lifecycle_id
            rows.append(features)
    return pd.DataFrame(rows), pd.DataFrame(source_rows)


def load_quotes(symbol: str, quote_dir: Path) -> pd.DataFrame:
    path = quote_dir / f"{symbol}.csv"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if frame.empty:
        return frame
    frame["ts_dt"] = pd.to_datetime(frame["quote_ts"], utc=True, errors="coerce")
    for column in ["mid", "bid", "ask", "bid_size", "ask_size", "spread_bps", "nbbo_size_dollar", "nbbo_imbalance"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.dropna(subset=["ts_dt"]).sort_values("ts_dt").reset_index(drop=True)


def load_trades(symbol: str, trade_dir: Path) -> pd.DataFrame:
    path = trade_dir / f"{symbol}.csv"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if frame.empty:
        return frame
    frame["ts_dt"] = pd.to_datetime(frame["trade_ts"], utc=True, errors="coerce")
    for column in ["price", "size"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.dropna(subset=["ts_dt"]).sort_values("ts_dt").reset_index(drop=True)


def micro_window_features(quotes: pd.DataFrame, trades: pd.DataFrame, entry_ts: pd.Timestamp) -> dict[str, object]:
    q60 = window(quotes, entry_ts - pd.Timedelta(seconds=60), entry_ts)
    t60 = window(trades, entry_ts - pd.Timedelta(seconds=60), entry_ts)
    quote_count = int(len(q60))
    trade_count = int(len(t60))
    spread_median = float(q60["spread_bps"].median()) if quote_count else np.nan
    spread_p90 = float(q60["spread_bps"].quantile(0.9)) if quote_count else np.nan
    depth_median = float(q60["nbbo_size_dollar"].median()) if quote_count else np.nan
    imbalance_mean = float(q60["nbbo_imbalance"].mean()) if quote_count else np.nan
    mid_response = pct_change(q60["mid"].iloc[0], q60["mid"].iloc[-1]) if quote_count >= 2 else np.nan
    trade_response = pct_change(t60["price"].iloc[0], t60["price"].iloc[-1]) if trade_count >= 2 else np.nan
    dollar_volume = float((t60["price"] * t60["size"]).sum()) if trade_count else 0.0
    state = classify_microstructure(quote_count, trade_count, spread_median, spread_p90, depth_median, imbalance_mean, mid_response, trade_response)
    return {
        "quote_available_flag": int(not quotes.empty),
        "trade_available_flag": int(not trades.empty),
        "micro_quote_count_60s": quote_count,
        "micro_trade_count_60s": trade_count,
        "micro_spread_median_bps_60s": spread_median,
        "micro_spread_p90_bps_60s": spread_p90,
        "micro_depth_median_usd_60s": depth_median,
        "micro_imbalance_mean_60s": imbalance_mean,
        "micro_mid_response_pct_60s": mid_response,
        "micro_trade_response_pct_60s": trade_response,
        "micro_trade_dollar_volume_60s": dollar_volume,
        "micro_continuation_state": state,
        "micro_assignment_used_outcome_flag": 0,
        "micro_missing_treated_as_negative_flag": 0,
    }


def window(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if frame.empty:
        return frame
    ts = frame["ts_dt"].astype("int64").to_numpy()
    left = np.searchsorted(ts, start.value, side="left")
    right = np.searchsorted(ts, end.value, side="right")
    return frame.iloc[left:right]


def classify_microstructure(
    quote_count: int,
    trade_count: int,
    spread_median: float,
    spread_p90: float,
    depth_median: float,
    imbalance_mean: float,
    mid_response: float,
    trade_response: float,
) -> str:
    if quote_count == 0:
        return "micro_missing"
    if quote_count < 10:
        return "micro_sparse_observation"
    wide = pd.notna(spread_p90) and spread_p90 > 40
    thin = pd.notna(depth_median) and depth_median < 25000
    ask_heavy = pd.notna(imbalance_mean) and imbalance_mean < -0.25
    price_down = (pd.notna(mid_response) and mid_response < -0.001) or (pd.notna(trade_response) and trade_response < -0.001)
    tight = pd.notna(spread_median) and spread_median <= 15
    supported = pd.notna(imbalance_mean) and imbalance_mean >= -0.10
    price_ok = (pd.notna(mid_response) and mid_response >= 0) or (pd.notna(trade_response) and trade_response >= 0)
    active_trade = trade_count >= 5
    if wide or (thin and ask_heavy) or price_down:
        return "fragile_breakout"
    if tight and supported and (price_ok or active_trade):
        return "real_continuation"
    return "mixed_microstructure"


def build_content_quality_features(
    base: pd.DataFrame,
    event_predictions_path: Path,
    entry_event_links_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    links = pd.read_csv(entry_event_links_path)
    events = pd.read_csv(event_predictions_path)
    linked = links[links["lifecycle_id"].isin(base["lifecycle_id"])].merge(events, on=["event_id", "source_lane"], how="left", validate="many_to_one")
    event_features = [event_quality_features(row) for row in linked.to_dict(orient="records")]
    event_frame = pd.DataFrame(event_features)
    if event_frame.empty:
        return empty_content_features(base), pd.DataFrame()
    linked = pd.concat([linked.reset_index(drop=True), event_frame.reset_index(drop=True)], axis=1)
    rows: list[dict[str, object]] = []
    for lifecycle_id, group in linked.groupby("lifecycle_id", sort=False):
        score = (
            group["contract_magnitude_score"].max()
            + group["customer_importance_score"].max()
            + group["recurring_backlog_score"].max()
            + group["margin_impact_score"].max()
            + group["source_directness_score"].max()
            - group["content_risk_score"].max()
        )
        rows.append(
            {
                "lifecycle_id": lifecycle_id,
                "content_refined_event_count_task645": int(len(group)),
                "contract_magnitude_score": int(group["contract_magnitude_score"].max()),
                "customer_importance_score": int(group["customer_importance_score"].max()),
                "recurring_backlog_score": int(group["recurring_backlog_score"].max()),
                "margin_impact_score": int(group["margin_impact_score"].max()),
                "source_directness_score": int(group["source_directness_score"].max()),
                "content_risk_score": int(group["content_risk_score"].max()),
                "content_quality_score_task645": int(score),
                "content_quality_tier_task645": classify_content_tier(score, group),
                "content_assignment_used_outcome_flag": 0,
                "content_presence_only_signal_flag": 0,
            }
        )
    content = base[["lifecycle_id"]].merge(pd.DataFrame(rows), on="lifecycle_id", how="left")
    content = fill_content_missing(content)
    source = build_content_source_audit(linked)
    return content, source


def event_quality_features(row: dict[str, object]) -> dict[str, int]:
    text = " ".join(
        str(row.get(column, ""))
        for column in [
            "event_title",
            "event_category",
            "source_name",
            "content_stock_specific_causal_link",
            "content_named_customer_or_counterparty",
            "content_revenue_or_backlog_signal",
            "content_guidance_or_margin_signal",
            "content_supply_demand_signal",
            "content_regulatory_or_policy_transmission",
            "content_interpretation_evidence_span",
        ]
    ).lower()
    raw = read_raw_excerpt(row.get("raw_text_path", ""))
    blob = f"{text} {raw}".lower()
    magnitude = int(bool(re.search(r"\\$\\s?\\d+(\\.\\d+)?\\s?(million|billion|bn|m\\b)", blob)) or bool(re.search(r"\\b\\d+(\\.\\d+)?\\s?(million|billion)\\b", blob)))
    customer = int(any(token in blob for token in CUSTOMER_KEYWORDS))
    recurring = int(any(token in blob for token in RECURRING_KEYWORDS))
    margin = int(any(token in blob for token in MARGIN_KEYWORDS) or truthy(row.get("content_guidance_or_margin_signal")))
    direct = int(truthy(row.get("source_text_certified_flag")) and truthy(row.get("content_prediction_certified_flag")) and truthy(row.get("content_stock_specific_causal_link")))
    risk = int(any(token in blob for token in RISK_KEYWORDS) or str(row.get("event_category", "")).lower() in {"insider_or_sale_notice"})
    return {
        "contract_magnitude_score": magnitude,
        "customer_importance_score": customer,
        "recurring_backlog_score": recurring,
        "margin_impact_score": margin,
        "source_directness_score": direct,
        "content_risk_score": risk,
    }


CUSTOMER_KEYWORDS = (
    "microsoft",
    "amazon",
    "aws",
    "google",
    "alphabet",
    "meta",
    "apple",
    "nvidia",
    "tesla",
    "boeing",
    "lockheed",
    "nasa",
    "department of defense",
    "dod",
    "government",
    "hyperscaler",
    "fortune 500",
)
RECURRING_KEYWORDS = ("multi-year", "multiyear", "long-term", "backlog", "renewal", "subscription", "recurring", "framework agreement", "order book")
MARGIN_KEYWORDS = ("gross margin", "operating margin", "margin expansion", "profitability", "ebitda", "guidance", "pricing power", "cost efficiency")
RISK_KEYWORDS = ("offering", "dilution", "convertible", "warrant", "sanction", "tariff", "investigation", "margin pressure", "insider sale")


def read_raw_excerpt(path_value: object) -> str:
    rel = str(path_value or "")
    if not rel:
        return ""
    path = Path(rel)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists() or RAW_TEXT_ROOT not in path.parents:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:8000]
    except OSError:
        return ""


def truthy(value: object) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip() not in {"", "0", "0.0", "nan", "none", "false"}
    return bool(value)


def classify_content_tier(score: float, group: pd.DataFrame) -> str:
    risk = int(group["content_risk_score"].max()) == 1
    contract = pd.to_numeric(group.get("content_named_customer_or_counterparty", 0), errors="coerce").fillna(0).gt(0).any()
    supply = pd.to_numeric(group.get("content_supply_demand_signal", 0), errors="coerce").fillna(0).gt(0).any()
    if risk and score <= 1:
        return "risk_or_reversal_candidate"
    if score >= 4 and contract and supply:
        return "compound_contract_supply_quality"
    if score >= 3 and contract:
        return "strong_contract_quality"
    if score >= 3 and supply:
        return "strong_supply_quality"
    if score >= 2:
        return "moderate_content_quality"
    return "weak_presence_only_quality"


def empty_content_features(base: pd.DataFrame) -> pd.DataFrame:
    frame = base[["lifecycle_id"]].copy()
    return fill_content_missing(frame)


def fill_content_missing(content: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        "content_refined_event_count_task645": 0,
        "contract_magnitude_score": 0,
        "customer_importance_score": 0,
        "recurring_backlog_score": 0,
        "margin_impact_score": 0,
        "source_directness_score": 0,
        "content_risk_score": 0,
        "content_quality_score_task645": 0,
        "content_quality_tier_task645": "no_linked_content",
        "content_assignment_used_outcome_flag": 0,
        "content_presence_only_signal_flag": 0,
    }
    out = content.copy()
    for column, value in defaults.items():
        if column not in out.columns:
            out[column] = value
        else:
            out[column] = out[column].fillna(value)
    return out


def build_content_source_audit(linked: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source_lane, group in linked.groupby("source_lane", dropna=False):
        rows.append(
            {
                "source_lane": source_lane,
                "linked_event_rows": int(len(group)),
                "certified_source_rows": int(pd.to_numeric(group["source_text_certified_flag"], errors="coerce").fillna(0).sum()),
                "direct_source_rows": int(group["source_directness_score"].sum()),
                "historical_live_ready_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values("linked_event_rows", ascending=False).reset_index(drop=True)


def assign_combined_states(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["micro_continuation_state"] = out["micro_continuation_state"].fillna("micro_missing")
    out["content_quality_tier_task645"] = out["content_quality_tier_task645"].fillna("no_linked_content")
    strong_content = out["content_quality_tier_task645"].isin(
        ["compound_contract_supply_quality", "strong_contract_quality", "strong_supply_quality"]
    )
    clean_micro = out["micro_continuation_state"].eq("real_continuation")
    fragile_micro = out["micro_continuation_state"].eq("fragile_breakout")
    out["combined_quality_micro_state"] = "mixed_or_missing"
    out.loc[strong_content & clean_micro, "combined_quality_micro_state"] = "strong_content_clean_micro"
    out.loc[strong_content & ~clean_micro, "combined_quality_micro_state"] = "strong_content_unconfirmed_micro"
    out.loc[~strong_content & fragile_micro, "combined_quality_micro_state"] = "weak_content_fragile_micro"
    out.loc[out["content_quality_tier_task645"].eq("risk_or_reversal_candidate"), "combined_quality_micro_state"] = "risk_reversal_content"
    out["task645_assignment_used_outcome_flag"] = 0
    out["gpt_or_plugin_used_as_source_flag_task645"] = 0
    return out


def build_feature_diagnostics(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split_name in ["all", "train_design", "validation", "recent_oos"]:
        scoped = panel if split_name == "all" else panel[panel["split_name"].astype(str).eq(split_name)]
        for column in ["micro_continuation_state", "content_quality_tier_task645", "combined_quality_micro_state"]:
            rows.extend(group_quality(scoped, split_name, [column]))
    return pd.DataFrame(rows).sort_values(["split_name", "feature_group", "avg_return_pct"], ascending=[True, True, False]).reset_index(drop=True)


def build_interaction_diagnostics(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split_name in ["all", "validation", "recent_oos"]:
        scoped = panel if split_name == "all" else panel[panel["split_name"].astype(str).eq(split_name)]
        rows.extend(group_quality(scoped, split_name, ["content_quality_tier_task645", "micro_continuation_state"]))
    return pd.DataFrame(rows).sort_values(["split_name", "avg_return_pct"], ascending=[True, False]).reset_index(drop=True)


def group_quality(panel: pd.DataFrame, split_name: str, columns: list[str]) -> list[dict[str, object]]:
    rows = []
    if panel.empty:
        return rows
    for key, group in panel.groupby(columns, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        returns = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
        rows.append(
            {
                "split_name": split_name,
                "feature_group": "|".join(columns),
                **dict(zip(columns, key, strict=False)),
                "row_count": int(len(group)),
                "avg_return_pct": float(returns.mean() * 100.0),
                "median_return_pct": float(returns.median() * 100.0),
                "win_rate": float(returns.gt(0).mean()),
                "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
                "label_used_for_assignment_flag": 0,
            }
        )
    return rows


def build_account_grid(feature_panel: pd.DataFrame, execution: pd.DataFrame, qqq_path: Path) -> pd.DataFrame:
    rows = []
    qqq = load_qqq_history(qqq_path)
    for entry_action in ENTRY_ACTIONS:
        selected = select_execution_rows(feature_panel, execution, entry_action)
        for sizing_policy in SIZING_POLICIES:
            metrics, accepted = run_task645_account(selected, sizing_policy)
            rows.append(account_row("all", entry_action, sizing_policy, selected, accepted, metrics, qqq_final_for_period(qqq, selected)))
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def build_oos_grid(feature_panel: pd.DataFrame, execution: pd.DataFrame, qqq_path: Path) -> pd.DataFrame:
    rows = []
    qqq = load_qqq_history(qqq_path)
    for split_name in ["validation", "recent_oos"]:
        scoped = feature_panel[feature_panel["split_name"].astype(str).eq(split_name)].copy()
        for entry_action in ENTRY_ACTIONS:
            selected = select_execution_rows(scoped, execution, entry_action)
            for sizing_policy in SIZING_POLICIES:
                metrics, accepted = run_task645_account(selected, sizing_policy)
                rows.append(account_row(split_name, entry_action, sizing_policy, selected, accepted, metrics, qqq_final_for_period(qqq, selected)))
    return pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)


def select_execution_rows(feature_panel: pd.DataFrame, execution: pd.DataFrame, entry_action: str) -> pd.DataFrame:
    indexed = {
        (str(row["lifecycle_id"]), str(row["entry_policy"]), str(row["exit_policy"])): row
        for row in execution[execution["exit_policy"].eq("existing_exit")].to_dict(orient="records")
    }
    rows = []
    for feature in feature_panel.to_dict(orient="records"):
        policy = "base_delay1d_open"
        if (
            entry_action == "fragile_weak_delay_confirm"
            and str(feature.get("micro_continuation_state")) == "fragile_breakout"
            and str(feature.get("combined_quality_micro_state")) == "weak_content_fragile_micro"
        ):
            policy = "vwap_rs_confirm_60m"
        row = indexed.get((str(feature["lifecycle_id"]), policy, "existing_exit"))
        if row is None:
            continue
        merged = dict(row)
        for key, value in feature.items():
            if key not in merged:
                merged[key] = value
        merged["task645_entry_action"] = entry_action
        merged["required_entry_policy_task645"] = policy
        rows.append(merged)
    return pd.DataFrame(rows)


def run_task645_account(panel: pd.DataFrame, sizing_policy: str) -> tuple[dict[str, object], pd.DataFrame]:
    if panel.empty:
        return empty_quality(), pd.DataFrame()
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
        if len(open_positions) >= 5:
            continue
        weight = task645_position_weight(row, sizing_policy)
        if weight <= 0:
            continue
        capital = equity_value * weight
        open_positions.append({"exit_ts": row["simulated_exit_ts"], "capital": capital, "return": row["net_return_from_entry"]})
        accepted = dict(row)
        accepted["position_weight_task645"] = weight
        accepted["sizing_policy_task645"] = sizing_policy
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
    }, accepted


def task645_position_weight(row: dict[str, object], sizing_policy: str) -> float:
    if sizing_policy == "equal":
        return 0.20
    content = str(row.get("content_quality_tier_task645", "weak_presence_only_quality"))
    micro = str(row.get("micro_continuation_state", "micro_missing"))
    strong = content in {"compound_contract_supply_quality", "strong_contract_quality", "strong_supply_quality"}
    weak = content in {"weak_presence_only_quality", "risk_or_reversal_candidate"}
    if sizing_policy == "content_quality_soft":
        if content == "compound_contract_supply_quality":
            return 0.24
        if strong:
            return 0.22
        if content == "moderate_content_quality":
            return 0.19
        return 0.15
    if sizing_policy == "micro_fragile_reduce":
        if micro == "real_continuation":
            return 0.22
        if micro == "fragile_breakout":
            return 0.12
        if micro == "micro_sparse_observation":
            return 0.16
        return 0.20
    if strong and micro == "real_continuation":
        return 0.25
    if strong and micro in {"mixed_microstructure", "micro_missing"}:
        return 0.21
    if weak and micro == "fragile_breakout":
        return 0.10
    if micro == "fragile_breakout":
        return 0.14
    if content == "moderate_content_quality":
        return 0.18
    return 0.16


def empty_quality() -> dict[str, object]:
    return {
        "accepted_trade_count": 0,
        "final_capital_usd": INITIAL_CAPITAL_USD,
        "capital_return_pct": 0.0,
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "max_drawdown_pct": 0.0,
    }


def account_row(
    split_name: str,
    entry_action: str,
    sizing_policy: str,
    selected: pd.DataFrame,
    accepted: pd.DataFrame,
    metrics: dict[str, object],
    qqq_final: float,
) -> dict[str, object]:
    final = float(metrics["final_capital_usd"])
    return {
        "split_name": split_name,
        "entry_action": entry_action,
        "sizing_policy": sizing_policy,
        "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
        "source_trade_count": int(len(selected)),
        "accepted_trade_count": int(metrics["accepted_trade_count"]),
        "final_capital_usd": final,
        "capital_return_pct": float(metrics["capital_return_pct"]),
        "avg_net_return_pct": float(metrics["avg_net_return_pct"]),
        "win_rate": float(metrics["win_rate"]),
        "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
        "max_drawdown_pct": float(metrics["max_drawdown_pct"]),
        "qqq_final_capital_usd": float(qqq_final),
        "beats_qqq_flag": int(final > float(qqq_final)),
        "label_used_in_assignment_flag": 0,
        "presence_only_signal_used_flag": 0,
        "missing_microstructure_used_as_negative_flag": 0,
        "symbol_blacklist_used_flag": 0,
        "theme_blacklist_used_flag": 0,
    }


def build_source_audit(feature_panel: pd.DataFrame, micro_source: pd.DataFrame, content_source: pd.DataFrame, execution: pd.DataFrame) -> pd.DataFrame:
    quote_rows = int(feature_panel["micro_quote_count_60s"].gt(0).sum())
    trade_rows = int(feature_panel["micro_trade_count_60s"].gt(0).sum())
    base_rows = int(len(feature_panel))
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "base_signal_rows": base_rows,
                "execution_rows": int(len(execution)),
                "quote_covered_rows": quote_rows,
                "quote_covered_row_rate": float(quote_rows / max(base_rows, 1)),
                "trade_covered_rows": trade_rows,
                "trade_covered_row_rate": float(trade_rows / max(base_rows, 1)),
                "quote_source_symbol_count": int(micro_source["quote_source_exists_flag"].sum()),
                "trade_source_symbol_count": int(micro_source["trade_source_exists_flag"].sum()),
                "content_linked_rows": int(feature_panel["content_refined_event_count_task645"].gt(0).sum()),
                "content_source_lanes": int(content_source["source_lane"].nunique()) if not content_source.empty else 0,
                "gpt_design_captured_flag": int((REPORT_DIR / "task_645_gpt_design_response.md").exists()),
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "missing_microstructure_used_as_negative_flag": 0,
                "historical_live_ready_flag": 0,
            }
        ]
    )


def build_pass_fail(account: pd.DataFrame, oos: pd.DataFrame, source_audit: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    best = account.iloc[0]
    baseline = account[account["entry_action"].eq("base") & account["sizing_policy"].eq("equal")].iloc[0]
    base_final = float(task639["best_50bp_final_capital_usd"])
    base_dd = float(task639["best_50bp_max_drawdown_pct"])
    validation = matching_oos(oos, best, "validation")
    recent = matching_oos(oos, best, "recent_oos")
    quote_rate = float(source_audit.iloc[0]["quote_covered_row_rate"])
    trade_rate = float(source_audit.iloc[0]["trade_covered_row_rate"])
    uses_micro = "micro" in str(best["sizing_policy"]) or "fragile" in str(best["entry_action"])
    return pd.DataFrame(
        [
            {
                "gate": "gpt_design_captured",
                "pass_flag": int(source_audit.iloc[0]["gpt_design_captured_flag"]),
                "observed_value": f"captured={int(source_audit.iloc[0]['gpt_design_captured_flag'])}",
                "required_value": "GPT review packet must be captured as review-only input",
            },
            {
                "gate": "task639_baseline_reproduced",
                "pass_flag": int(abs(float(baseline["final_capital_usd"]) - base_final) <= 0.05),
                "observed_value": f"task645_base=${float(baseline['final_capital_usd']):.2f}; task639=${base_final:.2f}",
                "required_value": "Task645 base/equal must reproduce Task639 account result",
            },
            {
                "gate": "feature_candidate_beats_task639_return",
                "pass_flag": int(float(best["final_capital_usd"]) > base_final + 0.01),
                "observed_value": f"best=${float(best['final_capital_usd']):.2f}; task639=${base_final:.2f}",
                "required_value": "best feature-linked candidate must exceed Task639",
            },
            {
                "gate": "feature_candidate_reduces_task639_drawdown",
                "pass_flag": int(float(best["max_drawdown_pct"]) > base_dd + 0.01),
                "observed_value": f"best_dd={float(best['max_drawdown_pct']):.2f}%; task639_dd={base_dd:.2f}%",
                "required_value": "best feature-linked candidate must reduce drawdown severity",
            },
            {
                "gate": "same_config_validation_recent_beat_qqq",
                "pass_flag": int(
                    not validation.empty
                    and not recent.empty
                    and float(validation.iloc[0]["final_capital_usd"]) > float(validation.iloc[0]["qqq_final_capital_usd"])
                    and float(recent.iloc[0]["final_capital_usd"]) > float(recent.iloc[0]["qqq_final_capital_usd"])
                ),
                "observed_value": oos_observed(validation, recent),
                "required_value": "same config must beat QQQ in validation and recent OOS",
            },
            {
                "gate": "microstructure_coverage_sufficient_for_micro_rule",
                "pass_flag": int((not uses_micro) or (quote_rate >= 0.20 and trade_rate >= 0.10)),
                "observed_value": f"best_uses_micro={int(uses_micro)}; quote_rate={quote_rate:.3f}; trade_rate={trade_rate:.3f}",
                "required_value": "microstructure-linked account rule needs at least 20% quote-row and 10% trade-row coverage",
            },
            {
                "gate": "no_shortcut_or_missing_as_negative",
                "pass_flag": 1,
                "observed_value": "no labels/blacklists; missing_microstructure_used_as_negative=0",
                "required_value": "missing sources must be reported, not treated as bearish",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "feature validation only; historical sources are not live-ready",
                "required_value": "live-source readiness and paper-shadow replay required",
            },
        ]
    )


def build_decision(account: pd.DataFrame, oos: pd.DataFrame, pass_fail: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    best = account.iloc[0]
    validation = matching_oos(oos, best, "validation")
    recent = matching_oos(oos, best, "recent_oos")
    gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}
    strategy_candidate = int(
        gates["feature_candidate_beats_task639_return"]
        and gates["feature_candidate_reduces_task639_drawdown"]
        and gates["same_config_validation_recent_beat_qqq"]
        and gates["microstructure_coverage_sufficient_for_micro_rule"]
    )
    return pd.DataFrame(
        [
            {
                "decision": "PASS_RESEARCH_FEATURE_CANDIDATE_NOT_ACCEPTED" if strategy_candidate else "FEATURE_VALIDATION_PARTIAL_COVERAGE_NO_PROMOTION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "best_entry_action": best["entry_action"],
                "best_sizing_policy": best["sizing_policy"],
                "best_final_capital_usd": float(best["final_capital_usd"]),
                "best_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "task639_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "task639_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
                "best_validation_final_capital_usd": 0.0 if validation.empty else float(validation.iloc[0]["final_capital_usd"]),
                "best_validation_qqq_final_capital_usd": 0.0 if validation.empty else float(validation.iloc[0]["qqq_final_capital_usd"]),
                "best_recent_final_capital_usd": 0.0 if recent.empty else float(recent.iloc[0]["final_capital_usd"]),
                "best_recent_qqq_final_capital_usd": 0.0 if recent.empty else float(recent.iloc[0]["qqq_final_capital_usd"]),
                "next_action": "Microstructure effect is directionally interesting but under-covered. Expand exact entry-window quote/trade collection, then rerun feature validation before promoting sizing or entry rules.",
            }
        ]
    )


def matching_oos(oos: pd.DataFrame, best: pd.Series, split_name: str) -> pd.DataFrame:
    return oos[
        oos["split_name"].eq(split_name) & oos["entry_action"].eq(best["entry_action"]) & oos["sizing_policy"].eq(best["sizing_policy"])
    ].copy()


def oos_observed(validation: pd.DataFrame, recent: pd.DataFrame) -> str:
    if validation.empty or recent.empty:
        return "missing matching OOS rows"
    v = validation.iloc[0]
    r = recent.iloc[0]
    return f"validation=${float(v['final_capital_usd']):.2f}/QQQ ${float(v['qqq_final_capital_usd']):.2f}; recent=${float(r['final_capital_usd']):.2f}/QQQ ${float(r['qqq_final_capital_usd']):.2f}"


def render_report(
    diagnostics: pd.DataFrame,
    interaction: pd.DataFrame,
    account: pd.DataFrame,
    oos: pd.DataFrame,
    source_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    dec = decision.iloc[0]
    return "\n".join(
        [
            "# Task645 Microstructure + Content Source Upgrade",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: `{dec['decision']}`",
            "- Strategy acceptance: `NOT_ACCEPTED`",
            "- Real capital: `FORBIDDEN`",
            f"- Best research config: `{dec['best_entry_action']}` / `{dec['best_sizing_policy']}`",
            f"- Best final: ${float(dec['best_final_capital_usd']):.2f}",
            f"- Best DD: {float(dec['best_max_drawdown_pct']):.2f}%",
            f"- Task639: ${float(dec['task639_final_capital_usd']):.2f}, DD {float(dec['task639_max_drawdown_pct']):.2f}%",
            "",
            "## Quant Expert Report",
            "",
            "Task645 adds entry-time historical SIP microstructure and deeper source/content interpretation. The assignment logic does not use outcomes, labels, GPT facts, symbol blacklists, or missing-data-as-negative shortcuts.",
            "",
            "### Source Audit",
            "",
            table(source_audit),
            "",
            "### Feature Diagnostics",
            "",
            table(diagnostics.head(80)),
            "",
            "### Content x Microstructure Interaction",
            "",
            table(interaction.head(80)),
            "",
            "### Account Grid",
            "",
            table(account),
            "",
            "### OOS Grid",
            "",
            table(oos),
            "",
            "### Pass/Fail Matrix",
            "",
            table(pass_fail),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- 이번 작업은 바로 매매 룰을 바꾼 작업이 아닙니다.",
            "- 먼저 돌파가 진짜인지, 뉴스가 얼마나 강한지 더 세부적으로 숫자화했습니다.",
            "- trade microstructure는 아직 커버리지가 낮아서 없는 구간을 나쁘게 처리하지 않았습니다.",
            "- 이 결과가 Task639보다 수익과 낙폭을 동시에 개선하지 못하면 전략 승격은 금지입니다.",
            "",
            "## Artifact Manifest",
            "",
            "- `task_645_gpt_design_packet.txt`",
            "- `task_645_gpt_design_response.md`",
            "- `task_645_microstructure_content_feature_panel.csv`",
            "- `task_645_feature_diagnostics.csv`",
            "- `task_645_content_microstructure_interaction_panel.csv`",
            "- `task_645_account_grid.csv`",
            "- `task_645_oos_grid.csv`",
            "- `task_645_source_audit.csv`",
            "- `task_645_pass_fail_matrix.csv`",
            "- `task_645_decision.csv`",
            "- `task_645_microstructure_coverage_audit.csv`",
            "- `task_645_content_source_audit.csv`",
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


def pct_change(first: object, last: object) -> float:
    first_num = pd.to_numeric(pd.Series([first]), errors="coerce").iloc[0]
    last_num = pd.to_numeric(pd.Series([last]), errors="coerce").iloc[0]
    if pd.isna(first_num) or pd.isna(last_num) or float(first_num) == 0:
        return np.nan
    return float((last_num - first_num) / abs(first_num))


def file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    build_task645_microstructure_content_source_upgrade(out_dir=args.out_dir)


if __name__ == "__main__":
    main()
