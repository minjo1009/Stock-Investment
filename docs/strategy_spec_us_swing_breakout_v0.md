# 1. Strategy Overview

- Strategy name: `US Swing Breakout v0`
- Market: `US equities` (NYSE/NASDAQ/AMEX listed common stocks)
- Style: `Swing`
- Philosophy: Trend-following breakout entries with rule-based risk control

# 2. Universe Definition

Use only symbols that satisfy **all** rules below at signal time `t`:

- Security type: US common stock only
- Minimum close price: `Close_t >= 5.00`
- Maximum close price (capital-aware):
  - `Close_t <= max_affordable_price_t`
  - `max_affordable_price_t = equity_t * max_position_weight`
  - `max_position_weight` is defined in Section 8
  - Rationale: at least 1 share must be purchasable under per-position cap
- Liquidity volume filter: `AVG(Volume, 20)_t >= 1,000,000`
- Liquidity turnover filter: `AVG(Close * Volume, 20)_t >= 20,000,000 USD`
- Exclusions:
  - ETF/ETN/Closed-end funds
  - OTC/penny stocks
  - symbols failing above liquidity filters

# 3. Timeframe

- Primary timeframe: `Daily`
- Optional intraday reference: only for execution monitoring (no intraday signal generation in v0)

# 4. Entry Conditions

A long-entry setup exists at day `t` close only when **all** conditions are true.

## 4.1 Trend Filter

- `Close_t > SMA(50)_t`
- `SMA(20)_t > SMA(50)_t`
- `ROC(20)_t > 0`, where `ROC(20)_t = (Close_t / Close_{t-20}) - 1`

## 4.2 Liquidity Filter

- `AVG(Volume, 20)_t >= 1,000,000`
- `AVG(Close * Volume, 20)_t >= 20,000,000 USD`

## 4.3 Breakout Condition

- `Close_t >= BreakoutLevel_t`
- `BreakoutLevel_t = Highest(High, N) over [t-N, ..., t-1]`
- Initial `N = 20`
- The current bar high (`High_t`) is excluded from breakout window to avoid look-ahead

## 4.4 Entry Trigger

If 4.1 + 4.2 + 4.3 are all true at day `t` close, emit one `SignalEvent`:

- `side = BUY`
- `signal_type = ENTRY_BREAKOUT`
- `signal_time = market_close(t)`

# 5. Entry Execution Rules

- Order type: `LIMIT only`
- Submission timing: next regular session (`t+1`) after signal generation
- Reference price:
  - `reference_price = BreakoutLevel_t`
- Entry limit price:
  - `entry_limit_price = reference_price * (1 + 0.001)` (10 bps allowance)
- Gap filter:
  - `gap_pct = (Open_{t+1} - Close_t) / Close_t`
  - If `gap_pct > 0.03`, cancel entry for that signal (`NO_TRADE_GAP_FILTER`)
- Chase prohibition:
  - If order is unfilled and market trades above `entry_limit_price * 1.005` during valid entry window, cancel signal (`NO_CHASE_CANCEL`)
- Signal validity window:
  - Valid for `1` trading day only (`t+1` session)

# 6. Stop Loss Rules

Initial stop is fixed at entry:

- `stop_price = entry_price - k * ATR(14)_t`
- Initial `k = 2.0`
- `ATR(14)_t` is computed on day `t` (signal day) and frozen at entry time

# 7. Exit Rules

Exit signal is emitted when **any** of the following holds:

1. Stop hit
- Condition: `Low_t <= stop_price`
- Signal type: `EXIT_STOP`

2. Trend breakdown
- Condition: `Close_t < SMA(20)_t` for `2` consecutive closes
- Signal type: `EXIT_TREND_BREAK`

3. Max holding period
- Condition: `holding_days > max_holding_days`
- Signal type: `EXIT_TIME`

Execution note for exits in v0:

- Exit orders are also `LIMIT only`
- Default exit reference in v0: current day close (`Close_t`) at signal generation

# 8. Position Sizing

- Sizing framework: fixed-fraction with hard caps
- Per-position capital cap: `position_cap = equity_t * 0.10`
- Quantity rule: `quantity = floor(position_cap / entry_limit_price)`
- Minimum quantity: if `quantity < 1`, do not trade
- Max concurrent positions: `5`
- Max single-symbol weight: `10%` of total equity
- Portfolio gross exposure cap: `<= 50%` in v0

# 9. Signal Contract

Canonical outbound signal payload for strategy-execution handoff:

```python
SignalEvent:
    strategy_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    signal_type: Literal[
        "ENTRY_BREAKOUT",
        "EXIT_STOP",
        "EXIT_TREND_BREAK",
        "EXIT_TIME",
    ]
    signal_time: str
    reference_price: float
    breakout_level: float | None
    stop_price: float | None
    reason: str
```

Contract notes:

- `strategy_id` for this strategy: `us_swing_breakout_v0`
- `breakout_level` is required for `ENTRY_BREAKOUT`
- `stop_price` is required for `ENTRY_BREAKOUT` and `EXIT_STOP`
- `reason` must be machine-readable (`RULE_CODE:details` format preferred)

# 10. Parameters (Initial)

Initial fixed parameters for v0 (no optimization in this task):

- `breakout_window = 20`
- `ma_fast = 20`
- `ma_slow = 50`
- `atr_period = 14`
- `atr_mult = 2.0`
- `max_holding_days = 20`
- `gap_filter_max = 0.03`
- `entry_limit_buffer = 0.001`
- `chase_cancel_threshold = 0.005`

# 11. Risk & Limitations

- Trend regime break can cause rapid losses despite trend filter
- Sideways market can generate whipsaw and repeated false breakouts
- Gap risk can bypass expected entry/exit levels
- Limit-order fill uncertainty can create execution drift
- Broker/local execution mismatch can delay or distort state updates

# 12. Backtest Notes

- Model slippage explicitly (even with limit orders)
- Model limit-fill probability realistically (touch != guaranteed fill)
- Include unfilled signal handling and expired-signal logic
- Compare backtest fills with live execution logs to quantify divergence

# 13. Non-Goals

The following are explicitly out of scope for `US Swing Breakout v0`:

- Mean-reversion strategy behavior
- Scalping or intraday microstructure strategy
- Multi-strategy blending/ensemble logic
- ML/AI-driven signal generation
