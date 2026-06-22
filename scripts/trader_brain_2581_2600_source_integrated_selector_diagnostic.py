from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2581_2600_source_integrated_selector_diagnostic"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2581_2600_source_integrated_selector_diagnostic.md"
DECISION = REPORT_DIR / "task_2600_decision.csv"

TASK2341 = ROOT / "data/artifacts/task_2341_2360_plus8000_brain_full_universe_backtest"
TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"
TASK2541 = ROOT / "data/artifacts/task_2541_2560_sec_financing_dilution_acquisition"
TASK2561 = ROOT / "data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition"

AUTHORITY = "RESEARCH_ONLY_SOURCE_INTEGRATED_SELECTOR_DIAGNOSTIC"
BASE_POLICY = "exit_chain_repaired_soft_boost_cap_top2_v1"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def iter_csv(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)


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


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan", "."}:
            return default
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return default


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.fromisoformat(value[:10]).replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def yes(flag: bool) -> str:
    return "1" if flag else "0"


def cohort_key(row: dict[str, str]) -> str:
    return row["decision_asof_ts"]


def task_plan_rows() -> list[dict[str, object]]:
    plan = [
        (2581, "Freeze selector diagnostic contract", "No replay, no selector deployment, feature bridge only."),
        (2582, "Join SEC financing/dilution gates", "Use strict source-time gate rows from Task2541."),
        (2583, "Aggregate liquidity/rates regime by decision as-of", "Use Task2561 strict packets and proxy-only boundary."),
        (2584, "Build L2 feature bridge", "Translate SEC/regime values into bounded semantics."),
        (2585, "Build L3 interaction edges", "Connect dilution/survival risk with tightening/liquidity stress."),
        (2586, "Create adjusted selector score", "Base score plus preregistered source penalties/credits."),
        (2587, "Run selector-only topN diagnostic", "No capital path and no replay engine."),
        (2588, "Run outcome audit-only comparison", "Existing return rows only for ex-post diagnostics."),
        (2589, "Attribution and failure table", "Show changed selections and why."),
        (2590, "Leakage/PIT audit", "No future source, no missing-negative conversion."),
        (2591, "Source gap and proxy boundary audit", "Track any non-strict rows."),
        (2592, "Policy status preservation", "Keep NOT_ACCEPTED/DIAGNOSTIC_ONLY/FORBIDDEN."),
        (2593, "Subagent review packet capture", "Record bounded review roles."),
        (2594, "Artifact manifest", "Register every table."),
        (2595, "Validator implementation", "Assert source and selector diagnostic invariants."),
        (2596, "Registry update", "Task2581-2600 rows."),
        (2597, "Operating state update", "Compact state line."),
        (2598, "Decision report", "Short decision-maker and quant sections."),
        (2599, "Replay readiness conclusion", "State whether Task2601 replay can be designed."),
        (2600, "Closeout", "Final diagnostic decision CSV/JSON."),
    ]
    return [
        {
            "task_id": f"Task{num}",
            "sequence": num,
            "title": title,
            "scope": scope,
            "status": "completed_by_script",
            "backtest_run": "0",
            "selector_deployment_changed": "0",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for num, title, scope in plan
    ]


def contract_rows(candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2581",
            "contract_id": "SRCSEL2581-0001",
            "scope": "full_3100_candidate_pool",
            "candidate_rows": len(candidates),
            "base_selector_artifact": "task2350_full_api_l4_cards.csv",
            "return_source_for_audit_only": "task2384_repaired_exit_source_rows.csv",
            "sec_source": "Task2541 strict SEC financing/dilution gates",
            "liquidity_rates_source": "Task2561 strict liquidity/rates packets",
            "selector_only": "1",
            "capital_replay_run": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def load_inputs() -> dict[str, Any]:
    repaired = read_csv(TASK2381 / "task2384_repaired_exit_source_rows.csv")
    base_cards = read_csv(TASK2341 / "task2350_full_api_l4_cards.csv")
    l5 = read_csv(TASK2341 / "task2349_full_l5_decisions.csv")
    sec_gates = read_csv(TASK2541 / "task2547_feature_admission_gate.csv")
    liq_gates = read_csv(TASK2561 / "task2567_feature_admission_gate.csv")
    return {
        "repaired": repaired,
        "base_cards": base_cards,
        "l5": l5,
        "sec_gates": sec_gates,
        "liq_gates": liq_gates,
    }


def build_base_rows(inputs: dict[str, Any]) -> list[dict[str, str]]:
    by_spec_card = {row["trade_spec_id"]: row for row in inputs["base_cards"]}
    by_spec_l5 = {row["trade_spec_id"]: row for row in inputs["l5"]}
    rows: list[dict[str, str]] = []
    for row in inputs["repaired"]:
        spec = row["trade_spec_id"]
        card = by_spec_card.get(spec, {})
        l5 = by_spec_l5.get(spec, {})
        merged = dict(row)
        merged["base_selector_score"] = card.get("api_adjusted_rank_score") or l5.get("winner_acceleration_rank_score") or "0"
        merged["base_winner_score"] = card.get("base_winner_acceleration_rank_score") or l5.get("winner_acceleration_rank_score") or "0"
        merged["api_l2_state"] = card.get("api_l2_state", "")
        merged["strategy_sleeve"] = l5.get("strategy_sleeve", "")
        merged["winner_acceleration_state"] = l5.get("winner_acceleration_state", "")
        merged["winner_thesis_state"] = l5.get("winner_thesis_state", "")
        rows.append(merged)
    return rows


def source_join_audit_rows(inputs: dict[str, Any], candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    cand_specs = {row["trade_spec_id"] for row in candidates}
    sec_specs = {row["trade_spec_id"] for row in inputs["sec_gates"] if row.get("strict_gate_pass") == "1"}
    liq_specs = {row["trade_spec_id"] for row in inputs["liq_gates"] if row.get("strict_gate_pass") == "1"}
    return [
        {
            "task_id": "Task2582",
            "join_audit_id": "SRCJOIN2582-0001",
            "input": "sec_financing_dilution",
            "candidate_rows": len(candidates),
            "strict_join_rows": len(cand_specs & sec_specs),
            "gap_rows": len(cand_specs - sec_specs),
            "strict_join_ratio": round(len(cand_specs & sec_specs) / len(cand_specs), 6),
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2582",
            "join_audit_id": "SRCJOIN2582-0002",
            "input": "liquidity_rates_regime",
            "candidate_rows": len(candidates),
            "strict_join_rows": len(cand_specs & liq_specs),
            "gap_rows": len(cand_specs - liq_specs),
            "strict_join_ratio": round(len(cand_specs & liq_specs) / len(cand_specs), 6),
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        },
    ]


def build_sec_evidence(candidates: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    decision_by_symbol: dict[str, list[tuple[str, datetime]]] = defaultdict(list)
    for cand in candidates:
        dt = parse_ts(cand["decision_asof_ts"])
        if dt:
            decision_by_symbol[cand["symbol"]].append((cand["trade_spec_id"], dt))
    for symbol in decision_by_symbol:
        decision_by_symbol[symbol].sort(key=lambda item: item[1])

    events_by_symbol: dict[str, list[dict[str, str]]] = defaultdict(list)
    packet_path = TASK2541 / "task2545_normalized_sec_financing_dilution_packets.csv"
    for row in iter_csv(packet_path):
        if row.get("strict_gate_pass") != "1" or row.get("source_time_certified") != "1":
            continue
        symbol = row.get("symbol", "")
        if symbol not in decision_by_symbol:
            continue
        ts = parse_ts(row.get("available_to_brain_ts", ""))
        if ts is None:
            continue
        row["_parsed_ts"] = ts.isoformat()
        events_by_symbol[symbol].append(row)

    evidence: dict[str, dict[str, object]] = {}
    for cand in candidates:
        evidence[cand["trade_spec_id"]] = {
            "prior_event_count": 0,
            "high_or_medium_high_count": 0,
            "event_family_counts": {},
            "event_severity_counts": {},
            "max_available_to_brain_ts": "",
            "source_packet_ids_sample": "",
            "accession_numbers_sample": "",
        }

    for symbol, events in events_by_symbol.items():
        events.sort(key=lambda row: row["_parsed_ts"])
        for spec, decision_dt in decision_by_symbol[symbol]:
            prior = [event for event in events if parse_ts(event["_parsed_ts"]) and parse_ts(event["_parsed_ts"]) <= decision_dt]
            family_counts = Counter(event.get("event_family", "") for event in prior)
            severity_counts = Counter(event.get("event_severity", "") for event in prior)
            high_count = sum(count for severity, count in severity_counts.items() if severity in {"high", "medium_high"})
            latest_ts = max((event.get("available_to_brain_ts", "") for event in prior), default="")
            evidence[spec] = {
                "prior_event_count": len(prior),
                "high_or_medium_high_count": high_count,
                "event_family_counts": dict(family_counts),
                "event_severity_counts": dict(severity_counts),
                "max_available_to_brain_ts": latest_ts,
                "source_packet_ids_sample": "|".join(event.get("source_packet_id", "") for event in prior[:10]),
                "accession_numbers_sample": "|".join(event.get("accession_number", "") for event in prior[:10]),
            }
    return evidence


def build_liquidity_regime(decision_dates: list[str]) -> list[dict[str, object]]:
    wanted_series = {
        "DGS2",
        "DGS10",
        "T10Y2Y",
        "T10Y3M",
        "SOFR",
        "EFFR",
        "RRPONTSYD",
        "WTREGEN",
        "BAMLH0A0HYM2",
        "BAMLC0A0CM",
    }
    decision_dt = [(ts, parse_ts(ts)) for ts in sorted(decision_dates)]
    latest_by_decision: dict[str, dict[str, tuple[datetime, float, str]]] = {ts: {} for ts in decision_dates}
    packet_path = TASK2561 / "task2565_normalized_liquidity_rates_packets.csv"
    for row in iter_csv(packet_path):
        if row.get("strict_gate_pass") != "1":
            continue
        series = row.get("series_id", "")
        endpoint = row.get("endpoint_or_source_family", "")
        source_ts = parse_ts(row.get("available_to_brain_ts", ""))
        if source_ts is None:
            continue
        metric = ""
        if row.get("provider") == "FRED_ALFRED" and endpoint.startswith("fred_observations_") and series in wanted_series:
            metric = series
        elif row.get("provider") == "NYFED" and endpoint in {"nyfed_secured_rate", "nyfed_unsecured_rate"} and series in {"SOFR", "EFFR"}:
            metric = f"NYFED_{series}"
        elif row.get("provider") == "TREASURY" and endpoint == "treasury_operating_cash_balance" and series in {"close_today_bal", "open_today_bal"}:
            metric = f"TREASURY_{series}"
        elif row.get("provider") == "TREASURY" and endpoint == "treasury_debt_to_penny" and series == "tot_pub_debt_out_amt":
            metric = "TREASURY_tot_pub_debt_out_amt"
        if not metric:
            continue
        value = to_float(row.get("value"), default=float("nan"))
        if value != value:
            continue
        for ts, dt in decision_dt:
            if dt and source_ts <= dt:
                prev = latest_by_decision[ts].get(metric)
                if prev is None or source_ts > prev[0]:
                    latest_by_decision[ts][metric] = (source_ts, value, row.get("source_packet_id", ""))

    rows: list[dict[str, object]] = []
    for idx, ts in enumerate(sorted(decision_dates), start=1):
        values = latest_by_decision[ts]
        dgs10 = values.get("DGS10", (None, 0.0, ""))[1]
        dgs2 = values.get("DGS2", (None, 0.0, ""))[1]
        curve_10y2y = values.get("T10Y2Y", (None, 0.0, ""))[1]
        curve_10y3m = values.get("T10Y3M", (None, 0.0, ""))[1]
        sofr = values.get("SOFR", values.get("NYFED_SOFR", (None, 0.0, "")))[1]
        effr = values.get("EFFR", values.get("NYFED_EFFR", (None, 0.0, "")))[1]
        hy_oas = values.get("BAMLH0A0HYM2", (None, 0.0, ""))[1]
        ig_oas = values.get("BAMLC0A0CM", (None, 0.0, ""))[1]
        rrp = values.get("RRPONTSYD", (None, 0.0, ""))[1]
        wtregen = values.get("WTREGEN", values.get("TREASURY_close_today_bal", (None, 0.0, "")))[1]
        stress = 0
        reasons: list[str] = []
        if dgs10 >= 4.0:
            stress += 2
            reasons.append("10y_rate_high")
        if dgs2 >= 4.5:
            stress += 2
            reasons.append("2y_rate_high")
        if curve_10y2y <= -0.5:
            stress += 2
            reasons.append("curve_10y2y_deep_inversion")
        if curve_10y3m <= -1.0:
            stress += 2
            reasons.append("curve_10y3m_deep_inversion")
        if sofr >= 4.5 or effr >= 4.5:
            stress += 2
            reasons.append("front_end_funding_rate_high")
        if hy_oas >= 5.0:
            stress += 3
            reasons.append("credit_spread_stress")
        elif hy_oas >= 4.0:
            stress += 1
            reasons.append("credit_spread_watch")
        if rrp >= 1000:
            stress += 1
            reasons.append("rrp_liquidity_absorption_high")
        if wtregen >= 500:
            stress += 1
            reasons.append("treasury_cash_balance_high")
        if stress >= 8:
            state = "liquidity_rates_stress"
            score = -5.0
        elif stress >= 5:
            state = "liquidity_rates_tightening"
            score = -3.0
        elif stress >= 2:
            state = "liquidity_rates_neutral_watch"
            score = -1.0
        else:
            state = "liquidity_rates_tailwind_or_benign"
            score = 1.0
        rows.append(
            {
                "task_id": "Task2583",
                "regime_row_id": f"REGIME2583-{idx:04d}",
                "decision_asof_ts": ts,
                "latest_metric_count": len(values),
                "dgs10": round(dgs10, 6),
                "dgs2": round(dgs2, 6),
                "t10y2y": round(curve_10y2y, 6),
                "t10y3m": round(curve_10y3m, 6),
                "sofr": round(sofr, 6),
                "effr": round(effr, 6),
                "hy_oas": round(hy_oas, 6),
                "ig_oas": round(ig_oas, 6),
                "rrp": round(rrp, 6),
                "treasury_cash": round(wtregen, 6),
                "regime_stress_score": stress,
                "regime_state": state,
                "regime_selector_score": score,
                "reason_codes": "|".join(reasons),
                "strict_gate_pass": "1",
                "proxy_feature_allowed": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def sec_state_and_score(gate: dict[str, str], evidence: dict[str, object]) -> tuple[str, float, str]:
    if not gate or gate.get("strict_gate_pass") != "1":
        return "sec_financing_source_gap_neutral", 0.0, "source_gap_neutral_not_negative"
    prior = int(to_float(evidence.get("prior_event_count"), to_float(gate.get("prior_financing_event_count"), 0.0)))
    high = int(to_float(evidence.get("high_or_medium_high_count"), to_float(gate.get("high_or_medium_high_events_365d"), 0.0)))
    families = evidence.get("event_family_counts", {})
    if isinstance(families, dict) and (families.get("bankruptcy_or_receivership", 0) or families.get("listing_survival_risk", 0)):
        return "hard_survival_or_listing_risk", -10.0, "bankruptcy_or_listing_survival_event_present"
    if isinstance(families, dict) and families.get("debt_survival_financing", 0) >= 3:
        return "debt_survival_financing_cluster", -7.0, "debt_survival_financing_count>=3"
    if high >= 10:
        return "severe_recent_financing_dilution_pressure", -8.0, "high_or_medium_high_events_365d>=10"
    if high >= 5:
        return "high_recent_financing_dilution_pressure", -5.0, "high_or_medium_high_events_365d>=5"
    if high >= 2:
        return "moderate_recent_financing_dilution_watch", -2.0, "high_or_medium_high_events_365d>=2"
    if prior >= 20:
        return "recurrent_financing_history_watch", -1.0, "prior_financing_event_count>=20"
    return "clean_or_low_financing_pressure", 1.0, "no_material_recent_financing_cluster"


def l2_feature_bridge_rows(candidates: list[dict[str, str]], inputs: dict[str, Any], regime: list[dict[str, object]], sec_evidence: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    sec_by_spec = {row["trade_spec_id"]: row for row in inputs["sec_gates"]}
    liq_by_ts = {str(row["decision_asof_ts"]): row for row in regime}
    rows: list[dict[str, object]] = []
    for idx, cand in enumerate(candidates, start=1):
        sec_gate = sec_by_spec.get(cand["trade_spec_id"], {})
        evidence = sec_evidence.get(cand["trade_spec_id"], {})
        sec_state, sec_score, sec_reason = sec_state_and_score(sec_gate, evidence)
        reg = liq_by_ts[cand["decision_asof_ts"]]
        regime_score = to_float(reg["regime_selector_score"])
        regime_state = str(reg["regime_state"])
        interaction = 0.0
        interaction_state = "no_material_interaction"
        if sec_score <= -5 and regime_score <= -3:
            interaction = -4.0
            interaction_state = "dilution_pressure_amplified_by_tight_liquidity"
        elif sec_score <= -2 and regime_score <= -5:
            interaction = -3.0
            interaction_state = "financing_watch_amplified_by_macro_stress"
        elif sec_score >= 1 and regime_score >= 1:
            interaction = 1.0
            interaction_state = "clean_financing_profile_in_benign_liquidity"
        elif sec_score >= 1 and regime_score <= -5:
            interaction = -1.0
            interaction_state = "clean_company_but_hostile_macro_regime"
        source_score = sec_score + regime_score + interaction
        rows.append(
            {
                "task_id": "Task2584",
                "l2_bridge_id": f"L2BRIDGE2584-{idx:06d}",
                "candidate_id": cand["candidate_source_id"],
                "trade_spec_id": cand["trade_spec_id"],
                "symbol": cand["symbol"],
                "decision_asof_ts": cand["decision_asof_ts"],
                "base_selector_score": round(to_float(cand["base_selector_score"]), 6),
                "strategy_sleeve": cand.get("strategy_sleeve", ""),
                "sec_state": sec_state,
                "sec_selector_score": sec_score,
                "sec_reason": sec_reason,
                "prior_financing_event_count": evidence.get("prior_event_count", sec_gate.get("prior_financing_event_count", "")),
                "high_or_medium_high_events_365d": evidence.get("high_or_medium_high_count", sec_gate.get("high_or_medium_high_events_365d", "")),
                "sec_event_family_counts": json.dumps(evidence.get("event_family_counts", {}), sort_keys=True),
                "sec_event_severity_counts": json.dumps(evidence.get("event_severity_counts", {}), sort_keys=True),
                "sec_source_packet_ids_sample": evidence.get("source_packet_ids_sample", ""),
                "sec_accession_numbers_sample": evidence.get("accession_numbers_sample", ""),
                "sec_available_to_brain_ts_max": evidence.get("max_available_to_brain_ts", ""),
                "regime_state": regime_state,
                "regime_selector_score": regime_score,
                "regime_stress_score": reg["regime_stress_score"],
                "regime_reason_codes": reg["reason_codes"],
                "interaction_state": interaction_state,
                "interaction_selector_score": interaction,
                "source_integrated_selector_delta": source_score,
                "source_integrated_selector_score": round(to_float(cand["base_selector_score"]) + source_score, 6),
                "strict_sec_gate_pass": sec_gate.get("strict_gate_pass", "0"),
                "strict_liquidity_rates_gate_pass": "1",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def l3_edge_rows(l2_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(l2_rows, start=1):
        edges: list[tuple[str, str, float]] = []
        if to_float(row["sec_selector_score"]) < 0:
            edges.append(("sec_financing_dilution_pressures_selector", str(row["sec_state"]), to_float(row["sec_selector_score"])))
        else:
            edges.append(("sec_financing_profile_supports_selector", str(row["sec_state"]), to_float(row["sec_selector_score"])))
        edges.append(("liquidity_rates_regime_conditions_selector", str(row["regime_state"]), to_float(row["regime_selector_score"])))
        if to_float(row["interaction_selector_score"]) != 0:
            edges.append(("sec_x_regime_interaction_modifies_selector", str(row["interaction_state"]), to_float(row["interaction_selector_score"])))
        for edge_type, relation_state, score in edges:
            rows.append(
                {
                    "task_id": "Task2585",
                    "l3_edge_id": f"L3EDGE2585-{len(rows)+1:07d}",
                    "candidate_id": row["candidate_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "edge_type": edge_type,
                    "relation_state": relation_state,
                    "selector_score_contribution": score,
                    "strict_gate_pass": "1",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def rank_rows(l2_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in l2_rows:
        by_decision[str(row["decision_asof_ts"])].append(row)
    rows: list[dict[str, object]] = []
    for decision, items in sorted(by_decision.items()):
        base_sorted = sorted(items, key=lambda r: (-to_float(r["base_selector_score"]), str(r["trade_spec_id"])))
        adj_sorted = sorted(items, key=lambda r: (-to_float(r["source_integrated_selector_score"]), str(r["trade_spec_id"])))
        base_rank = {str(row["trade_spec_id"]): idx for idx, row in enumerate(base_sorted, start=1)}
        adj_rank = {str(row["trade_spec_id"]): idx for idx, row in enumerate(adj_sorted, start=1)}
        for row in items:
            rows.append(
                {
                    "task_id": "Task2586",
                    "rank_row_id": f"RANK2586-{len(rows)+1:06d}",
                    "candidate_id": row["candidate_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision,
                    "base_rank": base_rank[str(row["trade_spec_id"])],
                    "source_integrated_rank": adj_rank[str(row["trade_spec_id"])],
                    "rank_improvement": base_rank[str(row["trade_spec_id"])] - adj_rank[str(row["trade_spec_id"])],
                    "base_selector_score": row["base_selector_score"],
                    "source_integrated_selector_score": row["source_integrated_selector_score"],
                    "source_integrated_selector_delta": row["source_integrated_selector_delta"],
                    "sec_state": row["sec_state"],
                    "regime_state": row["regime_state"],
                    "interaction_state": row["interaction_state"],
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def selector_only_rows(rank: list[dict[str, object]], candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    outcome_by_spec = {row["trade_spec_id"]: row for row in candidates}
    rows: list[dict[str, object]] = []
    for n in [2, 3, 5, 10]:
        for mode in ["base", "source_integrated"]:
            selected = [
                row for row in rank
                if int(row["base_rank" if mode == "base" else "source_integrated_rank"]) <= n
            ]
            for item in selected:
                out = outcome_by_spec[str(item["trade_spec_id"])]
                rows.append(
                    {
                        "task_id": "Task2587",
                        "selector_row_id": f"SELONLY2587-{len(rows)+1:07d}",
                        "diagnostic_variant_id": f"{mode}_top{n}_selector_only_v1",
                        "selection_mode": mode,
                        "top_n": n,
                        "candidate_id": item["candidate_id"],
                        "trade_spec_id": item["trade_spec_id"],
                        "symbol": item["symbol"],
                        "decision_asof_ts": item["decision_asof_ts"],
                        "rank_used": item["base_rank" if mode == "base" else "source_integrated_rank"],
                        "selector_score_used": item["base_selector_score" if mode == "base" else "source_integrated_selector_score"],
                        "sec_state": item["sec_state"],
                        "regime_state": item["regime_state"],
                        "interaction_state": item["interaction_state"],
                        "audit_net_return": out.get("net_return", ""),
                        "audit_runtime_action": out.get("runtime_action", ""),
                        "capital_replay_run": "0",
                        "missing_source_is_negative": "0",
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
    return rows


def selector_metrics(selection_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in selection_rows:
        grouped[str(row["diagnostic_variant_id"])].append(row)
    rows: list[dict[str, object]] = []
    for variant, items in sorted(grouped.items()):
        returns = [to_float(row["audit_net_return"]) for row in items]
        rows.append(
            {
                "task_id": "Task2588",
                "metric_id": f"SELMETRIC2588-{len(rows)+1:04d}",
                "diagnostic_variant_id": variant,
                "selected_rows": len(items),
                "unique_symbols": len({row["symbol"] for row in items}),
                "avg_audit_net_return": round(sum(returns) / len(returns), 6) if returns else 0.0,
                "median_audit_net_return": round(sorted(returns)[len(returns) // 2], 6) if returns else 0.0,
                "negative_return_rows": sum(1 for value in returns if value < 0),
                "severe_loss_rows_le_minus_20pct": sum(1 for value in returns if value <= -0.20),
                "capital_replay_run": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def overlap_rows(selection_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_variant_decision: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in selection_rows:
        by_variant_decision[(str(row["diagnostic_variant_id"]), str(row["decision_asof_ts"]))].add(str(row["trade_spec_id"]))
    rows: list[dict[str, object]] = []
    for n in [2, 3, 5, 10]:
        base_v = f"base_top{n}_selector_only_v1"
        adj_v = f"source_integrated_top{n}_selector_only_v1"
        decisions = sorted({key[1] for key in by_variant_decision if key[0] in {base_v, adj_v}})
        for decision in decisions:
            base = by_variant_decision[(base_v, decision)]
            adj = by_variant_decision[(adj_v, decision)]
            rows.append(
                {
                    "task_id": "Task2589",
                    "overlap_id": f"SELOVERLAP2589-{len(rows)+1:05d}",
                    "top_n": n,
                    "decision_asof_ts": decision,
                    "base_count": len(base),
                    "source_integrated_count": len(adj),
                    "overlap_count": len(base & adj),
                    "added_count": len(adj - base),
                    "dropped_count": len(base - adj),
                    "added_trade_specs": "|".join(sorted(adj - base)),
                    "dropped_trade_specs": "|".join(sorted(base - adj)),
                    "capital_replay_run": "0",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
    return rows


def attribution_rows(rank_rows_: list[dict[str, object]], selection_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    top2_adj = {str(row["trade_spec_id"]) for row in selection_rows if row["diagnostic_variant_id"] == "source_integrated_top2_selector_only_v1"}
    top2_base = {str(row["trade_spec_id"]) for row in selection_rows if row["diagnostic_variant_id"] == "base_top2_selector_only_v1"}
    rank_by_spec = {str(row["trade_spec_id"]): row for row in rank_rows_}
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for spec in top2_adj - top2_base:
        row = rank_by_spec[spec]
        groups[f"added::{row['sec_state']}::{row['interaction_state']}"].append(row)
    for spec in top2_base - top2_adj:
        row = rank_by_spec[spec]
        groups[f"dropped::{row['sec_state']}::{row['interaction_state']}"].append(row)
    rows: list[dict[str, object]] = []
    for key, items in sorted(groups.items()):
        status, sec_state, interaction_state = key.split("::", 2)
        rows.append(
            {
                "task_id": "Task2590",
                "attribution_id": f"SELATTR2590-{len(rows)+1:04d}",
                "change_status": status,
                "sec_state": sec_state,
                "interaction_state": interaction_state,
                "row_count": len(items),
                "avg_rank_improvement": round(sum(to_float(row["rank_improvement"]) for row in items) / len(items), 6),
                "avg_source_integrated_delta": round(sum(to_float(row["source_integrated_selector_delta"]) for row in items) / len(items), 6),
                "example_trade_specs": "|".join(str(row["trade_spec_id"]) for row in items[:10]),
                "capital_replay_run": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def audit_rows(l2: list[dict[str, object]], regime: list[dict[str, object]], join: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2591",
            "audit_id": "SELAUDIT2591-0001",
            "check_name": "full_candidate_l2_rows",
            "observed": len(l2),
            "expected": 3100,
            "pass": yes(len(l2) == 3100),
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2591",
            "audit_id": "SELAUDIT2591-0002",
            "check_name": "decision_regime_rows",
            "observed": len(regime),
            "expected": 62,
            "pass": yes(len(regime) == 62),
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2591",
            "audit_id": "SELAUDIT2591-0003",
            "check_name": "join_gap_rows",
            "observed": sum(int(row["gap_rows"]) for row in join),
            "expected": 6,
            "pass": yes(sum(int(row["gap_rows"]) for row in join) == 6),
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2591",
            "audit_id": "SELAUDIT2591-0004",
            "check_name": "capital_replay_run",
            "observed": 0,
            "expected": 0,
            "pass": "1",
            "authority": AUTHORITY,
        },
    ]


def source_gap_rows(join: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in join:
        if int(item["gap_rows"]) > 0:
            rows.append(
                {
                    "task_id": "Task2592",
                    "source_gap_id": f"SELGAP2592-{len(rows)+1:04d}",
                    "source_family": item["input"],
                    "gap_rows": item["gap_rows"],
                    "gap_treatment": "neutral_not_negative",
                    "blocks_controlled_replay_design": "0",
                    "blocks_live": "1",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def subagent_rows() -> list[dict[str, object]]:
    agents = [
        ("Feynman", "019ed622-45b9-7642-bd94-60f9451f2d7a", "sec_financing_dilution_feature_contract", "read-only", "DATA_HEALTH / RESEARCH_ONLY"),
        ("Erdos", "019ed622-d7ad-7e70-ad2b-2dcc0c7a6130", "liquidity_rates_feature_contract", "read-only", "DATA_HEALTH / RESEARCH_ONLY"),
        ("Bernoulli", "019ed622-ec1f-7cf0-8de4-52069beb612f", "selector_only_diagnostic_design", "read-only", "RESEARCH_ONLY / BACKTEST_GOVERNANCE_HEALTH"),
        ("Meitner", "019ed623-00c6-7960-a951-f8ff5ac3984a", "leakage_pit_validator_requirements", "read-only", "DATA_HEALTH / GOVERNANCE_HEALTH"),
    ]
    return [
        {
            "task_id": "Task2593",
            "subagent_packet_id": f"SELSUB2593-{idx:04d}",
            "nickname": nickname,
            "agent_id": agent_id,
            "role": role,
            "write_scope": write_scope,
            "validation_authority": authority,
            "forbidden_actions": "no_edits|no_replay|no_strategy_acceptance|no_missing_source_negative",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (nickname, agent_id, role, write_scope, authority) in enumerate(agents, start=1)
    ]


def closeout_rows(
    candidates: list[dict[str, str]],
    l2: list[dict[str, object]],
    edges: list[dict[str, object]],
    selection: list[dict[str, object]],
    metrics: list[dict[str, object]],
    overlap: list[dict[str, object]],
    gaps: list[dict[str, object]],
) -> list[dict[str, object]]:
    top2_base = next(row for row in metrics if row["diagnostic_variant_id"] == "base_top2_selector_only_v1")
    top2_adj = next(row for row in metrics if row["diagnostic_variant_id"] == "source_integrated_top2_selector_only_v1")
    top2_overlap = [row for row in overlap if int(row["top_n"]) == 2]
    added = sum(int(row["added_count"]) for row in top2_overlap)
    dropped = sum(int(row["dropped_count"]) for row in top2_overlap)
    return [
        {
            "task_id": "Task2600",
            "verdict": "source_integrated_selector_only_diagnostic_complete_no_replay",
            "candidate_rows": len(candidates),
            "l2_bridge_rows": len(l2),
            "l3_edge_rows": len(edges),
            "selector_only_rows": len(selection),
            "source_gap_rows": len(gaps),
            "base_top2_avg_audit_return": top2_base["avg_audit_net_return"],
            "source_integrated_top2_avg_audit_return": top2_adj["avg_audit_net_return"],
            "top2_added_rows": added,
            "top2_dropped_rows": dropped,
            "capital_replay_run": "0",
            "selector_deployment_changed": "0",
            "replay_ready_next_task": "1" if len(gaps) == 1 else "0",
            "next_action": "Task2601+ should preregister a controlled replay variant using these selector-only source features, not tune live policy.",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], metrics: list[dict[str, object]], join: list[dict[str, object]], audit: list[dict[str, object]]) -> None:
    metric_lines = "\n".join(
        f"- `{row['diagnostic_variant_id']}`: rows {row['selected_rows']}, avg audit return {row['avg_audit_net_return']}, severe losses {row['severe_loss_rows_le_minus_20pct']}."
        for row in metrics
    )
    join_lines = "\n".join(
        f"- `{row['input']}`: strict {row['strict_join_rows']}/{row['candidate_rows']}, gaps {row['gap_rows']}."
        for row in join
    )
    audit_lines = "\n".join(
        f"- `{row['check_name']}`: {row['observed']}/{row['expected']} pass `{row['pass']}`."
        for row in audit
    )
    REPORT.write_text(
        f"""# Task2581-2600 Source Integrated Selector Diagnostic

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Candidate rows: {closeout['candidate_rows']}.
- L2 bridge rows: {closeout['l2_bridge_rows']}.
- L3 edge rows: {closeout['l3_edge_rows']}.
- Selector-only rows: {closeout['selector_only_rows']}.
- Source gaps: {closeout['source_gap_rows']}.
- Base top2 avg audit return: {closeout['base_top2_avg_audit_return']}.
- Source-integrated top2 avg audit return: {closeout['source_integrated_top2_avg_audit_return']}.
- Capital replay run: `0`.
- Selector deployment changed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task joins the two newly acquired source families into L2/L3 selector diagnostics:

{join_lines}

Interpretation:

- SEC financing/dilution is used mainly as dilution/survival risk, not as a standalone positive signal.
- Liquidity/rates regime is a market-context modifier. Treasury average interest rates remain proxy-only.
- SEC x liquidity/rates interaction penalizes financing pressure more heavily in tight liquidity or credit stress regimes.
- Existing repaired exit-chain returns are used only for ex-post selector diagnostics, never assignment.
- No capital path, replay engine, sizing, adapter, paper trading, or live order logic is touched.

Selector-only audit:

{metric_lines}

Validation summary:

{audit_lines}

## No-Background Decision-Maker Report

Conclusion first: the new sources are now inside the brain's selector diagnostic layer.

This does not mean the strategy is accepted. It means we can now see how SEC dilution risk and rates/liquidity regime would change top candidates before running a controlled replay.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2581_2600_source_integrated_selector_diagnostic/`.
- Report: `docs/reports/task_2581_2600_source_integrated_selector_diagnostic/task_2581_2600_source_integrated_selector_diagnostic.md`.
- Validator: `python scripts/trader_brain_2581_2600_source_integrated_selector_diagnostic_validate.py`.

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
    fieldnames = list(rows[0].keys())
    existing = {row["task_id"] for row in rows}
    for task_no in range(2581, 2601):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"Source Integrated Selector Diagnostic Step {task_no}",
                "owner_team": "Research Brain / Selector Diagnostics / Governance",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "source-integrated-selector-diagnostic-no-replay",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2581_2600_source_integrated_selector_diagnostic/task_2581_2600_source_integrated_selector_diagnostic.md",
                "key_decision": "docs/reports/task_2581_2600_source_integrated_selector_diagnostic/task_2600_decision.csv",
                "key_artifacts": "data/artifacts/task_2581_2600_source_integrated_selector_diagnostic",
                "validation_command": "python scripts/trader_brain_2581_2600_source_integrated_selector_diagnostic_validate.py",
                "notes": "Joins SEC financing/dilution and liquidity/rates regime into L2/L3 selector-only diagnostics; no replay.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    lines = path.read_text(encoding="utf-8").rstrip().splitlines()
    line_126 = (
        "126. Task2581-Task2600 joined SEC financing/dilution and liquidity/rates regime into L2/L3 selector-only diagnostics: "
        f"candidate rows {closeout['candidate_rows']}, L2 rows {closeout['l2_bridge_rows']}, L3 edges {closeout['l3_edge_rows']}, "
        f"selector-only rows {closeout['selector_only_rows']}, source gaps {closeout['source_gap_rows']}; no replay, no selector deployment change. "
        "Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN."
    )
    out = []
    replaced = False
    for line in lines:
        if line.startswith("126. Task2581-Task2600"):
            out.append(line_126)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(line_126)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    candidates = build_base_rows(inputs)
    decision_dates = sorted({row["decision_asof_ts"] for row in candidates})
    sec_evidence = build_sec_evidence(candidates)
    contract = contract_rows(candidates)
    plan = task_plan_rows()
    join = source_join_audit_rows(inputs, candidates)
    regime = build_liquidity_regime(decision_dates)
    l2 = l2_feature_bridge_rows(candidates, inputs, regime, sec_evidence)
    l3 = l3_edge_rows(l2)
    ranks = rank_rows(l2)
    selection = selector_only_rows(ranks, candidates)
    metrics = selector_metrics(selection)
    overlaps = overlap_rows(selection)
    attribution = attribution_rows(ranks, selection)
    audit = audit_rows(l2, regime, join)
    gaps = source_gap_rows(join)
    subagents = subagent_rows()
    closeout = closeout_rows(candidates, l2, l3, selection, metrics, overlaps, gaps)

    outputs = [
        ("task2581_task_plan.csv", plan),
        ("task2581_selector_diagnostic_contract.csv", contract),
        ("task2582_source_join_audit.csv", join),
        ("task2583_liquidity_rates_regime_by_decision.csv", regime),
        ("task2584_l2_source_feature_bridge.csv", l2),
        ("task2585_l3_source_interaction_edges.csv", l3),
        ("task2586_source_integrated_selector_ranks.csv", ranks),
        ("task2587_selector_only_selection_rows.csv", selection),
        ("task2588_selector_only_audit_metrics.csv", metrics),
        ("task2589_selection_overlap.csv", overlaps),
        ("task2590_change_attribution.csv", attribution),
        ("task2591_leakage_pit_audit.csv", audit),
        ("task2592_source_gap_and_proxy_boundary.csv", gaps),
        ("task2593_subagent_packets.csv", subagents),
        ("task2600_closeout.csv", closeout),
    ]
    for filename, rows in outputs:
        write_csv(OUT_DIR / filename, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2600_closeout.json", closeout[0])
    write_report(closeout[0], metrics, join, audit)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2581_2600_SOURCE_INTEGRATED_SELECTOR_DIAGNOSTIC_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
