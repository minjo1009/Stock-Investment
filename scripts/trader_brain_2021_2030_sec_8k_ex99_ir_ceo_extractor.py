from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1834 = ROOT / "data/artifacts/task_1834_1847_targeted_source_implementation"
TASK1961 = ROOT / "data/artifacts/task_1961_1970_free_source_acquisition"
TASK2001 = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
OUT_DIR = ROOT / "data/artifacts/task_2021_2030_sec_8k_ex99_ir_ceo_extractor"
RAW_OUT = ROOT / "data/raw/task_2021_2030_sec_8k_ex99_ir_ceo_extractor"
REPORT_DIR = ROOT / "docs/reports/task_2021_2030_sec_8k_ex99_ir_ceo_extractor"
REPORT = REPORT_DIR / "task_2021_2030_sec_8k_ex99_ir_ceo_extractor.md"
DECISION = REPORT_DIR / "task_2021_2030_decision.csv"
AUTHORITY = "DIAGNOSTIC_SEC_8K_EX99_IR_CEO_EXTRACTOR_ONLY"
POLICY_ID = "winner_accel_top5_to_top2_convex_v1"


DOCUMENT_RE = re.compile(r"<DOCUMENT>(.*?)</DOCUMENT>", re.I | re.S)
TEXT_RE = re.compile(r"<TEXT>(.*?)</TEXT>", re.I | re.S)

IR_KEYWORDS = {
    "guidance": ["guidance", "outlook", "expects", "forecast", "raise", "raised", "lower", "lowered"],
    "demand": ["demand", "orders", "bookings", "backlog", "pipeline", "customer demand"],
    "customer_momentum": ["customer", "customers", "design win", "hyperscale", "cloud", "enterprise"],
    "capacity": ["capacity", "supply", "ramp", "production", "shipment", "shipments"],
    "pricing": ["pricing", "price", "asp", "average selling price"],
    "margin": ["margin", "gross margin", "operating margin", "profitability"],
    "risk": ["risk", "uncertain", "headwind", "challenge", "weakness", "delay"],
    "financing": ["offering", "convertible", "warrant", "atm", "debt", "credit facility"],
    "policy_exposure": ["export", "regulation", "government", "policy", "chips", "tariff"],
}

SPEAKER_PATTERNS = [
    ("ceo", re.compile(r"\b(chief executive officer|ceo|president and chief executive officer)\b", re.I)),
    ("cfo", re.compile(r"\b(chief financial officer|cfo)\b", re.I)),
    ("management", re.compile(r"\b(chairman|president|executive vice president|senior vice president)\b", re.I)),
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


def clean_text(value: str, max_chars: int = 300_000) -> str:
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


def is_ex99_or_press_doc(doc_type: str, filename: str, description: str, text: str) -> tuple[bool, str, str]:
    meta = " ".join([doc_type, filename, description]).lower()
    dtype = doc_type.upper().strip()
    suffix = Path(filename.lower()).suffix
    text_like = suffix in {".htm", ".html", ".txt", ".xml", ""} and dtype != "GRAPHIC"
    ex991_name = any(token in meta for token in ["ex-99.1", "ex99.1", "ex99_1", "ex99-1", "ex_991", "dex991", "99.1"])
    if dtype.startswith("EX-99.1") and text_like:
        return True, "ex99_1_strict_detected", "1"
    if dtype.startswith("EX-99") and ex991_name and text_like:
        return True, "ex99_1_loose_detected", "1"
    if dtype.startswith("EX-99") and text_like:
        return True, "other_ex99_family_reference_only", "0"
    if "press release" in meta:
        return True, "press_release_candidate_reference_only", "0"
    probe = text[:25_000].lower()
    if any(phrase in probe for phrase in ["press release", "announces financial results", "reports financial results", "quarterly results", "fiscal year results"]):
        return True, "press_release_candidate_reference_only", "0"
    return False, "not_ir_press_candidate", "0"


def statement_families(text: str) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    families = []
    snippets = []
    for family, keywords in IR_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in lowered]
        if hits:
            families.append(family)
            snippets.extend(hits[:3])
    return sorted(set(families)), sorted(set(snippets))


def speaker_role(text: str) -> str:
    head = text[:60_000]
    for role, pattern in SPEAKER_PATTERNS:
        if pattern.search(head):
            return role
    return "issuer_statement"


def bounded_snippet(text: str, keywords: list[str]) -> str:
    lowered = text.lower()
    positions = [lowered.find(keyword.lower()) for keyword in keywords if lowered.find(keyword.lower()) >= 0]
    if not positions:
        return text[:500]
    pos = min(positions)
    start = max(0, pos - 220)
    end = min(len(text), pos + 520)
    return text[start:end]


def load_inputs() -> dict[str, object]:
    return {
        "scope": read_csv(TASK2001 / "task2004_aggressive_source_extraction_panel.csv"),
        "sec_packets": read_csv(TASK1834 / "task1836_sec_financing_dilution_source_packets.csv"),
        "guidance": read_csv(TASK1961 / "task1965_sec_guidance_expanded_receipt_ledger.csv"),
    }


def scope_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(inputs["scope"], start=1):
        rows.append(
            {
                "task_id": "Task2021",
                "scope_id": f"EX99SCOPE-2021-{idx:06d}",
                "policy_variant_id": row["policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "beneficiary_chain": row["beneficiary_chain"],
                "prior_ir_ceo_state": row["ir_ceo_extractor_state"],
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def candidate_docs(inputs: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    scope_by_spec = {row["trade_spec_id"]: row for row in inputs["scope"]}
    scope_ids = set(scope_by_spec)
    packet_rows = [
        row for row in inputs["sec_packets"]
        if row["trade_spec_id"] in scope_ids
        and row.get("form") == "8-K"
        and row.get("asof_guard_pass") == "1"
        and row.get("inferred_matching_used") == "0"
    ]
    rows: list[dict[str, object]] = []
    rejections: list[dict[str, object]] = []
    doc_idx = 1
    reject_idx = 1
    for packet in packet_rows:
        decision = parse_ts(scope_by_spec[packet["trade_spec_id"]]["decision_asof_ts"])
        available = parse_ts(packet.get("available_to_brain_ts", ""))
        path = ROOT / packet.get("local_path", "")
        if not path.exists() or not decision or not available or available > decision:
            rejections.append(
                {
                    "task_id": "Task2027",
                    "rejection_id": f"EX99REJECT-2027-{reject_idx:06d}",
                    "trade_spec_id": packet["trade_spec_id"],
                    "symbol": packet["symbol"],
                    "accession": packet.get("accession", ""),
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
        docs = DOCUMENT_RE.findall(raw)
        if not docs:
            docs = [raw]
        detected = 0
        for seq, doc in enumerate(docs, start=1):
            doc_type = tag_value(doc, "TYPE") or packet.get("document_type", "")
            filename = tag_value(doc, "FILENAME") or packet.get("primary_document", "")
            description = tag_value(doc, "DESCRIPTION")
            text = clean_text(document_text(doc))
            is_candidate, state, gate_eligible = is_ex99_or_press_doc(doc_type, filename, description, text)
            if not is_candidate:
                continue
            detected += 1
            out_dir = RAW_OUT / packet["symbol"] / packet["accession"]
            out_dir.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", filename or f"document_{seq}.txt")[:120]
            raw_out = out_dir / f"{seq:02d}_{safe_name}.txt"
            raw_out.write_text(text, encoding="utf-8")
            families, keyword_hits = statement_families(text)
            rows.append(
                {
                    "task_id": "Task2022",
                    "ex99_doc_id": f"EX99DOC-2022-{doc_idx:07d}",
                    "trade_spec_id": packet["trade_spec_id"],
                    "candidate_source_id": packet["candidate_source_id"],
                    "symbol": packet["symbol"],
                    "decision_asof_ts": scope_by_spec[packet["trade_spec_id"]]["decision_asof_ts"],
                    "cik": packet.get("cik", ""),
                    "accession": packet.get("accession", ""),
                    "form": packet.get("form", ""),
                    "items": packet.get("items", ""),
                    "acceptance_datetime": packet.get("acceptance_datetime", ""),
                    "available_to_brain_ts": packet.get("available_to_brain_ts", ""),
                    "sec_url": packet.get("sec_url", ""),
                    "complete_submission_local_path": packet.get("local_path", ""),
                    "complete_submission_sha256": packet.get("sha256", ""),
                    "document_sequence": seq,
                    "document_type": doc_type,
                    "document_filename": filename,
                    "document_description": description,
                    "exhibit_detection_state": state,
                    "ex99_1_gate_eligible": gate_eligible,
                    "statement_family_hits": "|".join(families),
                    "keyword_hits": "|".join(keyword_hits),
                    "speaker_role_proxy": speaker_role(text),
                    "extracted_text_local_path": str(raw_out.relative_to(ROOT)).replace("\\", "/"),
                    "extracted_text_sha256": file_sha256(raw_out),
                    "statement_text_hash": sha256_text(text),
                    "asof_guard_pass": "1",
                    "inferred_matching_used": "0",
                    "current_2026_direct_input_used": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            doc_idx += 1
        if detected == 0:
            rejections.append(
                {
                    "task_id": "Task2027",
                    "rejection_id": f"EX99REJECT-2027-{reject_idx:06d}",
                    "trade_spec_id": packet["trade_spec_id"],
                    "symbol": packet["symbol"],
                    "accession": packet.get("accession", ""),
                    "reason": "no_exhibit_99_1_or_reference_candidate_detected",
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            reject_idx += 1
    return rows, rejections


def snippet_rows(docs: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, doc in enumerate(docs, start=1):
        path = ROOT / str(doc["extracted_text_local_path"])
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        keywords = str(doc.get("keyword_hits", "")).split("|") if doc.get("keyword_hits") else []
        snippet = bounded_snippet(text, keywords)
        rows.append(
            {
                "task_id": "Task2023",
                "statement_snippet_id": f"EX99SNIP-2023-{idx:07d}",
                "ex99_doc_id": doc["ex99_doc_id"],
                "trade_spec_id": doc["trade_spec_id"],
                "symbol": doc["symbol"],
                "decision_asof_ts": doc["decision_asof_ts"],
                "speaker_role_proxy": doc["speaker_role_proxy"],
                "statement_family_hits": doc["statement_family_hits"],
                "snippet_text": snippet[:900],
                "snippet_hash": sha256_text(snippet),
                "bounded_snippet_word_count": len(snippet.split()),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def l2_rows(docs: list[dict[str, object]]) -> list[dict[str, object]]:
    best_by_spec: dict[str, dict[str, object]] = {}
    for doc in docs:
        if doc.get("ex99_1_gate_eligible") != "1":
            continue
        spec = str(doc["trade_spec_id"])
        current = best_by_spec.get(spec)
        score = len(str(doc.get("statement_family_hits", "")).split("|")) if doc.get("statement_family_hits") else 0
        if not current or score > int(current["_score"]):
            best = dict(doc)
            best["_score"] = score
            best_by_spec[spec] = best
    rows = []
    for idx, (spec, doc) in enumerate(sorted(best_by_spec.items()), start=1):
        families = set(str(doc.get("statement_family_hits", "")).split("|")) if doc.get("statement_family_hits") else set()
        positive = len(families & {"guidance", "demand", "customer_momentum", "capacity", "pricing", "margin"})
        risk = len(families & {"risk", "financing", "policy_exposure"})
        if positive >= 3 and risk == 0:
            state = "ir_ceo_positive_support"
        elif positive >= 2 and risk <= 1:
            state = "ir_ceo_mixed_support"
        elif risk >= 2:
            state = "ir_ceo_risk_or_financing_caution"
        else:
            state = "ir_ceo_low_signal"
        rows.append(
            {
                "task_id": "Task2024",
                "l2_ir_ceo_semantic_id": f"EX99L2-2024-{idx:06d}",
                "trade_spec_id": spec,
                "candidate_source_id": doc["candidate_source_id"],
                "symbol": doc["symbol"],
                "decision_asof_ts": doc["decision_asof_ts"],
                "best_ex99_doc_id": doc["ex99_doc_id"],
                "ir_ceo_semantic_state": state,
                "positive_family_count": positive,
                "risk_family_count": risk,
                "statement_family_hits": doc.get("statement_family_hits", ""),
                "speaker_role_proxy": doc.get("speaker_role_proxy", ""),
                "asof_guard_pass": "1",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def l3_rows(l2: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    edge_idx = 1
    for row in l2:
        families = set(row.get("statement_family_hits", "").split("|")) if row.get("statement_family_hits") else set()
        mechanisms = []
        if families & {"guidance", "demand"}:
            mechanisms.append(("issuer_guidance_or_demand_supports_winner_thesis", "supports"))
        if "customer_momentum" in families:
            mechanisms.append(("issuer_statement_confirms_customer_momentum", "supports"))
        if families & {"capacity", "pricing", "margin"}:
            mechanisms.append(("issuer_operating_quality_supports_monetization", "supports"))
        if families & {"risk", "financing"}:
            mechanisms.append(("issuer_statement_routes_to_risk_budget", "routes_to_risk_budget"))
        if not mechanisms:
            mechanisms.append(("issuer_statement_low_signal_no_edge_promotion", "weakens"))
        for mechanism, relation in mechanisms:
            rows.append(
                {
                    "task_id": "Task2025",
                    "l3_ir_ceo_edge_id": f"EX99L3-2025-{edge_idx:07d}",
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "from_l2_ir_ceo_semantic_id": row["l2_ir_ceo_semantic_id"],
                    "mechanism_edge": mechanism,
                    "relation_type": relation,
                    "asof_guard_pass": "1",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            edge_idx += 1
    return rows


def gate_rows(scope: list[dict[str, object]], l2: list[dict[str, object]]) -> list[dict[str, object]]:
    l2_by_spec = {row["trade_spec_id"]: row for row in l2}
    rows = []
    for idx, row in enumerate(scope, start=1):
        semantic = l2_by_spec.get(row["trade_spec_id"])
        attached = semantic is not None
        rows.append(
            {
                "task_id": "Task2026",
                "ir_ceo_gate_id": f"EX99GATE-2026-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "prior_ir_ceo_state": row["prior_ir_ceo_state"],
                "new_ir_ceo_extractor_state": "attached_asof_exhibit_99_1" if attached else "source_gap_neutral",
                "l2_ir_ceo_semantic_id": semantic.get("l2_ir_ceo_semantic_id", "") if semantic else "",
                "ir_ceo_family_gate_pass": "1" if attached else "0",
                "paper_shadow_trade_allowed_after_ir_ceo_only": "0",
                "paper_shadow_blocker": "other_source_families_still_required",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def audit_rows() -> list[dict[str, object]]:
    rows = [
        ("sec_exhibit_engineer", "Use exact existing trade_spec/CIK/accession paths; do not overwrite with current ticker map.", "adopted_exact_existing_packet_join"),
        ("ir_ceo_specialist", "Extract Exhibit 99.1 and press release documents first; speaker role is a proxy until structured transcript exists.", "adopted_ex99_press_release_proxy"),
        ("quant_governance", "IR/CEO family pass does not open paper shadow because transcript/customer/policy gates remain open.", "paper_gate_remains_blocked"),
        ("backend_validator", "Validator must enforce no current source, no outcome assignment, as-of pass, and no inferred matching.", "implemented_validator_contract"),
    ]
    return [
        {
            "task_id": "Task2028",
            "audit_id": f"EX99AUDIT-2028-{idx:03d}",
            "role": role,
            "finding": finding,
            "implementation_decision": decision,
            "review_authority": "SUBAGENT_GPT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (role, finding, decision) in enumerate(rows, start=1)
    ]


def closeout_rows(scope: list[dict[str, object]], docs: list[dict[str, object]], l2: list[dict[str, object]], gates: list[dict[str, object]], rejections: list[dict[str, object]]) -> list[dict[str, object]]:
    attached = sum(1 for row in gates if row["ir_ceo_family_gate_pass"] == "1")
    detection_counts = Counter(str(row.get("exhibit_detection_state", "")) for row in docs)
    return [
        {
            "task_id": "Task2030",
            "verdict": "sec_8k_ex99_ir_ceo_extractor_complete_diagnostic_only",
            "aggressive_scope_rows": len(scope),
            "ex99_candidate_doc_rows": len(docs),
            "ex99_1_strict_doc_rows": detection_counts.get("ex99_1_strict_detected", 0),
            "ex99_1_loose_doc_rows": detection_counts.get("ex99_1_loose_detected", 0),
            "reference_only_doc_rows": sum(
                count for state, count in detection_counts.items()
                if state not in {"ex99_1_strict_detected", "ex99_1_loose_detected"}
            ),
            "ir_ceo_l2_semantic_rows": len(l2),
            "ir_ceo_family_gate_pass_rows": attached,
            "rejection_rows": len(rejections),
            "paper_shadow_policy_status": "BLOCKED_OTHER_SOURCE_FAMILIES_STILL_REQUIRED",
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
    text = f"""# Task2021-2030 SEC 8-K Exhibit 99.1 IR/CEO Extractor

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Aggressive scope rows: {closeout['aggressive_scope_rows']}.
- Exhibit/reference candidate docs: {closeout['ex99_candidate_doc_rows']}.
- Strict EX-99.1 docs: {closeout['ex99_1_strict_doc_rows']}.
- Loose EX-99.1 docs: {closeout['ex99_1_loose_doc_rows']}.
- Reference-only docs: {closeout['reference_only_doc_rows']}.
- IR/CEO L2 semantic rows: {closeout['ir_ceo_l2_semantic_rows']}.
- IR/CEO family gate pass rows: {closeout['ir_ceo_family_gate_pass_rows']}.
- Rejection rows: {closeout['rejection_rows']}.
- Paper shadow policy status: `{closeout['paper_shadow_policy_status']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task attaches the first missing source family for the aggressive policy: issuer IR/CEO evidence from SEC 8-K Exhibit 99.1 documents.

Press-release-like 8-K body text and other EX-99 family documents are retained as reference-only diagnostics. They do not pass the IR/CEO family gate.

Rules:

- Only existing trade-spec, CIK, accession, and local raw filing paths are used.
- `available_to_brain_ts <= decision_asof_ts` is required.
- No symbol/date/price/time proximity fallback is used.
- Only strict or loose EX-99.1 documents can pass the IR/CEO family gate.
- Missing Exhibit 99.1 is a neutral source gap, not a negative signal.
- Speaker role is a deterministic proxy from text, not a certified transcript speaker label.
- This does not open paper shadow because earnings call, customer confirmation, and policy/news gates remain required.

## No-Background Decision-Maker Report

1. Company announcement / CEO-style evidence has now been attached from SEC EX-99.1 documents.
2. This improves source backing for the aggressive policy.
3. It still does not allow paper trading automation by itself.
4. Next source family should be official policy/news or customer-confirmation fixtures.

## Artifact Manifest

- `task2021_aggressive_ir_ceo_scope.csv`
- `task2022_sec_8k_ex99_candidate_docs.csv`
- `task2023_ir_ceo_statement_snippets.csv`
- `task2024_l2_ir_ceo_semantics.csv`
- `task2025_l3_ir_ceo_edges.csv`
- `task2026_ir_ceo_gate_delta.csv`
- `task2027_negative_fixture_rejections.csv`
- `task2028_subagent_audit.csv`
- `task2030_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    text = registry.read_text(encoding="utf-8")
    if "Task2021," in text:
        return
    titles = {
        2021: "Aggressive IR CEO Scope",
        2022: "SEC 8-K Exhibit 99 Candidate Docs",
        2023: "IR CEO Statement Snippets",
        2024: "IR CEO L2 Semantics",
        2025: "IR CEO L3 Edges",
        2026: "IR CEO Gate Delta",
        2027: "IR CEO Negative Fixtures",
        2028: "IR CEO Subagent Audit",
        2029: "IR CEO Artifact Manifest",
        2030: "IR CEO Extractor Closeout",
    }
    rows = []
    for task_num in range(2021, 2031):
        rows.append(
            {
                "task_id": f"Task{task_num}",
                "title": titles[task_num],
                "owner_team": "Research Governance / Source Acquisition",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "ir-ceo-source-family-attached-paper-still-blocked",
                "parent_task": "Task2020" if task_num == 2021 else f"Task{task_num - 1}",
                "key_report": "docs/reports/task_2021_2030_sec_8k_ex99_ir_ceo_extractor/task_2021_2030_sec_8k_ex99_ir_ceo_extractor.md",
                "key_decision": "docs/reports/task_2021_2030_sec_8k_ex99_ir_ceo_extractor/task_2021_2030_decision.csv",
                "key_artifacts": "data/artifacts/task_2021_2030_sec_8k_ex99_ir_ceo_extractor",
                "validation_command": "python scripts/trader_brain_2021_2030_sec_8k_ex99_ir_ceo_extractor_validate.py",
                "notes": "Attaches strict/loose SEC 8-K Exhibit 99.1 issuer IR/CEO evidence for aggressive policy trades while keeping paper shadow blocked.",
            }
        )
    with registry.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writerows(rows)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "102. Task2021-Task2030"
    row = (
        f"102. Task2021-Task2030 attached the SEC 8-K Exhibit 99.1 IR-CEO source family for the aggressive policy: "
        f"{closeout['aggressive_scope_rows']} scope rows, {closeout['ex99_candidate_doc_rows']} candidate/reference docs, "
        f"{closeout['ex99_1_strict_doc_rows']} strict EX-99.1 docs, {closeout['ex99_1_loose_doc_rows']} loose EX-99.1 docs, "
        f"{closeout['ir_ceo_l2_semantic_rows']} L2 semantic rows, and {closeout['ir_ceo_family_gate_pass_rows']} IR/CEO gate-pass rows were produced; "
        "paper shadow remains blocked because other source families are still required, while strategy remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    lines = text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if line.startswith(marker):
            lines[idx] = row
            path.write_text("".join(lines), encoding="utf-8")
            return
    insert_at = 0
    for idx, line in enumerate(lines):
        if line.startswith("101. Task2011-Task2020"):
            insert_at = idx + 1
            break
    lines.insert(insert_at, row)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    scope = scope_rows(inputs)
    docs, rejections = candidate_docs(inputs)
    snippets = snippet_rows(docs)
    l2 = l2_rows(docs)
    l3 = l3_rows(l2)
    gates = gate_rows(scope, l2)
    audit = audit_rows()
    closeout = closeout_rows(scope, docs, l2, gates, rejections)

    write_csv(OUT_DIR / "task2021_aggressive_ir_ceo_scope.csv", scope)
    write_csv(OUT_DIR / "task2022_sec_8k_ex99_candidate_docs.csv", docs)
    write_csv(OUT_DIR / "task2023_ir_ceo_statement_snippets.csv", snippets)
    write_csv(OUT_DIR / "task2024_l2_ir_ceo_semantics.csv", l2)
    write_csv(OUT_DIR / "task2025_l3_ir_ceo_edges.csv", l3)
    write_csv(OUT_DIR / "task2026_ir_ceo_gate_delta.csv", gates)
    write_csv(OUT_DIR / "task2027_negative_fixture_rejections.csv", rejections)
    write_csv(OUT_DIR / "task2028_subagent_audit.csv", audit)
    write_csv(OUT_DIR / "task2030_closeout.csv", closeout)
    write_json(OUT_DIR / "task2030_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0])
    update_registry()
    update_operating_state(closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(
        f"[TASK2021_2030_OK] docs={len(docs)} l2={len(l2)} gate={closeout[0]['ir_ceo_family_gate_pass_rows']}"
    )


if __name__ == "__main__":
    main()
