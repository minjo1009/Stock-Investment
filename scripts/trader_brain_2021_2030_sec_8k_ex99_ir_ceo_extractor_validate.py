from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2021_2030_sec_8k_ex99_ir_ceo_extractor"
REPORT = ROOT / "docs/reports/task_2021_2030_sec_8k_ex99_ir_ceo_extractor/task_2021_2030_sec_8k_ex99_ir_ceo_extractor.md"
DECISION = ROOT / "docs/reports/task_2021_2030_sec_8k_ex99_ir_ceo_extractor/task_2021_2030_decision.csv"
AUTHORITY = "DIAGNOSTIC_SEC_8K_EX99_IR_CEO_EXTRACTOR_ONLY"


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


def validate_docs(docs: list[dict[str, str]]) -> None:
    require(len(docs) == 396, f"expected 396 candidate/reference docs, got {len(docs)}")
    eligible_states = {"ex99_1_strict_detected", "ex99_1_loose_detected"}
    strict = 0
    loose = 0
    reference = 0
    for row in docs:
        require(row["authority"] == AUTHORITY, "unexpected authority in docs")
        require(row["form"] == "8-K", "non-8-K document admitted")
        require(row["cik"], "missing CIK")
        require(row["accession"], "missing accession")
        require(row["trade_spec_id"], "missing trade_spec_id")
        require(row["sec_url"].startswith("https://www.sec.gov/Archives/"), "non-SEC URL admitted")
        require(row["asof_guard_pass"] == "1", "as-of guard failed doc admitted")
        require(row["inferred_matching_used"] == "0", "inferred matching admitted")
        require(row["current_2026_direct_input_used"] == "0", "current-2026 source admitted")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment flag in docs")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment flag in docs")
        require(parse_ts(row["available_to_brain_ts"]) <= parse_ts(row["decision_asof_ts"]), "available timestamp after decision")
        complete_path = ROOT / row["complete_submission_local_path"]
        extracted_path = ROOT / row["extracted_text_local_path"]
        require(complete_path.exists(), f"missing complete submission: {complete_path}")
        require(extracted_path.exists(), f"missing extracted text: {extracted_path}")
        require(file_sha256(complete_path) == row["complete_submission_sha256"], "complete submission hash mismatch")
        require(file_sha256(extracted_path) == row["extracted_text_sha256"], "extracted text hash mismatch")
        require(row["statement_text_hash"] == row["extracted_text_sha256"], "statement text hash must match extracted text hash")
        state = row["exhibit_detection_state"]
        eligible = row["ex99_1_gate_eligible"]
        if state in eligible_states:
            require(eligible == "1", "EX-99.1 state not gate eligible")
        else:
            require(eligible == "0", "reference-only state marked gate eligible")
        strict += state == "ex99_1_strict_detected"
        loose += state == "ex99_1_loose_detected"
        reference += state not in eligible_states
    require(strict == 175, f"expected 175 strict EX-99.1 docs, got {strict}")
    require(loose == 2, f"expected 2 loose EX-99.1 docs, got {loose}")
    require(reference == 219, f"expected 219 reference-only docs, got {reference}")


def validate_l2_l3(docs: list[dict[str, str]], l2: list[dict[str, str]], l3: list[dict[str, str]]) -> None:
    eligible_doc_ids = {row["ex99_doc_id"] for row in docs if row["ex99_1_gate_eligible"] == "1"}
    eligible_specs = {row["trade_spec_id"] for row in docs if row["ex99_1_gate_eligible"] == "1"}
    require(len(eligible_specs) == 102, f"expected 102 eligible trade specs, got {len(eligible_specs)}")
    require(len(l2) == 102, f"expected 102 L2 rows, got {len(l2)}")
    l2_ids = set()
    for row in l2:
        require(row["authority"] == AUTHORITY, "unexpected authority in L2")
        require(row["trade_spec_id"] in eligible_specs, "L2 created from non-eligible trade spec")
        require(row["best_ex99_doc_id"] in eligible_doc_ids, "L2 best doc is not EX-99.1 eligible")
        require(row["asof_guard_pass"] == "1", "L2 as-of guard not passed")
        require(row["missing_source_is_negative"] == "0", "L2 missing source converted to negative")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment flag in L2")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment flag in L2")
        l2_ids.add(row["l2_ir_ceo_semantic_id"])
    require(len(l3) == 377, f"expected 377 L3 edges, got {len(l3)}")
    for row in l3:
        require(row["authority"] == AUTHORITY, "unexpected authority in L3")
        require(row["from_l2_ir_ceo_semantic_id"] in l2_ids, "L3 edge points outside L2")
        require(row["asof_guard_pass"] == "1", "L3 as-of guard not passed")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment flag in L3")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment flag in L3")


def validate_gates(scope: list[dict[str, str]], l2: list[dict[str, str]], gates: list[dict[str, str]]) -> None:
    require(len(scope) == 116, f"expected 116 scope rows, got {len(scope)}")
    require(len(gates) == 116, f"expected 116 gate rows, got {len(gates)}")
    scope_specs = {row["trade_spec_id"] for row in scope}
    l2_by_spec = {row["trade_spec_id"]: row["l2_ir_ceo_semantic_id"] for row in l2}
    for row in scope:
        require(row["authority"] == AUTHORITY, "unexpected authority in scope")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment flag in scope")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment flag in scope")
    for row in gates:
        spec = row["trade_spec_id"]
        require(spec in scope_specs, "gate row outside scope")
        require(row["authority"] == AUTHORITY, "unexpected authority in gates")
        require(row["paper_shadow_trade_allowed_after_ir_ceo_only"] == "0", "paper shadow opened by IR/CEO-only gate")
        require(row["paper_shadow_blocker"] == "other_source_families_still_required", "wrong paper shadow blocker")
        require(row["missing_source_is_negative"] == "0", "missing source converted to negative in gate")
        require(row["assignment_uses_future_outcome"] == "0", "future outcome assignment flag in gate")
        require(row["outcome_used_for_assignment"] == "0", "outcome assignment flag in gate")
        if spec in l2_by_spec:
            require(row["ir_ceo_family_gate_pass"] == "1", "eligible L2 did not pass gate")
            require(row["l2_ir_ceo_semantic_id"] == l2_by_spec[spec], "gate L2 pointer mismatch")
            require(row["new_ir_ceo_extractor_state"] == "attached_asof_exhibit_99_1", "unexpected attached state")
        else:
            require(row["ir_ceo_family_gate_pass"] == "0", "source-gap row passed gate")
            require(row["l2_ir_ceo_semantic_id"] == "", "source-gap row has L2 pointer")
            require(row["new_ir_ceo_extractor_state"] == "source_gap_neutral", "unexpected source-gap state")


def validate_closeout(closeout: dict[str, str]) -> None:
    expected = {
        "aggressive_scope_rows": "116",
        "ex99_candidate_doc_rows": "396",
        "ex99_1_strict_doc_rows": "175",
        "ex99_1_loose_doc_rows": "2",
        "reference_only_doc_rows": "219",
        "ir_ceo_l2_semantic_rows": "102",
        "ir_ceo_family_gate_pass_rows": "102",
        "rejection_rows": "75",
        "paper_shadow_policy_status": "BLOCKED_OTHER_SOURCE_FAMILIES_STILL_REQUIRED",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "authority": AUTHORITY,
    }
    for key, value in expected.items():
        require(closeout.get(key) == value, f"closeout mismatch for {key}: {closeout.get(key)} != {value}")


def main() -> None:
    scope = read_csv(OUT_DIR / "task2021_aggressive_ir_ceo_scope.csv")
    docs = read_csv(OUT_DIR / "task2022_sec_8k_ex99_candidate_docs.csv")
    snippets = read_csv(OUT_DIR / "task2023_ir_ceo_statement_snippets.csv")
    l2 = read_csv(OUT_DIR / "task2024_l2_ir_ceo_semantics.csv")
    l3 = read_csv(OUT_DIR / "task2025_l3_ir_ceo_edges.csv")
    gates = read_csv(OUT_DIR / "task2026_ir_ceo_gate_delta.csv")
    rejections = read_csv(OUT_DIR / "task2027_negative_fixture_rejections.csv")
    audit = read_csv(OUT_DIR / "task2028_subagent_audit.csv")
    closeout_rows = read_csv(OUT_DIR / "task2030_closeout.csv")
    decision_rows = read_csv(DECISION)

    require(REPORT.exists(), "missing report")
    require(len(snippets) == len(docs), "snippet count must equal doc count")
    require(len(rejections) == 75, f"expected 75 rejections, got {len(rejections)}")
    require(all(row["missing_source_is_negative"] == "0" for row in rejections), "rejection converted source gap to negative")
    require(len(audit) >= 4, "missing subagent audit rows")
    require(len(closeout_rows) == 1, "expected one closeout row")
    require(decision_rows == closeout_rows, "decision CSV does not match closeout")

    validate_docs(docs)
    validate_l2_l3(docs, l2, l3)
    validate_gates(scope, l2, gates)
    validate_closeout(closeout_rows[0])

    print("[TASK2021_2030_VALIDATE_OK] source_health=pass governance_health=pass paper_shadow=blocked")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
