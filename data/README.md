# Historical Data Foundation (US Daily OHLCV)

## Data Source
- Primary source: Yahoo Finance (free daily OHLCV)
- Fetch tool: `scripts/fetch_us_daily_data.py`

## Storage Layout
- Path: `data/raw/us_daily/{symbol}.csv`
- Example:
  - `data/raw/us_daily/AAPL.csv`
  - `data/raw/us_daily/MSFT.csv`

## CSV Schema
Required columns:
- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `symbol`

Optional:
- `adj_close`

Conventions:
- Column names use lowercase simple format
- `timestamp` is stored as sortable date text (`YYYY-MM-DD`)
- Rows are sorted ascending by `timestamp`

## Fetch Commands
Default universe:
```bash
python scripts/fetch_us_daily_data.py
```

Custom symbols:
```bash
python scripts/fetch_us_daily_data.py --symbols AAPL MSFT NVDA
```

Custom period:
```bash
python scripts/fetch_us_daily_data.py --period 2y
```

## Loader API
- `load_daily_bars(symbol: str) -> DataFrame`
- `load_universe_daily_bars(symbols: list[str]) -> dict[str, DataFrame]`

## Notes / Limitations
- Free data can include corrections, delayed updates, and occasional missing values.
- `adj_close` availability can vary by source response.
- This foundation is for quick backtest and chart/debug usage, not institutional-grade market data.
