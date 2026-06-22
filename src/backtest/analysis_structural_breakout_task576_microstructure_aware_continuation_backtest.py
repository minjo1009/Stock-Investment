from __future__ import annotations

from src.backtest.build_task576_microstructure_aware_continuation_backtest import build_task576, write_task576


def main() -> int:
    artifacts = build_task576()
    write_task576(artifacts)
    row = artifacts["task_576_decision.csv"].iloc[0]
    print(
        "[TASK576] "
        f"status={row['strategy_acceptance_status']} "
        f"selected={row['selected_rows']} "
        f"best={row['best_candidate_set']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
