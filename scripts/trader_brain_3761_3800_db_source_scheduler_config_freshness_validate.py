from __future__ import annotations

import csv
import json
import os
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "trading.db"
TASK_ID = "task_3761_3800_db_source_scheduler_config_freshness_validator"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs" / "reports" / TASK_ID
CONFIG = ROOT / "configs" / "db_source_acquisition_scheduler.json"
RUNNER = ROOT / "scripts" / "run_db_source_acquisition_scheduler.ps1"
INSTALLER = ROOT / "scripts" / "install_db_source_acquisition_scheduler_task.ps1"
SEC_LIVE_ATTEMPT = ARTIFACT_DIR / "sec_live_adapter_attempt.json"


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise AssertionError(f"missing json artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _count(con: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> int:
    return int(con.execute(sql, params).fetchone()[0])


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone() is not None


def _validate_config() -> dict[str, object]:
    if not CONFIG.exists():
        raise AssertionError("missing DB source acquisition scheduler config")
    if not RUNNER.exists() or not INSTALLER.exists():
        raise AssertionError("missing DB source acquisition scheduler scripts")
    payload = _load_json(CONFIG)
    if payload.get("owner_id") != "operator-db-source-acquisition-scheduler":
        raise AssertionError("unexpected source scheduler owner_id")
    if payload.get("default_allow_network") is not False:
        raise AssertionError("default_allow_network must stay false")
    jobs = {str(row.get("name")): row for row in payload.get("jobs", [])}
    for name in ("intraday_market_sources_5m", "heavy_sources_60m", "registered_db_loop_5m"):
        if name not in jobs:
            raise AssertionError(f"missing scheduler job config: {name}")
    if "sec_events" not in jobs["heavy_sources_60m"].get("families", []):
        raise AssertionError("heavy source job must include sec_events")
    run_text = RUNNER.read_text(encoding="utf-8")
    install_text = INSTALLER.read_text(encoding="utf-8")
    required = ("tools.db.run_source_acquisition_once", "tools.db.run_registered_loop_once", "--apply")
    for token in required:
        if token not in run_text:
            raise AssertionError(f"scheduler runner missing token: {token}")
    forbidden = ("KISClient", "submit_order", "run_trade_once")
    combined = run_text + "\n" + install_text
    for token in forbidden:
        if token in combined:
            raise AssertionError(f"scheduler scripts must not call order path: {token}")
    return {
        "owner_id": payload["owner_id"],
        "jobs": len(payload.get("jobs", [])),
        "default_allow_network": payload["default_allow_network"],
        "sec_user_agent_env_present": bool(os.environ.get(str(payload.get("sec_user_agent_env_name") or ""))),
    }


def _validate_sec_attempt() -> dict[str, object]:
    if not SEC_LIVE_ATTEMPT.exists():
        return {"sec_live_attempt_artifact": "MISSING_ALLOWED_IF_USER_AGENT_ABSENT"}
    payload = _load_json(SEC_LIVE_ATTEMPT)
    results = payload.get("results", [])
    if not results:
        raise AssertionError("SEC live attempt artifact has no results")
    result = results[0]
    if os.environ.get("SEC_USER_AGENT"):
        if result.get("status") != "SUCCESS":
            raise AssertionError("SEC_USER_AGENT exists but SEC live adapter did not succeed")
    else:
        if result.get("skipped_reason") != "SEC_USER_AGENT_MISSING":
            raise AssertionError("SEC live missing-user-agent path must record SEC_USER_AGENT_MISSING")
    return {
        "sec_live_attempt_status": result.get("status"),
        "sec_live_attempt_skipped_reason": result.get("skipped_reason", ""),
    }


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    config_audit = _validate_config()
    sec_audit = _validate_sec_attempt()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        control = con.execute(
            "SELECT run_mode, kill_switch_active FROM control_state WHERE control_key='default'"
        ).fetchone()
        if control is None or (control["run_mode"], int(control["kill_switch_active"])) != ("DIAGNOSTIC_ONLY", 1):
            raise AssertionError(f"control_state must stay fail closed, got {dict(control) if control else None}")
        bad_permissions = _count(
            con,
            """
            SELECT COUNT(*)
            FROM scheduler_job_registry
            WHERE execution_permitted != 0
               OR broker_mutation_permitted != 0
               OR real_capital_permitted != 0
               OR paper_promotion_permitted != 0
            """,
        )
        if bad_permissions:
            raise AssertionError("scheduler registry permission columns must stay 0")

        for table in ("indicator_snapshots", "runtime_strategy_decisions", "reconciliation_runs"):
            if not _table_exists(con, table):
                raise AssertionError(f"missing required runtime table: {table}")

        indicator_diag = con.execute(
            """
            SELECT COUNT(*) AS rows, COALESCE(SUM(entry_allowed),0) AS entries,
                   COALESCE(SUM(selected_for_portfolio),0) AS selected
            FROM indicator_snapshots
            WHERE reason='DIAGNOSTIC_INDICATOR_REFRESH_NO_TRADE'
            """
        ).fetchone()
        if int(indicator_diag["rows"]) <= 0 or int(indicator_diag["entries"]) != 0 or int(indicator_diag["selected"]) != 0:
            raise AssertionError("diagnostic indicator rows must exist with no entry/selection permission")

        runtime_diag = con.execute(
            """
            SELECT COUNT(*) AS rows, COALESCE(SUM(quantity),0) AS quantity,
                   COALESCE(SUM(entry_allowed),0) AS entries,
                   COALESCE(SUM(used_label_flag),0) AS labels,
                   COALESCE(SUM(dummy_fallback_used_flag),0) AS dummy
            FROM runtime_strategy_decisions
            WHERE created_by_task='Task3761_3800'
            """
        ).fetchone()
        if int(runtime_diag["rows"]) <= 0:
            raise AssertionError("diagnostic runtime decisions missing")
        if any(int(runtime_diag[key]) != 0 for key in ("quantity", "entries", "labels", "dummy")):
            raise AssertionError("diagnostic runtime decisions must not permit orders, entries, labels, or dummy fallback")

        broker_block = con.execute(
            """
            SELECT status, max_severity, block_new_orders, raw_snapshot_json
            FROM reconciliation_runs
            WHERE reconciliation_id LIKE 'diag-broker-truth:%'
            ORDER BY finished_at DESC
            LIMIT 1
            """
        ).fetchone()
        if broker_block is None:
            raise AssertionError("diagnostic broker truth blocker row missing")
        if broker_block[:3] != ("BLOCKED", "CRITICAL", 1):
            raise AssertionError(f"unexpected broker blocker row: {broker_block[:3]}")
        broker_payload = json.loads(broker_block["raw_snapshot_json"])
        if broker_payload.get("broker_api_called") is not False or broker_payload.get("broker_mutation") is not False:
            raise AssertionError("broker truth blocker must not call or mutate broker state")

        required_families = {
            "broker_truth_reconciliation": {
                "diagnostic_broker_truth_reconciliation",
                "operator_broker_truth_fixture_reconciliation",
            },
            "indicator_snapshots": {"derived_indicator_snapshots_from_market_bars"},
            "runtime_strategy_decisions": {"derived_runtime_strategy_decisions_from_indicators"},
        }
        for family, allowed_providers in required_families.items():
            row = con.execute(
                """
                SELECT provider, freshness_status, strict_gate_allowed, proxy_allowed, evidence_ref
                FROM source_freshness
                WHERE source_family=?
                """,
                (family,),
            ).fetchone()
            if row is None:
                raise AssertionError(f"missing source_freshness row for {family}")
            if row["provider"] not in allowed_providers:
                raise AssertionError(f"unexpected provider for {family}: {row['provider']}")
            if int(row["strict_gate_allowed"]) != 0 or int(row["proxy_allowed"]) != 0:
                raise AssertionError(f"{family} gates must remain closed")
            if not row["evidence_ref"]:
                raise AssertionError(f"{family} evidence_ref missing")

        gate_rows = []
        for row in con.execute(
            """
            SELECT sf.source_family, sf.freshness_status, sf.strict_gate_allowed,
                   sf.proxy_allowed, sf.evidence_ref,
                   sr.receipt_id AS receipt_id,
                   COUNT(dle.edge_id) AS lineage_edges
            FROM source_freshness sf
            LEFT JOIN source_receipts sr ON sr.receipt_id=sf.evidence_ref
            LEFT JOIN data_lineage_edges dle ON dle.source_receipt_id=sf.evidence_ref
            GROUP BY sf.source_family, sf.freshness_status, sf.strict_gate_allowed,
                     sf.proxy_allowed, sf.evidence_ref, sr.receipt_id
            ORDER BY sf.source_family
            """
        ).fetchall():
            explicit_flag = int(row["strict_gate_allowed"]) == 1 or int(row["proxy_allowed"]) == 1
            evidence_ok = bool(row["receipt_id"]) and int(row["lineage_edges"]) > 0
            current = row["freshness_status"] == "CURRENT_OR_RECENT"
            gate_candidate = current and evidence_ok and explicit_flag
            gate_rows.append(
                {
                    "source_family": row["source_family"],
                    "freshness_status": row["freshness_status"],
                    "evidence_receipt_exists": int(bool(row["receipt_id"])),
                    "lineage_edge_count": int(row["lineage_edges"] or 0),
                    "explicit_gate_flag": int(explicit_flag),
                    "gate_open_candidate": int(gate_candidate),
                }
            )
        if any(int(row["gate_open_candidate"]) for row in gate_rows):
            raise AssertionError("active DB must not have gate-open candidate rows in this diagnostic task")
        if any(int(row["evidence_receipt_exists"]) == 0 for row in gate_rows):
            raise AssertionError("every source_freshness row must join to a source receipt")
        _write_csv(ARTIFACT_DIR / "source_freshness_gate_condition_audit.csv", gate_rows)

        freshness_rows = [dict(row) for row in con.execute("SELECT * FROM source_freshness ORDER BY source_family").fetchall()]
        ledger_rows = [
            dict(row)
            for row in con.execute(
                """
                SELECT *
                FROM scheduler_run_ledger
                WHERE cadence IN (
                    'broker_truth_reconciliation_refresh',
                    'indicator_snapshots_refresh',
                    'runtime_strategy_decisions_refresh'
                )
                ORDER BY created_at DESC
                LIMIT 30
                """
            ).fetchall()
        ]
    finally:
        con.close()

    _write_csv(ARTIFACT_DIR / "source_freshness_after_task.csv", freshness_rows)
    _write_csv(ARTIFACT_DIR / "scheduler_run_ledger_task_rows.csv", ledger_rows)
    result = {
        "config_audit": config_audit,
        "sec_audit": sec_audit,
        "indicator_diag_rows": int(indicator_diag["rows"]),
        "runtime_diag_rows": int(runtime_diag["rows"]),
        "broker_blocker_status": "BLOCKED",
        "active_gate_open_candidates": 0,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (ARTIFACT_DIR / "source_scheduler_config_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "[TASK3761_3800_OK] scheduler_config=PASS fresh_loop_evidence=PASS "
        "gate_conditions=PASS gates_closed=1 broker_blocked=1"
    )


if __name__ == "__main__":
    main()
