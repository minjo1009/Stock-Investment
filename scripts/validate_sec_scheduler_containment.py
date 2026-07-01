from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONFIG = ROOT / "configs" / "db_source_acquisition_scheduler.json"
RUNNER = ROOT / "scripts" / "run_db_source_acquisition_scheduler.ps1"
BLOCK_STATE_DEFAULT = ROOT / "data" / "artifacts" / "sec_live_access_block_state.json"
ARTIFACT = ROOT / "data" / "artifacts" / "task_3848_sec_scheduler_containment" / "sec_scheduler_containment_validate.json"
STARTUP_DIR = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

SCAN_ROOTS = (
    ROOT / "configs",
    ROOT / "scripts",
    ROOT / "tools",
)
SEC_RISK_TOKENS = (
    "data.sec.gov",
    "www.sec.gov/cgi-bin/browse-edgar",
    "www.sec.gov/files/company_tickers.json",
    "sec_events",
    "SEC_USER_AGENT",
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_ts(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _sec_cooldown_active(block_state: dict[str, Any]) -> tuple[bool, str]:
    retry_after = _parse_ts(str(block_state.get("retry_after_ts") or ""))
    if retry_after is None:
        detected = _parse_ts(str(block_state.get("detected_at") or ""))
        if detected is not None:
            cooldown_seconds = int(block_state.get("cooldown_seconds") or 0)
            retry_after = detected + timedelta(seconds=cooldown_seconds)
    if retry_after is None:
        return False, ""
    return datetime.now(UTC) < retry_after, retry_after.isoformat().replace("+00:00", "Z")


def _powershell_json(command: str) -> tuple[list[dict[str, Any]], str]:
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:  # pragma: no cover - Windows environment probe.
        return [], f"POWERSHELL_PROBE_FAILED:{type(exc).__name__}"
    stdout = completed.stdout.strip()
    if completed.returncode != 0:
        return [], f"POWERSHELL_EXIT_{completed.returncode}:{completed.stderr.strip()[:200]}"
    if not stdout:
        return [], ""
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return [], "POWERSHELL_JSON_PARSE_FAILED"
    if isinstance(payload, dict):
        return [payload], ""
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)], ""
    return [], ""


def _process_audit() -> tuple[list[dict[str, Any]], str]:
    command = r"""
Get-CimInstance Win32_Process |
  Where-Object {
    $_.CommandLine -match 'run_db_source_acquisition_scheduler.ps1' -and
    $_.CommandLine -notmatch 'Get-CimInstance'
  } |
  Select-Object ProcessId, CommandLine |
  ConvertTo-Json -Depth 3
"""
    return _powershell_json(command)


def _scheduled_task_audit() -> tuple[list[dict[str, Any]], str]:
    command = r"""
Get-ScheduledTask |
  Where-Object {
    $_.TaskName -match 'Trader|Foreign|Quant|Source|Runtime|AIInfra|KR-Pilot'
  } |
  Select-Object TaskName, TaskPath, State |
  ConvertTo-Json -Depth 3
"""
    return _powershell_json(command)


def _startup_audit() -> list[dict[str, Any]]:
    if not STARTUP_DIR.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(STARTUP_DIR.iterdir()):
        name = path.name
        if not any(token.lower() in name.lower() for token in ("Trader", "Foreign", "Quant", "Source", "Runtime")):
            continue
        text = ""
        try:
            if path.suffix.lower() in {".vbs", ".ps1", ".cmd", ".bat"}:
                for encoding in ("utf-8-sig", "utf-16", "cp949"):
                    try:
                        text = path.read_text(encoding=encoding)
                        break
                    except UnicodeError:
                        continue
        except OSError:
            text = ""
        rows.append(
            {
                "name": name,
                "path": str(path),
                "mentions_db_source_scheduler": int("run_db_source_acquisition_scheduler.ps1" in text),
                "mentions_runtime_scheduler": int("run_runtime_diagnostic_scheduler.ps1" in text),
            }
        )
    return rows


def _repo_sec_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            if path.suffix.lower() not in {".py", ".ps1", ".json", ".env", ".txt", ".md"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            tokens = [token for token in SEC_RISK_TOKENS if token in text]
            if tokens:
                rows.append({"path": str(path.relative_to(ROOT)), "tokens": tokens})
    return rows


def _config_audit(config: dict[str, Any], cooldown_active: bool) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    failures: list[str] = []
    if config.get("default_allow_network") is not False:
        failures.append("default_allow_network must remain false")
    if config.get("sec_live_auto_scheduler_enabled") is not False and cooldown_active:
        failures.append("sec_live_auto_scheduler_enabled must remain false during active SEC cooldown")
    for job in config.get("jobs", []):
        name = str(job.get("name") or "")
        enabled = bool(job.get("enabled"))
        allow_network = bool(job.get("allow_network", config.get("default_allow_network", False)))
        families = [str(value) for value in job.get("families", [])]
        contains_sec = "sec_events" in families
        severity = "INFO"
        if enabled and allow_network and contains_sec and cooldown_active:
            severity = "P0"
            failures.append(f"enabled network scheduler job includes sec_events during active cooldown: {name}")
        findings.append(
            {
                "job": name,
                "enabled": int(enabled),
                "allow_network": int(allow_network),
                "families": families,
                "contains_sec_events": int(contains_sec),
                "severity": severity,
            }
        )
    return findings, failures


def _runner_audit() -> list[str]:
    failures: list[str] = []
    text = RUNNER.read_text(encoding="utf-8") if RUNNER.exists() else ""
    for token in ("sec_live_auto_scheduler_enabled", "SEC_LIVE_AUTO_SCHEDULER_DISABLED"):
        if token not in text:
            failures.append(f"scheduler runner missing containment token: {token}")
    return failures


def _sec_guard_probe(cooldown_active: bool) -> tuple[dict[str, Any], list[str]]:
    if not cooldown_active:
        return {"status": "SKIPPED_NO_ACTIVE_COOLDOWN"}, []
    from tools.db import run_source_acquisition_once as runner

    failures: list[str] = []

    def _blocked(*_args: object, **_kwargs: object) -> dict[str, Any]:
        raise AssertionError("SEC live network function was called during active cooldown")

    original_json = runner._fetch_sec_json_live
    original_text = runner._fetch_sec_text_live
    try:
        runner._fetch_sec_json_live = _blocked  # type: ignore[assignment]
        runner._fetch_sec_text_live = _blocked  # type: ignore[assignment]
        frame, reason = runner._fetch_sec_events_hybrid(("AAPL",), allow_network=True)
    finally:
        runner._fetch_sec_json_live = original_json  # type: ignore[assignment]
        runner._fetch_sec_text_live = original_text  # type: ignore[assignment]
    if reason != "SEC_LIVE_ACCESS_COOLDOWN_ACTIVE" or not frame.empty:
        failures.append(f"SEC live cooldown guard returned unexpected result: reason={reason} rows={len(frame)}")
    return {"status": "CHECKED", "reason": reason, "rows": int(len(frame))}, failures


def main() -> None:
    config = _load_json(CONFIG)
    block_path = ROOT / str(config.get("sec_live_block_state_path") or BLOCK_STATE_DEFAULT.relative_to(ROOT))
    block_state = _load_json(block_path)
    cooldown_active, retry_after = _sec_cooldown_active(block_state)

    failures: list[str] = []
    config_findings, config_failures = _config_audit(config, cooldown_active)
    failures.extend(config_failures)
    failures.extend(_runner_audit())
    guard_probe, guard_failures = _sec_guard_probe(cooldown_active)
    failures.extend(guard_failures)

    processes, process_warning = _process_audit()
    if processes:
        failures.append("DB source acquisition scheduler process is still running")
    scheduled_tasks, task_warning = _scheduled_task_audit()
    startup_entries = _startup_audit()
    repo_inventory = _repo_sec_inventory()

    payload = {
        "status": "PASS" if not failures else "FAIL",
        "checked_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "network_call_run": False,
        "sec_cooldown_active": int(cooldown_active),
        "sec_retry_after_ts": retry_after,
        "sec_block_reason": block_state.get("reason", ""),
        "config_findings": config_findings,
        "running_db_source_scheduler_processes": processes,
        "scheduled_task_inventory": scheduled_tasks,
        "startup_inventory": startup_entries,
        "repo_sec_reference_inventory": repo_inventory,
        "registered_loop_sec_events_note": "registered_loop sec_events uses cached DB evidence and is not proof of live SEC access",
        "sec_guard_probe": guard_probe,
        "warnings": [value for value in (process_warning, task_warning) if value],
        "failures": failures,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
