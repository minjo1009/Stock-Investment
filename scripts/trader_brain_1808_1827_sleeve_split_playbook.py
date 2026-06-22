from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1768_1787_preentry_risk_budget_v2 as v2
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
OUT_DIR = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
REPORT_DIR = ROOT / "docs/reports/task_1808_1827_sleeve_split_playbook"
REPORT = REPORT_DIR / "task_1808_1827_sleeve_split_playbook.md"
DECISION = REPORT_DIR / "task_1808_1827_decision.csv"

AUTHORITY = "DIAGNOSTIC_SLEEVE_SPLIT_PLAYBOOK_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "sleeve_split_top3_v1": {"source_policy": "winner_defense_budget_top3_v1", "slot_cap": 3},
    "sleeve_split_top5_v1": {"source_policy": "winner_defense_budget_top5_v1", "slot_cap": 5},
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row.keys():
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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value: object) -> date | None:
    return v2.parse_date(value)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def expert_rows() -> list[dict[str, object]]:
    rows = [
        (
            "portfolio_pm",
            "Core-satellite portfolio construction",
            "One global top-N book is a frontier problem; split sleeve mandates before more sizing tweaks.",
            "adopt_sleeve_split",
        ),
        (
            "risk_budget_officer",
            "CFA-style risk budgeting",
            "Allocate risk by strategy sleeve and factor cluster, not only by position-level volatility.",
            "adopt_sleeve_risk_budget",
        ),
        (
            "factor_quant",
            "Fama-French and AQR factor framing",
            "Winner, cyclical beta, speculative event, and defensive quality have different payoff/risk mechanics.",
            "adopt_factor_sleeve_mapping",
        ),
        (
            "event_study_quant",
            "MacKinlay event-study framing",
            "Use attribution ledger before replay so the policy can target the actual drawdown source.",
            "adopt_drawdown_ledger_first",
        ),
        (
            "semiconductor_specialist",
            "AI/semiconductor cycle playbook",
            "High-quality winners need a different hold rule from speculative catalysts.",
            "adopt_winner_compounder_playbook",
        ),
        (
            "backend_governance",
            "Project harness discipline",
            "Freeze sleeve/playbook rules before replay; outcomes must stay audit-only.",
            "adopt_frozen_config",
        ),
    ]
    return [
        {
            "task_id": "Task1825",
            "expert_review_id": f"SLEEVEAUDIT-1825-{idx:03d}",
            "expert_role": role,
            "source_anchor": source,
            "critique": critique,
            "implementation_decision": decision,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, source, critique, decision) in enumerate(rows, 1)
    ]


def load_panel() -> list[dict[str, str]]:
    return read_csv(TASK1788 / "task1790_winner_defense_panel.csv")


def load_trades() -> list[dict[str, str]]:
    return read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv")


def source_trade_map() -> dict[tuple[str, str], dict[str, str]]:
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in load_trades()}


def qqq_regime(decision_asof_ts: str, cache: dict[str, pd.DataFrame | None]) -> dict[str, object]:
    parsed = replay.parse_ts(decision_asof_ts)
    if parsed is None:
        return {
            "regime_state": "regime_source_gap",
            "qqq_return_63d": 0.0,
            "qqq_drawdown_126d": 0.0,
            "qqq_realized_vol_63d": 0.0,
            "regime_data_ready": "0",
        }
    frame = replay.load_price("QQQ", cache)
    if frame is None:
        return {
            "regime_state": "regime_source_gap",
            "qqq_return_63d": 0.0,
            "qqq_drawdown_126d": 0.0,
            "qqq_realized_vol_63d": 0.0,
            "regime_data_ready": "0",
        }
    d = parsed.date()
    hist = frame[frame["Date"] <= d].tail(127).copy()
    if len(hist) < 30:
        return {
            "regime_state": "regime_source_gap",
            "qqq_return_63d": 0.0,
            "qqq_drawdown_126d": 0.0,
            "qqq_realized_vol_63d": 0.0,
            "regime_data_ready": "0",
        }
    last = float(hist.iloc[-1]["Close"])
    ret_base = float(hist.tail(64).iloc[0]["Close"]) if len(hist) >= 64 else float(hist.iloc[0]["Close"])
    qqq_return_63d = last / ret_base - 1.0 if ret_base > 0 else 0.0
    peak = float(hist["Close"].max())
    drawdown = last / peak - 1.0 if peak > 0 else 0.0
    vol = float(hist.tail(64)["Close"].pct_change().dropna().std() * (252**0.5))
    if qqq_return_63d <= -0.12 or drawdown <= -0.16:
        regime = "broad_selloff"
    elif qqq_return_63d <= -0.06 or drawdown <= -0.10:
        regime = "valuation_compression"
    elif qqq_return_63d >= 0.08 and drawdown >= -0.06:
        regime = "risk_on"
    elif qqq_return_63d >= 0.02:
        regime = "neutral_to_positive"
    else:
        regime = "neutral_chop"
    return {
        "regime_state": regime,
        "qqq_return_63d": round(qqq_return_63d, 6),
        "qqq_drawdown_126d": round(drawdown, 6),
        "qqq_realized_vol_63d": round(vol, 6),
        "regime_data_ready": "1",
    }


def classify_sleeve(row: dict[str, str]) -> str:
    cluster = row.get("factor_cluster", "")
    cause = row.get("volatility_cause", "")
    bucket = row.get("winner_defense_bucket", "")
    event = row.get("event_family", "")
    payoff = row.get("payoff_quality_bucket", "")
    quality = to_float(row.get("winner_quality_beta"))
    rel = to_float(row.get("relative_return_63d"))
    vol = to_float(row.get("realized_vol_63d"))
    liquidity = to_float(row.get("avg_dollar_volume_20d"))

    if event in {"survival", "dilution", "financing"} or cause == "terminal_or_financing_thesis_risk":
        return "speculative_event"
    if bucket in {"strong_winner_defense", "qualified_winner_defense"} and quality >= 68 and rel >= 0.06 and payoff in {"top3_payoff_candidate", "eligible_payoff_candidate"}:
        return "winner_compounder"
    if cluster in {"cyclical_beta", "financial_beta"}:
        return "cyclical_beta"
    if cluster == "speculative_growth" or vol >= 0.55 or liquidity < 50_000_000:
        return "speculative_event"
    if cluster == "defensive_quality" or (vol <= 0.26 and liquidity >= 100_000_000):
        return "defensive_quality"
    if cause in {"normal_winner_volatility", "leader_momentum_volatility"} and quality >= 60:
        return "winner_compounder"
    return "cyclical_beta"


def sleeve_contract_rows() -> list[dict[str, object]]:
    contracts = [
        ("winner_compounder", "drive_cagr", "quality plus payoff plus relative strength", "terminal_or_financing risk; thesis break", "allow concentrated hold with drawdown-aware cap"),
        ("cyclical_beta", "harvest regime beta", "cycle and market regime confirmation", "valuation compression or broad selloff", "size only when regime supports"),
        ("speculative_event", "capture catalyst convexity", "event validation with limited capital", "dilution, financing stress, catalyst expiry", "small cap and fast invalidation"),
        ("defensive_quality", "drawdown buffer", "liquidity, lower volatility, defensive quality", "quality deterioration", "stabilize book when attack sleeves are risky"),
    ]
    return [
        {
            "task_id": "Task1809",
            "sleeve_id": f"SLEEVE-1809-{idx:03d}",
            "sleeve_name": name,
            "mandate": mandate,
            "entry_basis": entry,
            "invalidation_basis": invalidation,
            "risk_budget_rule": risk,
            "authority": AUTHORITY,
        }
        for idx, (name, mandate, entry, invalidation, risk) in enumerate(contracts, 1)
    ]


def regime_panel(panel: list[dict[str, str]]) -> list[dict[str, object]]:
    cache: dict[str, pd.DataFrame | None] = {}
    seen: set[str] = set()
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(sorted(panel, key=lambda r: (r["decision_asof_ts"], r["target_policy_variant_id"])), 1):
        key = f"{row['target_policy_variant_id']}|{row['decision_asof_ts']}"
        if key in seen:
            continue
        seen.add(key)
        regime = qqq_regime(row["decision_asof_ts"], cache)
        rows.append(
            {
                "task_id": "Task1810",
                "regime_id": f"REGIME-1810-{idx:06d}",
                "target_policy_variant_id": row["target_policy_variant_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                **regime,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def source_routing_rows() -> list[dict[str, object]]:
    routes = [
        ("company_filings_ir", "winner_compounder", "growth durability and thesis integrity"),
        ("company_filings_ir", "speculative_event", "dilution, financing, runway, and catalyst validation"),
        ("earnings_guidance", "winner_compounder", "expectation gap and hold extension"),
        ("earnings_guidance", "cyclical_beta", "cycle confirmation or earnings break"),
        ("macro_policy_official", "cyclical_beta", "risk-on/risk-off and policy support"),
        ("positioning_liquidity_volatility", "defensive_quality", "liquidity and drawdown buffer"),
        ("sector_specialist_official_docs", "winner_compounder", "theme tailwind and competitive durability"),
    ]
    return [
        {
            "task_id": "Task1811",
            "source_route_id": f"SOURCEROUTE-1811-{idx:03d}",
            "source_family": source,
            "sleeve_name": sleeve,
            "routing_meaning": meaning,
            "authority": AUTHORITY,
        }
        for idx, (source, sleeve, meaning) in enumerate(routes, 1)
    ]


def enrich_panel(panel: list[dict[str, str]], regimes: list[dict[str, object]]) -> list[dict[str, object]]:
    regime_by_key = {(row["target_policy_variant_id"], row["decision_asof_ts"]): row for row in regimes}
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(panel, 1):
        sleeve = classify_sleeve(row)
        regime = regime_by_key[(row["target_policy_variant_id"], row["decision_asof_ts"])]
        quality = to_float(row["winner_quality_beta"])
        payoff_score = to_float(row["payoff_quality_score"])
        rel = to_float(row["relative_return_63d"])
        drawdown = to_float(row["prior_drawdown_126d"])
        terminal = "1" if row["volatility_cause"] == "terminal_or_financing_thesis_risk" or row["event_family"] in {"survival", "dilution", "financing"} else "0"
        sleeve_score = payoff_score * 0.35 + quality * 0.35 + max(0.0, rel) * 100.0 * 0.20 + max(0.0, 0.15 + drawdown) * 100.0 * 0.10
        if terminal == "1":
            sleeve_score = min(sleeve_score, 38.0)
        if sleeve == "defensive_quality":
            sleeve_score += 6.0
        rows.append(
            {
                **row,
                "task_id": "Task1812",
                "sleeve_meaning_id": f"SLEEVEMEANING-1812-{idx:07d}",
                "strategy_sleeve": sleeve,
                "regime_state": regime["regime_state"],
                "qqq_return_63d": regime["qqq_return_63d"],
                "qqq_drawdown_126d": regime["qqq_drawdown_126d"],
                "qqq_realized_vol_63d": regime["qqq_realized_vol_63d"],
                "terminal_override_flag": terminal,
                "sleeve_quality_score": round(clamp(sleeve_score, 0.0, 100.0), 4),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def relation_edges(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    edges: list[dict[str, object]] = []
    edge_idx = 1
    for row in rows:
        sleeve = row["strategy_sleeve"]
        cause = row["volatility_cause"]
        regime = row["regime_state"]
        if sleeve == "winner_compounder":
            primitive = "supports_winner_hold" if cause in {"normal_winner_volatility", "leader_momentum_volatility", "ordinary_noise"} else "conditions_winner_size"
        elif sleeve == "cyclical_beta":
            primitive = "cyclical_regime_confirms" if regime in {"risk_on", "neutral_to_positive"} else "cyclical_regime_weakens"
        elif sleeve == "speculative_event":
            primitive = "speculative_event_cap_or_exit" if row["terminal_override_flag"] == "1" else "speculative_event_limited_size"
        else:
            primitive = "defensive_buffer_needed" if regime in {"broad_selloff", "valuation_compression"} else "defensive_buffer_optional"
        edges.append(
            {
                "task_id": "Task1813",
                "sleeve_edge_id": f"SLEEVEEDGE-1813-{edge_idx:07d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "target_policy_variant_id": row["target_policy_variant_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": sleeve,
                "relation_primitive": primitive,
                "edge_explanation": f"{sleeve}|{regime}|{cause}",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        edge_idx += 1
    return edges


def thesis_cards(rows: list[dict[str, object]], edges: list[dict[str, object]]) -> list[dict[str, object]]:
    edge_by_spec = {row["trade_spec_id"]: row for row in edges}
    cards: list[dict[str, object]] = []
    for idx, row in enumerate(rows, 1):
        edge = edge_by_spec[row["trade_spec_id"]]
        invalidation = {
            "winner_compounder": "source_confirmed_thesis_break_or_terminal_override",
            "cyclical_beta": "regime_turns_valuation_compression_or_broad_selloff",
            "speculative_event": "catalyst_expiry_dilution_financing_or_terminal_override",
            "defensive_quality": "quality_or_liquidity_buffer_break",
        }[row["strategy_sleeve"]]
        cards.append(
            {
                "task_id": "Task1814",
                "sleeve_thesis_card_id": f"SLEEVETHESIS-1814-{idx:07d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "target_policy_variant_id": row["target_policy_variant_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": row["strategy_sleeve"],
                "regime_state": row["regime_state"],
                "sleeve_quality_score": row["sleeve_quality_score"],
                "relation_primitive": edge["relation_primitive"],
                "invalidation_rule": invalidation,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return cards


def sleeve_multiplier(row: dict[str, object]) -> tuple[float, str, str]:
    base = to_float(row["winner_defense_multiplier_v3"])
    sleeve = row["strategy_sleeve"]
    regime = row["regime_state"]
    terminal = row["terminal_override_flag"] == "1"
    quality = to_float(row["sleeve_quality_score"])
    cause = row["volatility_cause"]
    multiplier = base
    action = "hold"
    reason = "base_winner_defense"

    if sleeve == "winner_compounder":
        if terminal:
            multiplier = min(multiplier, 0.35)
            action = "reduce"
            reason = "winner_terminal_override"
        elif regime in {"risk_on", "neutral_to_positive"} and quality >= 74:
            multiplier = min(multiplier * 1.06, 1.18)
            action = "add_or_hold"
            reason = "winner_regime_supported"
        elif regime in {"broad_selloff", "valuation_compression"}:
            multiplier = min(multiplier * 0.92, 1.05)
            action = "hold_or_trim"
            reason = "winner_macro_pressure"
    elif sleeve == "cyclical_beta":
        if regime == "risk_on":
            multiplier = min(multiplier * 1.03, 1.05)
            action = "hold"
            reason = "cyclical_regime_on"
        elif regime in {"broad_selloff", "valuation_compression"}:
            multiplier *= 0.62
            action = "reduce"
            reason = "cyclical_regime_off"
        else:
            multiplier *= 0.82
            action = "trim"
            reason = "cyclical_neutral_chop"
    elif sleeve == "speculative_event":
        if terminal:
            multiplier = 0.0
            action = "no_entry"
            reason = "speculative_terminal_block"
        elif regime in {"broad_selloff", "valuation_compression"}:
            multiplier = min(multiplier * 0.55, 0.32)
            action = "reduce"
            reason = "speculative_risk_off_cap"
        else:
            multiplier = min(multiplier, 0.48)
            action = "cap"
            reason = "speculative_event_cap"
    else:
        if regime in {"broad_selloff", "valuation_compression"}:
            multiplier = min(max(multiplier, 0.70) * 1.04, 0.95)
            action = "hold"
            reason = "defensive_buffer_on"
        else:
            multiplier = min(multiplier, 0.78)
            action = "hold"
            reason = "defensive_buffer_optional"

    if cause in {"issuer_specific_expectation_break", "company_specific_drawdown"} and quality < 60:
        multiplier *= 0.70
        action = "reduce"
        reason = "issuer_specific_damage_cap"
    multiplier = round(clamp(multiplier, 0.0, 1.18), 4)
    return multiplier, action, reason


def risk_budget_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for idx, row in enumerate(rows, 1):
        mult, action, reason = sleeve_multiplier(row)
        out.append(
            {
                "task_id": "Task1815",
                "sleeve_budget_id": f"SLEEVEBUDGET-1815-{idx:07d}",
                "target_policy_variant_id": row["target_policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": row["strategy_sleeve"],
                "regime_state": row["regime_state"],
                "winner_defense_multiplier_v3": row["winner_defense_multiplier_v3"],
                "sleeve_budget_multiplier": mult,
                "sleeve_action": action,
                "sleeve_action_reason": reason,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return out


def playbook_rows() -> list[dict[str, object]]:
    rows = [
        ("Task1817", "winner_compounder", "quality plus payoff plus relative strength; hold through normal volatility", "add_or_hold in risk_on; hold_or_trim in compression; reduce on terminal override"),
        ("Task1818", "cyclical_beta", "requires market and cycle support", "hold in risk_on; trim neutral; reduce in broad selloff or valuation compression"),
        ("Task1819", "speculative_event", "small capital catalyst sleeve", "cap normally; reduce in risk-off; no-entry on terminal financing/dilution risk"),
        ("Task1820", "defensive_quality", "portfolio buffer sleeve", "maintain buffer in risk-off; cap in risk-on so it does not crowd out winners"),
    ]
    return [
        {
            "task_id": task,
            "playbook_id": f"PLAYBOOK-{task[-4:]}-{idx:03d}",
            "strategy_sleeve": sleeve,
            "playbook_contract": contract,
            "l5_action_rule": rule,
            "authority": AUTHORITY,
        }
        for idx, (task, sleeve, contract, rule) in enumerate(rows, 1)
    ]


def action_rules_rows() -> list[dict[str, object]]:
    rules = [
        ("hold", "allowed when sleeve thesis and regime contract remain intact"),
        ("add_or_hold", "allowed only for winner_compounder with quality/regime support"),
        ("trim", "used for neutral cyclical or defensive optional states"),
        ("reduce", "used for regime-off cyclical/speculative or issuer-specific damage"),
        ("no_entry", "used for terminal speculative financing/dilution risk"),
    ]
    return [
        {
            "task_id": "Task1816",
            "l5_action_rule_id": f"SLEEVEACTION-1816-{idx:03d}",
            "sleeve_action": action,
            "rule_meaning": meaning,
            "authority": AUTHORITY,
        }
        for idx, (action, meaning) in enumerate(rules, 1)
    ]


def frozen_config_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1821",
            "config_id": "SLEEVEPLAYBOOK-1821-FROZEN-V1",
            "source_policy_top3": "winner_defense_budget_top3_v1",
            "source_policy_top5": "winner_defense_budget_top5_v1",
            "replay_policy_top3": "sleeve_split_top3_v1",
            "replay_policy_top5": "sleeve_split_top5_v1",
            "initial_capital": INITIAL_CAPITAL,
            "benchmark": "QQQ",
            "round_trip_cost_bps": 10,
            "slippage_bps_each_side": 5,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
    ]


def replay_budget(budget_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    source_trades = source_trade_map()
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in budget_rows:
        grouped[(str(row["target_policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    trade_idx = 1
    for policy_id, config in POLICIES.items():
        source_policy = config["source_policy"]
        capital = INITIAL_CAPITAL
        decisions = sorted({key[1] for key in grouped if key[0] == source_policy})
        for decision_ts in decisions:
            rows = sorted(grouped[(source_policy, decision_ts)], key=lambda r: to_float(r["sleeve_budget_multiplier"]), reverse=True)
            base_alloc = capital / int(config["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            sleeve_counts: Counter[str] = Counter()
            for row in rows:
                source = source_trades.get((source_policy, str(row["trade_spec_id"])))
                if not source:
                    continue
                mult = to_float(row["sleeve_budget_multiplier"])
                if mult <= 0:
                    continue
                allocated = base_alloc * mult
                pnl = allocated * to_float(source.get("net_return"))
                capital += pnl
                period_pnl += pnl
                allocated_count += 1
                sleeve_counts[str(row["strategy_sleeve"])] += 1
                trades.append(
                    {
                        "task_id": "Task1822",
                        "trade_row_id": f"SLEEVETRADE-1822-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": row["trade_spec_id"],
                        "candidate_source_id": row["candidate_source_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "strategy_sleeve": row["strategy_sleeve"],
                        "regime_state": row["regime_state"],
                        "sleeve_action": row["sleeve_action"],
                        "sleeve_action_reason": row["sleeve_action_reason"],
                        "sleeve_budget_multiplier": mult,
                        "source_net_return": source.get("net_return", ""),
                        "capital_allocated": round(allocated, 4),
                        "pnl": round(pnl, 4),
                        "net_return": source.get("net_return", ""),
                        "entry_date": source.get("entry_date", ""),
                        "actual_exit_date": source.get("actual_exit_date", ""),
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            equity.append(
                {
                    "task_id": "Task1822",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(rows),
                    "allocated_count": allocated_count,
                    "winner_compounder_count": sleeve_counts["winner_compounder"],
                    "cyclical_beta_count": sleeve_counts["cyclical_beta"],
                    "speculative_event_count": sleeve_counts["speculative_event"],
                    "defensive_quality_count": sleeve_counts["defensive_quality"],
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base = {row["policy_variant_id"]: row for row in read_csv(TASK1788 / "task1793_winner_defense_replay_metrics.csv")}
    base_map = {
        "sleeve_split_top3_v1": "winner_defense_budget_top3_v1",
        "sleeve_split_top5_v1": "winner_defense_budget_top5_v1",
    }
    tr_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    eq_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        tr_groups[str(row["policy_variant_id"])].append(row)
    for row in equity:
        eq_groups[str(row["policy_variant_id"])].append(row)
    out: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(eq_groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        tr_rows = tr_groups[policy_id]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end_dates = [parse_date(row.get("actual_exit_date")) for row in tr_rows]
        end = max([d for d in end_dates if d is not None] or [start])
        cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd = replay.max_drawdown(values)
        baseline = base[base_map[policy_id]]
        out.append(
            {
                "task_id": "Task1823",
                "policy_variant_id": policy_id,
                "baseline_policy_variant_id": base_map[policy_id],
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr, 6),
                "max_drawdown": round(mdd, 6),
                "trade_count": len(tr_rows),
                "baseline_final_equity": baseline["final_equity"],
                "baseline_cagr": baseline["cagr"],
                "baseline_max_drawdown": baseline["max_drawdown"],
                "delta_final_equity": round(final - to_float(baseline["final_equity"]), 4),
                "delta_cagr": round(cagr - to_float(baseline["cagr"]), 6),
                "delta_mdd": round(mdd - to_float(baseline["max_drawdown"]), 6),
                "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
                "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
                "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return out


def split_rows(equity: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in equity:
        d = replay.parse_ts(str(row["decision_asof_ts"])).date()
        window = "IS_2021_2023" if d.year <= 2023 else "OOS_2024_2026Q1"
        groups[(str(row["policy_variant_id"]), window)].append(row)
    rows: list[dict[str, object]] = []
    for (policy_id, window), items in sorted(groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in items]
        rows.append(
            {
                "task_id": "Task1823",
                "policy_variant_id": policy_id,
                "split_window": window,
                "period_count": len(items),
                "split_final_equity": round(values[-1], 4),
                "split_total_return": round(values[-1] / INITIAL_CAPITAL - 1.0, 6),
                "split_max_drawdown": round(replay.max_drawdown(values), 6),
                "authority": AUTHORITY,
            }
        )
    return rows


def cost_stress_rows(metrics_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    stress_bps = [0, 25, 50, 100]
    idx = 1
    for metric in metrics_rows:
        trades = int(metric["trade_count"])
        for bps in stress_bps:
            haircut = trades * (bps / 10000.0) * 0.35
            stressed_final = to_float(metric["final_equity"]) * max(0.0, 1.0 - haircut)
            rows.append(
                {
                    "task_id": "Task1823",
                    "cost_stress_id": f"SLEEVECOST-1823-{idx:04d}",
                    "policy_variant_id": metric["policy_variant_id"],
                    "round_trip_cost_bps": bps,
                    "approx_trade_count": trades,
                    "stressed_final_equity": round(stressed_final, 4),
                    "beats_qqq_after_stress": "1" if stressed_final > QQQ_BENCHMARK_FINAL else "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def attribution_ledger(rows: list[dict[str, object]], trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    by_spec = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in trades}
    equity_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in equity:
        equity_groups[str(row["policy_variant_id"])].append(row)
    equity_audit: dict[tuple[str, str], dict[str, object]] = {}
    for policy_id, group in equity_groups.items():
        previous_equity = INITIAL_CAPITAL
        previous_decision = ""
        peak = INITIAL_CAPITAL
        previous_drawdown_amount = 0.0
        for eq in sorted(group, key=lambda row: str(row["decision_asof_ts"])):
            equity_end = to_float(eq["equity"])
            peak = max(peak, equity_end)
            drawdown_amount = equity_end - peak
            drawdown_pct = drawdown_amount / peak if peak else 0.0
            period_drawdown_delta = drawdown_amount - previous_drawdown_amount
            equity_audit[(policy_id, str(eq["decision_asof_ts"]))] = {
                "attribution_period_start": previous_decision,
                "attribution_period_end": eq["decision_asof_ts"],
                "equity_start": previous_equity,
                "equity_end": equity_end,
                "equity_peak_to_date": peak,
                "drawdown_amount": drawdown_amount,
                "drawdown_pct": drawdown_pct,
                "period_drawdown_delta": period_drawdown_delta,
                "period_pnl": to_float(eq["period_pnl"]),
            }
            previous_equity = equity_end
            previous_decision = str(eq["decision_asof_ts"])
            previous_drawdown_amount = drawdown_amount
    trade_groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for trade in trades:
        trade_groups[(str(trade["policy_variant_id"]), str(trade["decision_asof_ts"]))].append(trade)
    drawdown_contrib: dict[tuple[str, str], float] = {}
    for key, group in trade_groups.items():
        audit = equity_audit.get(key)
        if not audit:
            continue
        delta = to_float(audit["period_drawdown_delta"])
        negative_total = sum(to_float(trade["pnl"]) for trade in group if to_float(trade["pnl"]) < 0)
        for trade in group:
            pnl = to_float(trade["pnl"])
            if delta < 0 and pnl < 0 and negative_total < 0:
                drawdown_contrib[(str(trade["policy_variant_id"]), str(trade["trade_spec_id"]))] = round(delta * (pnl / negative_total), 6)
            else:
                drawdown_contrib[(str(trade["policy_variant_id"]), str(trade["trade_spec_id"]))] = 0.0
    ledger: list[dict[str, object]] = []
    idx = 1
    for row in rows:
        policy_id = row["target_policy_variant_id"].replace("winner_defense_budget", "sleeve_split")
        trade = by_spec.get((policy_id, row["trade_spec_id"]))
        eq = equity_audit.get((policy_id, row["decision_asof_ts"]), {})
        pnl = to_float(trade.get("pnl")) if trade else 0.0
        period_pnl = to_float(eq.get("period_pnl")) if eq else 0.0
        dd_contrib = drawdown_contrib.get((policy_id, str(row["trade_spec_id"])), 0.0)
        ledger.append(
            {
                "task_id": "Task1808",
                "ledger_id": f"SLEEVELEDGER-1808-{idx:07d}",
                "policy_variant_id": policy_id,
                "source_policy_variant_id": row["target_policy_variant_id"],
                "attribution_period_start": eq.get("attribution_period_start", ""),
                "attribution_period_end": eq.get("attribution_period_end", row["decision_asof_ts"]),
                "decision_asof_ts": row["decision_asof_ts"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "tradable_object_id": row["symbol"],
                "derived_theme": row["derived_theme"],
                "strategy_sleeve": row["strategy_sleeve"],
                "factor_cluster": row["factor_cluster"],
                "avg_dollar_volume_20d": row["avg_dollar_volume_20d"],
                "liquidity_risk": row["liquidity_risk"],
                "source_independence_state": row["source_independence_state"],
                "event_family": row["event_family"],
                "payoff_mechanism": row["payoff_mechanism"],
                "expectation_state": row["expectation_state"],
                "absorption_state": row["absorption_state"],
                "materiality_state": row["materiality_state"],
                "regime_state": row["regime_state"],
                "volatility_cause": row["volatility_cause"],
                "cluster_count_same_decision": row["cluster_count_same_decision"],
                "cluster_corr_63d": row["cluster_corr_63d"],
                "risk_pressure": row["risk_pressure"],
                "cluster_pressure": row["cluster_pressure"],
                "fragility_pressure": row["fragility_pressure"],
                "air_pocket_pressure": row["air_pocket_pressure"],
                "liquidity_pressure": row["liquidity_pressure"],
                "collapse_risk_bucket": row["collapse_risk_bucket"],
                "payoff_quality_bucket": row["payoff_quality_bucket"],
                "payoff_quality_score": row["payoff_quality_score"],
                "winner_quality_beta": row["winner_quality_beta"],
                "winner_defense_bucket": row["winner_defense_bucket"],
                "winner_defense_credit": row["winner_defense_credit"],
                "selection_reason": row["selection_reason"],
                "risk_budget_state": row["risk_budget_state"],
                "risk_budget_multiplier": row["risk_budget_multiplier"],
                "risk_budget_state_v2": row["risk_budget_state_v2"],
                "risk_budget_multiplier_v2": row["risk_budget_multiplier_v2"],
                "winner_defense_id": row["winner_defense_id"],
                "winner_defense_multiplier_v3": row["winner_defense_multiplier_v3"],
                "winner_defense_action": row["winner_defense_action"],
                "sleeve_action": trade.get("sleeve_action") if trade else "no_entry",
                "sleeve_budget_multiplier": trade.get("sleeve_budget_multiplier") if trade else 0.0,
                "capital_allocated": trade.get("capital_allocated") if trade else 0.0,
                "allocated_weight": round(to_float(trade.get("capital_allocated")) / to_float(eq.get("equity_start"), INITIAL_CAPITAL), 6) if trade and to_float(eq.get("equity_start"), INITIAL_CAPITAL) else 0.0,
                "entry_date": trade.get("entry_date") if trade else "",
                "actual_exit_date": trade.get("actual_exit_date") if trade else "",
                "position_open_at_period_start": "0",
                "position_open_at_period_end": "0",
                "period_position_weight": round(to_float(trade.get("capital_allocated")) / to_float(eq.get("equity_start"), INITIAL_CAPITAL), 6) if trade and to_float(eq.get("equity_start"), INITIAL_CAPITAL) else 0.0,
                "pnl": round(pnl, 4),
                "period_pnl": round(period_pnl, 4),
                "cumulative_trade_pnl": round(pnl, 4),
                "period_pnl_share_audit_only": round(pnl / period_pnl, 6) if period_pnl else 0.0,
                "net_return": trade.get("net_return") if trade else "",
                "source_net_return": trade.get("source_net_return") if trade else "",
                "equity_start": round(to_float(eq.get("equity_start")), 4),
                "equity_end": round(to_float(eq.get("equity_end")), 4),
                "equity_peak_to_date": round(to_float(eq.get("equity_peak_to_date")), 4),
                "drawdown_amount": round(to_float(eq.get("drawdown_amount")), 4),
                "drawdown_pct": round(to_float(eq.get("drawdown_pct")), 6),
                "period_drawdown_delta": round(to_float(eq.get("period_drawdown_delta")), 6),
                "trade_drawdown_contribution": dd_contrib,
                "trade_drawdown_contribution_pct": round(dd_contrib / to_float(eq.get("period_drawdown_delta")), 6) if to_float(eq.get("period_drawdown_delta")) else 0.0,
                "sleeve_candidate_group": row["strategy_sleeve"],
                "sleeve_audit_bucket": "drawdown_contributor" if dd_contrib < 0 else ("recovery_or_positive" if pnl > 0 else "neutral_or_no_entry"),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return ledger


def failure_attribution(rows: list[dict[str, object]], trades: list[dict[str, object]], metrics_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    idx = 1
    for label in ["strategy_sleeve", "regime_state", "sleeve_action", "sleeve_action_reason"]:
        counts = Counter(str(row[label]) for row in rows if label in row)
        for reason, count in counts.most_common():
            out.append({"task_id": "Task1824", "attribution_id": f"SLEEVEATTR-1824-{idx:05d}", "failure_area": label, "reason": reason, "row_count": count, "authority": AUTHORITY})
            idx += 1
    for label in ["strategy_sleeve", "regime_state", "sleeve_action"]:
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for trade in trades:
            grouped[str(trade[label])].append(trade)
        for reason, group in sorted(grouped.items()):
            out.append(
                {
                    "task_id": "Task1824",
                    "attribution_id": f"SLEEVEATTR-1824-{idx:05d}",
                    "failure_area": f"{label}_pnl",
                    "reason": reason,
                    "row_count": len(group),
                    "pnl_sum": round(sum(to_float(row["pnl"]) for row in group), 4),
                    "avg_net_return": round(sum(to_float(row["net_return"]) for row in group) / len(group), 6) if group else 0.0,
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    for metric in metrics_rows:
        if metric["joint_target_met"] != "1":
            out.append(
                {
                    "task_id": "Task1824",
                    "attribution_id": f"SLEEVEATTR-1824-{idx:05d}",
                    "failure_area": "target_failure",
                    "policy_variant_id": metric["policy_variant_id"],
                    "cagr": metric["cagr"],
                    "max_drawdown": metric["max_drawdown"],
                    "joint_target_met": metric["joint_target_met"],
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return out


def gate_closeout(metrics_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best = max(metrics_rows, key=lambda row: to_float(row["final_equity"]))
    gate = [
        {
            "task_id": "Task1826",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "joint_target_met_by_any": "1" if any(row["joint_target_met"] == "1" for row in metrics_rows) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "sleeve_split_diagnostic_only_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1827",
            "verdict": "sleeve_split_playbook_implemented_diagnostic_only",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "audit sleeve attribution and decide whether to add targeted rates earnings-revision and sector-breadth data",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(metrics_rows: list[dict[str, object]], split: list[dict[str, object]], cost: list[dict[str, object]], attr: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1808-1827 Sleeve Split Playbook",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Best policy: `{closeout['best_policy_variant_id']}`.",
        f"- Best final equity: {closeout['best_final_equity']}.",
        f"- Best CAGR: {closeout['best_cagr']}.",
        f"- Best MDD: {closeout['best_max_drawdown']}.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Data source and exact join keys:",
        "",
        "- Source panel: `task1790_winner_defense_panel.csv`, joined by `target_policy_variant_id`, `trade_spec_id`, and `decision_asof_ts`.",
        "- Source trades: `task1792_winner_defense_replay_trades.csv`, joined by `policy_variant_id` and `trade_spec_id`.",
        "- Market regime: prior QQQ prices only, using rows on or before `decision_asof_ts`.",
        "",
        "Leakage audit:",
        "",
        "- Assignment uses pre-entry features, sleeve taxonomy, prior QQQ regime, and frozen playbook rules only.",
        "- PnL, period PnL share, and drawdown contribution are audit-only fields.",
        "",
        "| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | Joint Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics_rows:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['baseline_final_equity']} | {row['baseline_max_drawdown']} | {row['delta_final_equity']} | {row['delta_mdd']} | {row['trade_count']} | {row['joint_target_met']} |"
        )
    lines.extend(["", "Split/OOS metrics:", "", "| Policy | Window | Final | Return | MDD |", "| --- | --- | ---: | ---: | ---: |"])
    for row in split:
        lines.append(f"| `{row['policy_variant_id']}` | {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(["", "Cost/slippage stress:", "", "| Policy | Cost bps | Stressed Final | Beats QQQ |", "| --- | ---: | ---: | ---: |"])
    for row in cost:
        lines.append(f"| `{row['policy_variant_id']}` | {row['round_trip_cost_bps']} | {row['stressed_final_equity']} | {row['beats_qqq_after_stress']} |")
    lines.extend(["", "Failure decomposition:", ""])
    for row in attr[:34]:
        lines.append(f"- `{row['failure_area']}`: {row.get('reason', row.get('policy_variant_id', ''))} count={row.get('row_count','')} pnl={row.get('pnl_sum','')} cagr={row.get('cagr','')} mdd={row.get('max_drawdown','')}")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. This task stops treating all candidates as one game.",
            "2. It splits trades into winner, cyclical, speculative, and defensive sleeves.",
            "3. Each sleeve receives a different playbook and risk budget.",
            "4. The replay is still diagnostic and does not approve strategy.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1808_trade_drawdown_attribution_ledger.csv`",
            "- `task1809_sleeve_taxonomy_contract.csv`",
            "- `task1810_regime_classifier_panel.csv`",
            "- `task1811_l1_source_routing_contract.csv`",
            "- `task1812_l2_sleeve_meaning_panel.csv`",
            "- `task1813_l3_sleeve_relation_edges.csv`",
            "- `task1814_l4_sleeve_thesis_cards.csv`",
            "- `task1815_sleeve_risk_budget.csv`",
            "- `task1816_l5_sleeve_action_rules.csv`",
            "- `task1817_1820_sleeve_playbooks.csv`",
            "- `task1821_frozen_policy_config.csv`",
            "- `task1822_controlled_sleeve_replay_trades.csv/equity`",
            "- `task1823_sleeve_replay_metrics.csv/split_oos/cost_stress`",
            "- `task1824_failure_attribution.csv`",
            "- `task1825_expert_audit.csv`",
            "- `task1826_acceptance_gate.csv`",
            "- `task1827_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1808_1827_sleeve_split_playbook_validate.py`",
            "",
            "```text",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "```",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    raw_panel = load_panel()
    contracts = sleeve_contract_rows()
    regimes = regime_panel(raw_panel)
    meaning = enrich_panel(raw_panel, regimes)
    edges = relation_edges(meaning)
    cards = thesis_cards(meaning, edges)
    budgets = risk_budget_rows(meaning)
    actions = action_rules_rows()
    playbooks = playbook_rows()
    config = frozen_config_rows()
    trades, equity = replay_budget(budgets)
    metric_rows = metrics(trades, equity)
    split = split_rows(equity)
    cost = cost_stress_rows(metric_rows)
    ledger = attribution_ledger(meaning, trades, equity)
    attr = failure_attribution(budgets, trades, metric_rows)
    experts = expert_rows()
    gate, closeout = gate_closeout(metric_rows)
    outputs = [
        ("task1808_trade_drawdown_attribution_ledger.csv", ledger),
        ("task1809_sleeve_taxonomy_contract.csv", contracts),
        ("task1810_regime_classifier_panel.csv", regimes),
        ("task1811_l1_source_routing_contract.csv", source_routing_rows()),
        ("task1812_l2_sleeve_meaning_panel.csv", meaning),
        ("task1813_l3_sleeve_relation_edges.csv", edges),
        ("task1814_l4_sleeve_thesis_cards.csv", cards),
        ("task1815_sleeve_risk_budget.csv", budgets),
        ("task1816_l5_sleeve_action_rules.csv", actions),
        ("task1817_1820_sleeve_playbooks.csv", playbooks),
        ("task1821_frozen_policy_config.csv", config),
        ("task1822_controlled_sleeve_replay_trades.csv", trades),
        ("task1822_controlled_sleeve_replay_equity.csv", equity),
        ("task1823_sleeve_replay_metrics.csv", metric_rows),
        ("task1823_split_oos_metrics.csv", split),
        ("task1823_cost_stress_metrics.csv", cost),
        ("task1824_failure_attribution.csv", attr),
        ("task1825_expert_audit.csv", experts),
        ("task1826_acceptance_gate.csv", gate),
        ("task1827_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task1827_closeout.json", closeout[0])
    write_report(metric_rows, split, cost, attr, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1808_1827] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
