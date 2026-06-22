from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1181_1190_l0_l3_strengthening_plan"
REPORT = ROOT / "docs/reports/task_1181_1190_l0_l3_strengthening_plan"

REQUIRED_FILES = [
    "task1181_source_catalog.csv",
    "task1181_download_ledger.csv",
    "task1182_project_context_packet.csv",
    "task1183_expert_roster.csv",
    "task1184_l0_l3_gap_matrix.csv",
    "task1185_l0_l3_strengthening_plan.csv",
    "task1186_subagent_packet_index.csv",
    "task1190_l0_l3_plan_closeout.csv",
    "task1190_l0_l3_plan_closeout.json",
    "artifact_manifest.csv",
]


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if not (REPORT / "task_1181_1190_l0_l3_strengthening_plan.md").exists():
        errors.append("missing report md")
    if not (REPORT / "task_1181_1190_decision.csv").exists():
        errors.append("missing decision csv")
    if not (REPORT / "expert_packets").exists():
        errors.append("missing expert packet directory")
    if errors:
        return errors

    catalog = rows("task1181_source_catalog.csv")
    downloads = rows("task1181_download_ledger.csv")
    context = rows("task1182_project_context_packet.csv")
    experts = rows("task1183_expert_roster.csv")
    gaps = rows("task1184_l0_l3_gap_matrix.csv")
    plan = rows("task1185_l0_l3_strengthening_plan.csv")
    packets = rows("task1186_subagent_packet_index.csv")
    closeout = rows("task1190_l0_l3_plan_closeout.csv")
    closeout_json = json.loads((ART / "task1190_l0_l3_plan_closeout.json").read_text(encoding="utf-8"))

    if len(catalog) != 18:
        errors.append("source catalog must contain 18 rows")
    if len(downloads) != len(catalog):
        errors.append("download ledger must match source catalog")
    downloaded = [row for row in downloads if row["download_status"] in {"downloaded", "already_downloaded"}]
    if len(downloaded) < 15:
        errors.append("must download at least 15 context sources")
    if not any(row["domain"] == "semiconductor/policy" for row in catalog):
        errors.append("semiconductor policy context missing")
    if not any(row["domain"] == "power_grid/ai" for row in catalog):
        errors.append("power grid AI context missing")
    if not any(row["domain"] == "policy" for row in catalog):
        errors.append("policy source context missing")

    if len(context) < 3:
        errors.append("project context packet must describe current state")
    if not any("Task1171-1180" in row["current_state"] for row in context):
        errors.append("context packet must include latest broad-universe failure")

    if len(experts) != 14:
        errors.append("expert roster must contain 14 roles")
    if len(packets) != len(experts):
        errors.append("subagent packet index must match expert roster")
    packet_files = list((REPORT / "expert_packets").glob("*.md"))
    if len(packet_files) != len(experts):
        errors.append("expert packet markdown file count must match expert roster")

    if len(gaps) != 10:
        errors.append("gap matrix must contain 10 gaps")
    if not {"L0", "L1", "L2", "L3"}.issubset({row["layer"] for row in gaps}):
        errors.append("gap matrix must cover L0 L1 L2 and L3")

    if len(plan) != 10:
        errors.append("strengthening plan must contain Task1191 through Task1200")
    expected_tasks = {f"Task{idx}" for idx in range(1191, 1201)}
    if {row["task_id"] for row in plan} != expected_tasks:
        errors.append("strengthening plan task ids must be Task1191 through Task1200")
    if any(row["status"] != "planned" for row in plan):
        errors.append("next tasks must be planned only")

    if len(closeout) != 1:
        errors.append("closeout must have one row")
    else:
        row = closeout[0]
        if row["replay_executed"] != "0" or row["selection_promoted"] != "0":
            errors.append("plan task must not execute replay or promote selection")
        if row["strategy_acceptance"] != "NOT_ACCEPTED":
            errors.append("strategy acceptance changed")
        if row["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("deployment readiness changed")
        if row["real_capital"] != "FORBIDDEN":
            errors.append("real capital changed")

    if closeout_json.get("planned_next_tasks") != 10:
        errors.append("json closeout must record 10 planned next tasks")
    if closeout_json.get("replay_executed") != "0":
        errors.append("json closeout must record no replay")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("[TRADER_BRAIN_1181_1190_L0_L3_STRENGTHENING_PLAN_FAIL]")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[TRADER_BRAIN_1181_1190_L0_L3_STRENGTHENING_PLAN_OK] artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
