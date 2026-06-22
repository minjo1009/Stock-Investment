from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from integration.kis_client import KISClient


REQUIRED_ENV = (
    "KIS_APP_KEY",
    "KIS_APP_SECRET",
    "KIS_ACCOUNT_NUMBER",
    "KIS_PRODUCT_CODE",
)

SENSITIVE_KEYS = {
    "authorization",
    "appkey",
    "appsecret",
    "access_token",
    "token",
    "hashkey",
    "cano",
    "acnt_prdt_cd",
    "account",
    "account_number",
    "ord_gno_brno",
}


@dataclass
class LifecycleDecision:
    status: str
    answer: str
    reasons: list[str]


def _load_env_file(path: Path) -> bool:
    if not path.exists():
        return False
    loaded = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value
            loaded = True
    return loaded


def _safe_ratio(num: float, den: float) -> float:
    return (num / den) if den else 0.0


def _sanitize(data: Any) -> Any:
    if isinstance(data, dict):
        out: dict[str, Any] = {}
        for k, v in data.items():
            key = str(k)
            if key.strip().lower() in SENSITIVE_KEYS:
                out[key] = "__REDACTED__"
            else:
                out[key] = _sanitize(v)
        return out
    if isinstance(data, list):
        return [_sanitize(v) for v in data]
    if isinstance(data, str):
        # conservative redact for long token-like strings
        if len(data) > 32 and data.isalnum():
            return "__REDACTED__"
    return data


def _table_exists(con: sqlite3.Connection, table_name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def _run_phase5_loop(*, db_path: str, env_file: str, runs: int, interval_minutes: int, symbols: str) -> dict[str, Any]:
    cmd = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(Path("scripts") / "run_phase5_paper_loop.ps1"),
        "-DbPath",
        db_path,
        "-EnvFile",
        env_file,
        "-MaxRuns",
        str(runs),
        "-IntervalMinutes",
        str(interval_minutes),
    ]
    if symbols.strip():
        cmd.extend(["-Symbols", symbols.strip()])
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    return {
        "returncode": proc.returncode,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
    }


def _collect_db_stats(db_path: str) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        if not _table_exists(con, "orders"):
            return {
                "orders_total": 0,
                "submitted_orders": 0,
                "filled_orders": 0,
                "cancelled_orders": 0,
                "unknown_orders": 0,
                "market_order_path_count": 0,
                "latest_orders": [],
                "latest_order_id": None,
                "latest_order_symbol": None,
                "latest_order_status": None,
                "latest_submitted_at": None,
            }
        rows = [dict(r) for r in con.execute(
            """
            SELECT order_id, symbol, status, raw_status, submitted_at
            FROM orders
            ORDER BY submitted_at DESC
            LIMIT 100
            """
        ).fetchall()]
        submitted = sum(1 for r in rows if str(r.get("status") or "").upper() in {"SUBMITTED", "PENDING", "PARTIAL", "FILLED", "CANCELLED", "EXPIRED", "TIMEOUT", "FAILED", "REJECTED"})
        filled = sum(1 for r in rows if str(r.get("status") or "").upper() == "FILLED")
        cancelled = sum(1 for r in rows if str(r.get("status") or "").upper() == "CANCELLED")
        unknown = sum(1 for r in rows if str(r.get("status") or "").upper() == "UNKNOWN")
        market_path = sum(1 for r in rows if "MARKET" in str(r.get("raw_status") or "").upper())
        latest = rows[0] if rows else {}
        return {
            "orders_total": len(rows),
            "submitted_orders": submitted,
            "filled_orders": filled,
            "cancelled_orders": cancelled,
            "unknown_orders": unknown,
            "market_order_path_count": market_path,
            "latest_orders": rows[:20],
            "latest_order_id": latest.get("order_id"),
            "latest_order_symbol": latest.get("symbol"),
            "latest_order_status": latest.get("status"),
            "latest_submitted_at": latest.get("submitted_at"),
        }
    finally:
        con.close()


def _collect_recon_stats(db_path: str) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        if not _table_exists(con, "reconciliation_runs"):
            return {
                "reconciliation_total": 0,
                "reconciliation_critical_count": 0,
                "reconciliation_success_count": 0,
                "cancel_unknown_escalation_count": 0,
                "late_fill_count": 0,
                "latest_reconciliation": [],
            }
        runs = [dict(r) for r in con.execute(
            """
            SELECT reconciliation_id, status, max_severity, started_at, finished_at
            FROM reconciliation_runs
            ORDER BY started_at DESC
            LIMIT 100
            """
        ).fetchall()]
        critical = sum(1 for r in runs if str(r.get("max_severity") or "").upper() == "CRITICAL")
        success = sum(
            1
            for r in runs
            if str(r.get("status") or "").upper() in {"MATCH", "OK", "SUCCESS", "CLEAN", "NO_MISMATCH"}
        )
        late_fill = 0
        unknown_escalation = 0
        if _table_exists(con, "reconciliation_events"):
            events = [dict(r) for r in con.execute(
                """
                SELECT event_type
                FROM reconciliation_events
                ORDER BY created_at DESC
                LIMIT 500
                """
            ).fetchall()]
            late_fill = sum(1 for e in events if str(e.get("event_type") or "").upper() == "LATE_FILL")
            unknown_escalation = sum(1 for e in events if str(e.get("event_type") or "").upper() == "UNKNOWN_ESCALATED")
        return {
            "reconciliation_total": len(runs),
            "reconciliation_critical_count": critical,
            "reconciliation_success_count": success,
            "cancel_unknown_escalation_count": unknown_escalation,
            "late_fill_count": late_fill,
            "latest_reconciliation": runs[:20],
        }
    finally:
        con.close()


def _collect_evidence_stats(runs_dir: Path) -> dict[str, Any]:
    files = sorted(runs_dir.glob("*.json"))
    entries: list[dict[str, Any]] = []
    for p in files[-100:]:
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            entries.append(payload)
    total = len(entries)
    runs_with_orders = sum(1 for e in entries if int(e.get("order_attempts") or 0) > 0)
    runs_with_fills = sum(1 for e in entries if int(e.get("filled_orders") or 0) > 0)
    runs_with_cancels = sum(1 for e in entries if int(e.get("cancelled_orders") or 0) > 0)
    return {
        "total_runs": total,
        "runs_with_orders": runs_with_orders,
        "runs_with_fills": runs_with_fills,
        "runs_with_cancels": runs_with_cancels,
        "runs_files": [str(p) for p in files[-50:]],
    }


def _capture_fixtures(*, fixture_dir: Path, order_id: str | None, symbol: str | None) -> dict[str, Any]:
    fixture_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"written": [], "missing": []}

    def _write(name: str, payload: dict[str, Any]) -> None:
        p = fixture_dir / name
        p.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        result["written"].append(str(p))

    if not all(os.environ.get(k) for k in REQUIRED_ENV):
        # write placeholders with explicit reason
        placeholder = {
            "_fixture_meta": {
                "source": "KIS paper",
                "captured_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "sanitized": True,
                "reason": "missing_env",
            },
            "response": None,
        }
        for name in (
            "order_submit_response.json",
            "order_status_pending.json",
            "order_status_filled.json",
            "order_status_cancelled.json",
            "fills_response.json",
        ):
            _write(name, placeholder)
        return result

    try:
        kis = KISClient.from_env()
    except Exception as exc:
        placeholder = {
            "_fixture_meta": {
                "source": "KIS paper",
                "captured_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "sanitized": True,
                "reason": f"kis_client_init_failed: {exc}",
            },
            "response": None,
        }
        for name in (
            "order_submit_response.json",
            "order_status_pending.json",
            "order_status_filled.json",
            "order_status_cancelled.json",
            "fills_response.json",
        ):
            _write(name, placeholder)
        return result

    statuses = kis.fetch_broker_order_statuses(symbol=symbol)
    pending = next((s for s in statuses if str(s.get("mapped_status")).upper() in {"SUBMITTED", "PENDING", "PARTIAL"}), None)
    filled = next((s for s in statuses if str(s.get("mapped_status")).upper() == "FILLED"), None)
    cancelled = next((s for s in statuses if str(s.get("mapped_status")).upper() == "CANCELLED"), None)

    sample_order = order_id or (pending or filled or cancelled or {}).get("order_id")
    sample_symbol = symbol or (pending or filled or cancelled or {}).get("symbol")

    submit_payload = {
        "_fixture_meta": {
            "source": "KIS paper",
            "captured_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "sanitized": True,
            "case": "order_submit_response",
            "note": "submit response may be unavailable unless a new order is submitted in this session.",
        },
        "response": {
            "order_id": sample_order,
            "symbol": sample_symbol,
        },
    }
    _write("order_submit_response.json", _sanitize(submit_payload))

    _write(
        "order_status_pending.json",
        _sanitize(
            {
                "_fixture_meta": {
                    "source": "KIS paper",
                    "captured_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "sanitized": True,
                    "case": "order_status_pending",
                },
                "response": pending,
            }
        ),
    )
    _write(
        "order_status_filled.json",
        _sanitize(
            {
                "_fixture_meta": {
                    "source": "KIS paper",
                    "captured_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "sanitized": True,
                    "case": "order_status_filled",
                },
                "response": filled,
            }
        ),
    )
    _write(
        "order_status_cancelled.json",
        _sanitize(
            {
                "_fixture_meta": {
                    "source": "KIS paper",
                    "captured_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "sanitized": True,
                    "case": "order_status_cancelled",
                },
                "response": cancelled,
            }
        ),
    )

    fills_response = None
    if sample_order:
        try:
            fills_response = kis.get_fills(str(sample_order), symbol=str(sample_symbol or ""))
        except Exception as exc:
            fills_response = {"error": str(exc)}
    _write(
        "fills_response.json",
        _sanitize(
            {
                "_fixture_meta": {
                    "source": "KIS paper",
                    "captured_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "sanitized": True,
                    "case": "fills_response",
                },
                "response": fills_response,
            }
        ),
    )
    return result


def _decide(
    *,
    submitted_orders: int,
    filled_orders: int,
    cancelled_orders: int,
    unknown_events: int,
    reconciliation_critical_count: int,
    market_order_path_count: int,
    cancel_unknown_escalation_count: int,
) -> LifecycleDecision:
    reasons: list[str] = []
    if unknown_events > 0:
        reasons.append("UNKNOWN_EVENT_DETECTED")
    if reconciliation_critical_count > 0:
        reasons.append("RECONCILIATION_CRITICAL_DETECTED")
    if market_order_path_count > 0:
        reasons.append("MARKET_ORDER_PATH_DETECTED")
    if cancel_unknown_escalation_count > 0:
        reasons.append("CANCEL_LOOP_UNKNOWN_ESCALATION")
    if reasons:
        return LifecycleDecision(status="FAIL", answer="NO", reasons=reasons)

    if submitted_orders >= 1 and (filled_orders >= 1 or cancelled_orders >= 1):
        return LifecycleDecision(status="PASS", answer="YES", reasons=["BROKER_LIFECYCLE_CONFIRMED"])
    if submitted_orders >= 1:
        return LifecycleDecision(status="WARNING", answer="NO", reasons=["ORDER_SUBMITTED_BUT_NO_TERMINAL_FILL_CANCEL"])
    return LifecycleDecision(status="WARNING", answer="NO", reasons=["NO_ORDER_SAMPLE"])


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 091 - Paper Broker Lifecycle Evidence Gate")
    lines.append("")
    lines.append("## 1. Execution Summary")
    es = report["execution_summary"]
    for k in ("total_runs", "runs_with_orders", "runs_with_fills", "runs_with_cancels"):
        lines.append(f"- {k}: {es.get(k)}")
    lines.append("")
    lines.append("## 2. Lifecycle Trace")
    lt = report["lifecycle_trace"]
    for k in (
        "submitted_orders",
        "filled_orders",
        "cancelled_orders",
        "unknown_orders",
        "latest_order_id",
        "latest_order_symbol",
        "latest_order_status",
        "latest_submitted_at",
    ):
        lines.append(f"- {k}: {lt.get(k)}")
    lines.append("")
    lines.append("## 3. Broker vs Local State Comparison")
    bc = report["broker_local_comparison"]
    for k, v in bc.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 4. Anomalies")
    for k, v in report["anomalies"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 5. Fixture List")
    for p in report.get("fixtures", {}).get("written", []):
        lines.append(f"- written: {p}")
    for p in report.get("fixtures", {}).get("missing", []):
        lines.append(f"- missing: {p}")
    lines.append("")
    lines.append("## 6. Decision")
    lines.append(f"- status: {report['decision']['status']}")
    lines.append(f"- answer: {report['decision']['answer']}")
    for reason in report["decision"]["reasons"]:
        lines.append(f"- reason: {reason}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 091: Paper broker lifecycle evidence gate")
    parser.add_argument("--db-path", type=str, default=os.environ.get("TRADING_DB_PATH", "trading.db"))
    parser.add_argument("--env-file", type=str, default="config/kis_paper.env")
    parser.add_argument("--run-loop", action="store_true")
    parser.add_argument("--loop-runs", type=int, default=1)
    parser.add_argument("--loop-interval-minutes", type=int, default=5)
    parser.add_argument("--symbols", type=str, default="")
    parser.add_argument("--runs-dir", type=str, default="docs/reports/task_087/runs")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_091/task_091_broker_lifecycle.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_091/task_091_broker_lifecycle.md")
    parser.add_argument("--fixture-dir", type=str, default="tests/fixtures/kis/real")
    args = parser.parse_args()

    _load_env_file(Path(args.env_file))
    missing_env = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    env_name = (os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper")
    if env_name != "paper":
        report = {
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "decision": {
                "status": "FAIL",
                "answer": "NO",
                "reasons": ["LIVE_ENVIRONMENT_DETECTED"],
            },
            "execution_summary": {"total_runs": 0, "runs_with_orders": 0, "runs_with_fills": 0, "runs_with_cancels": 0},
            "lifecycle_trace": {},
            "broker_local_comparison": {},
            "anomalies": {},
            "fixtures": {"written": [], "missing": []},
            "loop_execution": {"executed": False},
            "missing_env": missing_env,
        }
        out_json = Path(args.json_out)
        out_md = Path(args.md_out)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
        out_md.write_text(_markdown(report), encoding="utf-8")
        print(f"written_json={out_json}")
        print(f"written_md={out_md}")
        print("decision=FAIL")
        return 0

    loop_execution = {"executed": False}
    if args.run_loop and not missing_env:
        loop_execution = _run_phase5_loop(
            db_path=args.db_path,
            env_file=args.env_file,
            runs=max(1, int(args.loop_runs)),
            interval_minutes=max(0, int(args.loop_interval_minutes)),
            symbols=args.symbols,
        )
        loop_execution["executed"] = True

    evidence_stats = _collect_evidence_stats(Path(args.runs_dir))
    db_stats = _collect_db_stats(args.db_path)
    recon_stats = _collect_recon_stats(args.db_path)

    unknown_events = int(db_stats["unknown_orders"])
    reconciliation_critical_count = int(recon_stats["reconciliation_critical_count"])
    market_order_path_count = int(db_stats["market_order_path_count"])
    cancel_unknown_escalation_count = int(recon_stats["cancel_unknown_escalation_count"])
    decision = _decide(
        submitted_orders=int(db_stats["submitted_orders"]),
        filled_orders=int(db_stats["filled_orders"]),
        cancelled_orders=int(db_stats["cancelled_orders"]),
        unknown_events=unknown_events,
        reconciliation_critical_count=reconciliation_critical_count,
        market_order_path_count=market_order_path_count,
        cancel_unknown_escalation_count=cancel_unknown_escalation_count,
    )

    fixtures = _capture_fixtures(
        fixture_dir=Path(args.fixture_dir),
        order_id=db_stats.get("latest_order_id"),
        symbol=db_stats.get("latest_order_symbol"),
    )

    lifecycle_trace = {
        "submitted_orders": db_stats["submitted_orders"],
        "filled_orders": db_stats["filled_orders"],
        "cancelled_orders": db_stats["cancelled_orders"],
        "unknown_orders": db_stats["unknown_orders"],
        "latest_order_id": db_stats["latest_order_id"],
        "latest_order_symbol": db_stats["latest_order_symbol"],
        "latest_order_status": db_stats["latest_order_status"],
        "latest_submitted_at": db_stats["latest_submitted_at"],
    }
    broker_local_comparison = {
        "reconciliation_total": recon_stats["reconciliation_total"],
        "reconciliation_success_count": recon_stats["reconciliation_success_count"],
        "reconciliation_critical_count": recon_stats["reconciliation_critical_count"],
        "local_unknown_orders": db_stats["unknown_orders"],
        "broker_local_aligned": (recon_stats["reconciliation_critical_count"] == 0 and db_stats["unknown_orders"] == 0),
    }
    anomalies = {
        "partial_fill_observed": bool(db_stats["latest_order_status"] and str(db_stats["latest_order_status"]).upper() == "PARTIAL"),
        "cancel_race_fill_observed": bool(recon_stats["cancel_unknown_escalation_count"] > 0),
        "late_fill_count": recon_stats["late_fill_count"],
        "market_order_path_count": db_stats["market_order_path_count"],
        "loop_non_zero": (loop_execution.get("returncode") not in (None, 0)),
    }

    report = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment": env_name,
        "missing_env": missing_env,
        "loop_execution": loop_execution,
        "execution_summary": evidence_stats,
        "lifecycle_trace": lifecycle_trace,
        "broker_local_comparison": broker_local_comparison,
        "anomalies": anomalies,
        "fixtures": fixtures,
        "decision": {
            "status": decision.status,
            "answer": decision.answer,
            "reasons": decision.reasons,
        },
    }

    out_json = Path(args.json_out)
    out_md = Path(args.md_out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    out_md.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={out_json}")
    print(f"written_md={out_md}")
    print(f"decision={decision.status}")
    print(f"answer={decision.answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
