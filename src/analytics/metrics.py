from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class FullSummary:
    total_pnl: float
    net_pnl: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    trade_count: int


@dataclass(frozen=True)
class PortfolioSummary:
    total_pnl: float
    net_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    trade_count: int
    capital_utilization: float
    max_exposure: float


def summarize_full_results(results: list[Any], *, initial_equity: float) -> FullSummary:
    if not results:
        return FullSummary(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)

    gross = [item.trade.actual_pnl for item in results if item.trade.actual_pnl is not None]
    net = [item.net_pnl for item in results]
    wins = [value for value in net if value > 0]
    losses = [value for value in net if value < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")
    returns = [value / initial_equity for value in net]
    sharpe_ratio = compute_simple_sharpe(returns)

    return FullSummary(
        total_pnl=sum(gross),
        net_pnl=sum(net),
        win_rate=(len(wins) / len(net)) * 100.0,
        profit_factor=profit_factor,
        max_drawdown=compute_max_drawdown_from_pnl(net),
        sharpe_ratio=sharpe_ratio,
        trade_count=len(results),
    )


def summarize_portfolio_results(
    results: list[Any],
    *,
    initial_equity: float,
    max_positions: int,
) -> PortfolioSummary:
    if max_positions <= 0:
        max_positions = 1
    full = summarize_full_results(results, initial_equity=initial_equity)
    total_capital = float(initial_equity) * float(max_positions)
    if total_capital <= 0:
        total_capital = 1.0

    notionals: list[float] = []
    for item in results:
        entry_fill = getattr(item.trade, "entry_fill_price", None)
        qty = getattr(item.trade, "quantity", None)
        if entry_fill is None or qty is None:
            continue
        notionals.append(abs(float(entry_fill) * float(qty)))

    capital_utilization = float(statistics.fmean(notionals) / total_capital) if notionals else 0.0
    max_exposure = float(max(notionals) / total_capital) if notionals else 0.0
    return PortfolioSummary(
        total_pnl=full.total_pnl,
        net_pnl=full.net_pnl,
        max_drawdown=full.max_drawdown,
        sharpe_ratio=full.sharpe_ratio,
        trade_count=full.trade_count,
        capital_utilization=capital_utilization,
        max_exposure=max_exposure,
    )


def analyze_yearly_performance(results: list[Any]) -> pd.DataFrame:
    if not results:
        return pd.DataFrame(columns=["year", "total_pnl", "net_pnl", "trade_count", "win_rate"])
    rows = []
    for item in results:
        rows.append(
            {
                "year": item.trade.entry_time.year,
                "gross_pnl": item.trade.actual_pnl if item.trade.actual_pnl is not None else 0.0,
                "net_pnl": item.net_pnl,
                "win": 1 if item.net_pnl > 0 else 0,
            }
        )
    df = pd.DataFrame(rows)
    grouped = (
        df.groupby("year", as_index=False)
        .agg(total_pnl=("gross_pnl", "sum"), net_pnl=("net_pnl", "sum"), trade_count=("net_pnl", "count"), wins=("win", "sum"))
        .sort_values("year")
    )
    grouped["win_rate"] = (grouped["wins"] / grouped["trade_count"]) * 100.0
    return grouped[["year", "total_pnl", "net_pnl", "trade_count", "win_rate"]]


def analyze_regime_performance(results: list[Any]) -> pd.DataFrame:
    if not results:
        return pd.DataFrame(columns=["regime", "total_pnl", "net_pnl", "trade_count", "win_rate"])
    rows = []
    for item in results:
        rows.append(
            {
                "regime": item.regime,
                "gross_pnl": item.trade.actual_pnl if item.trade.actual_pnl is not None else 0.0,
                "net_pnl": item.net_pnl,
                "win": 1 if item.net_pnl > 0 else 0,
            }
        )
    df = pd.DataFrame(rows)
    grouped = (
        df.groupby("regime", as_index=False)
        .agg(total_pnl=("gross_pnl", "sum"), net_pnl=("net_pnl", "sum"), trade_count=("net_pnl", "count"), wins=("win", "sum"))
        .sort_values("regime")
    )
    grouped["win_rate"] = (grouped["wins"] / grouped["trade_count"]) * 100.0
    return grouped[["regime", "total_pnl", "net_pnl", "trade_count", "win_rate"]]


def compute_max_drawdown_from_pnl(net_pnls: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in net_pnls:
        equity += pnl
        if equity > peak:
            peak = equity
        drawdown = peak - equity
        if drawdown > max_dd:
            max_dd = drawdown
    return max_dd


def compute_simple_sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean_r = statistics.fmean(returns)
    std_r = statistics.pstdev(returns)
    if std_r == 0:
        return 0.0
    return (mean_r / std_r) * math.sqrt(len(returns))
