from __future__ import annotations

from src.backtest.build_task572_575_historical_microstructure_backfill import run_all_tasks


def main() -> int:
    artifacts = run_all_tasks()
    decision = artifacts["task575"]["task_575_decision.csv"].iloc[0]
    print(
        "[TASK572_575] "
        f"status={decision['strategy_acceptance_status']} "
        f"next_action={decision['next_action']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
