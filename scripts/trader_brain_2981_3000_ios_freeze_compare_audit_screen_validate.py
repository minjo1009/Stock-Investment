from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2981_3000_ios_freeze_compare_audit_screen"
ARTIFACT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID


def fail(message: str) -> None:
    raise SystemExit(f"[TASK2981_3000_VALIDATE_FAIL] {message}")


def require(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path}")
    return path.read_text(encoding="utf-8")


def require_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        fail(f"missing {path}")
    frame = pd.read_csv(path, dtype=str).fillna("")
    if frame.empty:
        fail(f"empty {path}")
    return frame


def main() -> None:
    types = require(ROOT / "apps/ios-trader-brain/src/types/cockpit.ts")
    data = require(ROOT / "apps/ios-trader-brain/src/lib/cockpit-data.ts")
    fixture = require(ROOT / "apps/ios-trader-brain/src/fixtures/cockpit-fixture.ts")
    risk = require(ROOT / "apps/ios-trader-brain/src/app/(tabs)/risk.tsx")
    catalog = require(ROOT / "scripts/build_trader_terminal_catalog.py")
    report = require(REPORT_DIR / f"{TASK_ID}.md")
    opstate = require(ROOT / "docs/operating_system/project_operating_state.md")

    for token in ["PolicyCompareAudit", "policyCompare?: PolicyCompareAudit", "PolicyCompareGate", "PolicyCompareBlocker"]:
        if token not in types:
            fail(f"types missing {token}")

    for token in ["normalizePolicyCompare", "policy_compare_audit", "runtime.policy_compare_audit", "v2.policy_compare_audit"]:
        if token not in data:
            fail(f"normalizer missing {token}")

    for token in ["policyCompare", "strict raw/as-of source gate", "NO_REPLAY_UNTIL_BLOCKER_POLICY_DEFINED"]:
        if token not in fixture:
            fail(f"fixture missing {token}")

    for token in ["L4 비교 감사", "Replay 결정", "Freeze 원장", "성과 비교 전 게이트", "Split / OOS 계획"]:
        if token not in risk:
            fail(f"risk screen missing visible section {token}")

    for token in ["policy_compare_audit.json", "policy_compare_same_experiment_gate.csv", "_policy_compare_audit_payload"]:
        if token not in catalog:
            fail(f"catalog builder missing {token}")

    forbidden_patterns = [
        r"\bsubmitOrder\b",
        r"\bplaceOrder\b",
        r"\bsendLiveOrder\b",
        r"\bcreateOrder\b",
        r"\brealOrdersAllowed:\s*true\b",
        r"\bliveOrderButtonsAllowed:\s*true\b",
    ]
    app_sources = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in (ROOT / "apps/ios-trader-brain/src").rglob("*.ts*"))
    for pattern in forbidden_patterns:
        if re.search(pattern, app_sources):
            fail(f"forbidden order mutation pattern found: {pattern}")

    closeout = require_csv(ARTIFACT_DIR / "task3000_closeout.csv").iloc[0].to_dict()
    if closeout.get("strict_asof_status") != "BLOCKED":
        fail("strict_asof_status must remain BLOCKED")
    if closeout.get("performance_compare_allowed_now") != "0":
        fail("performance_compare_allowed_now must remain 0")
    if closeout.get("replay_performed") != "0":
        fail("replay_performed must remain 0")
    if closeout.get("paper_order_intents_created") != "0" or closeout.get("live_orders_created") != "0":
        fail("paper/live orders must remain 0")
    if closeout.get("strategy_acceptance") != "NOT_ACCEPTED":
        fail("strategy acceptance changed")
    if closeout.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        fail("deployment readiness changed")
    if closeout.get("real_capital") != "FORBIDDEN":
        fail("real capital changed")

    snapshot_path = ARTIFACT_DIR / "task2982_catalog_policy_compare_audit_snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot.get("status") != "BLOCKED":
        fail("snapshot status must be BLOCKED")
    if not snapshot.get("policy_freezes") or not snapshot.get("same_experiment_gate"):
        fail("snapshot missing freeze or same-experiment rows")

    registry = require_csv(ROOT / "tasks/task_registry.csv")
    task_rows = registry[registry["task_id"].isin([f"Task{idx}" for idx in range(2981, 3001)])]
    if len(task_rows) != 20:
        fail(f"expected 20 registry rows, found {len(task_rows)}")

    if "Task2981-Task3000 exposed" not in opstate:
        fail("operating state missing Task2981-3000 line")
    if "Test results do not modify strategy acceptance status" not in report:
        fail("report missing required status footer")

    print("[TASK2981_3000_VALIDATE_OK]")


if __name__ == "__main__":
    main()
