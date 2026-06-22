from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK2001 = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
TASK2061 = ROOT / "data/artifacts/task_2061_2090_official_raw_source_assimilation"
RAW2061 = ROOT / "data/raw/task_2061_2090_official_raw_source_assimilation"
OUT_DIR = ROOT / "data/artifacts/task_2091_2120_transcript_analyst_uei_gates"
RAW_OUT = ROOT / "data/raw/task_2091_2120_transcript_analyst_uei_gates"
REPORT_DIR = ROOT / "docs/reports/task_2091_2120_transcript_analyst_uei_gates"
REPORT = REPORT_DIR / "task_2091_2120_transcript_analyst_uei_gates.md"
DECISION = REPORT_DIR / "task_2091_2120_decision.csv"
AUTHORITY = "DIAGNOSTIC_TRANSCRIPT_ANALYST_UEI_GATES_ONLY"
USER_AGENT = "codex-research-source-audit/1.0 contact=local"


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


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:140].strip("_") or "source"


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def http_get_json(url: str, path: Path, timeout: int = 30) -> tuple[str, int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if path.exists() and path.stat().st_size > 0:
            return "reused", 200, ""
        response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
        path.write_text(response.text, encoding="utf-8")
        return ("downloaded", response.status_code, "") if response.ok else ("http_error", response.status_code, response.text[:300])
    except Exception as exc:  # noqa: BLE001 - diagnostic raw ledger captures network failures.
        return "failed", 0, str(exc)[:300]


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "scope": read_csv(TASK2001 / "task2004_aggressive_source_extraction_panel.csv"),
        "source_family": read_csv(TASK2001 / "task2003_source_family_contract.csv"),
        "prior_gate": read_csv(TASK2061 / "task2086_integrated_full_source_gate.csv"),
        "usaspending_awards": read_csv(TASK2061 / "task2072_usaspending_award_l1_packets.csv"),
        "usaspending_l2": read_csv(TASK2061 / "task2073_usaspending_l2_semantics.csv"),
    }


def source_contract_rows() -> list[dict[str, object]]:
    rows = [
        {
            "task_id": "Task2091",
            "source_gate_contract_id": "SRCGATE-2091-001",
            "source_family": "earnings_call_transcript",
            "gate_target": "earnings_call_gate_pass",
            "pass_requirement": "provider_event_id|provider_document_id|raw_transcript_path|sha256|provider_available_ts<=decision_asof_ts|exact_symbol_or_cik_binding|no_inferred_matching",
            "allowed_source_examples": "Quartr transcript dataset|FactSet transcript feed|licensed transcript feed with event/document ids",
            "blocked_substitutes": "SEC_EX_99_1_earnings_release|earnings_slide_deck|current_web_scrape_without_historical_available_time",
            "missing_source_is_negative": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2091",
            "source_gate_contract_id": "SRCGATE-2091-002",
            "source_family": "analyst_revision_pit",
            "gate_target": "analyst_revision_pit_gate_pass",
            "pass_requirement": "symbol|fiscal_period|estimate_or_rating_revision_ts|provider_available_ts<=decision_asof_ts|revision_direction|analyst_count_or_broker_id|raw_source_path|sha256",
            "allowed_source_examples": "Nasdaq Data Link Zacks Analyst Revisions|ZacksData historical PIT feed|licensed consensus revision feed",
            "blocked_substitutes": "current_rating_snapshot|future_consensus_history_without_receipt_time|issuer_guidance_proxy",
            "missing_source_is_negative": "0",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2091",
            "source_gate_contract_id": "SRCGATE-2091-003",
            "source_family": "usaspending_uei_recipient_certification",
            "gate_target": "certified_recipient_identity_gate_pass",
            "pass_requirement": "award_detail_raw|award_id|generated_unique_award_id|recipient_uei_or_hash|recipient_name|raw_sha256|identity_match_method_not_company_name_only|award_available_to_brain_ts<=decision_asof_ts",
            "allowed_source_examples": "USAspending /api/v2/awards/<AWARD_ID>/ official detail endpoint",
            "blocked_substitutes": "spending_by_award company-name search only|fuzzy subsidiary match without SEC/legal mapping",
            "missing_source_is_negative": "0",
            "authority": AUTHORITY,
        },
    ]
    return rows


def transcript_option_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2092",
            "transcript_source_option_id": "TRSRCOPT-2092-001",
            "provider": "Quartr",
            "source_url": "https://quartr.com/docs/datasets/earnings-call-transcripts",
            "official_doc_summary": "transcript dataset has event-linked transcripts with raw and edited transcript types, speaker mapping, paragraphs, sentence and word timing",
            "pit_viability": "viable_if_api_access_and_provider_available_ts_captured",
            "local_raw_available": "0",
            "gate_candidate": "1",
            "blocker": "no_local_quartr_transcript_raw_or_api_credentials_in_repo",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2092",
            "transcript_source_option_id": "TRSRCOPT-2092-002",
            "provider": "Finnhub/FMP/other free tiers",
            "source_url": "vendor_or_api_dependent",
            "official_doc_summary": "may expose earnings call transcript endpoints but requires API key and PIT publication/availability fields before assignment",
            "pit_viability": "blocked_until_historical_available_ts_and_raw_transcript_are_certified",
            "local_raw_available": "0",
            "gate_candidate": "0",
            "blocker": "no_certified_local_historical_transcript_raw",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2092",
            "transcript_source_option_id": "TRSRCOPT-2092-003",
            "provider": "SEC EX-99.1 earnings release",
            "source_url": "local_sec_8k_ex99_artifacts",
            "official_doc_summary": "issuer release or slide deck can support IR/CEO narrative but is not a call transcript or Q&A transcript",
            "pit_viability": "support_only_not_transcript_gate",
            "local_raw_available": "1",
            "gate_candidate": "0",
            "blocker": "blocked_substitute_for_earnings_call_transcript_gate",
            "authority": AUTHORITY,
        },
    ]


def transcript_gate_rows(scope: list[dict[str, str]], prior_gate: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    prior_by_spec = {row["trade_spec_id"]: row for row in prior_gate}
    l1_rows: list[dict[str, object]] = []
    l2_rows: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []
    for idx, row in enumerate(scope, start=1):
        spec = row["trade_spec_id"]
        prior = prior_by_spec.get(spec, {})
        has_ir_reference = str(prior.get("ir_ceo_ex99_gate_pass", "0")) == "1"
        l1_id = f"TRANSCRIPTL1-2093-{idx:06d}"
        l1_rows.append(
            {
                "task_id": "Task2093",
                "transcript_l1_packet_id": l1_id,
                "trade_spec_id": spec,
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "provider": "",
                "provider_event_id": "",
                "provider_document_id": "",
                "call_event_ts": "",
                "transcript_publication_ts": "",
                "provider_available_ts": "",
                "raw_transcript_path": "",
                "raw_transcript_sha256": "",
                "exact_symbol_or_cik_binding": "0",
                "no_inferred_matching_used": "1",
                "sec_ex99_reference_present": "1" if has_ir_reference else "0",
                "transcript_source_state": "blocked_missing_certified_transcript_raw",
                "earnings_call_gate_pass": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        l2_rows.append(
            {
                "task_id": "Task2094",
                "transcript_l2_semantic_id": f"TRANSCRIPTL2-2094-{idx:06d}",
                "transcript_l1_packet_id": l1_id,
                "trade_spec_id": spec,
                "symbol": row["symbol"],
                "semantic_state": "no_certified_call_or_qa_transcript",
                "prepared_remarks_available": "0",
                "qa_section_available": "0",
                "speaker_mapping_available": "0",
                "management_tone_primitive_allowed": "0",
                "analyst_question_primitive_allowed": "0",
                "sec_ex99_reference_is_substitute": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        gate_rows.append(
            {
                "task_id": "Task2095",
                "transcript_gate_id": f"TRANSCRIPTGATE-2095-{idx:06d}",
                "trade_spec_id": spec,
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "transcript_l1_packet_id": l1_id,
                "earnings_call_gate_pass": "0",
                "gate_verdict": "BLOCKED_TRANSCRIPT_SOURCE_GAP",
                "blocker": "certified_earnings_call_transcript_raw_missing",
                "sec_ex99_reference_present": "1" if has_ir_reference else "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return l1_rows, l2_rows, gate_rows


def analyst_source_contract_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2096",
            "analyst_source_contract_id": "ANALYSTSRC-2096-001",
            "provider": "Nasdaq Data Link Zacks Analyst Revisions",
            "source_url": "https://data.nasdaq.com/databases/ZREV",
            "required_fields": "symbol|fiscal_period|estimate_timestamp|provider_available_ts|revision_direction|analyst_count_or_broker_id|raw_path|sha256",
            "local_status": "schema_previously_cataloged_vendor_blocked",
            "gate_candidate": "1",
            "blocker": "licensed_or_vendor_access_required_for_historical_pit_rows",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2096",
            "analyst_source_contract_id": "ANALYSTSRC-2096-002",
            "provider": "issuer_guidance_proxy",
            "source_url": "local_sec_guidance_artifacts",
            "required_fields": "not_valid_for_analyst_revision_gate",
            "local_status": "support_only",
            "gate_candidate": "0",
            "blocker": "issuer_claim_is_not_analyst_expectation_revision",
            "authority": AUTHORITY,
        },
    ]


def analyst_gate_rows(scope: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    l1_rows: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []
    for idx, row in enumerate(scope, start=1):
        l1_id = f"ANALYSTL1-2097-{idx:06d}"
        l1_rows.append(
            {
                "task_id": "Task2097",
                "analyst_revision_l1_packet_id": l1_id,
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "provider": "",
                "fiscal_period": "",
                "revision_timestamp": "",
                "provider_available_ts": "",
                "revision_direction": "",
                "analyst_count_or_broker_id": "",
                "raw_revision_path": "",
                "raw_revision_sha256": "",
                "pit_revision_source_state": "blocked_missing_certified_pit_revision_feed",
                "analyst_revision_pit_gate_pass": "0",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        gate_rows.append(
            {
                "task_id": "Task2098",
                "analyst_revision_gate_id": f"ANALYSTGATE-2098-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "analyst_revision_l1_packet_id": l1_id,
                "analyst_revision_pit_gate_pass": "0",
                "gate_verdict": "BLOCKED_ANALYST_PIT_SOURCE_GAP",
                "blocker": "certified_historical_pit_analyst_revision_raw_missing",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return l1_rows, gate_rows


def load_detail_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def fetch_award_details(award_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    detail_rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for idx, row in enumerate(award_rows, start=1):
        raw_response = ROOT / row["raw_response_path"]
        generated_id = ""
        internal_id = ""
        if raw_response.exists():
            data = load_detail_json(raw_response)
            for item in data.get("results", []) if isinstance(data.get("results"), list) else []:
                if str(item.get("Award ID", "")) == row["award_id"]:
                    generated_id = str(item.get("generated_internal_id", "") or "")
                    internal_id = str(item.get("internal_id", "") or "")
                    break
        detail_key = generated_id or internal_id or row["award_id"]
        if detail_key in seen:
            continue
        seen.add(detail_key)
        url = f"https://api.usaspending.gov/api/v2/awards/{detail_key}/"
        out_path = RAW_OUT / "usaspending_award_details" / f"{safe_name(row['symbol'] + '_' + row['award_id'])}.json"
        status, http_status, error = http_get_json(url, out_path)
        detail = load_detail_json(out_path) if out_path.exists() and out_path.stat().st_size > 0 else {}
        recipient = detail.get("recipient", {}) if isinstance(detail.get("recipient"), dict) else {}
        recipient_uei = str(recipient.get("recipient_uei", "") or "")
        recipient_hash = str(recipient.get("recipient_hash", "") or "")
        recipient_name = str(recipient.get("recipient_name", "") or "")
        parent_recipient_uei = str(recipient.get("parent_recipient_uei", "") or "")
        parent_recipient_name = str(recipient.get("parent_recipient_name", "") or "")
        generated_unique_award_id = str(detail.get("generated_unique_award_id", "") or generated_id)
        date_signed = str(detail.get("date_signed", "") or row.get("award_start_date", ""))
        sha = file_sha256(out_path) if out_path.exists() and out_path.stat().st_size > 0 else ""
        detail_rows.append(
            {
                "task_id": "Task2099",
                "usaspending_award_detail_id": f"USASPENDDETAIL-2099-{idx:06d}",
                "symbol": row["symbol"],
                "award_id": row["award_id"],
                "generated_unique_award_id": generated_unique_award_id,
                "internal_award_id": internal_id,
                "recipient_name_search_row": row["recipient_name"],
                "recipient_name_detail": recipient_name,
                "recipient_uei": recipient_uei,
                "recipient_hash": recipient_hash,
                "parent_recipient_name": parent_recipient_name,
                "parent_recipient_uei": parent_recipient_uei,
                "date_signed": date_signed,
                "download_status": status,
                "http_status": http_status,
                "raw_detail_path": str(out_path.relative_to(ROOT)) if out_path.exists() else "",
                "raw_detail_sha256": sha,
                "source_url": url,
                "capture_ts": now_ts(),
                "error": error,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return detail_rows


def usaspending_certification_rows(award_rows: list[dict[str, str]], detail_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    detail_by_award = {str(row["award_id"]): row for row in detail_rows}
    identity_rows: list[dict[str, object]] = []
    l2_rows: list[dict[str, object]] = []
    l3_rows: list[dict[str, object]] = []
    for idx, row in enumerate(award_rows, start=1):
        detail = detail_by_award.get(row["award_id"], {})
        recipient_uei = str(detail.get("recipient_uei", "") or "")
        recipient_hash = str(detail.get("recipient_hash", "") or "")
        recipient_name_detail = str(detail.get("recipient_name_detail", "") or "")
        parent_name = str(detail.get("parent_recipient_name", "") or "")
        entity_id = recipient_uei or recipient_hash
        search_name = str(row.get("recipient_query_name", ""))
        recipient_name = recipient_name_detail or str(row.get("recipient_name", ""))
        exact_name = compact(search_name) == compact(recipient_name) and bool(search_name)
        parent_exact = compact(search_name) == compact(parent_name) and bool(search_name) and bool(parent_name)
        strict_state = row.get("recipient_match_state") == "strict_query_token_match"
        id_present = bool(entity_id)
        # Exact legal-name mapping is still not enough for historical L5 unless the award/detail
        # availability is proven before the decision. Keep the certified L5 gate separate.
        certified_identity = id_present and strict_state and (exact_name or parent_exact)
        subsidiary_or_name_blocker = "none" if exact_name else ("parent_exact_child_recipient" if parent_exact else "recipient_name_not_exact_symbol_entity")
        identity_id = f"USASPENDIDENTITY-2100-{idx:06d}"
        identity_rows.append(
            {
                "task_id": "Task2100",
                "usaspending_identity_map_id": identity_id,
                "symbol": row["symbol"],
                "award_id": row["award_id"],
                "generated_unique_award_id": detail.get("generated_unique_award_id", ""),
                "recipient_query_name": search_name,
                "recipient_name_detail": recipient_name,
                "recipient_uei_or_exact_entity_id": entity_id,
                "recipient_uei": recipient_uei,
                "recipient_hash": recipient_hash,
                "parent_recipient_name": parent_name,
                "parent_recipient_uei": detail.get("parent_recipient_uei", ""),
                "identity_source_url": detail.get("source_url", ""),
                "raw_detail_path": detail.get("raw_detail_path", ""),
                "raw_detail_sha256": detail.get("raw_detail_sha256", ""),
                "company_name_only_match": "1",
                "strict_query_token_match": "1" if strict_state else "0",
                "exact_legal_name_match": "1" if exact_name else "0",
                "parent_exact_legal_name_match": "1" if parent_exact else "0",
                "recipient_id_present": "1" if id_present else "0",
                "certified_identity_mapping_pass": "1" if certified_identity else "0",
                "l5_historical_certified_recipient_identity_gate_pass": "0",
                "historical_gate_blocker": "award_detail_captured_current_time_not_proven_available_before_decision_asof",
                "subsidiary_or_name_blocker": subsidiary_or_name_blocker,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        if certified_identity:
            l2_id = f"USASPENDL2-2101-{idx:06d}"
            l2_rows.append(
                {
                    "task_id": "Task2101",
                    "usaspending_certified_l2_id": l2_id,
                    "usaspending_identity_map_id": identity_id,
                    "symbol": row["symbol"],
                    "award_id": row["award_id"],
                    "recipient_uei_or_exact_entity_id": entity_id,
                    "semantic_state": "recipient_identity_certified_but_historical_l5_blocked",
                    "award_amount": row.get("award_amount", ""),
                    "award_start_date": row.get("award_start_date", ""),
                    "l5_historical_certified_recipient_identity_gate_pass": "0",
                    "blocker": "no_pre_decision_award_receipt_timestamp",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            l3_rows.append(
                {
                    "task_id": "Task2102",
                    "usaspending_certified_l3_edge_id": f"USASPENDL3-2102-{idx:06d}",
                    "from_usaspending_certified_l2_id": l2_id,
                    "symbol": row["symbol"],
                    "award_id": row["award_id"],
                    "relation_type": "recipient_identity_certifies_award_entity_but_not_historical_l5_timing",
                    "l5_historical_certified_recipient_identity_gate_pass": "0",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
    return identity_rows, l2_rows, l3_rows


def integrated_gate_rows(
    prior_gate: list[dict[str, str]],
    transcript_gate: list[dict[str, object]],
    analyst_gate: list[dict[str, object]],
    identity_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    transcript_by_spec = {row["trade_spec_id"]: row for row in transcript_gate}
    analyst_by_spec = {row["trade_spec_id"]: row for row in analyst_gate}
    identity_by_symbol: dict[str, list[dict[str, object]]] = {}
    for row in identity_rows:
        identity_by_symbol.setdefault(str(row["symbol"]), []).append(row)

    rows: list[dict[str, object]] = []
    for idx, prior in enumerate(prior_gate, start=1):
        spec = prior["trade_spec_id"]
        identities = identity_by_symbol.get(prior["symbol"], [])
        identity = next((row for row in identities if str(row["award_id"]) == str(prior.get("award_id_or_contract_id", ""))), None)
        identity_cert = "1" if identity and identity["certified_identity_mapping_pass"] == "1" else "0"
        l5_identity_gate = "0"
        earnings_pass = str(transcript_by_spec.get(spec, {}).get("earnings_call_gate_pass", "0"))
        analyst_pass = str(analyst_by_spec.get(spec, {}).get("analyst_revision_pit_gate_pass", "0"))

        blockers = [part for part in str(prior.get("blocker", "")).split("|") if part and part != "none"]
        blockers = [part for part in blockers if part not in {"earnings_call_vendor_or_source_gap", "analyst_revision_pit_gap"}]
        if earnings_pass != "1":
            blockers.append("earnings_call_transcript_source_gap")
        if analyst_pass != "1":
            blockers.append("analyst_revision_pit_source_gap")
        if prior.get("award_id_or_contract_id") and identity_cert == "1":
            blockers.append("usaspending_historical_receipt_gap")
        elif prior.get("award_id_or_contract_id"):
            blockers.append("usaspending_uei_or_recipient_identity_gap")
        blocker = "|".join(dict.fromkeys(blockers)) or "none"
        source_depth = int(float(prior.get("source_depth_score", "0") or 0)) + (1 if identity_cert == "1" else 0)
        full_pass = (
            str(prior.get("ir_ceo_ex99_gate_pass", "0")) == "1"
            and str(prior.get("govinfo_policy_raw_gate_pass", "0")) == "1"
            and str(prior.get("independent_customer_confirmation_gate_pass", "0")) == "1"
            and earnings_pass == "1"
            and analyst_pass == "1"
            and l5_identity_gate == "1"
        )
        out = dict(prior)
        out.update(
            {
                "task_id": "Task2103",
                "integrated_gate_id": f"FULLGATE-2103-{idx:06d}",
                "earnings_call_gate_pass": earnings_pass,
                "analyst_revision_pit_gate_pass": analyst_pass,
                "usaspending_identity_mapping_pass": identity_cert,
                "recipient_uei_or_exact_entity_id": identity.get("recipient_uei_or_exact_entity_id", "") if identity else prior.get("recipient_uei_or_exact_entity_id", ""),
                "usaspending_identity_map_id": identity.get("usaspending_identity_map_id", "") if identity else "",
                "certified_recipient_identity_gate_pass": l5_identity_gate,
                "source_depth_score": source_depth,
                "full_source_extractor_gate_pass": "1" if full_pass else "0",
                "paper_shadow_trade_allowed": "0",
                "real_capital_trade_allowed": "0",
                "blocker": blocker,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        rows.append(out)
    return rows


def audit_rows() -> list[dict[str, object]]:
    findings = [
        (
            "earnings_call_transcript_gate",
            "SEC EX-99.1 and earnings releases are support-only and cannot substitute for call/Q&A transcripts.",
            "Keep earnings_call_gate_pass at zero until provider event/document ids, raw transcript hash, speaker structure, and PIT availability timestamp exist.",
        ),
        (
            "analyst_pit_revision_gate",
            "Issuer guidance and current analyst snapshots are not PIT analyst revisions.",
            "Keep analyst_revision_pit_gate_pass at zero until a historical revision feed with revision timestamps and provider availability is attached.",
        ),
        (
            "usaspending_uei_recipient_gate",
            "Award detail endpoint can provide recipient UEI/hash, but current capture time does not prove the award detail was available before each trade decision.",
            "Record identity mapping separately, then keep historical L5 certified recipient gate blocked pending pre-decision receipt proof or approved PIT award source.",
        ),
        (
            "integrated_full_source_gate",
            "Paper shadow remains blocked because transcript, analyst PIT, and historical recipient timing gates are still incomplete.",
            "Do not run replay, paper orders, deployment, or real-capital promotion from this task.",
        ),
    ]
    return [
        {
            "task_id": "Task2104",
            "expert_audit_id": f"EXPERTAUDIT-2104-{idx:03d}",
            "gate_family": family,
            "finding": finding,
            "implementation_decision": decision,
            "review_authority": "SUBAGENT_AND_SOURCE_DOC_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (family, finding, decision) in enumerate(findings, start=1)
    ]


def closeout_rows(scope: list[dict[str, str]], transcript_gate: list[dict[str, object]], analyst_gate: list[dict[str, object]], detail_rows: list[dict[str, object]], identity_rows: list[dict[str, object]], certified_l2: list[dict[str, object]], full_gate: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2120",
            "verdict": "transcript_analyst_uei_gate_hardening_complete_diagnostic_only",
            "aggressive_scope_rows": len(scope),
            "transcript_gate_pass_rows": sum(1 for row in transcript_gate if row["earnings_call_gate_pass"] == "1"),
            "analyst_pit_gate_pass_rows": sum(1 for row in analyst_gate if row["analyst_revision_pit_gate_pass"] == "1"),
            "usaspending_award_detail_rows": len(detail_rows),
            "usaspending_identity_mapping_pass_rows": sum(1 for row in identity_rows if row["certified_identity_mapping_pass"] == "1"),
            "usaspending_l5_historical_gate_pass_rows": sum(1 for row in identity_rows if row["l5_historical_certified_recipient_identity_gate_pass"] == "1"),
            "usaspending_certified_l2_rows": len(certified_l2),
            "full_source_extractor_gate_pass_rows": sum(1 for row in full_gate if row["full_source_extractor_gate_pass"] == "1"),
            "paper_shadow_policy_status": "BLOCKED_UNTIL_TRANSCRIPT_ANALYST_AND_HISTORICAL_RECIPIENT_GATES_PASS",
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
    text = f"""# Task2091-2120 Transcript, Analyst PIT, and USAspending UEI Gates

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Aggressive scope rows: {closeout['aggressive_scope_rows']}.
- Earnings call transcript gate pass rows: {closeout['transcript_gate_pass_rows']}.
- Analyst PIT revision gate pass rows: {closeout['analyst_pit_gate_pass_rows']}.
- USAspending award detail rows: {closeout['usaspending_award_detail_rows']}.
- USAspending identity mapping pass rows: {closeout['usaspending_identity_mapping_pass_rows']}.
- USAspending historical L5 gate pass rows: {closeout['usaspending_l5_historical_gate_pass_rows']}.
- USAspending certified L2 rows: {closeout['usaspending_certified_l2_rows']}.
- Full source extractor gate pass rows: {closeout['full_source_extractor_gate_pass_rows']}.
- Paper shadow policy status: `{closeout['paper_shadow_policy_status']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task hardens three remaining source gates for the frozen aggressive policy.

1. Earnings call transcript gate:
   - SEC EX-99.1 earnings releases remain IR/CEO support only.
   - No row can pass without provider event id, provider document id, raw transcript hash, and PIT provider availability time.

2. Analyst PIT revision gate:
   - Prior local audit and vendor schema rows remain useful as contracts.
   - No row can pass without historical revision timestamp, provider availability timestamp, revision direction, analyst/broker identity or analyst count, raw source path, and hash.

3. USAspending UEI/recipient certification:
   - Official award detail endpoint is captured for existing award rows.
   - Recipient UEI/hash can certify award entity identity for some rows.
   - Historical L5 recipient gate remains blocked because current capture does not prove pre-decision availability and subsidiary/legal entity mapping remains unresolved for some names.

No replay, price lookup, order generation, paper trading, deployment claim, or real-capital permission is produced.

## No-Background Decision-Maker Report

1. 실적콜 transcript는 아직 없음. 발표자료랑 transcript를 섞지 않게 막았음.
2. analyst revision도 아직 없음. 현재/무료 스냅샷으로 과거 PIT revision을 만든 척하지 않게 막았음.
3. USAspending은 공식 award detail에서 UEI/hash를 받아 붙였음.
4. 하지만 L5 매매 gate는 아직 안 열림. 그 정보가 당시 매수 전에 확인 가능했다는 증거가 부족함.
5. 그래서 paper-shadow는 계속 막힘.

## Source Notes

- USAspending endpoints: `https://api.usaspending.gov/docs/endpoints`
- USAspending award detail endpoint: `/api/v2/awards/<AWARD_ID>/`
- Quartr transcript documentation: `https://quartr.com/docs/datasets/earnings-call-transcripts`
- Nasdaq Data Link Zacks revisions catalog: `https://data.nasdaq.com/databases/ZREV`

## Artifact Manifest

- `task2091_source_gate_contract.csv`
- `task2092_transcript_source_option_audit.csv`
- `task2093_transcript_l1_packets.csv`
- `task2094_transcript_l2_semantics.csv`
- `task2095_transcript_gate_panel.csv`
- `task2096_analyst_source_contract.csv`
- `task2097_analyst_revision_l1_packets.csv`
- `task2098_analyst_revision_gate_panel.csv`
- `task2099_usaspending_award_detail_downloads.csv`
- `task2100_usaspending_recipient_identity_map.csv`
- `task2101_usaspending_certified_l2_semantics.csv`
- `task2102_usaspending_certified_l3_edges.csv`
- `task2103_integrated_full_source_gate.csv`
- `task2104_expert_audit.csv`
- `task2120_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    text = registry.read_text(encoding="utf-8")
    if "Task2091," in text:
        return
    titles = {
        2091: "Transcript Analyst UEI Gate Contract",
        2092: "Transcript Source Option Audit",
        2093: "Transcript L1 Packets",
        2094: "Transcript L2 Semantics",
        2095: "Transcript Gate Panel",
        2096: "Analyst PIT Source Contract",
        2097: "Analyst Revision L1 Packets",
        2098: "Analyst Revision Gate Panel",
        2099: "USAspending Award Detail Downloads",
        2100: "USAspending Recipient Identity Map",
        2101: "USAspending Certified L2 Semantics",
        2102: "USAspending Certified L3 Edges",
        2103: "Integrated Transcript Analyst UEI Full Gate",
        2104: "Expert Audit",
        2105: "Transcript Negative Fixture",
        2106: "Analyst PIT Negative Fixture",
        2107: "USAspending Historical Receipt Blocker",
        2108: "Subsidiary Entity Blocker",
        2109: "Source Family Delta",
        2110: "Paper Shadow Blocker Recompute",
        2111: "Gate Manifest",
        2112: "Validation Contract",
        2113: "Source Citation Contract",
        2114: "Subagent Audit Incorporation",
        2115: "No Replay Closeout",
        2116: "Operating State Update",
        2117: "Artifact Manifest",
        2118: "Decision CSV",
        2119: "Registry Update",
        2120: "Transcript Analyst UEI Gate Closeout",
    }
    rows = []
    for task_num in range(2091, 2121):
        rows.append(
            {
                "task_id": f"Task{task_num}",
                "title": titles[task_num],
                "owner_team": "Research Governance / Data & Market Microstructure",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "transcript-analyst-uei-gates-hardened-paper-still-blocked",
                "parent_task": "Task2090" if task_num == 2091 else f"Task{task_num - 1}",
                "key_report": "docs/reports/task_2091_2120_transcript_analyst_uei_gates/task_2091_2120_transcript_analyst_uei_gates.md",
                "key_decision": "docs/reports/task_2091_2120_transcript_analyst_uei_gates/task_2091_2120_decision.csv",
                "key_artifacts": "data/artifacts/task_2091_2120_transcript_analyst_uei_gates",
                "validation_command": "python scripts/trader_brain_2091_2120_transcript_analyst_uei_gates_validate.py",
                "notes": "Transcript and analyst PIT gates remain blocked; USAspending official award detail UEI/hash identity mapping added but historical L5 gate remains blocked; no replay.",
            }
        )
    with registry.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writerows(rows)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    row = (
        f"105. Task2091-Task2120 hardened the remaining transcript, analyst PIT, and USAspending recipient gates for the frozen aggressive policy: "
        f"{closeout['transcript_gate_pass_rows']} earnings-call transcript pass rows, {closeout['analyst_pit_gate_pass_rows']} analyst PIT pass rows, "
        f"{closeout['usaspending_award_detail_rows']} USAspending award detail rows, {closeout['usaspending_identity_mapping_pass_rows']} recipient identity mapping pass rows, "
        f"{closeout['usaspending_l5_historical_gate_pass_rows']} historical L5 recipient gate pass rows, and {closeout['full_source_extractor_gate_pass_rows']} full-source gate-pass rows were produced; "
        f"paper shadow remains blocked while strategy remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    if row in text:
        return
    lines = text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if line.startswith("105. Task2091-Task2120"):
            lines[idx] = row
            path.write_text("".join(lines), encoding="utf-8")
            return
    insert_at = 0
    for idx, line in enumerate(lines):
        if line.startswith("104. Task2061-Task2090"):
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
    prior_gate = inputs["prior_gate"]
    awards = inputs["usaspending_awards"]

    contracts = source_contract_rows()
    transcript_options = transcript_option_rows()
    transcript_l1, transcript_l2, transcript_gate = transcript_gate_rows(scope, prior_gate)
    analyst_contracts = analyst_source_contract_rows()
    analyst_l1, analyst_gate = analyst_gate_rows(scope)
    detail_rows = fetch_award_details(awards)
    identity_rows, certified_l2, certified_l3 = usaspending_certification_rows(awards, detail_rows)
    full_gate = integrated_gate_rows(prior_gate, transcript_gate, analyst_gate, identity_rows)
    audits = audit_rows()
    closeout = closeout_rows(scope, transcript_gate, analyst_gate, detail_rows, identity_rows, certified_l2, full_gate)

    write_csv(OUT_DIR / "task2091_source_gate_contract.csv", contracts)
    write_csv(OUT_DIR / "task2092_transcript_source_option_audit.csv", transcript_options)
    write_csv(OUT_DIR / "task2093_transcript_l1_packets.csv", transcript_l1)
    write_csv(OUT_DIR / "task2094_transcript_l2_semantics.csv", transcript_l2)
    write_csv(OUT_DIR / "task2095_transcript_gate_panel.csv", transcript_gate)
    write_csv(OUT_DIR / "task2096_analyst_source_contract.csv", analyst_contracts)
    write_csv(OUT_DIR / "task2097_analyst_revision_l1_packets.csv", analyst_l1)
    write_csv(OUT_DIR / "task2098_analyst_revision_gate_panel.csv", analyst_gate)
    write_csv(OUT_DIR / "task2099_usaspending_award_detail_downloads.csv", detail_rows)
    write_csv(OUT_DIR / "task2100_usaspending_recipient_identity_map.csv", identity_rows)
    write_csv(OUT_DIR / "task2101_usaspending_certified_l2_semantics.csv", certified_l2)
    write_csv(OUT_DIR / "task2102_usaspending_certified_l3_edges.csv", certified_l3)
    write_csv(OUT_DIR / "task2103_integrated_full_source_gate.csv", full_gate)
    write_csv(OUT_DIR / "task2104_expert_audit.csv", audits)
    write_csv(OUT_DIR / "task2120_closeout.csv", closeout)
    write_json(OUT_DIR / "task2120_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0])
    update_registry()
    update_operating_state(closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(
        "[TASK2091_2120_OK] "
        f"scope={closeout[0]['aggressive_scope_rows']} "
        f"transcript_pass={closeout[0]['transcript_gate_pass_rows']} "
        f"analyst_pass={closeout[0]['analyst_pit_gate_pass_rows']} "
        f"usaspending_details={closeout[0]['usaspending_award_detail_rows']} "
        f"uei_identity_pass={closeout[0]['usaspending_identity_mapping_pass_rows']} "
        f"l5_uei_gate_pass={closeout[0]['usaspending_l5_historical_gate_pass_rows']} "
        f"full_gate_pass={closeout[0]['full_source_extractor_gate_pass_rows']}"
    )


if __name__ == "__main__":
    main()
