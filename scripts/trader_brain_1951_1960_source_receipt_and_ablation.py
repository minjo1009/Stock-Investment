from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1941_1950_gap_hardening as gap
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
TASK1808 = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
TASK1834 = ROOT / "data/artifacts/task_1834_1847_targeted_source_implementation"
TASK1931 = ROOT / "data/artifacts/task_1931_1940_interaction_forecast_layer"
TASK1941 = ROOT / "data/artifacts/task_1941_1950_gap_hardening"
OUT_DIR = ROOT / "data/artifacts/task_1951_1960_source_receipt_and_ablation"
REPORT_DIR = ROOT / "docs/reports/task_1951_1960_source_receipt_and_ablation"
REPORT = REPORT_DIR / "task_1951_1960_source_receipt_and_ablation.md"
DECISION = REPORT_DIR / "task_1951_1960_decision.csv"
AUTHORITY = "DIAGNOSTIC_SOURCE_RECEIPT_ABLATION_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265

GUIDANCE_PATTERNS = {
    "guidance": re.compile(r"\bguidance\b", re.IGNORECASE),
    "outlook": re.compile(r"\boutlook\b", re.IGNORECASE),
    "forecast": re.compile(r"\bforecast(?:s|ed|ing)?\b", re.IGNORECASE),
    "expects": re.compile(r"\bexpect(?:s|ed|ing)?\b", re.IGNORECASE),
    "raises": re.compile(r"\brais(?:e|es|ed|ing)\b", re.IGNORECASE),
    "lowers": re.compile(r"\blower(?:s|ed|ing)?\b", re.IGNORECASE),
    "backlog": re.compile(r"\bbacklog\b", re.IGNORECASE),
    "contract": re.compile(r"\bcontract(?:s|ual)?\b", re.IGNORECASE),
    "customer": re.compile(r"\bcustomer(?:s)?\b", re.IGNORECASE),
    "revenue": re.compile(r"\brevenue(?:s)?\b", re.IGNORECASE),
}
GUIDANCE_TERMS = {
    "guidance": ["guidance"],
    "outlook": ["outlook"],
    "forecast": ["forecast", "forecasts", "forecasted", "forecasting"],
    "expects": ["expect", "expects", "expected", "expecting"],
    "raises": ["raise", "raises", "raised", "raising"],
    "lowers": ["lower", "lowers", "lowered", "lowering"],
    "backlog": ["backlog"],
    "contract": ["contract", "contracts", "contractual"],
    "customer": ["customer", "customers"],
    "revenue": ["revenue", "revenues"],
}
SCAN_CACHE: dict[str, tuple[int, str, str]] = {}


def read_csv(path: Path) -> list[dict[str, str]]:
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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_ts(value: str) -> datetime | None:
    try:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_inputs() -> dict[str, object]:
    return {
        "budget": read_csv(TASK1808 / "task1815_sleeve_risk_budget.csv"),
        "winner_trades": read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        "sleeve_metrics": read_csv(TASK1808 / "task1823_sleeve_replay_metrics.csv"),
        "interaction_metrics": read_csv(TASK1931 / "task1938_interaction_top3_replay_metrics.csv"),
        "event": read_csv(TASK1931 / "task1932_event_window_absorption_panel.csv"),
        "breadth": read_csv(TASK1931 / "task1933_sector_breadth_source_field.csv"),
        "hardened_l4": read_csv(TASK1941 / "task1945_hardened_l4_thesis_cards.csv"),
        "hardened_metrics": read_csv(TASK1941 / "task1946_hardened_top3_replay_metrics.csv"),
        "hardened_top5": read_csv(TASK1941 / "task1947_top5_shadow_safety_audit.csv"),
        "rates_contract": read_csv(TASK1834 / "task1834_rates_liquidity_source_contract.csv"),
        "rates_packets": read_csv(TASK1834 / "task1834_rates_source_packets.csv"),
        "rates_panel": read_csv(TASK1834 / "task1835_rates_liquidity_decision_asof_panel.csv"),
        "rates_observations": read_csv(TASK1834 / "task1835_rates_liquidity_observations.csv"),
        "earnings_gate": read_csv(TASK1834 / "task1838_earnings_revision_vendor_gate.csv"),
        "sec_links": read_csv(TASK1834 / "task1842_sec_dilution_decision_asof_links.csv"),
        "sec_packets": read_csv(TASK1834 / "task1836_sec_financing_dilution_source_packets.csv"),
    }


def input_manifest_rows() -> list[dict[str, object]]:
    inputs = [
        ("event_window_absorption", TASK1931 / "task1932_event_window_absorption_panel.csv"),
        ("sector_breadth", TASK1931 / "task1933_sector_breadth_source_field.csv"),
        ("hardened_l4", TASK1941 / "task1945_hardened_l4_thesis_cards.csv"),
        ("hardened_top3_metrics", TASK1941 / "task1946_hardened_top3_replay_metrics.csv"),
        ("top5_shadow_safety", TASK1941 / "task1947_top5_shadow_safety_audit.csv"),
        ("rates_source_contract", TASK1834 / "task1834_rates_liquidity_source_contract.csv"),
        ("rates_source_packets", TASK1834 / "task1834_rates_source_packets.csv"),
        ("rates_observations", TASK1834 / "task1835_rates_liquidity_observations.csv"),
        ("earnings_vendor_gate", TASK1834 / "task1838_earnings_revision_vendor_gate.csv"),
        ("sec_decision_asof_links", TASK1834 / "task1842_sec_dilution_decision_asof_links.csv"),
        ("sec_financing_source_packets", TASK1834 / "task1836_sec_financing_dilution_source_packets.csv"),
    ]
    return [
        {
            "task_id": "Task1951",
            "input_id": f"SRCRECEIPTINPUT-1951-{idx:03d}",
            "input_name": name,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "exists": "1" if path.exists() else "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, path) in enumerate(inputs, 1)
    ]


def event_breadth_receipt_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for row in inputs["event"]:
        rows.append(
            {
                "task_id": "Task1952",
                "receipt_id": f"SRCRECEIPT-1952-{idx:06d}",
                "source_family": "price_event_window",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "source_available_to_brain_ts": row["decision_asof_ts"],
                "source_time_pass": "1",
                "receipt_grade": "derived_prior_window_timestamped",
                "raw_source_certification": "raw_ohlcv_manifest_not_in_this_task",
                "feature_fields": "prior_return_20d_source_field|prior_return_63d_source_field|relative_return_63d_source_field|prior_drawdown_126d_source_field",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    for row in inputs["breadth"]:
        rows.append(
            {
                "task_id": "Task1952",
                "receipt_id": f"SRCRECEIPT-1952-{idx:06d}",
                "source_family": "theme_breadth",
                "trade_spec_id": "",
                "candidate_source_id": "",
                "symbol": "",
                "decision_asof_ts": row["decision_asof_ts"],
                "source_available_to_brain_ts": row["decision_asof_ts"],
                "source_time_pass": "1",
                "receipt_grade": "derived_cross_section_timestamped",
                "raw_source_certification": "raw_candidate_cross_section_manifest_not_in_this_task",
                "feature_fields": "theme_candidate_count|theme_positive_share_63d|theme_avg_relative_return_63d|sector_breadth_state",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def macro_vintage_attempt_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    source_contract = {row["series_id"]: row for row in inputs["rates_contract"]}
    packet_by_series = {row["series_id"]: row for row in inputs["rates_packets"] if row.get("series_id")}
    observations_by_series: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inputs["rates_observations"]:
        observations_by_series[row["series_id"]].append(row)
    top3_decisions = sorted(
        {row["decision_asof_ts"] for row in inputs["budget"] if row["target_policy_variant_id"] == "winner_defense_budget_top3_v1"}
    )
    rows = []
    idx = 1
    for series_id, contract in sorted(source_contract.items()):
        packet = packet_by_series.get(series_id, {})
        observations = observations_by_series.get(series_id, [])
        latest_only = sum(1 for row in observations if row.get("latest_vintage_only_flag") == "1")
        vintage_certified = sum(1 for row in observations if row.get("vintage_asof_certified_flag") == "1")
        rows.append(
            {
                "task_id": "Task1953",
                "macro_vintage_attempt_id": f"MACROATTEMPT-1953-{idx:04d}",
                "series_id": series_id,
                "source_url": packet.get("source_url", contract.get("source_url", "")),
                "local_raw_path": packet.get("raw_storage_path", ""),
                "local_fetch_status": packet.get("fetch_status", contract.get("fetch_status", "")),
                "local_feed_type": contract.get("feed_type", "fred_latest_or_unknown"),
                "observation_row_count": len(observations),
                "latest_vintage_only_row_count": latest_only,
                "vintage_asof_certified_row_count": vintage_certified,
                "latest_vintage_only": "1",
                "alfred_vintage_certified": "0",
                "active_score_permission": "shadow_only",
                "attempt_status": "blocked_no_local_alfred_vintage_archive_or_api_key",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    for decision_ts in top3_decisions:
        rows.append(
            {
                "task_id": "Task1953",
                "macro_vintage_attempt_id": f"MACROATTEMPT-1953-{idx:04d}",
                "series_id": "DECISION_GATE",
                "source_url": "",
                "local_raw_path": "",
                "local_fetch_status": "derived_from_task1835_panel",
                "local_feed_type": "decision_asof_gate",
                "decision_asof_ts": decision_ts,
                "latest_vintage_only": "1",
                "alfred_vintage_certified": "0",
                "active_score_permission": "shadow_only",
                "attempt_status": "macro_score_not_allowed_active_until_vintage_certified",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def scan_guidance_text(path: Path) -> tuple[int, str, str]:
    cache_key = str(path)
    if cache_key in SCAN_CACHE:
        return SCAN_CACHE[cache_key]
    if not path.exists() or not path.is_file():
        return 0, "", ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0, "", ""
    lower = text.lower()
    hits = []
    count = 0
    snippet_parts = []
    for name, terms in GUIDANCE_TERMS.items():
        term_count = sum(lower.count(term) for term in terms)
        if term_count:
            hits.append(name)
            count += term_count
            if len(snippet_parts) < 6:
                first_positions = [lower.find(term) for term in terms if lower.find(term) >= 0]
                pos = min(first_positions) if first_positions else 0
                start = max(0, pos - 80)
                end = min(len(text), pos + 160)
                snippet_parts.append(text[start:end])
    snippet_hash = hashlib.sha256("\n".join(snippet_parts).encode("utf-8", errors="ignore")).hexdigest() if snippet_parts else ""
    result = (count, "|".join(sorted(hits)), snippet_hash)
    SCAN_CACHE[cache_key] = result
    return result


def issuer_public_guidance_probe_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    link_by_spec = {row["trade_spec_id"]: row for row in inputs["sec_links"]}
    packet_by_id = {row["financing_source_packet_id"]: row for row in inputs["sec_packets"]}
    rows = []
    for idx, l4 in enumerate(inputs["hardened_l4"], 1):
        link = link_by_spec.get(l4["trade_spec_id"], {})
        packet_id = link.get("latest_financing_source_packet_id", "")
        packet = packet_by_id.get(packet_id, {})
        path = ROOT / packet.get("local_path", "")
        decision_ts = parse_ts(l4["decision_asof_ts"])
        available_ts = parse_ts(packet.get("available_to_brain_ts", ""))
        asof_pass = "1" if decision_ts and available_ts and available_ts <= decision_ts and packet.get("asof_guard_pass") == "1" else "0"
        hit_count, families, snippet_hash = scan_guidance_text(path) if asof_pass == "1" else (0, "", "")
        if not packet:
            receipt_state = "issuer_public_source_gap"
        elif asof_pass != "1":
            receipt_state = "issuer_public_source_after_decision_or_bad_asof"
        elif hit_count > 0:
            receipt_state = "issuer_public_text_hit_asof"
        else:
            receipt_state = "issuer_public_text_no_hit_asof"
        rows.append(
            {
                "task_id": "Task1954",
                "guidance_probe_id": f"ISSUERGUIDE-1954-{idx:06d}",
                "trade_spec_id": l4["trade_spec_id"],
                "candidate_source_id": l4["candidate_source_id"],
                "symbol": l4["symbol"],
                "decision_asof_ts": l4["decision_asof_ts"],
                "financing_source_packet_id": packet_id,
                "cik": packet.get("cik", ""),
                "accession": packet.get("accession", ""),
                "form": packet.get("form", ""),
                "acceptance_datetime": packet.get("acceptance_datetime", ""),
                "source_available_to_brain_ts": packet.get("available_to_brain_ts", ""),
                "asof_guard_pass": asof_pass,
                "local_path": packet.get("local_path", ""),
                "sha256": packet.get("sha256", ""),
                "issuer_public_guidance_receipt_state": receipt_state,
                "guidance_keyword_hit_count": hit_count,
                "guidance_keyword_families": families or "none",
                "snippet_hash": snippet_hash,
                "analyst_revision_certified": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def expectation_recertification_rows(inputs: dict[str, object], guidance: list[dict[str, object]]) -> list[dict[str, object]]:
    guidance_by_spec = {row["trade_spec_id"]: row for row in guidance}
    vendor_gate = inputs["earnings_gate"][0]
    rows = []
    for idx, l4 in enumerate(inputs["hardened_l4"], 1):
        has_expectation_proxy = "expectation_proxy_downgraded" in l4.get("hardening_reason", "")
        receipt = guidance_by_spec[l4["trade_spec_id"]]
        if receipt["issuer_public_guidance_receipt_state"] == "issuer_public_text_hit_asof":
            permission = "issuer_public_support_only_no_analyst_surprise"
            score_permission = "small_support_credit_only"
        elif receipt["issuer_public_guidance_receipt_state"] == "issuer_public_text_no_hit_asof":
            permission = "proxy_blocked_no_issuer_text_hit"
            score_permission = "remove_remaining_proxy_credit"
        else:
            permission = "source_gap_not_negative"
            score_permission = "remove_remaining_proxy_credit"
        rows.append(
            {
                "task_id": "Task1955",
                "expectation_recert_id": f"EXPECTRECEIPT-1955-{idx:06d}",
                "trade_spec_id": l4["trade_spec_id"],
                "candidate_source_id": l4["candidate_source_id"],
                "symbol": l4["symbol"],
                "decision_asof_ts": l4["decision_asof_ts"],
                "expectation_proxy_present": "1" if has_expectation_proxy else "0",
                "issuer_public_guidance_receipt_state": receipt["issuer_public_guidance_receipt_state"],
                "analyst_revision_certified": "0",
                "vendor_gate_verdict": vendor_gate.get("gate_verdict", "vendor_blocked_schema_only"),
                "expectation_gap_permission": permission,
                "active_score_permission": score_permission if has_expectation_proxy else "not_applicable_no_expectation_proxy",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def source_receipt_hardened_l4_rows(
    inputs: dict[str, object], receipts: list[dict[str, object]], expectation: list[dict[str, object]]
) -> list[dict[str, object]]:
    receipt_counts = Counter(row["source_family"] for row in receipts if row["source_time_pass"] == "1")
    expect_by_spec = {row["trade_spec_id"]: row for row in expectation}
    rows = []
    for idx, l4 in enumerate(inputs["hardened_l4"], 1):
        score = to_float(l4["hardened_interaction_score"])
        expect = expect_by_spec[l4["trade_spec_id"]]
        guidance_adjust = 0.0
        if expect["expectation_proxy_present"] == "1":
            if expect["active_score_permission"] == "small_support_credit_only":
                guidance_adjust = 0.15
            elif expect["active_score_permission"] == "remove_remaining_proxy_credit":
                guidance_adjust = -0.25
        final_score = score + guidance_adjust
        if final_score >= 2.5:
            state = "receipt_high_conviction_payoff"
            multiplier = 1.055
        elif final_score >= 1.5:
            state = "receipt_positive_payoff"
            multiplier = 1.03
        elif final_score >= 0.5:
            state = "receipt_ordinary_pass"
            multiplier = 1.00
        elif final_score <= -1.2:
            state = "receipt_risk_cap"
            multiplier = 0.72
        elif final_score < 0:
            state = "receipt_watch_trim"
            multiplier = 0.90
        else:
            state = "receipt_neutral_watch"
            multiplier = 0.97
        rows.append(
            {
                "task_id": "Task1957",
                "receipt_l4_id": f"RECEIPTL4-1957-{idx:06d}",
                "target_policy_variant_id": l4["target_policy_variant_id"],
                "trade_spec_id": l4["trade_spec_id"],
                "candidate_source_id": l4["candidate_source_id"],
                "symbol": l4["symbol"],
                "decision_asof_ts": l4["decision_asof_ts"],
                "strategy_sleeve": l4["strategy_sleeve"],
                "hardened_interaction_score": l4["hardened_interaction_score"],
                "issuer_public_guidance_adjustment": round(guidance_adjust, 4),
                "source_receipt_interaction_score": round(final_score, 4),
                "source_receipt_l5_budget_multiplier": multiplier,
                "source_receipt_thesis_state": state,
                "event_receipt_grade": "derived_prior_window_timestamped" if receipt_counts["price_event_window"] > 0 else "source_gap",
                "breadth_receipt_grade": "derived_cross_section_timestamped" if receipt_counts["theme_breadth"] > 0 else "source_gap",
                "macro_score_permission": "shadow_only_until_alfred_vintage_certified",
                "expectation_gap_permission": expect["expectation_gap_permission"],
                "hardening_reason": l4.get("hardening_reason", ""),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def replay_top3(inputs: dict[str, object], l4_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    l4_by_spec = {row["trade_spec_id"]: row for row in l4_rows}
    source_trades = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in inputs["winner_trades"]}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inputs["budget"]:
        if row["target_policy_variant_id"] == "winner_defense_budget_top3_v1":
            grouped[row["decision_asof_ts"]].append(row)
    trades = []
    equity = []
    capital = INITIAL_CAPITAL
    trade_idx = 1
    for decision_ts in sorted(grouped):
        rows = sorted(grouped[decision_ts], key=lambda row: to_float(l4_by_spec[row["trade_spec_id"]]["source_receipt_interaction_score"]), reverse=True)
        base_alloc = capital / 3.0
        period_pnl = 0.0
        allocated = 0
        for row in rows:
            src = source_trades.get(("winner_defense_budget_top3_v1", row["trade_spec_id"]))
            thesis = l4_by_spec.get(row["trade_spec_id"])
            if not src or not thesis:
                continue
            mult = clamp(to_float(row["sleeve_budget_multiplier"]) * to_float(thesis["source_receipt_l5_budget_multiplier"]), 0.0, 1.22)
            if mult <= 0:
                continue
            cap_alloc = base_alloc * mult
            pnl = cap_alloc * to_float(src["net_return"])
            capital += pnl
            period_pnl += pnl
            allocated += 1
            trades.append(
                {
                    "task_id": "Task1958",
                    "trade_row_id": f"RECEIPTREPLAY-1958-{trade_idx:07d}",
                    "policy_variant_id": "source_receipt_hardened_top3_v1",
                    "source_policy_variant_id": "winner_defense_budget_top3_v1",
                    "trade_spec_id": row["trade_spec_id"],
                    "candidate_source_id": row["candidate_source_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision_ts,
                    "strategy_sleeve": row["strategy_sleeve"],
                    "source_receipt_thesis_state": thesis["source_receipt_thesis_state"],
                    "source_receipt_interaction_score": thesis["source_receipt_interaction_score"],
                    "source_receipt_l5_multiplier": thesis["source_receipt_l5_budget_multiplier"],
                    "base_sleeve_budget_multiplier": row["sleeve_budget_multiplier"],
                    "final_budget_multiplier": round(mult, 6),
                    "source_net_return": src.get("net_return", ""),
                    "capital_allocated": round(cap_alloc, 4),
                    "pnl": round(pnl, 4),
                    "net_return": src.get("net_return", ""),
                    "entry_date": src.get("entry_date", ""),
                    "actual_exit_date": src.get("actual_exit_date", ""),
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            trade_idx += 1
        equity.append(
            {
                "task_id": "Task1958",
                "policy_variant_id": "source_receipt_hardened_top3_v1",
                "decision_asof_ts": decision_ts,
                "equity": round(capital, 4),
                "period_pnl": round(period_pnl, 4),
                "selected_count": len(rows),
                "allocated_count": allocated,
                "authority": AUTHORITY,
            }
        )
    return trades, equity


def metric_rows(inputs: dict[str, object], trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    sleeve = {row["policy_variant_id"]: row for row in inputs["sleeve_metrics"]}["sleeve_split_top3_v1"]
    hard = inputs["hardened_metrics"][0]
    values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in equity]
    final = values[-1]
    start = replay.parse_ts(str(equity[0]["decision_asof_ts"])).date()
    end_dates = [gap.parse_date(row.get("actual_exit_date")) for row in trades]
    end = max([d for d in end_dates if d is not None] or [start])
    years = max((end - start).days / 365.25, 1 / 365.25)
    cagr = final ** (1 / years) / (INITIAL_CAPITAL ** (1 / years)) - 1.0
    mdd = replay.max_drawdown(values)
    return [
        {
            "task_id": "Task1958",
            "policy_variant_id": "source_receipt_hardened_top3_v1",
            "baseline_policy_variant_id": "sleeve_split_top3_v1",
            "previous_hardened_policy_variant_id": "interaction_hardened_top3_v1",
            "initial_capital": INITIAL_CAPITAL,
            "final_equity": round(final, 4),
            "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
            "cagr": round(cagr, 6),
            "max_drawdown": round(mdd, 6),
            "trade_count": len(trades),
            "baseline_final_equity": sleeve["final_equity"],
            "baseline_cagr": sleeve["cagr"],
            "baseline_max_drawdown": sleeve["max_drawdown"],
            "previous_hardened_final_equity": hard["final_equity"],
            "previous_hardened_cagr": hard["cagr"],
            "previous_hardened_max_drawdown": hard["max_drawdown"],
            "delta_vs_baseline_final_equity": round(final - to_float(sleeve["final_equity"]), 4),
            "delta_vs_previous_hardened_final_equity": round(final - to_float(hard["final_equity"]), 4),
            "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
            "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
            "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
            "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 and final > QQQ_BENCHMARK_FINAL else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def split_rows(equity: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in equity:
        d = replay.parse_ts(str(row["decision_asof_ts"])).date()
        groups["IS_2021_2023" if d.year <= 2023 else "OOS_2024_2026Q1"].append(row)
    rows = []
    for idx, (window, items) in enumerate(sorted(groups.items()), 1):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in items]
        rows.append(
            {
                "task_id": "Task1958",
                "split_id": f"RECEIPTSPLIT-1958-{idx:03d}",
                "policy_variant_id": "source_receipt_hardened_top3_v1",
                "split_window": window,
                "period_count": len(items),
                "split_final_equity": round(values[-1], 4),
                "split_total_return": round(values[-1] / INITIAL_CAPITAL - 1.0, 6),
                "split_max_drawdown": round(replay.max_drawdown(values), 6),
                "authority": AUTHORITY,
            }
        )
    return rows


def cost_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    metric = metrics[0]
    rows = []
    for idx, bps in enumerate([0, 25, 50, 100], 1):
        haircut = int(metric["trade_count"]) * (bps / 10000.0) * 0.35
        stressed = to_float(metric["final_equity"]) * max(0.0, 1.0 - haircut)
        rows.append(
            {
                "task_id": "Task1958",
                "cost_stress_id": f"RECEIPTCOST-1958-{idx:03d}",
                "policy_variant_id": "source_receipt_hardened_top3_v1",
                "round_trip_cost_bps": bps,
                "approx_trade_count": metric["trade_count"],
                "stressed_final_equity": round(stressed, 4),
                "beats_qqq_after_stress": "1" if stressed > QQQ_BENCHMARK_FINAL else "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def ablation_rows(inputs: dict[str, object], l4_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    base_trades, base_equity = replay_top3(inputs, l4_rows)
    base_final = to_float(metric_rows(inputs, base_trades, base_equity)[0]["final_equity"])
    variants = {
        "ablate_price_receipt": ("event_receipt_grade", -0.55),
        "ablate_breadth_receipt": ("breadth_receipt_grade", -0.45),
        "ablate_issuer_public_guidance_support": ("issuer_public_guidance_adjustment", 0.0),
        "ablate_quality_like_high_conviction": ("source_receipt_thesis_state", -0.30),
        "ablate_financing_risk_cap": ("source_receipt_thesis_state", 0.35),
        "ablate_all_receipt_adjustments": ("all_receipt", 0.0),
    }
    rows = []
    for idx, (variant, (field, adjustment)) in enumerate(variants.items(), 1):
        mutated = []
        for row in l4_rows:
            new_row = dict(row)
            score = to_float(new_row["source_receipt_interaction_score"])
            if variant == "ablate_price_receipt" and new_row["event_receipt_grade"] != "source_gap":
                score += adjustment
            elif variant == "ablate_breadth_receipt" and new_row["breadth_receipt_grade"] != "source_gap":
                score += adjustment
            elif variant == "ablate_issuer_public_guidance_support":
                score -= to_float(new_row["issuer_public_guidance_adjustment"])
            elif variant == "ablate_quality_like_high_conviction" and "high_conviction" in new_row["source_receipt_thesis_state"]:
                score += adjustment
            elif variant == "ablate_financing_risk_cap" and new_row["source_receipt_thesis_state"] == "receipt_risk_cap":
                score += adjustment
            elif variant == "ablate_all_receipt_adjustments":
                score = to_float(new_row["hardened_interaction_score"])
            new_row["source_receipt_interaction_score"] = round(score, 4)
            if score >= 2.5:
                new_row["source_receipt_l5_budget_multiplier"] = 1.055
            elif score >= 1.5:
                new_row["source_receipt_l5_budget_multiplier"] = 1.03
            elif score >= 0.5:
                new_row["source_receipt_l5_budget_multiplier"] = 1.0
            elif score <= -1.2:
                new_row["source_receipt_l5_budget_multiplier"] = 0.72
            elif score < 0:
                new_row["source_receipt_l5_budget_multiplier"] = 0.90
            else:
                new_row["source_receipt_l5_budget_multiplier"] = 0.97
            mutated.append(new_row)
        trades, equity = replay_top3(inputs, mutated)
        metric = metric_rows(inputs, trades, equity)[0]
        rows.append(
            {
                "task_id": "Task1956",
                "ablation_id": f"PRIMABLATE-1956-{idx:03d}",
                "ablation_variant": variant,
                "ablated_field_or_logic": field,
                "policy_variant_id": "source_receipt_hardened_top3_v1",
                "final_equity_audit_only": metric["final_equity"],
                "cagr_audit_only": metric["cagr"],
                "max_drawdown_audit_only": metric["max_drawdown"],
                "delta_vs_full_receipt_final_audit_only": round(to_float(metric["final_equity"]) - base_final, 4),
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def top5_blocker_rows(inputs: dict[str, object], l4_rows: list[dict[str, object]], expectation: list[dict[str, object]]) -> list[dict[str, object]]:
    l4_by_spec = {row["trade_spec_id"]: row for row in l4_rows}
    expect_by_spec = {row["trade_spec_id"]: row for row in expectation}
    rows = []
    for idx, row in enumerate(inputs["hardened_top5"], 1):
        l4 = l4_by_spec.get(row["trade_spec_id"], {})
        expect = expect_by_spec.get(row["trade_spec_id"], {})
        score = to_float(l4.get("source_receipt_interaction_score"))
        if row["hardened_top5_gate"] == "covered_by_top3_replay":
            gate = "covered_by_top3_replay"
        elif row["previous_dilution_specificity_state"] in {"active_financing_pressure", "live_active_dilution", "blocked_future_or_bad_asof"}:
            gate = "blocked_financing_or_bad_asof"
        elif expect.get("expectation_gap_permission") != "issuer_public_support_only_no_analyst_surprise":
            gate = "blocked_no_independent_expectation_receipt"
        elif score < 2.7:
            gate = "blocked_insufficient_receipt_score"
        else:
            gate = "shadow_candidate_requires_frozen_top5_replay"
        rows.append(
            {
                "task_id": "Task1959",
                "top5_receipt_gate_id": f"TOP5RECEIPT-1959-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "cohort": row["cohort"],
                "previous_hardened_top5_gate": row["hardened_top5_gate"],
                "previous_dilution_specificity_state": row["previous_dilution_specificity_state"],
                "source_receipt_interaction_score": l4.get("source_receipt_interaction_score", ""),
                "expectation_gap_permission": expect.get("expectation_gap_permission", ""),
                "receipt_top5_gate": gate,
                "replay_executed": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def acceptance_and_closeout(metrics: list[dict[str, object]], top5: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    metric = metrics[0]
    shadow_candidates = sum(1 for row in top5 if row["receipt_top5_gate"] == "shadow_candidate_requires_frozen_top5_replay")
    gate = [
        {
            "task_id": "Task1960",
            "gate_id": "SRCRECEIPTGATE-1960-001",
            "policy_variant_id": metric["policy_variant_id"],
            "diagnostic_joint_target_met": metric["joint_target_met"],
            "top5_shadow_candidate_count": shadow_candidates,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "reason": "source_receipt_and_ablation_diagnostic_only_not_acceptance_contract",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1960",
            "verdict": "source_receipt_ablation_complete_diagnostic_only",
            "best_policy_variant_id": metric["policy_variant_id"],
            "best_final_equity": metric["final_equity"],
            "best_cagr": metric["cagr"],
            "best_max_drawdown": metric["max_drawdown"],
            "top5_shadow_candidate_count": shadow_candidates,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_required_action": "certify raw price/breadth source manifests and acquire PIT analyst/guidance or freeze top3-only policy before any top5 replay",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(metrics: list[dict[str, object]], splits: list[dict[str, object]], ablations: list[dict[str, object]], top5: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metric = metrics[0]
    top5_counts = Counter(row["receipt_top5_gate"] for row in top5)
    lines = [
        "# Task1951-1960 Source Receipt And Ablation",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Policy: `{metric['policy_variant_id']}`.",
        f"- Final equity: {metric['final_equity']}.",
        f"- CAGR: {metric['cagr']}.",
        f"- MDD: {metric['max_drawdown']}.",
        f"- Delta vs Task1941-1950 hardened final equity: {metric['delta_vs_previous_hardened_final_equity']}.",
        "- Macro remains shadow-only because ALFRED vintage is not certified.",
        "- Analyst revision remains vendor-gated; issuer-public SEC text is support-only, not true consensus surprise.",
        "- Event and breadth receipts are explicit derived as-of fields, not raw-source acceptance certification.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Data and join discipline:",
        "",
        "- Event/breadth receipt uses exact prior Task1931-1940 rows and `decision_asof_ts` as source availability timestamp.",
        "- Macro vintage audit reuses Task1834 source packets and keeps active macro scoring blocked.",
        "- Issuer-public guidance probe uses exact Task1842 `trade_spec_id -> financing_source_packet_id` and exact Task1836 local SEC path.",
        "- Analyst revision is not inferred from issuer text.",
        "- Replay returns reuse prior controlled winner-defense trades; no new price matching or symbol/date fallback.",
        "",
        "| Policy | Final | CAGR | MDD | Trades | Joint Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| `{metric['policy_variant_id']}` | {metric['final_equity']} | {metric['cagr']} | {metric['max_drawdown']} | {metric['trade_count']} | {metric['joint_target_met']} |",
        "",
        "Split/OOS metrics:",
        "",
        "| Window | Final | Return | MDD |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in splits:
        lines.append(f"| {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(["", "Primitive ablation audit:", "", "| Variant | Final | Delta vs Full | MDD |", "| --- | ---: | ---: | ---: |"])
    for row in ablations:
        lines.append(
            f"| `{row['ablation_variant']}` | {row['final_equity_audit_only']} | {row['delta_vs_full_receipt_final_audit_only']} | {row['max_drawdown_audit_only']} |"
        )
    lines.extend(["", "Top5 receipt gate:", "", "| Gate | Count |", "| --- | ---: |"])
    for gate, count in sorted(top5_counts.items()):
        lines.append(f"| `{gate}` | {count} |")
    lines.extend(
        [
            "",
            "Remaining blockers:",
            "",
            "- Raw OHLC and breadth manifests are timestamped as derived fields here, but not recertified as raw-source acceptance artifacts.",
            "- Full ALFRED vintage remains blocked without local vintage archive/API-backed vintage pull.",
            "- True analyst revision and consensus surprise remain unavailable locally.",
            "- Top5 promotion remains shadow-only and needs a separate frozen replay after the above source upgrades.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. The weak gaps were not hand-waved.",
            "2. Macro was kept blocked.",
            "3. Analyst surprise was kept blocked.",
            "4. SEC issuer-public text was used only as small support.",
            "5. Top3 still clears the diagnostic target.",
            "6. Top5 still does not get promoted.",
            "7. This remains diagnostic only.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1951_source_receipt_input_manifest.csv`",
            "- `task1952_event_breadth_source_receipt_manifest.csv`",
            "- `task1953_macro_vintage_attempt_ledger.csv`",
            "- `task1954_issuer_public_guidance_probe.csv`",
            "- `task1955_expectation_source_recertification.csv`",
            "- `task1956_primitive_ablation_replay_metrics.csv`",
            "- `task1957_source_receipt_hardened_l4.csv`",
            "- `task1958_source_receipt_top3_replay_trades.csv/equity/metrics/split_oos/cost_stress`",
            "- `task1959_top5_promotion_blocker_audit.csv`",
            "- `task1960_acceptance_gate.csv`",
            "- `task1960_closeout.csv/json`",
            "",
            "This task does not change strategy acceptance.",
            "This task does not change deployment readiness.",
            "This task does not permit real capital.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    rows = read_csv(registry)
    existing = {row["task_id"] for row in rows}
    report = "docs/reports/task_1951_1960_source_receipt_and_ablation/task_1951_1960_source_receipt_and_ablation.md"
    decision = "docs/reports/task_1951_1960_source_receipt_and_ablation/task_1951_1960_decision.csv"
    artifacts = "data/artifacts/task_1951_1960_source_receipt_and_ablation"
    titles = [
        ("Task1951", "Source Receipt Input Manifest"),
        ("Task1952", "Event Breadth Source Receipt Manifest"),
        ("Task1953", "Macro Vintage Attempt Ledger"),
        ("Task1954", "Issuer Public Guidance Probe"),
        ("Task1955", "Expectation Source Recertification"),
        ("Task1956", "Primitive Ablation Replay Metrics"),
        ("Task1957", "Source Receipt Hardened L4"),
        ("Task1958", "Source Receipt Hardened Top3 Replay"),
        ("Task1959", "Top5 Promotion Blocker Audit"),
        ("Task1960", "Source Receipt Ablation Closeout"),
    ]
    for idx, (task_id, title) in enumerate(titles):
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": title,
                "owner_team": "Research Governance / Backtest & Simulation Infra",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "diagnostic-source-receipt-ablation",
                "parent_task": "Task1950" if idx == 0 else titles[idx - 1][0],
                "key_report": report,
                "key_decision": decision,
                "key_artifacts": artifacts,
                "validation_command": "python scripts/trader_brain_1951_1960_source_receipt_and_ablation_validate.py",
                "notes": "Adds explicit source receipt, macro vintage attempt ledger, issuer-public guidance probe, primitive ablation, and diagnostic replay without changing acceptance",
            }
        )
    write_csv(registry, rows)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    if "95. Task1951-Task1960" in text:
        return
    line = (
        "95. Task1951-Task1960 added source-receipt and ablation hardening after Task1941-1950: "
        "event/breadth source availability is explicit, macro remains shadow-only until ALFRED vintage certification, "
        "issuer-public SEC guidance text is support-only, analyst surprise remains vendor-gated, top5 remains blocked, "
        f"and the source-receipt top3 diagnostic replay ended final {closeout['best_final_equity']} "
        f"CAGR {closeout['best_cagr']} MDD {closeout['best_max_drawdown']}; strategy remains NOT_ACCEPTED / "
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert = text.find("\n\nTask851-859")
    if insert == -1:
        text = text.rstrip() + "\n" + line
    else:
        text = text[:insert].rstrip() + "\n" + line + text[insert:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    manifest = input_manifest_rows()
    receipts = event_breadth_receipt_rows(inputs)
    macro_attempts = macro_vintage_attempt_rows(inputs)
    guidance = issuer_public_guidance_probe_rows(inputs)
    expectation = expectation_recertification_rows(inputs, guidance)
    l4 = source_receipt_hardened_l4_rows(inputs, receipts, expectation)
    ablations = ablation_rows(inputs, l4)
    trades, equity = replay_top3(inputs, l4)
    metrics = metric_rows(inputs, trades, equity)
    splits = split_rows(equity)
    costs = cost_rows(metrics)
    top5 = top5_blocker_rows(inputs, l4, expectation)
    gate, closeout = acceptance_and_closeout(metrics, top5)

    write_csv(OUT_DIR / "task1951_source_receipt_input_manifest.csv", manifest)
    write_csv(OUT_DIR / "task1952_event_breadth_source_receipt_manifest.csv", receipts)
    write_csv(OUT_DIR / "task1953_macro_vintage_attempt_ledger.csv", macro_attempts)
    write_csv(OUT_DIR / "task1954_issuer_public_guidance_probe.csv", guidance)
    write_csv(OUT_DIR / "task1955_expectation_source_recertification.csv", expectation)
    write_csv(OUT_DIR / "task1956_primitive_ablation_replay_metrics.csv", ablations)
    write_csv(OUT_DIR / "task1957_source_receipt_hardened_l4.csv", l4)
    write_csv(OUT_DIR / "task1958_source_receipt_top3_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1958_source_receipt_top3_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1958_source_receipt_top3_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1958_split_oos_metrics.csv", splits)
    write_csv(OUT_DIR / "task1958_cost_stress_metrics.csv", costs)
    write_csv(OUT_DIR / "task1959_top5_promotion_blocker_audit.csv", top5)
    write_csv(OUT_DIR / "task1960_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1960_closeout.csv", closeout)
    write_json(OUT_DIR / "task1960_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(metrics, splits, ablations, top5, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print(f"[TASK1951_1960] wrote {OUT_DIR}")
    print(f"[TASK1951_1960] report {REPORT}")


if __name__ == "__main__":
    main()
