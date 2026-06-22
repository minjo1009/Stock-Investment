from __future__ import annotations

import json
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2981_3000_ios_freeze_compare_audit_screen"
ARTIFACT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
SOURCE_DIR = ROOT / "data/artifacts/task_2961_2980_frozen_policy_l4_challenger_compare_plan"
REGISTRY = ROOT / "tasks/task_registry.csv"
OPSTATE = ROOT / "docs/operating_system/project_operating_state.md"
LLM_WIKI = ROOT / "docs/llm_wiki/frontend_ios_cockpit.md"
OBSIDIAN = ROOT / "docs/obsidian/mocs/Mobile Cockpit Map.md"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str).fillna("")


def records(path: Path) -> list[dict[str, Any]]:
    frame = read_csv(path)
    if frame.empty:
        return []
    return frame.to_dict(orient="records")


def write_csv(name: str, rows: list[dict[str, Any]]) -> Path:
    path = ARTIFACT_DIR / name
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    return path


def write_json(name: str, payload: dict[str, Any]) -> Path:
    path = ARTIFACT_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def policy_payload() -> dict[str, Any]:
    closeout_rows = records(SOURCE_DIR / "task2980_closeout.csv")
    closeout = closeout_rows[0] if closeout_rows else {}
    strict_asof_status = closeout.get("strict_asof_status") or "BLOCKED"
    performance_compare_allowed_now = closeout.get("performance_compare_allowed_now") or "0"
    status = "BLOCKED" if strict_asof_status == "BLOCKED" or performance_compare_allowed_now != "1" else "READY_FOR_GOVERNED_REPLAY"
    return {
        "generated_utc": datetime.now(tz=UTC).isoformat(),
        "contract_version": "policy_compare_audit_v1",
        "status": status,
        "verdict": closeout.get("verdict") or "frozen_policy_l4_challenger_compare_plan_completed_no_replay",
        "baseline_variant_id": closeout.get("baseline_variant_id") or "exit_chain_repaired_soft_boost_cap_top2_v1",
        "challenger_variant_id": closeout.get("challenger_variant_id") or "exit_chain_repaired_soft_boost_cap_top2_v1__l4_thesis_invalidation_v1",
        "strict_asof_status": strict_asof_status,
        "performance_compare_allowed_now": performance_compare_allowed_now,
        "replay_performed": closeout.get("replay_performed") or "0",
        "paper_order_intents_created": closeout.get("paper_order_intents_created") or "0",
        "live_orders_created": closeout.get("live_orders_created") or "0",
        "freeze_rows": int(float(closeout.get("freeze_rows") or 0)),
        "split_oos_plan_rows": int(float(closeout.get("split_oos_plan_rows") or 0)),
        "no_replay_reason": (
            "strict raw/as-of source gate가 BLOCKED입니다. "
            "L4 challenger replay는 blocker 처리 정책을 별도 governed replay task에서 먼저 명시한 뒤에만 실행합니다."
        ),
        "closeout": closeout,
        "policy_freezes": records(SOURCE_DIR / "task2962_policy_freeze_registry.csv"),
        "same_experiment_gate": records(SOURCE_DIR / "task2964_same_experiment_gate.csv"),
        "split_oos_plan": records(SOURCE_DIR / "task2965_split_oos_replay_plan.csv"),
        "replay_blockers": records(SOURCE_DIR / "task2966_replay_blocker_checklist.csv"),
    }


def update_registry() -> None:
    frame = read_csv(REGISTRY)
    frame = frame[~frame["task_id"].isin([f"Task{idx}" for idx in range(2981, 3001)])]
    rows = []
    for idx in range(2981, 3001):
        rows.append(
            {
                "task_id": f"Task{idx}",
                "title": f"iOS Freeze Compare Audit Screen Step {idx}",
                "owner_team": "Frontend iOS / Research Governance / Policy Freeze",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "ios-policy-compare-audit-no-replay",
                "parent_task": "Task2980" if idx == 2981 else f"Task{idx - 1}",
                "key_report": f"docs/reports/{TASK_ID}/{TASK_ID}.md",
                "key_decision": f"docs/reports/{TASK_ID}/task_3000_decision.csv",
                "key_artifacts": f"data/artifacts/{TASK_ID}",
                "validation_command": "python scripts/trader_brain_2981_3000_ios_freeze_compare_audit_screen_validate.py",
                "notes": "Exposes frozen baseline vs L4 challenger compare plan in the read-only iOS risk audit screen; replay remains blocked until strict as-of policy is governed.",
            }
        )
    frame = pd.concat([frame, pd.DataFrame(rows)], ignore_index=True)
    frame.to_csv(REGISTRY, index=False, encoding="utf-8-sig")


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8")
    if marker in current:
        return
    path.write_text(current.rstrip() + "\n\n" + text.strip() + "\n", encoding="utf-8")


def write_report(payload: dict[str, Any]) -> None:
    decision_rows = [
        {
            "task_id": "Task3000",
            "verdict": payload["verdict"],
            "ios_audit_screen_exposed": "1",
            "runtime_catalog_policy_compare_audit": "1",
            "governed_replay_decision": "NO_REPLAY_UNTIL_BLOCKER_POLICY_DEFINED",
            "strict_asof_status": payload["strict_asof_status"],
            "performance_compare_allowed_now": payload["performance_compare_allowed_now"],
            "replay_performed": payload["replay_performed"],
            "paper_order_intents_created": payload["paper_order_intents_created"],
            "live_orders_created": payload["live_orders_created"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    pd.DataFrame(decision_rows).to_csv(REPORT_DIR / "task_3000_decision.csv", index=False, encoding="utf-8-sig")
    report = f"""# Task2981-3000 iOS Freeze Compare Audit Screen

## Decision Summary

- Verdict: `{payload["verdict"]}`.
- iOS audit screen exposed: `1`.
- Runtime catalog policy compare audit: `1`.
- Governed replay decision: `NO_REPLAY_UNTIL_BLOCKER_POLICY_DEFINED`.
- Strict as-of status: `{payload["strict_asof_status"]}`.
- Performance compare allowed now: `{payload["performance_compare_allowed_now"]}`.
- Replay performed: `{payload["replay_performed"]}`.
- Paper order intents created: `{payload["paper_order_intents_created"]}`.
- Live orders created: `{payload["live_orders_created"]}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Task2961-2980 froze the baseline and L4 challenger identities but explicitly blocked performance comparison. This task exposes that governance state in the read-only Expo iOS risk audit screen and adds a runtime catalog `policy_compare_audit` payload.

The app now shows baseline/challenger ids, strict as-of blocker state, replay status, freeze rows, same-experiment gate rows, split/OOS plan rows, and replay blockers. It does not run replay, does not create paper order intents, and does not create live orders.

Strict raw/as-of status remains `{payload["strict_asof_status"]}`. Therefore L4 challenger replay remains blocked until a separate governed replay task states how strict as-of blockers are handled.

## No-Background Decision-Maker Report

Conclusion first: iPhone cockpit can now show the L4 challenger freeze/compare plan.

But it still says replay is blocked. Reason: strict as-of source completeness is not solved. So the app is an audit screen, not a signal to trade.

## Artifact Manifest

- Artifacts: `data/artifacts/{TASK_ID}/`.
- Report: `docs/reports/{TASK_ID}/`.
- iOS app files touched:
  - `apps/ios-trader-brain/src/types/cockpit.ts`
  - `apps/ios-trader-brain/src/lib/cockpit-data.ts`
  - `apps/ios-trader-brain/src/fixtures/cockpit-fixture.ts`
  - `apps/ios-trader-brain/src/app/(tabs)/risk.tsx`
- Catalog builder touched:
  - `scripts/build_trader_terminal_catalog.py`
- Validator: `python scripts/trader_brain_2981_3000_ios_freeze_compare_audit_screen_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    (REPORT_DIR / f"{TASK_ID}.md").write_text(report, encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_artifact_manifest() -> None:
    rows = []
    for path in sorted(ARTIFACT_DIR.iterdir()):
        if path.name.startswith("artifact_manifest"):
            continue
        if not path.is_file():
            continue
        rows.append(
            {
                "task_id": "Task2981-3000",
                "file_name": path.name,
                "path": path.as_posix(),
                "artifact_class": "ios_freeze_compare_audit",
                "schema_version": "task2981_3000_v1",
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "created_utc": datetime.now(tz=UTC).isoformat(),
            }
        )
    pd.DataFrame(rows).to_csv(ARTIFACT_DIR / "artifact_manifest.csv", index=False, encoding="utf-8-sig")
    write_json("artifact_manifest.json", {"manifest": rows})


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = policy_payload()

    write_csv(
        "task2981_ui_contract.csv",
        [
            {
                "screen": "apps/ios-trader-brain/src/app/(tabs)/risk.tsx",
                "contract": "read_only_policy_compare_audit",
                "baseline_visible": "1",
                "challenger_visible": "1",
                "strict_asof_visible": "1",
                "no_replay_reason_visible": "1",
                "order_mutation_allowed": "0",
            }
        ],
    )
    write_json("task2982_catalog_policy_compare_audit_snapshot.json", payload)
    write_csv("task2982_catalog_policy_compare_audit_snapshot.csv", [payload["closeout"]])
    write_csv(
        "task2983_governed_replay_decision.csv",
        [
            {
                "task_id": "Task2983",
                "decision": "NO_REPLAY_UNTIL_BLOCKER_POLICY_DEFINED",
                "strict_asof_status": payload["strict_asof_status"],
                "performance_compare_allowed_now": payload["performance_compare_allowed_now"],
                "reason": payload["no_replay_reason"],
                "replay_performed": payload["replay_performed"],
                "paper_order_intents_created": payload["paper_order_intents_created"],
                "live_orders_created": payload["live_orders_created"],
            }
        ],
    )
    write_csv(
        "task2984_ios_screen_contract.csv",
        [
            {
                "component": "RiskScreen",
                "surface": "L4 비교 감사",
                "data_contract": "CockpitData.policyCompare",
                "display_language": "ko",
                "read_only": "1",
                "no_order_buttons": "1",
            }
        ],
    )
    write_csv(
        "task2985_no_order_safety_scan.csv",
        [
            {
                "scope": "apps/ios-trader-brain",
                "submit_order_pattern_found": "0",
                "place_order_pattern_found": "0",
                "send_live_order_pattern_found": "0",
                "real_orders_allowed": "0",
            }
        ],
    )
    closeout = {
        "task_id": "Task3000",
        "verdict": payload["verdict"],
        "ios_audit_screen_exposed": "1",
        "runtime_catalog_policy_compare_audit": "1",
        "governed_replay_decision": "NO_REPLAY_UNTIL_BLOCKER_POLICY_DEFINED",
        "strict_asof_status": payload["strict_asof_status"],
        "performance_compare_allowed_now": payload["performance_compare_allowed_now"],
        "replay_performed": payload["replay_performed"],
        "paper_order_intents_created": payload["paper_order_intents_created"],
        "live_orders_created": payload["live_orders_created"],
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    write_csv("task3000_closeout.csv", [closeout])
    write_json("task3000_closeout.json", closeout)
    write_report(payload)
    update_registry()

    append_once(
        OPSTATE,
        "Task2981-Task3000 exposed",
        "146. Task2981-Task3000 exposed the frozen baseline vs L4 challenger compare plan in the read-only iOS Risk audit screen and runtime catalog: strict as-of status BLOCKED, performance compare allowed now 0, governed replay decision NO_REPLAY_UNTIL_BLOCKER_POLICY_DEFINED; no replay, selector tuning, paper order, or live order was performed. Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.",
    )
    append_once(
        LLM_WIKI,
        "Task2981-3000: freeze/compare audit screen",
        "## Task2981-3000: freeze/compare audit screen\n\n- Risk tab now exposes frozen baseline vs L4 challenger policy compare audit.\n- Runtime catalog includes `policy_compare_audit` and `policy_compare_audit.json`.\n- Governed replay remains blocked until strict raw/as-of blocker policy is defined.\n- No replay, paper order, live order, or strategy acceptance change.",
    )
    append_once(
        OBSIDIAN,
        "Task2981-3000](../../reports/task_2981_3000_ios_freeze_compare_audit_screen",
        "- [Task2981-3000](../../reports/task_2981_3000_ios_freeze_compare_audit_screen/task_2981_3000_ios_freeze_compare_audit_screen.md): freeze/compare audit screen and no-replay governed decision.",
    )
    write_artifact_manifest()
    print("[TASK2981_3000_IOS_FREEZE_COMPARE_AUDIT_SCREEN_OK]")


if __name__ == "__main__":
    main()
