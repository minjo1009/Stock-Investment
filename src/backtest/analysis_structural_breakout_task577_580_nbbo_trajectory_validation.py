from __future__ import annotations

from src.backtest.build_task577_580_nbbo_trajectory_validation import run_all_tasks


def main() -> int:
    artifacts = run_all_tasks()
    row = artifacts["task580"]["task_580_decision.csv"].iloc[0]
    print(
        "[TASK577_580] "
        f"status={row['strategy_acceptance_status']} "
        f"next={row['next_action']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
