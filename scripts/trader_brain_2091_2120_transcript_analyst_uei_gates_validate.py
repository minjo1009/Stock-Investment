from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2091_2120_transcript_analyst_uei_gates"
RAW_OUT = ROOT / "data/raw/task_2091_2120_transcript_analyst_uei_gates"
REPORT = ROOT / "docs/reports/task_2091_2120_transcript_analyst_uei_gates/task_2091_2120_transcript_analyst_uei_gates.md"
DECISION = ROOT / "docs/reports/task_2091_2120_transcript_analyst_uei_gates/task_2091_2120_decision.csv"
TASK2001 = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
AUTHORITY = "DIAGNOSTIC_TRANSCRIPT_ANALYST_UEI_GATES_ONLY"


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


def validate_contracts(contracts: list[dict[str, str]], transcript_options: list[dict[str, str]], analyst_contracts: list[dict[str, str]]) -> None:
    require(len(contracts) == 3, f"expected 3 source gate contracts, got {len(contracts)}")
    families = {row["source_family"] for row in contracts}
    require(families == {"earnings_call_transcript", "analyst_revision_pit", "usaspending_uei_recipient_certification"}, f"bad contract families: {families}")
    for row in contracts:
        require(row["missing_source_is_negative"] == "0", "contract missing-source negative")
        require(row["authority"] == AUTHORITY, "contract authority mismatch")
    require(len(transcript_options) == 3, "expected three transcript options")
    sec_rows = [row for row in transcript_options if row["provider"] == "SEC EX-99.1 earnings release"]
    require(sec_rows and sec_rows[0]["gate_candidate"] == "0", "SEC EX-99.1 cannot be transcript gate candidate")
    require(len(analyst_contracts) == 2, "expected two analyst source contracts")
    issuer_proxy = [row for row in analyst_contracts if row["provider"] == "issuer_guidance_proxy"]
    require(issuer_proxy and issuer_proxy[0]["gate_candidate"] == "0", "issuer guidance cannot be analyst revision gate")


def validate_transcript(scope: list[dict[str, str]], l1: list[dict[str, str]], l2: list[dict[str, str]], gate: list[dict[str, str]]) -> None:
    require(len(l1) == len(scope) == 116, f"transcript L1/scope mismatch {len(l1)} {len(scope)}")
    require(len(l2) == 116, "expected 116 transcript L2 rows")
    require(len(gate) == 116, "expected 116 transcript gate rows")
    scope_specs = {row["trade_spec_id"] for row in scope}
    l1_ids = {row["transcript_l1_packet_id"] for row in l1}
    for row in l1:
        require(row["trade_spec_id"] in scope_specs, "transcript L1 outside scope")
        require(row["earnings_call_gate_pass"] == "0", "transcript gate unexpectedly passed")
        require(row["raw_transcript_path"] == "", "blocked transcript row has raw path")
        require(row["provider_event_id"] == "", "blocked transcript row has provider event id")
        require(row["provider_document_id"] == "", "blocked transcript row has provider document id")
        require(row["no_inferred_matching_used"] == "1", "transcript inferred matching flag wrong")
        require(row["missing_source_is_negative"] == "0", "transcript missing source treated negative")
        require(row["assignment_uses_future_outcome"] == "0", "transcript future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "transcript outcome assignment flag")
        require(row["authority"] == AUTHORITY, "transcript authority mismatch")
    for row in l2:
        require(row["transcript_l1_packet_id"] in l1_ids, "transcript L2 points outside L1")
        require(row["semantic_state"] == "no_certified_call_or_qa_transcript", "transcript L2 overclaims state")
        require(row["prepared_remarks_available"] == "0", "prepared remarks overclaimed")
        require(row["qa_section_available"] == "0", "Q&A overclaimed")
        require(row["speaker_mapping_available"] == "0", "speaker mapping overclaimed")
        require(row["sec_ex99_reference_is_substitute"] == "0", "SEC EX-99 treated as substitute")
    for row in gate:
        require(row["transcript_l1_packet_id"] in l1_ids, "transcript gate points outside L1")
        require(row["earnings_call_gate_pass"] == "0", "earnings call gate opened")
        require(row["gate_verdict"] == "BLOCKED_TRANSCRIPT_SOURCE_GAP", "bad transcript gate verdict")
        require(row["blocker"] == "certified_earnings_call_transcript_raw_missing", "bad transcript blocker")


def validate_analyst(scope: list[dict[str, str]], l1: list[dict[str, str]], gate: list[dict[str, str]]) -> None:
    require(len(l1) == len(scope) == 116, "analyst L1/scope mismatch")
    require(len(gate) == 116, "expected 116 analyst gate rows")
    scope_specs = {row["trade_spec_id"] for row in scope}
    l1_ids = {row["analyst_revision_l1_packet_id"] for row in l1}
    for row in l1:
        require(row["trade_spec_id"] in scope_specs, "analyst L1 outside scope")
        require(row["analyst_revision_pit_gate_pass"] == "0", "analyst PIT gate unexpectedly passed")
        require(row["raw_revision_path"] == "", "blocked analyst row has raw path")
        require(row["revision_timestamp"] == "", "blocked analyst row has revision timestamp")
        require(row["provider_available_ts"] == "", "blocked analyst row has availability timestamp")
        require(row["pit_revision_source_state"] == "blocked_missing_certified_pit_revision_feed", "bad analyst source state")
        require(row["missing_source_is_negative"] == "0", "analyst missing source negative")
        require(row["assignment_uses_future_outcome"] == "0", "analyst future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "analyst outcome assignment flag")
    for row in gate:
        require(row["analyst_revision_l1_packet_id"] in l1_ids, "analyst gate points outside L1")
        require(row["analyst_revision_pit_gate_pass"] == "0", "analyst gate opened")
        require(row["gate_verdict"] == "BLOCKED_ANALYST_PIT_SOURCE_GAP", "bad analyst gate verdict")
        require(row["blocker"] == "certified_historical_pit_analyst_revision_raw_missing", "bad analyst blocker")


def validate_usaspending(details: list[dict[str, str]], identity: list[dict[str, str]], l2: list[dict[str, str]], l3: list[dict[str, str]]) -> None:
    require(len(details) == 9, f"expected 9 award detail rows, got {len(details)}")
    detail_ids = {row["award_id"] for row in details}
    for row in details:
        require(row["download_status"] in {"downloaded", "reused", "http_error", "failed"}, "bad award detail status")
        require(row["assignment_uses_future_outcome"] == "0", "award detail future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "award detail outcome flag")
        require(row["authority"] == AUTHORITY, "award detail authority mismatch")
        if row["download_status"] in {"downloaded", "reused"}:
            raw = ROOT / row["raw_detail_path"]
            require(raw.exists(), f"missing award detail raw: {raw}")
            require(file_sha256(raw) == row["raw_detail_sha256"], "award detail hash mismatch")
            require(row["source_url"].startswith("https://api.usaspending.gov/api/v2/awards/"), "bad award detail URL")
            require(row["recipient_name_detail"] != "", "award detail missing recipient name")
    require(len(identity) == 9, "expected 9 identity rows")
    identity_ids = {row["usaspending_identity_map_id"] for row in identity}
    pass_rows = [row for row in identity if row["certified_identity_mapping_pass"] == "1"]
    require(len(pass_rows) >= 1, "expected at least one official UEI/hash identity mapping pass")
    for row in identity:
        require(row["award_id"] in detail_ids, "identity row without detail")
        require(row["company_name_only_match"] == "1", "identity row should acknowledge company-name search basis")
        require(row["l5_historical_certified_recipient_identity_gate_pass"] == "0", "historical L5 recipient gate opened")
        require(row["historical_gate_blocker"] == "award_detail_captured_current_time_not_proven_available_before_decision_asof", "bad historical gate blocker")
        require(row["missing_source_is_negative"] == "0", "identity missing source negative")
        require(row["assignment_uses_future_outcome"] == "0", "identity future assignment flag")
        require(row["outcome_used_for_assignment"] == "0", "identity outcome flag")
        if row["certified_identity_mapping_pass"] == "1":
            require(row["recipient_uei_or_exact_entity_id"] != "", "identity pass missing recipient id")
            require(row["raw_detail_path"] != "", "identity pass missing raw detail")
            require((ROOT / row["raw_detail_path"]).exists(), "identity raw detail missing")
            require(row["strict_query_token_match"] == "1", "identity pass without strict query token match")
            require(row["exact_legal_name_match"] == "1" or row["parent_exact_legal_name_match"] == "1", "identity pass without exact legal name")
    l2_ids = {row["usaspending_certified_l2_id"] for row in l2}
    require(len(l2) == len(pass_rows), "certified L2 rows should equal identity pass rows")
    require(len(l3) == len(pass_rows), "certified L3 rows should equal identity pass rows")
    for row in l2:
        require(row["usaspending_identity_map_id"] in identity_ids, "certified L2 points outside identity")
        require(row["semantic_state"] == "recipient_identity_certified_but_historical_l5_blocked", "certified L2 overclaims")
        require(row["l5_historical_certified_recipient_identity_gate_pass"] == "0", "certified L2 opened L5")
        require(row["blocker"] == "no_pre_decision_award_receipt_timestamp", "certified L2 blocker mismatch")
    for row in l3:
        require(row["from_usaspending_certified_l2_id"] in l2_ids, "certified L3 points outside L2")
        require(row["relation_type"] == "recipient_identity_certifies_award_entity_but_not_historical_l5_timing", "certified L3 relation overclaims")
        require(row["l5_historical_certified_recipient_identity_gate_pass"] == "0", "certified L3 opened L5")


def validate_full_gate(scope: list[dict[str, str]], full_gate: list[dict[str, str]]) -> None:
    require(len(full_gate) == len(scope) == 116, "full gate/scope mismatch")
    scope_specs = {row["trade_spec_id"] for row in scope}
    for row in full_gate:
        require(row["trade_spec_id"] in scope_specs, "full gate outside scope")
        require(row["authority"] == AUTHORITY, "full gate authority mismatch")
        require(row["earnings_call_gate_pass"] == "0", "full gate transcript opened")
        require(row["analyst_revision_pit_gate_pass"] == "0", "full gate analyst opened")
        require(row["certified_recipient_identity_gate_pass"] == "0", "full gate historical recipient opened")
        require(row["full_source_extractor_gate_pass"] == "0", "full source gate opened")
        require(row["paper_shadow_trade_allowed"] == "0", "paper shadow opened")
        require(row["real_capital_trade_allowed"] == "0", "real capital opened")
        require("earnings_call_transcript_source_gap" in row["blocker"], "full gate missing transcript blocker")
        require("analyst_revision_pit_source_gap" in row["blocker"], "full gate missing analyst blocker")
        require(row["missing_source_is_negative"] == "0", "full gate missing source negative")
        require(row["assignment_uses_future_outcome"] == "0", "full gate future assignment")
        require(row["outcome_used_for_assignment"] == "0", "full gate outcome assignment")


def validate_closeout(closeout: dict[str, str], detail_count: int, identity_pass_count: int, certified_l2_count: int) -> None:
    expected = {
        "verdict": "transcript_analyst_uei_gate_hardening_complete_diagnostic_only",
        "aggressive_scope_rows": "116",
        "transcript_gate_pass_rows": "0",
        "analyst_pit_gate_pass_rows": "0",
        "usaspending_award_detail_rows": str(detail_count),
        "usaspending_identity_mapping_pass_rows": str(identity_pass_count),
        "usaspending_l5_historical_gate_pass_rows": "0",
        "usaspending_certified_l2_rows": str(certified_l2_count),
        "full_source_extractor_gate_pass_rows": "0",
        "paper_shadow_policy_status": "BLOCKED_UNTIL_TRANSCRIPT_ANALYST_AND_HISTORICAL_RECIPIENT_GATES_PASS",
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
    contracts = read_csv(OUT_DIR / "task2091_source_gate_contract.csv")
    transcript_options = read_csv(OUT_DIR / "task2092_transcript_source_option_audit.csv")
    transcript_l1 = read_csv(OUT_DIR / "task2093_transcript_l1_packets.csv")
    transcript_l2 = read_csv(OUT_DIR / "task2094_transcript_l2_semantics.csv")
    transcript_gate = read_csv(OUT_DIR / "task2095_transcript_gate_panel.csv")
    analyst_contracts = read_csv(OUT_DIR / "task2096_analyst_source_contract.csv")
    analyst_l1 = read_csv(OUT_DIR / "task2097_analyst_revision_l1_packets.csv")
    analyst_gate = read_csv(OUT_DIR / "task2098_analyst_revision_gate_panel.csv")
    details = read_csv(OUT_DIR / "task2099_usaspending_award_detail_downloads.csv")
    identity = read_csv(OUT_DIR / "task2100_usaspending_recipient_identity_map.csv")
    certified_l2 = read_csv(OUT_DIR / "task2101_usaspending_certified_l2_semantics.csv")
    certified_l3 = read_csv(OUT_DIR / "task2102_usaspending_certified_l3_edges.csv")
    full_gate = read_csv(OUT_DIR / "task2103_integrated_full_source_gate.csv")
    audits = read_csv(OUT_DIR / "task2104_expert_audit.csv")
    closeout = read_csv(OUT_DIR / "task2120_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(len(audits) == 4, "expected 4 expert audit rows")
    require(len(closeout) == 1, "expected one closeout row")
    require(decision == closeout, "decision CSV differs from closeout")
    require(len(manifest) >= 15, "manifest missing artifacts")

    validate_contracts(contracts, transcript_options, analyst_contracts)
    validate_transcript(scope, transcript_l1, transcript_l2, transcript_gate)
    validate_analyst(scope, analyst_l1, analyst_gate)
    validate_usaspending(details, identity, certified_l2, certified_l3)
    validate_full_gate(scope, full_gate)
    validate_closeout(
        closeout[0],
        len(details),
        sum(1 for row in identity if row["certified_identity_mapping_pass"] == "1"),
        len(certified_l2),
    )

    print("[TASK2091_2120_VALIDATE_OK] source_health=pass governance_health=pass paper_shadow=blocked")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
