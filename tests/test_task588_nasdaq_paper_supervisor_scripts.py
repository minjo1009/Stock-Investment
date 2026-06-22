from __future__ import annotations

import unittest
from pathlib import Path
import subprocess


class Task588NasdaqPaperSupervisorScriptsTest(unittest.TestCase):
    def test_supervisor_runs_task588_once_per_market_interval(self) -> None:
        script = Path("scripts/run_task588_nasdaq_paper_loop.ps1").read_text(encoding="utf-8")
        self.assertIn("function Get-NasdaqCalendarStatus", script)
        self.assertIn("nasdaq_market_calendar", script)
        self.assertIn("CalendarCsv", script)
        self.assertIn('"-m", "src.app.task_588_kis_paper_market_hours_runtime_loop"', script)
        self.assertIn('"--iterations", "1"', script)
        self.assertIn("TRADING_MAX_OPEN_ORDERS", script)
        self.assertIn("nasdaq_paper_supervisor_status.csv", script)
        self.assertIn("task_589_paper_eod_slack_report", script)
        self.assertIn("supervisor_slack_alert", script)
        self.assertIn("Invoke-AutomationLifecycleNotice", script)
        self.assertIn("PAPER_AUTOTRADE_LIFECYCLE", script)
        self.assertIn("Paper automation started.", script)
        self.assertIn("Paper automation ended.", script)
        self.assertIn("PowerActionAfterEod", script)
        self.assertIn('[string]$PowerActionAfterEod = "Hibernate"', script)
        self.assertIn("shutdown is disabled by workstation policy; hibernating instead", script)
        self.assertNotIn("shutdown.exe /s", script)

    def test_supervisor_powershell_script_parses(self) -> None:
        script = Path("scripts/run_task588_nasdaq_paper_loop.ps1")
        command = (
            "$errors=$null; "
            f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath '{script}'), [ref]$errors) | Out-Null; "
            "if ($errors) { $errors | ForEach-Object { $_.Message }; exit 1 }"
        )
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_installer_registers_logon_scheduled_task(self) -> None:
        script = Path("scripts/install_task588_nasdaq_paper_loop_task.ps1").read_text(encoding="utf-8")
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn", script)
        self.assertIn("Register-ScheduledTask", script)
        self.assertIn("Install-StartupFallback", script)
        self.assertIn("GetFolderPath(\"Startup\")", script)
        self.assertIn("$TaskName.vbs", script)
        self.assertIn("Encoding Unicode", script)
        self.assertIn("run_task588_nasdaq_paper_loop.ps1", script)
        self.assertIn("RestartCount 3", script)
        self.assertIn('[ValidateSet("None", "Sleep", "Hibernate")]', script)
        self.assertIn('[string]$PowerActionAfterEod = "Hibernate"', script)

    def test_power_schedule_documents_wake_limit(self) -> None:
        script = Path("scripts/install_task588_market_power_schedule.ps1").read_text(encoding="utf-8")
        self.assertIn("-WakeToRun", script)
        self.assertIn("PowerActionAfterEod", script)
        self.assertIn('[ValidateSet("None", "Sleep", "Hibernate")]', script)
        self.assertIn('[string]$PowerActionAfterEod = "Hibernate"', script)
        self.assertIn("Full shutdown is intentionally not used", script)


if __name__ == "__main__":
    unittest.main()
