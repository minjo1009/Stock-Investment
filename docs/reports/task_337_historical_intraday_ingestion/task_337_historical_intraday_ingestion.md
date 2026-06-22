# Task 337: Historical Intraday Ingestion

- Task 336 reinterpretation: `NO_DATA_COVERAGE`
- Covered trade dates: `354`
- Anchored OOS covered trade dates: `30`
- Task 336 readiness: `ready`

## Coverage Summary

| metric | value |
| --- | --- |
| required_trade_dates | 371 |
| covered_trade_count | 354 |
| missing_symbol_count | 0 |
| missing_date_count | 0 |
| insufficient_window_count | 17 |

## Readiness Gate

- each anchored OOS symbol has coverage: `True`
- full historical ingestion still required: `False`

## Top Missing Dates

| symbol | trade_date | coverage_status | bar_count | source |
| --- | --- | --- | --- | --- |
| AVGO | 2021-08-27 | insufficient_window | 54 | ALPACA_HISTORICAL_5M |
| AVGO | 2022-08-18 | insufficient_window | 57 | ALPACA_HISTORICAL_5M |
| AVGO | 2024-05-15 | insufficient_window | 59 | ALPACA_HISTORICAL_5M |
| COST | 2021-10-26 | insufficient_window | 56 | ALPACA_HISTORICAL_5M |
| COST | 2021-10-29 | insufficient_window | 55 | ALPACA_HISTORICAL_5M |
| COST | 2023-06-30 | insufficient_window | 39 | ALPACA_HISTORICAL_5M |
| COST | 2023-09-15 | insufficient_window | 47 | ALPACA_HISTORICAL_5M |
| COST | 2023-09-28 | insufficient_window | 47 | ALPACA_HISTORICAL_5M |
| COST | 2024-05-03 | insufficient_window | 49 | ALPACA_HISTORICAL_5M |
| COST | 2024-11-25 | insufficient_window | 57 | ALPACA_HISTORICAL_5M |
| COST | 2025-05-13 | insufficient_window | 50 | ALPACA_HISTORICAL_5M |
| COST | 2025-05-30 | insufficient_window | 50 | ALPACA_HISTORICAL_5M |
| GOOGL | 2021-07-23 | insufficient_window | 55 | ALPACA_HISTORICAL_5M |
| GOOGL | 2022-03-18 | insufficient_window | 58 | ALPACA_HISTORICAL_5M |
| NFLX | 2024-06-14 | insufficient_window | 58 | ALPACA_HISTORICAL_5M |
| NFLX | 2024-06-17 | insufficient_window | 56 | ALPACA_HISTORICAL_5M |
| NFLX | 2025-06-27 | insufficient_window | 52 | ALPACA_HISTORICAL_5M |

## Conclusion

- Current bottleneck is historical intraday coverage, not strategy edge.
- Task 336 should only be rerun after Phase 2 historical backfill reaches the readiness gate.
