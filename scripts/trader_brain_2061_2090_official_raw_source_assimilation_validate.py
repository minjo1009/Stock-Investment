from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2061_2090_official_raw_source_assimilation"
TASK2001 = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
TASK2021 = ROOT / "data/artifacts/task_2021_2030_sec_8k_ex99_ir_ceo_extractor"
TASK2031 = ROOT / "data/artifacts/task_2031_2060_free_official_source_layers"
REPORT = ROOT / "docs/reports/task_2061_2090_official_raw_source_assimilation/task_2061_2090_official_raw_source_assimilation.md"
DECISION = ROOT / "docs/reports/task_2061_2090_official_raw_source_assimilation/task_2061_2090_decision.csv"
AUTHORITY = "DIAGNOSTIC_OFFICIAL_RAW_SOURCE_ASSIMILATION_ONLY"


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


def validate_govinfo(downloads: list[dict[str, str]], l1: list[dict[str, str]], l2: list[dict[str, str]], l3: list[dict[str, str]]) -> None:
    require(len(downloads) == 51, f"expected 51 GovInfo downloads, got {len(downloads)}")
    for row in downloads:
        require(row["authority"] == AUTHORITY, "GovInfo download authority mismatch")
        require(row["official_pdf_url"].startswith("https://www.govinfo.gov/content/pkg/FR-"), "non-GovInfo PDF URL")
        require(row["download_status"] in {"downloaded", "reused"}, "GovInfo PDF not downloaded")
        path = ROOT / row["raw_pdf_path"]
        require(path.exists(), f"missing GovInfo PDF: {path}")
        require(len(row["raw_pdf_sha256"]) == 64, "GovInfo hash not sha256-like")
        require(file_sha256(path) == row["raw_pdf_sha256"], "GovInfo PDF hash mismatch")
        require(row["error"] == "", "GovInfo success row has error text")
        require(row["assignment_uses_future_outcome"] == "0", "GovInfo future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "GovInfo outcome assignment flag")
    require(len(l1) == 171, f"expected 171 GovInfo L1 rows, got {len(l1)}")
    for row in l1:
        require(row["raw_govinfo_source_attached"] == "1", "GovInfo L1 missing raw attach")
        require(row["asof_guard_pass"] == "1", "GovInfo L1 as-of failed")
        require(parse_ts(row["available_to_brain_ts"]) <= parse_ts(row["decision_asof_ts"]), "GovInfo future source")
        require(row["inferred_matching_used"] == "0", "GovInfo inferred matching")
        require(row["missing_source_is_negative"] == "0", "GovInfo missing source negative")
        require(row["assignment_uses_future_outcome"] == "0", "GovInfo L1 future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "GovInfo L1 outcome assignment flag")
    l1_ids = {row["govinfo_policy_l1_packet_id"] for row in l1}
    require(len(l2) == 57, f"expected 57 GovInfo L2 rows, got {len(l2)}")
    require(len(l3) == 57, f"expected 57 GovInfo L3 rows, got {len(l3)}")
    l2_ids = {row["govinfo_policy_l2_semantic_id"] for row in l2}
    for row in l2:
        require(row["govinfo_policy_l1_packet_id"] in l1_ids, "GovInfo L2 points outside L1")
        require(row["policy_raw_depth_state"] == "federal_register_plus_govinfo_pdf_raw", "GovInfo wrong raw depth state")
        require(row["asof_guard_pass"] == "1", "GovInfo L2 as-of failed")
        require(row["missing_source_is_negative"] == "0", "GovInfo L2 missing negative")
    for row in l3:
        require(row["from_govinfo_policy_l2_semantic_id"] in l2_ids, "GovInfo L3 points outside L2")
        require(row["relation_type"] == "source_depth_confirms_policy_layer", "GovInfo L3 overclaims relation")


def validate_usaspending(queries: list[dict[str, str]], awards: list[dict[str, str]], l2: list[dict[str, str]], l3: list[dict[str, str]]) -> None:
    require(len(queries) == 16, f"expected 16 USAspending queries, got {len(queries)}")
    for row in queries:
        require(row["authority"] == AUTHORITY, "USAspending query authority mismatch")
        require(row["assignment_uses_future_outcome"] == "0", "USAspending query future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "USAspending query outcome assignment flag")
        if row["raw_response_path"]:
            path = ROOT / row["raw_response_path"]
            require(path.exists(), f"missing USAspending raw response: {path}")
            require(file_sha256(path) == row["raw_response_sha256"], "USAspending raw hash mismatch")
    require(len(awards) == 9, f"expected 9 USAspending award rows, got {len(awards)}")
    for row in awards:
        require(row["historical_assignment_allowed"] == "0", "USAspending award allowed historical assignment")
        require(row["authority"] == AUTHORITY, "USAspending award authority mismatch")
        require(row["assignment_uses_future_outcome"] == "0", "USAspending award future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "USAspending award outcome assignment flag")
        require(row["raw_response_path"], "USAspending award missing raw response path")
        require((ROOT / row["raw_response_path"]).exists(), "USAspending award raw response missing")
    require(len(l2) == 3, f"expected 3 USAspending L2 rows, got {len(l2)}")
    require(len(l3) == 3, f"expected 3 USAspending L3 rows, got {len(l3)}")
    l2_ids = {row["usaspending_l2_semantic_id"] for row in l2}
    for row in l2:
        require(row["semantic_state"] == "official_federal_contract_award_context_shadow_only", "USAspending L2 overclaims")
        require(row["historical_assignment_allowed"] == "0", "USAspending L2 allowed historical assignment")
        require(row["independent_customer_confirmation_gate_pass"] == "0", "USAspending L2 opened customer gate")
        require(row["missing_source_is_negative"] == "0", "USAspending L2 missing negative")
    for row in l3:
        require(row["from_usaspending_l2_semantic_id"] in l2_ids, "USAspending L3 points outside L2")
        require(row["historical_assignment_allowed"] == "0", "USAspending L3 allowed historical assignment")
        require(row["relation_type"] == "shadow_official_customer_award_context", "USAspending L3 overclaims relation")


def validate_counterparty(downloads: list[dict[str, str]], l1: list[dict[str, str]], l2: list[dict[str, str]], l3: list[dict[str, str]]) -> None:
    require(len(downloads) == 7, f"expected 7 counterparty downloads, got {len(downloads)}")
    for row in downloads:
        require(row["authority"] == AUTHORITY, "counterparty download authority mismatch")
        require(row["download_status"] in {"downloaded", "reused", "http_error", "failed"}, "unexpected counterparty download status")
        if row["download_status"] in {"downloaded", "reused"}:
            path = ROOT / row["raw_source_path"]
            require(path.exists(), f"missing counterparty raw source: {path}")
            require(file_sha256(path) == row["raw_source_sha256"], "counterparty raw hash mismatch")
            require(row["error"] == "", "counterparty success row has error text")
        require(row["assignment_uses_future_outcome"] == "0", "counterparty future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "counterparty outcome assignment flag")
    require(len(l1) == 46, f"expected 46 independent customer L1 rows, got {len(l1)}")
    pass_rows = [row for row in l1 if row["independent_customer_confirmation_gate_pass"] == "1"]
    require(len(pass_rows) == 10, f"expected 10 independent customer pass rows, got {len(pass_rows)}")
    for row in l1:
        require(row["missing_source_is_negative"] == "0", "independent customer L1 missing negative")
        require(row["assignment_uses_future_outcome"] == "0", "independent customer L1 future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "independent customer L1 outcome assignment flag")
        if row["independent_customer_confirmation_gate_pass"] == "1":
            require(row["asof_guard_pass"] == "1", "independent customer pass without as-of")
            require(row["beneficiary_chain_match_pass"] == "1", "independent customer pass without chain match")
            require(row["independent_counterparty_source"] == "1", "independent customer pass from issuer source")
            require(parse_ts(row["available_to_brain_ts"]) <= parse_ts(row["decision_asof_ts"]), "independent customer future source")
            require(row["blocker"] == "none", "independent customer pass has blocker")
        else:
            require(row["missing_source_is_negative"] == "0", "independent customer failed row negative")
    l1_ids = {row["independent_customer_l1_packet_id"] for row in l1}
    require(len(l2) == 10, f"expected 10 independent customer L2 rows, got {len(l2)}")
    require(len(l3) == 10, f"expected 10 independent customer L3 rows, got {len(l3)}")
    l2_ids = {row["independent_customer_l2_semantic_id"] for row in l2}
    for row in l2:
        require(row["independent_customer_l1_packet_id"] in l1_ids, "independent customer L2 points outside L1")
        require(row["semantic_state"] == "independent_counterparty_confirmation_attached", "independent customer L2 wrong state")
        require(row["asof_guard_pass"] == "1", "independent customer L2 as-of failed")
        require(row["missing_source_is_negative"] == "0", "independent customer L2 missing negative")
    for row in l3:
        require(row["from_independent_customer_l2_semantic_id"] in l2_ids, "independent customer L3 points outside L2")
        require(row["relation_type"] == "independent_customer_confirmation", "independent customer L3 wrong relation")
        require(row["asof_guard_pass"] == "1", "independent customer L3 as-of failed")


def validate_full_gate(scope: list[dict[str, str]], full_gate: list[dict[str, str]]) -> None:
    require(len(scope) == 116, f"expected 116 scope rows, got {len(scope)}")
    require(len(full_gate) == 116, f"expected 116 full gate rows, got {len(full_gate)}")
    scope_specs = {row["trade_spec_id"] for row in scope}
    for row in full_gate:
        require(row["trade_spec_id"] in scope_specs, "full gate row outside scope")
        require(row["govinfo_policy_raw_gate_pass"] in {"0", "1"}, "bad GovInfo raw gate")
        require(row["strict_customer_entity_match_pass"] == "0", "USAspending name match treated as certified")
        require(row["certified_recipient_identity_gate_pass"] == "0", "certified recipient identity unexpectedly passed")
        require(row["full_source_extractor_gate_pass"] == "0", "full source gate unexpectedly passed")
        require(row["paper_shadow_trade_allowed"] == "0", "paper shadow opened")
        require(row["real_capital_trade_allowed"] == "0", "real capital opened")
        require(row["blocker"] != "none", "blocked full gate row missing blocker")
        require(row["missing_source_is_negative"] == "0", "full gate missing negative")
        require(row["assignment_uses_future_outcome"] == "0", "full gate future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "full gate outcome assignment flag")


def validate_closeout(closeout: dict[str, str]) -> None:
    expected = {
        "verdict": "official_raw_source_assimilation_complete_diagnostic_only",
        "loop_count": "3",
        "aggressive_scope_rows": "116",
        "govinfo_pdf_download_rows": "51",
        "govinfo_pdf_success_rows": "51",
        "govinfo_policy_l2_trade_rows": "57",
        "usaspending_query_rows": "16",
        "usaspending_award_rows": "9",
        "usaspending_shadow_l2_symbol_rows": "3",
        "counterparty_source_download_rows": "7",
        "independent_customer_l2_trade_rows": "10",
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
    contracts = read_csv(OUT_DIR / "task2061_three_loop_contract.csv")
    govinfo_downloads = read_csv(OUT_DIR / "task2062_govinfo_pdf_download_ledger.csv")
    govinfo_l1 = read_csv(OUT_DIR / "task2063_govinfo_policy_l1_packets.csv")
    govinfo_l2 = read_csv(OUT_DIR / "task2064_govinfo_policy_l2_semantics.csv")
    govinfo_l3 = read_csv(OUT_DIR / "task2065_govinfo_policy_l3_edges.csv")
    usaspending_queries = read_csv(OUT_DIR / "task2071_usaspending_query_ledger.csv")
    usaspending_awards = read_csv(OUT_DIR / "task2072_usaspending_award_l1_packets.csv")
    usaspending_l2 = read_csv(OUT_DIR / "task2073_usaspending_l2_semantics.csv")
    usaspending_l3 = read_csv(OUT_DIR / "task2074_usaspending_l3_edges.csv")
    counterparty_downloads = read_csv(OUT_DIR / "task2081_counterparty_source_downloads.csv")
    independent_l1 = read_csv(OUT_DIR / "task2082_independent_customer_l1_packets.csv")
    independent_l2 = read_csv(OUT_DIR / "task2083_independent_customer_l2_semantics.csv")
    independent_l3 = read_csv(OUT_DIR / "task2084_independent_customer_l3_edges.csv")
    full_gate = read_csv(OUT_DIR / "task2086_integrated_full_source_gate.csv")
    audits = read_csv(OUT_DIR / "task2087_three_loop_audit.csv")
    closeout = read_csv(OUT_DIR / "task2090_closeout.csv")
    decision = read_csv(DECISION)

    require(REPORT.exists(), "missing report")
    require(len(contracts) == 3, "expected three loop contracts")
    require(len(audits) == 3, "expected three audit rows")
    require(len(closeout) == 1, "expected one closeout row")
    require(decision == closeout, "decision CSV differs from closeout")
    validate_govinfo(govinfo_downloads, govinfo_l1, govinfo_l2, govinfo_l3)
    validate_usaspending(usaspending_queries, usaspending_awards, usaspending_l2, usaspending_l3)
    validate_counterparty(counterparty_downloads, independent_l1, independent_l2, independent_l3)
    validate_full_gate(scope, full_gate)
    validate_closeout(closeout[0])

    print("[TASK2061_2090_VALIDATE_OK] source_health=pass governance_health=pass paper_shadow=blocked")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
