from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK2001 = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
TASK2021 = ROOT / "data/artifacts/task_2021_2030_sec_8k_ex99_ir_ceo_extractor"
TASK2031 = ROOT / "data/artifacts/task_2031_2060_free_official_source_layers"
OUT_DIR = ROOT / "data/artifacts/task_2061_2090_official_raw_source_assimilation"
RAW_OUT = ROOT / "data/raw/task_2061_2090_official_raw_source_assimilation"
REPORT_DIR = ROOT / "docs/reports/task_2061_2090_official_raw_source_assimilation"
REPORT = REPORT_DIR / "task_2061_2090_official_raw_source_assimilation.md"
DECISION = REPORT_DIR / "task_2061_2090_decision.csv"
AUTHORITY = "DIAGNOSTIC_OFFICIAL_RAW_SOURCE_ASSIMILATION_ONLY"
POLICY_ID = "winner_accel_top5_to_top2_convex_v1"
USER_AGENT = "codex-research-source-audit/1.0 contact=local"

CONTRACT_AWARD_TYPES = ["A", "B", "C", "D"]
USASPENDING_ENDPOINT = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

COUNTERPARTY_SOURCES = [
    {
        "source_id": "CUSTRAW-2081-000",
        "symbol": "CEG",
        "counterparty": "Microsoft",
        "source_url": "https://www.microsoft.com/en-us/microsoft-cloud/blog/2024/09/20/accelerating-the-addition-of-carbon-free-energy-an-update-on-progress/",
        "publication_ts": "2024-09-20T00:00:00+00:00",
        "source_type": "counterparty_historical_source",
        "known_asof_limitation": "usable_only_for_ceg_rows_after_2024_09_20",
        "allowed_beneficiary_chains": ["power_grid_cooling"],
        "keywords": ["Constellation", "Crane", "carbon-free energy", "Microsoft"],
    },
    {
        "source_id": "CUSTRAW-2081-001",
        "symbol": "CEG",
        "counterparty": "Microsoft",
        "source_url": "https://datacenters.microsoft.com/gl_sustainabilities/crane-clean-energy-center/",
        "publication_ts": "2026-02-10T00:00:00+00:00",
        "source_type": "counterparty_current_historical_reference",
        "known_asof_limitation": "after_2025_ceg_aggressive_decisions",
        "allowed_beneficiary_chains": ["power_grid_cooling"],
        "keywords": ["Crane Clean Energy Center", "Microsoft", "datacenters"],
    },
    {
        "source_id": "CUSTRAW-2081-002",
        "symbol": "CEG",
        "counterparty": "Microsoft",
        "source_url": "https://www.microsoft.com/en-us/corporate-responsibility/sustainability",
        "publication_ts": "2026-06-16T00:00:00+00:00",
        "source_type": "counterparty_current_reference_no_historical_receipt",
        "known_asof_limitation": "current_page_not_assignment_grade_for_2021_2026q1",
        "allowed_beneficiary_chains": ["power_grid_cooling"],
        "keywords": ["Crane Clean Energy Center", "nuclear energy", "PPA"],
    },
    {
        "source_id": "CUSTRAW-2081-003",
        "symbol": "CEG",
        "counterparty": "Constellation",
        "source_url": "https://www.constellationenergy.com/news/2024/Constellation-to-Launch-Crane-Clean-Energy-Center-Restoring-Jobs-and-Carbon-Free-Power-to-The-Grid.html",
        "publication_ts": "2024-09-20T00:00:00+00:00",
        "source_type": "issuer_reference_not_independent_customer",
        "known_asof_limitation": "issuer_side_only",
        "allowed_beneficiary_chains": ["power_grid_cooling"],
        "keywords": ["Microsoft", "20-year", "power purchase agreement"],
    },
    {
        "source_id": "CUSTRAW-2081-004",
        "symbol": "AMD",
        "counterparty": "Microsoft",
        "source_url": "https://blogs.microsoft.com/blog/2023/11/15/microsoft-ignite-2023-ai-transformation-and-the-technology-driving-change/",
        "publication_ts": "2023-11-15T00:00:00+00:00",
        "source_type": "counterparty_historical_source",
        "known_asof_limitation": "usable_for_amd_rows_after_2023_11_15_when_accelerator_compute",
        "allowed_beneficiary_chains": ["accelerator_compute"],
        "keywords": ["AMD", "MI300X", "Azure", "AI"],
    },
    {
        "source_id": "CUSTRAW-2081-005",
        "symbol": "ANET",
        "counterparty": "Meta",
        "source_url": "https://engineering.fb.com/2024/03/12/data-center-engineering/building-metas-genai-infrastructure/",
        "publication_ts": "2024-03-12T00:00:00+00:00",
        "source_type": "counterparty_historical_source",
        "known_asof_limitation": "usable_for_anet_rows_after_2024_03_12_when_datacenter_connectivity",
        "allowed_beneficiary_chains": ["datacenter_connectivity"],
        "keywords": ["Arista", "Meta", "GenAI", "network"],
    },
    {
        "source_id": "CUSTRAW-2081-006",
        "symbol": "AVGO",
        "counterparty": "Meta",
        "source_url": "https://engineering.fb.com/2024/10/15/data-infrastructure/open-future-networking-hardware-ai-ocp-2024-meta/",
        "publication_ts": "2024-10-15T00:00:00+00:00",
        "source_type": "counterparty_historical_source_conditional",
        "known_asof_limitation": "blocked_for_current_avgo_accelerator_compute_rows_due_relation_mismatch",
        "allowed_beneficiary_chains": ["datacenter_connectivity"],
        "keywords": ["Broadcom", "Meta", "switch", "AI"],
    },
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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def parse_ts(value: str) -> datetime | None:
    try:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def safe_name(value: str, suffix: str = "") -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:130].strip("_") or "source"
    return stem + suffix


def http_get(url: str, path: Path, timeout: int = 30) -> tuple[str, int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if path.exists() and path.stat().st_size > 0:
            return "reused", 200, ""
        response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
        path.write_bytes(response.content)
        return ("downloaded", response.status_code, "") if response.ok else ("http_error", response.status_code, response.text[:300])
    except Exception as exc:  # noqa: BLE001 - diagnostic ledger must capture network failures.
        return "failed", 0, str(exc)[:300]


def http_post_json(url: str, body: dict[str, object], path: Path, timeout: int = 40) -> tuple[str, int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if path.exists() and path.stat().st_size > 0:
            return "reused", 200, ""
        response = requests.post(url, json=body, timeout=timeout, headers={"User-Agent": USER_AGENT})
        path.write_text(response.text, encoding="utf-8")
        return ("downloaded", response.status_code, "") if response.ok else ("http_error", response.status_code, response.text[:300])
    except Exception as exc:  # noqa: BLE001
        return "failed", 0, str(exc)[:300]


def extract_company_name(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")[:80_000]
    match = re.search(r"COMPANY CONFORMED NAME:\s*([^\n\r]+)", text)
    if match:
        return match.group(1).strip()
    match = re.search(r"CENTRAL INDEX KEY:.*?(?:COMPANY|CONFORMED).*?NAME:\s*([^\n\r]+)", text, re.I | re.S)
    return match.group(1).strip() if match else ""


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "scope": read_csv(TASK2001 / "task2004_aggressive_source_extraction_panel.csv"),
        "ir_gate": read_csv(TASK2021 / "task2026_ir_ceo_gate_delta.csv"),
        "policy_l1": read_csv(TASK2031 / "task2033_policy_l1_packets.csv"),
        "policy_l5": read_csv(TASK2031 / "task2038_policy_l5_gate_delta.csv"),
        "customer_l5": read_csv(TASK2031 / "task2046_customer_l5_gate_delta.csv"),
        "customer_l2": read_csv(TASK2031 / "task2042_customer_l2_semantics.csv"),
        "source_docs": read_csv(TASK2031 / "task2041_issuer_customer_contract_docs.csv"),
    }


def loop_contract_rows() -> list[dict[str, object]]:
    rows = [
        ("loop1_govinfo_raw", "Download GovInfo PDFs referenced by Federal Register L1 matches and attach raw hashes."),
        ("loop2_usaspending_awards", "Query USAspending contracts by SEC-derived issuer names; keep fuzzy recipient matches blocked."),
        ("loop3_independent_customer_gate", "Download targeted counterparty/issuer pages and recompute full gate without paper-shadow promotion."),
    ]
    return [
        {
            "task_id": "Task2061",
            "loop_contract_id": f"RAWLOOP-2061-{idx:03d}",
            "loop_name": name,
            "objective": objective,
            "no_replay": "1",
            "paper_shadow_must_remain_blocked_unless_full_gate_passes": "1",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, objective) in enumerate(rows, start=1)
    ]


def govinfo_pdf_rows(policy_l1: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    pdf_by_url = {}
    for row in policy_l1:
        url = row.get("official_pdf_url", "")
        if url:
            pdf_by_url.setdefault(url, row)
    download_rows = []
    l1_rows = []
    l2_rows = []
    l3_rows = []
    url_to_download: dict[str, dict[str, object]] = {}
    for idx, (url, seed) in enumerate(sorted(pdf_by_url.items()), start=1):
        parsed = urlparse(url)
        filename = safe_name(Path(parsed.path).name or f"govinfo_{idx}", ".pdf" if not parsed.path.endswith(".pdf") else "")
        out_path = RAW_OUT / "govinfo_policy_pdfs" / filename
        status, http_status, error = http_get(url, out_path, timeout=30)
        sha = file_sha256(out_path) if out_path.exists() and out_path.stat().st_size > 0 else ""
        row = {
            "task_id": "Task2062",
            "govinfo_download_id": f"GOVINFO-2062-{idx:05d}",
            "official_pdf_url": url,
            "download_status": status,
            "http_status": http_status,
            "raw_pdf_path": str(out_path.relative_to(ROOT)).replace("\\", "/") if out_path.exists() else "",
            "raw_pdf_sha256": sha,
            "seed_policy_source_doc_id": seed["policy_source_doc_id"],
            "publication_ts": seed["publication_ts"],
            "provider": "GovInfo",
            "error": error,
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        download_rows.append(row)
        url_to_download[url] = row
        time.sleep(0.05)
    for idx, row in enumerate(policy_l1, start=1):
        dl = url_to_download.get(row["official_pdf_url"], {})
        ok = dl.get("download_status") in {"downloaded", "reused"} and bool(dl.get("raw_pdf_sha256"))
        l1_rows.append(
            {
                "task_id": "Task2063",
                "govinfo_policy_l1_packet_id": f"GOVPOLICYL1-2063-{idx:07d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "policy_source_doc_id": row["policy_source_doc_id"],
                "govinfo_download_id": dl.get("govinfo_download_id", ""),
                "provider": "GovInfo",
                "official_pdf_url": row["official_pdf_url"],
                "raw_pdf_path": dl.get("raw_pdf_path", ""),
                "raw_pdf_sha256": dl.get("raw_pdf_sha256", ""),
                "publication_ts": row["publication_ts"],
                "available_to_brain_ts": row["available_to_brain_ts"],
                "raw_govinfo_source_attached": "1" if ok else "0",
                "asof_guard_pass": "1" if parse_ts(row["available_to_brain_ts"]) and parse_ts(row["available_to_brain_ts"]) <= parse_ts(row["decision_asof_ts"]) else "0",
                "inferred_matching_used": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    best_by_spec = {}
    for row in l1_rows:
        if row["raw_govinfo_source_attached"] != "1" or row["asof_guard_pass"] != "1":
            continue
        spec = str(row["trade_spec_id"])
        best_by_spec.setdefault(spec, row)
    for idx, (spec, row) in enumerate(sorted(best_by_spec.items()), start=1):
        l2_id = f"GOVPOLICYL2-2064-{idx:06d}"
        l3_id = f"GOVPOLICYL3-2065-{idx:06d}"
        l2_rows.append(
            {
                "task_id": "Task2064",
                "govinfo_policy_l2_semantic_id": l2_id,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "govinfo_policy_l1_packet_id": row["govinfo_policy_l1_packet_id"],
                "policy_raw_depth_state": "federal_register_plus_govinfo_pdf_raw",
                "asof_guard_pass": "1",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l3_rows.append(
            {
                "task_id": "Task2065",
                "govinfo_policy_l3_edge_id": l3_id,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "from_govinfo_policy_l2_semantic_id": l2_id,
                "mechanism_edge": "official_pdf_raw_confirms_policy_context_source_depth",
                "relation_type": "source_depth_confirms_policy_layer",
                "asof_guard_pass": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return download_rows, l1_rows, l2_rows, l3_rows


def symbol_company_names(scope: list[dict[str, str]], source_docs: list[dict[str, str]]) -> dict[str, str]:
    by_symbol_paths: dict[str, list[str]] = {}
    for row in source_docs:
        by_symbol_paths.setdefault(row["symbol"], []).append(row["complete_submission_local_path"])
    names = {}
    for symbol in sorted({row["symbol"] for row in scope}):
        for raw_path in by_symbol_paths.get(symbol, []):
            name = extract_company_name(ROOT / raw_path)
            if name:
                names[symbol] = name
                break
    return names


def usaspending_rows(scope: list[dict[str, str]], source_docs: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    names = symbol_company_names(scope, source_docs)
    priority_symbols = sorted({row["symbol"] for row in scope if row["beneficiary_chain"] in {"power_grid_cooling", "software_ai_monetization", "datacenter_connectivity", "accelerator_compute", "semiconductor_broad_cycle", "semiconductor_equipment"}})
    query_rows = []
    award_rows = []
    l2_rows = []
    l3_rows = []
    award_idx = 1
    raw_dir = RAW_OUT / "usaspending_awards"
    for idx, symbol in enumerate(priority_symbols, start=1):
        company_name = names.get(symbol, "")
        if not company_name:
            query_rows.append(
                {
                    "task_id": "Task2071",
                    "usaspending_query_id": f"USASPENDQ-2071-{idx:04d}",
                    "symbol": symbol,
                    "recipient_query_name": "",
                    "query_status": "blocked_no_sec_company_name",
                    "http_status": 0,
                    "raw_response_path": "",
                    "raw_response_sha256": "",
                    "result_count": 0,
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            continue
        body = {
            "filters": {
                "time_period": [{"start_date": "2021-01-01", "end_date": "2026-03-31"}],
                "recipient_search_text": [company_name],
                "award_type_codes": CONTRACT_AWARD_TYPES,
            },
            "fields": ["Award ID", "Recipient Name", "Start Date", "End Date", "Award Amount", "Awarding Agency", "Award Type"],
            "page": 1,
            "limit": 5,
            "sort": "Award Amount",
            "order": "desc",
            "subawards": False,
        }
        raw_path = raw_dir / f"{safe_name(symbol + '_' + company_name)}.json"
        status, http_status, error = http_post_json(USASPENDING_ENDPOINT, body, raw_path)
        sha = file_sha256(raw_path) if raw_path.exists() and raw_path.stat().st_size > 0 else ""
        try:
            payload = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
        except json.JSONDecodeError:
            payload = {}
        results = payload.get("results", []) if isinstance(payload, dict) else []
        query_rows.append(
            {
                "task_id": "Task2071",
                "usaspending_query_id": f"USASPENDQ-2071-{idx:04d}",
                "symbol": symbol,
                "recipient_query_name": company_name,
                "query_status": status,
                "http_status": http_status,
                "raw_response_path": str(raw_path.relative_to(ROOT)).replace("\\", "/") if raw_path.exists() else "",
                "raw_response_sha256": sha,
                "result_count": len(results),
                "error": error,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        query_tokens = [token for token in norm(company_name).split() if len(token) > 2 and token not in {"inc", "corp", "co", "ltd", "the", "corporation"}]
        for result in results:
            recipient = str(result.get("Recipient Name", ""))
            recipient_norm = norm(recipient)
            exactish = bool(query_tokens) and all(token in recipient_norm for token in query_tokens[:2])
            award_id = str(result.get("Award ID", ""))
            start_date = str(result.get("Start Date", ""))
            award_amount = result.get("Award Amount", "")
            awarding_agency = result.get("Awarding Agency", "")
            award_rows.append(
                {
                    "task_id": "Task2072",
                    "usaspending_award_l1_id": f"USASPENDL1-2072-{award_idx:06d}",
                    "symbol": symbol,
                    "recipient_query_name": company_name,
                    "award_id": award_id,
                    "recipient_name": recipient,
                    "recipient_match_state": "strict_query_token_match" if exactish else "blocked_fuzzy_recipient_match",
                    "award_start_date": start_date,
                    "award_end_date": result.get("End Date", ""),
                    "award_amount": award_amount,
                    "awarding_agency": awarding_agency,
                    "award_type": result.get("Award Type", ""),
                    "raw_response_path": str(raw_path.relative_to(ROOT)).replace("\\", "/") if raw_path.exists() else "",
                    "raw_response_sha256": sha,
                    "source_url": "https://www.usaspending.gov/search",
                    "available_to_brain_ts": datetime.now(timezone.utc).isoformat(),
                    "historical_assignment_allowed": "0",
                    "independent_customer_confirmation_candidate": "1" if exactish else "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            award_idx += 1
        time.sleep(0.1)
    strict_awards_by_symbol = defaultdict(list)
    for row in award_rows:
        if row["recipient_match_state"] == "strict_query_token_match":
            strict_awards_by_symbol[str(row["symbol"])].append(row)
    for idx, (symbol, rows) in enumerate(sorted(strict_awards_by_symbol.items()), start=1):
        best = rows[0]
        l2_id = f"USASPENDL2-2073-{idx:05d}"
        l3_id = f"USASPENDL3-2074-{idx:05d}"
        l2_rows.append(
            {
                "task_id": "Task2073",
                "usaspending_l2_semantic_id": l2_id,
                "symbol": symbol,
                "usaspending_award_l1_id": best["usaspending_award_l1_id"],
                "semantic_state": "official_federal_contract_award_context_shadow_only",
                "recipient_name": best["recipient_name"],
                "award_amount": best["award_amount"],
                "awarding_agency": best["awarding_agency"],
                "historical_assignment_allowed": "0",
                "independent_customer_confirmation_gate_pass": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l3_rows.append(
            {
                "task_id": "Task2074",
                "usaspending_l3_edge_id": l3_id,
                "symbol": symbol,
                "from_usaspending_l2_semantic_id": l2_id,
                "mechanism_edge": "official_award_context_is_shadow_until_trade_specific_asof_link",
                "relation_type": "shadow_official_customer_award_context",
                "historical_assignment_allowed": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return query_rows, award_rows, l2_rows, l3_rows


def counterparty_rows(scope: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    download_rows = []
    l1_rows = []
    l2_rows = []
    l3_rows = []
    scope_by_symbol = defaultdict(list)
    for row in scope:
        scope_by_symbol[row["symbol"]].append(row)
    for src in COUNTERPARTY_SOURCES:
        out_path = RAW_OUT / "counterparty_sources" / safe_name(src["source_id"] + "_" + src["counterparty"] + "_" + src["symbol"], ".html")
        status, http_status, error = http_get(src["source_url"], out_path, timeout=30)
        sha = file_sha256(out_path) if out_path.exists() and out_path.stat().st_size > 0 else ""
        text = out_path.read_text(encoding="utf-8", errors="ignore") if out_path.exists() else ""
        keyword_hits = [kw for kw in src["keywords"] if kw.lower() in text.lower()]
        download_rows.append(
            {
                "task_id": "Task2081",
                "counterparty_source_id": src["source_id"],
                "symbol": src["symbol"],
                "counterparty": src["counterparty"],
                "source_url": src["source_url"],
                "source_type": src["source_type"],
                "known_asof_limitation": src["known_asof_limitation"],
                "publication_ts": src["publication_ts"],
                "download_status": status,
                "http_status": http_status,
                "raw_source_path": str(out_path.relative_to(ROOT)).replace("\\", "/") if out_path.exists() else "",
                "raw_source_sha256": sha,
                "keyword_hits": "|".join(keyword_hits),
                "source_text_hash": sha256_text(text[:80_000]) if text else "",
                "error": error,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    l1_idx = 1
    for dl in download_rows:
        pub = parse_ts(str(dl["publication_ts"]))
        for trade in scope_by_symbol.get(str(dl["symbol"]), []):
            decision = parse_ts(trade["decision_asof_ts"])
            asof_pass = bool(pub and decision and pub <= decision)
            independent = dl["counterparty"] != "Constellation" and dl["source_type"].startswith("counterparty")
            source_cfg = next(src for src in COUNTERPARTY_SOURCES if src["source_id"] == dl["counterparty_source_id"])
            chain_pass = trade["beneficiary_chain"] in set(source_cfg.get("allowed_beneficiary_chains", []))
            gate_pass = asof_pass and independent and chain_pass and dl["download_status"] in {"downloaded", "reused"} and bool(dl["keyword_hits"])
            l1_id = f"CUSTINDEPL1-2082-{l1_idx:05d}"
            l1_rows.append(
                {
                    "task_id": "Task2082",
                    "independent_customer_l1_packet_id": l1_id,
                    "trade_spec_id": trade["trade_spec_id"],
                    "candidate_source_id": trade["candidate_source_id"],
                    "symbol": trade["symbol"],
                    "decision_asof_ts": trade["decision_asof_ts"],
                    "counterparty_source_id": dl["counterparty_source_id"],
                    "counterparty": dl["counterparty"],
                    "source_url": dl["source_url"],
                    "publication_ts": dl["publication_ts"],
                    "available_to_brain_ts": dl["publication_ts"],
                    "raw_source_path": dl["raw_source_path"],
                    "raw_source_sha256": dl["raw_source_sha256"],
                    "keyword_hits": dl["keyword_hits"],
                    "asof_guard_pass": "1" if asof_pass else "0",
                    "beneficiary_chain": trade["beneficiary_chain"],
                    "beneficiary_chain_match_pass": "1" if chain_pass else "0",
                    "independent_counterparty_source": "1" if independent else "0",
                    "independent_customer_confirmation_gate_pass": "1" if gate_pass else "0",
                    "blocker": "none" if gate_pass else "publication_after_decision_or_issuer_side_or_keyword_or_chain_gap",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            l1_idx += 1
    passing = [row for row in l1_rows if row["independent_customer_confirmation_gate_pass"] == "1"]
    for idx, row in enumerate(passing, start=1):
        l2_id = f"CUSTINDEPL2-2083-{idx:05d}"
        l3_id = f"CUSTINDEPL3-2084-{idx:05d}"
        l2_rows.append(
            {
                "task_id": "Task2083",
                "independent_customer_l2_semantic_id": l2_id,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "independent_customer_l1_packet_id": row["independent_customer_l1_packet_id"],
                "semantic_state": "independent_counterparty_confirmation_attached",
                "counterparty": row["counterparty"],
                "asof_guard_pass": "1",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l3_rows.append(
            {
                "task_id": "Task2084",
                "independent_customer_l3_edge_id": l3_id,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "from_independent_customer_l2_semantic_id": l2_id,
                "mechanism_edge": "counterparty_source_confirms_customer_demand_context",
                "relation_type": "independent_customer_confirmation",
                "asof_guard_pass": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return download_rows, l1_rows, l2_rows, l3_rows


def integrated_gate_rows(
    scope: list[dict[str, str]],
    ir_gate: list[dict[str, str]],
    policy_l5: list[dict[str, str]],
    customer_l5: list[dict[str, str]],
    govinfo_l1: list[dict[str, object]],
    govinfo_l2: list[dict[str, object]],
    usaspending_queries: list[dict[str, object]],
    usaspending_awards: list[dict[str, object]],
    independent_l1: list[dict[str, object]],
) -> list[dict[str, object]]:
    ir_by_spec = {row["trade_spec_id"]: row for row in ir_gate}
    policy_by_spec = {row["trade_spec_id"]: row for row in policy_l5}
    customer_by_spec = {row["trade_spec_id"]: row for row in customer_l5}
    govinfo_by_spec: dict[str, dict[str, object]] = {}
    for row in govinfo_l1:
        if row["raw_govinfo_source_attached"] == "1" and row["asof_guard_pass"] == "1":
            govinfo_by_spec.setdefault(str(row["trade_spec_id"]), row)
    govinfo_specs = {str(row["trade_spec_id"]) for row in govinfo_l2}
    usaspending_query_by_symbol = {str(row["symbol"]): row for row in usaspending_queries}
    usaspending_award_by_symbol: dict[str, dict[str, object]] = {}
    for row in usaspending_awards:
        if row["recipient_match_state"] == "strict_query_token_match":
            usaspending_award_by_symbol.setdefault(str(row["symbol"]), row)
    independent_pass_specs = {str(row["trade_spec_id"]) for row in independent_l1 if row["independent_customer_confirmation_gate_pass"] == "1"}
    rows = []
    for idx, row in enumerate(scope, start=1):
        spec = row["trade_spec_id"]
        ir_pass = ir_by_spec.get(spec, {}).get("ir_ceo_family_gate_pass", "0")
        policy_pass = policy_by_spec.get(spec, {}).get("policy_news_family_gate_pass", "0")
        govinfo_pass = "1" if spec in govinfo_specs else "0"
        govinfo = govinfo_by_spec.get(spec, {})
        issuer_customer_claim = customer_by_spec.get(spec, {}).get("issuer_customer_claim_attached", "0")
        independent_customer_pass = "1" if spec in independent_pass_specs else "0"
        usaspending_query = usaspending_query_by_symbol.get(row["symbol"], {})
        usaspending_award = usaspending_award_by_symbol.get(row["symbol"], {})
        earnings_call_pass = "0"
        analyst_revision_pass = "0"
        full_pass = all(value == "1" for value in [ir_pass, policy_pass, govinfo_pass, independent_customer_pass, earnings_call_pass, analyst_revision_pass])
        blockers = []
        if ir_pass != "1":
            blockers.append("ir_ceo_ex99_gap")
        if policy_pass != "1":
            blockers.append("policy_news_gap")
        if govinfo_pass != "1":
            blockers.append("govinfo_policy_raw_gap")
        if independent_customer_pass != "1":
            blockers.append("independent_customer_confirmation_gap")
        if earnings_call_pass != "1":
            blockers.append("earnings_call_vendor_or_source_gap")
        if analyst_revision_pass != "1":
            blockers.append("analyst_revision_pit_gap")
        source_depth_score = sum(int(value) for value in [ir_pass, policy_pass, govinfo_pass, issuer_customer_claim, independent_customer_pass])
        rows.append(
            {
                "task_id": "Task2086",
                "integrated_gate_id": f"RAWFULLGATE-2086-{idx:06d}",
                "trade_spec_id": spec,
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "frozen_policy_variant_id": POLICY_ID,
                "ir_ceo_ex99_gate_pass": ir_pass,
                "policy_news_gate_pass": policy_pass,
                "govinfo_policy_raw_gate_pass": govinfo_pass,
                "govinfo_raw_packet_id": govinfo.get("govinfo_policy_l1_packet_id", ""),
                "govinfo_raw_hash": govinfo.get("raw_pdf_sha256", ""),
                "govinfo_published_ts": govinfo.get("publication_ts", ""),
                "govinfo_available_to_brain_ts": govinfo.get("available_to_brain_ts", ""),
                "usaspending_attempt_status": usaspending_query.get("query_status", "not_attempted"),
                "award_id_or_contract_id": usaspending_award.get("award_id", ""),
                "recipient_uei_or_exact_entity_id": "",
                "strict_customer_entity_match_pass": "0",
                "certified_recipient_identity_gate_pass": "0",
                "issuer_customer_claim_attached": issuer_customer_claim,
                "independent_customer_confirmation_gate_pass": independent_customer_pass,
                "earnings_call_gate_pass": earnings_call_pass,
                "analyst_revision_pit_gate_pass": analyst_revision_pass,
                "source_depth_score": source_depth_score,
                "full_source_extractor_gate_pass": "1" if full_pass else "0",
                "paper_shadow_trade_allowed": "0",
                "real_capital_trade_allowed": "0",
                "blocker": "none" if full_pass else "|".join(blockers),
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def audit_rows() -> list[dict[str, object]]:
    rows = [
        ("loop1_govinfo_raw", "GovInfo PDF raw files deepen policy/news source lineage but do not by themselves create trade permission.", "implemented"),
        ("loop2_usaspending_awards", "USAspending is official and keyless, but recipient matches remain shadow-only unless tied to trade-specific as-of customer thesis.", "implemented_shadow_only"),
        ("loop3_independent_customer", "Counterparty pages are separated from issuer pages and blocked when publication is after decision_asof.", "implemented_asof_block"),
    ]
    return [
        {
            "task_id": "Task2087",
            "audit_id": f"RAWAUDIT-2087-{idx:03d}",
            "loop_name": loop,
            "finding": finding,
            "implementation_decision": decision,
            "review_authority": "SUBAGENT_AND_GPT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (loop, finding, decision) in enumerate(rows, start=1)
    ]


def closeout_rows(scope: list[dict[str, str]], govinfo_downloads: list[dict[str, object]], govinfo_l2: list[dict[str, object]], usaspending_queries: list[dict[str, object]], usaspending_awards: list[dict[str, object]], usaspending_l2: list[dict[str, object]], counterparty_downloads: list[dict[str, object]], independent_l2: list[dict[str, object]], full_gate: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2090",
            "verdict": "official_raw_source_assimilation_complete_diagnostic_only",
            "loop_count": "3",
            "aggressive_scope_rows": len(scope),
            "govinfo_pdf_download_rows": len(govinfo_downloads),
            "govinfo_pdf_success_rows": sum(1 for row in govinfo_downloads if row["download_status"] in {"downloaded", "reused"}),
            "govinfo_policy_l2_trade_rows": len(govinfo_l2),
            "usaspending_query_rows": len(usaspending_queries),
            "usaspending_award_rows": len(usaspending_awards),
            "usaspending_shadow_l2_symbol_rows": len(usaspending_l2),
            "counterparty_source_download_rows": len(counterparty_downloads),
            "independent_customer_l2_trade_rows": len(independent_l2),
            "full_source_extractor_gate_pass_rows": sum(1 for row in full_gate if row["full_source_extractor_gate_pass"] == "1"),
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
    text = f"""# Task2061-2090 Official Raw Source Assimilation

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Loop count: {closeout['loop_count']}.
- Aggressive scope rows: {closeout['aggressive_scope_rows']}.
- GovInfo PDF download rows: {closeout['govinfo_pdf_download_rows']}.
- GovInfo PDF success rows: {closeout['govinfo_pdf_success_rows']}.
- GovInfo policy L2 trade rows: {closeout['govinfo_policy_l2_trade_rows']}.
- USAspending query rows: {closeout['usaspending_query_rows']}.
- USAspending award rows: {closeout['usaspending_award_rows']}.
- USAspending shadow L2 symbol rows: {closeout['usaspending_shadow_l2_symbol_rows']}.
- Counterparty source download rows: {closeout['counterparty_source_download_rows']}.
- Independent customer L2 trade rows: {closeout['independent_customer_l2_trade_rows']}.
- Full source extractor gate pass rows: {closeout['full_source_extractor_gate_pass_rows']}.
- Paper shadow policy status: `{closeout['paper_shadow_policy_status']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task repeats the source-quality loop three times:

1. GovInfo raw PDFs are downloaded from the Federal Register policy links.
2. USAspending contract-award API queries are captured as official shadow context.
3. Targeted counterparty/issuer pages are downloaded and as-of checked.

Boundaries:

- GovInfo raw depth strengthens policy/news lineage, but does not open paper shadow by itself.
- USAspending matches are shadow-only until they are tied to a trade-specific customer thesis and as-of receipt.
- Counterparty pages are blocked when publication time is after the trade decision.
- Issuer pages are not independent customer confirmation.
- No replay, price lookup, paper order, deployment claim, or real-capital permission is produced.

## No-Background Decision-Maker Report

1. Federal Register에서 한 단계 더 들어가 GovInfo PDF 원문까지 받았습니다.
2. USAspending 공식 계약 API도 조회했습니다.
3. Microsoft/Constellation 같은 고객·상대방 원문도 따로 받았습니다.
4. 하지만 과거 매수 시점보다 늦게 나온 자료는 막았습니다.
5. 그래서 paper-shadow는 아직 막혀 있습니다.

## Artifact Manifest

- `task2061_three_loop_contract.csv`
- `task2062_govinfo_pdf_download_ledger.csv`
- `task2063_govinfo_policy_l1_packets.csv`
- `task2064_govinfo_policy_l2_semantics.csv`
- `task2065_govinfo_policy_l3_edges.csv`
- `task2071_usaspending_query_ledger.csv`
- `task2072_usaspending_award_l1_packets.csv`
- `task2073_usaspending_l2_semantics.csv`
- `task2074_usaspending_l3_edges.csv`
- `task2081_counterparty_source_downloads.csv`
- `task2082_independent_customer_l1_packets.csv`
- `task2083_independent_customer_l2_semantics.csv`
- `task2084_independent_customer_l3_edges.csv`
- `task2086_integrated_full_source_gate.csv`
- `task2087_three_loop_audit.csv`
- `task2090_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    text = registry.read_text(encoding="utf-8")
    if "Task2061," in text:
        return
    titles = {
        2061: "Official Raw Source Loop Contract",
        2062: "GovInfo PDF Download Ledger",
        2063: "GovInfo Policy L1 Packets",
        2064: "GovInfo Policy L2 Semantics",
        2065: "GovInfo Policy L3 Edges",
        2066: "GovInfo Policy Gate Delta",
        2067: "GovInfo Negative Fixtures",
        2068: "GovInfo Loop Audit",
        2069: "GovInfo Artifact Manifest",
        2070: "GovInfo Loop Closeout",
        2071: "USAspending Query Ledger",
        2072: "USAspending Award L1 Packets",
        2073: "USAspending L2 Semantics",
        2074: "USAspending L3 Edges",
        2075: "USAspending Shadow Gate",
        2076: "DoD Award Raw Blocker",
        2077: "Award Matching Negative Fixtures",
        2078: "USAspending Loop Audit",
        2079: "USAspending Artifact Manifest",
        2080: "USAspending Loop Closeout",
        2081: "Counterparty Source Downloads",
        2082: "Independent Customer L1 Packets",
        2083: "Independent Customer L2 Semantics",
        2084: "Independent Customer L3 Edges",
        2085: "Independent Customer Gate Delta",
        2086: "Integrated Full Source Gate",
        2087: "Three Loop Audit",
        2088: "Validation Contract",
        2089: "Operating State Update",
        2090: "Official Raw Source Assimilation Closeout",
    }
    rows = []
    for task_num in range(2061, 2091):
        rows.append(
            {
                "task_id": f"Task{task_num}",
                "title": titles[task_num],
                "owner_team": "Research Governance / Data & Market Microstructure",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "official-raw-source-depth-added-paper-still-blocked",
                "parent_task": "Task2060" if task_num == 2061 else f"Task{task_num - 1}",
                "key_report": "docs/reports/task_2061_2090_official_raw_source_assimilation/task_2061_2090_official_raw_source_assimilation.md",
                "key_decision": "docs/reports/task_2061_2090_official_raw_source_assimilation/task_2061_2090_decision.csv",
                "key_artifacts": "data/artifacts/task_2061_2090_official_raw_source_assimilation",
                "validation_command": "python scripts/trader_brain_2061_2090_official_raw_source_assimilation_validate.py",
                "notes": "Three-loop official raw source assimilation: GovInfo PDFs, USAspending shadow awards, counterparty as-of audit; paper shadow remains blocked.",
            }
        )
    with registry.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writerows(rows)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "104. Task2061-Task2090"
    row = (
        f"104. Task2061-Task2090 repeated the official raw-source assimilation loop three times for the frozen aggressive policy: "
        f"{closeout['govinfo_pdf_success_rows']} GovInfo PDF raw sources, {closeout['govinfo_policy_l2_trade_rows']} GovInfo-backed policy trades, "
        f"{closeout['usaspending_query_rows']} USAspending queries, {closeout['usaspending_award_rows']} official award rows, "
        f"{closeout['counterparty_source_download_rows']} counterparty/issuer source downloads, {closeout['independent_customer_l2_trade_rows']} independent customer L2 rows, "
        f"and {closeout['full_source_extractor_gate_pass_rows']} full-source gate-pass rows were produced; paper shadow remains blocked while strategy remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    lines = text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if line.startswith(marker):
            lines[idx] = row
            path.write_text("".join(lines), encoding="utf-8")
            return
    insert_at = 0
    for idx, line in enumerate(lines):
        if line.startswith("103. Task2031-Task2060"):
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

    contracts = loop_contract_rows()
    govinfo_downloads, govinfo_l1, govinfo_l2, govinfo_l3 = govinfo_pdf_rows(inputs["policy_l1"])
    usaspending_queries, usaspending_awards, usaspending_l2, usaspending_l3 = usaspending_rows(scope, inputs["source_docs"])
    counterparty_downloads, independent_l1, independent_l2, independent_l3 = counterparty_rows(scope)
    full_gate = integrated_gate_rows(
        scope,
        inputs["ir_gate"],
        inputs["policy_l5"],
        inputs["customer_l5"],
        govinfo_l1,
        govinfo_l2,
        usaspending_queries,
        usaspending_awards,
        independent_l1,
    )
    audits = audit_rows()
    closeout = closeout_rows(scope, govinfo_downloads, govinfo_l2, usaspending_queries, usaspending_awards, usaspending_l2, counterparty_downloads, independent_l2, full_gate)

    write_csv(OUT_DIR / "task2061_three_loop_contract.csv", contracts)
    write_csv(OUT_DIR / "task2062_govinfo_pdf_download_ledger.csv", govinfo_downloads)
    write_csv(OUT_DIR / "task2063_govinfo_policy_l1_packets.csv", govinfo_l1)
    write_csv(OUT_DIR / "task2064_govinfo_policy_l2_semantics.csv", govinfo_l2)
    write_csv(OUT_DIR / "task2065_govinfo_policy_l3_edges.csv", govinfo_l3)
    write_csv(OUT_DIR / "task2071_usaspending_query_ledger.csv", usaspending_queries)
    write_csv(OUT_DIR / "task2072_usaspending_award_l1_packets.csv", usaspending_awards)
    write_csv(OUT_DIR / "task2073_usaspending_l2_semantics.csv", usaspending_l2)
    write_csv(OUT_DIR / "task2074_usaspending_l3_edges.csv", usaspending_l3)
    write_csv(OUT_DIR / "task2081_counterparty_source_downloads.csv", counterparty_downloads)
    write_csv(OUT_DIR / "task2082_independent_customer_l1_packets.csv", independent_l1)
    write_csv(OUT_DIR / "task2083_independent_customer_l2_semantics.csv", independent_l2)
    write_csv(OUT_DIR / "task2084_independent_customer_l3_edges.csv", independent_l3)
    write_csv(OUT_DIR / "task2086_integrated_full_source_gate.csv", full_gate)
    write_csv(OUT_DIR / "task2087_three_loop_audit.csv", audits)
    write_csv(OUT_DIR / "task2090_closeout.csv", closeout)
    write_json(OUT_DIR / "task2090_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0])
    update_registry()
    update_operating_state(closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(
        "[TASK2061_2090_OK] "
        f"govinfo_success={closeout[0]['govinfo_pdf_success_rows']} "
        f"govinfo_l2={closeout[0]['govinfo_policy_l2_trade_rows']} "
        f"usaspending_awards={closeout[0]['usaspending_award_rows']} "
        f"independent_l2={closeout[0]['independent_customer_l2_trade_rows']} "
        f"full_gate_pass={closeout[0]['full_source_extractor_gate_pass_rows']}"
    )


if __name__ == "__main__":
    main()
