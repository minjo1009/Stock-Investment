from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors"
REPORT = ROOT / "docs/reports/task_1318_1337_full_candidate_source_extractors/task_1318_1337_full_candidate_source_extractors.md"
AUTHORITY = "DIAGNOSTIC_FULL_CANDIDATE_SOURCE_EXTRACTORS_ONLY"

REQUIRED_FILES = {
    "task1318_full_candidate_source_schema.csv": 6,
    "task1319_full_candidate_source_plan.csv": 3100,
    "task1320_candidate_filing_bindings.csv": 3100,
    "task1321_sec_complete_submission_download_ledger.csv": 1,
    "task1322_sec_exhibit_document_index.csv": 1,
    "task1323_accession_source_evidence.csv": 1,
    "task1324_candidate_l1_source_bindings.csv": 3100,
    "task1325_candidate_l2_interpretation.csv": 3100,
    "task1326_candidate_l3_evidence_edges.csv": 18600,
    "task1327_full_candidate_readiness_panel.csv": 3100,
    "task1328_remaining_source_gap_ledger.csv": 3,
    "task1329_candidate_replacement_readiness_gate.csv": 1,
    "task1330_task_plan.csv": 20,
    "task1337_closeout.csv": 1,
    "artifact_manifest.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_files() -> None:
    for name, minimum_rows in REQUIRED_FILES.items():
        path = OUT_DIR / name
        require(path.exists(), f"missing artifact: {name}")
        rows = read_csv(path)
        require(len(rows) >= minimum_rows, f"{name} row count {len(rows)} < {minimum_rows}")


def validate_candidate_contract() -> None:
    plan = read_csv(OUT_DIR / "task1319_full_candidate_source_plan.csv")
    l1 = read_csv(OUT_DIR / "task1324_candidate_l1_source_bindings.csv")
    l2 = read_csv(OUT_DIR / "task1325_candidate_l2_interpretation.csv")
    l3 = read_csv(OUT_DIR / "task1326_candidate_l3_evidence_edges.csv")
    readiness = read_csv(OUT_DIR / "task1327_full_candidate_readiness_panel.csv")
    plan_ids = {row["candidate_source_id"] for row in plan}
    require(len(plan_ids) == 3100, "candidate_source_id count must be 3100")
    for rows, name in [(l1, "l1"), (l2, "l2"), (readiness, "readiness")]:
        ids = {row["candidate_source_id"] for row in rows}
        require(ids == plan_ids, f"{name} candidate ids do not match plan")
    edge_counts: dict[str, int] = {}
    for row in l3:
        edge_counts[row["candidate_source_id"]] = edge_counts.get(row["candidate_source_id"], 0) + 1
        require(row["assignment_uses_future_outcome"] == "0", "future assignment flag in l3")
        require(row["selection_use_allowed"] == "0", "l3 selection promoted")
        require(row["replay_use_allowed"] == "0", "l3 replay promoted")
        require(row["authority"] == AUTHORITY, "bad l3 authority")
    require(set(edge_counts) == plan_ids, "l3 candidates missing")
    require(all(count == 6 for count in edge_counts.values()), "each candidate must have 6 L3 source-family edges")


def validate_download_and_readiness_gate() -> None:
    downloads = read_csv(OUT_DIR / "task1321_sec_complete_submission_download_ledger.csv")
    require(all(row["download_status"] in {"downloaded", "cached", "reused_task1268_cache"} for row in downloads), "download failure present")
    gate = read_csv(OUT_DIR / "task1329_candidate_replacement_readiness_gate.csv")[0]
    require(gate["candidate_rows"] == "3100", "gate candidate row count mismatch")
    require(gate["l2_rows"] == "3100", "gate l2 row count mismatch")
    require(gate["ready_for_candidate_replacement_preregistration"] == "1", "candidate replacement prereg gate not open")
    require(gate["replay_executed"] == "0", "replay should not execute")
    require(gate["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
    require(gate["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment readiness changed")
    require(gate["real_capital"] == "FORBIDDEN", "real capital changed")


def validate_report_footer() -> None:
    text = REPORT.read_text(encoding="utf-8")
    require("Test results do not modify strategy acceptance status." in text, "missing validation authority footer")
    require("Strategy: NOT_ACCEPTED" in text, "missing strategy footer")
    require("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" in text, "missing deployment footer")
    require("Real Capital: FORBIDDEN" in text, "missing real-capital footer")


def main() -> None:
    validate_files()
    validate_candidate_contract()
    validate_download_and_readiness_gate()
    validate_report_footer()
    print("[PASS] Task1318-1337 full candidate source extractor validation")


if __name__ == "__main__":
    main()
