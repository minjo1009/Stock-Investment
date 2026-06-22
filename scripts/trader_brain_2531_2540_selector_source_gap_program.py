from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2531_2540_selector_source_gap_program"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2531_2540_selector_source_gap_program.md"
DECISION = REPORT_DIR / "task_2540_decision.csv"

TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"
TASK2401 = ROOT / "data/artifacts/task_2401_2500_research_to_paper_readiness"
TASK2501 = ROOT / "data/artifacts/task_2501_2510_kis_cost_basis_test"
TASK2511 = ROOT / "data/artifacts/task_2511_2520_kis_mdd_decomposition"
TASK2521 = ROOT / "data/artifacts/task_2521_2530_kis_cost_aware_guard_feasibility"

AUTHORITY = "DIAGNOSTIC_SELECTOR_SOURCE_GAP_PROGRAM_ONLY"


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
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return default


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "universe": read_csv(TASK2381 / "task2384_repaired_exit_source_rows.csv"),
        "kis_trades": read_csv(TASK2501 / "task2502_kis_repriced_trades.csv"),
        "mdd_trades": read_csv(TASK2511 / "task2513_mdd_window_trade_contributors.csv"),
        "source_gate": read_csv(TASK2401 / "task2421_source_time_gate_ledger.csv"),
        "gap_summary": read_csv(TASK2401 / "task2422_source_gap_summary.csv"),
        "feasibility": read_csv(TASK2521 / "task2527_feasibility_matrix.csv"),
    }


def yes(value: bool) -> str:
    return "1" if value else "0"


def scope_freeze_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    universe = inputs["universe"]
    kis = inputs["kis_trades"]
    mdd = inputs["mdd_trades"]
    decision_dates = sorted({row["decision_asof_ts"] for row in universe})
    return [
        {
            "task_id": "Task2531",
            "scope_id": "SCOPE2531-0001",
            "scope_type": "full_universe_selector_source_gap_program",
            "universe_rows": len(universe),
            "selected_kis_trade_rows": len(kis),
            "mdd_window_trade_rows": len(mdd),
            "negative_mdd_window_trade_rows": sum(1 for row in mdd if f(row.get("kis_pnl")) < 0),
            "decision_start": decision_dates[0],
            "decision_end": decision_dates[-1],
            "strict_raw_asof_complete_rows": sum(1 for row in inputs["source_gate"] if row.get("strict_raw_asof_complete") == "1"),
            "selector_changed": "0",
            "backtest_run": "0",
            "download_or_api_call_run": "0",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def recent_context_rows() -> list[dict[str, object]]:
    rows = [
        (
            "SRCCTX2532-0001",
            "SEC",
            "EDGAR APIs",
            "2024",
            "Official SEC submissions/companyfacts can be strict only when filing/accepted time is certified before decision time.",
            "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        ),
        (
            "SRCCTX2532-0002",
            "FMP",
            "Earnings transcript and press release APIs",
            "2026",
            "FMP exposes transcripts and press releases, but PIT assignment requires row-level publication/receipt certification and entitlement coverage.",
            "https://site.financialmodelingprep.com/developer/docs",
        ),
        (
            "SRCCTX2532-0003",
            "Finnhub",
            "Earnings call transcripts, recommendation trends, filings",
            "2026",
            "Finnhub offers transcript/recommendation/filing endpoints; strict assignment still needs historical revision timestamps, not capture-only rows.",
            "https://finnhub.io/docs/api",
        ),
        (
            "SRCCTX2532-0004",
            "Alpha Vantage",
            "News, sentiment, fundamentals, economic indicators",
            "2026",
            "Alpha Vantage can support market/news/macro proxies, but free-tier limits and premium endpoints must be treated as blockers, not negative evidence.",
            "https://www.alphavantage.co/documentation/",
        ),
        (
            "SRCCTX2532-0005",
            "Federal Reserve",
            "Analyst forecast inefficiency research",
            "2024",
            "Analyst forecast errors and revisions are economically relevant, but usable trading features require point-in-time revision history.",
            "https://www.federalreserve.gov/econres/feds/files/2024049pap.pdf",
        ),
        (
            "SRCCTX2532-0006",
            "Frontiers",
            "Transaction costs in minimum-risk portfolios",
            "2025",
            "Transaction costs can materially change net performance, so cost/liquidity inputs should affect entry filters before sizing overlays.",
            "https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2025.1585187/full",
        ),
    ]
    return [
        {
            "task_id": "Task2532",
            "context_id": context_id,
            "source_name": source,
            "title": title,
            "date_basis": date_basis,
            "lesson_for_program": lesson,
            "url": url,
            "used_as_design_context_only": "1",
            "used_as_source_of_truth_for_pnl": "0",
            "authority": AUTHORITY,
        }
        for context_id, source, title, date_basis, lesson, url in rows
    ]


def family_plan_rows() -> list[dict[str, object]]:
    families = [
        ("FAM2532-0001", "strict_raw_asof_certification", "L0/L1", "SEC/FMP/Finnhub/raw cache", "P0", "blocked", "strict_complete_0_of_3100", "required before paper/live; cannot score if only proxy"),
        ("FAM2532-0002", "financing_dilution_sec_events", "L2/L3/L4", "SEC 8-K/S-3/S-1/424B/ATM/Form D filings", "P0", "partly_free_strict_possible", "filing_total_1329_of_3100; SEC strict possible after accepted-time/raw-hash certification", "dilution/survival/financing split and bad-trade exclusion"),
        ("FAM2532-0003", "liquidity_rates_regime", "L2/L3/L4", "FRED/ALFRED/Treasury/NY Fed/price-volume", "P1", "proxy_possible", "KIS fixed fee exists but no real spread/ADV/rates regime admission", "selection throttle before drawdown appears"),
        ("FAM2532-0004", "earnings_transcript_guidance", "L2/L3/L4", "FMP/Finnhub/Alpha Vantage/issuer IR", "P1", "blocked_or_proxy", "earnings_surprise_154_of_3100; transcript strict gate uncertified", "guidance tone/surprise/QA pressure filter"),
        ("FAM2532-0005", "analyst_revision_rating_history", "L2/L4", "FMP/Finnhub/vendor", "P1", "blocked_or_proxy", "rating_score_214_of_3100; FMP grades mostly blocked", "expectation gap and downgrade risk"),
        ("FAM2532-0006", "contract_customer_confirmation", "L2/L3", "8-K EX-10/EX-99, customer filings, press releases", "P1", "blocked_by_entity_mapping", "source-to-customer mapping uncertified", "revenue validation quality"),
        ("FAM2532-0007", "sector_macro_regime_stress", "L3/L4", "FRED/ALFRED/ETF breadth/sector prices", "P2", "proxy_possible", "portfolio stress detected after drawdown", "avoid buying normal winners during hostile regime"),
        ("FAM2532-0008", "liquidity_spread_slippage", "L4/L5", "Alpaca/SIP/price-volume/NBBO when available", "P2", "proxy_possible", "KIS fixed fee but no real spread/ADV slippage", "thin-edge fragility before entry"),
        ("FAM2532-0009", "policy_news_entity_mapping", "L2/L3", "official policy releases/news affected entity map", "P2", "blocked_by_mapping", "no certified affected-entity map", "external catalyst and budget-risk filter"),
    ]
    return [
        {
            "task_id": "Task2532",
            "source_family_id": sid,
            "source_family": family,
            "affected_layer": layer,
            "candidate_provider_or_source": provider,
            "priority": priority,
            "current_admission_state": state,
            "current_evidence": evidence,
            "selector_use_case": use_case,
            "strict_pit_assignment_allowed_now": "0" if "strict_possible" not in state else "0",
            "proxy_annotation_allowed_now": "1" if state in {"blocked_or_proxy", "proxy_possible", "partly_free_strict_possible"} else "0",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for sid, family, layer, provider, priority, state, evidence, use_case in families
    ]


def admission_state_rows() -> list[dict[str, object]]:
    states = [
        ("strict_pass", "Row-level raw source exists; hash verified; source timestamp and available_to_brain_ts certified; available_to_brain_ts <= decision_asof_ts.", 1, 1, 0, 0, 0),
        ("proxy_allowed", "Source exists but is proxy, broad, capture-only, or vendor-limited; diagnostic annotation only.", 0, 1, 0, 1, 0),
        ("blocked", "Required source family is unavailable, quota/premium/auth blocked, raw missing, hash failed, timestamp uncertified, or future-timed.", 0, 1, 1, 1, 0),
        ("unknown", "No usable source evidence and no certified blocker classification yet; neutral missing state.", 0, 0, 0, 1, 0),
    ]
    return [
        {
            "task_id": "Task2533",
            "admission_state": state,
            "exact_meaning": meaning,
            "can_score_assignment": score,
            "can_annotate": annotate,
            "blocks_paper": paper,
            "blocks_live": live,
            "missing_source_is_negative": missing_negative,
            "authority": AUTHORITY,
        }
        for state, meaning, score, annotate, paper, live, missing_negative in states
    ]


def gap_ledger_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    mdd_examples = inputs["mdd_trades"][:6]
    family_rows = family_plan_rows()
    rows: list[dict[str, object]] = []
    idx = 1
    for fam in family_rows:
        for trade in mdd_examples:
            state = "blocked" if fam["priority"] in {"P0", "P1"} else "unknown"
            rows.append(
                {
                    "task_id": "Task2533",
                    "source_gap_ledger_id": f"SRCGAP2533-{idx:05d}",
                    "candidate_id": trade["candidate_source_id"],
                    "trade_spec_id": trade["trade_spec_id"],
                    "symbol": trade["symbol"],
                    "decision_asof_ts": trade["decision_asof_ts"],
                    "layer": fam["affected_layer"],
                    "feature_family": fam["source_family"],
                    "provider": fam["candidate_provider_or_source"],
                    "endpoint_or_source_family": fam["source_family"],
                    "required_for_layer": "1",
                    "required_for_assignment": yes(fam["priority"] == "P0"),
                    "required_for_paper": yes(fam["priority"] in {"P0", "P1"}),
                    "required_for_live": "1",
                    "gap_state": state,
                    "gap_reason": fam["current_evidence"],
                    "raw_path_expected": "",
                    "raw_path_found": "",
                    "raw_sha256_verified": "0",
                    "source_ts": "",
                    "available_to_brain_ts": "",
                    "source_time_basis": "not_certified",
                    "source_time_certified": "0",
                    "asof_pass": "0",
                    "blocked_by_quota": yes("quota" in str(fam["current_evidence"])),
                    "blocked_by_premium": yes("blocked" in str(fam["current_evidence"])),
                    "blocked_by_auth": "0",
                    "blocked_by_missing_raw": "1",
                    "blocked_by_hash_mismatch": "0",
                    "blocked_by_future_time": "0",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "allowed_resolution": "collect_certified_raw_or_keep_neutral",
                    "next_action": "Task2541+ source acquisition or provider entitlement decision",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def decision_asof_coverage_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    source_by_spec = {row["trade_spec_id"]: row for row in inputs["source_gate"]}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inputs["kis_trades"]:
        grouped[row["decision_asof_ts"]].append(row)
    mdd_specs = {row["trade_spec_id"] for row in inputs["mdd_trades"]}
    rows = []
    for idx, ts in enumerate(sorted(grouped, key=parse_ts), start=1):
        specs = grouped[ts]
        strict = sum(1 for row in specs if source_by_spec.get(row["trade_spec_id"], {}).get("strict_raw_asof_complete") == "1")
        proxy = sum(1 for row in specs if source_by_spec.get(row["trade_spec_id"], {}).get("proxy_feature_allowed") == "1")
        rows.append(
            {
                "task_id": "Task2534",
                "decision_asof_coverage_id": f"ASOFCOV2534-{idx:04d}",
                "decision_asof_ts": ts,
                "selected_trade_rows": len(specs),
                "mdd_window_trade_rows": sum(1 for row in specs if row["trade_spec_id"] in mdd_specs),
                "strict_raw_asof_complete_rows": strict,
                "proxy_or_uncertified_rows": proxy,
                "strict_coverage_ratio": round(strict / len(specs), 6) if specs else 0.0,
                "proxy_coverage_ratio": round(proxy / len(specs), 6) if specs else 0.0,
                "source_gap_blocks_paper": yes(strict < len(specs)),
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def feature_admission_gate_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    family_rows = family_plan_rows()
    rows: list[dict[str, object]] = []
    selected = inputs["kis_trades"]
    for trade in selected:
        for fam in family_rows:
            state = "blocked" if fam["priority"] == "P0" else ("proxy_allowed" if fam["current_admission_state"] in {"proxy_possible", "partly_free_strict_possible", "blocked_or_proxy"} else "unknown")
            can_score = state == "strict_pass"
            rows.append(
                {
                    "task_id": "Task2535",
                    "feature_gate_id": f"FEATGATE2535-{len(rows)+1:06d}",
                    "candidate_id": trade["candidate_source_id"],
                    "trade_spec_id": trade["trade_spec_id"],
                    "symbol": trade["symbol"],
                    "decision_asof_ts": trade["decision_asof_ts"],
                    "layer": fam["affected_layer"],
                    "feature_family": fam["source_family"],
                    "feature_value_present": "0",
                    "feature_value": "",
                    "provider": fam["candidate_provider_or_source"],
                    "source_packet_id": "",
                    "raw_path": "",
                    "raw_sha256": "",
                    "source_ts": "",
                    "available_to_brain_ts": "",
                    "source_time_basis": "not_certified",
                    "source_time_certified": "0",
                    "strict_gate_pass": "0",
                    "proxy_feature_allowed": yes(state == "proxy_allowed"),
                    "admission_state": state,
                    "can_score_assignment": yes(can_score),
                    "can_annotate_only": yes(state == "proxy_allowed"),
                    "blocks_paper": yes(state == "blocked" and fam["priority"] in {"P0", "P1"}),
                    "blocks_live": yes(state in {"blocked", "unknown"}),
                    "gate_fail_reason": "strict_source_missing_or_uncertified" if state != "strict_pass" else "",
                    "source_gap_ledger_id": "",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
    return rows


def provider_feasibility_rows() -> list[dict[str, object]]:
    rows = [
        ("SEC EDGAR", "submissions/companyfacts/filings/exhibits", "free_official", "strict_possible_with_accepted_time", "P0 for financing/dilution and filing context", "https://www.sec.gov/search-filings/edgar-application-programming-interfaces"),
        ("SEC Form D datasets", "private offerings/Form D data", "free_official", "strict_possible_with_filing_date_and_raw_snapshot", "P0/P1 for financing/dilution context", "https://www.sec.gov/data-research/sec-markets-data/form-d-data-sets"),
        ("FMP", "earnings transcripts/press releases/grades/price targets", "api_key_existing_but_entitlement_varies", "proxy_or_blocked_until_timestamp_and_entitlement_verified", "P0/P1 for transcripts and analyst context", "https://site.financialmodelingprep.com/developer/docs"),
        ("Finnhub", "transcripts/recommendation trends/filings", "api_key_existing_but_endpoint_limits_unknown", "proxy_or_blocked_until_historical_revision_ts_verified", "P0/P1 for transcripts and analyst context", "https://finnhub.io/docs/api"),
        ("Alpha Vantage", "news sentiment/fundamentals/economic indicators", "api_key_existing_free_tier_limited", "proxy_possible; strict only with source timestamp", "P2 macro/news/context; some endpoints quota blocked", "https://www.alphavantage.co/documentation/"),
        ("FRED/ALFRED", "rates/liquidity macro vintages", "api_key_existing", "strict_possible_for_vintage_macro", "P2 regime stress input", "https://fred.stlouisfed.org/docs/api/fred/"),
        ("Treasury FiscalData", "yield curve and fiscal data", "free_official", "strict_possible_with_release_date", "P1 rates/liquidity context", "https://fiscaldata.treasury.gov/api-documentation/"),
        ("NY Fed Markets API", "rates/liquidity operations data", "free_official", "strict_possible_with_publication_date", "P1 rates/liquidity context", "https://markets.newyorkfed.org/static/docs/markets-api.html"),
        ("Market data cache", "price/volume/ETF breadth/spread proxies", "local_or_api", "strict_market_data_possible_if timestamped", "P2 liquidity and absorption input", "local_cache_or_broker_data"),
    ]
    return [
        {
            "task_id": "Task2536",
            "provider_feasibility_id": f"PROVFEAS2536-{idx:04d}",
            "provider": provider,
            "source_family_or_endpoint": endpoint,
            "availability_class": availability,
            "pit_strict_feasibility": pit,
            "recommended_use": use,
            "reference_url": url,
            "api_secret_written": "0",
            "download_or_api_call_run": "0",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (provider, endpoint, availability, pit, use, url) in enumerate(rows, start=1)
    ]


def subagent_packet_rows() -> list[dict[str, object]]:
    rows = [
        ("Herschel", "019ed578-c098-76c1-9e59-c2188de6f6b1", "failure_source_gap_explorer", "read-only", "ranked selector/source gaps tied to Task2513 examples", "RESEARCH_ONLY"),
        ("Sartre", "019ed578-fa54-76d0-b452-7a72665fb508", "provider_recent_source_feasibility_explorer", "read-only", "recent provider/source family feasibility review", "DATA_HEALTH / RESEARCH_ONLY"),
        ("Kant", "019ed579-3a36-7722-9c7b-aa5c93abe47e", "feature_admission_contract_explorer", "read-only", "strict/proxy/blocked/unknown admission contract", "GOVERNANCE_HEALTH / DATA_HEALTH"),
    ]
    return [
        {
            "task_id": "Task2537",
            "subagent_packet_id": f"SUBPACK2537-{idx:04d}",
            "nickname": nickname,
            "agent_id": agent_id,
            "role": role,
            "write_scope": write_scope,
            "required_output": output,
            "validation_authority": authority,
            "file_edits_allowed": "0",
            "completed_or_pending_at_script_run": "completed_reviewed",
            "forbidden_actions_included": "1",
            "authority": AUTHORITY,
        }
        for idx, (nickname, agent_id, role, write_scope, output, authority) in enumerate(rows, start=1)
    ]


def acquisition_queue_rows() -> list[dict[str, object]]:
    rows = [
        ("ACQ2538-0001", "strict_raw_asof_certification", "P0", "Build raw source packet ledger for all selected and candidate rows before any assignment scoring.", "SEC accepted datetime + cached raw hash first; provider rows only if timestamp certified.", "blocks_paper_and_live"),
        ("ACQ2538-0002", "financing_dilution_sec_events", "P0", "Parse SEC forms and exhibits for offerings/ATM/S-3/S-1/424B/Form D/8-K dilution and survival context.", "SEC official raw; strict possible.", "highest_impact_free_source"),
        ("ACQ2538-0003", "liquidity_rates_regime", "P1", "Attach PIT rates/liquidity regime before selection throttles; use official vintage/release timestamps where possible.", "FRED/ALFRED + Treasury FiscalData + NY Fed.", "high_impact_free_source"),
        ("ACQ2538-0004", "earnings_transcript_guidance", "P1", "Acquire transcript metadata/text where free/API permits; keep proxy until publication/receipt time certified.", "FMP/Finnhub/Alpha Vantage/issuer IR; no API calls in Task2531-2540.", "blocks_assignment_scoring_until_certified"),
        ("ACQ2538-0005", "analyst_revision_rating_history", "P1", "Determine entitlement for PIT analyst revisions; do not substitute latest recommendation as historical truth.", "FMP/Finnhub/vendor gate.", "proxy_only_until_pit_revision_ts"),
        ("ACQ2538-0006", "contract_customer_confirmation", "P1", "Create certified customer/contract confirmation packets only where accession/customer ID mapping is explicit.", "SEC 8-K Item 1.01, EX-10/EX-99, USAspending after UEI mapping.", "revenue_validation_support"),
        ("ACQ2538-0007", "liquidity_spread_slippage", "P2", "Attach ADV/volume/spread proxy before KIS guard backtests; fixed fee alone is insufficient.", "price/volume/NBBO if available.", "entry_filter_support"),
        ("ACQ2538-0008", "sector_macro_regime_stress", "P2", "Attach PIT sector breadth/rates/vintage macro so stress guard can act before portfolio drawdown.", "FRED/ALFRED + ETF breadth.", "regime_filter_support"),
    ]
    return [
        {
            "task_id": "Task2538",
            "acquisition_queue_id": qid,
            "source_family": family,
            "priority": priority,
            "objective": objective,
            "recommended_first_source": source,
            "deployment_blocker_relevance": relevance,
            "download_or_api_call_run": "0",
            "requires_user_paid_vendor_decision": yes(family in {"analyst_revision_rating_history", "earnings_transcript_guidance"}),
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for qid, family, priority, objective, source, relevance in rows
    ]


def validation_assertion_rows() -> list[dict[str, object]]:
    assertions = [
        ("VA2539-001", "missing_source_is_negative == 0 for every row", "GOVERNANCE_HEALTH"),
        ("VA2539-002", "assignment_uses_future_outcome == 0 for every row", "GOVERNANCE_HEALTH"),
        ("VA2539-003", "outcome_used_for_assignment == 0 for every row", "GOVERNANCE_HEALTH"),
        ("VA2539-004", "can_score_assignment == 1 only when admission_state == strict_pass", "DATA_HEALTH"),
        ("VA2539-005", "strict_pass requires raw_path exists and raw_sha256 verified", "DATA_HEALTH"),
        ("VA2539-006", "strict_pass requires source_time_certified == 1", "DATA_HEALTH"),
        ("VA2539-007", "strict_pass requires available_to_brain_ts <= decision_asof_ts", "DATA_HEALTH"),
        ("VA2539-008", "proxy_allowed rows have can_score_assignment == 0", "DATA_HEALTH"),
        ("VA2539-009", "blocked required_for_paper rows set blocks_paper == 1", "GOVERNANCE_HEALTH"),
        ("VA2539-010", "blocked or unknown required_for_live rows set blocks_live == 1", "GOVERNANCE_HEALTH"),
        ("VA2539-011", "provider capture-only timestamps cannot open strict gates", "DATA_HEALTH"),
        ("VA2539-012", "quota/premium/auth failures classify as blocked not negative evidence", "DATA_HEALTH"),
        ("VA2539-013", "market/price rows may validate replay or absorption but cannot create source truth alone", "GOVERNANCE_HEALTH"),
        ("VA2539-014", "status footer remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN", "GOVERNANCE_HEALTH"),
    ]
    return [
        {"task_id": "Task2539", "assertion_id": aid, "assertion": assertion, "validation_authority": authority, "authority": AUTHORITY}
        for aid, assertion, authority in assertions
    ]


def closeout_rows(scope: dict[str, object], family_rows: list[dict[str, object]], feature_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    states = Counter(row["admission_state"] for row in feature_rows)
    p0 = [row for row in family_rows if row["priority"] == "P0"]
    return [
        {
            "task_id": "Task2540",
            "verdict": "selector_source_gap_program_built_no_replay_no_download",
            "full_universe_rows": scope["universe_rows"],
            "selected_kis_trade_rows": scope["selected_kis_trade_rows"],
            "mdd_window_trade_rows": scope["mdd_window_trade_rows"],
            "strict_raw_asof_complete_rows": scope["strict_raw_asof_complete_rows"],
            "p0_source_family_count": len(p0),
            "feature_gate_rows": len(feature_rows),
            "strict_pass_feature_rows": states.get("strict_pass", 0),
            "proxy_allowed_feature_rows": states.get("proxy_allowed", 0),
            "blocked_feature_rows": states.get("blocked", 0),
            "unknown_feature_rows": states.get("unknown", 0),
            "download_or_api_call_run": "0",
            "backtest_run": "0",
            "selector_changed": "0",
            "next_action": "Task2541+ should acquire P0/P1 source packets in priority order, starting with strict raw/as-of certification and SEC financing/dilution events.",
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


def write_report(closeout: dict[str, object], family_rows: list[dict[str, object]], queue_rows: list[dict[str, object]]) -> None:
    family_lines = "\n".join(
        f"- `{row['source_family']}` ({row['priority']}): {row['selector_use_case']} / current `{row['current_admission_state']}`."
        for row in family_rows
    )
    queue_lines = "\n".join(f"- `{row['source_family']}`: {row['objective']}" for row in queue_rows)
    REPORT.write_text(
        f"""# Task2531-2540 Selector Source Gap Program

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Full universe rows: {closeout['full_universe_rows']}.
- Selected KIS trade rows: {closeout['selected_kis_trade_rows']}.
- MDD-window trade rows: {closeout['mdd_window_trade_rows']}.
- Strict raw/as-of complete rows: {closeout['strict_raw_asof_complete_rows']}.
- P0 source family count: {closeout['p0_source_family_count']}.
- Download/API calls run: `0`.
- Backtest run: `0`.
- Selector changed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

The Task2521 guard test showed that portfolio-level de-risking can reduce MDD but tends to reduce return. The next bottleneck is selector source quality, not another sizing overlay.

Source family plan:

{family_lines}

Next acquisition queue:

{queue_lines}

Admission rule:

- `strict_pass` can score assignment.
- `proxy_allowed` can annotate only.
- `blocked` blocks paper/live when required.
- `unknown` is neutral missing evidence.
- Missing source is never negative.

## No-Background Decision-Maker Report

Conclusion first: the next work is source acquisition, not another backtest.

The system currently does not have enough certified historical source to know whether the brain could have known the right facts at the decision time. We created the source gap ledger and acquisition queue so Task2541+ can fill the most important gaps without mixing missing data with negative signals.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2531_2540_selector_source_gap_program/`.
- Validator: `python scripts/trader_brain_2531_2540_selector_source_gap_program_validate.py`.

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
    for task_no in range(2531, 2541):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"Selector Source Gap Program Step {task_no}",
                "owner_team": "Data & Market Microstructure / Research Governance / Brain Layer Architecture",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "selector-source-gap-program-no-download-no-replay",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2531_2540_selector_source_gap_program/task_2531_2540_selector_source_gap_program.md",
                "key_decision": "docs/reports/task_2531_2540_selector_source_gap_program/task_2540_decision.csv",
                "key_artifacts": "data/artifacts/task_2531_2540_selector_source_gap_program",
                "validation_command": "python scripts/trader_brain_2531_2540_selector_source_gap_program_validate.py",
                "notes": "Classifies selector source gaps and creates P0/P1 acquisition queue; no replay/download.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    lines = path.read_text(encoding="utf-8").rstrip().splitlines()
    line_123 = (
        "123. Task2531-Task2540 built the selector source-gap program after KIS guard feasibility failed to preserve return: "
        f"full universe {closeout['full_universe_rows']}, selected KIS trades {closeout['selected_kis_trade_rows']}, "
        f"MDD-window trades {closeout['mdd_window_trade_rows']}, strict raw/as-of complete rows {closeout['strict_raw_asof_complete_rows']}, "
        f"P0 source families {closeout['p0_source_family_count']}; no download, no replay, no selector change. "
        "Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN."
    )
    replaced = False
    out = []
    for line in lines:
        if line.startswith("123. Task2531-Task2540"):
            out.append(line_123)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(line_123)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    scope = scope_freeze_rows(inputs)
    recent_context = recent_context_rows()
    family_rows = family_plan_rows()
    admission_states = admission_state_rows()
    gap_rows = gap_ledger_rows(inputs)
    coverage_rows = decision_asof_coverage_rows(inputs)
    feature_rows = feature_admission_gate_rows(inputs)
    provider_rows = provider_feasibility_rows()
    subagent_rows = subagent_packet_rows()
    queue_rows = acquisition_queue_rows()
    assertions = validation_assertion_rows()
    closeout = closeout_rows(scope[0], family_rows, feature_rows)

    outputs = [
        ("task2531_scope_freeze.csv", scope),
        ("task2532_recent_source_context.csv", recent_context),
        ("task2532_source_family_plan.csv", family_rows),
        ("task2533_admission_states.csv", admission_states),
        ("task2533_source_gap_ledger.csv", gap_rows),
        ("task2534_decision_asof_coverage.csv", coverage_rows),
        ("task2535_feature_admission_gate.csv", feature_rows),
        ("task2536_provider_feasibility_matrix.csv", provider_rows),
        ("task2537_subagent_packets.csv", subagent_rows),
        ("task2538_next_acquisition_queue.csv", queue_rows),
        ("task2539_validation_assertions.csv", assertions),
        ("task2540_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2540_closeout.json", closeout[0])
    write_report(closeout[0], family_rows, queue_rows)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2531_2540_SELECTOR_SOURCE_GAP_PROGRAM_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
