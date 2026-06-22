from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2031_2060_free_official_source_layers"
TASK2001 = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
TASK2021 = ROOT / "data/artifacts/task_2021_2030_sec_8k_ex99_ir_ceo_extractor"
REPORT = ROOT / "docs/reports/task_2031_2060_free_official_source_layers/task_2031_2060_free_official_source_layers.md"
DECISION = ROOT / "docs/reports/task_2031_2060_free_official_source_layers/task_2031_2060_decision.csv"
AUTHORITY = "DIAGNOSTIC_FREE_OFFICIAL_SOURCE_LAYERS_ONLY"
POLICY_ID = "winner_accel_top5_to_top2_convex_v1"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_ts(value: str) -> datetime:
    if not value:
        raise AssertionError("missing timestamp")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_policy_docs(rows: list[dict[str, str]]) -> None:
    require(len(rows) == 3898, f"expected 3898 Federal Register docs, got {len(rows)}")
    for row in rows:
        require(row["authority"] == AUTHORITY, "unexpected policy doc authority")
        require(row["provider"] == "Federal Register", "unexpected policy provider")
        require(row["document_number"], "missing Federal Register document_number")
        require(row["official_source_url"].startswith("https://www.federalregister.gov/documents/"), "non-Federal Register URL")
        require(row["official_pdf_url"].startswith("https://www.govinfo.gov/content/pkg/"), "missing GovInfo official PDF pointer")
        raw_path = ROOT / row["raw_source_path"]
        require(raw_path.exists(), f"missing Federal Register raw path: {raw_path}")
        require(file_sha256(raw_path) == row["raw_source_sha256"], "Federal Register raw hash mismatch")
        require(row["publication_ts"] == row["available_to_brain_ts"], "FR available timestamp must equal publication timestamp")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment in policy docs")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment in policy docs")


def validate_policy_layer(docs: list[dict[str, str]], l1: list[dict[str, str]], rejections: list[dict[str, str]], l2: list[dict[str, str]], l3: list[dict[str, str]], l4: list[dict[str, str]], l5: list[dict[str, str]]) -> None:
    doc_ids = {row["policy_source_doc_id"] for row in docs}
    require(len(l1) == 171, f"expected 171 policy L1 rows, got {len(l1)}")
    require(len(rejections) == 59, f"expected 59 policy rejections, got {len(rejections)}")
    for row in l1:
        require(row["authority"] == AUTHORITY, "unexpected policy L1 authority")
        require(row["policy_source_doc_id"] in doc_ids, "policy L1 points outside FR docs")
        require(row["matching_key"] == "beneficiary_chain_theme_keyword_prior_asof", "unexpected policy matching key")
        require(row["asof_guard_pass"] == "1", "policy L1 as-of guard not passed")
        require(parse_ts(row["available_to_brain_ts"]) <= parse_ts(row["decision_asof_ts"]), "policy L1 future source")
        require(row["inferred_matching_used"] == "0", "policy L1 inferred matching")
        require(row["missing_source_is_negative"] == "0", "policy L1 missing source negative")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment in policy L1")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment in policy L1")
    for row in rejections:
        require(row["missing_source_is_negative"] == "0", "policy rejection converted missing to negative")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment in policy rejection")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment in policy rejection")
    l1_ids = {row["policy_l1_packet_id"] for row in l1}
    require(len(l2) == 57, f"expected 57 policy L2 rows, got {len(l2)}")
    require(len(l3) == 57, f"expected 57 policy L3 rows, got {len(l3)}")
    require(len(l4) == 57, f"expected 57 policy L4 rows, got {len(l4)}")
    require(len(l5) == 116, f"expected 116 policy L5 rows, got {len(l5)}")
    l2_ids = {row["policy_l2_semantic_id"] for row in l2}
    l3_ids = {row["policy_l3_edge_id"] for row in l3}
    for row in l2:
        require(row["policy_l1_packet_id"] in l1_ids, "policy L2 points outside L1")
        require(row["asof_guard_pass"] == "1", "policy L2 as-of guard not passed")
        require(row["missing_source_is_negative"] == "0", "policy L2 missing source negative")
    for row in l3:
        require(row["from_policy_l2_semantic_id"] in l2_ids, "policy L3 points outside L2")
        require(row["asof_guard_pass"] == "1", "policy L3 as-of guard not passed")
    for row in l4:
        require(row["policy_l3_edge_id"] in l3_ids, "policy L4 points outside L3")
        require(row["can_directly_create_trade"] == "0", "policy L4 can directly create trade")
    for row in l5:
        require(row["paper_shadow_trade_allowed_after_policy_only"] == "0", "policy-only opened paper shadow")
        require(row["missing_source_is_negative"] == "0", "policy L5 missing source negative")


def validate_customer_layer(docs: list[dict[str, str]], rejections: list[dict[str, str]], l2: list[dict[str, str]], l3: list[dict[str, str]], l4: list[dict[str, str]], l5: list[dict[str, str]]) -> None:
    require(len(docs) == 156, f"expected 156 customer docs, got {len(docs)}")
    require(len(rejections) == 134, f"expected 134 customer rejections, got {len(rejections)}")
    allowed_quality = {
        "issuer_contract_exhibit_claim",
        "issuer_ex99_named_counterparty_contract_claim",
        "issuer_ex99_customer_momentum_claim",
        "issuer_8k_named_counterparty_contract_claim",
    }
    for row in docs:
        require(row["authority"] == AUTHORITY, "unexpected customer doc authority")
        require(row["source_side"] == "issuer_sec_filing", "customer doc must be issuer-side SEC filing")
        require(row["source_quality_state"] in allowed_quality, "unexpected customer source quality state")
        require(row["customer_claim_gate_eligible"] == "1", "customer doc not gate eligible")
        require(row["independent_customer_confirmation"] == "0", "issuer claim marked independent customer confirmation")
        require(row["asof_guard_pass"] == "1", "customer doc as-of guard not passed")
        require(row["inferred_matching_used"] == "0", "customer doc inferred matching")
        require(parse_ts(row["available_to_brain_ts"]) <= parse_ts(row["decision_asof_ts"]), "customer doc future source")
        complete_path = ROOT / row["complete_submission_local_path"]
        snippet_path = ROOT / row["snippet_local_path"]
        require(complete_path.exists(), f"missing SEC complete source: {complete_path}")
        require(snippet_path.exists(), f"missing customer snippet: {snippet_path}")
        require(file_sha256(complete_path) == row["complete_submission_sha256"], "SEC complete source hash mismatch")
        require(file_sha256(snippet_path) == row["snippet_sha256"], "customer snippet hash mismatch")
        require(row["missing_source_is_negative"] == "0", "customer doc missing source negative")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment in customer doc")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment in customer doc")
    for row in rejections:
        require(row["missing_source_is_negative"] == "0", "customer rejection converted missing to negative")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment in customer rejection")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment in customer rejection")
    doc_ids = {row["customer_contract_doc_id"] for row in docs}
    require(len(l2) == 78, f"expected 78 customer L2 rows, got {len(l2)}")
    require(len(l3) == 78, f"expected 78 customer L3 rows, got {len(l3)}")
    require(len(l4) == 78, f"expected 78 customer L4 rows, got {len(l4)}")
    require(len(l5) == 116, f"expected 116 customer L5 rows, got {len(l5)}")
    l2_ids = {row["customer_l2_semantic_id"] for row in l2}
    l3_ids = {row["customer_l3_edge_id"] for row in l3}
    for row in l2:
        require(row["customer_contract_doc_id"] in doc_ids, "customer L2 points outside docs")
        require(row["independent_customer_confirmation"] == "0", "customer L2 claims independent confirmation")
        require(row["asof_guard_pass"] == "1", "customer L2 as-of guard not passed")
        require(row["missing_source_is_negative"] == "0", "customer L2 missing source negative")
    for row in l3:
        require(row["from_customer_l2_semantic_id"] in l2_ids, "customer L3 points outside L2")
        require(row["relation_type"] == "issuer_claim_requires_independent_confirmation", "customer L3 overclaims confirmation")
        require(row["asof_guard_pass"] == "1", "customer L3 as-of guard not passed")
    for row in l4:
        require(row["customer_l3_edge_id"] in l3_ids, "customer L4 points outside L3")
        require(row["independent_confirmation_required"] == "1", "customer L4 missing independent confirmation requirement")
        require(row["can_directly_create_trade"] == "0", "customer L4 can directly create trade")
    for row in l5:
        require(row["independent_customer_confirmation_gate_pass"] == "0", "issuer claim opened independent customer gate")
        require(row["paper_shadow_trade_allowed_after_customer_only"] == "0", "customer-only opened paper shadow")
        require(row["missing_source_is_negative"] == "0", "customer L5 missing source negative")


def validate_full_gate(scope: list[dict[str, str]], ir_gate: list[dict[str, str]], policy_l5: list[dict[str, str]], customer_l5: list[dict[str, str]], full_gate: list[dict[str, str]]) -> None:
    require(len(scope) == 116, f"expected 116 frozen scope rows, got {len(scope)}")
    require(len(ir_gate) == 116, f"expected 116 IR gate rows, got {len(ir_gate)}")
    require(len(full_gate) == 116, f"expected 116 integrated gate rows, got {len(full_gate)}")
    scope_specs = {row["trade_spec_id"] for row in scope}
    policy_by_spec = {row["trade_spec_id"]: row for row in policy_l5}
    customer_by_spec = {row["trade_spec_id"]: row for row in customer_l5}
    ir_by_spec = {row["trade_spec_id"]: row for row in ir_gate}
    for row in full_gate:
        spec = row["trade_spec_id"]
        require(spec in scope_specs, "full gate outside frozen scope")
        require(row["frozen_policy_variant_id"] == POLICY_ID, "wrong frozen policy id")
        require(row["ir_ceo_ex99_gate_pass"] == ir_by_spec[spec]["ir_ceo_family_gate_pass"], "IR gate recompute mismatch")
        require(row["policy_news_gate_pass"] == policy_by_spec[spec]["policy_news_family_gate_pass"], "policy gate recompute mismatch")
        require(row["issuer_customer_claim_attached"] == customer_by_spec[spec]["issuer_customer_claim_attached"], "customer gate recompute mismatch")
        require(row["independent_customer_confirmation_gate_pass"] == "0", "independent customer gate unexpectedly passed")
        require(row["earnings_call_gate_pass"] == "0", "earnings call gate unexpectedly passed")
        require(row["analyst_revision_pit_gate_pass"] == "0", "analyst revision gate unexpectedly passed")
        expected_depth = sum(int(row[key]) for key in ["ir_ceo_ex99_gate_pass", "policy_news_gate_pass", "issuer_customer_claim_attached"])
        require(int(row["source_depth_score"]) == expected_depth, "source depth score mismatch")
        require(row["full_source_extractor_gate_pass"] == "0", "full-source gate unexpectedly passed")
        require(row["paper_shadow_trade_allowed"] == "0", "paper shadow opened")
        require(row["real_capital_trade_allowed"] == "0", "real capital opened")
        require(row["blocker"] != "none", "blocked row missing blocker")
        require(row["missing_source_is_negative"] == "0", "full gate missing source negative")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment in full gate")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment in full gate")


def validate_closeout(closeout: dict[str, str]) -> None:
    expected = {
        "verdict": "free_official_source_layers_complete_diagnostic_only",
        "loop_count": "3",
        "aggressive_scope_rows": "116",
        "federal_register_doc_rows": "3898",
        "policy_l1_match_rows": "171",
        "policy_l2_semantic_rows": "57",
        "policy_trade_gate_pass_rows": "57",
        "issuer_customer_contract_doc_rows": "156",
        "customer_l2_semantic_rows": "78",
        "issuer_customer_claim_trade_rows": "78",
        "independent_customer_confirmation_trade_rows": "0",
        "full_source_extractor_gate_pass_rows": "0",
        "paper_shadow_policy_status": "BLOCKED_UNTIL_FULL_SOURCE_EXTRACTOR_GATE",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "authority": AUTHORITY,
    }
    for key, value in expected.items():
        require(closeout.get(key) == value, f"closeout mismatch {key}: {closeout.get(key)} != {value}")


def main() -> None:
    scope = read_csv(TASK2001 / "task2004_aggressive_source_extraction_panel.csv")
    ir_gate = read_csv(TASK2021 / "task2026_ir_ceo_gate_delta.csv")
    policy_docs = read_csv(OUT_DIR / "task2032_federal_register_policy_docs.csv")
    policy_l1 = read_csv(OUT_DIR / "task2033_policy_l1_packets.csv")
    policy_rejections = read_csv(OUT_DIR / "task2034_policy_negative_rejections.csv")
    policy_l2 = read_csv(OUT_DIR / "task2035_policy_l2_semantics.csv")
    policy_l3 = read_csv(OUT_DIR / "task2036_policy_l3_edges.csv")
    policy_l4 = read_csv(OUT_DIR / "task2037_policy_l4_thesis.csv")
    policy_l5 = read_csv(OUT_DIR / "task2038_policy_l5_gate_delta.csv")
    customer_docs = read_csv(OUT_DIR / "task2041_issuer_customer_contract_docs.csv")
    customer_l2 = read_csv(OUT_DIR / "task2042_customer_l2_semantics.csv")
    customer_l3 = read_csv(OUT_DIR / "task2043_customer_l3_edges.csv")
    customer_rejections = read_csv(OUT_DIR / "task2044_customer_negative_rejections.csv")
    customer_l4 = read_csv(OUT_DIR / "task2045_customer_l4_thesis.csv")
    customer_l5 = read_csv(OUT_DIR / "task2046_customer_l5_gate_delta.csv")
    audits = read_csv(OUT_DIR / "task2051_three_loop_audit.csv")
    full_gate = read_csv(OUT_DIR / "task2052_integrated_full_source_gate.csv")
    closeout = read_csv(OUT_DIR / "task2060_closeout.csv")
    decision = read_csv(DECISION)

    require(REPORT.exists(), "missing report")
    require(len(audits) == 3, "three-loop audit rows missing")
    require(len(closeout) == 1, "expected one closeout")
    require(decision == closeout, "decision CSV differs from closeout")
    validate_policy_docs(policy_docs)
    validate_policy_layer(policy_docs, policy_l1, policy_rejections, policy_l2, policy_l3, policy_l4, policy_l5)
    validate_customer_layer(customer_docs, customer_rejections, customer_l2, customer_l3, customer_l4, customer_l5)
    validate_full_gate(scope, ir_gate, policy_l5, customer_l5, full_gate)
    validate_closeout(closeout[0])

    print("[TASK2031_2060_VALIDATE_OK] source_health=pass governance_health=pass paper_shadow=blocked")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
