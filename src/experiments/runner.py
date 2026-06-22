from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from analytics.metrics import summarize_full_results
from backtest.engine_full import run_full_backtest_universe_with_stats
from experiments.registry import ExperimentMetrics, ExperimentRecord


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_id: str
    strategy: str
    execution_policy: str
    risk_policy: str
    fee: float
    slippage: float
    universe_name: str
    dataset_version: str


def _decision_from_metrics(*, pf: float, net_pnl: float, sharpe: float) -> str:
    if pf < 1.0 or net_pnl < 0:
        return "FAIL"
    if pf >= 1.2 and sharpe >= 1.0:
        return "PASS"
    return "WARNING"


def run_experiment(
    *,
    config: ExperimentConfig,
    symbols: list[str],
    base_dir: str | Path,
    initial_equity: float,
) -> ExperimentRecord:
    results, _stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=initial_equity,
        fee_rate=config.fee,
        slippage_rate=config.slippage,
        entry_policy=config.execution_policy,
        risk_policy=config.risk_policy,
    )
    summary = summarize_full_results(results, initial_equity=initial_equity)
    metrics = ExperimentMetrics(
        pf=float(summary.profit_factor),
        net_pnl=float(summary.net_pnl),
        mdd=float(summary.max_drawdown),
        sharpe=float(summary.sharpe_ratio),
    )
    return ExperimentRecord(
        experiment_id=config.experiment_id,
        strategy=config.strategy,
        execution_policy=config.execution_policy,
        risk_policy=config.risk_policy,
        fee=float(config.fee),
        slippage=float(config.slippage),
        universe=config.universe_name,
        dataset_version=config.dataset_version,
        metrics=metrics,
        decision=_decision_from_metrics(pf=metrics.pf, net_pnl=metrics.net_pnl, sharpe=metrics.sharpe),
    )
