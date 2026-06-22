from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_917_920_multifamily_relation_adapter"
TASK907 = ROOT / "data/artifacts/task_907_916_sec_l1_l5_pipeline"
UNIVERSE = ROOT / "data/raw/theme_universe_10x7.csv"
DECISIONS = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep/historical_decision_calendar.csv"
TASK636_CHECKPOINT = ROOT / "data/raw/task_636_content_source_text/task_636_source_text_checkpoint.csv"
FRED_REPAIRED = ROOT / "data/raw/macro_fred/task_655/fred_macro_release_repaired_feature_panel.csv"
FOMC_HTML = ROOT / "data/raw/fed_fomc_task612/fomccalendars.html"
INTEL_SNAPSHOT = ROOT / "data/raw/intelligence_task614/runtime_snapshots/20260607T035902Z"

SOURCE_FAMILIES = [
    "company_filings_ir",
    "earnings_guidance",
    "macro_policy_official",
    "supply_chain_customer_capex_cross_read",
    "positioning_liquidity_volatility",
    "sector_specialist_official_docs",
]

RELATION_PRIMITIVES = [
    "reinforces",
    "weakens",
    "invalidates",
    "conditions",
    "sequences",
    "explains",
    "contradicts",
    "source_gap_for",
    "noise_for",
]

AI_CAPEX_DEMAND_THEMES = {"cloud_ai_platforms"}
AI_CAPEX_SUPPLY_THEMES = {"ai_semiconductors", "power_grid_electrification", "industrial_automation_robotics"}
DEFENSE_THEMES = {"aerospace_defense_space"}
POLICY_SENSITIVE_THEMES = {"ai_semiconductors", "ev_autonomy_mobility", "crypto_fintech", "aerospace_defense_space"}

FAMILY_FIELDS = [
    "source_family",
    "attachment_state",
    "raw_source_rows",
    "covered_symbols",
    "covered_themes",
    "raw_source_examples",
    "coverage_note",
]

L1_FIELDS = [
    "evidence_id",
    "source_family",
    "symbol",
    "theme",
    "evidence_scope",
    "event_date",
    "published_ts",
    "received_ts",
    "available_to_brain_ts",
    "effective_ts",
    "source_name",
    "source_category",
    "source_url",
    "raw_storage_path",
    "raw_source_hash",
    "source_span_excerpt",
    "source_span_ref",
    "attachment_state",
    "source_gap_flag",
    "does_not_mean",
]

PRIMITIVE_FIELDS = [
    "primitive_fact_id",
    "evidence_id",
    "source_family",
    "symbol",
    "theme",
    "as_of_ts",
    "primitive_type",
    "primitive_state",
    "deterministic_rule_id",
    "source_span_ref",
    "reproducibility_hash",
    "uncertainty",
    "acceptance_state",
    "does_not_mean",
]

MEANING_FIELDS = [
    "economic_meaning_id",
    "primitive_fact_id",
    "evidence_id",
    "source_family",
    "symbol",
    "theme",
    "as_of_ts",
    "economic_channel",
    "meaning_state",
    "uncertainty",
    "does_not_mean",
]

RELATION_FIELDS = [
    "relation_edge_id",
    "decision_id",
    "decision_asof_ts",
    "split_id",
    "symbol",
    "theme",
    "relation_primitive",
    "mechanism_id",
    "edge_evidence_ids",
    "source_meaning_ids",
    "predecessor_node_id",
    "successor_node_id",
    "edge_asof_ts",
    "relation_authority",
    "does_not_mean",
]

CANDIDATE_FIELDS = [
    "candidate_bundle_id",
    "decision_id",
    "decision_asof_ts",
    "split_id",
    "symbol",
    "theme",
    "supporting_relation_ids",
    "contradicting_relation_ids",
    "invalidation_relation_ids",
    "source_gap_relation_ids",
    "supporting_evidence_ids",
    "contradicting_evidence_ids",
    "candidate_thesis_type",
    "contradiction_state",
    "invalidation_conditions",
    "weakest_layer",
    "unresolved_source_gaps",
    "adapter_eligible",
    "candidate_authority",
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
    "contradiction_state",
    "trade_spec_allowed",
    "diagnostic_replay_allowed",
    "decision_authority",
    "does_not_mean",
]

ADAPTER_SCHEMA_FIELDS = [
    "field_name",
    "required_for_adapter",
    "current_population_rule",
    "allowed_now",
    "blocks_backtest_if_missing",
    "notes",
]

ADAPTER_INPUT_FIELDS = [
    "adapter_input_id",
    "candidate_bundle_id",
    "trader_decision_id",
    "decision_asof_ts",
    "symbol",
    "theme",
    "source_graph_id",
    "supporting_evidence_ids",
    "contradicting_evidence_ids",
    "adapter_state",
    "side",
    "entry_rule",
    "exit_rule",
    "position_size_rule",
    "tradable_after_ts",
    "market_data_manifest_id",
    "cost_config_id",
    "slippage_config_id",
    "split_id",
    "ready_for_backtest",
    "blocked_reason",
]

SUMMARY_FIELDS = ["metric", "value"]

RELATION_CATALOG_FIELDS = [
    "relation_primitive",
    "definition",
    "allowed_trigger",
    "used_in_current_artifact",
    "absence_policy",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iso_date(date_value: str) -> str:
    if not date_value:
        return ""
    if "T" in date_value:
        return date_value
    return f"{date_value}T00:00:00Z"


def first_sentence(text: str, limit: int = 240) -> str:
    text = " ".join(text.replace("\r", " ").replace("\n", " ").split())
    return text[:limit]


def universe_maps() -> tuple[list[dict[str, str]], dict[str, str], dict[str, list[str]]]:
    rows = read_csv(UNIVERSE)
    symbol_theme = {row["symbol"]: row["theme"] for row in rows}
    theme_symbols: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        theme_symbols[row["theme"]].append(row["symbol"])
    return rows, symbol_theme, theme_symbols


def make_l1(
    source_family: str,
    symbol: str,
    theme: str,
    scope: str,
    event_date: str,
    source_name: str,
    category: str,
    url: str,
    path: Path,
    excerpt: str,
    suffix: object,
) -> dict[str, object]:
    source_hash = file_hash(path)
    span = first_sentence(excerpt)
    evidence_id = f"Task917|{source_family}|{stable_hash([symbol, theme, event_date, source_name, category, suffix])[:20]}"
    return {
        "evidence_id": evidence_id,
        "source_family": source_family,
        "symbol": symbol,
        "theme": theme,
        "evidence_scope": scope,
        "event_date": event_date,
        "published_ts": iso_date(event_date),
        "received_ts": iso_date(event_date),
        "available_to_brain_ts": iso_date(event_date),
        "effective_ts": iso_date(event_date),
        "source_name": source_name,
        "source_category": category,
        "source_url": url,
        "raw_storage_path": rel(path),
        "raw_source_hash": source_hash,
        "source_span_excerpt": span,
        "source_span_ref": stable_hash(span),
        "attachment_state": "attached_raw_external_source",
        "source_gap_flag": "raw_external_source_attached",
        "does_not_mean": "buy, sell, rank, score, sizing, or strategy acceptance",
    }


def load_task907_l1() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in read_csv(TASK907 / "task908_l1_sec_companyfacts_evidence.csv"):
        path = ROOT / row["raw_storage_path"]
        excerpt = (
            f"SEC companyfacts {row['form']} {row['source_concept']}={row['fact_value']} "
            f"{row['unit']} period_end={row['period_end']} accn={row['accession_or_document_id']}"
        )
        out.append(
            {
                "evidence_id": row["evidence_id"],
                "source_family": "company_filings_ir",
                "symbol": row["symbol"],
                "theme": row["theme"],
                "evidence_scope": "symbol",
                "event_date": row["published_ts"][:10],
                "published_ts": row["published_ts"],
                "received_ts": row["received_ts"],
                "available_to_brain_ts": row["available_to_brain_ts"],
                "effective_ts": row["period_end"],
                "source_name": "sec_companyfacts",
                "source_category": row["fact_family"],
                "source_url": row["raw_source_uri"],
                "raw_storage_path": row["raw_storage_path"],
                "raw_source_hash": file_hash(path) if path.exists() else row["raw_source_hash"],
                "source_span_excerpt": first_sentence(excerpt),
                "source_span_ref": stable_hash(excerpt),
                "attachment_state": "attached_raw_external_source",
                "source_gap_flag": "raw_external_source_attached",
                "does_not_mean": "buy, sell, rank, score, sizing, or strategy acceptance",
            }
        )
    return out


def load_task636_family_rows(symbol_theme: dict[str, str]) -> list[dict[str, object]]:
    source_rows = read_csv(TASK636_CHECKPOINT)
    out: list[dict[str, object]] = []
    per_family_symbol: dict[tuple[str, str], int] = defaultdict(int)
    for row in source_rows:
        symbols = [symbol for symbol in row["symbol_tags"].split(";") if symbol in symbol_theme]
        if not symbols or row["source_text_certified_flag"] != "1":
            continue
        if row["source_lane"] == "ceo_ir_transcripts_and_presentations":
            family = "earnings_guidance"
        elif row["source_lane"] == "institution_investment_actions":
            family = "positioning_liquidity_volatility"
        else:
            family = ""
        if not family:
            continue
        raw_path = ROOT / row["raw_text_path"]
        if not raw_path.exists():
            continue
        text = raw_path.read_text(encoding="utf-8", errors="ignore")
        for symbol in symbols:
            key = (family, symbol)
            if per_family_symbol[key] >= 5:
                continue
            per_family_symbol[key] += 1
            out.append(
                make_l1(
                    family,
                    symbol,
                    symbol_theme[symbol],
                    "symbol",
                    row["event_date"],
                    row["source_name"],
                    row["event_category"] or row["source_lane"],
                    row["source_url"],
                    raw_path,
                    text,
                    row["event_id"],
                )
            )
    return out


def load_macro_policy_rows(theme_symbols: dict[str, list[str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    fred_rows = read_csv(FRED_REPAIRED)
    for row in fred_rows:
        if row["observation_date"] > "2026-03-31":
            continue
        if row["series_id"] not in {"FEDFUNDS", "DGS10", "BAA10Y", "UNRATE", "CPIAUCSL"}:
            continue
        if row.get("value_change_3obs", "") == "":
            continue
        # Keep macro bounded: one row per series per quarter-ish first observation.
        month = row["observation_date"][:7]
        if not month.endswith(("-01", "-04", "-07", "-10")):
            continue
        for theme in POLICY_SENSITIVE_THEMES:
            path = FRED_REPAIRED
            excerpt = f"{row['series_id']} {row['description']} value={row['value']} observation={row['observation_date']} release={row['release_ts_utc']}"
            out.append(
                make_l1(
                    "macro_policy_official",
                    "",
                    theme,
                    "theme",
                    row["release_ts_utc"][:10],
                    "FRED",
                    row["category"],
                    row["source_url"],
                    path,
                    excerpt,
                    [row["series_id"], row["observation_date"], theme],
                )
            )
    if FOMC_HTML.exists():
        text = FOMC_HTML.read_text(encoding="utf-8", errors="ignore")
        for theme in POLICY_SENSITIVE_THEMES:
            out.append(
                make_l1(
                    "macro_policy_official",
                    "",
                    theme,
                    "theme",
                    "2026-03-31",
                    "Federal Reserve",
                    "fomc_calendar",
                    "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
                    FOMC_HTML,
                    text,
                    ["fomc_calendar", theme],
                )
            )
    return out[:240]


def load_sector_official_rows(theme_symbols: dict[str, list[str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    files = []
    if INTEL_SNAPSHOT.exists():
        files.extend(sorted((INTEL_SNAPSHOT / "geopolitical").glob("*.xml")))
        files.extend(sorted((INTEL_SNAPSHOT / "geopolitical").glob("ofac_recent_actions_page_*.html"))[:5])
        files.extend(sorted((INTEL_SNAPSHOT / "whitehouse").glob("*feed.xml"))[:4])
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for theme in DEFENSE_THEMES | POLICY_SENSITIVE_THEMES:
            out.append(
                make_l1(
                    "sector_specialist_official_docs",
                    "",
                    theme,
                    "theme",
                    "2026-03-31",
                    "official_policy_archive",
                    "policy_or_geopolitical_official_doc",
                    "",
                    path,
                    text,
                    [path.name, theme],
                )
            )
    return out[:80]


def load_supply_chain_cross_reads(task907_l1: list[dict[str, object]], symbol_theme: dict[str, str]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    eligible = [
        row
        for row in task907_l1
        if row["source_category"] in {"capex", "research_and_development", "assets", "revenue"}
        and row["theme"] in (AI_CAPEX_DEMAND_THEMES | AI_CAPEX_SUPPLY_THEMES)
    ]
    for row in eligible[:180]:
        source_path = ROOT / str(row["raw_storage_path"])
        if not source_path.exists():
            continue
        target_themes = AI_CAPEX_SUPPLY_THEMES if row["theme"] in AI_CAPEX_DEMAND_THEMES else AI_CAPEX_DEMAND_THEMES
        for target_theme in sorted(target_themes):
            out.append(
                make_l1(
                    "supply_chain_customer_capex_cross_read",
                    "",
                    target_theme,
                    "theme",
                    str(row["event_date"]),
                    "sec_companyfacts_cross_read",
                    str(row["source_category"]),
                    str(row["source_url"]),
                    source_path,
                    str(row["source_span_excerpt"]),
                    [row["evidence_id"], target_theme],
                )
            )
    return out[:240]


def build_family_manifest(l1_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for family in SOURCE_FAMILIES:
        rows = [row for row in l1_rows if row["source_family"] == family]
        out.append(
            {
                "source_family": family,
                "attachment_state": "attached" if rows else "missing",
                "raw_source_rows": len(rows),
                "covered_symbols": len({row["symbol"] for row in rows if row["symbol"]}),
                "covered_themes": len({row["theme"] for row in rows if row["theme"]}),
                "raw_source_examples": ";".join(sorted({str(row["raw_storage_path"]) for row in rows})[:5]),
                "coverage_note": "bounded_existing_raw_sources_no_synthetic_fill" if rows else "source_gap_not_negative",
            }
        )
    return out


def build_primitives(l1_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    type_map = {
        "company_filings_ir": "reported_company_fundamental_or_filing_fact",
        "earnings_guidance": "management_guidance_or_ir_context",
        "macro_policy_official": "macro_policy_condition_context",
        "supply_chain_customer_capex_cross_read": "supply_chain_capex_cross_read_context",
        "positioning_liquidity_volatility": "positioning_or_liquidity_context",
        "sector_specialist_official_docs": "sector_policy_specialist_context",
    }
    out: list[dict[str, object]] = []
    for idx, row in enumerate(l1_rows, start=1):
        rule = f"multifamily_primitive_v1::{row['source_family']}::{row['source_category']}"
        payload = [row["evidence_id"], row["source_span_ref"], rule]
        out.append(
            {
                "primitive_fact_id": f"PF918-{idx:06d}",
                "evidence_id": row["evidence_id"],
                "source_family": row["source_family"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "as_of_ts": row["available_to_brain_ts"],
                "primitive_type": type_map[str(row["source_family"])],
                "primitive_state": "source_backed_context",
                "deterministic_rule_id": rule,
                "source_span_ref": row["source_span_ref"],
                "reproducibility_hash": stable_hash(payload),
                "uncertainty": "symbol_direct" if row["evidence_scope"] == "symbol" else "theme_context_not_single_name_truth",
                "acceptance_state": "accepted_source_backed",
                "does_not_mean": "buy, sell, rank, score, sizing, or strategy acceptance",
            }
        )
    return out


def build_meanings(primitives: list[dict[str, object]]) -> list[dict[str, object]]:
    channel = {
        "company_filings_ir": "company_fundamental_context",
        "earnings_guidance": "management_expectation_context",
        "macro_policy_official": "macro_policy_condition",
        "supply_chain_customer_capex_cross_read": "customer_supplier_capex_transmission",
        "positioning_liquidity_volatility": "positioning_liquidity_context",
        "sector_specialist_official_docs": "sector_policy_condition",
    }
    out: list[dict[str, object]] = []
    for idx, row in enumerate(primitives, start=1):
        out.append(
            {
                "economic_meaning_id": f"EM918-{idx:06d}",
                "primitive_fact_id": row["primitive_fact_id"],
                "evidence_id": row["evidence_id"],
                "source_family": row["source_family"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "as_of_ts": row["as_of_ts"],
                "economic_channel": channel[str(row["source_family"])],
                "meaning_state": "source_backed_research_context",
                "uncertainty": row["uncertainty"],
                "does_not_mean": "buy, sell, rank, score, sizing, or strategy acceptance",
            }
        )
    return out


def relation_primitive_for(family: str, category: str, theme: str) -> str:
    if family == "earnings_guidance":
        return "explains"
    if family == "macro_policy_official":
        return "conditions"
    if family == "supply_chain_customer_capex_cross_read":
        return "reinforces"
    if family == "positioning_liquidity_volatility":
        if category in {"insider_or_sale_notice"}:
            return "weakens"
        if category in {"activist_13d"}:
            return "conditions"
        return "noise_for"
    if family == "sector_specialist_official_docs":
        return "conditions"
    if family == "company_filings_ir":
        return "explains"
    return "source_gap_for"


def build_relations(l1_rows: list[dict[str, object]], meanings: list[dict[str, object]]) -> list[dict[str, object]]:
    decisions = [row for row in read_csv(DECISIONS) if row["session_date"] <= "2026-03-31"]
    meaning_by_evidence = {row["evidence_id"]: row for row in meanings}
    rows_by_symbol_theme: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in l1_rows:
        key = (str(row["symbol"]), str(row["theme"]))
        rows_by_symbol_theme[key].append(row)
    out: list[dict[str, object]] = []
    idx = 1
    for decision in decisions:
        asof = decision["decision_asof_ts"]
        for key, rows in sorted(rows_by_symbol_theme.items()):
            available = [row for row in rows if str(row["available_to_brain_ts"]) <= asof]
            if not available:
                continue
            latest_by_family: dict[str, dict[str, object]] = {}
            for row in available:
                family = str(row["source_family"])
                if family not in latest_by_family or str(row["available_to_brain_ts"]) > str(latest_by_family[family]["available_to_brain_ts"]):
                    latest_by_family[family] = row
            for family, row in latest_by_family.items():
                primitive = relation_primitive_for(family, str(row["source_category"]), str(row["theme"]))
                meaning = meaning_by_evidence.get(str(row["evidence_id"]))
                out.append(
                    {
                        "relation_edge_id": f"RE919-{idx:07d}",
                        "decision_id": decision["decision_id"],
                        "decision_asof_ts": asof,
                        "split_id": decision["split_id"],
                        "symbol": row["symbol"],
                        "theme": row["theme"],
                        "relation_primitive": primitive,
                        "mechanism_id": f"{family}_to_{primitive}_v1",
                        "edge_evidence_ids": row["evidence_id"],
                        "source_meaning_ids": meaning["economic_meaning_id"] if meaning else "",
                        "predecessor_node_id": row["evidence_id"],
                        "successor_node_id": f"{row['symbol'] or row['theme']}|{decision['decision_id']}",
                        "edge_asof_ts": asof,
                        "relation_authority": "research_only_multifamily_source_backed",
                        "does_not_mean": "candidate approval, trade instruction, score, rank, or accepted graph",
                    }
                )
                idx += 1
            missing = [family for family in SOURCE_FAMILIES if family not in latest_by_family]
            for family in missing[:2]:
                out.append(
                    {
                        "relation_edge_id": f"RE919-{idx:07d}",
                        "decision_id": decision["decision_id"],
                        "decision_asof_ts": asof,
                        "split_id": decision["split_id"],
                        "symbol": key[0],
                        "theme": key[1],
                        "relation_primitive": "source_gap_for",
                        "mechanism_id": f"missing_{family}_v1",
                        "edge_evidence_ids": "",
                        "source_meaning_ids": "",
                        "predecessor_node_id": f"source_gap|{family}",
                        "successor_node_id": f"{key[0] or key[1]}|{decision['decision_id']}",
                        "edge_asof_ts": asof,
                        "relation_authority": "research_only_source_gap_not_negative",
                        "does_not_mean": "negative evidence, candidate rejection, trade instruction, score, or rank",
                    }
                )
                idx += 1
    return out


def build_candidates(relations: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in relations:
        grouped[(str(row["decision_id"]), str(row["symbol"]), str(row["theme"]))].append(row)
    out: list[dict[str, object]] = []
    idx = 1
    for (_decision_id, _symbol, _theme), rows in sorted(grouped.items()):
        supports = [row for row in rows if row["relation_primitive"] in {"reinforces", "explains", "conditions"}]
        contradicts = [row for row in rows if row["relation_primitive"] in {"weakens", "contradicts", "noise_for"}]
        invalidates = [row for row in rows if row["relation_primitive"] == "invalidates"]
        gaps = [row for row in rows if row["relation_primitive"] == "source_gap_for"]
        first = rows[0]
        contradiction_state = "contradiction_present" if supports and contradicts else "no_direct_contradiction"
        if invalidates:
            thesis = "blocked_by_invalidation"
        elif contradiction_state == "contradiction_present":
            thesis = "mixed_source_backed_watch_packet"
        elif len(supports) >= 2:
            thesis = "source_backed_watch_packet"
        else:
            thesis = "thin_or_gap_context_packet"
        out.append(
            {
                "candidate_bundle_id": f"CB919-{idx:07d}",
                "decision_id": first["decision_id"],
                "decision_asof_ts": first["decision_asof_ts"],
                "split_id": first["split_id"],
                "symbol": first["symbol"],
                "theme": first["theme"],
                "supporting_relation_ids": ";".join(str(row["relation_edge_id"]) for row in supports),
                "contradicting_relation_ids": ";".join(str(row["relation_edge_id"]) for row in contradicts),
                "invalidation_relation_ids": ";".join(str(row["relation_edge_id"]) for row in invalidates),
                "source_gap_relation_ids": ";".join(str(row["relation_edge_id"]) for row in gaps),
                "supporting_evidence_ids": ";".join(str(row["edge_evidence_ids"]) for row in supports if row["edge_evidence_ids"]),
                "contradicting_evidence_ids": ";".join(str(row["edge_evidence_ids"]) for row in contradicts if row["edge_evidence_ids"]),
                "candidate_thesis_type": thesis,
                "contradiction_state": contradiction_state,
                "invalidation_conditions": "invalidate_if_official_policy_blocks_core_theme_or_if_contradiction_edges_dominate",
                "weakest_layer": "source_family_gap" if gaps else "adapter_not_defined",
                "unresolved_source_gaps": ";".join(sorted({str(row["mechanism_id"]).replace("missing_", "").replace("_v1", "") for row in gaps})),
                "adapter_eligible": 0,
                "candidate_authority": "research_only_multifamily_l4",
                "does_not_mean": "side, entry, exit, position_size, score, rank, or strategy acceptance",
            }
        )
        idx += 1
    return out


def build_dry_decisions(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for idx, row in enumerate(candidates, start=1):
        if row["candidate_thesis_type"] == "blocked_by_invalidation":
            state = "skip_invalidation_present"
        elif row["contradiction_state"] == "contradiction_present":
            state = "review_only_watch_contradiction"
        elif row["candidate_thesis_type"] == "source_backed_watch_packet":
            state = "review_only_watch"
        else:
            state = "skip_source_thin"
        out.append(
            {
                "trader_decision_id": f"TD919-{idx:07d}",
                "candidate_bundle_id": row["candidate_bundle_id"],
                "decision_id": row["decision_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "split_id": row["split_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "decision_state": state,
                "decision_reason": row["candidate_thesis_type"],
                "contradiction_state": row["contradiction_state"],
                "trade_spec_allowed": 0,
                "diagnostic_replay_allowed": 0,
                "decision_authority": "dry_research_only_multifamily",
                "does_not_mean": "real trade, broker instruction, strategy acceptance, or real capital permission",
            }
        )
    return out


def build_adapter_schema() -> list[dict[str, object]]:
    return [
        {"field_name": "adapter_input_id", "required_for_adapter": 1, "current_population_rule": "stable generated id", "allowed_now": 1, "blocks_backtest_if_missing": 1, "notes": "lineage only"},
        {"field_name": "candidate_bundle_id", "required_for_adapter": 1, "current_population_rule": "L4 FK", "allowed_now": 1, "blocks_backtest_if_missing": 1, "notes": "must exist in L4"},
        {"field_name": "trader_decision_id", "required_for_adapter": 1, "current_population_rule": "L5 FK", "allowed_now": 1, "blocks_backtest_if_missing": 1, "notes": "must exist in L5"},
        {"field_name": "decision_asof_ts", "required_for_adapter": 1, "current_population_rule": "same as L5", "allowed_now": 1, "blocks_backtest_if_missing": 1, "notes": "as-of timestamp"},
        {"field_name": "symbol", "required_for_adapter": 1, "current_population_rule": "direct candidate symbol only", "allowed_now": 1, "blocks_backtest_if_missing": 1, "notes": "blank theme-level rows cannot trade"},
        {"field_name": "source_graph_id", "required_for_adapter": 1, "current_population_rule": "candidate relation ids hash", "allowed_now": 1, "blocks_backtest_if_missing": 1, "notes": "graph lineage"},
        {"field_name": "side", "required_for_adapter": 1, "current_population_rule": "not populated until explicit adapter policy", "allowed_now": 0, "blocks_backtest_if_missing": 1, "notes": "no inferred side"},
        {"field_name": "entry_rule", "required_for_adapter": 1, "current_population_rule": "not populated until adapter policy", "allowed_now": 0, "blocks_backtest_if_missing": 1, "notes": "no inferred entry"},
        {"field_name": "exit_rule", "required_for_adapter": 1, "current_population_rule": "not populated until adapter policy", "allowed_now": 0, "blocks_backtest_if_missing": 1, "notes": "no inferred exit"},
        {"field_name": "position_size_rule", "required_for_adapter": 1, "current_population_rule": "not populated until risk policy", "allowed_now": 0, "blocks_backtest_if_missing": 1, "notes": "no inferred sizing"},
        {"field_name": "tradable_after_ts", "required_for_adapter": 1, "current_population_rule": "not populated until execution calendar gate", "allowed_now": 0, "blocks_backtest_if_missing": 1, "notes": "must be > decision_asof_ts later"},
        {"field_name": "market_data_manifest_id", "required_for_adapter": 1, "current_population_rule": "not populated until market data gate", "allowed_now": 0, "blocks_backtest_if_missing": 1, "notes": "required before replay"},
        {"field_name": "cost_config_id", "required_for_adapter": 1, "current_population_rule": "not populated until cost gate", "allowed_now": 0, "blocks_backtest_if_missing": 1, "notes": "required before replay"},
        {"field_name": "slippage_config_id", "required_for_adapter": 1, "current_population_rule": "not populated until slippage gate", "allowed_now": 0, "blocks_backtest_if_missing": 1, "notes": "required before replay"},
    ]


def build_adapter_inputs(candidates: list[dict[str, object]], decisions: list[dict[str, object]]) -> list[dict[str, object]]:
    decision_by_bundle = {row["candidate_bundle_id"]: row for row in decisions}
    out: list[dict[str, object]] = []
    for idx, row in enumerate(candidates, start=1):
        decision = decision_by_bundle[row["candidate_bundle_id"]]
        relation_ids = ";".join(
            value
            for value in [
                str(row["supporting_relation_ids"]),
                str(row["contradicting_relation_ids"]),
                str(row["invalidation_relation_ids"]),
                str(row["source_gap_relation_ids"]),
            ]
            if value
        )
        out.append(
            {
                "adapter_input_id": f"AI920-{idx:07d}",
                "candidate_bundle_id": row["candidate_bundle_id"],
                "trader_decision_id": decision["trader_decision_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "source_graph_id": stable_hash(relation_ids),
                "supporting_evidence_ids": row["supporting_evidence_ids"],
                "contradicting_evidence_ids": row["contradicting_evidence_ids"],
                "adapter_state": "designed_blocked_not_trade_ready",
                "side": "",
                "entry_rule": "",
                "exit_rule": "",
                "position_size_rule": "",
                "tradable_after_ts": "",
                "market_data_manifest_id": "",
                "cost_config_id": "",
                "slippage_config_id": "",
                "split_id": row["split_id"],
                "ready_for_backtest": 0,
                "blocked_reason": "adapter_policy_trade_fields_market_data_cost_slippage_not_approved",
            }
        )
    return out


def build_relation_catalog(relations: list[dict[str, object]]) -> list[dict[str, object]]:
    used = {str(row["relation_primitive"]) for row in relations}
    definitions = {
        "reinforces": ("evidence supports an existing thesis mechanism", "source-backed support edge"),
        "weakens": ("evidence weakens but does not fully refute the thesis", "source-backed risk or dilution edge"),
        "invalidates": ("evidence directly breaks a thesis survival condition", "explicit official/source-backed invalidation only"),
        "conditions": ("evidence changes the regime or prerequisite for the thesis", "macro, policy, sector, or balance-sheet condition"),
        "sequences": ("evidence follows another evidence item in a required order", "two source-backed events with explicit temporal order"),
        "explains": ("evidence explains a mechanism without being a trade signal", "fundamental, guidance, or policy explanation"),
        "contradicts": ("evidence directly conflicts with another source-backed claim", "two source-backed claims with opposing content"),
        "source_gap_for": ("required source family is missing for a candidate", "missing source family; never treated as negative"),
        "noise_for": ("evidence is retained as context but too noisy for thesis support", "positioning, disclosure, or broad context edge"),
    }
    out: list[dict[str, object]] = []
    for primitive in RELATION_PRIMITIVES:
        definition, trigger = definitions[primitive]
        out.append(
            {
                "relation_primitive": primitive,
                "definition": definition,
                "allowed_trigger": trigger,
                "used_in_current_artifact": 1 if primitive in used else 0,
                "absence_policy": "do_not_synthesize_edge_without_source_backed_trigger",
            }
        )
    return out


def run(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    _universe, symbol_theme, theme_symbols = universe_maps()
    base_l1 = load_task907_l1()
    extra_l1 = []
    extra_l1.extend(load_task636_family_rows(symbol_theme))
    extra_l1.extend(load_macro_policy_rows(theme_symbols))
    extra_l1.extend(load_sector_official_rows(theme_symbols))
    extra_l1.extend(load_supply_chain_cross_reads(base_l1, symbol_theme))
    l1_rows = base_l1 + extra_l1
    family_manifest = build_family_manifest(l1_rows)
    primitives = build_primitives(l1_rows)
    meanings = build_meanings(primitives)
    relations = build_relations(l1_rows, meanings)
    relation_catalog = build_relation_catalog(relations)
    candidates = build_candidates(relations)
    dry_decisions = build_dry_decisions(candidates)
    adapter_schema = build_adapter_schema()
    adapter_inputs = build_adapter_inputs(candidates, dry_decisions)
    summary = {
        "task_id": "Task917-920",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority": "RESEARCH_ONLY_MULTIFAMILY_L1_L5_ADAPTER_DESIGN",
        "source_families_expected": len(SOURCE_FAMILIES),
        "source_families_attached": sum(1 for row in family_manifest if row["attachment_state"] == "attached"),
        "l1_evidence_rows": len(l1_rows),
        "primitive_fact_rows": len(primitives),
        "economic_meaning_rows": len(meanings),
        "relation_edge_rows": len(relations),
        "relation_primitives_used": len({row["relation_primitive"] for row in relations}),
        "relation_primitive_catalog_rows": len(relation_catalog),
        "candidate_bundle_rows": len(candidates),
        "candidate_bundles_with_contradiction": sum(1 for row in candidates if row["contradiction_state"] == "contradiction_present"),
        "dry_decision_rows": len(dry_decisions),
        "adapter_schema_rows": len(adapter_schema),
        "adapter_input_rows": len(adapter_inputs),
        "ready_for_backtest_rows": sum(int(row["ready_for_backtest"]) for row in adapter_inputs),
        "diagnostic_replay_status": "not_run_adapter_design_only",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    write_csv(out_dir / "task917_source_family_attachment_manifest.csv", family_manifest, FAMILY_FIELDS)
    write_csv(out_dir / "task917_multifamily_l1_evidence.csv", l1_rows, L1_FIELDS)
    write_csv(out_dir / "task918_multifamily_l2_primitives.csv", primitives, PRIMITIVE_FIELDS)
    write_csv(out_dir / "task918_multifamily_l2_meanings.csv", meanings, MEANING_FIELDS)
    write_csv(out_dir / "task919_relation_edges_9primitive.csv", relations, RELATION_FIELDS)
    write_csv(out_dir / "task919_relation_primitive_catalog.csv", relation_catalog, RELATION_CATALOG_FIELDS)
    write_csv(out_dir / "task919_l4_candidate_bundles_contradiction.csv", candidates, CANDIDATE_FIELDS)
    write_csv(out_dir / "task919_l5_dry_decisions.csv", dry_decisions, DRY_DECISION_FIELDS)
    write_csv(out_dir / "task920_adapter_input_schema.csv", adapter_schema, ADAPTER_SCHEMA_FIELDS)
    write_csv(out_dir / "task920_adapter_input_design_rows.csv", adapter_inputs, ADAPTER_INPUT_FIELDS)
    (out_dir / "task917_920_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    write_csv(out_dir / "task917_920_summary.csv", [{"metric": k, "value": v} for k, v in summary.items()], SUMMARY_FIELDS)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[TRADER_BRAIN_917_920_MULTIFAMILY_OK] "
        f"families={summary['source_families_attached']}/{summary['source_families_expected']} "
        f"l1={summary['l1_evidence_rows']} relations={summary['relation_edge_rows']} "
        f"candidates={summary['candidate_bundle_rows']} adapter_rows={summary['adapter_input_rows']} "
        f"ready={summary['ready_for_backtest_rows']}"
    )


if __name__ == "__main__":
    main()
