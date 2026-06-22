from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1141 = ROOT / "data/artifacts/task_1141_1150_external_source_acquisition"
TASK1834 = ROOT / "data/artifacts/task_1834_1847_targeted_source_implementation"
TASK2001 = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
TASK2011 = ROOT / "data/artifacts/task_2011_2020_subagent_source_discovery"
TASK2021 = ROOT / "data/artifacts/task_2021_2030_sec_8k_ex99_ir_ceo_extractor"
OUT_DIR = ROOT / "data/artifacts/task_2031_2060_free_official_source_layers"
RAW_OUT = ROOT / "data/raw/task_2031_2060_free_official_source_layers"
REPORT_DIR = ROOT / "docs/reports/task_2031_2060_free_official_source_layers"
REPORT = REPORT_DIR / "task_2031_2060_free_official_source_layers.md"
DECISION = REPORT_DIR / "task_2031_2060_decision.csv"
AUTHORITY = "DIAGNOSTIC_FREE_OFFICIAL_SOURCE_LAYERS_ONLY"
POLICY_ID = "winner_accel_top5_to_top2_convex_v1"

DOCUMENT_RE = re.compile(r"<DOCUMENT>(.*?)</DOCUMENT>", re.I | re.S)
TEXT_RE = re.compile(r"<TEXT>(.*?)</TEXT>", re.I | re.S)

CHAIN_THEME_MAP = {
    "accelerator_compute": ["ai_semiconductors", "cloud_ai_platforms"],
    "semiconductor_broad_cycle": ["ai_semiconductors"],
    "semiconductor_equipment": ["ai_semiconductors", "industrial_automation_robotics"],
    "datacenter_connectivity": ["cloud_ai_platforms", "ai_semiconductors"],
    "power_grid_cooling": ["power_grid_electrification"],
    "software_ai_monetization": ["cloud_ai_platforms", "data_devops_software"],
}

CHAIN_KEYWORDS = {
    "accelerator_compute": ["semiconductor", "chip", "artificial intelligence", "ai", "cloud", "export", "data center"],
    "semiconductor_broad_cycle": ["semiconductor", "chip", "wafer", "export", "manufacturing"],
    "semiconductor_equipment": ["semiconductor", "manufacturing", "equipment", "export", "wafer"],
    "datacenter_connectivity": ["cloud", "data center", "network", "artificial intelligence", "ai"],
    "power_grid_cooling": ["power grid", "electricity", "energy", "transmission", "nuclear"],
    "software_ai_monetization": ["artificial intelligence", "ai", "cloud", "data", "cybersecurity"],
}

POLICY_FAMILIES = {
    "export_control_or_trade": ["export", "import", "tariff", "trade", "international trade commission"],
    "federal_funding_or_procurement": ["funding", "grant", "award", "procurement", "contract"],
    "ai_security_or_cloud_regulation": ["artificial intelligence", "ai", "cloud", "cybersecurity", "data security"],
    "energy_grid_or_power_policy": ["power grid", "electricity", "energy", "transmission", "nuclear"],
    "competition_or_market_structure": ["competition", "antitrust", "market", "public interest"],
    "compliance_or_reporting": ["rule", "regulation", "notice", "compliance", "reporting"],
}

CUSTOMER_FAMILIES = {
    "customer_demand_claim": ["customer", "customers", "demand", "bookings", "orders", "backlog"],
    "contract_or_award_claim": ["contract", "agreement", "award", "purchase order", "supply agreement"],
    "design_win_claim": ["design win", "design-win", "platform win", "customer win"],
    "datacenter_or_cloud_customer_claim": ["hyperscale", "cloud", "data center", "datacenter", "enterprise"],
}

NAMED_COUNTERPARTIES = [
    "microsoft",
    "amazon",
    "aws",
    "oracle",
    "google",
    "meta",
    "nvidia",
    "openai",
    "crane",
    "constellation",
]


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


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_ts(value: str) -> datetime | None:
    try:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_publication_date(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def clean_text(value: str, max_chars: int = 160_000) -> str:
    text = re.sub(r"<script.*?</script>", " ", value, flags=re.I | re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def tag_value(doc: str, tag: str) -> str:
    match = re.search(rf"<{tag}>\s*([^\n\r<]+)", doc, flags=re.I)
    return match.group(1).strip() if match else ""


def document_text(doc: str) -> str:
    match = TEXT_RE.search(doc)
    return match.group(1) if match else doc


def family_hits(text: str, family_map: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    families = []
    keywords = []
    for family, terms in family_map.items():
        hit_terms = [term for term in terms if term in lowered]
        if hit_terms:
            families.append(family)
            keywords.extend(hit_terms[:4])
    return sorted(set(families)), sorted(set(keywords))


def bounded_snippet(text: str, keywords: list[str]) -> str:
    lowered = text.lower()
    positions = [lowered.find(keyword.lower()) for keyword in keywords if lowered.find(keyword.lower()) >= 0]
    pos = min(positions) if positions else 0
    start = max(0, pos - 240)
    end = min(len(text), pos + 720)
    return text[start:end]


def counterparty_fields(text: str) -> tuple[str, str, str, str]:
    lowered = text.lower()
    hits = sorted(
        {
            name for name in NAMED_COUNTERPARTIES
            if re.search(rf"(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])", lowered)
        }
    )
    duration_match = re.search(r"\b(\d+)[-\s]?(year|yr)\b", lowered)
    amount_match = re.search(r"\$[0-9][0-9,.]*(?:\s?(?:million|billion|m|bn))?", text, re.I)
    contract_terms = ["power purchase agreement", "purchase agreement", "supply agreement", "contract", "award"]
    contract_type = next((term for term in contract_terms if term in lowered), "")
    directness = "named_counterparty_contract_claim" if hits and contract_type else "named_counterparty_context" if hits else "issuer_customer_context"
    duration = duration_match.group(0) if duration_match else ""
    amount = amount_match.group(0) if amount_match else ""
    return "|".join(hits), contract_type, duration or amount, directness


def customer_doc_quality(doc_type: str, families: list[str], directness: str) -> tuple[bool, str]:
    dtype = doc_type.upper().strip()
    family_set = set(families)
    if dtype.startswith("EX-10") and "contract_or_award_claim" in family_set:
        return True, "issuer_contract_exhibit_claim"
    if dtype.startswith("EX-99") and directness == "named_counterparty_contract_claim":
        return True, "issuer_ex99_named_counterparty_contract_claim"
    if dtype.startswith("EX-99") and family_set & {"design_win_claim", "datacenter_or_cloud_customer_claim"}:
        return True, "issuer_ex99_customer_momentum_claim"
    if dtype in {"8-K", "FORM 8-K"} and directness == "named_counterparty_contract_claim":
        return True, "issuer_8k_named_counterparty_contract_claim"
    return False, "reference_only_generic_customer_language"


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "scope": read_csv(TASK2001 / "task2004_aggressive_source_extraction_panel.csv"),
        "fr_panel": read_csv(TASK1141 / "task1145_federal_register_policy_archive_panel.csv"),
        "sec_packets": read_csv(TASK1834 / "task1836_sec_financing_dilution_source_packets.csv"),
        "ir_gate": read_csv(TASK2021 / "task2026_ir_ceo_gate_delta.csv"),
        "symbol_priority": read_csv(TASK2011 / "task2013_aggressive_symbol_source_priority.csv"),
    }


def source_contract_rows() -> list[dict[str, object]]:
    rows = [
        ("Federal Register API", "policy_news", "free_official_no_key", "https://www.federalregister.gov/developers/documentation/api/v1", "keyless_public_api; official PDF links route to GovInfo"),
        ("GovInfo Developer Hub", "policy_news", "free_official_api_key_or_bulk", "https://www.govinfo.gov/developers", "official GPO source; API key may be needed for API, bulk data exists"),
        ("USAspending API", "customer_contract", "free_official_no_key_docs", "https://api.usaspending.gov/docs/endpoints", "federal award source; entity matching still requires strict recipient identity"),
        ("SEC EDGAR complete submissions", "issuer_contract_claim", "free_official_local", "https://www.sec.gov/search-filings/edgar-application-programming-interfaces", "issuer-side official filing source; not independent customer confirmation"),
    ]
    return [
        {
            "task_id": "Task2031",
            "source_contract_id": f"FREEOFFICIAL-2031-{idx:03d}",
            "source_name": name,
            "source_family": family,
            "free_source_status": status,
            "documentation_url": url,
            "implementation_note": note,
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, family, status, url, note) in enumerate(rows, start=1)
    ]


def load_federal_register_docs(fr_panel: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    idx = 1
    for panel in fr_panel:
        raw_path = ROOT / panel["raw_source_path"]
        if not raw_path.exists() or panel.get("download_status") != "downloaded":
            continue
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        for result in payload.get("results", []):
            text = " ".join(
                str(result.get(key, "") or "")
                for key in ["title", "abstract", "excerpts", "type"]
            )
            clean = clean_text(text, max_chars=20_000)
            families, keyword_hits = family_hits(clean, POLICY_FAMILIES)
            pub_ts = parse_publication_date(result["publication_date"])
            agency_names = "|".join(sorted({agency.get("name", "") for agency in result.get("agencies", []) if agency.get("name")}))
            rows.append(
                {
                    "task_id": "Task2032",
                    "policy_source_doc_id": f"POLICYDOC-2032-{idx:07d}",
                    "provider": "Federal Register",
                    "theme": panel["theme"],
                    "search_term": panel["search_term"],
                    "document_number": result.get("document_number", ""),
                    "title": result.get("title", ""),
                    "document_type": result.get("type", ""),
                    "agency_names": agency_names,
                    "publication_date": result.get("publication_date", ""),
                    "publication_ts": pub_ts.isoformat(),
                    "available_to_brain_ts": pub_ts.isoformat(),
                    "official_source_url": result.get("html_url", ""),
                    "official_pdf_url": result.get("pdf_url", ""),
                    "raw_source_path": panel["raw_source_path"],
                    "raw_source_sha256": panel["source_hash"],
                    "policy_family_hits": "|".join(families),
                    "keyword_hits": "|".join(keyword_hits),
                    "source_text_hash": sha256_text(clean),
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def policy_match_rows(scope: list[dict[str, str]], docs: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    docs_by_theme: dict[str, list[dict[str, object]]] = defaultdict(list)
    for doc in docs:
        docs_by_theme[str(doc["theme"])].append(doc)
    for theme_docs in docs_by_theme.values():
        theme_docs.sort(key=lambda row: str(row["publication_ts"]), reverse=True)

    matches = []
    rejections = []
    match_idx = 1
    reject_idx = 1
    for trade in scope:
        chain = trade["beneficiary_chain"]
        decision = parse_ts(trade["decision_asof_ts"])
        themes = CHAIN_THEME_MAP.get(chain, [])
        keywords = CHAIN_KEYWORDS.get(chain, [])
        if not themes or not decision:
            rejections.append(
                {
                    "task_id": "Task2034",
                    "policy_rejection_id": f"POLICYREJECT-2034-{reject_idx:06d}",
                    "trade_spec_id": trade["trade_spec_id"],
                    "symbol": trade["symbol"],
                    "decision_asof_ts": trade["decision_asof_ts"],
                    "beneficiary_chain": chain,
                    "reason": "uncertified_or_missing_beneficiary_chain",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            reject_idx += 1
            continue
        candidates = []
        for theme in themes:
            for doc in docs_by_theme.get(theme, []):
                pub_ts = parse_ts(str(doc["publication_ts"]))
                if not pub_ts or pub_ts > decision or pub_ts < decision - timedelta(days=540):
                    continue
                text = " ".join([str(doc.get("title", "")), str(doc.get("policy_family_hits", "")), str(doc.get("keyword_hits", ""))]).lower()
                keyword_score = sum(1 for keyword in keywords if keyword in text)
                if keyword_score == 0:
                    continue
                family_score = len(str(doc.get("policy_family_hits", "")).split("|")) if doc.get("policy_family_hits") else 0
                recency_days = (decision - pub_ts).days
                score = keyword_score * 10 + family_score * 3 - min(recency_days, 540) / 180
                candidates.append((score, recency_days, doc))
        if not candidates:
            rejections.append(
                {
                    "task_id": "Task2034",
                    "policy_rejection_id": f"POLICYREJECT-2034-{reject_idx:06d}",
                    "trade_spec_id": trade["trade_spec_id"],
                    "symbol": trade["symbol"],
                    "decision_asof_ts": trade["decision_asof_ts"],
                    "beneficiary_chain": chain,
                    "reason": "no_prior_theme_keyword_policy_doc",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            reject_idx += 1
            continue
        candidates.sort(key=lambda item: (-item[0], item[1], str(item[2]["document_number"])))
        for rank, (score, recency_days, doc) in enumerate(candidates[:3], start=1):
            matches.append(
                {
                    "task_id": "Task2033",
                    "policy_l1_packet_id": f"POLICYL1-2033-{match_idx:07d}",
                    "trade_spec_id": trade["trade_spec_id"],
                    "candidate_source_id": trade["candidate_source_id"],
                    "symbol": trade["symbol"],
                    "decision_asof_ts": trade["decision_asof_ts"],
                    "beneficiary_chain": chain,
                    "match_rank": rank,
                    "policy_source_doc_id": doc["policy_source_doc_id"],
                    "provider": doc["provider"],
                    "theme": doc["theme"],
                    "matching_key": "beneficiary_chain_theme_keyword_prior_asof",
                    "policy_match_score": round(score, 6),
                    "recency_days": recency_days,
                    "publication_ts": doc["publication_ts"],
                    "available_to_brain_ts": doc["available_to_brain_ts"],
                    "official_source_url": doc["official_source_url"],
                    "official_pdf_url": doc["official_pdf_url"],
                    "raw_source_path": doc["raw_source_path"],
                    "raw_source_sha256": doc["raw_source_sha256"],
                    "policy_family_hits": doc["policy_family_hits"],
                    "keyword_hits": doc["keyword_hits"],
                    "asof_guard_pass": "1",
                    "inferred_matching_used": "0",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            match_idx += 1
    return matches, rejections


def policy_l2_l3_l4_l5(matches: list[dict[str, object]], scope: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    best_by_spec: dict[str, dict[str, object]] = {}
    for row in matches:
        spec = str(row["trade_spec_id"])
        current = best_by_spec.get(spec)
        score = float(row["policy_match_score"])
        if current is None or score > float(current["policy_match_score"]):
            best_by_spec[spec] = row
    l2 = []
    l3 = []
    l4 = []
    l5 = []
    scope_by_spec = {row["trade_spec_id"]: row for row in scope}
    for idx, (spec, row) in enumerate(sorted(best_by_spec.items()), start=1):
        families = set(str(row.get("policy_family_hits", "")).split("|")) if row.get("policy_family_hits") else set()
        if families & {"export_control_or_trade", "compliance_or_reporting"}:
            state = "policy_risk_or_constraint_context"
            relation = "routes_to_policy_risk_budget"
        elif families & {"federal_funding_or_procurement", "energy_grid_or_power_policy"}:
            state = "policy_demand_or_funding_tailwind"
            relation = "supports_external_catalyst_context"
        elif families & {"ai_security_or_cloud_regulation", "competition_or_market_structure"}:
            state = "policy_mixed_market_structure_context"
            relation = "modifies_payoff_and_risk_context"
        else:
            state = "policy_low_signal_context"
            relation = "reference_only_low_signal"
        l2_id = f"POLICYL2-2035-{idx:06d}"
        l3_id = f"POLICYL3-2036-{idx:06d}"
        l4_id = f"POLICYL4-2037-{idx:06d}"
        l5_id = f"POLICYGATE-2038-{idx:06d}"
        l2.append(
            {
                "task_id": "Task2035",
                "policy_l2_semantic_id": l2_id,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "policy_l1_packet_id": row["policy_l1_packet_id"],
                "policy_semantic_state": state,
                "policy_family_hits": row["policy_family_hits"],
                "policy_source_doc_id": row["policy_source_doc_id"],
                "asof_guard_pass": "1",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l3.append(
            {
                "task_id": "Task2036",
                "policy_l3_edge_id": l3_id,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "from_policy_l2_semantic_id": l2_id,
                "mechanism_edge": relation,
                "relation_type": "policy_context_modifier",
                "asof_guard_pass": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l4.append(
            {
                "task_id": "Task2037",
                "policy_l4_thesis_id": l4_id,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "policy_l3_edge_id": l3_id,
                "policy_thesis_modifier": state,
                "policy_source_depth": "official_theme_prior_asof",
                "can_directly_create_trade": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l5.append(
            {
                "task_id": "Task2038",
                "policy_l5_gate_id": l5_id,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "policy_news_extractor_state": "attached_asof_official_policy_context",
                "policy_news_family_gate_pass": "1",
                "paper_shadow_trade_allowed_after_policy_only": "0",
                "paper_shadow_blocker": "other_source_families_still_required",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    present = set(best_by_spec)
    for row in scope:
        if row["trade_spec_id"] in present:
            continue
        l5.append(
            {
                "task_id": "Task2038",
                "policy_l5_gate_id": f"POLICYGATE-2038-GAP-{len(l5)+1:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "policy_news_extractor_state": "source_gap_neutral",
                "policy_news_family_gate_pass": "0",
                "paper_shadow_trade_allowed_after_policy_only": "0",
                "paper_shadow_blocker": "other_source_families_still_required",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return l2, l3, l4, l5


def customer_contract_docs(scope: list[dict[str, str]], sec_packets: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    scope_by_spec = {row["trade_spec_id"]: row for row in scope}
    scope_ids = set(scope_by_spec)
    rows = []
    rejections = []
    doc_idx = 1
    reject_idx = 1
    for packet in sec_packets:
        spec = packet.get("trade_spec_id", "")
        if spec not in scope_ids or packet.get("form") not in {"8-K", "8-K/A"}:
            continue
        if packet.get("asof_guard_pass") != "1" or packet.get("inferred_matching_used") != "0":
            continue
        decision = parse_ts(scope_by_spec[spec]["decision_asof_ts"])
        available = parse_ts(packet.get("available_to_brain_ts", ""))
        path = ROOT / packet.get("local_path", "")
        if not path.exists() or not decision or not available or available > decision:
            rejections.append(
                {
                    "task_id": "Task2044",
                    "customer_rejection_id": f"CUSTREJECT-2044-{reject_idx:06d}",
                    "trade_spec_id": spec,
                    "symbol": packet.get("symbol", ""),
                    "reason": "missing_raw_or_asof_fail",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            reject_idx += 1
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        docs = DOCUMENT_RE.findall(raw) or [raw]
        detected = 0
        for seq, doc in enumerate(docs, start=1):
            doc_type = tag_value(doc, "TYPE") or packet.get("document_type", "")
            filename = tag_value(doc, "FILENAME") or packet.get("primary_document", "")
            description = tag_value(doc, "DESCRIPTION")
            text = clean_text(document_text(doc))
            families, keywords = family_hits(text, CUSTOMER_FAMILIES)
            if not families:
                continue
            dtype = doc_type.upper().strip()
            if not (dtype.startswith("EX-10") or dtype.startswith("EX-99") or dtype in {"8-K", "FORM 8-K"}):
                continue
            counterparty_names, contract_type, contract_term_or_amount, directness = counterparty_fields(text)
            gate_eligible, source_quality_state = customer_doc_quality(doc_type, families, directness)
            if not gate_eligible:
                continue
            detected += 1
            out_dir = RAW_OUT / "customer_contract_claims" / packet["symbol"] / packet["accession"]
            out_dir.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", filename or f"document_{seq}.txt")[:120]
            out_path = out_dir / f"{seq:02d}_{safe_name}.txt"
            snippet = bounded_snippet(text, keywords)
            out_path.write_text(snippet, encoding="utf-8")
            rows.append(
                {
                    "task_id": "Task2041",
                    "customer_contract_doc_id": f"CUSTDOC-2041-{doc_idx:07d}",
                    "trade_spec_id": spec,
                    "candidate_source_id": packet["candidate_source_id"],
                    "symbol": packet["symbol"],
                    "decision_asof_ts": scope_by_spec[spec]["decision_asof_ts"],
                    "cik": packet.get("cik", ""),
                    "accession": packet.get("accession", ""),
                    "form": packet.get("form", ""),
                    "document_sequence": seq,
                    "document_type": doc_type,
                    "document_filename": filename,
                    "document_description": description,
                    "source_side": "issuer_sec_filing",
                    "source_quality_state": source_quality_state,
                    "customer_claim_gate_eligible": "1",
                    "independent_customer_confirmation": "0",
                    "counterparty_name": counterparty_names,
                    "named_counterparty_flag": "1" if counterparty_names else "0",
                    "contract_type": contract_type,
                    "contract_term_or_amount": contract_term_or_amount,
                    "directness_score": directness,
                    "acceptance_datetime": packet.get("acceptance_datetime", ""),
                    "available_to_brain_ts": packet.get("available_to_brain_ts", ""),
                    "sec_url": packet.get("sec_url", ""),
                    "complete_submission_local_path": packet.get("local_path", ""),
                    "complete_submission_sha256": packet.get("sha256", ""),
                    "snippet_local_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                    "snippet_sha256": file_sha256(out_path),
                    "customer_contract_family_hits": "|".join(families),
                    "keyword_hits": "|".join(keywords),
                    "asof_guard_pass": "1",
                    "inferred_matching_used": "0",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            doc_idx += 1
        if detected == 0:
            rejections.append(
                {
                    "task_id": "Task2044",
                    "customer_rejection_id": f"CUSTREJECT-2044-{reject_idx:06d}",
                    "trade_spec_id": spec,
                    "symbol": packet.get("symbol", ""),
                    "reason": "no_issuer_customer_contract_claim_detected",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            reject_idx += 1
    return rows, rejections


def customer_l2_l3_l4_l5(docs: list[dict[str, object]], scope: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    best_by_spec: dict[str, dict[str, object]] = {}
    for doc in docs:
        spec = str(doc["trade_spec_id"])
        score = len(str(doc.get("customer_contract_family_hits", "")).split("|")) if doc.get("customer_contract_family_hits") else 0
        if spec not in best_by_spec or score > int(best_by_spec[spec]["_score"]):
            row = dict(doc)
            row["_score"] = score
            best_by_spec[spec] = row
    l2 = []
    l3 = []
    l4 = []
    l5 = []
    for idx, (spec, row) in enumerate(sorted(best_by_spec.items()), start=1):
        families = set(str(row.get("customer_contract_family_hits", "")).split("|")) if row.get("customer_contract_family_hits") else set()
        if families & {"contract_or_award_claim", "design_win_claim"}:
            state = "issuer_claim_contract_or_design_win"
            relation = "issuer_claim_supports_revenue_validation_but_needs_independent_confirmation"
        elif families & {"customer_demand_claim", "datacenter_or_cloud_customer_claim"}:
            state = "issuer_claim_customer_demand"
            relation = "issuer_claim_supports_demand_context_but_needs_independent_confirmation"
        else:
            state = "issuer_customer_claim_low_signal"
            relation = "reference_only_low_signal"
        l2_id = f"CUSTL2-2042-{idx:06d}"
        l3_id = f"CUSTL3-2043-{idx:06d}"
        l4_id = f"CUSTL4-2045-{idx:06d}"
        l2.append(
            {
                "task_id": "Task2042",
                "customer_l2_semantic_id": l2_id,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "customer_contract_doc_id": row["customer_contract_doc_id"],
                "customer_contract_semantic_state": state,
                "customer_contract_family_hits": row["customer_contract_family_hits"],
                "counterparty_name": row.get("counterparty_name", ""),
                "named_counterparty_flag": row.get("named_counterparty_flag", "0"),
                "contract_type": row.get("contract_type", ""),
                "contract_term_or_amount": row.get("contract_term_or_amount", ""),
                "directness_score": row.get("directness_score", "issuer_customer_context"),
                "independent_customer_confirmation": "0",
                "asof_guard_pass": "1",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l3.append(
            {
                "task_id": "Task2043",
                "customer_l3_edge_id": l3_id,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "from_customer_l2_semantic_id": l2_id,
                "mechanism_edge": relation,
                "relation_type": "issuer_claim_requires_independent_confirmation",
                "asof_guard_pass": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l4.append(
            {
                "task_id": "Task2045",
                "customer_l4_thesis_id": l4_id,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "customer_l3_edge_id": l3_id,
                "customer_thesis_modifier": state,
                "independent_confirmation_required": "1",
                "can_directly_create_trade": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    present = set(best_by_spec)
    for idx, row in enumerate(scope, start=1):
        attached = row["trade_spec_id"] in present
        l5.append(
            {
                "task_id": "Task2046",
                "customer_l5_gate_id": f"CUSTGATE-2046-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "contract_customer_extractor_state": "issuer_claim_attached_independent_gap" if attached else "source_gap_neutral",
                "issuer_customer_claim_attached": "1" if attached else "0",
                "independent_customer_confirmation_gate_pass": "0",
                "paper_shadow_trade_allowed_after_customer_only": "0",
                "paper_shadow_blocker": "independent_customer_confirmation_or_other_source_families_required",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return l2, l3, l4, l5


def loop_audit_rows() -> list[dict[str, object]]:
    audit = [
        ("loop1_policy_news", "Federal Register official theme evidence can attach only through beneficiary_chain + theme + keyword + prior as-of; uncertified chains stay source_gap_neutral.", "implemented"),
        ("loop2_customer_contract", "Issuer SEC customer/contract claims are useful L2/L3 evidence but are not independent customer confirmation.", "implemented_gate_block"),
        ("loop3_full_gate", "Full-source gate remains blocked until earnings call, independent customer confirmation, and analyst/PIT revision gates are satisfied.", "implemented"),
    ]
    return [
        {
            "task_id": "Task2051",
            "loop_audit_id": f"LOOPAUDIT-2051-{idx:03d}",
            "loop_name": loop,
            "finding": finding,
            "implementation_decision": decision,
            "review_authority": "SUBAGENT_AND_GPT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (loop, finding, decision) in enumerate(audit, start=1)
    ]


def integrated_gate_rows(scope: list[dict[str, str]], ir_gate: list[dict[str, str]], policy_gate: list[dict[str, object]], customer_gate: list[dict[str, object]]) -> list[dict[str, object]]:
    ir_by_spec = {row["trade_spec_id"]: row for row in ir_gate}
    policy_by_spec = {str(row["trade_spec_id"]): row for row in policy_gate}
    customer_by_spec = {str(row["trade_spec_id"]): row for row in customer_gate}
    rows = []
    for idx, row in enumerate(scope, start=1):
        spec = row["trade_spec_id"]
        ir_pass = ir_by_spec.get(spec, {}).get("ir_ceo_family_gate_pass", "0")
        policy_pass = str(policy_by_spec.get(spec, {}).get("policy_news_family_gate_pass", "0"))
        issuer_customer_claim = str(customer_by_spec.get(spec, {}).get("issuer_customer_claim_attached", "0"))
        independent_customer_pass = str(customer_by_spec.get(spec, {}).get("independent_customer_confirmation_gate_pass", "0"))
        earnings_call_pass = "0"
        analyst_revision_pass = "0"
        source_depth_score = sum(int(value) for value in [ir_pass, policy_pass, issuer_customer_claim])
        full_pass = all(value == "1" for value in [ir_pass, policy_pass, independent_customer_pass, earnings_call_pass, analyst_revision_pass])
        blocker_parts = []
        if ir_pass != "1":
            blocker_parts.append("ir_ceo_ex99_gap")
        if policy_pass != "1":
            blocker_parts.append("policy_news_gap")
        if independent_customer_pass != "1":
            blocker_parts.append("independent_customer_confirmation_gap")
        if earnings_call_pass != "1":
            blocker_parts.append("earnings_call_vendor_or_source_gap")
        if analyst_revision_pass != "1":
            blocker_parts.append("analyst_revision_pit_gap")
        rows.append(
            {
                "task_id": "Task2052",
                "integrated_gate_id": f"FULLGATE-2052-{idx:06d}",
                "trade_spec_id": spec,
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "frozen_policy_variant_id": POLICY_ID,
                "ir_ceo_ex99_gate_pass": ir_pass,
                "policy_news_gate_pass": policy_pass,
                "issuer_customer_claim_attached": issuer_customer_claim,
                "independent_customer_confirmation_gate_pass": independent_customer_pass,
                "earnings_call_gate_pass": earnings_call_pass,
                "analyst_revision_pit_gate_pass": analyst_revision_pass,
                "source_depth_score": source_depth_score,
                "full_source_extractor_gate_pass": "1" if full_pass else "0",
                "paper_shadow_trade_allowed": "0",
                "real_capital_trade_allowed": "0",
                "blocker": "none" if full_pass else "|".join(blocker_parts),
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def closeout_rows(scope: list[dict[str, str]], policy_docs: list[dict[str, object]], policy_matches: list[dict[str, object]], policy_l2: list[dict[str, object]], customer_docs: list[dict[str, object]], customer_l2: list[dict[str, object]], full_gate: list[dict[str, object]]) -> list[dict[str, object]]:
    policy_specs = {row["trade_spec_id"] for row in policy_l2}
    customer_specs = {row["trade_spec_id"] for row in customer_l2}
    full_pass = sum(1 for row in full_gate if row["full_source_extractor_gate_pass"] == "1")
    return [
        {
            "task_id": "Task2060",
            "verdict": "free_official_source_layers_complete_diagnostic_only",
            "loop_count": "3",
            "aggressive_scope_rows": len(scope),
            "federal_register_doc_rows": len(policy_docs),
            "policy_l1_match_rows": len(policy_matches),
            "policy_l2_semantic_rows": len(policy_l2),
            "policy_trade_gate_pass_rows": len(policy_specs),
            "issuer_customer_contract_doc_rows": len(customer_docs),
            "customer_l2_semantic_rows": len(customer_l2),
            "issuer_customer_claim_trade_rows": len(customer_specs),
            "independent_customer_confirmation_trade_rows": 0,
            "full_source_extractor_gate_pass_rows": full_pass,
            "paper_shadow_policy_status": "BLOCKED_UNTIL_FULL_SOURCE_EXTRACTOR_GATE",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    text = f"""# Task2031-2060 Free Official Source Layers

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Loop count: {closeout['loop_count']}.
- Aggressive scope rows: {closeout['aggressive_scope_rows']}.
- Federal Register official docs reviewed: {closeout['federal_register_doc_rows']}.
- Policy L1 match rows: {closeout['policy_l1_match_rows']}.
- Policy L2 semantic rows: {closeout['policy_l2_semantic_rows']}.
- Policy trade gate pass rows: {closeout['policy_trade_gate_pass_rows']}.
- Issuer customer/contract doc rows: {closeout['issuer_customer_contract_doc_rows']}.
- Customer L2 semantic rows: {closeout['customer_l2_semantic_rows']}.
- Issuer customer claim trade rows: {closeout['issuer_customer_claim_trade_rows']}.
- Independent customer confirmation trade rows: {closeout['independent_customer_confirmation_trade_rows']}.
- Full source extractor gate pass rows: {closeout['full_source_extractor_gate_pass_rows']}.
- Paper shadow policy status: `{closeout['paper_shadow_policy_status']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task runs three implementation loops after Task2021-2030.

1. Loop 1 attaches free official policy/news context from Federal Register source files already acquired in Task1141.
2. Loop 2 extracts issuer-side customer/contract claims from exact SEC filing lineage.
3. Loop 3 recomputes full-source readiness and keeps paper shadow blocked.

Strict boundaries:

- Federal Register context is matched by beneficiary-chain theme and prior-as-of keyword evidence, not by price or PnL.
- Uncertified beneficiary chains are not promoted into policy evidence.
- Issuer customer/contract claims are not treated as independent customer confirmation.
- Missing source remains neutral, not negative.
- No replay, price lookup, paper order, deployment claim, or real-capital permission is produced.

## No-Background Decision-Maker Report

1. 공짜/공식 source를 더 붙였습니다.
2. 정책/뉴스는 Federal Register 기준으로 붙였습니다.
3. 고객/계약은 SEC 원문에서 issuer claim까지만 붙였습니다.
4. 독립 고객 확인은 아직 0건입니다.
5. 그래서 paper-shadow는 아직 막혀 있습니다.

## Artifact Manifest

- `task2031_free_official_source_contract.csv`
- `task2032_federal_register_policy_docs.csv`
- `task2033_policy_l1_packets.csv`
- `task2034_policy_negative_rejections.csv`
- `task2035_policy_l2_semantics.csv`
- `task2036_policy_l3_edges.csv`
- `task2037_policy_l4_thesis.csv`
- `task2038_policy_l5_gate_delta.csv`
- `task2041_issuer_customer_contract_docs.csv`
- `task2042_customer_l2_semantics.csv`
- `task2043_customer_l3_edges.csv`
- `task2044_customer_negative_rejections.csv`
- `task2045_customer_l4_thesis.csv`
- `task2046_customer_l5_gate_delta.csv`
- `task2051_three_loop_audit.csv`
- `task2052_integrated_full_source_gate.csv`
- `task2060_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    text = registry.read_text(encoding="utf-8")
    if "Task2031," in text:
        return
    titles = {
        2031: "Free Official Source Contract",
        2032: "Federal Register Policy Docs",
        2033: "Policy L1 Packets",
        2034: "Policy Negative Rejections",
        2035: "Policy L2 Semantics",
        2036: "Policy L3 Edges",
        2037: "Policy L4 Thesis",
        2038: "Policy L5 Gate Delta",
        2039: "Policy Loop Audit",
        2040: "Policy Loop Closeout",
        2041: "Issuer Customer Contract Docs",
        2042: "Customer L2 Semantics",
        2043: "Customer L3 Edges",
        2044: "Customer Negative Rejections",
        2045: "Customer L4 Thesis",
        2046: "Customer L5 Gate Delta",
        2047: "Customer Independence Blocker",
        2048: "Customer Loop Audit",
        2049: "Customer Loop Closeout",
        2050: "Customer Source Family Closeout",
        2051: "Three Loop Audit",
        2052: "Integrated Full Source Gate",
        2053: "Paper Shadow Blocker Recompute",
        2054: "Layer Integration Audit",
        2055: "Negative Fixture Audit",
        2056: "Validation Contract",
        2057: "Subagent Feedback Incorporation",
        2058: "Artifact Manifest",
        2059: "Operating State Update",
        2060: "Free Official Source Layers Closeout",
    }
    rows = []
    for task_num in range(2031, 2061):
        rows.append(
            {
                "task_id": f"Task{task_num}",
                "title": titles[task_num],
                "owner_team": "Research Governance / Data & Market Microstructure",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "free-official-source-layers-attached-paper-still-blocked",
                "parent_task": "Task2030" if task_num == 2031 else f"Task{task_num - 1}",
                "key_report": "docs/reports/task_2031_2060_free_official_source_layers/task_2031_2060_free_official_source_layers.md",
                "key_decision": "docs/reports/task_2031_2060_free_official_source_layers/task_2031_2060_decision.csv",
                "key_artifacts": "data/artifacts/task_2031_2060_free_official_source_layers",
                "validation_command": "python scripts/trader_brain_2031_2060_free_official_source_layers_validate.py",
                "notes": "Three-loop free/official source layer implementation for policy/news, issuer customer-contract claims, and integrated full-source gate; paper shadow remains blocked.",
            }
        )
    with registry.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writerows(rows)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "103. Task2031-Task2060"
    row = (
        f"103. Task2031-Task2060 ran three free-official source-layer loops for the frozen aggressive policy: "
        f"{closeout['federal_register_doc_rows']} Federal Register docs, {closeout['policy_l1_match_rows']} policy L1 matches, "
        f"{closeout['policy_trade_gate_pass_rows']} policy gate-pass trades, {closeout['issuer_customer_contract_doc_rows']} issuer customer/contract documents, "
        f"{closeout['issuer_customer_claim_trade_rows']} issuer customer-claim trades, 0 independent customer confirmations, and "
        f"{closeout['full_source_extractor_gate_pass_rows']} full-source gate-pass rows were produced; paper shadow remains blocked while strategy remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    lines = text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if line.startswith(marker):
            lines[idx] = row
            path.write_text("".join(lines), encoding="utf-8")
            return
    insert_at = 0
    for idx, line in enumerate(lines):
        if line.startswith("102. Task2021-Task2030"):
            insert_at = idx + 1
            break
    lines.insert(insert_at, row)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    scope = inputs["scope"]

    contracts = source_contract_rows()
    policy_docs = load_federal_register_docs(inputs["fr_panel"])
    policy_matches, policy_rejections = policy_match_rows(scope, policy_docs)
    policy_l2, policy_l3, policy_l4, policy_l5 = policy_l2_l3_l4_l5(policy_matches, scope)

    customer_docs, customer_rejections = customer_contract_docs(scope, inputs["sec_packets"])
    customer_l2, customer_l3, customer_l4, customer_l5 = customer_l2_l3_l4_l5(customer_docs, scope)

    loop_audits = loop_audit_rows()
    full_gate = integrated_gate_rows(scope, inputs["ir_gate"], policy_l5, customer_l5)
    closeout = closeout_rows(scope, policy_docs, policy_matches, policy_l2, customer_docs, customer_l2, full_gate)

    write_csv(OUT_DIR / "task2031_free_official_source_contract.csv", contracts)
    write_csv(OUT_DIR / "task2032_federal_register_policy_docs.csv", policy_docs)
    write_csv(OUT_DIR / "task2033_policy_l1_packets.csv", policy_matches)
    write_csv(OUT_DIR / "task2034_policy_negative_rejections.csv", policy_rejections)
    write_csv(OUT_DIR / "task2035_policy_l2_semantics.csv", policy_l2)
    write_csv(OUT_DIR / "task2036_policy_l3_edges.csv", policy_l3)
    write_csv(OUT_DIR / "task2037_policy_l4_thesis.csv", policy_l4)
    write_csv(OUT_DIR / "task2038_policy_l5_gate_delta.csv", policy_l5)
    write_csv(OUT_DIR / "task2041_issuer_customer_contract_docs.csv", customer_docs)
    write_csv(OUT_DIR / "task2042_customer_l2_semantics.csv", customer_l2)
    write_csv(OUT_DIR / "task2043_customer_l3_edges.csv", customer_l3)
    write_csv(OUT_DIR / "task2044_customer_negative_rejections.csv", customer_rejections)
    write_csv(OUT_DIR / "task2045_customer_l4_thesis.csv", customer_l4)
    write_csv(OUT_DIR / "task2046_customer_l5_gate_delta.csv", customer_l5)
    write_csv(OUT_DIR / "task2051_three_loop_audit.csv", loop_audits)
    write_csv(OUT_DIR / "task2052_integrated_full_source_gate.csv", full_gate)
    write_csv(OUT_DIR / "task2060_closeout.csv", closeout)
    write_json(OUT_DIR / "task2060_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0])
    update_registry()
    update_operating_state(closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(
        "[TASK2031_2060_OK] "
        f"policy_docs={len(policy_docs)} policy_l2={len(policy_l2)} "
        f"customer_docs={len(customer_docs)} customer_l2={len(customer_l2)} "
        f"full_gate_pass={closeout[0]['full_source_extractor_gate_pass_rows']}"
    )


if __name__ == "__main__":
    main()
