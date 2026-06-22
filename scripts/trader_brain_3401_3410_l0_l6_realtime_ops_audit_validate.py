from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs" / "reports" / "task_3401_3410_l0_l6_realtime_ops_audit"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_3401_3410_l0_l6_realtime_ops_audit"


def _read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    report = _read(REPORT_DIR / "task_3401_3410_l0_l6_realtime_ops_audit.md")
    decision_rows = _rows(REPORT_DIR / "task_3410_decision.csv")
    gap_rows = _rows(ARTIFACT_DIR / "l0_l6_gap_audit.csv")
    cadence_rows = _rows(ARTIFACT_DIR / "realtime_cadence_recommendation.csv")
    manifest_rows = _rows(ARTIFACT_DIR / "artifact_manifest.csv")

    required_report_phrases = [
        "event_driven_plus_10_min_intraday_heartbeat_diagnostic_only",
        "NOT_ACCEPTED",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "FORBIDDEN",
        "Do not run the full trading brain every 5 minutes.",
        "No trading code, selector, sizing, replay, paper order, broker mutation, or live order path changed.",
    ]
    for phrase in required_report_phrases:
        if phrase not in report:
            raise AssertionError(f"report missing phrase: {phrase}")

    if len(decision_rows) != 1:
        raise AssertionError("decision CSV must contain exactly one row")
    decision = decision_rows[0]
    if decision["default_cadence"] != "10_min_changed_candidate_brain_heartbeat":
        raise AssertionError("default cadence must be the 10-minute changed-candidate brain heartbeat")
    if decision["strategy"] != "NOT_ACCEPTED" or decision["deployment"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        raise AssertionError("decision status boundaries changed")
    if decision["real_capital"] != "FORBIDDEN":
        raise AssertionError("real capital boundary changed")

    expected_layers = {"L0_L1", "L0", "L2", "L3", "L4", "L5", "L6", "cross_cutting"}
    actual_layers = {row["layer"] for row in gap_rows}
    if actual_layers != expected_layers:
        raise AssertionError(f"gap audit layers mismatch: {sorted(actual_layers)}")

    cadence_by_name = {row["cadence"]: row for row in cadence_rows}
    if cadence_by_name["10_min"]["recommendation"] != "default":
        raise AssertionError("10-minute cadence must be default")
    if "full L0-L6 recompute" not in cadence_by_name["5_min"]["forbidden_now"]:
        raise AssertionError("5-minute cadence must forbid full L0-L6 recompute")
    if len(manifest_rows) != 4:
        raise AssertionError("artifact manifest row count changed")

    llm_readme = _read(ROOT / "docs" / "llm_wiki" / "README.md")
    llm_ops = _read(ROOT / "docs" / "llm_wiki" / "realtime_trading_operations.md")
    llm_index = _read(ROOT / "docs" / "llm_wiki" / "task_artifact_index.md")
    obsidian_home = _read(ROOT / "docs" / "obsidian" / "Vault Home.md")
    operating_state = _read(ROOT / "docs" / "operating_system" / "project_operating_state.md")
    registry = _read(ROOT / "tasks" / "task_registry.csv")

    required_navigation_phrases = [
        "Task3401-Task3410",
        "event-driven plus 10-minute",
        "realtime_trading_operations.md",
    ]
    combined_navigation = "\n".join([llm_readme, llm_ops, llm_index, obsidian_home, operating_state, registry])
    for phrase in required_navigation_phrases:
        if phrase not in combined_navigation:
            raise AssertionError(f"navigation missing phrase: {phrase}")

    for task_id in ["Task3401", "Task3410"]:
        if task_id not in registry:
            raise AssertionError(f"registry missing {task_id}")

    print("[TASK3401_3410_OK] L0-L6 realtime ops audit, cadence recommendation, wiki navigation, and registry checks passed")


if __name__ == "__main__":
    main()
