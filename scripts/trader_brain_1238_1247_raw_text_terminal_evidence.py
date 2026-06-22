from __future__ import annotations

import csv
import hashlib
import html
import json
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
TASK1171 = ROOT / "data/artifacts/task_1171_1180_public_filer_proxy_backtest"
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1228 = ROOT / "data/artifacts/task_1228_1237_volatility_terminal_discriminator"
RAW_CACHE = ROOT / "data/raw/task_1238_1247_sec_filing_text_cache"
OUT_DIR = ROOT / "data/artifacts/task_1238_1247_raw_text_terminal_evidence"
REPORT_DIR = ROOT / "docs/reports/task_1238_1247_raw_text_terminal_evidence"

AUTHORITY = "DIAGNOSTIC_RAW_TEXT_TERMINAL_EVIDENCE_ONLY"
BASE_VARIANT = "l0_l3_slot5_v1"
USER_AGENT = "QuantResearchDiagnostic/1.0 contact@example.com"

FILING_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A", "8-K", "8-K/A", "S-3", "S-3/A", "S-1", "S-1/A"}
PREFIX_FORMS = ("424B",)
LOOKBACK_DAYS = 540
MAX_FILINGS_PER_SELECTION = 5
MAX_DOWNLOADS = 700

PATTERNS = {
    "going_concern": [
        r"substantial doubt",
        r"going concern",
        r"continue as a going concern",
        r"ability to continue",
    ],
    "liquidity_distress": [
        r"liquidity shortfall",
        r"working capital deficit",
        r"negative cash flow",
        r"recurring losses",
        r"capital resources",
        r"cash runway",
    ],
    "dilution_financing": [
        r"at-the-market",
        r"\bATM\b",
        r"shelf registration",
        r"convertible note",
        r"convertible debt",
        r"warrant",
        r"equity line",
        r"registered direct offering",
        r"prospectus supplement",
        r"dilution",
    ],
    "listing_deficiency": [
        r"Item\s+3\.01",
        r"continued listing",
        r"listing standards?",
        r"minimum bid",
        r"deficiency notice",
        r"delist",
        r"Nasdaq Listing Rule",
        r"NYSE American",
    ],
    "debt_default_restructuring": [
        r"event of default",
        r"covenant breach",
        r"debt default",
        r"forbearance",
        r"restructuring",
        r"bankruptcy",
        r"Chapter 11",
    ],
    "reverse_split_action": [
        r"reverse stock split",
        r"reverse split",
        r"share consolidation",
    ],
}

FAMILY_SEVERITY = {
    "going_concern": 3,
    "listing_deficiency": 3,
    "debt_default_restructuring": 3,
    "dilution_financing": 2,
    "liquidity_distress": 2,
    "reverse_split_action": 2,
}

HARD_TERMINAL_FAMILIES = {"going_concern", "listing_deficiency", "debt_default_restructuring"}


def evidence_confidence(family: str, pattern: str, excerpt: str, form: str, items: str) -> tuple[str, int, int, str, str, str, str]:
    lower = excerpt.lower()
    item_set = {item.strip() for item in items.split(",") if item.strip()}
    confidence = "low"
    terminal_signal = 0
    watch_signal = 0
    reason = "keyword_context_low_confidence"
    polarity = "boilerplate"
    event_state = "routine_disclosure"
    entity_scope = "issuer_unknown"

    if family == "going_concern":
        mitigated = any(token in lower for token in ["alleviated substantial doubt", "sufficient liquidity", "not raise substantial doubt", "does not raise substantial doubt", "no longer substantial doubt", "no substantial doubt"])
        boilerplate = "if it concludes" in lower or "evaluates whether" in lower and "has concluded" not in lower and "contains an explanatory paragraph" not in lower
        adverse = any(token in lower for token in ["raises substantial doubt", "substantial doubt exists", "substantial doubt about", "substantial doubt regarding"])
        if adverse and not mitigated:
            if boilerplate:
                confidence, watch_signal, reason = "low", 0, "going_concern_evaluation_boilerplate"
                polarity, event_state = "hypothetical", "boilerplate"
            else:
                confidence, terminal_signal, reason = "high", 1, "unresolved_substantial_doubt_context"
                polarity, event_state, entity_scope = "adverse", "actual_event", "issuer"
        elif mitigated:
            confidence, watch_signal, reason = "low", 0, "mitigated_substantial_doubt_context"
            polarity, event_state = "mitigated", "risk_resolved"
        elif "going concern" in lower and "ability to continue" in lower:
            confidence, watch_signal, reason = "medium", 1, "going_concern_ability_context"
            polarity, event_state = "adverse", "risk_disclosed"
        elif pattern == "ability to continue":
            confidence, watch_signal, reason = "low", 0, "ability_phrase_without_doubt"
            polarity, event_state = "boilerplate", "routine_disclosure"
    elif family == "listing_deficiency":
        if "3.01" in item_set or "Item 3.01" in excerpt:
            if any(token in lower for token in ["received a notice", "received notice", "notified", "deficiency notice", "minimum bid"]):
                confidence, terminal_signal, reason = "high", 1, "8k_item_301_listing_event"
                polarity, event_state, entity_scope = "adverse", "actual_event", "issuer"
            else:
                confidence, watch_signal, reason = "medium", 1, "8k_item_301_transfer_or_title_only"
                polarity, event_state, entity_scope = "adverse", "risk_disclosed", "issuer"
        elif any(token in lower for token in ["deficiency notice", "minimum bid", "nasdaq listing rule", "delist"]):
            confidence, watch_signal, reason = "medium", 1, "listing_rule_context"
            polarity, event_state = "adverse", "risk_disclosed"
        elif pattern in {"listing standards?", "continued listing"}:
            confidence, watch_signal, reason = "low", 0, "generic_listing_standard_language"
            polarity, event_state = "boilerplate", "routine_disclosure"
    elif family == "debt_default_restructuring":
        hard_tokens = [
            "received a notice of default",
            "notice of default",
            "was in default",
            "is in default",
            "defaulted",
            "failed to make",
            "failed to pay",
            "missed payment",
            "forbearance agreement",
            "waiver of default",
            "acceleration notice",
            "restructuring support agreement",
            "filed for bankruptcy",
            "chapter 11",
        ]
        boilerplate_tokens = [
            "would constitute",
            "could constitute",
            "may constitute",
            "if an event of default",
            "upon an event of default",
            "events of default include",
            "events of bankruptcy",
            "subject to applicable bankruptcy",
            "become insolvent",
            "if bankruptcy",
        ]
        nonissuer = "subsidiar" in lower or "not have a material impact" in lower or "no material impact" in lower
        resolved_historical = any(token in lower for token in ["emerged from chapter 11", "completed its financial restructuring", "completed its restructuring", "excluding the impact of"])
        if any(token in lower for token in hard_tokens):
            if nonissuer:
                confidence, watch_signal, reason = "medium", 1, "subsidiary_or_nonmaterial_bankruptcy_context"
                polarity, event_state, entity_scope = "adverse", "risk_disclosed", "subsidiary_or_nonissuer"
            elif resolved_historical:
                confidence, watch_signal, reason = "medium", 1, "historical_resolved_restructuring_context"
                polarity, event_state, entity_scope = "historical", "risk_resolved", "issuer"
            else:
                confidence, terminal_signal, reason = "high", 1, "actual_default_or_bankruptcy_context"
                polarity, event_state, entity_scope = "adverse", "actual_event", "issuer"
        elif any(token in lower for token in boilerplate_tokens):
            confidence, watch_signal, reason = "low", 0, "boilerplate_default_clause"
            polarity, event_state = "hypothetical", "boilerplate"
        elif "forbearance" in lower or "restructuring" in lower:
            confidence, watch_signal, reason = "medium", 1, "forbearance_or_restructuring_context"
            polarity, event_state = "adverse", "risk_disclosed"
    elif family == "dilution_financing":
        high_forms = form.startswith("S-") or form.startswith("424B")
        if high_forms and any(token in lower for token in ["at-the-market", "prospectus supplement", "registered direct offering", "shelf registration"]):
            confidence, watch_signal, reason = "medium", 1, "active_financing_or_shelf_context"
            polarity, event_state = "adverse", "risk_disclosed"
        elif "warrant" in lower or "convertible" in lower:
            confidence, watch_signal, reason = "low", 0, "financing_instrument_keyword_only"
            polarity, event_state = "boilerplate", "routine_disclosure"
    elif family == "liquidity_distress":
        if any(token in lower for token in ["liquidity shortfall", "working capital deficit", "negative cash flow", "recurring losses"]):
            confidence, watch_signal, reason = "medium", 1, "liquidity_distress_context"
            polarity, event_state = "adverse", "risk_disclosed"
        elif pattern == "capital resources":
            confidence, watch_signal, reason = "low", 0, "mda_section_heading_only"
            polarity, event_state = "boilerplate", "routine_disclosure"
    elif family == "reverse_split_action":
        confidence, watch_signal, reason = "medium", 1, "reverse_split_context"
        polarity, event_state = "adverse", "risk_disclosed"

    severity = FAMILY_SEVERITY[family] if confidence == "high" else max(FAMILY_SEVERITY[family] - 1, 1) if confidence == "medium" else 0
    return confidence, severity, terminal_signal, reason if terminal_signal else reason, polarity, event_state, entity_scope


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


def sec_archive_url(cik: str, accession: str, primary_doc: str) -> str:
    cik_int = str(int(cik))
    return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession.replace('-', '')}/{primary_doc}"


def cache_path(cik: str, accession: str, primary_doc: str) -> Path:
    clean_doc = re.sub(r"[^A-Za-z0-9_.-]+", "_", primary_doc.split("/")[-1])
    return RAW_CACHE / f"CIK{int(cik):010d}" / accession / clean_doc


def download(url: str, out: Path) -> tuple[str, int, str]:
    if out.exists() and out.stat().st_size > 0:
        payload = out.read_bytes()
        return "cached", len(payload), sha256_bytes(payload)
    out.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read()
    except Exception as exc:  # noqa: BLE001 - ledger needs the exact failure text.
        return f"failed:{type(exc).__name__}:{exc}", 0, ""
    out.write_bytes(payload)
    time.sleep(0.12)
    return "downloaded", len(payload), sha256_bytes(payload)


def normalize_text(path: Path) -> str:
    raw = path.read_bytes()[:4_000_000]
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_evidence(text: str, form: str, items: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family, patterns in PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                continue
            start = max(match.start() - 160, 0)
            end = min(match.end() + 220, len(text))
            excerpt = text[start:end]
            confidence, severity, terminal_signal, reason, polarity, event_state, entity_scope = evidence_confidence(family, pattern, excerpt, form, items)
            rows.append(
                {
                    "evidence_family": family,
                    "matched_pattern": pattern,
                    "evidence_confidence": confidence,
                    "context_polarity": polarity,
                    "event_state": event_state,
                    "entity_scope": entity_scope,
                    "terminal_signal": terminal_signal,
                    "watch_signal": 1 if confidence in {"high", "medium"} else 0,
                    "severity_weight": severity,
                    "context_reason": reason,
                    "excerpt": excerpt[:500],
                    "char_start": match.start(),
                    "char_end": match.end(),
                }
            )
            break
    return rows


def load_submission_filings(zip_file: zipfile.ZipFile, cik: str) -> list[dict[str, str]]:
    names = [f"CIK{int(cik):010d}.json"]
    rows: list[dict[str, str]] = []
    seen = set()
    idx = 0
    while idx < len(names):
        name = names[idx]
        idx += 1
        if name in seen or name not in zip_file.namelist():
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


def load_inputs() -> tuple[list[dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    selections = [
        row
        for row in read_csv(TASK1201 / "task1205_slot_selections.csv")
        if row["policy_variant_id"] == BASE_VARIANT
    ]
    pool = {row["symbol"]: row for row in read_csv(TASK1171 / "task1171_price_download_pool.csv")}
    routes = {row["selection_id"]: row for row in read_csv(TASK1228 / "task1231_l2_volatility_terminal_discriminator.csv")}
    return selections, pool, routes


def select_candidate_filings(
    selection: dict[str, str],
    pool_row: dict[str, str],
    filings_by_cik: dict[str, list[dict[str, str]]],
) -> list[dict[str, str]]:
    decision_ts = parse_ts(selection["decision_asof_ts"])
    if decision_ts is None:
        return []
    start = decision_ts - timedelta(days=LOOKBACK_DAYS)
    filings = []
    for filing in filings_by_cik.get(pool_row["cik"], []):
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
    for bucket, limit in [("hard_8k", 2), ("financing", 2), ("periodic", 2), ("general_8k", 1)]:
        for filing in by_bucket.get(bucket, [])[:limit]:
            key = (filing["accessionNumber"], filing["primaryDocument"])
            if key not in {(row["accessionNumber"], row["primaryDocument"]) for row in picked}:
                picked.append(filing)
            if len(picked) >= MAX_FILINGS_PER_SELECTION:
                return picked
    return picked[:MAX_FILINGS_PER_SELECTION]


def expert_packets() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1238",
            "expert_role": "distressed_listing_trader",
            "critical_instruction": "Do not classify high volatility as terminal risk without listing, funding, legal, or survival evidence.",
            "must_have_evidence": "going_concern;listing_deficiency;default;dilution;reverse_split",
            "review_output_required": "missed_terminal_risk,false_terminal_block,high_vol_winner_preserved",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1238",
            "expert_role": "macro_policy_theme_pm",
            "critical_instruction": "Separate policy/theme volatility from issuer survival impairment.",
            "must_have_evidence": "source_asof;issuer_specific_link;theme_relation;contradiction_path",
            "review_output_required": "theme_volatility_not_terminal_by_default",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1238",
            "expert_role": "backend_source_engineer",
            "critical_instruction": "Every evidence row must carry symbol, decision_asof, acceptance timestamp, URL, local hash, and excerpt locator.",
            "must_have_evidence": "raw_file_hash;available_to_brain_ts;source_time_pass;no_future_assignment",
            "review_output_required": "binding_gap;download_gap;extractor_gap",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1238",
            "expert_role": "quant_risk_reviewer",
            "critical_instruction": "Replay metrics cannot prove classifier precision. Audit routes before replay.",
            "must_have_evidence": "route_distribution;independent_family_count;proxy_only_flag",
            "review_output_required": "false_positive_cost;missed_collapse;winner_preservation",
            "authority": AUTHORITY,
        },
    ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_CACHE.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    selections, pool, routes = load_inputs()
    ciks = sorted({pool[row["symbol"]]["cik"] for row in selections if row["symbol"] in pool})

    with zipfile.ZipFile(SEC_ZIP) as zip_file:
        filings_by_cik = {cik: load_submission_filings(zip_file, cik) for cik in ciks}

    metadata_rows: list[dict[str, object]] = []
    binding_rows: list[dict[str, object]] = []
    filing_download_rows: list[dict[str, object]] = []
    evidence_rows: list[dict[str, object]] = []
    download_seen: dict[tuple[str, str, str], dict[str, object]] = {}
    evidence_by_doc: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    downloads_used = 0

    for selection_idx, selection in enumerate(selections, start=1):
        symbol = selection["symbol"]
        pool_row = pool.get(symbol)
        if not pool_row:
            continue
        candidates = select_candidate_filings(selection, pool_row, filings_by_cik)
        if not candidates:
            binding_rows.append(
                {
                    "task_id": "Task1239",
                    "binding_id": f"BIND1239-{selection_idx:06d}-000",
                    "selection_id": selection["selection_id"],
                    "symbol": symbol,
                    "cik": pool_row["cik"],
                    "decision_asof_ts": selection["decision_asof_ts"],
                    "accession": "",
                    "form": "",
                    "available_to_brain_ts": "",
                    "source_time_pass": "0",
                    "raw_source_status": "no_candidate_filing_in_lookback",
                    "authority": AUTHORITY,
                }
            )
            continue

        for filing_idx, filing in enumerate(candidates, start=1):
            accepted = parse_ts(filing["acceptanceDateTime"])
            decision_ts = parse_ts(selection["decision_asof_ts"])
            source_time_pass = "1" if accepted and decision_ts and accepted <= decision_ts else "0"
            accession = filing["accessionNumber"]
            primary_doc = filing["primaryDocument"]
            url = sec_archive_url(pool_row["cik"], accession, primary_doc)
            local = cache_path(pool_row["cik"], accession, primary_doc)
            doc_key = (pool_row["cik"], accession, primary_doc)

            metadata_rows.append(
                {
                    "task_id": "Task1239",
                    "selection_id": selection["selection_id"],
                    "symbol": symbol,
                    "cik": pool_row["cik"],
                    "decision_asof_ts": selection["decision_asof_ts"],
                    "form": filing["form"],
                    "items": filing["items"],
                    "accession": accession,
                    "filing_date": filing["filingDate"],
                    "report_date": filing["reportDate"],
                    "acceptance_datetime": filing["acceptanceDateTime"],
                    "available_to_brain_ts": ts_string(accepted),
                    "primary_document": primary_doc,
                    "sec_url": url,
                    "raw_member_path": filing["raw_member_path"],
                    "source_time_pass": source_time_pass,
                    "authority": AUTHORITY,
                }
            )

            if doc_key not in download_seen:
                if downloads_used >= MAX_DOWNLOADS:
                    status, size, digest = "skipped:max_download_limit", 0, ""
                else:
                    status, size, digest = download(url, local)
                    if status in {"downloaded", "cached"}:
                        downloads_used += 1
                download_seen[doc_key] = {
                    "task_id": "Task1240",
                    "cik": pool_row["cik"],
                    "accession": accession,
                    "form": filing["form"],
                    "primary_document": primary_doc,
                    "sec_url": url,
                    "local_path": str(local.relative_to(ROOT).as_posix()),
                    "download_status": status,
                    "size_bytes": size,
                    "sha256": digest,
                    "authority": AUTHORITY,
                }
                if status in {"downloaded", "cached"}:
                    text = normalize_text(local)
                    evidence_by_doc[doc_key] = find_evidence(text, filing["form"], filing.get("items", ""))
                else:
                    evidence_by_doc[doc_key] = []

            drow = download_seen[doc_key]
            binding_rows.append(
                {
                    "task_id": "Task1239",
                    "binding_id": f"BIND1239-{selection_idx:06d}-{filing_idx:03d}",
                    "selection_id": selection["selection_id"],
                    "symbol": symbol,
                    "cik": pool_row["cik"],
                    "decision_asof_ts": selection["decision_asof_ts"],
                    "accession": accession,
                    "form": filing["form"],
                    "available_to_brain_ts": ts_string(accepted),
                    "source_time_pass": source_time_pass,
                    "raw_source_status": drow["download_status"],
                    "authority": AUTHORITY,
                }
            )

            for ev_idx, evidence in enumerate(evidence_by_doc.get(doc_key, []), start=1):
                evidence_rows.append(
                    {
                        "task_id": "Task1241",
                        "evidence_id": f"EVID1241-{len(evidence_rows)+1:06d}",
                        "selection_id": selection["selection_id"],
                        "symbol": symbol,
                        "cik": pool_row["cik"],
                        "decision_asof_ts": selection["decision_asof_ts"],
                        "form": filing["form"],
                        "items": filing["items"],
                        "accession": accession,
                        "primary_document": primary_doc,
                        "evidence_family": evidence["evidence_family"],
                        "matched_pattern": evidence["matched_pattern"],
                        "evidence_confidence": evidence["evidence_confidence"],
                        "context_polarity": evidence["context_polarity"],
                        "event_state": evidence["event_state"],
                        "entity_scope": evidence["entity_scope"],
                        "terminal_signal": evidence["terminal_signal"],
                        "watch_signal": evidence["watch_signal"],
                        "severity_weight": evidence["severity_weight"],
                        "context_reason": evidence["context_reason"],
                        "excerpt": evidence["excerpt"],
                        "excerpt_locator": f"char:{evidence['char_start']}-{evidence['char_end']}",
                        "available_to_brain_ts": ts_string(accepted),
                        "source_time_pass": source_time_pass,
                        "raw_file_sha256": drow["sha256"],
                        "sec_url": url,
                        "outcome_used_for_assignment": "0",
                        "authority": AUTHORITY,
                    }
                )

    filing_download_rows = list(download_seen.values())

    evidence_by_selection: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in evidence_rows:
        evidence_by_selection[str(row["selection_id"])].append(row)

    l2_rows: list[dict[str, object]] = []
    l3_rows: list[dict[str, object]] = []
    audit_rows: list[dict[str, object]] = []
    for idx, selection in enumerate(selections, start=1):
        sid = selection["selection_id"]
        evs = evidence_by_selection.get(sid, [])
        signal_evs = [
            ev
            for ev in evs
            if ev["source_time_pass"] == "1" and str(ev.get("evidence_confidence")) in {"high", "medium"}
        ]
        terminal_evs = [
            ev
            for ev in signal_evs
            if str(ev.get("terminal_signal")) == "1"
            and str(ev.get("context_polarity")) == "adverse"
            and str(ev.get("event_state")) == "actual_event"
            and str(ev.get("entity_scope")) == "issuer"
            and str(ev["evidence_family"]) in HARD_TERMINAL_FAMILIES
        ]
        families = sorted({str(ev["evidence_family"]) for ev in signal_evs})
        terminal_families = sorted({str(ev["evidence_family"]) for ev in terminal_evs})
        independent_count = len(families)
        terminal_family_count = len(terminal_families)
        severity_sum = sum(int(ev["severity_weight"]) for ev in signal_evs)
        route = routes.get(sid, {}).get("volatility_terminal_route", "missing_previous_route")
        proxy_only = "1" if not evs else "0"
        signal_absent = "1" if not families else "0"
        if terminal_family_count >= 1:
            survival_state = "hard_terminal_evidence"
        elif independent_count >= 2 and severity_sum >= 3 and any(family in families for family in ["liquidity_distress", "listing_deficiency", "going_concern", "debt_default_restructuring"]):
            survival_state = "conjunctive_distress_evidence"
        elif independent_count == 1:
            survival_state = "single_family_watch_evidence"
        elif evs:
            survival_state = "raw_text_keyword_noise_or_boilerplate"
        else:
            survival_state = "no_raw_terminal_text_evidence_attached"

        if survival_state == "hard_terminal_evidence":
            l2_route = "terminal_distress"
            relation = "invalidates"
        elif survival_state == "conjunctive_distress_evidence":
            l2_route = "watch_distress"
            relation = "weakens"
        elif survival_state == "single_family_watch_evidence":
            l2_route = "evidence_watch"
            relation = "conditions"
        elif route == "high_vol_upside":
            l2_route = "high_vol_upside_raw_not_contradicted"
            relation = "preserves"
        else:
            l2_route = "ordinary_or_proxy_only"
            relation = "passes"

        l2_rows.append(
            {
                "task_id": "Task1242",
                "l2_primitive_id": f"L2TERM1242-{idx:06d}",
                "selection_id": sid,
                "symbol": selection["symbol"],
                "decision_asof_ts": selection["decision_asof_ts"],
                "previous_route": route,
                "terminal_interpretation_route": l2_route,
                "survival_state": survival_state,
                "evidence_families": ";".join(families),
                "terminal_evidence_families": ";".join(terminal_families),
                "independent_source_family_count": independent_count,
                "terminal_source_family_count": terminal_family_count,
                "severity_sum": severity_sum,
                "proxy_only_after_raw_text": proxy_only,
                "signal_absent_after_context_filter": signal_absent,
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l3_rows.append(
            {
                "task_id": "Task1243",
                "l3_edge_id": f"L3TERM1243-{idx:06d}",
                "selection_id": sid,
                "symbol": selection["symbol"],
                "decision_asof_ts": selection["decision_asof_ts"],
                "from_node": l2_route,
                "to_node": "candidate_thesis_survival_assumption",
                "relation_primitive": relation,
                "mechanism": "raw_terminal_text_evidence" if not proxy_only == "1" else "no_raw_text_contradiction_found",
                "edge_strength": min(severity_sum, 10),
                "invalidates_candidate": "1" if relation == "invalidates" else "0",
                "requires_l4_review": "1" if relation in {"invalidates", "weakens", "conditions"} else "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        audit_rows.append(
            {
                "task_id": "Task1244",
                "selection_id": sid,
                "symbol": selection["symbol"],
                "decision_asof_ts": selection["decision_asof_ts"],
                "previous_route": route,
                "terminal_interpretation_route": l2_route,
                "raw_evidence_attached": "1" if families else "0",
                "independent_source_family_count": independent_count,
                "terminal_source_family_count": terminal_family_count,
                "passes_independent_distress_conjunction": "1" if independent_count >= 2 else "0",
                "high_vol_winner_preservation_review": "1" if route == "high_vol_upside" and l2_route != "terminal_distress" else "0",
                "missing_raw_source_is_not_negative": "1",
                "selection_promoted": "0",
                "authority": AUTHORITY,
            }
        )

    route_counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in l2_rows:
        route_counts[(str(row["previous_route"]), str(row["terminal_interpretation_route"]))] += 1
    route_rows = [
        {
            "task_id": "Task1245",
            "previous_route": previous,
            "terminal_interpretation_route": current,
            "rows": count,
            "authority": AUTHORITY,
        }
        for (previous, current), count in sorted(route_counts.items())
    ]

    expert_audit_rows = [
        {
            "task_id": "Task1246",
            "expert_role": "distressed_listing_trader",
            "audit_verdict": "upgrade_required_but_direction_correct",
            "critical_finding": "Terminal distress cannot be inferred from volatility. Raw source bindings now exist, but exchange delisting event ledgers remain incomplete.",
            "upgrade_applied": "Added terminal_distress/evidence_watch routes and L3 invalidation edges from raw text families.",
            "remaining_gap": "Official Nasdaq/NYSE historical deficiency event feed is still not complete.",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1246",
            "expert_role": "macro_policy_theme_pm",
            "audit_verdict": "upgrade_required_but_direction_correct",
            "critical_finding": "Theme volatility must stay investable unless issuer survival evidence contradicts it.",
            "upgrade_applied": "High-vol upside rows are preserved when no raw terminal contradiction is found.",
            "remaining_gap": "Non-SEC policy/news/transcript source-time extraction is not part of this task.",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1246",
            "expert_role": "backend_source_engineer",
            "audit_verdict": "upgrade_required_but_direction_correct",
            "critical_finding": "Every evidence row needs hash, URL, accession, decision_asof, and available_to_brain timestamp.",
            "upgrade_applied": "Added raw SEC cache ledger, evidence excerpt locator, SHA256, and source_time_pass validation.",
            "remaining_gap": "SEC HTML parsing is deterministic keyword extraction, not full semantic section parsing.",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1246",
            "expert_role": "quant_risk_reviewer",
            "audit_verdict": "no_replay_yet",
            "critical_finding": "Classifier audit must precede another replay.",
            "upgrade_applied": "Added route transition and independent distress conjunction audit panels.",
            "remaining_gap": "No classifier precision/recall claim until evaluation-only outcome panel is separately reviewed.",
            "authority": AUTHORITY,
        },
    ]

    closeout = {
        "task_id": "Task1247",
        "verdict": "raw_text_terminal_evidence_layer_implemented_not_accepted",
        "selection_rows": len(selections),
        "metadata_rows": len(metadata_rows),
        "binding_rows": len(binding_rows),
        "downloaded_or_cached_filings": sum(1 for row in filing_download_rows if row["download_status"] in {"downloaded", "cached"}),
        "l1_evidence_rows": len(evidence_rows),
        "l2_rows": len(l2_rows),
        "l3_rows": len(l3_rows),
        "raw_evidence_attached_selections": sum(1 for row in audit_rows if row["raw_evidence_attached"] == "1"),
        "terminal_distress_rows": sum(1 for row in l2_rows if row["terminal_interpretation_route"] == "terminal_distress"),
        "replay_executed": "0",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "Use this raw evidence layer to preregister a route audit before any controlled replay.",
        "authority": AUTHORITY,
    }

    write_csv(OUT_DIR / "task1238_expert_packets.csv", expert_packets())
    write_csv(OUT_DIR / "task1239_sec_filing_metadata_asof.csv", metadata_rows)
    write_csv(OUT_DIR / "task1239_selection_filing_bindings.csv", binding_rows)
    write_csv(OUT_DIR / "task1240_raw_filing_download_ledger.csv", filing_download_rows)
    write_csv(OUT_DIR / "task1241_l1_terminal_text_evidence.csv", evidence_rows)
    write_csv(OUT_DIR / "task1242_l2_survival_primitives.csv", l2_rows)
    write_csv(OUT_DIR / "task1243_l3_terminal_invalidation_edges.csv", l3_rows)
    write_csv(OUT_DIR / "task1244_independent_distress_audit.csv", audit_rows)
    write_csv(OUT_DIR / "task1245_route_transition_audit.csv", route_rows)
    write_csv(OUT_DIR / "task1246_expert_critical_audit_upgrade.csv", expert_audit_rows)
    write_csv(OUT_DIR / "task1247_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1247_closeout.json", closeout)

    decision_rows = [
        {
            "task_id": "Task1238-1247",
            "decision": "raw_text_terminal_evidence_layer_implemented",
            "replay_executed": "0",
            "selection_promoted": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    write_csv(REPORT_DIR / "task_1238_1247_decision.csv", decision_rows)

    report = f"""# Task1238-1247 Raw Text Terminal Evidence Layer

## Decision Summary

- Verdict: `raw_text_terminal_evidence_layer_implemented_not_accepted`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: SEC filing metadata, raw filing cache, L1 terminal text evidence, L2 survival primitives, L3 invalidation edges, and expert audit upgrade rows were implemented.
- Key metrics: {len(selections)} selection rows, {len(metadata_rows)} as-of filing metadata rows, {len(evidence_rows)} L1 evidence rows, {sum(1 for row in audit_rows if row["raw_evidence_attached"] == "1")} selections with raw text evidence attached.
- Next action: review route audit and preregister a controlled policy before replay.

## Quant Expert Report

- Data source and source readiness: SEC bulk submissions metadata from `submissions.zip`; selected SEC Archives primary documents cached under `data/raw/task_1238_1247_sec_filing_text_cache`.
- Exact join keys: `symbol`, `cik`, `selection_id`, `decision_asof_ts`, `accession`, `primary_document`.
- Leakage audit: every L1 evidence row requires `available_to_brain_ts <= decision_asof_ts`; outcome, PnL, future return, and exit fields are not used for assignment.
- Split/OOS metrics: not applicable; no replay was executed.
- Failure decomposition: this task fixes raw SEC text binding for terminal-risk families, but official historical exchange deficiency feeds and non-SEC dynamic source extraction remain incomplete.
- Cost/slippage stress: not applicable because PnL did not change.
- Remaining blockers: PIT exchange listing event feed, richer section-level semantic parser, non-SEC source-time evidence.

## No-Background Decision-Maker Report

We moved from proxy-only volatility judgment toward actual filing-text evidence.

The brain can now see whether a selected stock had prior SEC text about going concern, dilution, listing deficiency, default, restructuring, or reverse split.

This does not make the strategy accepted. It makes the next replay less blind.

## Artifact Manifest

- Inputs: Task1201 slot5 selections, Task1171 public-filer pool, Task1228 route outputs, SEC bulk submissions zip.
- Outputs: expert packets, filing metadata, binding ledger, download ledger, L1 evidence, L2 primitives, L3 edges, independent distress audit, route transition audit, expert upgrade audit, closeout.
- Validation commands:
  - `python scripts/trader_brain_1238_1247_raw_text_terminal_evidence_validate.py`
  - `python -m unittest tests.test_trader_brain_1238_1247_raw_text_terminal_evidence`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1238_1247_raw_text_terminal_evidence.md").write_text(report, encoding="utf-8")
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
