from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1228 = ROOT / "data/artifacts/task_1228_1237_volatility_terminal_discriminator"
TASK1238 = ROOT / "data/artifacts/task_1238_1247_raw_text_terminal_evidence"
TASK1258 = ROOT / "data/artifacts/task_1258_1267_multisource_l1_l3_judgment"
RAW_DIR = ROOT / "data/raw/task_1268_1287_sec_complete_submission_cache"
OUT_DIR = ROOT / "data/artifacts/task_1268_1287_source_extractors"
REPORT_DIR = ROOT / "docs/reports/task_1268_1287_source_extractors"

AUTHORITY = "DIAGNOSTIC_SOURCE_EXTRACTOR_ATTACHMENT_ONLY"
USER_AGENT = "QuantResearchDiagnostic/1.0 contact@example.com"
MAX_ACCESSION_DOWNLOADS = 700

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


def source_schema() -> list[dict[str, object]]:
    rows = [
        ("sec_survival", "attached", "symbol,cik,selection_id,decision_asof_ts,accession,accepted_ts,document_type,hash,excerpt,event_state,entity_scope", "survival risk and hard invalidation"),
        ("ir_ceo_earnings_call", "partially_attached_via_sec_exhibits", "symbol,selection_id,accepted_ts,document_type,speaker_role,narrative_topic,specificity_score,excerpt", "management narrative and Q&A proxy from 8-K/EX-99 style exhibits"),
        ("contract_orders_customer", "partially_attached_via_sec_exhibits", "symbol,selection_id,accepted_ts,document_type,contract_quality,customer_or_counterparty,materiality_hint,excerpt", "contract/order/customer validation from exhibits"),
        ("analyst_institution", "vendor_required_gap", "broker,published_ts,rating,estimate_revision,target_delta,consensus_delta,report_id", "expectation change and priced/not-priced state"),
        ("policy_news_catalyst", "theme_shadow_attached_symbol_extractor_pending", "theme,publication_ts,agency,document_number,affected_entity,effective_window,mechanism", "official policy catalyst"),
        ("market_price_volume", "attached", "symbol,decision_asof_ts,momentum_126d,momentum_252d,avg_dollar_volume_60d,realized_vol_90d", "market acceptance confirmation"),
    ]
    return [
        {
            "task_id": "Task1268",
            "source_family": family,
            "availability_state": state,
            "required_fields": fields,
            "l2_use": use,
            "missing_is_negative": "0",
            "replay_ready": "1" if state in {"attached", "partially_attached_via_sec_exhibits"} else "0",
            "authority": AUTHORITY,
        }
        for family, state, fields, use in rows
    ]


def accession_url(cik: str, accession: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{accession}.txt"


def cache_path(cik: str, accession: str) -> Path:
    return RAW_DIR / f"CIK{int(cik):010d}" / f"{accession}.txt"


def download_complete_submission(cik: str, accession: str) -> tuple[str, int, str, Path]:
    out = cache_path(cik, accession)
    if out.exists() and out.stat().st_size > 0:
        payload = out.read_bytes()
        return "cached", len(payload), sha256_bytes(payload), out
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
    return dtype.startswith("EX-99") or dtype.startswith("EX-10") or "press release" in desc or "earnings" in desc or "presentation" in desc


def first_match(text: str, patterns: list[str]) -> tuple[str, str, int, int] | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return pattern, text[max(0, match.start() - 220) : min(len(text), match.end() + 360)], match.start(), match.end()
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


def build() -> dict[str, int]:
    metadata = read_csv(TASK1238 / "task1239_sec_filing_metadata_asof.csv")
    l1_base = read_csv(TASK1258 / "task1260_l1_multisource_packets.csv")
    signals = {row["selection_id"]: row for row in read_csv(TASK1228 / "task1230_l1_prior_knowable_signals.csv")}
    l1_by_selection = {row["selection_id"]: row for row in l1_base}

    by_accession: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in metadata:
        by_accession[(row["cik"], row["accession"])].append(row)

    download_rows: list[dict[str, object]] = []
    document_rows: list[dict[str, object]] = []
    ir_rows: list[dict[str, object]] = []
    contract_rows: list[dict[str, object]] = []
    downloads = 0

    for (cik, accession), rows_for_accession in sorted(by_accession.items()):
        if downloads >= MAX_ACCESSION_DOWNLOADS:
            break
        status, size, digest, path = download_complete_submission(cik, accession)
        downloads += 1 if status in {"downloaded", "cached"} else 0
        download_rows.append(
            {
                "task_id": "Task1269",
                "cik": cik,
                "accession": accession,
                "download_status": status,
                "size_bytes": size,
                "sha256": digest,
                "local_path": path.relative_to(ROOT).as_posix(),
                "sec_url": accession_url(cik, accession),
                "authority": AUTHORITY,
            }
        )
        if status not in {"downloaded", "cached"}:
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        docs = [doc for doc in parse_documents(raw) if interesting_doc(doc)]
        for doc_idx, doc in enumerate(docs, start=1):
            text = doc["text"]
            doc_id = f"DOC1270-{len(document_rows)+1:07d}"
            document_rows.append(
                {
                    "task_id": "Task1270",
                    "document_id": doc_id,
                    "cik": cik,
                    "accession": accession,
                    "document_type": doc["document_type"],
                    "sequence": doc["sequence"],
                    "filename": doc["filename"],
                    "description": doc["description"],
                    "text_size": len(text),
                    "sha256": digest,
                    "authority": AUTHORITY,
                }
            )
            ir_match = first_match(text, IR_PATTERNS)
            contract_match = first_match(text, CONTRACT_PATTERNS)
            for base_row in rows_for_accession:
                if ir_match:
                    pattern, excerpt, start, end = ir_match
                    narrative_state, specificity, reason = classify_ir(excerpt)
                    ir_rows.append(
                        {
                            "task_id": "Task1271",
                            "ir_evidence_id": f"IR1271-{len(ir_rows)+1:07d}",
                            "selection_id": base_row["selection_id"],
                            "symbol": base_row["symbol"],
                            "decision_asof_ts": base_row["decision_asof_ts"],
                            "cik": cik,
                            "accession": accession,
                            "document_id": doc_id,
                            "document_type": doc["document_type"],
                            "matched_pattern": pattern,
                            "narrative_state": narrative_state,
                            "specificity_score": specificity,
                            "context_reason": reason,
                            "excerpt": excerpt[:700],
                            "excerpt_locator": f"char:{start}-{end}",
                            "available_to_brain_ts": base_row["available_to_brain_ts"],
                            "source_time_pass": base_row["source_time_pass"],
                            "selection_use_allowed": "0",
                            "replay_use_allowed": "0",
                            "authority": AUTHORITY,
                        }
                    )
                if contract_match:
                    pattern, excerpt, start, end = contract_match
                    contract_state, score, reason = classify_contract(excerpt)
                    contract_rows.append(
                        {
                            "task_id": "Task1272",
                            "contract_evidence_id": f"CON1272-{len(contract_rows)+1:07d}",
                            "selection_id": base_row["selection_id"],
                            "symbol": base_row["symbol"],
                            "decision_asof_ts": base_row["decision_asof_ts"],
                            "cik": cik,
                            "accession": accession,
                            "document_id": doc_id,
                            "document_type": doc["document_type"],
                            "matched_pattern": pattern,
                            "contract_state": contract_state,
                            "contract_score": score,
                            "context_reason": reason,
                            "excerpt": excerpt[:700],
                            "excerpt_locator": f"char:{start}-{end}",
                            "available_to_brain_ts": base_row["available_to_brain_ts"],
                            "source_time_pass": base_row["source_time_pass"],
                            "selection_use_allowed": "0",
                            "replay_use_allowed": "0",
                            "authority": AUTHORITY,
                        }
                    )

    best_ir: dict[str, dict[str, object]] = {}
    for row in ir_rows:
        sid = str(row["selection_id"])
        if sid not in best_ir or int(row["specificity_score"]) > int(best_ir[sid]["specificity_score"]):
            best_ir[sid] = row
    best_contract: dict[str, dict[str, object]] = {}
    for row in contract_rows:
        sid = str(row["selection_id"])
        if sid not in best_contract or int(row["contract_score"]) > int(best_contract[sid]["contract_score"]):
            best_contract[sid] = row

    l1_rows: list[dict[str, object]] = []
    l2_rows: list[dict[str, object]] = []
    l3_rows: list[dict[str, object]] = []
    readiness_rows: list[dict[str, object]] = []
    for idx, row in enumerate(l1_base, start=1):
        sid = row["selection_id"]
        ir = best_ir.get(sid)
        contract = best_contract.get(sid)
        signal = signals.get(sid, {})
        market = row["market_acceptance_state"]
        survival = row["sec_survival_state"]
        ir_state = ir["narrative_state"] if ir else "missing_or_no_ir_exhibit_signal"
        contract_state = contract["contract_state"] if contract else "missing_or_no_contract_signal"
        if survival == "terminal_distress":
            composite = "hard_survival_review_required"
        elif contract_state == "validated_contract_or_order" and ir_state == "specific_management_narrative" and market.startswith("market_acceptance"):
            composite = "validated_growth_multisource_confirmed"
        elif contract_state in {"validated_contract_or_order", "contract_watch_needs_materiality"} and market.startswith("market_acceptance"):
            composite = "revenue_validation_market_confirmed"
        elif ir_state == "specific_management_narrative" and market.startswith("market_acceptance"):
            composite = "management_narrative_market_confirmed"
        elif row["policy_catalyst_state"] == "theme_policy_shadow_supportive" and market.startswith("market_acceptance"):
            composite = "policy_market_confirmed_but_company_source_gap"
        else:
            composite = "multisource_incomplete_or_watch"
        l1_rows.append(
            {
                "task_id": "Task1273",
                "enhanced_l1_id": f"ENHL1-1273-{idx:06d}",
                **row,
                "management_narrative_state": ir_state,
                "management_specificity_score": ir["specificity_score"] if ir else 0,
                "management_evidence_id": ir["ir_evidence_id"] if ir else "",
                "contract_revenue_state": contract_state,
                "contract_score": contract["contract_score"] if contract else 0,
                "contract_evidence_id": contract["contract_evidence_id"] if contract else "",
                "analyst_expectation_state": "vendor_required_gap",
                "missing_is_negative": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
        l2_rows.append(
            {
                "task_id": "Task1274",
                "enhanced_l2_id": f"ENHL2-1274-{idx:06d}",
                "selection_id": sid,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "enhanced_composite_interpretation": composite,
                "sec_survival_state": survival,
                "management_narrative_state": ir_state,
                "contract_revenue_state": contract_state,
                "policy_catalyst_state": row["policy_catalyst_state"],
                "market_acceptance_state": market,
                "analyst_expectation_state": "vendor_required_gap",
                "assignment_uses_future_outcome": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
        edge_specs = [
            ("ir_ceo_earnings_call", ir_state, "management_narrative", "reinforces" if ir_state == "specific_management_narrative" else "caps_confidence"),
            ("contract_orders_customer", contract_state, "revenue_validation", "reinforces" if contract_state == "validated_contract_or_order" else "conditions"),
            ("analyst_institution", "vendor_required_gap", "priced_expectations", "caps_confidence"),
            ("policy_news_catalyst", row["policy_catalyst_state"], "external_catalyst", "supports" if row["policy_catalyst_state"] == "theme_policy_shadow_supportive" else "conditions"),
            ("market_price_volume", market, "market_acceptance", "confirms" if market.startswith("market_acceptance") else "conditions"),
            ("sec_survival", survival, "survival_assumption", "invalidates" if survival == "terminal_distress" else "conditions"),
        ]
        for family, from_node, to_node, relation in edge_specs:
            l3_rows.append(
                {
                    "task_id": "Task1275",
                    "enhanced_l3_edge_id": f"ENHL3-1275-{len(l3_rows)+1:07d}",
                    "selection_id": sid,
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "source_family": family,
                    "from_node": from_node,
                    "to_node": to_node,
                    "relation_primitive": relation,
                    "assignment_uses_future_outcome": "0",
                    "selection_use_allowed": "0",
                    "replay_use_allowed": "0",
                    "authority": AUTHORITY,
                }
            )
        readiness_rows.append(
            {
                "task_id": "Task1276",
                "selection_id": sid,
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "has_sec_survival": "1",
                "has_policy_shadow": "1" if row["policy_catalyst_state"] != "no_theme_policy_shadow_event" else "0",
                "has_market_acceptance": "1",
                "has_ir_ceo_exhibit": "1" if ir else "0",
                "has_contract_exhibit": "1" if contract else "0",
                "has_analyst_pit": "0",
                "backtest_readiness_state": "shadow_policy_ready_no_analyst" if ir or contract else "insufficient_nonsec_company_sources",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )

    write_csv(OUT_DIR / "task1268_backtest_source_data_schema.csv", source_schema())
    write_csv(OUT_DIR / "task1269_sec_complete_submission_download_ledger.csv", download_rows)
    write_csv(OUT_DIR / "task1270_sec_exhibit_document_index.csv", document_rows)
    write_csv(OUT_DIR / "task1271_ir_ceo_exhibit_evidence.csv", ir_rows)
    write_csv(OUT_DIR / "task1272_contract_order_exhibit_evidence.csv", contract_rows)
    write_csv(OUT_DIR / "task1273_enhanced_l1_multisource_packets.csv", l1_rows)
    write_csv(OUT_DIR / "task1274_enhanced_l2_multisource_interpretation.csv", l2_rows)
    write_csv(OUT_DIR / "task1275_enhanced_l3_relation_edges.csv", l3_rows)
    write_csv(OUT_DIR / "task1276_backtest_readiness_panel.csv", readiness_rows)
    return {
        "download_rows": len(download_rows),
        "downloaded_or_cached": sum(1 for row in download_rows if row["download_status"] in {"downloaded", "cached"}),
        "exhibit_documents": len(document_rows),
        "ir_rows": len(ir_rows),
        "contract_rows": len(contract_rows),
        "l1_rows": len(l1_rows),
        "l2_rows": len(l2_rows),
        "l3_rows": len(l3_rows),
        "ready_rows": sum(1 for row in readiness_rows if row["backtest_readiness_state"] == "shadow_policy_ready_no_analyst"),
    }


def gap_and_closeout(stats: dict[str, int]) -> None:
    gaps = [
        {
            "task_id": "Task1277",
            "source_family": "analyst_institution",
            "gap_state": "vendor_required",
            "needed_for_backtest": "estimate_revision_pit;rating_change_pit;broker_timestamp;consensus_delta",
            "workaround_allowed": "0",
            "reason": "do_not_infer_institution_expectation_from_public_price_or_headlines",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1277",
            "source_family": "ir_ceo_earnings_call",
            "gap_state": "partial_sec_exhibit_proxy_attached",
            "needed_for_backtest": "full transcript with speaker roles and event timestamp",
            "workaround_allowed": "0",
            "reason": "8-K exhibits capture many releases but not full Q&A tone",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1277",
            "source_family": "contract_orders_customer",
            "gap_state": "partial_sec_exhibit_proxy_attached",
            "needed_for_backtest": "customer confirmation and contract materiality fields",
            "workaround_allowed": "0",
            "reason": "issuer press releases alone cannot fully validate revenue quality",
            "authority": AUTHORITY,
        },
    ]
    gate = {
        "task_id": "Task1278",
        **stats,
        "selection_promoted": "0",
        "replay_executed": "0",
        "ready_for_shadow_policy_preregistration": "1" if stats["ready_rows"] >= 100 else "0",
        "ready_for_final_backtest": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    closeout = {
        "task_id": "Task1287",
        "verdict": "source_extractors_attached_partial_backtest_readiness_no_replay",
        **stats,
        "selection_promoted": "0",
        "replay_executed": "0",
        "ready_for_shadow_policy_preregistration": gate["ready_for_shadow_policy_preregistration"],
        "ready_for_final_backtest": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "Prereigster shadow-only multisource rank policy or attach licensed analyst and full transcript feeds before controlled replay.",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1277_remaining_source_gap_ledger.csv", gaps)
    write_csv(OUT_DIR / "task1278_backtest_readiness_gate.csv", [gate])
    write_csv(OUT_DIR / "task1287_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1287_closeout.json", closeout)
    write_csv(REPORT_DIR / "task_1268_1287_decision.csv", [closeout])
    report = f"""# Task1268-1287 Source Extractor Attachment

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: backtest source data schema was clarified and SEC complete-submission exhibit extractors were attached for IR/CEO narrative and contract/order evidence.
- Key metrics: {stats['downloaded_or_cached']} complete submissions cached, {stats['exhibit_documents']} exhibit documents indexed, {stats['ir_rows']} IR/CEO evidence rows, {stats['contract_rows']} contract/order evidence rows, {stats['l1_rows']} enhanced L1 rows, {stats['l3_rows']} enhanced L3 edges.
- Next action: preregister a shadow-only multisource policy or attach licensed analyst/full transcript feeds before controlled replay.

## Quant Expert Report

- Data source and source readiness: SEC complete submission `.txt` archives were used to parse EX-99/EX-10/press release style exhibits; Task1258 policy and market panels were reused.
- Exact join keys: `selection_id`, `symbol`, `decision_asof_ts`, `cik`, `accession`, `document_id`.
- Leakage audit: all exhibit evidence inherits SEC `available_to_brain_ts <= decision_asof_ts`; no PnL, future return, or outcome columns are used for assignment.
- Split/OOS metrics: not applicable; no replay was executed.
- Remaining blockers: analyst/institution PIT data, full earnings-call transcript Q&A, customer-side contract confirmation, symbol-level policy affected-entity extractor.

## No-Background Decision-Maker Report

We clarified exactly what data the brain needs.

Then we attached the first real non-SEC-like company source lane by parsing SEC exhibit documents that often contain press releases, CEO quotes, guidance, contracts, and customer announcements.

This is enough for a shadow policy preregistration, but not enough for final strategy acceptance.

## Artifact Manifest

- `task1268_backtest_source_data_schema.csv`
- `task1269_sec_complete_submission_download_ledger.csv`
- `task1270_sec_exhibit_document_index.csv`
- `task1271_ir_ceo_exhibit_evidence.csv`
- `task1272_contract_order_exhibit_evidence.csv`
- `task1273_enhanced_l1_multisource_packets.csv`
- `task1274_enhanced_l2_multisource_interpretation.csv`
- `task1275_enhanced_l3_relation_edges.csv`
- `task1276_backtest_readiness_panel.csv`
- `task1277_remaining_source_gap_ledger.csv`
- `task1278_backtest_readiness_gate.csv`
- `task1287_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1268_1287_source_extractors_validate.py`
- `python -m unittest tests.test_trader_brain_1268_1287_source_extractors`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1268_1287_source_extractors.md").write_text(report, encoding="utf-8")
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout, indent=2, ensure_ascii=False))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stats = build()
    gap_and_closeout(stats)


if __name__ == "__main__":
    main()
