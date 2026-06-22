from __future__ import annotations

import argparse
import json
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backtest.analysis_stop_loss_structure import _load_price_frames, _trade_rows
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
from backtest.engine_full import run_full_backtest_universe_with_stats, summarize
import backtest.engine_full as engine_full
import risk.policies as risk_policies


ENTRY_POLICY = "LIMITED_CHASE"
STRATEGY = "US_BREAKOUT_V0"

SCENARIOS = [
    {"name": "s4_kis_realistic", "fee_rate": 0.0025, "slippage_rate": 0.0010},
    {"name": "s5_kis_stress_20", "fee_rate": 0.0025, "slippage_rate": 0.0020},
    {"name": "s6_kis_stress_30", "fee_rate": 0.0025, "slippage_rate": 0.0030},
]

TIME_STOP_DAYS = [5, 10, 15, 20, 30]
MFE_TRIGGERS = [0.03, 0.05, 0.07]
GIVEBACK_RATIOS = [0.5, 0.6, 0.7]
MIN_PROFIT_BUFFERS = [0.0, 0.01, 0.02]


@dataclass(frozen=True)
class RiskGridConfig:
    policy_group: str
    risk_policy_name: str
    time_stop_days: int
    mfe_trigger: float
    giveback_ratio: float
    min_profit_buffer: float


@contextmanager
def patched_risk_environment(config: RiskGridConfig):
    old_mfe_trigger = risk_policies.RISK_MFE_TRIGGER
    old_giveback = risk_policies.RISK_GIVEBACK_FRACTION
    old_time_bars = risk_policies.RISK_TIME_STOP_BARS
    old_profit_buffer = risk_policies.RISK_TIME_STOP_MIN_RETURN
    old_engine_mfe_trigger = engine_full.RISK_MFE_TRIGGER
    had_policy = config.risk_policy_name in risk_policies.RISK_POLICIES
    old_policy = risk_policies.RISK_POLICIES.get(config.risk_policy_name)
    try:
        risk_policies.RISK_MFE_TRIGGER = float(config.mfe_trigger)
        risk_policies.RISK_GIVEBACK_FRACTION = float(config.giveback_ratio)
        risk_policies.RISK_TIME_STOP_BARS = int(config.time_stop_days)
        risk_policies.RISK_TIME_STOP_MIN_RETURN = float(config.min_profit_buffer)
        engine_full.RISK_MFE_TRIGGER = float(config.mfe_trigger)

        if config.policy_group == "TIME_STOP_ONLY":
            flags = {"break_even": False, "giveback": False, "time_stop": True}
        elif config.policy_group == "TIME_STOP_MFE":
            flags = {"break_even": True, "giveback": False, "time_stop": True}
        elif config.policy_group == "TIME_STOP_MFE_GIVEBACK":
            flags = {"break_even": True, "giveback": True, "time_stop": True}
        elif config.policy_group == "TIME_STOP_PROFIT_BUFFER":
            flags = {"break_even": False, "giveback": False, "time_stop": True}
        else:
            raise ValueError(f"unknown policy_group={config.policy_group}")

        risk_policies.RISK_POLICIES[config.risk_policy_name] = flags
        yield
    finally:
        risk_policies.RISK_MFE_TRIGGER = old_mfe_trigger
        risk_policies.RISK_GIVEBACK_FRACTION = old_giveback
        risk_policies.RISK_TIME_STOP_BARS = old_time_bars
        risk_policies.RISK_TIME_STOP_MIN_RETURN = old_profit_buffer
        engine_full.RISK_MFE_TRIGGER = old_engine_mfe_trigger
        if had_policy:
            risk_policies.RISK_POLICIES[config.risk_policy_name] = old_policy if old_policy is not None else {}
        else:
            risk_policies.RISK_POLICIES.pop(config.risk_policy_name, None)


def _build_grid() -> list[RiskGridConfig]:
    configs: list[RiskGridConfig] = []

    # TIME_STOP only
    for days in TIME_STOP_DAYS:
        configs.append(
            RiskGridConfig(
                policy_group="TIME_STOP_ONLY",
                risk_policy_name="GRID_TIME_STOP_ONLY",
                time_stop_days=days,
                mfe_trigger=0.03,
                giveback_ratio=0.50,
                min_profit_buffer=0.0,
            )
        )

    # TIME_STOP + MFE trigger
    for days in TIME_STOP_DAYS:
        for mfe_trigger in MFE_TRIGGERS:
            configs.append(
                RiskGridConfig(
                    policy_group="TIME_STOP_MFE",
                    risk_policy_name="GRID_TIME_STOP_MFE",
                    time_stop_days=days,
                    mfe_trigger=mfe_trigger,
                    giveback_ratio=0.50,
                    min_profit_buffer=0.0,
                )
            )

    # TIME_STOP + MFE + giveback
    for days in TIME_STOP_DAYS:
        for mfe_trigger in MFE_TRIGGERS:
            for giveback_ratio in GIVEBACK_RATIOS:
                configs.append(
                    RiskGridConfig(
                        policy_group="TIME_STOP_MFE_GIVEBACK",
                        risk_policy_name="GRID_TIME_STOP_MFE_GIVEBACK",
                        time_stop_days=days,
                        mfe_trigger=mfe_trigger,
                        giveback_ratio=giveback_ratio,
                        min_profit_buffer=0.0,
                    )
                )

    # TIME_STOP + profit buffer
    for days in TIME_STOP_DAYS:
        for min_profit_buffer in MIN_PROFIT_BUFFERS:
            configs.append(
                RiskGridConfig(
                    policy_group="TIME_STOP_PROFIT_BUFFER",
                    risk_policy_name="GRID_TIME_STOP_PROFIT_BUFFER",
                    time_stop_days=days,
                    mfe_trigger=0.03,
                    giveback_ratio=0.50,
                    min_profit_buffer=min_profit_buffer,
                )
            )

    return configs


def _run_one(
    *,
    symbols: list[str],
    base_dir: Path,
    initial_equity: float,
    fee_rate: float,
    slippage_rate: float,
    risk_policy_name: str,
    frames: dict[str, Any],
) -> dict[str, Any]:
    results, _stats = run_full_backtest_universe_with_stats(
        symbols=symbols,
        base_dir=base_dir,
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        entry_policy=ENTRY_POLICY,
        risk_policy=risk_policy_name,
    )
    summary = summarize(results, initial_equity=initial_equity)
    trades = _trade_rows(results, frames)
    stops = trades[trades["stop_hit_flag"] == True].copy() if not trades.empty else trades
    good_then_stop = int((stops["classification"] == "GOOD_THEN_STOP").sum()) if not stops.empty else 0
    return {
        "trade_count": int(summary.trade_count),
        "pf": float(summary.profit_factor),
        "net_pnl": float(summary.net_pnl),
        "mdd": float(summary.max_drawdown),
        "sharpe": float(summary.sharpe_ratio),
        "stop_count": int(len(stops)),
        "good_then_stop": good_then_stop,
    }


def _markdown_report(*, report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 068-B Risk Grid Result")
    lines.append("")
    lines.append("## Setup")
    setup = report["setup"]
    lines.append(f"- strategy: {setup['strategy']}")
    lines.append(f"- execution_policy: {setup['execution_policy']}")
    lines.append(f"- symbols: {len(setup['symbols'])}")
    lines.append(f"- grid_size: {setup['grid_size']}")
    lines.append("")
    lines.append("## Top 5 Candidates (S4 Filtered)")
    lines.append("")
    lines.append("| Rank | Policy | PF(S4) | Net(S4) | MDD(S4) | Sharpe(S4) | GOOD->STOP delta |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|")
    top = report.get("top5", [])
    for idx, row in enumerate(top, start=1):
        s4 = row["scenarios"]["s4_kis_realistic"]
        lines.append(
            f"| {idx} | {row['policy_group']} (t={row['time_stop_days']}, mfe={row['mfe_trigger']}, g={row['giveback_ratio']}, p={row['min_profit_buffer']}) | "
            f"{s4['pf']:.4f} | {s4['net_pnl']:.2f} | {s4['mdd']:.2f} | {s4['sharpe']:.4f} | {s4['good_then_stop_delta_vs_baseline']} |"
        )
    if not top:
        lines.append("| - | no candidate passed filter | - | - | - | - | - |")
    lines.append("")
    lines.append("## Notes")
    lines.append("- Primary filter: PF>=1.1, Net>PnL baseline, MDD<=baseline (S4).")
    lines.append("- Secondary filter: Sharpe improved, GOOD_THEN_STOP reduced.")
    return "\n".join(lines) + "\n"


def _config_key(config: RiskGridConfig) -> str:
    return (
        f"{config.policy_group}|t={config.time_stop_days}|mfe={config.mfe_trigger}"
        f"|g={config.giveback_ratio}|p={config.min_profit_buffer}"
    )


def _load_checkpoint(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 068-B: Risk Layer Parameter Grid (Cost-aware)")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument("--json-out", type=str, default="docs/task_068B_risk_grid.json")
    parser.add_argument("--md-out", type=str, default="docs/task_068B_risk_grid.md")
    parser.add_argument("--checkpoint-out", type=str, default="docs/task_068B_risk_grid.checkpoint.json")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    base_dir = Path(args.data_dir)
    frames = _load_price_frames(symbols, base_dir)
    grid = _build_grid()
    checkpoint_path = Path(args.checkpoint_out)

    baseline_by_scenario: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    if args.resume:
        checkpoint = _load_checkpoint(checkpoint_path)
        if checkpoint is not None:
            baseline_by_scenario = dict(checkpoint.get("baseline", {}))
            rows = list(checkpoint.get("results", []))
            print(f"resume_loaded=true existing_rows={len(rows)} checkpoint={checkpoint_path}", flush=True)

    if not baseline_by_scenario:
        for scenario in SCENARIOS:
            baseline_by_scenario[scenario["name"]] = _run_one(
                symbols=symbols,
                base_dir=base_dir,
                initial_equity=args.initial_equity,
                fee_rate=float(scenario["fee_rate"]),
                slippage_rate=float(scenario["slippage_rate"]),
                risk_policy_name="BASELINE",
                frames=frames,
            )
        _write_checkpoint(
            checkpoint_path,
            {
                "setup": {"symbols": symbols, "data_dir": str(base_dir), "grid_size": len(grid)},
                "baseline": baseline_by_scenario,
                "results": rows,
            },
        )
        print("baseline_ready=true", flush=True)

    done_keys = {str(row.get("config_key")) for row in rows if row.get("config_key")}

    for idx, config in enumerate(grid, start=1):
        key = _config_key(config)
        if key in done_keys:
            continue
        with patched_risk_environment(config):
            row: dict[str, Any] = {
                "config_key": key,
                "policy_group": config.policy_group,
                "time_stop_days": int(config.time_stop_days),
                "mfe_trigger": float(config.mfe_trigger),
                "giveback_ratio": float(config.giveback_ratio),
                "min_profit_buffer": float(config.min_profit_buffer),
                "scenarios": {},
            }
            for scenario in SCENARIOS:
                scenario_name = str(scenario["name"])
                metrics = _run_one(
                    symbols=symbols,
                    base_dir=base_dir,
                    initial_equity=args.initial_equity,
                    fee_rate=float(scenario["fee_rate"]),
                    slippage_rate=float(scenario["slippage_rate"]),
                    risk_policy_name=config.risk_policy_name,
                    frames=frames,
                )
                baseline = baseline_by_scenario[scenario_name]
                metrics["net_pnl_delta_vs_baseline"] = float(metrics["net_pnl"] - baseline["net_pnl"])
                metrics["mdd_delta_vs_baseline"] = float(metrics["mdd"] - baseline["mdd"])
                metrics["sharpe_delta_vs_baseline"] = float(metrics["sharpe"] - baseline["sharpe"])
                metrics["good_then_stop_delta_vs_baseline"] = int(baseline["good_then_stop"] - metrics["good_then_stop"])
                row["scenarios"][scenario_name] = metrics
            rows.append(row)
            done_keys.add(key)
            _write_checkpoint(
                checkpoint_path,
                {
                    "setup": {"symbols": symbols, "data_dir": str(base_dir), "grid_size": len(grid)},
                    "baseline": baseline_by_scenario,
                    "results": rows,
                },
            )
            print(f"progress={idx}/{len(grid)} completed_rows={len(rows)} key={key}", flush=True)

    s4_baseline = baseline_by_scenario["s4_kis_realistic"]
    phase1_candidates = [
        row
        for row in rows
        if row["scenarios"]["s4_kis_realistic"]["pf"] >= 1.1
        and row["scenarios"]["s4_kis_realistic"]["net_pnl"] > s4_baseline["net_pnl"]
        and row["scenarios"]["s4_kis_realistic"]["mdd"] <= s4_baseline["mdd"]
    ]
    phase2_candidates = [
        row
        for row in phase1_candidates
        if row["scenarios"]["s4_kis_realistic"]["sharpe"] > s4_baseline["sharpe"]
        and row["scenarios"]["s4_kis_realistic"]["good_then_stop"] < s4_baseline["good_then_stop"]
    ]

    ranked = sorted(
        phase2_candidates if phase2_candidates else phase1_candidates,
        key=lambda r: (
            r["scenarios"]["s4_kis_realistic"]["pf"],
            r["scenarios"]["s4_kis_realistic"]["net_pnl"],
            -r["scenarios"]["s4_kis_realistic"]["mdd"],
            r["scenarios"]["s4_kis_realistic"]["sharpe"],
        ),
        reverse=True,
    )
    top5 = ranked[:5]

    report = {
        "setup": {
            "strategy": STRATEGY,
            "execution_policy": ENTRY_POLICY,
            "symbols": symbols,
            "data_dir": str(base_dir),
            "initial_equity": float(args.initial_equity),
            "scenarios": SCENARIOS,
            "grid_size": len(grid),
            "grid_axes": {
                "time_stop_days": TIME_STOP_DAYS,
                "mfe_trigger": MFE_TRIGGERS,
                "giveback_ratio": GIVEBACK_RATIOS,
                "min_profit_buffer": MIN_PROFIT_BUFFERS,
            },
        },
        "baseline": baseline_by_scenario,
        "results": rows,
        "filters": {
            "phase1": "PF >= 1.1 and Net PnL > baseline and MDD <= baseline (S4)",
            "phase2": "Sharpe improved and GOOD_THEN_STOP reduced (S4)",
            "phase1_count": len(phase1_candidates),
            "phase2_count": len(phase2_candidates),
        },
        "top5": top5,
    }

    json_text = json.dumps(report, ensure_ascii=True, indent=2)
    json_path = Path(args.json_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json_text, encoding="utf-8")

    md_path = Path(args.md_out)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_markdown_report(report=report), encoding="utf-8")

    print(f"written_json={json_path}")
    print(f"written_md={md_path}")
    print(f"grid_size={len(grid)}")
    print(f"phase1_count={len(phase1_candidates)}")
    print(f"phase2_count={len(phase2_candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
