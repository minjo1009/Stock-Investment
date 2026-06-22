from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_907_916_sec_l1_l5_pipeline"
REPORT_DIR = ROOT / "docs/reports/task_907_916_sec_l1_l5_pipeline"
UNIVERSE = ROOT / "data/raw/theme_universe_10x7.csv"
COMPANY_TICKERS = ROOT / "data/raw/fundamental/sec_companyfacts/company_tickers.json"
COMPANYFACTS_DIR = ROOT / "data/raw/fundamental/sec_companyfacts/companyfacts"
DECISION_CALENDAR = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep/historical_decision_calendar.csv"

START_FILED = "2020-01-01"
END_FILED = "2026-03-31"
SEC_USER_AGENT = "trader-brain-research contact@example.com"
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

FAMILY_CONCEPTS = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "net_income": ("NetIncomeLoss", "ProfitLoss"),
    "operating_income": ("OperatingIncomeLoss",),
    "cash": ("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
    "assets": ("Assets",),
    "liabilities": ("Liabilities",),
    "research_and_development": ("ResearchAndDevelopmentExpense",),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment",),
}

SOURCE_CORPUS_FIELDS = [
    "symbol",
    "theme",
    "cik",
    "entity_name",
    "source_family",
    "raw_source_uri",
    "raw_storage_path",
    "raw_source_hash",
    "published_ts",
    "received_ts",
    "available_to_brain_ts",
    "effective_ts",
    "revision_id",
    "coverage_state",
    "download_status",
    "does_not_mean",
]

L1_FIELDS = [
    "evidence_id",
    "source_event_id",
    "symbol",
    "theme",
    "cik",
    "source_family",
    "source_concept",
    "fact_family",
    "unit",
    "fact_value",
    "period_start",
    "period_end",
    "fy",
    "fp",
    "form",
    "accession_or_document_id",
    "published_ts",
    "received_ts",
    "available_to_brain_ts",
    "raw_source_uri",
    "raw_storage_path",
    "raw_source_hash",
    "source_gap_flag",
    "l1_admission_state",
    "backtest_eligible_flag",
    "outcome_used_for_assignment_flag",
]

ADMISSION_FIELDS = [
    "evidence_id",
    "symbol",
    "theme",
    "source_family",
    "raw_storage_path",
    "raw_source_hash",
    "available_to_brain_ts",
    "admission_state",
    "rejection_reason",
    "can_enter_l2",
]

SPAN_FIELDS = [
    "evidence_id",
    "source_span_ref",
    "source_span_excerpt",
    "extraction_rule_id",
    "reproducibility_hash",
    "uncertainty",
]

PRIMITIVE_FIELDS = [
    "primitive_fact_id",
    "evidence_id",
    "symbol",
    "theme",
    "as_of_ts",
    "fact_family",
    "source_concept",
    "fact_value",
    "unit",
    "period_end",
    "form",
    "primitive_type",
    "primitive_state",
    "source_span_ref",
    "deterministic_rule_id",
    "reproducibility_hash",
    "uncertainty",
    "acceptance_state",
    "does_not_mean",
]

MEANING_FIELDS = [
    "economic_meaning_id",
    "primitive_fact_id",
    "evidence_id",
    "symbol",
    "theme",
    "as_of_ts",
    "fact_family",
    "economic_channel",
    "meaning_state",
    "uncertainty",
    "meaning_authority",
    "does_not_mean",
]

RELATION_FIELDS = [
    "relation_snapshot_id",
    "decision_id",
    "decision_asof_ts",
    "split_id",
    "symbol",
    "theme",
    "available_meaning_count",
    "available_fact_families",
    "missing_core_families",
    "relation_edges",
    "relation_state",
    "source_meaning_ids",
    "edge_asof_ts",
    "relation_authority",
    "does_not_mean",
]

CANDIDATE_FIELDS = [
    "candidate_bundle_id",
    "relation_snapshot_id",
    "decision_id",
    "decision_asof_ts",
    "split_id",
    "symbol",
    "theme",
    "candidate_thesis_type",
    "supporting_evidence_ids",
    "contradicting_evidence_ids",
    "weakest_layer",
    "unresolved_source_gaps",
    "candidate_authority",
    "adapter_eligible",
    "does_not_mean",
]

DRY_DECISION_FIELDS = [
    "trader_decision_id",
    "candidate_bundle_id",
    "decision_id",
    "decision_asof_ts",
    "split_id",
    "symbol",
    "theme",
    "decision_state",
    "decision_reason",
    "trade_spec_allowed",
    "diagnostic_replay_allowed",
    "decision_authority",
    "does_not_mean",
]

REPLAY_GATE_FIELDS = ["gate", "value", "threshold", "status", "action"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json_path(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    if payload.startswith(b"\x1f\x8b"):
        payload = gzip.decompress(payload)
    return json.loads(payload.decode("utf-8"))


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_ticker_map() -> dict[str, dict[str, object]]:
    data = json.loads(COMPANY_TICKERS.read_text(encoding="utf-8"))
    values = data.values() if isinstance(data, dict) else data
    return {str(row["ticker"]).upper(): row for row in values}


def companyfacts_path(symbol: str, cik: int) -> Path:
    return COMPANYFACTS_DIR / f"{symbol}_{cik:010d}.json"


def fetch_companyfacts(symbol: str, cik: int, force: bool = False) -> tuple[Path | None, str]:
    path = companyfacts_path(symbol, cik)
    if path.exists() and not force:
        return path, "existing"
    url = SEC_COMPANYFACTS_URL.format(cik=cik)
    request = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
        if payload.startswith(b"\x1f\x8b"):
            payload = gzip.decompress(payload)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        time.sleep(0.12)
        return path, "downloaded"
    except urllib.error.HTTPError as exc:
        return None, f"http_error_{exc.code}"
    except OSError as exc:
        return None, f"download_error_{type(exc).__name__}"


def available_ts_from_filed(filed: str) -> str:
    parsed = datetime.fromisoformat(filed).replace(tzinfo=timezone.utc)
    return (parsed + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")


def sec_fact_units(facts: dict[str, object], concept: str) -> dict[str, list[dict[str, object]]]:
    for namespace in ("us-gaap", "dei", "ifrs-full"):
        section = facts.get(namespace, {})
        if isinstance(section, dict) and concept in section:
            units = section[concept].get("units", {})
            if isinstance(units, dict):
                return units
    return {}


def select_fact_rows(symbol_row: dict[str, str], raw_path: Path, source_hash: str, uri: str, cik: int) -> list[dict[str, object]]:
    data = read_json_path(raw_path)
    facts = data.get("facts", {})
    out: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    for family, concepts in FAMILY_CONCEPTS.items():
        for concept in concepts:
            units = sec_fact_units(facts, concept)
            for unit, items in units.items():
                if unit not in {"USD", "shares"}:
                    continue
                for item in items:
                    filed = str(item.get("filed", ""))
                    if not filed or filed < START_FILED or filed > END_FILED:
                        continue
                    key = (family, concept, unit, item.get("accn"), item.get("end"), item.get("val"), filed)
                    if key in seen:
                        continue
                    seen.add(key)
                    source_event_id = f"sec_companyfacts|{symbol_row['symbol']}|{family}|{item.get('accn', '')}|{item.get('end', '')}|{filed}"
                    evidence_id = "Task907|" + stable_hash(source_event_id)[:20]
                    out.append(
                        {
                            "evidence_id": evidence_id,
                            "source_event_id": source_event_id,
                            "symbol": symbol_row["symbol"],
                            "theme": symbol_row["theme"],
                            "cik": f"{cik:010d}",
                            "source_family": "sec_companyfacts",
                            "source_concept": concept,
                            "fact_family": family,
                            "unit": unit,
                            "fact_value": item.get("val", ""),
                            "period_start": item.get("start", ""),
                            "period_end": item.get("end", ""),
                            "fy": item.get("fy", ""),
                            "fp": item.get("fp", ""),
                            "form": item.get("form", ""),
                            "accession_or_document_id": item.get("accn", ""),
                            "published_ts": filed + "T00:00:00Z",
                            "received_ts": filed + "T00:00:00Z",
                            "available_to_brain_ts": available_ts_from_filed(filed),
                            "raw_source_uri": uri,
                            "raw_storage_path": relative(raw_path),
                            "raw_source_hash": source_hash,
                            "source_gap_flag": "raw_external_source_attached",
                            "l1_admission_state": "admitted_external_source",
                            "backtest_eligible_flag": 0,
                            "outcome_used_for_assignment_flag": 0,
                        }
                    )
                    break
    return sorted(out, key=lambda row: (str(row["symbol"]), str(row["available_to_brain_ts"]), str(row["fact_family"]), str(row["source_concept"])))


def build_source_corpus(universe: list[dict[str, str]], force_download: bool = False) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    ticker_map = load_ticker_map()
    manifest: list[dict[str, object]] = []
    l1_rows: list[dict[str, object]] = []
    for row in universe:
        symbol = row["symbol"].upper()
        ticker = ticker_map.get(symbol)
        if not ticker:
            manifest.append(
                {
                    "symbol": symbol,
                    "theme": row["theme"],
                    "cik": "",
                    "entity_name": "",
                    "source_family": "sec_companyfacts",
                    "raw_source_uri": "",
                    "raw_storage_path": "",
                    "raw_source_hash": "",
                    "published_ts": "",
                    "received_ts": "",
                    "available_to_brain_ts": "",
                    "effective_ts": "",
                    "revision_id": "",
                    "coverage_state": "missing_ticker_cik",
                    "download_status": "missing_ticker_cik",
                    "does_not_mean": "negative evidence or tradability",
                }
            )
            continue
        cik = int(ticker["cik_str"])
        uri = SEC_COMPANYFACTS_URL.format(cik=cik)
        raw_path, status = fetch_companyfacts(symbol, cik, force_download)
        if not raw_path:
            manifest.append(
                {
                    "symbol": symbol,
                    "theme": row["theme"],
                    "cik": f"{cik:010d}",
                    "entity_name": ticker.get("title", ""),
                    "source_family": "sec_companyfacts",
                    "raw_source_uri": uri,
                    "raw_storage_path": "",
                    "raw_source_hash": "",
                    "published_ts": "",
                    "received_ts": "",
                    "available_to_brain_ts": "",
                    "effective_ts": "",
                    "revision_id": "",
                    "coverage_state": "raw_source_missing",
                    "download_status": status,
                    "does_not_mean": "negative evidence or tradability",
                }
            )
            continue
        source_hash = file_hash(raw_path)
        manifest.append(
            {
                "symbol": symbol,
                "theme": row["theme"],
                "cik": f"{cik:010d}",
                "entity_name": ticker.get("title", ""),
                "source_family": "sec_companyfacts",
                "raw_source_uri": uri,
                "raw_storage_path": relative(raw_path),
                "raw_source_hash": source_hash,
                "published_ts": "fact_level_filed_date",
                "received_ts": "fact_level_filed_date",
                "available_to_brain_ts": "fact_level_filed_date_plus_one_day",
                "effective_ts": "fact_level_period_end",
                "revision_id": source_hash[:16],
                "coverage_state": "raw_source_attached",
                "download_status": status,
                "does_not_mean": "negative evidence or tradability",
            }
        )
        l1_rows.extend(select_fact_rows(row, raw_path, source_hash, uri, cik))
    return manifest, l1_rows


def build_admission(l1_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in l1_rows:
        path = ROOT / str(row["raw_storage_path"])
        ok = bool(row["raw_source_hash"]) and path.exists() and row["source_family"] != "internal_source_event_capture"
        out.append(
            {
                "evidence_id": row["evidence_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "source_family": row["source_family"],
                "raw_storage_path": row["raw_storage_path"],
                "raw_source_hash": row["raw_source_hash"],
                "available_to_brain_ts": row["available_to_brain_ts"],
                "admission_state": "admitted_to_l2" if ok else "rejected_for_l2_admission",
                "rejection_reason": "" if ok else "missing_raw_file_or_internal_source",
                "can_enter_l2": 1 if ok else 0,
            }
        )
    return out


def build_spans(l1_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    spans: list[dict[str, object]] = []
    for row in l1_rows:
        excerpt = (
            f"SEC companyfacts {row['form']} {row['source_concept']}={row['fact_value']} {row['unit']} "
            f"period_end={row['period_end']} filed={row['published_ts']} accn={row['accession_or_document_id']}"
        )
        payload = {"evidence_id": row["evidence_id"], "excerpt": excerpt, "rule": "sec_companyfacts_span_v1"}
        spans.append(
            {
                "evidence_id": row["evidence_id"],
                "source_span_ref": stable_hash(excerpt),
                "source_span_excerpt": excerpt,
                "extraction_rule_id": "sec_companyfacts_span_v1",
                "reproducibility_hash": stable_hash(payload),
                "uncertainty": "aggregate_api_fact_not_full_filing_text",
            }
        )
    return spans


def primitive_state(family: str, value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "reported_value_unparsed"
    if family in {"net_income", "operating_income"}:
        return "reported_profit" if numeric >= 0 else "reported_loss"
    if numeric == 0:
        return "reported_zero_value"
    return "reported_positive_value" if numeric > 0 else "reported_negative_value"


def build_primitives(l1_rows: list[dict[str, object]], spans: list[dict[str, object]]) -> list[dict[str, object]]:
    span_by_id = {row["evidence_id"]: row for row in spans}
    out: list[dict[str, object]] = []
    for idx, row in enumerate(l1_rows, start=1):
        span = span_by_id[row["evidence_id"]]
        rule = f"sec_companyfacts_primitive_v1::{row['fact_family']}::{row['source_concept']}"
        payload = {"evidence_id": row["evidence_id"], "rule": rule, "value": row["fact_value"], "period_end": row["period_end"]}
        out.append(
            {
                "primitive_fact_id": f"PF911-{idx:06d}",
                "evidence_id": row["evidence_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "as_of_ts": row["available_to_brain_ts"],
                "fact_family": row["fact_family"],
                "source_concept": row["source_concept"],
                "fact_value": row["fact_value"],
                "unit": row["unit"],
                "period_end": row["period_end"],
                "form": row["form"],
                "primitive_type": "reported_fundamental_fact",
                "primitive_state": primitive_state(str(row["fact_family"]), row["fact_value"]),
                "source_span_ref": span["source_span_ref"],
                "deterministic_rule_id": rule,
                "reproducibility_hash": stable_hash(payload),
                "uncertainty": span["uncertainty"],
                "acceptance_state": "accepted_source_backed",
                "does_not_mean": "buy, sell, rank, score, sizing, or strategy acceptance",
            }
        )
    return out


def economic_channel(family: str) -> str:
    return {
        "revenue": "demand_or_scale_context",
        "net_income": "profitability_context",
        "operating_income": "operating_profitability_context",
        "cash": "liquidity_context",
        "assets": "balance_sheet_scale_context",
        "liabilities": "leverage_or_obligation_context",
        "research_and_development": "innovation_investment_context",
        "capex": "capital_intensity_context",
    }.get(family, "fundamental_context")


def build_meanings(primitives: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for idx, row in enumerate(primitives, start=1):
        out.append(
            {
                "economic_meaning_id": f"EM912-{idx:06d}",
                "primitive_fact_id": row["primitive_fact_id"],
                "evidence_id": row["evidence_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "as_of_ts": row["as_of_ts"],
                "fact_family": row["fact_family"],
                "economic_channel": economic_channel(str(row["fact_family"])),
                "meaning_state": "source_backed_context_available",
                "uncertainty": row["uncertainty"],
                "meaning_authority": "research_only_sec_companyfacts",
                "does_not_mean": "buy, sell, rank, score, sizing, or strategy acceptance",
            }
        )
    return out


def latest_by_family(meanings: list[dict[str, object]], asof_ts: str) -> dict[str, dict[str, object]]:
    latest: dict[str, dict[str, object]] = {}
    for row in meanings:
        if str(row["as_of_ts"]) > asof_ts:
            continue
        family = str(row["fact_family"])
        if family not in latest or str(row["as_of_ts"]) > str(latest[family]["as_of_ts"]):
            latest[family] = row
    return latest


def relation_edges(families: set[str]) -> list[str]:
    edges: list[str] = []
    if {"revenue", "net_income"} <= families:
        edges.append("revenue_to_profitability_context")
    if {"cash", "liabilities"} <= families:
        edges.append("liquidity_to_obligation_context")
    if {"revenue", "research_and_development"} <= families:
        edges.append("scale_to_innovation_investment_context")
    if {"revenue", "capex"} <= families:
        edges.append("scale_to_capital_intensity_context")
    if {"assets", "liabilities"} <= families:
        edges.append("asset_base_to_obligation_context")
    return edges


def build_relations(meanings: list[dict[str, object]], decisions: list[dict[str, str]]) -> list[dict[str, object]]:
    by_symbol: dict[str, list[dict[str, object]]] = {}
    for meaning in meanings:
        by_symbol.setdefault(str(meaning["symbol"]), []).append(meaning)
    out: list[dict[str, object]] = []
    idx = 1
    core = {"revenue", "net_income", "cash", "assets", "liabilities"}
    for decision in decisions:
        if decision["session_date"] > "2026-03-31":
            continue
        for symbol, rows in sorted(by_symbol.items()):
            latest = latest_by_family(rows, decision["decision_asof_ts"])
            if not latest:
                continue
            families = set(latest)
            missing = sorted(core - families)
            edges = relation_edges(families)
            relation_state = "source_backed_relation_context_ready" if len(edges) >= 2 and len(families) >= 4 else "source_backed_relation_context_thin"
            out.append(
                {
                    "relation_snapshot_id": f"RS913-{idx:06d}",
                    "decision_id": decision["decision_id"],
                    "decision_asof_ts": decision["decision_asof_ts"],
                    "split_id": decision["split_id"],
                    "symbol": symbol,
                    "theme": rows[0]["theme"],
                    "available_meaning_count": len(latest),
                    "available_fact_families": ";".join(sorted(families)),
                    "missing_core_families": ";".join(missing),
                    "relation_edges": ";".join(edges),
                    "relation_state": relation_state,
                    "source_meaning_ids": ";".join(str(row["economic_meaning_id"]) for row in latest.values()),
                    "edge_asof_ts": decision["decision_asof_ts"],
                    "relation_authority": "research_only_sec_companyfacts_asof",
                    "does_not_mean": "candidate approval, trade instruction, score, rank, or accepted graph",
                }
            )
            idx += 1
    return out


def build_candidates(relations: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for idx, row in enumerate(relations, start=1):
        ready = row["relation_state"] == "source_backed_relation_context_ready"
        out.append(
            {
                "candidate_bundle_id": f"CB914-{idx:06d}",
                "relation_snapshot_id": row["relation_snapshot_id"],
                "decision_id": row["decision_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "split_id": row["split_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "candidate_thesis_type": "source_backed_fundamental_context_packet" if ready else "source_backed_thin_context_packet",
                "supporting_evidence_ids": row["source_meaning_ids"],
                "contradicting_evidence_ids": "",
                "weakest_layer": "missing_non_sec_catalyst_sources" if ready else "thin_sec_fact_family_coverage",
                "unresolved_source_gaps": "earnings_transcript;press_release;policy_news;price_reaction_context",
                "candidate_authority": "research_only_not_adapter_eligible",
                "adapter_eligible": 0,
                "does_not_mean": "side, entry, exit, position_size, score, rank, or strategy acceptance",
            }
        )
    return out


def build_dry_decisions(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for idx, row in enumerate(candidates, start=1):
        watch = row["candidate_thesis_type"] == "source_backed_fundamental_context_packet"
        out.append(
            {
                "trader_decision_id": f"TD915-{idx:06d}",
                "candidate_bundle_id": row["candidate_bundle_id"],
                "decision_id": row["decision_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "split_id": row["split_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "decision_state": "review_only_watch" if watch else "skip_source_thin",
                "decision_reason": row["candidate_thesis_type"],
                "trade_spec_allowed": 0,
                "diagnostic_replay_allowed": 0,
                "decision_authority": "dry_research_only_sec_companyfacts",
                "does_not_mean": "real trade, broker instruction, strategy acceptance, or real capital permission",
            }
        )
    return out


def run(out_dir: Path, force_download: bool = False) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    universe = read_csv(UNIVERSE)
    decisions = read_csv(DECISION_CALENDAR)
    corpus, l1_rows = build_source_corpus(universe, force_download=force_download)
    admission = build_admission(l1_rows)
    admitted_l1 = [row for row in l1_rows if any(a["evidence_id"] == row["evidence_id"] and a["can_enter_l2"] == 1 for a in admission)]
    spans = build_spans(admitted_l1)
    primitives = build_primitives(admitted_l1, spans)
    meanings = build_meanings(primitives)
    relations = build_relations(meanings, decisions)
    candidates = build_candidates(relations)
    dry_decisions = build_dry_decisions(candidates)
    replay_gates = [
        {
            "gate": "l1_sec_companyfacts_raw_source_coverage",
            "value": sum(1 for row in corpus if row["coverage_state"] == "raw_source_attached"),
            "threshold": "70 symbols for full 10x7 coverage",
            "status": "pass" if sum(1 for row in corpus if row["coverage_state"] == "raw_source_attached") == len(universe) else "partial",
            "action": "use attached SEC source files as first L1 source family",
        },
        {
            "gate": "six_source_family_breadth",
            "value": "1_of_6_sec_companyfacts",
            "threshold": "company_filings_ir;earnings_guidance;macro_policy;supply_chain_capex;positioning_liquidity_volatility;sector_specialist_official_docs",
            "status": "partial",
            "action": "do_not_claim full source corpus until remaining families are attached",
        },
        {
            "gate": "l2_source_backed_primitive_generation",
            "value": len(primitives),
            "threshold": ">0 source-backed primitives",
            "status": "pass" if primitives else "fail",
            "action": "allow research-only L3 relation snapshots" if primitives else "block L3",
        },
        {
            "gate": "l5_trade_spec_allowed",
            "value": 0,
            "threshold": "needs catalyst source, adapter schema, split/OOS/cost/slippage audit",
            "status": "no_go",
            "action": "do_not_run_backtest",
        },
    ]

    write_csv(out_dir / "task907_source_corpus_manifest.csv", corpus, SOURCE_CORPUS_FIELDS)
    write_csv(out_dir / "task908_l1_sec_companyfacts_evidence.csv", l1_rows, L1_FIELDS)
    write_csv(out_dir / "task909_source_admission_audit.csv", admission, ADMISSION_FIELDS)
    write_csv(out_dir / "task910_source_span_panel.csv", spans, SPAN_FIELDS)
    write_csv(out_dir / "task911_l2_primitive_facts.csv", primitives, PRIMITIVE_FIELDS)
    write_csv(out_dir / "task912_l2_economic_meanings.csv", meanings, MEANING_FIELDS)
    write_csv(out_dir / "task913_l3_relation_snapshots.csv", relations, RELATION_FIELDS)
    write_csv(out_dir / "task914_l4_candidate_bundles.csv", candidates, CANDIDATE_FIELDS)
    write_csv(out_dir / "task915_l5_dry_decisions.csv", dry_decisions, DRY_DECISION_FIELDS)
    write_csv(out_dir / "task916_replay_gate.csv", replay_gates, REPLAY_GATE_FIELDS)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "Task907-916",
        "authority": "RESEARCH_ONLY_SEC_COMPANYFACTS_L1_L5",
        "universe_symbols": len(universe),
        "raw_source_attached_symbols": sum(1 for row in corpus if row["coverage_state"] == "raw_source_attached"),
        "raw_source_missing_symbols": sum(1 for row in corpus if row["coverage_state"] != "raw_source_attached"),
        "l1_evidence_rows": len(l1_rows),
        "l2_admitted_rows": len(admitted_l1),
        "source_span_rows": len(spans),
        "primitive_fact_rows": len(primitives),
        "economic_meaning_rows": len(meanings),
        "relation_snapshot_rows": len(relations),
        "candidate_bundle_rows": len(candidates),
        "dry_decision_rows": len(dry_decisions),
        "diagnostic_replay_status": "not_run_l5_trade_spec_no_go",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (out_dir / "task907_916_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()
    summary = run(args.out_dir, force_download=args.force_download)
    print(
        "[TRADER_BRAIN_907_916_SEC_L1_L5_OK] "
        f"sources={summary['raw_source_attached_symbols']}/{summary['universe_symbols']} "
        f"l1={summary['l1_evidence_rows']} primitives={summary['primitive_fact_rows']} "
        f"relations={summary['relation_snapshot_rows']} decisions={summary['dry_decision_rows']} "
        f"replay={summary['diagnostic_replay_status']}"
    )


if __name__ == "__main__":
    main()
