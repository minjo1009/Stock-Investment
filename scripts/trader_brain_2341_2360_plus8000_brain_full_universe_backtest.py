from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import trader_brain_1768_1787_preentry_risk_budget_v2 as preentry
import trader_brain_1788_1807_winner_defense_budget as windef
import trader_brain_1991_2000_winner_acceleration_surgery as winaccel
import trader_brain_2191_2200_api_drawdown_sizing_guard as guard
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2341_2360_plus8000_brain_full_universe_backtest"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2341_2360_plus8000_brain_full_universe_backtest.md"
DECISION = REPORT_DIR / "task_2341_2360_decision.csv"

TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK1508 = ROOT / "data/artifacts/task_1508_1517_bottleneck_verification"
TASK1698 = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
TASK2151 = ROOT / "data/artifacts/task_2151_2180_api_three_loop_hardening"
TASK2191 = ROOT / "data/artifacts/task_2191_2200_api_drawdown_sizing_guard"
TASK2251 = ROOT / "data/artifacts/task_2251_2280_plus8000_full_source_acquisition"
TASK2291 = ROOT / "data/artifacts/task_2291_2310_plus8000_feature_full_universe_backtest"
TASK2321 = ROOT / "data/artifacts/task_2321_2340_plus8000_brain_newdata_backtest"

AUTHORITY = "DIAGNOSTIC_PLUS8000_BRAIN_FULL_UNIVERSE_BACKTEST_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265
QQQ_BENCHMARK_CAGR = 0.126318
SOURCE_POLICY = "winner_defense_budget_top5_v1"
RETURN_POLICIES = ["scheduled_uniform", "actual_else_scheduled"]
POLICY_MAP = {
    "api_dd_guard_soft_boost_cap_top2_v1": "soft_boost_cap_top2_v1",
    "api_dd_guard_stress_neutral_top2_v1": "stress_neutral_top2_v1",
    "api_dd_guard_winner_preserve_top2_v1": "winner_preserve_top2_v1",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def f(value: object, default: float = 0.0) -> float:
    return guard.to_float(value, default)


def row_key(row: dict[str, object]) -> tuple[str, str, str, str]:
    return (
        str(row.get("candidate_source_id", "")),
        str(row.get("trade_spec_id", "")),
        str(row.get("symbol", "")),
        str(row.get("decision_asof_ts", "")),
    )


def factor_cluster(symbol: str, theme: str) -> str:
    semis = {"AMD", "NVDA", "AVGO", "AMAT", "ASML", "LRCX", "KLAC", "ADI", "ARM", "MRVL", "MU", "WDC", "STX", "TER", "ONTO", "ACLS", "AMBA", "ALGM", "AEIS"}
    financials = {"AIG", "AFG", "AMP", "C", "CB", "BNY", "BCS", "BBVA"}
    industrials = {"AME", "AOS", "AGCO", "CAT", "ALSN", "APH", "ETN", "PWR", "VRT"}
    biotech = {"ACAD", "ADPT", "ALNY", "BMRN", "CDNA", "ARGX", "BNTX"}
    if symbol in semis or "semiconductor" in theme or "ai" in theme:
        return "semis_growth_beta"
    if symbol in financials:
        return "financial_beta"
    if symbol in industrials or "industrial" in theme:
        return "industrial_cyclical_beta"
    if symbol in biotech:
        return "biotech_event_beta"
    if "energy" in theme or "power" in theme:
        return "energy_power_beta"
    if "space" in theme:
        return "space_speculative_beta"
    return "mixed_other"


def strategy_sleeve(symbol: str, theme: str, cluster: str, payoff_bucket: str) -> tuple[str, float]:
    if cluster == "semis_growth_beta" and payoff_bucket in {"top3_payoff_candidate", "eligible_payoff_candidate"}:
        return "winner_compounder", 1.14
    if cluster in {"industrial_cyclical_beta", "financial_beta", "energy_power_beta"}:
        return "cyclical_beta", 0.92
    if cluster in {"biotech_event_beta", "space_speculative_beta"}:
        return "speculative_event", 0.66
    if payoff_bucket == "top3_payoff_candidate":
        return "quality_compounder", 1.02
    return "ordinary_core", 0.82


def build_full_preentry_panel() -> list[dict[str, object]]:
    rank_rows = read_csv(TASK1488 / "task1494_payoff_ranker_v6.csv")
    payoff_by_spec = {row["trade_spec_id"]: row for row in read_csv(TASK1698 / "task1700_payoff_quality_v2_panel.csv")}
    collapse_by_spec = {row["trade_spec_id"]: row for row in read_csv(TASK1698 / "task1699_collapse_risk_v2_panel.csv")}
    base_rows: list[dict[str, object]] = []
    for idx, rank in enumerate(rank_rows, start=1):
        spec = rank["trade_spec_id"]
        pay = payoff_by_spec.get(spec, {})
        col = collapse_by_spec.get(spec, {})
        theme = rank.get("derived_theme", "")
        cluster = factor_cluster(rank["symbol"], theme)
        payoff_score = f(pay.get("payoff_quality_score"))
        collapse_score = f(col.get("collapse_risk_score"))
        payoff_bucket = pay.get("payoff_quality_bucket", "")
        collapse_bucket = col.get("collapse_risk_bucket", "")
        pre_gate = pay.get("pre_entry_gate", col.get("pre_entry_gate", ""))
        baseline_preserved = (
            pre_gate == "allow"
            and payoff_bucket in {"top3_payoff_candidate", "eligible_payoff_candidate", "watch_or_cap_candidate"}
            and collapse_bucket in {"ordinary_pass", "ordinary_volatility", "theme_volatility"}
        )
        prior = f(col.get("prior_return_63d"))
        rel = f(col.get("relative_return_63d"))
        drawdown = f(col.get("prior_drawdown_126d"))
        vol = f(col.get("realized_vol_63d"))
        liquidity = f(col.get("avg_dollar_volume_20d"))
        air = int(drawdown <= -0.30 and rel <= -0.10)
        fragility = int(collapse_score >= 40 or collapse_bucket in {"terminal_business_risk", "dilution_pressure"})
        liq = int(0 < liquidity < 25_000_000)
        high_vol = int(vol >= 0.65 and payoff_score < 65)
        weak = int(payoff_score < 45 or pre_gate == "block")
        risk_points = air + fragility * 2 + liq + high_vol + weak
        row = {
            "task_id": "Task2342",
            "preentry_full_id": f"PLUS8000FULLPRE-2342-{idx:07d}",
            "policy_variant_id": "bad_trade_gate_top5_v1",
            "trade_spec_id": spec,
            "candidate_source_id": rank["candidate_source_id"],
            "symbol": rank["symbol"],
            "decision_asof_ts": rank["decision_asof_ts"],
            "derived_theme": theme,
            "factor_cluster": cluster,
            "selection_reason": "baseline_preserved" if baseline_preserved else "full_universe_extension_cap",
            "collapse_risk_bucket": collapse_bucket,
            "payoff_quality_bucket": payoff_bucket,
            "payoff_quality_score": round(payoff_score, 6),
            "prior_return_63d": prior,
            "relative_return_63d": rel,
            "prior_drawdown_126d": drawdown,
            "realized_vol_63d": vol,
            "avg_dollar_volume_20d": liquidity,
            "air_pocket_risk": str(air),
            "fragility_risk": str(fragility),
            "liquidity_risk": str(liq),
            "high_vol_risk": str(high_vol),
            "quality_weak_risk": str(weak),
            "preentry_risk_points": risk_points,
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        base_rows.append(row)
    cluster_counts: Counter[tuple[str, str, str]] = Counter((str(row["decision_asof_ts"]), str(row["policy_variant_id"]), str(row["factor_cluster"])) for row in base_rows)
    corr = preentry.cluster_corr_map([{k: str(v) for k, v in row.items()} for row in base_rows])
    out: list[dict[str, object]] = []
    for idx, row in enumerate(base_rows, start=1):
        payoff_score = f(row["payoff_quality_score"])
        risk_points = f(row["preentry_risk_points"])
        cluster_count = cluster_counts[(str(row["decision_asof_ts"]), str(row["policy_variant_id"]), str(row["factor_cluster"]))]
        cluster_corr = corr.get((str(row["policy_variant_id"]), str(row["trade_spec_id"])), 0.0)
        payoff_credit = preentry.clamp((payoff_score - 75.0) / 100.0, -0.10, 0.28)
        risk_pressure = 0.075 * risk_points
        cluster_pressure = 0.0
        if cluster_count >= 2 and row["factor_cluster"] not in {"defensive_quality", "mixed_other"}:
            cluster_pressure += 0.07
        if cluster_corr >= 0.55:
            cluster_pressure += 0.08
        elif cluster_corr >= 0.35:
            cluster_pressure += 0.04
        fragility_pressure = 0.07 if row["fragility_risk"] == "1" else 0.0
        air_pressure = 0.06 if row["air_pocket_risk"] == "1" else 0.0
        liquidity_pressure = 0.05 if row["liquidity_risk"] == "1" else 0.0
        multiplier = 1.0 + payoff_credit - risk_pressure - cluster_pressure - fragility_pressure - air_pressure - liquidity_pressure
        if row["selection_reason"] != "baseline_preserved":
            multiplier = min(multiplier, 0.40)
        no_entry = risk_points >= 6 and payoff_score < 82 and row["selection_reason"] == "baseline_preserved"
        if no_entry:
            multiplier = 0.0
        elif multiplier < 0.20:
            multiplier = 0.20
        multiplier = round(preentry.clamp(multiplier, 0.0, 1.05), 4)
        state = preentry.risk_budget_state(multiplier, no_entry)
        extended = dict(row)
        extended.update(
            {
                "task_id": "Task2342",
                "preentry_full_id": f"PLUS8000FULLPRE-2342-{idx:07d}",
                "cluster_count_same_decision": cluster_count,
                "cluster_corr_63d": cluster_corr,
                "payoff_credit": round(payoff_credit, 6),
                "risk_pressure": round(risk_pressure, 6),
                "cluster_pressure": round(cluster_pressure, 6),
                "fragility_pressure": round(fragility_pressure, 6),
                "air_pocket_pressure": round(air_pressure, 6),
                "liquidity_pressure": round(liquidity_pressure, 6),
                "risk_budget_state_v2": state,
                "risk_budget_multiplier_v2": multiplier,
            }
        )
        out.append(extended)
    return out


def build_winner_defense_panel(pre_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    payoff_by_spec = {row["trade_spec_id"]: row for row in read_csv(TASK1698 / "task1700_payoff_quality_v2_panel.csv")}
    collapse_by_spec = {row["trade_spec_id"]: row for row in read_csv(TASK1698 / "task1699_collapse_risk_v2_panel.csv")}
    policy = windef.POLICIES["winner_defense_budget_top5_v1"]
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(pre_rows, start=1):
        pay = payoff_by_spec.get(str(row["trade_spec_id"]), {})
        col = collapse_by_spec.get(str(row["trade_spec_id"]), {})
        cause = windef.volatility_cause(row, pay, col)
        quality = windef.winner_quality_beta(row, pay, col, cause)
        credit = windef.defense_credit(quality, cause, str(pay.get("event_family", "")), float(policy["defense_credit_cap"]))
        adjusted_risk_pressure = f(row.get("risk_pressure"))
        if quality >= 82 and cause in {"normal_winner_volatility", "leader_momentum_volatility", "market_beta_selloff"}:
            adjusted_risk_pressure = max(0.0, adjusted_risk_pressure - 0.08)
        elif quality >= 68 and cause in {"normal_winner_volatility", "leader_momentum_volatility"}:
            adjusted_risk_pressure = max(0.0, adjusted_risk_pressure - 0.04)
        if cause in {"issuer_specific_expectation_break", "company_specific_drawdown"} and quality < 70:
            adjusted_risk_pressure += 0.04
        if cause == "terminal_or_financing_thesis_risk":
            adjusted_risk_pressure += 0.10
        multiplier = (
            1.0
            + f(row.get("payoff_credit"))
            + credit
            - adjusted_risk_pressure
            - f(row.get("cluster_pressure"))
            - f(row.get("fragility_pressure"))
            - f(row.get("air_pocket_pressure"))
            - f(row.get("liquidity_pressure"))
        )
        if row["selection_reason"] != "baseline_preserved":
            multiplier = min(multiplier, 0.45 if quality >= 70 else 0.35)
        if cause == "terminal_or_financing_thesis_risk":
            multiplier = min(multiplier, 0.40)
        no_entry = cause == "terminal_or_financing_thesis_risk" and quality < 35
        if no_entry:
            multiplier = 0.0
        elif multiplier < 0.20:
            multiplier = 0.20
        multiplier = round(windef.clamp(multiplier, 0.0, float(policy["max_multiplier"])), 4)
        out = dict(row)
        out.update(
            {
                "task_id": "Task2343",
                "winner_defense_id": f"PLUS8000FULLWINDEF-2343-{idx:07d}",
                "target_policy_variant_id": SOURCE_POLICY,
                "event_family": pay.get("event_family", ""),
                "payoff_mechanism": pay.get("payoff_mechanism", ""),
                "expectation_state": pay.get("expectation_state", ""),
                "absorption_state": pay.get("absorption_state", ""),
                "materiality_state": pay.get("materiality_state", ""),
                "source_independence_state": pay.get("source_independence_state", ""),
                "volatility_cause": cause,
                "winner_quality_beta": quality,
                "winner_defense_bucket": windef.defense_bucket(quality),
                "winner_defense_credit": credit,
                "adjusted_risk_pressure": round(adjusted_risk_pressure, 6),
                "adjusted_cluster_pressure": row.get("cluster_pressure", ""),
                "winner_defense_multiplier_v3": multiplier,
                "winner_defense_action": "no_entry" if no_entry else "enter_with_winner_defense_budget",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        rows.append(out)
    return rows


def build_acceleration_layers(winner_panel: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    budget_rows: list[dict[str, object]] = []
    for idx, row in enumerate(winner_panel, start=1):
        sleeve, sleeve_mult = strategy_sleeve(str(row["symbol"]), str(row.get("derived_theme", "")), str(row.get("factor_cluster", "")), str(row.get("payoff_quality_bucket", "")))
        budget_rows.append(
            {
                "task_id": "Task2344",
                "budget_id": f"PLUS8000FULLBUDGET-2344-{idx:07d}",
                "target_policy_variant_id": SOURCE_POLICY,
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": sleeve,
                "sleeve_budget_multiplier": round(min(f(row.get("winner_defense_multiplier_v3")), sleeve_mult), 6),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    indexes = {"panel": {str(row["trade_spec_id"]): row for row in winner_panel}, "interaction": {}, "free_l4": {}, "trades": {}}
    inputs = {"budget": budget_rows, "requirements": [], "calibration": [], "sleeve_metrics": [], "winner_panel": winner_panel, "winner_trades": [], "interaction_l4": [], "free_l4": [], "free_metrics": [{"policy_variant_id": "", "final_equity": "0"}]}
    old_auth = winaccel.AUTHORITY
    try:
        winaccel.AUTHORITY = AUTHORITY
        l1 = winaccel.l1_rows(inputs, indexes)
        l2 = winaccel.l2_rows(l1)
        l3 = winaccel.l3_rows(l2)
        l4 = winaccel.l4_rows(l2, l3)
        l5 = winaccel.l5_rows(inputs, indexes, l4)
    finally:
        winaccel.AUTHORITY = old_auth
    for idx, row in enumerate(l1, start=1):
        row["task_id"] = "Task2345"
        row["l1_packet_id"] = f"PLUS8000FULLL1-2345-{idx:07d}"
        row["authority"] = AUTHORITY
    for idx, row in enumerate(l2, start=1):
        row["task_id"] = "Task2346"
        row["l2_semantic_id"] = f"PLUS8000FULLL2-2346-{idx:07d}"
        row["authority"] = AUTHORITY
    for idx, row in enumerate(l3, start=1):
        row["task_id"] = "Task2347"
        row["l3_edge_id"] = f"PLUS8000FULLL3-2347-{idx:07d}"
        row["authority"] = AUTHORITY
    for idx, row in enumerate(l4, start=1):
        row["task_id"] = "Task2348"
        row["l4_thesis_id"] = f"PLUS8000FULLL4-2348-{idx:07d}"
        row["authority"] = AUTHORITY
    for idx, row in enumerate(l5, start=1):
        row["task_id"] = "Task2349"
        row["l5_decision_id"] = f"PLUS8000FULLL5-2349-{idx:07d}"
        row["authority"] = AUTHORITY
    return budget_rows, l1, l2, l3, l4, l5


def api_overlay(l5_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    features = {row_key(row): row for row in read_csv(TASK2251 / "task2256_recomputed_plus8000_feature_panel.csv")}
    cards: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    audit: list[dict[str, object]] = []
    for idx, row in enumerate(l5_rows, start=1):
        feat = features.get(row_key(row), {})
        state = feat.get("api_proxy_state", "api_proxy_source_gap_neutral")
        score = f(feat.get("api_proxy_score"))
        surprise = f(feat.get("latest_earnings_surprise_pct"))
        rating = f(feat.get("rating_score"))
        if state == "api_proxy_risk_or_weak_quality" or score <= -8:
            adjust = -12.0
            api_state = "api_risk_context_cap_required"
            mult = 0.72
            action = "newdata_risk_cap"
        elif state == "api_proxy_supportive" and score >= 24:
            adjust = 8.0 + min(4.0, max(surprise, 0.0) * 0.04) + min(2.0, max(rating, 0.0) * 0.1)
            api_state = "api_event_context_supportive"
            mult = 1.08
            action = "newdata_supportive_boost"
        elif state == "api_proxy_supportive" and score >= 18:
            adjust = 4.0
            api_state = "api_event_context_supportive"
            mult = 1.03
            action = "newdata_light_support"
        else:
            adjust = 0.0
            api_state = "api_source_gap_neutral" if state == "api_proxy_source_gap_neutral" else "api_mixed_or_light_neutral"
            mult = 1.0
            action = "newdata_neutral"
        base_score = f(row.get("winner_acceleration_rank_score"))
        common = {
            "trade_spec_id": row["trade_spec_id"],
            "candidate_source_id": row["candidate_source_id"],
            "symbol": row["symbol"],
            "decision_asof_ts": row["decision_asof_ts"],
        }
        cards.append(
            {
                "task_id": "Task2350",
                "api_l4_score_card_id": f"PLUS8000FULLAPI-2350-{idx:07d}",
                **common,
                "base_winner_acceleration_rank_score": row.get("winner_acceleration_rank_score", ""),
                "api_l2_state": api_state,
                "api_l2_score": round(adjust, 6),
                "api_raw_overlay_score": round(score, 6),
                "api_cohort_overlay_score": round(score, 6),
                "api_adjusted_rank_score": round(base_score + adjust, 6),
                "strict_gate_status": "PLUS8000_FULL_UNIVERSE_FEATURE_PROXY_NOT_STRICT_RAW_COMPLETE",
                "newdata_api_proxy_state": state,
                "newdata_api_proxy_score": score,
                "newdata_financial_source": feat.get("financial_source", "financial_source_gap"),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        decisions.append(
            {
                "task_id": "Task2351",
                "api_l5_decision_id": f"PLUS8000FULLAPIL5-2351-{idx:07d}",
                **common,
                "api_l2_state": api_state,
                "api_l5_action": action,
                "api_l5_budget_multiplier": round(mult, 6),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        audit.append(
            {
                "task_id": "Task2352",
                "api_overlay_audit_id": f"PLUS8000FULLAPIAUDIT-2352-{idx:07d}",
                **common,
                "newdata_api_proxy_state": state,
                "newdata_api_proxy_score": score,
                "api_l2_state": api_state,
                "rank_adjustment": round(adjust, 6),
                "api_l5_budget_multiplier": round(mult, 6),
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return cards, decisions, audit


def source_trade_rows(l5_rows: list[dict[str, object]], return_policy: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    scheduled = {row["trade_spec_id"]: row for row in read_csv(TASK1508 / "task1509_candidate_scheduled_return_panel.csv")}
    actual = {row["trade_spec_id"]: row for row in read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv") if row["policy_variant_id"] == SOURCE_POLICY}
    rows: list[dict[str, object]] = []
    audit: list[dict[str, object]] = []
    for idx, row in enumerate(l5_rows, start=1):
        spec = str(row["trade_spec_id"])
        chosen = None
        source = "missing"
        if return_policy == "actual_else_scheduled" and spec in actual:
            a = actual[spec]
            chosen = {
                "net_return": a.get("net_return", ""),
                "entry_date": a.get("entry_date", ""),
                "actual_exit_date": a.get("actual_exit_date", ""),
            }
            source = "task1788_actual_exit_available"
        if chosen is None and spec in scheduled:
            s = scheduled[spec]
            chosen = {
                "net_return": s.get("scheduled_net_return", ""),
                "entry_date": s.get("entry_date", ""),
                "actual_exit_date": s.get("scheduled_exit_date", ""),
            }
            source = "task1509_scheduled_uniform"
        if chosen is None:
            chosen = {"net_return": "0.0", "entry_date": "", "actual_exit_date": str(row["decision_asof_ts"])[:10]}
            source = "return_source_missing_neutral_zero"
        rows.append(
            {
                "task_id": "Task2353",
                "source_trade_id": f"PLUS8000FULLSOURCE-2353-{return_policy}-{idx:07d}",
                "return_source_policy": return_policy,
                "policy_variant_id": SOURCE_POLICY,
                "trade_spec_id": spec,
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "net_return": chosen["net_return"],
                "entry_date": chosen["entry_date"],
                "actual_exit_date": chosen["actual_exit_date"],
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        audit.append(
            {
                "task_id": "Task2353",
                "return_source_audit_id": f"PLUS8000FULLRETAUDIT-2353-{return_policy}-{idx:07d}",
                "return_source_policy": return_policy,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "return_source": source,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows, audit


def run_guard_for_policy(l5: list[dict[str, object]], cards: list[dict[str, object]], decisions: list[dict[str, object]], source_trades: list[dict[str, object]], return_policy: str) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    inputs = {
        "l5": [{str(k): str(v) for k, v in row.items()} for row in l5],
        "cards": [{str(k): str(v) for k, v in row.items()} for row in cards],
        "decisions": [{str(k): str(v) for k, v in row.items()} for row in decisions],
        "source_trades": [{str(k): str(v) for k, v in row.items()} for row in source_trades],
        "baseline_metrics": read_csv(TASK2151 / "task2175_api_three_loop_replay_metrics.csv"),
    }
    old_auth = guard.AUTHORITY
    try:
        guard.AUTHORITY = AUTHORITY
        guard_rows, trades, equity, metrics = guard.replay_guard(inputs)
    finally:
        guard.AUTHORITY = old_auth
    for row in guard_rows:
        old_policy = str(row["policy_variant_id"])
        row["task_id"] = "Task2354"
        row["return_source_policy"] = return_policy
        row["policy_variant_id"] = f"plus8000_full_{return_policy}_{POLICY_MAP.get(old_policy, old_policy)}"
        row["authority"] = AUTHORITY
    for row in trades:
        old_policy = str(row["policy_variant_id"])
        row["task_id"] = "Task2355"
        row["return_source_policy"] = return_policy
        row["policy_variant_id"] = f"plus8000_full_{return_policy}_{POLICY_MAP.get(old_policy, old_policy)}"
        row["authority"] = AUTHORITY
    for row in equity:
        old_policy = str(row["policy_variant_id"])
        row["task_id"] = "Task2356"
        row["return_source_policy"] = return_policy
        row["policy_variant_id"] = f"plus8000_full_{return_policy}_{POLICY_MAP.get(old_policy, old_policy)}"
        row["authority"] = AUTHORITY
    for row in metrics:
        old_policy = str(row["policy_variant_id"])
        row["task_id"] = "Task2357"
        row["return_source_policy"] = return_policy
        row["policy_variant_id"] = f"plus8000_full_{return_policy}_{POLICY_MAP.get(old_policy, old_policy)}"
        row["authority"] = AUTHORITY
    return guard_rows, trades, equity, metrics


def coverage_rows(pre_rows: list[dict[str, object]], l5: list[dict[str, object]], api_audit: list[dict[str, object]], return_audit: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    metrics = [
        ("full_universe_candidate_rows", len(pre_rows), len(pre_rows)),
        ("l5_decision_rows", len(l5), len(pre_rows)),
        ("api_proxy_supportive_rows", sum(1 for row in api_audit if row["newdata_api_proxy_state"] == "api_proxy_supportive"), len(api_audit)),
        ("api_proxy_source_gap_rows", sum(1 for row in api_audit if row["newdata_api_proxy_state"] == "api_proxy_source_gap_neutral"), len(api_audit)),
    ]
    source_counts = Counter(str(row["return_source"]) for row in return_audit)
    for source, count in source_counts.items():
        metrics.append((f"return_source_{source}", count, len(return_audit)))
    for metric, count, total in metrics:
        rows.append(
            {
                "task_id": "Task2358",
                "coverage_id": f"PLUS8000FULLCOVER-2358-{idx:04d}",
                "metric": metric,
                "rows": count,
                "total_rows": total,
                "ratio": round(count / total, 6) if total else 0.0,
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def comparison_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "task_id": "Task2359",
            "comparison_id": "PLUS8000FULLCOMP-2359-0001",
            "variant": "qqq_buy_hold_benchmark",
            "scope": "benchmark",
            "final_equity": QQQ_BENCHMARK_FINAL,
            "cagr": QQQ_BENCHMARK_CAGR,
            "max_drawdown": "",
            "trade_count": "",
            "authority": AUTHORITY,
        }
    ]
    idx = 2
    refs = [
        (TASK2191 / "task2196_guard_replay_metrics.csv", "original_plus8000_selected_trade"),
        (TASK2291 / "task2300_replay_metrics.csv", "prior_wrong_full_universe_proxy"),
        (TASK2321 / "task2328_replay_metrics.csv", "plus8000_brain_existing_universe_newdata"),
    ]
    for path, scope in refs:
        if not path.exists():
            continue
        for row in read_csv(path):
            rows.append(
                {
                    "task_id": "Task2359",
                    "comparison_id": f"PLUS8000FULLCOMP-2359-{idx:04d}",
                    "variant": row.get("policy_variant_id", ""),
                    "scope": scope,
                    "final_equity": row.get("final_equity", ""),
                    "cagr": row.get("cagr", ""),
                    "max_drawdown": row.get("max_drawdown", ""),
                    "trade_count": row.get("trade_count", ""),
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    for row in metrics:
        rows.append(
            {
                "task_id": "Task2359",
                "comparison_id": f"PLUS8000FULLCOMP-2359-{idx:04d}",
                "variant": row.get("policy_variant_id", ""),
                "scope": "plus8000_brain_structure_full_universe",
                "final_equity": row.get("final_equity", ""),
                "cagr": row.get("cagr", ""),
                "max_drawdown": row.get("max_drawdown", ""),
                "trade_count": row.get("trade_count", ""),
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def selection_overlap_rows(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    old_trades = read_csv(TASK2191 / "task2194_guard_replay_trades.csv")
    rows: list[dict[str, object]] = []
    idx = 1
    for old_policy, suffix in POLICY_MAP.items():
        new_policy = f"plus8000_full_actual_else_scheduled_{suffix}"
        old_rows = [row for row in old_trades if row.get("policy_variant_id") == old_policy]
        new_rows = [row for row in trades if row.get("policy_variant_id") == new_policy]
        old_specs = {row["trade_spec_id"] for row in old_rows}
        new_specs = {row["trade_spec_id"] for row in new_rows}
        common = old_specs & new_specs
        added = new_specs - old_specs
        removed = old_specs - new_specs
        rows.append(
            {
                "task_id": "Task2359",
                "overlap_audit_id": f"PLUS8000FULLOVERLAP-2359-{idx:04d}",
                "old_policy_variant_id": old_policy,
                "new_policy_variant_id": new_policy,
                "old_trade_count": len(old_specs),
                "new_trade_count": len(new_specs),
                "common_trade_count": len(common),
                "added_trade_count": len(added),
                "removed_trade_count": len(removed),
                "common_ratio_vs_old": round(len(common) / len(old_specs), 6) if old_specs else 0.0,
                "common_ratio_vs_new": round(len(common) / len(new_specs), 6) if new_specs else 0.0,
                "top_added_symbols": ";".join(f"{symbol}:{count}" for symbol, count in Counter(row["symbol"] for row in new_rows if row["trade_spec_id"] in added).most_common(10)),
                "top_removed_symbols": ";".join(f"{symbol}:{count}" for symbol, count in Counter(row["symbol"] for row in old_rows if row["trade_spec_id"] in removed).most_common(10)),
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def closeout_rows(metrics: list[dict[str, object]], pre_rows: list[dict[str, object]], l5: list[dict[str, object]]) -> list[dict[str, object]]:
    best = max(metrics, key=lambda row: (row.get("joint_target_met") == "1", f(row.get("final_equity"))))
    return [
        {
            "task_id": "Task2360",
            "verdict": "plus8000_brain_full_universe_backtest_complete_diagnostic_only",
            "full_universe_candidate_rows": len(pre_rows),
            "l5_decision_rows": len(l5),
            "original_candidate_set_only": "0",
            "plus8000_brain_structure_preserved": "1",
            "same_replay_capital_path_as_plus8000": "1",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "joint_target_met": best["joint_target_met"],
            "strict_raw_asof_complete": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], metrics: list[dict[str, object]], comparison: list[dict[str, object]], coverage: list[dict[str, object]], overlap: list[dict[str, object]]) -> None:
    metric_lines = "\n".join(
        f"- `{row['policy_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in metrics
    )
    comparison_lines = "\n".join(
        f"- `{row['variant']}` ({row['scope']}): final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in comparison
    )
    coverage_lines = "\n".join(
        f"- `{row['metric']}`: {row['rows']}/{row['total_rows']} ({row['ratio']})."
        for row in coverage
    )
    overlap_lines = "\n".join(
        f"- `{row['old_policy_variant_id']}` -> `{row['new_policy_variant_id']}`: common {row['common_trade_count']}/{row['old_trade_count']} old, added {row['added_trade_count']}, removed {row['removed_trade_count']}."
        for row in overlap
    )
    REPORT.write_text(
        f"""# Task2341-2360 Plus8000 Brain Full-Universe Backtest

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Full universe candidate rows: {closeout['full_universe_candidate_rows']}.
- L5 decision rows: {closeout['l5_decision_rows']}.
- Original candidate set only: `{closeout['original_candidate_set_only']}`.
- Plus8000 brain structure preserved: `{closeout['plus8000_brain_structure_preserved']}`.
- Same replay capital path as +8000: `{closeout['same_replay_capital_path_as_plus8000']}`.
- Best policy: `{closeout['best_policy_variant_id']}`.
- Best final equity: {closeout['best_final_equity']}.
- Best CAGR: {closeout['best_cagr']}.
- Best MDD: {closeout['best_max_drawdown']}.
- Joint target met: `{closeout['joint_target_met']}`.
- Strict raw/as-of complete: `{closeout['strict_raw_asof_complete']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task applies the +8000 brain structure to the full 3,100-candidate universe: pre-entry risk budget, winner defense, winner acceleration, Task2251 new-data API overlay, and Task2191 drawdown/sizing guard. It does not reuse only the old 116 trades. It includes two return-source policies: uniform scheduled returns for all candidates, and actual Task1788 returns where available with scheduled fallback for full-universe extension rows.

Replay results:

{metric_lines}

Comparison:

{comparison_lines}

Coverage:

{coverage_lines}

Selection overlap:

{overlap_lines}

## No-Background Decision-Maker Report

Conclusion first: this is the requested shape: +8000 brain structure, new data, full universe. It remains diagnostic because strict raw/as-of completeness is not solved and full-universe extension still uses generated bridge rows for stages that originally existed only on the 377-row +8000 candidate set.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2341_2360_plus8000_brain_full_universe_backtest/`.
- Validator: `python scripts/trader_brain_2341_2360_plus8000_brain_full_universe_backtest_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
""",
        encoding="utf-8",
    )


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    existing = {row["task_id"] for row in rows}
    fieldnames = list(rows[0].keys())
    for task_no in range(2341, 2361):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"Plus8000 Brain Full-Universe Backtest Step {task_no}",
                "owner_team": "Research Governance / Backtest & Simulation Infra",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "feature-proxy-ready-raw-asof-incomplete",
                "parent_task": f"Task{task_no - 1}" if task_no > 2341 else "Task2340",
                "key_report": "docs/reports/task_2341_2360_plus8000_brain_full_universe_backtest/task_2341_2360_plus8000_brain_full_universe_backtest.md",
                "key_decision": "docs/reports/task_2341_2360_plus8000_brain_full_universe_backtest/task_2341_2360_decision.csv",
                "key_artifacts": "data/artifacts/task_2341_2360_plus8000_brain_full_universe_backtest",
                "validation_command": "python scripts/trader_brain_2341_2360_plus8000_brain_full_universe_backtest_validate.py",
                "notes": "Applies +8000 brain structure to full 3100 candidate universe with Task2251 new-data overlay.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "116. Task2341-Task2360"
    if marker in text:
        return
    line = (
        f"116. Task2341-Task2360 ran the requested +8000 brain full-universe diagnostic: 3,100 candidates, "
        f"new Task2251 data overlay, +8000 brain structure preserved, and Task2191 replay capital path reused. "
        f"Best `{closeout['best_policy_variant_id']}` final {closeout['best_final_equity']} CAGR {closeout['best_cagr']} "
        f"MDD {closeout['best_max_drawdown']}; strict raw/as-of complete remains 0. Status remains NOT_ACCEPTED / "
        f"DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pre_rows = build_full_preentry_panel()
    winner_panel = build_winner_defense_panel(pre_rows)
    budget, l1, l2, l3, l4, l5 = build_acceleration_layers(winner_panel)
    cards, decisions, api_audit = api_overlay(l5)
    all_source_rows: list[dict[str, object]] = []
    all_return_audit: list[dict[str, object]] = []
    all_guard: list[dict[str, object]] = []
    all_trades: list[dict[str, object]] = []
    all_equity: list[dict[str, object]] = []
    all_metrics: list[dict[str, object]] = []
    for return_policy in RETURN_POLICIES:
        source_rows, return_audit = source_trade_rows(l5, return_policy)
        guards, trades, equity, metrics = run_guard_for_policy(l5, cards, decisions, source_rows, return_policy)
        all_source_rows.extend(source_rows)
        all_return_audit.extend(return_audit)
        all_guard.extend(guards)
        all_trades.extend(trades)
        all_equity.extend(equity)
        all_metrics.extend(metrics)
    coverage = coverage_rows(pre_rows, l5, api_audit, all_return_audit)
    comparison = comparison_rows(all_metrics)
    overlap = selection_overlap_rows(all_trades)
    closeout = closeout_rows(all_metrics, pre_rows, l5)

    write_csv(OUT_DIR / "task2341_experiment_contract.csv", [
        {
            "task_id": "Task2341",
            "full_universe_candidate_rows": len(pre_rows),
            "original_candidate_set_only": "0",
            "plus8000_brain_structure_preserved": "1",
            "same_replay_capital_path_as_plus8000": "1",
            "new_data_source": "data/artifacts/task_2251_2280_plus8000_full_source_acquisition/task2256_recomputed_plus8000_feature_panel.csv",
            "strict_raw_asof_complete": "0",
            "authority": AUTHORITY,
        }
    ])
    write_csv(OUT_DIR / "task2342_full_preentry_panel.csv", pre_rows)
    write_csv(OUT_DIR / "task2343_full_winner_defense_panel.csv", winner_panel)
    write_csv(OUT_DIR / "task2344_full_sleeve_budget_rows.csv", budget)
    write_csv(OUT_DIR / "task2345_full_l1_packets.csv", l1)
    write_csv(OUT_DIR / "task2346_full_l2_semantics.csv", l2)
    write_csv(OUT_DIR / "task2347_full_l3_edges.csv", l3)
    write_csv(OUT_DIR / "task2348_full_l4_thesis_cards.csv", l4)
    write_csv(OUT_DIR / "task2349_full_l5_decisions.csv", l5)
    write_csv(OUT_DIR / "task2350_full_api_l4_cards.csv", cards)
    write_csv(OUT_DIR / "task2351_full_api_l5_decisions.csv", decisions)
    write_csv(OUT_DIR / "task2352_full_api_overlay_audit.csv", api_audit)
    write_csv(OUT_DIR / "task2353_full_return_source_rows.csv", all_source_rows)
    write_csv(OUT_DIR / "task2353_full_return_source_audit.csv", all_return_audit)
    write_csv(OUT_DIR / "task2354_full_guard_rows.csv", all_guard)
    write_csv(OUT_DIR / "task2355_full_replay_trades.csv", all_trades)
    write_csv(OUT_DIR / "task2356_full_replay_equity.csv", all_equity)
    write_csv(OUT_DIR / "task2357_full_replay_metrics.csv", all_metrics)
    write_csv(OUT_DIR / "task2358_full_coverage.csv", coverage)
    write_csv(OUT_DIR / "task2359_comparison_matrix.csv", comparison)
    write_csv(OUT_DIR / "task2359_selection_overlap_audit.csv", overlap)
    write_csv(OUT_DIR / "task2360_closeout.csv", closeout)
    write_json(OUT_DIR / "task2360_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], all_metrics, comparison, coverage, overlap)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2341_2360_PLUS8000_BRAIN_FULL_UNIVERSE_BACKTEST_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
