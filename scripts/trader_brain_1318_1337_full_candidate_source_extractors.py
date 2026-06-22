from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import time
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
SEC_ZIP = ROOT / "data/raw/task_1161_1170_sec_bulk_submissions/submissions.zip"
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
OLD_RAW_DIR = ROOT / "data/raw/task_1268_1287_sec_complete_submission_cache"
RAW_DIR = ROOT / "data/raw/task_1318_1337_sec_complete_candidate_cache"
OUT_DIR = ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors"
REPORT_DIR = ROOT / "docs/reports/task_1318_1337_full_candidate_source_extractors"

AUTHORITY = "DIAGNOSTIC_FULL_CANDIDATE_SOURCE_EXTRACTORS_ONLY"
USER_AGENT = "QuantResearchDiagnostic/1.0 contact@example.com"
LOOKBACK_DAYS = 540
MAX_FILINGS_PER_CANDIDATE = 5
MAX_ACCESSION_DOWNLOADS = int(os.getenv("TASK1318_MAX_DOWNLOADS", "999999"))

FILING_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A", "8-K", "8-K/A", "S-3", "S-3/A", "S-1", "S-1/A"}
PREFIX_FORMS = ("424B",)

IR_PATTERNS = [
    r"chief executive officer",
    r"\bCEO\b",
    r"chief financial officer",
    r"\bCFO\b",
    r"guidance",
    r"outlook",
    r"backlog",
    r"bookings",
    r"demand",
    r"margin",
    r"revenue growth",
]

CONTRACT_PATTERNS = [
    r"entered into",
    r"contract",
    r"agreement",
    r"award",
    r"purchase order",
    r"customer",
    r"multi-year",
    r"supply agreement",
    r"partnership",
    r"backlog",
    r"order",
]

WEAK_CONTRACT_PATTERNS = [r"memorandum of understanding", r"\bMOU\b", r"letter of intent", r"\bLOI\b", r"non-binding", r"pilot"]

SURVIVAL_PATTERNS = {
    "going_concern": [r"substantial doubt", r"going concern", r"continue as a going concern"],
    "listing_deficiency": [r"Item\s+3\.01", r"continued listing", r"minimum bid", r"deficiency notice", r"delist"],
    "debt_default_restructuring": [r"event of default", r"debt default", r"forbearance", r"restructuring", r"bankruptcy", r"Chapter 11"],
    "dilution_financing": [r"at-the-market", r"\bATM\b", r"shelf registration", r"convertible note", r"warrant", r"registered direct offering", r"dilution"],
    "liquidity_distress": [r"liquidity shortfall", r"working capital deficit", r"negative cash flow", r"recurring losses", r"cash runway"],
    "reverse_split_action": [r"reverse stock split", r"reverse split"],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    cleaned = value.replace(".000Z", "+00:00").replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def ts_string(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(timezone.utc).isoformat()


def is_target_form(form: str) -> bool:
    return form in FILING_FORMS or any(form.startswith(prefix) for prefix in PREFIX_FORMS)


def accession_url(cik: str, accession: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{accession}.txt"


def cache_path(root: Path, cik: str, accession: str) -> Path:
    return root / f"CIK{int(cik):010d}" / f"{accession}.txt"


def download_complete_submission(cik: str, accession: str) -> tuple[str, int, str, Path]:
    out = cache_path(RAW_DIR, cik, accession)
    old = cache_path(OLD_RAW_DIR, cik, accession)
    if out.exists() and out.stat().st_size > 0:
        payload = out.read_bytes()
        return "cached", len(payload), sha256_bytes(payload), out
    if old.exists() and old.stat().st_size > 0:
        payload = old.read_bytes()
        return "reused_task1268_cache", len(payload), sha256_bytes(payload), old
    out.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(accession_url(cik, accession), headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read()
    except Exception as exc:  # noqa: BLE001 - exact failure belongs in ledger.
        return f"failed:{type(exc).__name__}:{exc}", 0, "", out
    out.write_bytes(payload)
    time.sleep(0.12)
    return "downloaded", len(payload), sha256_bytes(payload), out


def strip_html(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_documents(raw: str) -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    for match in re.finditer(r"<DOCUMENT>([\s\S]*?)</DOCUMENT>", raw, flags=re.IGNORECASE):
        block = match.group(1)
        doc_type = re.search(r"<TYPE>\s*([^\n\r<]+)", block, flags=re.IGNORECASE)
        sequence = re.search(r"<SEQUENCE>\s*([^\n\r<]+)", block, flags=re.IGNORECASE)
        filename = re.search(r"<FILENAME>\s*([^\n\r<]+)", block, flags=re.IGNORECASE)
        description = re.search(r"<DESCRIPTION>\s*([^\n\r<]+)", block, flags=re.IGNORECASE)
        text_match = re.search(r"<TEXT>([\s\S]*)</TEXT>", block, flags=re.IGNORECASE)
        text = strip_html(text_match.group(1) if text_match else block)
        docs.append(
            {
                "document_type": doc_type.group(1).strip() if doc_type else "",
                "sequence": sequence.group(1).strip() if sequence else "",
                "filename": filename.group(1).strip() if filename else "",
                "description": description.group(1).strip() if description else "",
                "text": text[:1_500_000],
            }
        )
    return docs


def interesting_doc(doc: dict[str, str]) -> bool:
    dtype = doc["document_type"].upper()
    desc = (doc["description"] + " " + doc["filename"]).lower()
    return (
        dtype.startswith("EX-99")
        or dtype.startswith("EX-10")
        or dtype.startswith("8-K")
        or "press release" in desc
        or "earnings" in desc
        or "presentation" in desc
        or "agreement" in desc
    )


def first_match(text: str, patterns: list[str]) -> tuple[str, str] | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            excerpt = text[max(0, match.start() - 220) : min(len(text), match.end() + 360)]
            return pattern, excerpt
    return None


def classify_ir(text: str) -> tuple[str, int, str]:
    lower = text.lower()
    specificity = 0
    if re.search(r"\$?\d+(\.\d+)?\s*(million|billion|%)", lower):
        specificity += 2
    if any(token in lower for token in ["guidance", "outlook", "expects", "forecast"]):
        specificity += 1
    if any(token in lower for token in ["backlog", "bookings", "demand", "margin", "revenue"]):
        specificity += 1
    if any(token in lower for token in ["pleased", "excited", "proud"]) and specificity == 0:
        return "promotional_low_specificity", 0, "optimism_without_numbers"
    if specificity >= 3:
        return "specific_management_narrative", specificity, "numbers_and_operating_bridge_present"
    if specificity >= 1:
        return "limited_management_narrative", specificity, "some_operating_detail"
    return "generic_management_narrative", specificity, "speaker_or_topic_only"


def classify_contract(text: str) -> tuple[str, int, str]:
    lower = text.lower()
    weak = any(re.search(pattern, lower, flags=re.IGNORECASE) for pattern in WEAK_CONTRACT_PATTERNS)
    score = 0
    if any(token in lower for token in ["signed", "definitive", "entered into", "awarded", "purchase order"]):
        score += 2
    if re.search(r"\$?\d+(\.\d+)?\s*(million|billion)", lower):
        score += 2
    if any(token in lower for token in ["multi-year", "customer", "delivery", "supply", "backlog"]):
        score += 1
    if weak:
        return "weak_nonbinding_or_pilot", max(score - 2, 0), "MOU_LOI_nonbinding_or_pilot_language"
    if score >= 4:
        return "validated_contract_or_order", score, "binding_or_materiality_context_present"
    if score >= 2:
        return "contract_watch_needs_materiality", score, "some_contract_terms_present"
    return "generic_contract_keyword", score, "contract_keyword_without_materiality"


def classify_survival(family: str, excerpt: str, form: str, items: str) -> tuple[str, int, str]:
    lower = excerpt.lower()
    item_set = {item.strip() for item in items.split(",") if item.strip()}
    if family == "going_concern":
        adverse = any(token in lower for token in ["raises substantial doubt", "substantial doubt exists", "substantial doubt about"])
        mitigated = any(token in lower for token in ["alleviated substantial doubt", "no longer substantial doubt", "not raise substantial doubt"])
        if adverse and not mitigated:
            return "terminal_distress", 3, "unresolved_substantial_doubt_context"
        return "watch_distress", 1, "going_concern_context"
    if family == "listing_deficiency":
        if "3.01" in item_set or any(token in lower for token in ["deficiency notice", "minimum bid", "delist"]):
            return "terminal_distress", 3, "listing_deficiency_context"
        return "watch_distress", 1, "generic_listing_context"
    if family == "debt_default_restructuring":
        if any(token in lower for token in ["notice of default", "was in default", "is in default", "failed to pay", "filed for bankruptcy", "chapter 11"]):
            return "terminal_distress", 3, "actual_default_or_bankruptcy_context"
        return "watch_distress", 1, "default_or_restructuring_context"
    if family in {"dilution_financing", "liquidity_distress", "reverse_split_action"}:
        return "watch_distress", 1, f"{family}_context"
    return "no_distress", 0, "no_context"


def load_submission_filings(zip_file: zipfile.ZipFile, cik: str) -> list[dict[str, str]]:
    names = [f"CIK{int(cik):010d}.json"]
    rows: list[dict[str, str]] = []
    seen = set()
    name_set = set(zip_file.namelist())
    idx = 0
    while idx < len(names):
        name = names[idx]
        idx += 1
        if name in seen or name not in name_set:
            continue
        seen.add(name)
        data = json.loads(zip_file.read(name))
        recent = data.get("filings", {}).get("recent", {})
        length = len(recent.get("accessionNumber", []))
        for i in range(length):
            form = str(recent.get("form", [""] * length)[i])
            if not is_target_form(form):
                continue
            rows.append(
                {
                    "cik": f"{int(cik):010d}",
                    "accessionNumber": recent.get("accessionNumber", [""] * length)[i],
                    "filingDate": recent.get("filingDate", [""] * length)[i],
                    "reportDate": recent.get("reportDate", [""] * length)[i],
                    "acceptanceDateTime": recent.get("acceptanceDateTime", [""] * length)[i],
                    "form": form,
                    "items": recent.get("items", [""] * length)[i],
                    "size": recent.get("size", [""] * length)[i],
                    "primaryDocument": recent.get("primaryDocument", [""] * length)[i],
                    "primaryDocDescription": recent.get("primaryDocDescription", [""] * length)[i],
                    "raw_member_path": f"zip://{SEC_ZIP.as_posix()}!{name}",
                }
            )
        for file_ref in data.get("filings", {}).get("files", []) or []:
            ref_name = file_ref.get("name")
            if ref_name and ref_name not in seen:
                names.append(ref_name)
    rows.sort(key=lambda row: row["acceptanceDateTime"])
    return rows


def select_candidate_filings(candidate: dict[str, str], filings_by_cik: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    decision_ts = parse_ts(candidate["decision_asof_ts"])
    if decision_ts is None:
        return []
    start = decision_ts - timedelta(days=LOOKBACK_DAYS)
    filings = []
    for filing in filings_by_cik.get(candidate["cik"], []):
        accepted = parse_ts(filing["acceptanceDateTime"])
        if accepted is None or accepted > decision_ts or accepted < start:
            continue
        filings.append(filing)
    filings.sort(key=lambda row: row["acceptanceDateTime"], reverse=True)
    by_bucket: dict[str, list[dict[str, str]]] = defaultdict(list)
    for filing in filings:
        form = filing["form"]
        items = filing.get("items", "")
        if form.startswith("424B") or form.startswith("S-"):
            bucket = "financing"
        elif form.startswith("10-"):
            bucket = "periodic"
        elif form.startswith("8-K") and any(item in items for item in ["3.01", "2.04", "1.01", "2.05", "8.01"]):
            bucket = "hard_8k"
        elif form.startswith("8-K"):
            bucket = "general_8k"
        else:
            bucket = "other"
        by_bucket[bucket].append(filing)
    picked: list[dict[str, str]] = []
    seen = set()
    for bucket, limit in [("hard_8k", 2), ("financing", 2), ("periodic", 2), ("general_8k", 1)]:
        for filing in by_bucket.get(bucket, [])[:limit]:
            key = (filing["accessionNumber"], filing["primaryDocument"])
            if key not in seen:
                picked.append(filing)
                seen.add(key)
            if len(picked) >= MAX_FILINGS_PER_CANDIDATE:
                return picked
    return picked[:MAX_FILINGS_PER_CANDIDATE]


def source_schema() -> list[dict[str, object]]:
    rows = [
        ("sec_survival", "attached_full_candidate_pool", "candidate_source_id,trade_spec_id,cik,accession,accepted_ts,evidence_id,event_state,excerpt_hash"),
        ("ir_ceo_earnings_call", "attached_via_sec_exhibits_full_candidate_pool", "speaker_role proxy,narrative_state,specificity_score,evidence_id,document_locator"),
        ("contract_orders_customer", "attached_via_sec_exhibits_full_candidate_pool", "contract_state,contract_score,counterparty proxy,evidence_id,document_locator"),
        ("analyst_institution", "vendor_required_gap", "broker,published_ts,rating,estimate_revision,target_delta,consensus_delta"),
        ("policy_news_catalyst", "theme_shadow_gap_for_full_candidates", "theme,publication_ts,agency,affected_entity,mechanism"),
        ("market_price_volume", "price_gate_attached_only", "entry_date,entry_price,price_gate_pass; full volume factors pending"),
    ]
    return [
        {
            "task_id": "Task1318",
            "source_family": family,
            "availability_state": state,
            "required_fields": fields,
            "missing_is_negative": "0",
            "authority": AUTHORITY,
        }
        for family, state, fields in rows
    ]


def evidence_priority(row: dict[str, object]) -> tuple[int, int]:
    state = str(row["source_state"])
    score = int(row.get("source_score", 0) or 0)
    state_rank = {
        "validated_contract_or_order": 5,
        "specific_management_narrative": 5,
        "terminal_distress": 5,
        "contract_watch_needs_materiality": 3,
        "limited_management_narrative": 3,
        "watch_distress": 3,
        "generic_contract_keyword": 1,
        "generic_management_narrative": 1,
        "promotional_low_specificity": 0,
        "weak_nonbinding_or_pilot": 0,
    }.get(state, 0)
    return state_rank, score


def build() -> dict[str, int]:
    candidates = read_csv(TASK1201 / "task1203_l5_trade_specs.csv")
    price_gate = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1204_price_gate.csv")}
    ciks = sorted({row["cik"] for row in candidates})

    with zipfile.ZipFile(SEC_ZIP) as zip_file:
        filings_by_cik = {cik: load_submission_filings(zip_file, cik) for cik in ciks}

    plan_rows = []
    binding_rows = []
    unique_accessions: dict[tuple[str, str], dict[str, str]] = {}
    for idx, candidate in enumerate(candidates, start=1):
        candidate_source_id = f"CANDSRC1319-{idx:07d}"
        plan_rows.append(
            {
                "task_id": "Task1318",
                "candidate_source_id": candidate_source_id,
                "trade_spec_id": candidate["trade_spec_id"],
                "l4_candidate_card_id": candidate["l4_candidate_card_id"],
                "decision_asof_ts": candidate["decision_asof_ts"],
                "symbol": candidate["symbol"],
                "cik": candidate["cik"],
                "candidate_rank": candidate["candidate_rank"],
                "derived_theme": candidate["derived_theme"],
                "source_lookup_scope": "full_3100_candidate_pool",
                "authority": AUTHORITY,
            }
        )
        picked = select_candidate_filings(candidate, filings_by_cik)
        if not picked:
            binding_rows.append(
                {
                    "task_id": "Task1319",
                    "candidate_source_id": candidate_source_id,
                    "trade_spec_id": candidate["trade_spec_id"],
                    "symbol": candidate["symbol"],
                    "cik": candidate["cik"],
                    "decision_asof_ts": candidate["decision_asof_ts"],
                    "accession": "",
                    "form": "",
                    "available_to_brain_ts": "",
                    "source_time_pass": "0",
                    "raw_source_status": "no_candidate_filing_in_lookback",
                    "authority": AUTHORITY,
                }
            )
            continue
        for filing_idx, filing in enumerate(picked, start=1):
            accepted = parse_ts(filing["acceptanceDateTime"])
            decision_ts = parse_ts(candidate["decision_asof_ts"])
            source_time_pass = "1" if accepted and decision_ts and accepted <= decision_ts else "0"
            accession = filing["accessionNumber"]
            binding_rows.append(
                {
                    "task_id": "Task1319",
                    "binding_id": f"BIND1319-{idx:07d}-{filing_idx:03d}",
                    "candidate_source_id": candidate_source_id,
                    "trade_spec_id": candidate["trade_spec_id"],
                    "symbol": candidate["symbol"],
                    "cik": candidate["cik"],
                    "decision_asof_ts": candidate["decision_asof_ts"],
                    "form": filing["form"],
                    "items": filing["items"],
                    "accession": accession,
                    "filing_date": filing["filingDate"],
                    "report_date": filing["reportDate"],
                    "acceptance_datetime": filing["acceptanceDateTime"],
                    "available_to_brain_ts": ts_string(accepted),
                    "primary_document": filing["primaryDocument"],
                    "primary_doc_description": filing["primaryDocDescription"],
                    "source_time_pass": source_time_pass,
                    "raw_member_path": filing["raw_member_path"],
                    "raw_source_status": "metadata_bound_download_pending",
                    "authority": AUTHORITY,
                }
            )
            unique_accessions[(candidate["cik"], accession)] = {
                "cik": candidate["cik"],
                "accession": accession,
                "form": filing["form"],
                "items": filing["items"],
                "acceptance_datetime": filing["acceptanceDateTime"],
            }

    download_rows = []
    document_rows = []
    evidence_rows = []
    accession_evidence: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)

    for idx, ((cik, accession), info) in enumerate(sorted(unique_accessions.items()), start=1):
        if idx == 1 or idx % 250 == 0 or idx == len(unique_accessions):
            print(f"[Task1321] accession_download_parse {idx}/{len(unique_accessions)}", flush=True)
        if idx > MAX_ACCESSION_DOWNLOADS:
            status, size, digest, path = "skipped_download_cap", 0, "", cache_path(RAW_DIR, cik, accession)
        else:
            status, size, digest, path = download_complete_submission(cik, accession)
        download_rows.append(
            {
                "task_id": "Task1320",
                "cik": cik,
                "accession": accession,
                "download_status": status,
                "size_bytes": size,
                "sha256": digest,
                "local_path": path.relative_to(ROOT).as_posix() if path.exists() or path.parent.exists() else "",
                "sec_url": accession_url(cik, accession),
                "authority": AUTHORITY,
            }
        )
        if status not in {"downloaded", "cached", "reused_task1268_cache"}:
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        docs = [doc for doc in parse_documents(raw) if interesting_doc(doc)]
        for doc_idx, doc in enumerate(docs, start=1):
            document_id = f"DOC1321-{len(document_rows)+1:08d}"
            document_rows.append(
                {
                    "task_id": "Task1321",
                    "document_id": document_id,
                    "cik": cik,
                    "accession": accession,
                    "document_type": doc["document_type"],
                    "sequence": doc["sequence"],
                    "filename": doc["filename"],
                    "description": doc["description"],
                    "text_length": len(doc["text"]),
                    "authority": AUTHORITY,
                }
            )
            ir = first_match(doc["text"], IR_PATTERNS)
            if ir:
                state, score, reason = classify_ir(ir[1])
                ev = {
                    "task_id": "Task1322",
                    "evidence_id": f"EVID1322-{len(evidence_rows)+1:08d}",
                    "cik": cik,
                    "accession": accession,
                    "document_id": document_id,
                    "source_family": "ir_ceo_earnings_call",
                    "source_state": state,
                    "source_score": score,
                    "reason": reason,
                    "matched_pattern": ir[0],
                    "excerpt_hash": hashlib.sha256(ir[1].encode("utf-8", errors="ignore")).hexdigest(),
                    "excerpt": ir[1][:700],
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
                evidence_rows.append(ev)
                accession_evidence[(cik, accession)].append(ev)
            contract = first_match(doc["text"], CONTRACT_PATTERNS)
            if contract:
                state, score, reason = classify_contract(contract[1])
                ev = {
                    "task_id": "Task1322",
                    "evidence_id": f"EVID1322-{len(evidence_rows)+1:08d}",
                    "cik": cik,
                    "accession": accession,
                    "document_id": document_id,
                    "source_family": "contract_orders_customer",
                    "source_state": state,
                    "source_score": score,
                    "reason": reason,
                    "matched_pattern": contract[0],
                    "excerpt_hash": hashlib.sha256(contract[1].encode("utf-8", errors="ignore")).hexdigest(),
                    "excerpt": contract[1][:700],
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
                evidence_rows.append(ev)
                accession_evidence[(cik, accession)].append(ev)
            for family, patterns in SURVIVAL_PATTERNS.items():
                survival = first_match(doc["text"], patterns)
                if not survival:
                    continue
                state, score, reason = classify_survival(family, survival[1], info["form"], info["items"])
                ev = {
                    "task_id": "Task1322",
                    "evidence_id": f"EVID1322-{len(evidence_rows)+1:08d}",
                    "cik": cik,
                    "accession": accession,
                    "document_id": document_id,
                    "source_family": "sec_survival",
                    "source_state": state,
                    "source_score": score,
                    "reason": reason,
                    "matched_pattern": survival[0],
                    "excerpt_hash": hashlib.sha256(survival[1].encode("utf-8", errors="ignore")).hexdigest(),
                    "excerpt": survival[1][:700],
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
                evidence_rows.append(ev)
                accession_evidence[(cik, accession)].append(ev)
                break

    evidence_by_candidate: dict[str, list[dict[str, object]]] = defaultdict(list)
    for binding in binding_rows:
        if binding.get("source_time_pass") != "1" or not binding.get("accession"):
            continue
        for ev in accession_evidence.get((str(binding["cik"]), str(binding["accession"])), []):
            evidence_by_candidate[str(binding["candidate_source_id"])].append(ev)

    l1_rows = []
    l2_rows = []
    l3_rows = []
    readiness_rows = []
    bindings_by_candidate: dict[str, list[dict[str, object]]] = defaultdict(list)
    for binding in binding_rows:
        bindings_by_candidate[str(binding.get("candidate_source_id", ""))].append(binding)
    for row in plan_rows:
        cid = str(row["candidate_source_id"])
        evs = evidence_by_candidate.get(cid, [])
        by_family: dict[str, list[dict[str, object]]] = defaultdict(list)
        for ev in evs:
            by_family[str(ev["source_family"])].append(ev)
        best_ir = max(by_family.get("ir_ceo_earnings_call", []), key=evidence_priority, default=None)
        best_contract = max(by_family.get("contract_orders_customer", []), key=evidence_priority, default=None)
        best_survival = max(by_family.get("sec_survival", []), key=evidence_priority, default=None)
        ir_state = str(best_ir["source_state"]) if best_ir else "missing_or_no_ir_exhibit_signal"
        contract_state = str(best_contract["source_state"]) if best_contract else "missing_or_no_contract_signal"
        survival_state = str(best_survival["source_state"]) if best_survival else "no_terminal_distress_evidence_found"
        pg = price_gate.get(str(row["trade_spec_id"]), {})
        market_state = "price_gate_attached" if pg.get("price_gate_pass") == "1" else "price_gate_gap"

        if survival_state == "terminal_distress":
            composite = "hard_survival_review_required"
        elif contract_state == "validated_contract_or_order" and ir_state == "specific_management_narrative":
            composite = "validated_growth_multisource_confirmed"
        elif contract_state in {"validated_contract_or_order", "contract_watch_needs_materiality"} and market_state == "price_gate_attached":
            composite = "revenue_validation_market_confirmed"
        elif ir_state == "specific_management_narrative" and market_state == "price_gate_attached":
            composite = "management_narrative_market_confirmed"
        else:
            composite = "multisource_incomplete_or_watch"

        l1_rows.append(
            {
                "task_id": "Task1323",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "cik": row["cik"],
                "decision_asof_ts": row["decision_asof_ts"],
                "management_narrative_state": ir_state,
                "management_evidence_id": best_ir["evidence_id"] if best_ir else "",
                "contract_revenue_state": contract_state,
                "contract_evidence_id": best_contract["evidence_id"] if best_contract else "",
                "sec_survival_state": survival_state,
                "survival_evidence_id": best_survival["evidence_id"] if best_survival else "",
                "market_acceptance_state": market_state,
                "analyst_expectation_state": "vendor_required_gap",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l2_rows.append(
            {
                "task_id": "Task1324",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "candidate_rank": row["candidate_rank"],
                "derived_theme": row["derived_theme"],
                "full_candidate_composite_interpretation": composite,
                "sec_survival_state": survival_state,
                "management_narrative_state": ir_state,
                "contract_revenue_state": contract_state,
                "market_acceptance_state": market_state,
                "analyst_expectation_state": "vendor_required_gap",
                "assignment_uses_future_outcome": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
        edge_inputs = [
            ("ir_ceo_earnings_call", ir_state, best_ir["evidence_id"] if best_ir else "", "reinforces" if ir_state == "specific_management_narrative" else "source_gap_for"),
            ("contract_orders_customer", contract_state, best_contract["evidence_id"] if best_contract else "", "reinforces" if contract_state == "validated_contract_or_order" else "conditions"),
            ("sec_survival", survival_state, best_survival["evidence_id"] if best_survival else "", "invalidates" if survival_state == "terminal_distress" else "conditions"),
            ("market_price_volume", market_state, "", "confirms" if market_state == "price_gate_attached" else "source_gap_for"),
            ("analyst_institution", "vendor_required_gap", "", "source_gap_for"),
            ("policy_news_catalyst", "theme_shadow_gap_for_full_candidates", "", "source_gap_for"),
        ]
        for family, state, evidence_id, relation in edge_inputs:
            l3_rows.append(
                {
                    "task_id": "Task1325",
                    "candidate_source_id": cid,
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "source_family": family,
                    "source_state": state,
                    "evidence_id": evidence_id,
                    "relation_primitive": relation,
                    "assignment_uses_future_outcome": "0",
                    "selection_use_allowed": "0",
                    "replay_use_allowed": "0",
                    "authority": AUTHORITY,
                }
            )
        readiness_state = "full_candidate_shadow_ready_no_analyst" if best_ir or best_contract or best_survival else "full_candidate_source_gap"
        readiness_rows.append(
            {
                "task_id": "Task1326",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "has_candidate_filings": "1" if any(b.get("accession") for b in bindings_by_candidate.get(cid, [])) else "0",
                "has_sec_survival": "1" if best_survival else "0",
                "has_ir_ceo_exhibit": "1" if best_ir else "0",
                "has_contract_exhibit": "1" if best_contract else "0",
                "has_price_gate": "1" if market_state == "price_gate_attached" else "0",
                "has_analyst_pit": "0",
                "backtest_readiness_state": readiness_state,
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )

    write_csv(OUT_DIR / "task1318_full_candidate_source_schema.csv", source_schema())
    write_csv(OUT_DIR / "task1319_full_candidate_source_plan.csv", plan_rows)
    write_csv(OUT_DIR / "task1320_candidate_filing_bindings.csv", binding_rows)
    write_csv(OUT_DIR / "task1321_sec_complete_submission_download_ledger.csv", download_rows)
    write_csv(OUT_DIR / "task1322_sec_exhibit_document_index.csv", document_rows)
    write_csv(OUT_DIR / "task1323_accession_source_evidence.csv", evidence_rows)
    write_csv(OUT_DIR / "task1324_candidate_l1_source_bindings.csv", l1_rows)
    write_csv(OUT_DIR / "task1325_candidate_l2_interpretation.csv", l2_rows)
    write_csv(OUT_DIR / "task1326_candidate_l3_evidence_edges.csv", l3_rows)
    write_csv(OUT_DIR / "task1327_full_candidate_readiness_panel.csv", readiness_rows)
    stats = {
        "candidate_rows": len(plan_rows),
        "filing_binding_rows": len(binding_rows),
        "unique_accessions": len(unique_accessions),
        "download_rows": len(download_rows),
        "downloaded_or_cached": sum(1 for row in download_rows if row["download_status"] in {"downloaded", "cached", "reused_task1268_cache"}),
        "download_failures": sum(1 for row in download_rows if str(row["download_status"]).startswith("failed")),
        "exhibit_documents": len(document_rows),
        "accession_evidence_rows": len(evidence_rows),
        "l1_rows": len(l1_rows),
        "l2_rows": len(l2_rows),
        "l3_rows": len(l3_rows),
        "ready_rows": sum(1 for row in readiness_rows if row["backtest_readiness_state"] == "full_candidate_shadow_ready_no_analyst"),
    }
    return stats


def closeout(stats: dict[str, int]) -> None:
    gaps = [
        {
            "task_id": "Task1328",
            "gap_area": "analyst_institution",
            "current_state": "vendor_required_gap_for_full_candidate_pool",
            "required_state": "PIT analyst estimate and rating revision feed",
            "missing_is_negative": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1328",
            "gap_area": "policy_news_catalyst",
            "current_state": "theme shadow not rebuilt for all 3100 candidates in this task",
            "required_state": "official policy/news affected-entity source binding per candidate",
            "missing_is_negative": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1328",
            "gap_area": "market_price_volume",
            "current_state": "price gate attached but full volume/momentum factor panel not rebuilt for all candidates",
            "required_state": "as-of market acceptance panel for all candidates",
            "missing_is_negative": "0",
            "authority": AUTHORITY,
        },
    ]
    gate = {
        "task_id": "Task1329",
        **stats,
        "full_candidate_extractor_attached": "1" if stats["l2_rows"] == 3100 else "0",
        "ready_for_candidate_replacement_preregistration": "1" if stats["l2_rows"] == 3100 else "0",
        "ready_for_final_backtest": "0",
        "selection_promoted": "0",
        "replay_executed": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    task_plan = [
        {"task_id": f"Task{task_no}", "task_name": name, "status": "implemented", "authority": AUTHORITY}
        for task_no, name in [
            (1318, "full candidate source schema"),
            (1319, "full candidate source plan"),
            (1320, "candidate filing bindings"),
            (1321, "SEC complete submission download ledger"),
            (1322, "SEC exhibit document index"),
            (1323, "accession source evidence"),
            (1324, "candidate L1 source bindings"),
            (1325, "candidate L2 interpretations"),
            (1326, "candidate L3 evidence edges"),
            (1327, "full candidate readiness panel"),
            (1328, "remaining source gap ledger"),
            (1329, "candidate replacement readiness gate"),
            (1330, "report and manifest"),
            (1331, "validation script"),
            (1332, "unit test"),
            (1333, "operating state update"),
            (1334, "registry update"),
            (1335, "no replay acceptance preservation"),
            (1336, "next replacement replay handoff"),
            (1337, "closeout"),
        ]
    ]
    close = {
        "task_id": "Task1337",
        "verdict": "full_candidate_source_extractors_attached_no_replay",
        **stats,
        "ready_for_candidate_replacement_preregistration": gate["ready_for_candidate_replacement_preregistration"],
        "selection_promoted": "0",
        "replay_executed": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "preregister candidate replacement replay using full-candidate L2/L3 source panel",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1328_remaining_source_gap_ledger.csv", gaps)
    write_csv(OUT_DIR / "task1329_candidate_replacement_readiness_gate.csv", [gate])
    write_csv(OUT_DIR / "task1330_task_plan.csv", task_plan)
    write_csv(OUT_DIR / "task1337_closeout.csv", [close])
    write_json(OUT_DIR / "task1337_closeout.json", close)
    write_csv(REPORT_DIR / "task_1318_1337_decision.csv", [close])
    report = f"""# Task1318-1337 Full Candidate Source Extractors

## Decision Summary

- Verdict: `full_candidate_source_extractors_attached_no_replay`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Candidate rows: {stats['candidate_rows']}.
- Filing bindings: {stats['filing_binding_rows']}.
- Unique accessions: {stats['unique_accessions']}.
- Downloaded/cached complete submissions: {stats['downloaded_or_cached']}.
- L2 candidate rows: {stats['l2_rows']}.
- L3 evidence edges: {stats['l3_rows']}.
- What changed: the extractor expanded from selected slot5 rows to the full 3,100 candidate pool.
- Next action: preregister candidate replacement replay using this full-candidate source panel.

## Quant Expert Report

- Data source and source readiness: SEC bulk submissions metadata and SEC Archives complete submission text files were used for full-candidate source binding.
- Exact join keys: `candidate_source_id`, `trade_spec_id`, `symbol`, `cik`, `decision_asof_ts`, `accession`, `evidence_id`.
- Leakage audit: every filing binding requires `available_to_brain_ts <= decision_asof_ts`; L1-L3 assignment does not use future return, PnL, realized exit, or outcome labels.
- Split/OOS metrics: not applicable; no replay was executed.
- Failure decomposition: analyst PIT, symbol-level policy/news affected-entity extraction, and full as-of market acceptance factors remain explicit gaps.
- Cost/slippage stress: not applicable because no PnL changed.

## No-Background Decision-Maker Report

The previous weakness was real: only the already-selected 310 rows had source extraction.

This task attaches source extraction to all 3,100 candidates.

Now the next replay can actually drop weak selected names and replace them with stronger candidates from the same decision month.

This still does not approve the strategy.

## Artifact Manifest

- `task1318_full_candidate_source_schema.csv`
- `task1319_full_candidate_source_plan.csv`
- `task1320_candidate_filing_bindings.csv`
- `task1321_sec_complete_submission_download_ledger.csv`
- `task1322_sec_exhibit_document_index.csv`
- `task1323_accession_source_evidence.csv`
- `task1324_candidate_l1_source_bindings.csv`
- `task1325_candidate_l2_interpretation.csv`
- `task1326_candidate_l3_evidence_edges.csv`
- `task1327_full_candidate_readiness_panel.csv`
- `task1328_remaining_source_gap_ledger.csv`
- `task1329_candidate_replacement_readiness_gate.csv`
- `task1330_task_plan.csv`
- `task1337_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1318_1337_full_candidate_source_extractors_validate.py`
- `python -m unittest tests.test_trader_brain_1318_1337_full_candidate_source_extractors`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1318_1337_full_candidate_source_extractors.md").write_text(report, encoding="utf-8")
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(close, indent=2, ensure_ascii=False))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stats = build()
    closeout(stats)


if __name__ == "__main__":
    main()
