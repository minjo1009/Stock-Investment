from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_TASK395_PANEL = Path("docs/reports/task_395_forward_live_regime_detectability/forward_live_lifecycle_regime_panel.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_396_forward_live_cost_constrained_validation")


@dataclass(frozen=True)
class ForwardLiveCostConstrainedValidation396Artifacts:
    cost_model_assumptions: pd.DataFrame
    cost_constrained_lifecycle_panel: pd.DataFrame
    cost_constrained_policy_quality: pd.DataFrame
    cost_constrained_split_quality: pd.DataFrame
    cost_constrained_transition_quality: pd.DataFrame
    forward_live_degradation_audit: pd.DataFrame
    capital_exposure_audit: pd.DataFrame
    task_396_decision: pd.DataFrame


def build_forward_live_cost_constrained_validation_396(
    *,
    task395_lifecycle_panel_path: Path = DEFAULT_TASK395_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
    max_concurrent_positions: int = 20,
) -> ForwardLiveCostConstrainedValidation396Artifacts:
    panel = pd.read_csv(task395_lifecycle_panel_path, encoding="utf-8-sig")
    assumptions = build_cost_model_assumptions(max_concurrent_positions=max_concurrent_positions)
    cost_panel = build_cost_constrained_lifecycle_panel(panel, max_concurrent_positions=max_concurrent_positions)
    policy_quality = summarize_cost_policy_quality(cost_panel)
    split_quality = summarize_cost_split_quality(cost_panel)
    transition_quality = summarize_cost_transition_quality(cost_panel)
    degradation = build_forward_live_degradation_audit(cost_panel, split_quality)
    exposure = build_capital_exposure_audit(cost_panel)
    decision = build_task_396_decision(cost_panel, split_quality, transition_quality, degradation, exposure)
    artifacts = ForwardLiveCostConstrainedValidation396Artifacts(
        cost_model_assumptions=assumptions,
        cost_constrained_lifecycle_panel=cost_panel,
        cost_constrained_policy_quality=policy_quality,
        cost_constrained_split_quality=split_quality,
        cost_constrained_transition_quality=transition_quality,
        forward_live_degradation_audit=degradation,
        capital_exposure_audit=exposure,
        task_396_decision=decision,
    )
    write_task_396_artifacts(artifacts, out_dir)
    return artifacts


def build_cost_model_assumptions(*, max_concurrent_positions: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"assumption": "round_trip_commission_bps", "value": 5.0},
            {"assumption": "round_trip_slippage_bps", "value": 7.5},
            {"assumption": "add_transaction_cost_bps", "value": 4.0},
            {"assumption": "scale_transaction_cost_bps", "value": 6.0},
            {"assumption": "reduce_transaction_cost_bps", "value": 3.0},
            {"assumption": "volatility_penalty_multiplier", "value": 0.10},
            {"assumption": "spread_penalty_bps_low_liquidity", "value": 5.0},
            {"assumption": "max_concurrent_positions", "value": float(max_concurrent_positions)},
            {"assumption": "position_sizing_mode", "value": "equal_slot_weight"},
            {"assumption": "hindsight_strict_role", "value": "upper_bound_only"},
        ]
    )


def build_cost_constrained_lifecycle_panel(panel: pd.DataFrame, *, max_concurrent_positions: int) -> pd.DataFrame:
    base = _prepare_panel(panel)
    frames = []
    for policy_name in ["ungated_baseline", "hindsight_strict_upper_bound", "forward_live_strict", "cost_constrained_forward_live_strict"]:
        scoped = base.copy()
        scoped["policy_name"] = policy_name
        if policy_name == "ungated_baseline":
            scoped["policy_gate_flag"] = 1
        elif policy_name == "hindsight_strict_upper_bound":
            scoped["policy_gate_flag"] = scoped["hindsight_strict_regime_gate_flag"]
        else:
            scoped["policy_gate_flag"] = scoped["forward_live_strict_regime_gate_flag"]
        scoped["capital_slot_allowed_flag"] = 1
        if policy_name == "cost_constrained_forward_live_strict":
            scoped = _apply_capital_slots(scoped, max_concurrent_positions=max_concurrent_positions)
        scoped["policy_accepted_lifecycle_flag"] = (
            (scoped["policy_gate_flag"] == 1) & (scoped["capital_slot_allowed_flag"] == 1)
        ).astype(int)
        scoped["net_return_from_entry"] = scoped["return_from_entry"] - scoped["estimated_total_cost"]
        scoped["post_cost_positive_return_flag"] = (scoped["net_return_from_entry"] > 0).astype(int)
        scoped["cost_model_applied_flag"] = 1
        scoped["full_day_regime_used_flag"] = 0 if policy_name != "hindsight_strict_upper_bound" else 1
        scoped["future_outcome_used_for_regime_flag"] = 0
        scoped["symbol_session_inference_used_flag"] = 0
        scoped["deployment_claim_flag"] = 0
        frames.append(scoped)
    return pd.concat(frames, ignore_index=True)


def summarize_cost_policy_quality(panel: pd.DataFrame) -> pd.DataFrame:
    accepted = panel[panel["policy_accepted_lifecycle_flag"].eq(1)].copy()
    return _summarize(accepted, ["policy_name"])


def summarize_cost_split_quality(panel: pd.DataFrame) -> pd.DataFrame:
    accepted = panel[panel["policy_accepted_lifecycle_flag"].eq(1)].copy()
    summary = _summarize(accepted, ["policy_name", "anchored_split"])
    total = panel.groupby(["policy_name", "anchored_split"], dropna=False).agg(
        candidate_lifecycle_count=("lifecycle_id", "nunique"),
        accepted_lifecycle_count=("policy_accepted_lifecycle_flag", "sum"),
        capital_blocked_count=("capital_slot_allowed_flag", lambda s: int((s == 0).sum())),
    ).reset_index()
    out = total.merge(summary, on=["policy_name", "anchored_split"], how="left")
    out["trade_reduction_rate"] = 1.0 - out["accepted_lifecycle_count"] / out["candidate_lifecycle_count"].replace(0, pd.NA)
    return out


def summarize_cost_transition_quality(panel: pd.DataFrame) -> pd.DataFrame:
    accepted = panel[panel["policy_accepted_lifecycle_flag"].eq(1)].copy()
    accepted["reinforcement_group"] = "entry_only_or_reduce"
    accepted.loc[(accepted["add_flag"] == 1) & (accepted["scale_flag"] == 0), "reinforcement_group"] = "add_only"
    accepted.loc[(accepted["add_flag"] == 1) & (accepted["scale_flag"] == 1), "reinforcement_group"] = "add_scale"
    return _summarize(accepted, ["policy_name", "anchored_split", "reinforcement_group"])


def build_forward_live_degradation_audit(panel: pd.DataFrame, split_quality: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["train", "validation", "recent_oos"]:
        hindsight = _split_row(split_quality, "hindsight_strict_upper_bound", split)
        forward = _split_row(split_quality, "forward_live_strict", split)
        costed = _split_row(split_quality, "cost_constrained_forward_live_strict", split)
        rows.append(
            {
                "anchored_split": split,
                "hindsight_strict_trade_count": int(hindsight.get("trade_count", 0) or 0),
                "forward_live_trade_count": int(forward.get("trade_count", 0) or 0),
                "cost_constrained_trade_count": int(costed.get("trade_count", 0) or 0),
                "hindsight_net_avg_return": _float_or_nan(hindsight.get("avg_net_return_from_entry")),
                "forward_live_net_avg_return": _float_or_nan(forward.get("avg_net_return_from_entry")),
                "cost_constrained_net_avg_return": _float_or_nan(costed.get("avg_net_return_from_entry")),
                "forward_live_degradation_vs_hindsight": _float_or_nan(hindsight.get("avg_net_return_from_entry")) - _float_or_nan(forward.get("avg_net_return_from_entry")),
                "capital_constraint_degradation_vs_forward_live": _float_or_nan(forward.get("avg_net_return_from_entry")) - _float_or_nan(costed.get("avg_net_return_from_entry")),
            }
        )
    return pd.DataFrame(rows)


def build_capital_exposure_audit(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for policy_name, group in panel.groupby("policy_name", dropna=False):
        scoped = group[group["policy_gate_flag"].eq(1)].copy()
        accepted = scoped[scoped["policy_accepted_lifecycle_flag"].eq(1)]
        by_time = scoped.groupby("entry_ts_dt").agg(
            gated_count=("lifecycle_id", "nunique"),
            accepted_count=("policy_accepted_lifecycle_flag", "sum"),
            capital_blocked_count=("capital_slot_allowed_flag", lambda s: int((s == 0).sum())),
        ).reset_index()
        rows.append(
            {
                "policy_name": policy_name,
                "gated_lifecycle_count": len(scoped),
                "accepted_lifecycle_count": len(accepted),
                "capital_blocked_count": int((scoped["capital_slot_allowed_flag"] == 0).sum()),
                "max_concurrent_gated_entries": int(by_time["gated_count"].max()) if not by_time.empty else 0,
                "max_concurrent_accepted_entries": int(by_time["accepted_count"].max()) if not by_time.empty else 0,
                "avg_concurrent_gated_entries": float(by_time["gated_count"].mean()) if not by_time.empty else 0.0,
                "avg_concurrent_accepted_entries": float(by_time["accepted_count"].mean()) if not by_time.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def build_task_396_decision(
    panel: pd.DataFrame,
    split_quality: pd.DataFrame,
    transition_quality: pd.DataFrame,
    degradation: pd.DataFrame,
    exposure: pd.DataFrame,
) -> pd.DataFrame:
    baseline_val = _split_row(split_quality, "ungated_baseline", "validation")
    cost_val = _split_row(split_quality, "cost_constrained_forward_live_strict", "validation")
    cost_oos = _split_row(split_quality, "cost_constrained_forward_live_strict", "recent_oos")
    add_scale_val = _transition_row(transition_quality, "cost_constrained_forward_live_strict", "validation", "add_scale")
    exposure_row = exposure[exposure["policy_name"].eq("cost_constrained_forward_live_strict")]
    exposure_data = exposure_row.iloc[0].to_dict() if not exposure_row.empty else {}
    baseline_avg = _float_or_nan(baseline_val.get("avg_net_return_from_entry"))
    cost_val_avg = _float_or_nan(cost_val.get("avg_net_return_from_entry"))
    cost_oos_avg = _float_or_nan(cost_oos.get("avg_net_return_from_entry"))
    add_scale_avg = _float_or_nan(add_scale_val.get("avg_net_return_from_entry"))
    viability = int(
        pd.notna(cost_val_avg)
        and pd.notna(baseline_avg)
        and cost_val_avg > baseline_avg
        and pd.notna(cost_oos_avg)
        and cost_oos_avg > 0
        and pd.notna(add_scale_avg)
        and add_scale_avg > 0
        and int(cost_val.get("trade_count", 0) or 0) >= 100
    )
    return pd.DataFrame(
        [
            {
                "task_396_verdict": "COMPLETE_PASS",
                "evaluation_status": "COST_CONSTRAINED_FORWARD_LIVE_DIAGNOSTIC_COMPLETE",
                "canonical_lifecycle_count": int(panel["lifecycle_id"].nunique()),
                "cost_constrained_validation_trade_count": int(cost_val.get("trade_count", 0) or 0),
                "cost_constrained_validation_net_avg_return": cost_val_avg,
                "cost_constrained_recent_oos_net_avg_return": cost_oos_avg,
                "cost_constrained_validation_add_scale_net_avg_return": add_scale_avg,
                "baseline_validation_net_avg_return": baseline_avg,
                "max_concurrent_accepted_entries": exposure_data.get("max_concurrent_accepted_entries", 0),
                "capital_blocked_count": exposure_data.get("capital_blocked_count", 0),
                "post_cost_viability_flag": viability,
                "full_day_regime_used_for_realistic_policy_flag": 0,
                "symbol_session_inference_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "COST_CONSTRAINED_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT",
                "next_priority": "portfolio_path_equity_curve_and_live_regime_monitoring",
            }
        ]
    )


def write_task_396_artifacts(artifacts: ForwardLiveCostConstrainedValidation396Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.cost_model_assumptions.to_csv(out_dir / "cost_model_assumptions.csv", index=False, encoding="utf-8-sig")
    artifacts.cost_constrained_lifecycle_panel.to_csv(out_dir / "cost_constrained_lifecycle_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.cost_constrained_policy_quality.to_csv(out_dir / "cost_constrained_policy_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.cost_constrained_split_quality.to_csv(out_dir / "cost_constrained_split_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.cost_constrained_transition_quality.to_csv(out_dir / "cost_constrained_transition_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.forward_live_degradation_audit.to_csv(out_dir / "forward_live_degradation_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.capital_exposure_audit.to_csv(out_dir / "capital_exposure_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_396_decision.to_csv(out_dir / "task_396_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 396 - Forward-Live Gate Degradation & Cost-Constrained Validation",
        "",
        "## Required Answers",
        "- Did Task 396 use forward-live regime for realistic policy? `YES`",
        "- Did Task 396 use hindsight strict as anything other than upper bound? `NO`",
        "- Did Task 396 use reconstruction or symbol/session matching? `NO`",
        "- Did Task 396 make a deployment claim? `NO`",
        "",
        "## Decision",
        artifacts.task_396_decision.to_csv(index=False).strip(),
        "",
        "## Cost Model Assumptions",
        artifacts.cost_model_assumptions.to_csv(index=False).strip(),
        "",
        "## Split Quality",
        artifacts.cost_constrained_split_quality.to_csv(index=False).strip(),
        "",
        "## Degradation Audit",
        artifacts.forward_live_degradation_audit.to_csv(index=False).strip(),
        "",
        "## Capital Exposure Audit",
        artifacts.capital_exposure_audit.to_csv(index=False).strip(),
    ]
    (out_dir / "task_396_forward_live_cost_constrained_validation.md").write_text("\n".join(lines), encoding="utf-8-sig")


def _prepare_panel(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["entry_ts_dt"] = pd.to_datetime(out["entry_ts"], errors="coerce", utc=True)
    out = out.sort_values(["entry_ts_dt", "lifecycle_id"]).reset_index(drop=True)
    for column in ["add_flag", "scale_flag", "reduce_flag", "add_scale_flag", "hindsight_strict_regime_gate_flag", "forward_live_strict_regime_gate_flag"]:
        if column not in out.columns:
            out[column] = 0
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0).astype(int)
    for column in ["return_from_entry", "forward_live_avg_intraday_range", "forward_live_liquidity_ratio"]:
        if column not in out.columns:
            out[column] = 0.0
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0.0)
    low_liquidity = out["forward_live_liquidity_ratio"] < 0.90
    out["base_round_trip_cost"] = 0.00125
    out["add_cost"] = out["add_flag"] * 0.00040
    out["scale_cost"] = out["scale_flag"] * 0.00060
    out["reduce_cost"] = out["reduce_flag"] * 0.00030
    out["volatility_penalty"] = out["forward_live_avg_intraday_range"].clip(lower=0.0) * 0.10
    out["spread_penalty"] = low_liquidity.astype(float) * 0.00050
    out["estimated_total_cost"] = (
        out["base_round_trip_cost"]
        + out["add_cost"]
        + out["scale_cost"]
        + out["reduce_cost"]
        + out["volatility_penalty"]
        + out["spread_penalty"]
    )
    return out


def _apply_capital_slots(frame: pd.DataFrame, *, max_concurrent_positions: int) -> pd.DataFrame:
    out = frame.copy()
    out["capital_slot_allowed_flag"] = 0
    eligible = out[out["policy_gate_flag"].eq(1)].copy()
    allowed_index = (
        eligible.sort_values(["entry_ts_dt", "forward_live_theme_rank", "lifecycle_id"])
        .groupby("entry_ts_dt", dropna=False)
        .head(max_concurrent_positions)
        .index
    )
    out.loc[allowed_index, "capital_slot_allowed_flag"] = 1
    out.loc[out["policy_gate_flag"].eq(0), "capital_slot_allowed_flag"] = 0
    return out


def _summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    columns = keys + [
        "trade_count",
        "win_count",
        "win_rate",
        "avg_gross_return_from_entry",
        "avg_net_return_from_entry",
        "median_net_return_from_entry",
        "sum_net_return_from_entry",
        "compounded_net_pnl",
        "avg_estimated_total_cost",
        "add_rate",
        "scale_rate",
        "add_scale_rate",
        "reduce_rate",
        "avg_bars_held",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    scoped = frame.copy()
    scoped["post_cost_positive_return_flag"] = (scoped["net_return_from_entry"] > 0).astype(int)
    return scoped.groupby(keys, dropna=False).agg(
        trade_count=("lifecycle_id", "nunique"),
        win_count=("post_cost_positive_return_flag", "sum"),
        win_rate=("post_cost_positive_return_flag", "mean"),
        avg_gross_return_from_entry=("return_from_entry", "mean"),
        avg_net_return_from_entry=("net_return_from_entry", "mean"),
        median_net_return_from_entry=("net_return_from_entry", "median"),
        sum_net_return_from_entry=("net_return_from_entry", "sum"),
        compounded_net_pnl=("net_return_from_entry", _compound_returns),
        avg_estimated_total_cost=("estimated_total_cost", "mean"),
        add_rate=("add_flag", "mean"),
        scale_rate=("scale_flag", "mean"),
        add_scale_rate=("add_scale_flag", "mean"),
        reduce_rate=("reduce_flag", "mean"),
        avg_bars_held=("bars_held", "mean"),
    ).reset_index().reindex(columns=columns)


def _split_row(frame: pd.DataFrame, policy_name: str, split: str) -> dict[str, object]:
    rows = frame[frame["policy_name"].eq(policy_name) & frame["anchored_split"].eq(split)]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def _transition_row(frame: pd.DataFrame, policy_name: str, split: str, reinforcement_group: str) -> dict[str, object]:
    rows = frame[
        frame["policy_name"].eq(policy_name)
        & frame["anchored_split"].eq(split)
        & frame["reinforcement_group"].eq(reinforcement_group)
    ]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def _compound_returns(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0)
    return float((1.0 + values).prod() - 1.0)


def _float_or_nan(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 396 forward-live cost-constrained validation.")
    parser.add_argument("--task395-panel", type=Path, default=DEFAULT_TASK395_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--max-concurrent-positions", type=int, default=20)
    args = parser.parse_args()
    artifacts = build_forward_live_cost_constrained_validation_396(
        task395_lifecycle_panel_path=args.task395_panel,
        out_dir=args.out_dir,
        max_concurrent_positions=args.max_concurrent_positions,
    )
    row = artifacts.task_396_decision.iloc[0]
    print(
        "[TASK396] "
        f"status={row['evaluation_status']} viability={row['post_cost_viability_flag']} "
        f"val_net={row['cost_constrained_validation_net_avg_return']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
