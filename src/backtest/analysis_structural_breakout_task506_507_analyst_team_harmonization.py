from __future__ import annotations

from src.backtest.build_task506_507_analyst_team_harmonization import (
    build_task506_analyst_team_source_audit,
    build_task507_analyst_harmonized_trading_logic,
)


def main() -> None:
    build_task506_analyst_team_source_audit()
    build_task507_analyst_harmonized_trading_logic()


if __name__ == "__main__":
    main()
