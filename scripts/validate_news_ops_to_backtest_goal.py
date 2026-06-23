from __future__ import annotations

import subprocess
import sys


COMMANDS = (
    [sys.executable, "scripts/validate_news_ops_scope_a_b.py"],
    [sys.executable, "scripts/validate_l0_l1_storage.py"],
    [sys.executable, "scripts/validate_l1_l6_consumption_contract.py"],
    [sys.executable, "scripts/validate_source_time_audit.py"],
    [sys.executable, "scripts/validate_diagnostic_backtest_prereqs.py"],
)


def main() -> None:
    for command in COMMANDS:
        subprocess.run(command, check=True)
    print("[TASK3883_SCOPE_A_G_OK] scheduler_to_backtest_goal_validators=PASS no_execution_replay=1")


if __name__ == "__main__":
    main()
