from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK2001 = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
OUT_DIR = ROOT / "data/artifacts/task_2011_2020_subagent_source_discovery"
REPORT_DIR = ROOT / "docs/reports/task_2011_2020_subagent_source_discovery"
REPORT = REPORT_DIR / "task_2011_2020_subagent_source_discovery.md"
DECISION = REPORT_DIR / "task_2011_2020_decision.csv"
AUTHORITY = "DIAGNOSTIC_SUBAGENT_SOURCE_DISCOVERY_ONLY"


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


def source_family_rows() -> list[dict[str, object]]:
    rows = [
        {
            "family": "ir_ceo_press_release",
            "subagent": "Franklin",
            "ranked_primary_source": "SEC 8-K Exhibit 99.1",
            "secondary_sources": "issuer IR archive|PRNewswire|BusinessWire|GlobeNewswire",
            "mcp_or_vendor_status": "Quartr available but provider guide/company-id access blocked in this session",
            "feasibility": "high_for_sec_exhibits_medium_for_issuer_ir_crosscheck",
            "immediate_action": "build_sec_8k_exhibit_99_1_extractor_for_48_symbols",
            "paper_gate_effect": "can_unlock_ir_ceo_family_only",
            "blocker": "issuer_ir_exact_time_and_bulk_wire_access",
        },
        {
            "family": "earnings_call_transcript",
            "subagent": "Plato",
            "ranked_primary_source": "Quartr Pro/API/MCP",
            "secondary_sources": "FactSet CallStreet|Finnhub|API Ninjas|FMP|Alpha Vantage|company IR pages",
            "mcp_or_vendor_status": "Quartr is best structured source but subscription_required/provider-guide access blocked",
            "feasibility": "vendor_gated_for_acceptance_grade_transcripts",
            "immediate_action": "create_transcript_vendor_gate_and_key_check_queue_by_symbol_decision",
            "paper_gate_effect": "blocked_until_provider_available_ts_and_document_ids_are_captured",
            "blocker": "subscription_or_api_key_and_provider_available_ts",
        },
        {
            "family": "contract_customer_confirmation",
            "subagent": "Herschel",
            "ranked_primary_source": "SEC issuer/customer filings",
            "secondary_sources": "customer-side SEC/IR|government awards|company IR press releases|NIST CHIPS|USAspending|DoD contracts",
            "mcp_or_vendor_status": "no SEC-specific MCP discovered; Quartr can help but evidence must retain ids/urls",
            "feasibility": "high_for_ANET_AMD_CEG_partial_low_for_CIEN_AVGO_AEIS_named_customer",
            "immediate_action": "build_positive_and_blocker_fixture_queue_ANET_AMD_CEG_vs_CIEN_AVGO_AEIS",
            "paper_gate_effect": "can_unlock_named_customer_for_some_rows_only",
            "blocker": "unnamed_cloud_provider_or_vendor_gated_customer_detail",
        },
        {
            "family": "policy_news_external_catalyst",
            "subagent": "Laplace",
            "ranked_primary_source": "Federal Register API and GovInfo",
            "secondary_sources": "Congress.gov/GovInfo bills|NIST CHIPS awards|USAspending|DoD contracts|FCC/FAA/FERC|state utility filings",
            "mcp_or_vendor_status": "no official GovInfo/Federal Register MCP installed; public APIs are available",
            "feasibility": "high_for_federal_official_sources_medium_for_state_utility_filings",
            "immediate_action": "build_federal_register_govinfo_chips_usaspending_source_catalog",
            "paper_gate_effect": "can_unlock_policy_news_family_for_chain_level_catalysts",
            "blocker": "exact_symbol_mapping_for_policy_chain_and_state_filing_schema_variance",
        },
    ]
    for idx, row in enumerate(rows, start=1):
        row.update(
            {
                "task_id": "Task2011",
                "subagent_finding_id": f"SUBFIND-2011-{idx:03d}",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def ranked_source_options() -> list[dict[str, object]]:
    options = [
        ("ir_ceo_press_release", 1, "SEC EDGAR 8-K Exhibit 99.1", "https://www.sec.gov/search-filings/edgar-application-programming-interfaces", "free_official", "high", "accepted_ts_raw_filing_hash"),
        ("ir_ceo_press_release", 2, "Issuer IR archives", "issuer_specific", "free_public", "medium", "publication_date_ir_url_raw_html"),
        ("ir_ceo_press_release", 3, "PRNewswire/BusinessWire/GlobeNewswire", "https://www.globenewswire.com/rss/list", "free_public_or_limited", "medium", "wire_timestamp_raw_html"),
        ("earnings_call_transcript", 1, "Quartr Pro/API/MCP", "https://quartr.com/docs/datasets/earnings-call-transcripts", "vendor_gated", "high_if_available", "event_id_document_id_provider_available_ts"),
        ("earnings_call_transcript", 2, "FactSet Events & Transcripts / CallStreet", "https://insight.factset.com/resources/at-a-glance-document-distributor-xml-company-events-transcript-datafeed", "vendor_gated", "high_if_available", "event_transcript_feed_ids"),
        ("earnings_call_transcript", 3, "Finnhub transcripts", "https://pkg.go.dev/github.com/Finnhub-Stock-API/finnhub-go", "possibly_paid", "medium", "transcript_id_event_time"),
        ("earnings_call_transcript", 4, "API Ninjas earnings transcript", "https://api-ninjas.com/api/earningscalltranscript", "premium_only", "medium", "ticker_cik_quarter_timestamp"),
        ("earnings_call_transcript", 5, "FMP/Alpha Vantage transcripts", "https://www.alphavantage.co/documentation/", "api_key_or_paid", "medium_low_for_asof", "quarter_transcript_publication_check_needed"),
        ("contract_customer_confirmation", 1, "SEC issuer/customer filings", "https://www.sec.gov/edgar/search/", "free_official", "high_sparse", "cik_accession_exact_named_customer"),
        ("contract_customer_confirmation", 2, "Customer-side SEC/IR", "https://www.sec.gov/search-filings/edgar-application-programming-interfaces", "free_official", "medium", "counterparty_exact_text_span"),
        ("contract_customer_confirmation", 3, "USAspending/SAM/DoD awards", "https://api.usaspending.gov/docs/endpoints", "free_official", "medium", "award_id_recipient_uei_action_date"),
        ("contract_customer_confirmation", 4, "NIST CHIPS awards", "https://www.nist.gov/chips/chips-america-awards", "free_official", "medium", "award_announcement_date_company"),
        ("policy_news_external_catalyst", 1, "Federal Register API", "https://www.federalregister.gov/developers/documentation/api/v1", "free_official", "high", "document_number_publication_date_raw_url"),
        ("policy_news_external_catalyst", 2, "GovInfo", "https://www.govinfo.gov/developers", "free_official", "high", "package_id_collection_raw_zip_pdf_xml"),
        ("policy_news_external_catalyst", 3, "Congress.gov/GovInfo bills", "https://www.loc.gov/apis/additional-apis/congress-dot-gov-api/", "key_or_govinfo_fallback", "medium_high", "bill_id_action_date_text"),
        ("policy_news_external_catalyst", 4, "DoD daily contracts", "https://www.defense.gov/News/Contracts/", "free_official", "medium", "contract_date_recipient_amount"),
        ("policy_news_external_catalyst", 5, "FERC/FCC/FAA/state utility filings", "https://www.ferc.gov/ferc-online/elibrary", "free_official_but_schema_varies", "medium_low", "docket_id_release_date_raw_document"),
    ]
    rows = []
    for idx, (family, rank, name, url, access, feasibility, required) in enumerate(options, start=1):
        rows.append(
            {
                "task_id": "Task2012",
                "source_option_id": f"SRCOPT-2012-{idx:03d}",
                "source_family": family,
                "rank": rank,
                "source_name": name,
                "source_url_or_locator": url,
                "access_model": access,
                "feasibility": feasibility,
                "required_asof_evidence": required,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def symbol_priority_rows() -> list[dict[str, object]]:
    trades = read_csv(TASK2001 / "task2004_aggressive_source_extraction_panel.csv")
    counts = Counter(row["symbol"] for row in trades)
    chains: dict[str, Counter[str]] = {}
    for row in trades:
        chains.setdefault(row["symbol"], Counter())[row["beneficiary_chain"]] += 1
    priority = []
    high_fixture = {"ANET", "AMD", "CEG"}
    blocker_fixture = {"CIEN", "AVGO", "AEIS", "CALX", "AMZN", "ADPT"}
    for idx, (symbol, count) in enumerate(counts.most_common(), start=1):
        chain = chains[symbol].most_common(1)[0][0]
        if symbol in high_fixture:
            fixture_type = "positive_free_source_fixture"
        elif symbol in blocker_fixture:
            fixture_type = "blocker_or_vendor_gate_fixture"
        elif count >= 4:
            fixture_type = "high_frequency_queue"
        else:
            fixture_type = "standard_queue"
        priority.append(
            {
                "task_id": "Task2013",
                "symbol_priority_id": f"SYMSRC-2013-{idx:03d}",
                "symbol": symbol,
                "aggressive_trade_count": count,
                "dominant_beneficiary_chain": chain,
                "fixture_type": fixture_type,
                "first_pass_source_families": "sec_exhibit_99_1|issuer_ir|customer_sec_ir|policy_official",
                "transcript_source_status": "vendor_gate_or_api_key_check",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return priority


def field_contract_rows() -> list[dict[str, object]]:
    contracts = [
        ("L1", "source_packet", "source_family|provider|symbol|cik|document_id|event_id|accession|url|raw_path|sha256|publication_ts|available_to_brain_ts|decision_asof_ts|retrieved_ts|matching_key|no_inferred_matching_used"),
        ("L2", "ir_ceo_semantics", "speaker_role|statement_text_hash|guidance|demand|customer_momentum|capacity|pricing|margin|risk|policy_exposure"),
        ("L2", "transcript_semantics", "speaker_name|speaker_role|is_qa|paragraph_index|timestamp_start_sec|primitive_family|snippet_hash"),
        ("L2", "customer_contract_semantics", "counterparty_name|named_counterparty_flag|contract_type|amount|duration|revenue_concentration_pct|directness_score"),
        ("L2", "policy_news_semantics", "agency|document_id|legal_stage|policy_action_type|affected_chain|amount_usd|effective_date|confidence"),
        ("L3", "relation_edges", "supports|accelerates|weakens|invalidates|routes_to_risk_budget|confirms_customer_demand|caps_concentration"),
        ("L4", "thesis_bridge", "full_source_thesis_state|primary_blocker|source_gap_neutral_flag|weakest_source_family"),
        ("L5", "paper_gate", "paper_shadow_trade_allowed|real_capital_trade_allowed|blocker|policy_hash"),
    ]
    return [
        {
            "task_id": "Task2014",
            "contract_id": f"FIELD-2014-{idx:03d}",
            "layer": layer,
            "object_name": obj,
            "required_fields": fields,
            "asof_rule": "available_to_brain_ts <= decision_asof_ts",
            "forbidden_rule": "no_current_2026_direct_assignment_no_outcome_assignment_no_proximity_fallback",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (layer, obj, fields) in enumerate(contracts, start=1)
    ]


def backlog_rows() -> list[dict[str, object]]:
    tasks = [
        ("Task2021", "SEC 8-K Exhibit 99.1 IR/CEO extractor", "Unlock IR/CEO family using existing CIK/accession/accepted time."),
        ("Task2022", "Federal Register and GovInfo policy extractor", "Attach official policy/news catalysts with publication date and raw source."),
        ("Task2023", "Customer confirmation fixture extractor", "Build ANET/AMD/CEG positive fixtures and CIEN/AVGO/AEIS blocker fixtures."),
        ("Task2024", "Transcript vendor gate implementation", "Check Quartr subscription, FMP/Alpha/Finnhub/API key availability, and build transcript queue."),
        ("Task2025", "Source-depth paper gate recomputation", "Recompute paper shadow gate after extractors attach."),
        ("Task2026", "Aggressive policy paper shadow dry run plan", "Only if Task2025 passes; no real capital."),
    ]
    return [
        {
            "task_id": task_id,
            "sequence": idx,
            "title": title,
            "objective": objective,
            "depends_on": "Task2011-2020",
            "status": "planned",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (task_id, title, objective) in enumerate(tasks, start=1)
    ]


def write_report(summary: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    text = f"""# Task2011-2020 Subagent Source Discovery

## Decision Summary

- Verdict: `subagent_source_discovery_complete`.
- Source families reviewed: {summary['source_family_count']}.
- Ranked source options: {summary['source_option_count']}.
- Aggressive symbols queued: {summary['symbol_count']}.
- Highest priority symbols: AVGO, ANET, AA, CIEN, AEIS, CEG.
- Immediate implementation order: SEC 8-K Exhibit 99.1 -> Federal Register/GovInfo -> customer confirmation fixtures -> transcript vendor gate.
- Paper shadow remains blocked until source gates are implemented and recomputed.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Subagents were assigned by source family:

- IR/CEO: SEC 8-K Exhibit 99.1 plus issuer IR/newswire.
- Earnings calls: Quartr is best, but vendor/subscription gate is active.
- Customer/contracts: free public sources can help ANET, AMD, and CEG; CIEN, AVGO, AEIS likely need blocker handling or vendor support.
- Policy/news: Federal Register, GovInfo, CHIPS/NIST, USAspending, and DoD contracts are the first implementation path.

The next work should not start by opening paper trading. It should first implement the source extractors and recompute the paper-shadow gate.

## No-Background Decision-Maker Report

1. 서브에이전트 4개를 돌렸다.
2. 공짜로 바로 할 수 있는 건 SEC 8-K, Federal Register/GovInfo, 일부 고객확인이다.
3. 실적콜은 Quartr/FactSet 같은 유료 게이트가 크다.
4. 다음 구현 순서는 확정됐다.
5. 아직 모의계좌 자동투입은 열면 안 된다.

## Artifact Manifest

- `task2011_subagent_source_findings.csv`
- `task2012_ranked_source_options.csv`
- `task2013_aggressive_symbol_source_priority.csv`
- `task2014_l1_l5_source_field_contract.csv`
- `task2015_2021_2026_implementation_backlog.csv`
- `task2020_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    text = registry.read_text(encoding="utf-8")
    if "Task2011," in text:
        return
    titles = {
        2011: "Subagent Source Family Findings",
        2012: "Ranked Source Options",
        2013: "Aggressive Symbol Source Queue",
        2014: "L1-L5 Source Field Contract",
        2015: "Source Extractor Backlog",
        2016: "IR CEO Source Routing",
        2017: "Transcript Source Routing",
        2018: "Customer Contract Source Routing",
        2019: "Policy News Source Routing",
        2020: "Subagent Source Discovery Closeout",
    }
    rows = []
    for task_num in range(2011, 2021):
        rows.append(
            {
                "task_id": f"Task{task_num}",
                "title": titles[task_num],
                "owner_team": "Research Governance / Source Acquisition",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "source-discovery-complete-implementation-pending",
                "parent_task": "Task2010" if task_num == 2011 else f"Task{task_num - 1}",
                "key_report": "docs/reports/task_2011_2020_subagent_source_discovery/task_2011_2020_subagent_source_discovery.md",
                "key_decision": "docs/reports/task_2011_2020_subagent_source_discovery/task_2011_2020_decision.csv",
                "key_artifacts": "data/artifacts/task_2011_2020_subagent_source_discovery",
                "validation_command": "python scripts/trader_brain_2011_2020_subagent_source_discovery_validate.py",
                "notes": "Captures subagent/GPT/MCP/source discovery for the four missing aggressive-policy source families.",
            }
        )
    with registry.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writerows(rows)


def update_operating_state(summary: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "101. Task2011-Task2020"
    row = (
        f"101. Task2011-Task2020 completed subagent source discovery for the four missing aggressive-policy source families: "
        "IR/CEO should start with SEC 8-K Exhibit 99.1, earnings calls are Quartr/FactSet-style vendor gated, "
        "customer confirmation is partly free for ANET/AMD/CEG and blocker-heavy for CIEN/AVGO/AEIS, and policy/news should start with Federal Register/GovInfo/NIST/USAspending/DoD; "
        "paper shadow remains blocked until extractor implementation and gate recomputation, while strategy remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    if marker not in text:
        lines = text.splitlines(keepends=True)
        insert_at = 0
        for idx, line in enumerate(lines):
            if line.startswith("100. Task2001-Task2010"):
                insert_at = idx + 1
                break
        lines.insert(insert_at, row)
        path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    findings = source_family_rows()
    options = ranked_source_options()
    symbols = symbol_priority_rows()
    contracts = field_contract_rows()
    backlog = backlog_rows()
    summary = {
        "task_id": "Task2020",
        "verdict": "subagent_source_discovery_complete",
        "source_family_count": len(findings),
        "source_option_count": len(options),
        "symbol_count": len(symbols),
        "next_implementation_order": "SEC_8K_EX99_1|Federal_Register_GovInfo|Customer_Confirmation_Fixtures|Transcript_Vendor_Gate",
        "paper_shadow_policy_status": "BLOCKED_UNTIL_EXTRACTORS_IMPLEMENTED_AND_GATE_RECOMPUTED",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task2011_subagent_source_findings.csv", findings)
    write_csv(OUT_DIR / "task2012_ranked_source_options.csv", options)
    write_csv(OUT_DIR / "task2013_aggressive_symbol_source_priority.csv", symbols)
    write_csv(OUT_DIR / "task2014_l1_l5_source_field_contract.csv", contracts)
    write_csv(OUT_DIR / "task2015_2021_2026_implementation_backlog.csv", backlog)
    write_csv(OUT_DIR / "task2020_closeout.csv", [summary])
    write_json(OUT_DIR / "task2020_closeout.json", summary)
    write_csv(DECISION, [summary])
    write_report(summary)
    update_registry()
    update_operating_state(summary)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK2011_2020_OK] families={len(findings)} options={len(options)} symbols={len(symbols)}")


if __name__ == "__main__":
    main()
