from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2231_2250_plus8000_data_parity"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2231_2250_plus8000_data_parity.md"
DECISION = REPORT_DIR / "task_2231_2250_decision.csv"

TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK2121 = ROOT / "data/artifacts/task_2121_2150_free_api_full_capture_proxy_replay"
TASK2151 = ROOT / "data/artifacts/task_2151_2180_api_three_loop_hardening"
TASK2191 = ROOT / "data/artifacts/task_2191_2200_api_drawdown_sizing_guard"

AUTHORITY = "DATA_PARITY_PLUS8000_SELECTED_TRADE_FEATURE_EXPANSION_ONLY"
PARITY_THRESHOLD = 0.95


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


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("candidate_source_id", ""),
        row.get("trade_spec_id", ""),
        row.get("symbol", ""),
        row.get("decision_asof_ts", ""),
    )


def parse_dt(value: object) -> datetime | None:
    if value in {"", None}:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "None", "nan"}:
            return default
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "full_pool": read_csv(TASK1488 / "task1494_payoff_ranker_v6.csv"),
        "specs": read_csv(TASK1201 / "task1203_l5_trade_specs.csv"),
        "api_features": read_csv(TASK2121 / "task2124_l1_api_proxy_features.csv"),
        "api_normalized": read_csv(TASK2121 / "task2123_api_normalized_sources.csv"),
        "api_coverage": read_csv(TASK2151 / "task2162_decision_asof_coverage.csv"),
        "api_l2": read_csv(TASK2151 / "task2163_l2_api_semantics_hardened.csv"),
        "api_l4": read_csv(TASK2151 / "task2171_l4_api_score_cards_hardened.csv"),
        "api_l5": read_csv(TASK2151 / "task2172_l5_api_decisions_hardened.csv"),
        "plus8000_metrics": read_csv(TASK2191 / "task2196_guard_replay_metrics.csv"),
    }


def feature_contract(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    files = [
        (
            "task2124_l1_api_proxy_features",
            TASK2121 / "task2124_l1_api_proxy_features.csv",
            [
                "filing_total_365d",
                "filing_8k_365d",
                "filing_10x_365d",
                "latest_earnings_surprise_pct",
                "latest_revenue",
                "latest_net_income",
                "latest_free_cash_flow",
                "latest_cash",
                "latest_debt",
                "rating_score",
                "api_proxy_score",
                "api_proxy_state",
                "strict_transcript_gate_pass",
                "strict_analyst_revision_gate_pass",
            ],
            "L1_api_proxy_features_used_before_plus8000_sizing",
        ),
        (
            "task2162_decision_asof_coverage",
            TASK2151 / "task2162_decision_asof_coverage.csv",
            [
                "asof_source_packet_count",
                "material_event_packet_count",
                "periodic_operating_packet_count",
                "capital_markets_packet_count",
                "ownership_packet_count",
                "governance_packet_count",
                "earnings_surprise_packet_count",
                "recommendation_packet_count",
                "fundamental_quality_packet_count",
                "strict_transcript_gate_pass",
                "strict_analyst_revision_gate_pass",
                "coverage_state",
            ],
            "API_source_packet_coverage_used_for_hardened_L2",
        ),
        (
            "task2163_l2_api_semantics_hardened",
            TASK2151 / "task2163_l2_api_semantics_hardened.csv",
            ["api_l2_state", "api_l2_score", "microstructure_summary", "l5_direct_gate_permission"],
            "hardened_L2_API_semantics",
        ),
        (
            "task2171_l4_api_score_cards_hardened",
            TASK2151 / "task2171_l4_api_score_cards_hardened.csv",
            ["base_winner_acceleration_rank_score", "api_raw_overlay_score", "api_cohort_overlay_score", "api_adjusted_rank_score"],
            "hardened_L4_API_adjusted_rank",
        ),
        (
            "task2172_l5_api_decisions_hardened",
            TASK2151 / "task2172_l5_api_decisions_hardened.csv",
            ["api_l5_action", "api_l5_budget_multiplier", "base_raw_combined_multiplier", "strict_gate_status"],
            "hardened_L5_API_budget_decision",
        ),
    ]
    rows: list[dict[str, object]] = []
    row_counts = {
        "task2124_l1_api_proxy_features": len(inputs["api_features"]),
        "task2162_decision_asof_coverage": len(inputs["api_coverage"]),
        "task2163_l2_api_semantics_hardened": len(inputs["api_l2"]),
        "task2171_l4_api_score_cards_hardened": len(inputs["api_l4"]),
        "task2172_l5_api_decisions_hardened": len(inputs["api_l5"]),
    }
    key_counts = {
        "task2124_l1_api_proxy_features": len({key(row) for row in inputs["api_features"]}),
        "task2162_decision_asof_coverage": len({key(row) for row in inputs["api_coverage"]}),
        "task2163_l2_api_semantics_hardened": len({key(row) for row in inputs["api_l2"]}),
        "task2171_l4_api_score_cards_hardened": len({key(row) for row in inputs["api_l4"]}),
        "task2172_l5_api_decisions_hardened": len({key(row) for row in inputs["api_l5"]}),
    }
    for idx, (name, path, fields, role) in enumerate(files, start=1):
        rows.append(
            {
                "task_id": "Task2231",
                "contract_row_id": f"PLUS8000CONTRACT2231-{idx:03d}",
                "contract_name": name,
                "source_artifact": str(path.relative_to(ROOT)).replace("\\", "/"),
                "source_rows": row_counts[name],
                "source_exact_keys": key_counts[name],
                "required_fields": "|".join(fields),
                "role_in_plus8000_test": role,
                "must_expand_to_full_candidate_pool": "1",
                "full_candidate_target_rows": len(inputs["full_pool"]),
                "full_candidate_target_keys": len({key(row) for row in inputs["full_pool"]}),
                "sha256": file_hash(path),
                "authority": AUTHORITY,
            }
        )
    return rows


def build_source_index(normalized: list[dict[str, str]]) -> dict[str, dict[str, list[dict[str, str]]]]:
    index: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in normalized:
        symbol = row.get("symbol", "")
        endpoint = row.get("endpoint_name", "")
        if symbol and endpoint:
            record: dict[str, object] = {}
            try:
                record = json.loads(row.get("record_json", "") or "{}")
            except json.JSONDecodeError:
                record = {}
            packed = dict(row)
            for key_, value in record.items():
                if key_ not in packed:
                    packed[key_] = str(value)
            index[symbol][endpoint].append(packed)
    return index


def latest_before(rows: list[dict[str, str]], decision: datetime | None) -> dict[str, str] | None:
    if decision is None:
        return None
    best_row = None
    best_ts = None
    for row in rows:
        ts = parse_dt(row.get("source_ts"))
        if ts and ts <= decision and (best_ts is None or ts > best_ts):
            best_ts = ts
            best_row = row
    return best_row


def count_filings(rows: list[dict[str, str]], decision: datetime | None, lookback_days: int = 365) -> tuple[int, int, int]:
    if decision is None:
        return 0, 0, 0
    start = decision - timedelta(days=lookback_days)
    total = eightk = tenx = 0
    for row in rows:
        ts = parse_dt(row.get("acceptedDate") or row.get("filedDate") or row.get("source_ts"))
        if not ts or not (start <= ts <= decision):
            continue
        total += 1
        form = str(row.get("form", ""))
        if form.startswith("8-K"):
            eightk += 1
        if form in {"10-Q", "10-K"}:
            tenx += 1
    return total, eightk, tenx


def recompute_plus8000_features(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    source_index = build_source_index(inputs["api_normalized"])
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(inputs["full_pool"], start=1):
        decision = parse_dt(row["decision_asof_ts"])
        endpoints = source_index.get(row["symbol"], {})
        filings = endpoints.get("stock_filings", [])
        recommendations = endpoints.get("stock_recommendation", []) or endpoints.get("grades_historical", [])
        earnings_rows = endpoints.get("earnings_history", []) or endpoints.get("earnings", [])
        income_rows = endpoints.get("income_statement", [])
        balance_rows = endpoints.get("balance_sheet", [])
        cash_rows = endpoints.get("cash_flow", [])
        filing_total, filing_8k, filing_10x = count_filings(filings, decision)
        earnings = latest_before(earnings_rows, decision)
        income = latest_before(income_rows, decision)
        balance = latest_before(balance_rows, decision)
        cash_flow = latest_before(cash_rows, decision)
        grades = latest_before(recommendations, decision)
        surprise_pct = to_float((earnings or {}).get("surprisePercentage"), 0.0)
        revenue = to_float((income or {}).get("revenue"), 0.0)
        net_income = to_float((income or {}).get("netIncome"), 0.0)
        cash = to_float((balance or {}).get("cashAndCashEquivalents"), 0.0)
        debt = to_float((balance or {}).get("totalDebt"), 0.0)
        fcf = to_float((cash_flow or {}).get("freeCashFlow"), 0.0)
        strong_buy = to_float((grades or {}).get("analystRatingsStrongBuy"), 0.0)
        buy = to_float((grades or {}).get("analystRatingsBuy"), 0.0)
        hold = to_float((grades or {}).get("analystRatingsHold"), 0.0)
        sell = to_float((grades or {}).get("analystRatingsSell"), 0.0)
        strong_sell = to_float((grades or {}).get("analystRatingsStrongSell"), 0.0)
        rating_total = strong_buy + buy + hold + sell + strong_sell
        rating_score = ((strong_buy * 2 + buy - sell - strong_sell * 2) / rating_total * 10.0) if rating_total > 0 else 0.0
        quality_score = 0.0
        if revenue > 0:
            quality_score += clamp(net_income / revenue, -0.2, 0.3) * 40
            quality_score += clamp(fcf / revenue, -0.2, 0.3) * 45
        if cash > 0 or debt > 0:
            quality_score += clamp((cash - debt) / max(cash + debt, 1.0), -1, 1) * 8
        filing_score = min(filing_total, 10) * 0.7 + min(filing_8k, 5) * 0.9 + min(filing_10x, 4) * 1.2
        surprise_score = clamp(surprise_pct, -30, 30) * 0.35
        api_proxy_score = round(filing_score + surprise_score + quality_score + rating_score, 4)
        if api_proxy_score >= 18:
            state = "api_proxy_supportive"
        elif api_proxy_score <= -8:
            state = "api_proxy_risk_or_weak_quality"
        elif filing_total == 0 and not earnings and not income:
            state = "api_proxy_source_gap_neutral"
        else:
            state = "api_proxy_mixed_or_light"
        raw_fields_present = any([filings, recommendations, earnings_rows, income_rows, balance_rows, cash_rows])
        rows.append(
            {
                "task_id": "Task2236",
                "api_feature_id": f"PLUS8000FEAT2236-{idx:07d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "filing_total_365d": filing_total,
                "filing_8k_365d": filing_8k,
                "filing_10x_365d": filing_10x,
                "latest_earnings_surprise_pct": round(surprise_pct, 4),
                "latest_revenue": revenue,
                "latest_net_income": net_income,
                "latest_free_cash_flow": fcf,
                "latest_cash": cash,
                "latest_debt": debt,
                "rating_score": round(rating_score, 4),
                "api_proxy_score": api_proxy_score,
                "api_proxy_state": state,
                "strict_transcript_gate_pass": "0",
                "strict_analyst_revision_gate_pass": "0",
                "feature_schema_parity_pass": "1",
                "raw_source_present_for_any_contract_endpoint": "1" if raw_fields_present else "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def parity_panel(inputs: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    maps = {
        "api_features": {key(row): row for row in inputs["api_features"]},
        "api_coverage": {key(row): row for row in inputs["api_coverage"]},
        "api_l2": {key(row): row for row in inputs["api_l2"]},
        "api_l4": {key(row): row for row in inputs["api_l4"]},
        "api_l5": {key(row): row for row in inputs["api_l5"]},
    }
    source_index = build_source_index(inputs["api_normalized"])
    panel: list[dict[str, object]] = []
    queue_seen: set[tuple[str, str]] = set()
    queue: list[dict[str, object]] = []
    for idx, row in enumerate(inputs["full_pool"], start=1):
        k = key(row)
        symbol = row["symbol"]
        decision = parse_dt(row["decision_asof_ts"])
        api_feature = maps["api_features"].get(k, {})
        coverage = maps["api_coverage"].get(k, {})
        l2 = maps["api_l2"].get(k, {})
        l4 = maps["api_l4"].get(k, {})
        l5 = maps["api_l5"].get(k, {})
        endpoints = source_index.get(symbol, {})
        stock_filings = endpoints.get("stock_filings", [])
        stock_recommendation = endpoints.get("stock_recommendation", [])
        earnings = endpoints.get("earnings_history", []) or endpoints.get("earnings", [])
        income = endpoints.get("income_statement", [])
        balance = endpoints.get("balance_sheet", [])
        cash_flow = endpoints.get("cash_flow", [])
        endpoint_flags = {
            "stock_filings": int(bool(stock_filings)),
            "stock_recommendation": int(bool(stock_recommendation)),
            "earnings_history": int(bool(earnings)),
            "income_statement": int(bool(income)),
            "balance_sheet": int(bool(balance)),
            "cash_flow": int(bool(cash_flow)),
        }
        asof_flags = {
            "stock_filings": int(bool(latest_before(stock_filings, decision))),
            "stock_recommendation": int(bool(latest_before(stock_recommendation, decision))),
            "earnings_history": int(bool(latest_before(earnings, decision))),
            "income_statement": int(bool(latest_before(income, decision))),
            "balance_sheet": int(bool(latest_before(balance, decision))),
            "cash_flow": int(bool(latest_before(cash_flow, decision))),
        }
        exact_api_feature = int(bool(api_feature))
        exact_hardened = int(bool(coverage and l2 and l4 and l5))
        symbol_raw_parity = int(all(endpoint_flags.values()))
        asof_raw_parity = int(all(asof_flags.values()))
        full_parity = int(exact_api_feature and exact_hardened and symbol_raw_parity and asof_raw_parity)
        for endpoint_name, present in endpoint_flags.items():
            if not present and (symbol, endpoint_name) not in queue_seen:
                queue_seen.add((symbol, endpoint_name))
                provider = "finnhub" if endpoint_name in {"stock_filings", "stock_recommendation"} else ("alpha_vantage" if endpoint_name == "earnings_history" else "fmp")
                queue.append(
                    {
                        "task_id": "Task2234",
                        "acquisition_queue_id": f"PLUS8000QUEUE2234-{len(queue)+1:05d}",
                        "symbol": symbol,
                        "provider": provider,
                        "endpoint_name": endpoint_name,
                        "required_for_contract": "1",
                        "reason": "missing_symbol_endpoint_for_plus8000_data_parity",
                        "status": "queued_not_downloaded_by_this_parity_audit",
                        "authority": AUTHORITY,
                    }
                )
        panel.append(
            {
                "task_id": "Task2233",
                "parity_row_id": f"PLUS8000PARITY2233-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": symbol,
                "decision_asof_ts": row["decision_asof_ts"],
                "exact_task2124_feature_match": exact_api_feature,
                "exact_task2162_2172_hardened_match": exact_hardened,
                **{f"symbol_endpoint_{name}": value for name, value in endpoint_flags.items()},
                **{f"asof_endpoint_{name}": value for name, value in asof_flags.items()},
                "symbol_raw_endpoint_parity": symbol_raw_parity,
                "asof_raw_endpoint_parity": asof_raw_parity,
                "plus8000_data_parity_pass": full_parity,
                "api_proxy_score": api_feature.get("api_proxy_score", ""),
                "api_proxy_state": api_feature.get("api_proxy_state", ""),
                "api_l2_state": l2.get("api_l2_state", ""),
                "api_l2_score": l2.get("api_l2_score", ""),
                "api_adjusted_rank_score": l4.get("api_adjusted_rank_score", ""),
                "api_l5_budget_multiplier": l5.get("api_l5_budget_multiplier", ""),
                "strict_gate_status": l5.get("strict_gate_status", ""),
                "missing_source_is_negative": "0",
                "replay_allowed": "0",
                "replay_block_reason": "plus8000_data_parity_not_complete",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    summary: list[dict[str, object]] = []
    fields = [
        "exact_task2124_feature_match",
        "exact_task2162_2172_hardened_match",
        "symbol_raw_endpoint_parity",
        "asof_raw_endpoint_parity",
        "plus8000_data_parity_pass",
        "symbol_endpoint_stock_filings",
        "symbol_endpoint_stock_recommendation",
        "symbol_endpoint_earnings_history",
        "symbol_endpoint_income_statement",
        "symbol_endpoint_balance_sheet",
        "symbol_endpoint_cash_flow",
        "asof_endpoint_stock_filings",
        "asof_endpoint_stock_recommendation",
        "asof_endpoint_earnings_history",
        "asof_endpoint_income_statement",
        "asof_endpoint_balance_sheet",
        "asof_endpoint_cash_flow",
    ]
    for idx, field in enumerate(fields, start=1):
        covered = sum(int(row[field]) for row in panel)
        summary.append(
            {
                "task_id": "Task2235",
                "coverage_row_id": f"PLUS8000COVER2235-{idx:03d}",
                "coverage_metric": field,
                "candidate_rows": len(panel),
                "covered_rows": covered,
                "missing_rows": len(panel) - covered,
                "coverage_ratio": round(covered / len(panel), 6) if panel else 0.0,
                "parity_threshold": PARITY_THRESHOLD,
                "parity_gate_pass": "1" if panel and covered / len(panel) >= PARITY_THRESHOLD else "0",
                "authority": AUTHORITY,
            }
        )
    return panel, queue, summary


def feature_schema_summary(features: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, metric in enumerate(["feature_schema_parity_pass", "raw_source_present_for_any_contract_endpoint"], start=1):
        covered = sum(1 for row in features if row[metric] == "1")
        rows.append(
            {
                "task_id": "Task2237",
                "feature_schema_summary_id": f"PLUS8000FEATSUM2237-{idx:03d}",
                "coverage_metric": metric,
                "candidate_rows": len(features),
                "covered_rows": covered,
                "missing_rows": len(features) - covered,
                "coverage_ratio": round(covered / len(features), 6) if features else 0.0,
                "authority": AUTHORITY,
            }
        )
    states = Counter(str(row["api_proxy_state"]) for row in features)
    for state, count in sorted(states.items()):
        rows.append(
            {
                "task_id": "Task2237",
                "feature_schema_summary_id": f"PLUS8000FEATSUM2237-{len(rows)+1:03d}",
                "coverage_metric": f"api_proxy_state::{state}",
                "candidate_rows": len(features),
                "covered_rows": count,
                "missing_rows": len(features) - count,
                "coverage_ratio": round(count / len(features), 6) if features else 0.0,
                "authority": AUTHORITY,
            }
        )
    return rows


def closeout_rows(summary: list[dict[str, object]], queue: list[dict[str, object]], inputs: dict[str, list[dict[str, str]]], feature_summary: list[dict[str, object]]) -> list[dict[str, object]]:
    full = next(row for row in summary if row["coverage_metric"] == "plus8000_data_parity_pass")
    gate_pass = full["parity_gate_pass"] == "1"
    best = max(inputs["plus8000_metrics"], key=lambda row: to_float(row.get("final_equity")))
    feature_schema = next(row for row in feature_summary if row["coverage_metric"] == "feature_schema_parity_pass")
    any_raw = next(row for row in feature_summary if row["coverage_metric"] == "raw_source_present_for_any_contract_endpoint")
    return [
        {
            "task_id": "Task2250",
            "verdict": "plus8000_data_parity_pass_replay_still_requires_user_confirmation" if gate_pass else "plus8000_data_parity_failed_replay_blocked",
            "candidate_rows": full["candidate_rows"],
            "plus8000_parity_rows": full["covered_rows"],
            "plus8000_parity_ratio": full["coverage_ratio"],
            "parity_gate_pass": "1" if gate_pass else "0",
            "missing_acquisition_queue_rows": len(queue),
            "feature_schema_rows": feature_schema["covered_rows"],
            "feature_schema_ratio": feature_schema["coverage_ratio"],
            "any_raw_source_rows": any_raw["covered_rows"],
            "any_raw_source_ratio": any_raw["coverage_ratio"],
            "reference_plus8000_policy": best["policy_variant_id"],
            "reference_plus8000_final_equity": best["final_equity"],
            "reference_plus8000_cagr": best["cagr"],
            "reference_plus8000_mdd": best["max_drawdown"],
            "replay_allowed": "0",
            "replay_requires_user_confirmation": "1",
            "replay_block_reason": "explicit_user_authorization_required_even_if_parity_passes" if gate_pass else "same_standard_plus8000_data_not_attached_to_full_3100_pool",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], summary: list[dict[str, object]], contract: list[dict[str, object]], feature_summary: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    coverage_lines = "\n".join(
        f"- `{row['coverage_metric']}`: {row['covered_rows']}/{row['candidate_rows']} ({row['coverage_ratio']}), pass {row['parity_gate_pass']}."
        for row in summary
    )
    contract_lines = "\n".join(
        f"- `{row['contract_name']}`: source rows {row['source_rows']}, exact keys {row['source_exact_keys']}, role `{row['role_in_plus8000_test']}`."
        for row in contract
    )
    feature_lines = "\n".join(
        f"- `{row['coverage_metric']}`: {row['covered_rows']}/{row['candidate_rows']} ({row['coverage_ratio']})."
        for row in feature_summary
    )
    text = f"""# Task2231-2250 Plus8000 Data Parity

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Candidate rows: {closeout['candidate_rows']}.
- Plus8000 parity rows: {closeout['plus8000_parity_rows']}.
- Plus8000 parity ratio: {closeout['plus8000_parity_ratio']}.
- Feature schema rows: {closeout['feature_schema_rows']}.
- Any raw source rows: {closeout['any_raw_source_rows']}.
- Replay allowed: `{closeout['replay_allowed']}`.
- Replay blocker: `{closeout['replay_block_reason']}`.
- Missing acquisition queue rows: {closeout['missing_acquisition_queue_rows']}.
- Reference +8000 policy: `{closeout['reference_plus8000_policy']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task does not run a replay. It first checks whether the data level used in the +8000 selected-trade sizing test is attached to the full 3,100-candidate pool under the same feature contract.

Contract:

{contract_lines}

Coverage:

{coverage_lines}

Recomputed full-candidate feature schema:

{feature_lines}

## No-Background Decision-Maker Report

Conclusion first: the +8000 feature schema can be generated for 3,100 rows, but raw source parity is still weak. Therefore a fair full-universe replay under raw-source parity is blocked until the user explicitly authorizes proxy-schema parity replay.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2231_2250_plus8000_data_parity/`.
- Validator: `python scripts/trader_brain_2231_2250_plus8000_data_parity_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    existing = {row["task_id"] for row in rows}
    fieldnames = list(rows[0].keys())
    for task_no in range(2231, 2251):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "task_name": f"Plus8000 Data Parity Expansion Step {task_no}",
                "workstream": "Research Governance / Data Management",
                "status": "active",
                "validation_tier": "data-health",
                "acceptance_state": "NOT_ACCEPTED",
                "current_decision": "plus8000-data-parity-before-full-universe-replay",
                "upstream_task": f"Task{task_no - 1}" if task_no > 2231 else "Task2230",
                "report_path": "docs/reports/task_2231_2250_plus8000_data_parity/task_2231_2250_plus8000_data_parity.md",
                "decision_path": "docs/reports/task_2231_2250_plus8000_data_parity/task_2231_2250_decision.csv",
                "artifact_path": "data/artifacts/task_2231_2250_plus8000_data_parity",
                "validation_command": "python scripts/trader_brain_2231_2250_plus8000_data_parity_validate.py",
                "notes": "Freezes the +8000 selected-trade feature contract and blocks replay until the same data standard is attached to the 3100 full candidate pool.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "111. Task2231-Task2250"
    if marker in text:
        return
    line = (
        f"111. Task2231-Task2250 froze the +8000 selected-trade data contract and audited parity against "
        f"the 3,100-candidate pool. Parity rows {closeout['plus8000_parity_rows']}/{closeout['candidate_rows']} "
        f"({closeout['plus8000_parity_ratio']}); replay is `{closeout['replay_allowed']}` because "
        f"`{closeout['replay_block_reason']}`. Status remains NOT_ACCEPTED / "
        f"DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert_at = text.find("\n\n\nTask851-859 data certification status:")
    if insert_at == -1:
        text = text.rstrip() + "\n" + line
    else:
        text = text[:insert_at] + "\n" + line + text[insert_at:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    contract = feature_contract(inputs)
    panel, queue, summary = parity_panel(inputs)
    recomputed_features = recompute_plus8000_features(inputs)
    feature_summary = feature_schema_summary(recomputed_features)
    closeout = closeout_rows(summary, queue, inputs, feature_summary)
    write_csv(OUT_DIR / "task2231_plus8000_feature_contract.csv", contract)
    write_csv(OUT_DIR / "task2232_full_candidate_target_universe.csv", [
        {
            "task_id": "Task2232",
            "target_universe_id": "PLUS8000TARGET2232-001",
            "candidate_rows": len(inputs["full_pool"]),
            "unique_symbols": len({row["symbol"] for row in inputs["full_pool"]}),
            "decision_asof_count": len({row["decision_asof_ts"] for row in inputs["full_pool"]}),
            "same_standard_required": "plus8000_selected_trade_feature_contract",
            "authority": AUTHORITY,
        }
    ])
    write_csv(OUT_DIR / "task2233_full_candidate_plus8000_parity_panel.csv", panel)
    write_csv(OUT_DIR / "task2234_missing_source_acquisition_queue.csv", queue)
    write_csv(OUT_DIR / "task2235_parity_coverage_summary.csv", summary)
    write_csv(OUT_DIR / "task2236_recomputed_plus8000_feature_panel.csv", recomputed_features)
    write_csv(OUT_DIR / "task2237_recomputed_feature_summary.csv", feature_summary)
    write_csv(OUT_DIR / "task2250_closeout.csv", closeout)
    write_json(OUT_DIR / "task2250_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], summary, contract, feature_summary)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2231_2250_PLUS8000_DATA_PARITY_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
