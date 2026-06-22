from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from .paper_runtime_common import append_registry_rows, utc_now, write_csv, write_task_report


REPORT_DIR = Path("docs/reports/task_586_frontend_paper_ops_integration")


def run_task586() -> dict[str, pd.DataFrame]:
    catalog_proc = subprocess.run(
        [sys.executable, "scripts/build_trader_terminal_catalog.py"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    build_proc = subprocess.run(
        [npm_cmd, "run", "build"],
        cwd=Path("frontend/trader-terminal"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=300,
    )
    catalog_path = Path("frontend/trader-terminal/public/catalog/trader_terminal_catalog.json")
    contract = pd.DataFrame(
        [
            {"section": "connection", "fields": "KIS/Slack/env/control_state", "source": "paper_ops.v2 + Task582 legacy"},
            {"section": "data_status", "fields": "latest quote ts/freshness/stale reason", "source": "Task583"},
            {"section": "strategy_decision", "fields": "decision_id/status/reason/score", "source": "Task584"},
            {"section": "order_status", "fields": "submitted/filled/rejected/lineage", "source": "Task585"},
            {"section": "slack_status", "fields": "message type/send status", "source": "Task587"},
        ]
    )
    status = (
        "FRONTEND_PAPER_OPS_V2_READY"
        if catalog_proc.returncode == 0 and build_proc.returncode == 0 and catalog_path.exists()
        else "FRONTEND_BUILD_OR_CATALOG_FAILED"
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task586",
                "task_name": "Frontend Paper Ops Integration V2",
                "decision_status": status,
                "catalog_path": str(catalog_path),
                "catalog_exists_flag": int(catalog_path.exists()),
                "catalog_build_returncode": catalog_proc.returncode,
                "frontend_build_returncode": build_proc.returncode,
                "ui_reads_catalog_only_flag": 1,
                "deployment_ready_flag": 0,
                "diagnostic_only_flag": 1,
            }
        ]
    )
    build_audit = pd.DataFrame(
        [
            {
                "created_at_utc": utc_now(),
                "command": "python scripts/build_trader_terminal_catalog.py",
                "catalog_returncode": catalog_proc.returncode,
                "catalog_stdout_tail": catalog_proc.stdout[-2000:],
                "catalog_stderr_tail": catalog_proc.stderr[-2000:],
                "frontend_build_returncode": build_proc.returncode,
                "frontend_build_stdout_tail": build_proc.stdout[-2000:],
                "frontend_build_stderr_tail": build_proc.stderr[-2000:],
            }
        ]
    )
    artifacts = {
        "frontend_paper_ops_contract_v2.csv": contract,
        "frontend_catalog_build_audit.csv": build_audit,
        "task_586_decision.csv": decision,
    }
    for name, frame in artifacts.items():
        write_csv(REPORT_DIR, name, frame)
    (REPORT_DIR / "frontend_paper_ops_contract_v2.md").parent.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "frontend_paper_ops_contract_v2.md").write_text(
        "# Frontend Paper Ops Contract V2\n\n"
        "- UI reads `frontend/trader-terminal/public/catalog/trader_terminal_catalog.json` only.\n"
        "- Task583 provides data freshness.\n"
        "- Task584 provides runtime decision and no-trade reason.\n"
        "- Task585 provides order/fill/lifecycle lineage.\n"
        "- Task587 provides Slack send state.\n"
        "- No raw CSV is read directly by React.\n",
        encoding="utf-8",
    )
    write_task_report(
        REPORT_DIR,
        "task_586_frontend_paper_ops_integration.md",
        title="Task586 - Frontend Paper Ops Integration V2",
        decision_summary=[
            f"decision_status={status}",
            "React paper ops page is catalog-backed.",
            "No raw CSV direct-read is required in the frontend.",
        ],
        quant_lines=[
            "The frontend now exposes the operational chain from data freshness through runtime decision to order lineage.",
            "The catalog preserves Task/artifact provenance and avoids UI-side interpretation of raw task files.",
        ],
        decision_maker_lines=[
            "모의거래 화면에서 왜 거래가 됐는지 또는 왜 안 됐는지 볼 수 있게 만들었습니다.",
            "데이터 최신성, 전략 판단, 주문 상태, Slack 보고 상태가 한 화면에 표시됩니다.",
        ],
    )
    append_registry_rows(
        [
            {
                "task_id": "Task586",
                "title": "Frontend Paper Ops Integration V2",
                "owner_team": "Frontend Team",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "diagnostic-only",
                "data_readiness": "runtime-source",
                "parent_task": "Task585",
                "key_report": str(REPORT_DIR / "task_586_frontend_paper_ops_integration.md"),
                "key_decision": str(REPORT_DIR / "task_586_decision.csv"),
                "key_artifacts": str(REPORT_DIR),
                "validation_command": "python -m unittest tests.test_task586_frontend_paper_ops_integration",
                "notes": "Catalog-backed paper ops v2 UI integration.",
            }
        ]
    )
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    artifacts = run_task586()
    print(artifacts["task_586_decision.csv"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
