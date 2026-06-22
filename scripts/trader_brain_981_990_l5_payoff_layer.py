from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_SOURCE_DIR = ROOT / "data/raw/research/l5_payoff_layer"
OUT_DIR = ROOT / "data/artifacts/task_981_990_l5_payoff_layer"
RANKING_PATH = ROOT / "data/artifacts/task_961_970_external_audit_redesign/task969_shadow_trader_ranking.csv"
SPEC_PATH = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate/task929_controlled_trade_specs.csv"
DAILY_DIR = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay/canonical_daily"
BASELINE_TRADES_PATH = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay/task943_slot_capped_replay_trades.csv"
SHADOW_TRADES_PATH = ROOT / "data/artifacts/task_971_980_external_audit_shadow_replay/task975_replay_trades.csv"
SOURCE_DOWNLOAD_MANIFEST = RAW_SOURCE_DIR / "download_manifest.csv"

AUTHORITY = "REVIEW_ONLY_L5_PAYOFF_LAYER_NO_REPLAY"
FORBIDDEN_SELECTION_INPUTS = "future_return realized_return pnl post_entry_price_change outcome_rank exit_price"
STATUS = {
    "strategy_acceptance": "NOT_ACCEPTED",
    "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
}
LAYER_SOURCE_MAP = [
    {
        "layer_id": "L5-A",
        "layer_name": "reflectedness_variant_perception",
        "source_name": "morgan_stanley_probabilities_and_payoffs",
        "source_url": "https://www.morganstanley.com/im/publication/insights/articles/article_probabilitiesandpayoffs.pdf",
        "source_role": "price_value_gap_and_expected_value_context",
        "caution": "interpretation_only_not_a_price_target_or_buy_sell_signal",
    },
    {
        "layer_id": "L5-B",
        "layer_name": "payoff_shape_convexity",
        "source_name": "cfa_embrace_the_skew",
        "source_url": "https://rpc.cfainstitute.org/blogs/enterprising-investor/2024/unlocking-stock-market-success-why-you-should-embrace-the-skew",
        "source_role": "equity_return_asymmetry_context",
        "caution": "right_tail_potential_does_not_mean_positive_expected_return",
    },
    {
        "layer_id": "L5-B",
        "layer_name": "payoff_shape_convexity",
        "source_name": "bali_cakici_whitelaw_maxing_out_lottery_stocks",
        "source_url": "https://pages.stern.nyu.edu/~rwhitela/papers/max%20jfe11.pdf",
        "source_role": "lottery_like_extreme_return_caution",
        "caution": "lottery_like_features_can_be_overpriced_or_low_expected_return",
    },
    {
        "layer_id": "L5-C",
        "layer_name": "motion_timing",
        "source_name": "asness_moskowitz_pedersen_value_momentum_everywhere",
        "source_url": "https://pages.stern.nyu.edu/~lpederse/papers/ValMomEverywhere.pdf",
        "source_role": "value_and_momentum_timing_context",
        "caution": "momentum_is_not_independent_confirmation_and_can_crash",
    },
    {
        "layer_id": "L5-D",
        "layer_name": "best_expression_substitution",
        "source_name": "cfa_active_equity_portfolio_construction",
        "source_url": "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/active-equity-investing-portfolio-construction",
        "source_role": "security_selection_expression_and_implementation_context",
        "caution": "best_expression_is_not_approval_to_trade",
    },
    {
        "layer_id": "L5-E",
        "layer_name": "portfolio_construction_risk_budget",
        "source_name": "cfa_active_equity_portfolio_construction",
        "source_url": "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/active-equity-investing-portfolio-construction",
        "source_role": "position_sizing_risk_budget_liquidity_turnover_context",
        "caution": "risk_budget_is_not_alpha",
    },
    {
        "layer_id": "L5-V",
        "layer_name": "validation_false_discovery_guard",
        "source_name": "harvey_liu_zhu_cross_section_expected_returns",
        "source_url": "https://www.nber.org/system/files/working_papers/w20592/w20592.pdf",
        "source_role": "multiple_testing_and_false_discovery_context",
        "caution": "new_feature_count_requires_pre_registration_and_oos_testing",
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            {str(key).lstrip("\ufeff").strip('"'): value for key, value in row.items()}
            for row in reader
        ]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_daily(symbol: str) -> list[dict[str, object]]:
    path = DAILY_DIR / f"{symbol}.csv"
    if not path.exists():
        return []
    out: list[dict[str, object]] = []
    prev_close: float | None = None
    for row in read_csv(path):
        close = float(row["adj_close"])
        ret = None if prev_close in {None, 0.0} else close / float(prev_close) - 1.0
        out.append(
            {
                "date": row["timestamp"],
                "adj_close": close,
                "volume": float(row["volume"]),
                "dollar_volume": close * float(row["volume"]),
                "ret": ret,
            }
        )
        prev_close = close
    return out


def prior_rows(rows: list[dict[str, object]], entry_date: str) -> list[dict[str, object]]:
    return [row for row in rows if str(row["date"]) < entry_date]


def pct_return(rows: list[dict[str, object]], n: int) -> float | None:
    if len(rows) <= n:
        return None
    last = float(rows[-1]["adj_close"])
    start = float(rows[-1 - n]["adj_close"])
    if start == 0.0:
        return None
    return last / start - 1.0


def stdev(values: list[float]) -> float | None:
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return None
    mean = sum(vals) / len(vals)
    return math.sqrt(sum((v - mean) ** 2 for v in vals) / (len(vals) - 1))


def max_drawdown_prior(rows: list[dict[str, object]], n: int) -> float | None:
    if len(rows) < 2:
        return None
    sample = rows[-n:] if len(rows) >= n else rows
    peak = -math.inf
    dd = 0.0
    for row in sample:
        value = float(row["adj_close"])
        peak = max(peak, value)
        if peak > 0:
            dd = min(dd, value / peak - 1.0)
    return dd


def max_daily_return(rows: list[dict[str, object]], n: int) -> float | None:
    sample = rows[-n:] if len(rows) >= n else rows
    vals = [float(row["ret"]) for row in sample if row["ret"] is not None]
    return max(vals) if vals else None


def mean(values: list[float]) -> float | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def fmt(value: float | None) -> str:
    return "" if value is None else f"{value:.8f}"


def bucket_reflectedness(ret63: float | None, rel63: float | None, dist_high: float | None) -> str:
    if ret63 is None or rel63 is None or dist_high is None:
        return "insufficient_history"
    if ret63 > 0.25 and dist_high > -0.05:
        return "highly_reflected_momentum_proxy"
    if ret63 < -0.10 and rel63 < -0.05:
        return "under_pressure_reset_proxy"
    if rel63 > 0.10:
        return "positive_relative_motion_proxy"
    return "neutral_reflectedness_proxy"


def bucket_payoff(maxret63: float | None, vol63: float | None, dd63: float | None) -> str:
    if maxret63 is None or vol63 is None or dd63 is None:
        return "insufficient_history"
    if maxret63 > 0.15 and vol63 > 0.04 and dd63 < -0.20:
        return "right_tail_high_risk_proxy"
    if maxret63 > 0.10 and dd63 > -0.15:
        return "right_tail_contained_drawdown_proxy"
    if dd63 < -0.30:
        return "left_tail_or_broken_trend_proxy"
    return "linear_or_unclear_payoff_proxy"


def bucket_timing(ret21: float | None, ret63: float | None, reversal5: float | None) -> str:
    if ret21 is None or ret63 is None or reversal5 is None:
        return "insufficient_history"
    if ret21 > 0.08 and ret63 > 0.10 and reversal5 > -0.03:
        return "positive_motion_timing_proxy"
    if ret21 < -0.08 and ret63 > 0.05:
        return "pullback_after_positive_trend_proxy"
    if ret21 > 0.15 and reversal5 > 0.05:
        return "possibly_extended_timing_proxy"
    return "neutral_timing_proxy"


def rank_within(groups: dict[tuple[str, str], list[dict[str, object]]], key_name: str) -> dict[str, int]:
    ranks: dict[str, int] = {}
    for group in groups.values():
        ordered = sorted(
            group,
            key=lambda row: (
                -(float(row[key_name]) if row[key_name] not in {"", None} else -999999.0),
                str(row["symbol"]),
                str(row["trade_spec_id"]),
            ),
        )
        for idx, row in enumerate(ordered, start=1):
            ranks[str(row["trade_spec_id"])] = idx
    return ranks


def build() -> dict[str, object]:
    ranking = sorted(read_csv(RANKING_PATH), key=lambda row: (row["decision_asof_ts"], row["entry_date"], row["trade_spec_id"]))
    specs = {row["trade_spec_id"]: row for row in read_csv(SPEC_PATH)}
    qqq_daily = load_daily("QQQ")
    daily_cache: dict[str, list[dict[str, object]]] = {}
    base_trades = {row["trade_spec_id"]: row for row in read_csv(BASELINE_TRADES_PATH) if row.get("slot_cap") == "10"}
    shadow_trades = {row["trade_spec_id"]: row for row in read_csv(SHADOW_TRADES_PATH)}
    download_manifest = {row["source_name"]: row for row in read_csv(SOURCE_DOWNLOAD_MANIFEST)} if SOURCE_DOWNLOAD_MANIFEST.exists() else {}

    source_rows = []
    for src in LAYER_SOURCE_MAP:
        local = next((row for name, row in download_manifest.items() if name.startswith(src["source_name"].split("_")[0]) or src["source_name"] in name), None)
        local_path = local["local_path"] if local else ""
        source_rows.append(
            {
                **src,
                "download_state": local["download_state"] if local else "not_downloaded_or_web_context_only",
                "local_path": local_path,
                "local_sha256": sha256(ROOT / local_path) if local_path else "",
                "use_mode": "research_context_only_not_source_of_trade_truth",
                "authority": AUTHORITY,
            }
        )

    layer_contract = [
        {
            "task_id": "Task981",
            "layer_id": "L5-source",
            "completion_goal": "source_context_downloaded_or_recorded_with_citations_and_cautions",
            "output_file": "task981_l5_source_context_manifest.csv",
            "perfect_done_condition": "every L5 layer has at least one source context row and explicit caution with no_replay",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task982",
            "layer_id": "L5-contract",
            "completion_goal": "define allowed inputs forbidden inputs and no-replay boundary",
            "output_file": "task982_l5_layer_contract.csv",
            "perfect_done_condition": "each layer has question allowed fields forbidden fields completion state and no_replay boundary",
            "authority": AUTHORITY,
        },
    ]
    for layer_id, question in [
        ("L5-A", "is_the_thesis_already_reflected_or_still_variant"),
        ("L5-B", "what_is_the_ex_ante_payoff_shape_and_tail_risk"),
        ("L5-C", "why_now_and_is_motion_supportive_or_extended"),
        ("L5-D", "is_this_the_best_expression_inside_theme_cohort"),
        ("L5-E", "does_this_consume_portfolio_risk_budget_wisely"),
        ("L5-V", "can_this_feature_survive_pre_registration_and_no_leakage_checks"),
    ]:
        layer_contract.append(
            {
                "task_id": f"Task98{len(layer_contract)+1}",
                "layer_id": layer_id,
                "completion_goal": question,
                "output_file": f"task98x_{layer_id.lower().replace('-', '_')}_panel.csv",
                "perfect_done_condition": "feature_only_no_replay_no_future_outcome_selection_input",
                "authority": AUTHORITY,
            }
        )

    base_features: list[dict[str, object]] = []
    for row in ranking:
        symbol = row["symbol"]
        if symbol not in daily_cache:
            daily_cache[symbol] = load_daily(symbol)
        prior = prior_rows(daily_cache[symbol], row["entry_date"])
        qqq_prior = prior_rows(qqq_daily, row["entry_date"])
        ret5 = pct_return(prior, 5)
        ret21 = pct_return(prior, 21)
        ret63 = pct_return(prior, 63)
        ret126 = pct_return(prior, 126)
        qqq63 = pct_return(qqq_prior, 63)
        rel63 = None if ret63 is None or qqq63 is None else ret63 - qqq63
        returns21 = [float(item["ret"]) for item in prior[-21:] if item["ret"] is not None]
        returns63 = [float(item["ret"]) for item in prior[-63:] if item["ret"] is not None]
        vol21 = stdev(returns21)
        vol63 = stdev(returns63)
        dd63 = max_drawdown_prior(prior, 63)
        maxret21 = max_daily_return(prior, 21)
        maxret63 = max_daily_return(prior, 63)
        high252 = max([float(item["adj_close"]) for item in prior[-252:]], default=None)
        last_close = float(prior[-1]["adj_close"]) if prior else None
        dist_high = None if not prior or not high252 or high252 == 0 else (last_close / high252 - 1.0)
        dollar20 = mean([float(item["dollar_volume"]) for item in prior[-20:]])
        volume20 = [float(item["volume"]) for item in prior[-20:]]
        vol_mean20 = mean(volume20)
        vol_std20 = stdev(volume20)
        volume_z = None if not prior or vol_mean20 is None or not vol_std20 or vol_std20 == 0 else (float(prior[-1]["volume"]) - vol_mean20) / vol_std20
        base_features.append(
            {
                **row,
                "candidate_bundle_id": specs.get(row["trade_spec_id"], {}).get("candidate_bundle_id", ""),
                "adapter_input_id": specs.get(row["trade_spec_id"], {}).get("adapter_input_id", ""),
                "source_graph_id": specs.get(row["trade_spec_id"], {}).get("source_graph_id", ""),
                "side": specs.get(row["trade_spec_id"], {}).get("side", ""),
                "last_price_date_before_entry": prior[-1]["date"] if prior else "",
                "max_price_timestamp_used": prior[-1]["date"] if prior else "",
                "lookback_rows": len(prior),
                "price_coverage_state": "pass" if len(prior) >= 63 else "insufficient_history",
                "ret_5d_prior": ret5,
                "ret_21d_prior": ret21,
                "ret_63d_prior": ret63,
                "ret_126d_prior": ret126,
                "qqq_ret_63d_prior": qqq63,
                "relative_strength_vs_qqq_63d_prior": rel63,
                "vol_21d_prior": vol21,
                "vol_63d_prior": vol63,
                "drawdown_63d_prior": dd63,
                "max_daily_return_21d_prior": maxret21,
                "max_daily_return_63d_prior": maxret63,
                "distance_to_252d_high_prior": dist_high,
                "avg_dollar_volume_20d_prior": dollar20,
                "volume_z_20d_prior": volume_z,
            }
        )

    group_by_entry_theme: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in base_features:
        group_by_entry_theme[(str(row["entry_date"]), str(row["theme"]))].append(row)
    expression_rank_by_rel = rank_within(group_by_entry_theme, "relative_strength_vs_qqq_63d_prior")
    expression_rank_by_liquidity = rank_within(group_by_entry_theme, "avg_dollar_volume_20d_prior")

    reflectedness_rows = []
    payoff_rows = []
    timing_rows = []
    expression_rows = []
    risk_rows = []
    validation_rows = []
    selected_by_entry = defaultdict(list)
    cluster_counts_by_entry = defaultdict(int)
    theme_counts_by_entry = defaultdict(int)
    for row in base_features:
        if row["shadow_slot10_selected"] == "1":
            selected_by_entry[str(row["entry_date"])].append(row)
            cluster_counts_by_entry[(str(row["entry_date"]), str(row["thesis_cluster_key"]))] += 1
            theme_counts_by_entry[(str(row["entry_date"]), str(row["theme"]))] += 1

    for row in base_features:
        ret63 = row["ret_63d_prior"]
        rel63 = row["relative_strength_vs_qqq_63d_prior"]
        dist_high = row["distance_to_252d_high_prior"]
        maxret63 = row["max_daily_return_63d_prior"]
        vol63 = row["vol_63d_prior"]
        dd63 = row["drawdown_63d_prior"]
        timing_state = bucket_timing(row["ret_21d_prior"], row["ret_63d_prior"], row["ret_5d_prior"])
        reflectedness_rows.append(
            {
                "trade_spec_id": row["trade_spec_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "entry_date": row["entry_date"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "last_price_date_before_entry": row["last_price_date_before_entry"],
                "ret_21d_prior": fmt(row["ret_21d_prior"]),
                "ret_63d_prior": fmt(ret63),
                "relative_strength_vs_qqq_63d_prior": fmt(rel63),
                "distance_to_252d_high_prior": fmt(dist_high),
                "reflectedness_bucket": bucket_reflectedness(ret63, rel63, dist_high),
                "use_mode": "diagnostic_feature_only",
                "forbidden_inputs": FORBIDDEN_SELECTION_INPUTS,
                "authority": AUTHORITY,
            }
        )
        payoff_rows.append(
            {
                "trade_spec_id": row["trade_spec_id"],
                "entry_date": row["entry_date"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "max_daily_return_21d_prior": fmt(row["max_daily_return_21d_prior"]),
                "max_daily_return_63d_prior": fmt(maxret63),
                "vol_21d_prior": fmt(row["vol_21d_prior"]),
                "vol_63d_prior": fmt(vol63),
                "drawdown_63d_prior": fmt(dd63),
                "payoff_shape_bucket": bucket_payoff(maxret63, vol63, dd63),
                "lottery_like_caution": "1" if maxret63 is not None and maxret63 > 0.15 else "0",
                "use_mode": "diagnostic_feature_only_not_expected_return_claim",
                "forbidden_inputs": FORBIDDEN_SELECTION_INPUTS,
                "authority": AUTHORITY,
            }
        )
        timing_rows.append(
            {
                "trade_spec_id": row["trade_spec_id"],
                "entry_date": row["entry_date"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "ret_5d_prior": fmt(row["ret_5d_prior"]),
                "ret_21d_prior": fmt(row["ret_21d_prior"]),
                "ret_63d_prior": fmt(row["ret_63d_prior"]),
                "trend_acceleration_proxy": fmt(None if row["ret_21d_prior"] is None or row["ret_63d_prior"] is None else row["ret_21d_prior"] - row["ret_63d_prior"] / 3.0),
                "volume_z_20d_prior": fmt(row["volume_z_20d_prior"]),
                "timing_state": timing_state,
                "use_mode": "diagnostic_feature_only",
                "forbidden_inputs": FORBIDDEN_SELECTION_INPUTS,
                "authority": AUTHORITY,
            }
        )
        rel_rank = expression_rank_by_rel.get(str(row["trade_spec_id"]), 0)
        liq_rank = expression_rank_by_liquidity.get(str(row["trade_spec_id"]), 0)
        expression_rows.append(
            {
                "trade_spec_id": row["trade_spec_id"],
                "entry_date": row["entry_date"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "expression_rank_by_relative_strength_in_theme": rel_rank,
                "expression_rank_by_liquidity_in_theme": liq_rank,
                "avg_dollar_volume_20d_prior": fmt(row["avg_dollar_volume_20d_prior"]),
                "best_expression_proxy_state": "theme_leader_proxy" if rel_rank == 1 else "theme_alternative_proxy",
                "liquidity_state": "liquid_proxy" if row["avg_dollar_volume_20d_prior"] is not None and row["avg_dollar_volume_20d_prior"] > 10_000_000 else "liquidity_review_needed",
                "instrument_scope": "common_equity_only",
                "use_mode": "diagnostic_feature_only",
                "forbidden_inputs": FORBIDDEN_SELECTION_INPUTS,
                "authority": AUTHORITY,
            }
        )
        selected_theme_count = theme_counts_by_entry[(str(row["entry_date"]), str(row["theme"]))]
        selected_cluster_count = cluster_counts_by_entry[(str(row["entry_date"]), str(row["thesis_cluster_key"]))]
        risk_rows.append(
            {
                "trade_spec_id": row["trade_spec_id"],
                "entry_date": row["entry_date"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "shadow_slot10_selected": row["shadow_slot10_selected"],
                "selected_theme_count_entry_date": selected_theme_count,
                "selected_cluster_count_entry_date": selected_cluster_count,
                "vol_63d_prior": fmt(row["vol_63d_prior"]),
                "drawdown_63d_prior": fmt(row["drawdown_63d_prior"]),
                "avg_dollar_volume_20d_prior": fmt(row["avg_dollar_volume_20d_prior"]),
                "risk_budget_proxy_state": "crowded_theme_review" if selected_theme_count >= 5 and row["shadow_slot10_selected"] == "1" else "normal_review",
                "use_mode": "diagnostic_feature_only_not_position_size",
                "forbidden_inputs": FORBIDDEN_SELECTION_INPUTS,
                "authority": AUTHORITY,
            }
        )
        validation_rows.append(
            {
                "trade_spec_id": row["trade_spec_id"],
                "entry_date": row["entry_date"],
                "symbol": row["symbol"],
                "max_price_timestamp_used": row["max_price_timestamp_used"],
                "feature_time_state": "pass" if row["max_price_timestamp_used"] and str(row["max_price_timestamp_used"]) < str(row["entry_date"]) else "insufficient_history_or_block",
                "price_coverage_state": row["price_coverage_state"],
                "row_count_matches_task969": "1",
                "selection_use_allowed": "0",
                "replay_executed": "0",
                "forbidden_inputs": FORBIDDEN_SELECTION_INPUTS,
                "authority": AUTHORITY,
            }
        )

    # Evaluation-only gap diagnostic. This file can mention realized PnL, but it is blocked from assignment logic.
    baseline_ids = set(base_trades)
    shadow_ids = set(shadow_trades)
    gap_rows = []
    for side, ids_set, source in [
        ("baseline_only", baseline_ids - shadow_ids, base_trades),
        ("shadow_only", shadow_ids - baseline_ids, shadow_trades),
    ]:
        for trade_spec_id in sorted(ids_set):
            trade = source[trade_spec_id]
            gap_rows.append(
                {
                    "trade_spec_id": trade_spec_id,
                    "gap_side": side,
                    "symbol": trade["symbol"],
                    "theme": trade["theme"],
                    "evaluation_only_pnl": trade["pnl"],
                    "evaluation_only_return_pct": trade["return_pct"],
                    "evaluation_use_mode": "post_replay_failure_decomposition_only_never_selection_input",
                    "authority": AUTHORITY,
                }
            )

    closeout = {
        "task_id": "Task981-990",
        "verdict": "l5_payoff_layer_feature_only_complete_no_replay",
        "input_ranking_rows": len(ranking),
        "l5_feature_rows": len(base_features),
        "source_context_rows": len(source_rows),
        "gap_diagnostic_rows": len(gap_rows),
        "replay_executed": "0",
        "next_action": "review_l5_panels_then_pre_register_one_policy_before_any_replay",
        **STATUS,
        "authority": AUTHORITY,
    }

    write_csv(OUT_DIR / "task981_l5_source_context_manifest.csv", source_rows, [
        "layer_id", "layer_name", "source_name", "source_url", "source_role", "caution",
        "download_state", "local_path", "local_sha256", "use_mode", "authority",
    ])
    write_csv(OUT_DIR / "task982_l5_layer_contract.csv", layer_contract, [
        "task_id", "layer_id", "completion_goal", "output_file", "perfect_done_condition", "authority",
    ])
    write_csv(OUT_DIR / "task983_l5a_reflectedness_panel.csv", reflectedness_rows, [
        "trade_spec_id", "decision_asof_ts", "entry_date", "symbol", "theme", "last_price_date_before_entry",
        "ret_21d_prior", "ret_63d_prior", "relative_strength_vs_qqq_63d_prior",
        "distance_to_252d_high_prior", "reflectedness_bucket", "use_mode", "forbidden_inputs", "authority",
    ])
    write_csv(OUT_DIR / "task984_l5b_payoff_shape_panel.csv", payoff_rows, [
        "trade_spec_id", "entry_date", "symbol", "theme", "max_daily_return_21d_prior",
        "max_daily_return_63d_prior", "vol_21d_prior", "vol_63d_prior", "drawdown_63d_prior",
        "payoff_shape_bucket", "lottery_like_caution", "use_mode", "forbidden_inputs", "authority",
    ])
    write_csv(OUT_DIR / "task985_l5c_motion_timing_panel.csv", timing_rows, [
        "trade_spec_id", "entry_date", "symbol", "theme", "ret_5d_prior", "ret_21d_prior",
        "ret_63d_prior", "trend_acceleration_proxy", "volume_z_20d_prior", "timing_state",
        "use_mode", "forbidden_inputs", "authority",
    ])
    write_csv(OUT_DIR / "task986_l5d_best_expression_panel.csv", expression_rows, [
        "trade_spec_id", "entry_date", "symbol", "theme", "expression_rank_by_relative_strength_in_theme",
        "expression_rank_by_liquidity_in_theme", "avg_dollar_volume_20d_prior", "best_expression_proxy_state",
        "liquidity_state", "instrument_scope", "use_mode", "forbidden_inputs", "authority",
    ])
    write_csv(OUT_DIR / "task987_l5e_portfolio_risk_budget_panel.csv", risk_rows, [
        "trade_spec_id", "entry_date", "symbol", "theme", "shadow_slot10_selected",
        "selected_theme_count_entry_date", "selected_cluster_count_entry_date", "vol_63d_prior",
        "drawdown_63d_prior", "avg_dollar_volume_20d_prior", "risk_budget_proxy_state",
        "use_mode", "forbidden_inputs", "authority",
    ])
    write_csv(OUT_DIR / "task988_l5v_validation_guard_panel.csv", validation_rows, [
        "trade_spec_id", "entry_date", "symbol", "max_price_timestamp_used", "feature_time_state",
        "price_coverage_state", "row_count_matches_task969", "selection_use_allowed", "replay_executed",
        "forbidden_inputs", "authority",
    ])
    write_csv(OUT_DIR / "task989_baseline_shadow_gap_evaluation_only.csv", gap_rows, [
        "trade_spec_id", "gap_side", "symbol", "theme", "evaluation_only_pnl",
        "evaluation_only_return_pct", "evaluation_use_mode", "authority",
    ])
    write_csv(OUT_DIR / "task990_l5_payoff_layer_closeout.csv", [closeout], list(closeout.keys()))
    write_csv(OUT_DIR / "task981_990_summary.csv", [closeout], list(closeout.keys()))
    (OUT_DIR / "task981_990_summary.json").write_text(json.dumps(closeout, indent=2), encoding="utf-8")
    return closeout


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_981_990_L5_PAYOFF_LAYER_OK] "
        f"rows={summary['l5_feature_rows']} sources={summary['source_context_rows']} replay={summary['replay_executed']}"
    )


if __name__ == "__main__":
    main()
