from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_TASK392_PANEL = Path("docs/reports/task_392_macro_vol_theme_regime_overlay/lifecycle_regime_panel.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_393_regime_gated_canonical_continuation_validation")


@dataclass(frozen=True)
class RegimeGatedCanonicalContinuationValidation393Artifacts:
    regime_gated_lifecycle_panel: pd.DataFrame
    gate_split_quality: pd.DataFrame
    gate_monthly_quality: pd.DataFrame
    gate_reinforcement_quality: pd.DataFrame
    gate_reduce_quality: pd.DataFrame
    regime_gate_validation_audit: pd.DataFrame
    task_393_decision: pd.DataFrame


def build_regime_gated_canonical_continuation_validation_393(
    *,
    task392_lifecycle_regime_panel_path: Path = DEFAULT_TASK392_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> RegimeGatedCanonicalContinuationValidation393Artifacts:
    panel = pd.read_csv(task392_lifecycle_regime_panel_path, encoding="utf-8-sig")
    gated_panel = attach_regime_gate_flags(panel)
    split_quality = summarize_gate_split_quality(gated_panel)
    monthly_quality = summarize_gate_monthly_quality(gated_panel)
    reinforcement_quality = summarize_gate_reinforcement_quality(gated_panel)
    reduce_quality = summarize_gate_reduce_quality(gated_panel)
    validation_audit = build_regime_gate_validation_audit(split_quality)
    decision = build_task_393_decision(gated_panel, split_quality, validation_audit)
    artifacts = RegimeGatedCanonicalContinuationValidation393Artifacts(
        regime_gated_lifecycle_panel=gated_panel,
        gate_split_quality=split_quality,
        gate_monthly_quality=monthly_quality,
        gate_reinforcement_quality=reinforcement_quality,
        gate_reduce_quality=reduce_quality,
        regime_gate_validation_audit=validation_audit,
        task_393_decision=decision,
    )
    write_task_393_artifacts(artifacts, out_dir)
    return artifacts


def attach_regime_gate_flags(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    for column in [
        "market_regime",
        "breadth_regime",
        "liquidity_regime",
        "theme_leadership_regime",
        "volatility_regime",
    ]:
        if column not in out.columns:
            out[column] = "unknown"
        out[column] = out[column].fillna("unknown").astype(str)
    out["entry_month"] = pd.to_datetime(out["entry_ts"], errors="coerce", utc=True).dt.strftime("%Y-%m")
    out["ungated_baseline_flag"] = 1
    out["risk_on_gate_flag"] = out["market_regime"].eq("risk_on_broad").astype(int)
    out["liquidity_expansion_gate_flag"] = out["liquidity_regime"].eq("liquidity_expansion").astype(int)
    out["broad_participation_gate_flag"] = out["breadth_regime"].eq("broad_participation").astype(int)
    out["theme_leader_gate_flag"] = out["theme_leadership_regime"].eq("theme_leader").astype(int)
    out["strict_regime_gate_flag"] = (
        out["market_regime"].eq("risk_on_broad")
        & out["breadth_regime"].eq("broad_participation")
        & (out["liquidity_regime"].eq("liquidity_expansion") | out["theme_leadership_regime"].eq("theme_leader"))
    ).astype(int)
    out["risk_off_suppression_gate_flag"] = (
        ~out["market_regime"].eq("risk_off_weak") & ~out["breadth_regime"].eq("weak_breadth")
    ).astype(int)
    out["reconstruction_used_flag"] = 0
    out["symbol_session_inference_used_flag"] = 0
    out["threshold_relaxation_flag"] = 0
    return out


def summarize_gate_split_quality(panel: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for gate_name, column in _gate_columns().items():
        scoped = panel[panel[column].eq(1)].copy()
        summary = _summarize(scoped, ["anchored_split"])
        summary.insert(0, "gate_name", gate_name)
        summary.insert(1, "gate_allowed_count", len(scoped))
        frames.append(summary)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def summarize_gate_monthly_quality(panel: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for gate_name, column in _gate_columns().items():
        scoped = panel[panel[column].eq(1)].copy()
        summary = _summarize(scoped, ["entry_month"])
        summary.insert(0, "gate_name", gate_name)
        frames.append(summary)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def summarize_gate_reinforcement_quality(panel: pd.DataFrame) -> pd.DataFrame:
    scoped_panel = panel.copy()
    scoped_panel["reinforcement_group"] = "entry_only_or_reduce"
    scoped_panel.loc[(scoped_panel["add_flag"] == 1) & (scoped_panel["scale_flag"] == 0), "reinforcement_group"] = "add_only"
    scoped_panel.loc[(scoped_panel["add_flag"] == 1) & (scoped_panel["scale_flag"] == 1), "reinforcement_group"] = "add_scale"
    frames = []
    for gate_name, column in _gate_columns().items():
        scoped = scoped_panel[scoped_panel[column].eq(1)].copy()
        summary = _summarize(scoped, ["anchored_split", "reinforcement_group"])
        summary.insert(0, "gate_name", gate_name)
        frames.append(summary)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def summarize_gate_reduce_quality(panel: pd.DataFrame) -> pd.DataFrame:
    scoped_panel = panel.copy()
    scoped_panel["reduce_group"] = scoped_panel["reduce_flag"].map({1: "reduce_present", 0: "no_reduce"})
    frames = []
    for gate_name, column in _gate_columns().items():
        scoped = scoped_panel[scoped_panel[column].eq(1)].copy()
        summary = _summarize(scoped, ["anchored_split", "reduce_group"])
        summary.insert(0, "gate_name", gate_name)
        frames.append(summary)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_regime_gate_validation_audit(split_quality: pd.DataFrame) -> pd.DataFrame:
    baseline = split_quality[
        split_quality["gate_name"].eq("ungated_baseline") & split_quality["anchored_split"].eq("validation")
    ]
    baseline_row = baseline.iloc[0].to_dict() if not baseline.empty else {}
    rows = []
    for gate_name, group in split_quality.groupby("gate_name", dropna=False):
        validation = group[group["anchored_split"].eq("validation")]
        recent_oos = group[group["anchored_split"].eq("recent_oos")]
        train = group[group["anchored_split"].eq("train")]
        val_row = validation.iloc[0].to_dict() if not validation.empty else {}
        oos_row = recent_oos.iloc[0].to_dict() if not recent_oos.empty else {}
        train_row = train.iloc[0].to_dict() if not train.empty else {}
        validation_avg = _float_or_nan(val_row.get("avg_return_from_entry"))
        baseline_avg = _float_or_nan(baseline_row.get("avg_return_from_entry"))
        validation_pnl = _float_or_nan(val_row.get("compounded_pnl"))
        baseline_pnl = _float_or_nan(baseline_row.get("compounded_pnl"))
        oos_avg = _float_or_nan(oos_row.get("avg_return_from_entry"))
        rows.append(
            {
                "gate_name": gate_name,
                "train_trade_count": int(train_row.get("trade_count", 0) or 0),
                "validation_trade_count": int(val_row.get("trade_count", 0) or 0),
                "recent_oos_trade_count": int(oos_row.get("trade_count", 0) or 0),
                "validation_avg_return": validation_avg,
                "validation_compounded_pnl": validation_pnl,
                "recent_oos_avg_return": oos_avg,
                "recent_oos_compounded_pnl": _float_or_nan(oos_row.get("compounded_pnl")),
                "validation_avg_lift_vs_ungated": validation_avg - baseline_avg,
                "validation_pnl_lift_vs_ungated": validation_pnl - baseline_pnl,
                "validation_collapse_reduced_flag": int(pd.notna(validation_avg) and pd.notna(baseline_avg) and validation_avg > baseline_avg),
                "recent_oos_positive_flag": int(pd.notna(oos_avg) and oos_avg > 0),
                "diagnostic_gate_pass_flag": int(
                    gate_name != "ungated_baseline"
                    and int(val_row.get("trade_count", 0) or 0) >= 100
                    and pd.notna(validation_avg)
                    and pd.notna(baseline_avg)
                    and validation_avg > baseline_avg
                    and pd.notna(oos_avg)
                    and oos_avg > 0
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["diagnostic_gate_pass_flag", "validation_avg_lift_vs_ungated", "recent_oos_avg_return"],
        ascending=[False, False, False],
    )


def build_task_393_decision(
    panel: pd.DataFrame,
    split_quality: pd.DataFrame,
    validation_audit: pd.DataFrame,
) -> pd.DataFrame:
    passing = validation_audit[validation_audit["diagnostic_gate_pass_flag"].eq(1)]
    best = passing.iloc[0].to_dict() if not passing.empty else {}
    baseline_rows = split_quality[split_quality["gate_name"].eq("ungated_baseline")]
    validation_rows = baseline_rows[baseline_rows["anchored_split"].eq("validation")]
    validation_baseline = validation_rows.iloc[0].to_dict() if not validation_rows.empty else {}
    return pd.DataFrame(
        [
            {
                "task_393_verdict": "COMPLETE_PASS",
                "evaluation_status": "REGIME_GATE_DIAGNOSTIC_COMPLETE",
                "canonical_lifecycle_count": len(panel),
                "gate_count": len(_gate_columns()),
                "diagnostic_gate_pass_count": len(passing),
                "best_diagnostic_gate": best.get("gate_name", ""),
                "best_validation_avg_lift_vs_ungated": best.get("validation_avg_lift_vs_ungated", ""),
                "best_recent_oos_avg_return": best.get("recent_oos_avg_return", ""),
                "ungated_validation_trade_count": validation_baseline.get("trade_count", 0),
                "ungated_validation_avg_return": validation_baseline.get("avg_return_from_entry", ""),
                "reconstruction_used_flag": 0,
                "symbol_session_inference_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT",
                "next_priority": "regime_gate_policy_holdout_or_cost_constrained_portfolio_simulation",
            }
        ]
    )


def write_task_393_artifacts(
    artifacts: RegimeGatedCanonicalContinuationValidation393Artifacts,
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.regime_gated_lifecycle_panel.to_csv(out_dir / "regime_gated_lifecycle_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.gate_split_quality.to_csv(out_dir / "gate_split_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.gate_monthly_quality.to_csv(out_dir / "gate_monthly_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.gate_reinforcement_quality.to_csv(out_dir / "gate_reinforcement_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.gate_reduce_quality.to_csv(out_dir / "gate_reduce_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.regime_gate_validation_audit.to_csv(out_dir / "regime_gate_validation_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_393_decision.to_csv(out_dir / "task_393_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 393 - Regime-Gated Canonical Continuation Validation",
        "",
        "## Required Answers",
        "- Did Task 393 use canonical lifecycle stream only? `YES`",
        "- Did Task 393 use reconstruction or symbol/session matching? `NO`",
        "- Did Task 393 relax thresholds or promote themes? `NO`",
        "- Did Task 393 make a deployment claim? `NO`",
        "",
        "## Decision",
        artifacts.task_393_decision.to_csv(index=False).strip(),
        "",
        "## Regime Gate Validation Audit",
        artifacts.regime_gate_validation_audit.to_csv(index=False).strip(),
        "",
        "## Gate Split Quality",
        artifacts.gate_split_quality.to_csv(index=False).strip(),
    ]
    (out_dir / "task_393_regime_gated_canonical_continuation_validation.md").write_text(
        "\n".join(lines),
        encoding="utf-8-sig",
    )


def _summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    columns = keys + [
        "trade_count",
        "win_count",
        "win_rate",
        "avg_return_from_entry",
        "median_return_from_entry",
        "sum_return_from_entry",
        "compounded_pnl",
        "add_rate",
        "scale_rate",
        "add_scale_rate",
        "reduce_rate",
        "avg_bars_held",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    scoped = frame.copy()
    scoped["return_from_entry"] = pd.to_numeric(scoped["return_from_entry"], errors="coerce").fillna(0.0)
    scoped["positive_return_flag"] = (scoped["return_from_entry"] > 0).astype(int)
    grouped = scoped.groupby(keys, dropna=False)
    summary = grouped.agg(
        trade_count=("lifecycle_id", "nunique"),
        win_count=("positive_return_flag", "sum"),
        win_rate=("positive_return_flag", "mean"),
        avg_return_from_entry=("return_from_entry", "mean"),
        median_return_from_entry=("return_from_entry", "median"),
        sum_return_from_entry=("return_from_entry", "sum"),
        compounded_pnl=("return_from_entry", _compound_returns),
        add_rate=("add_flag", "mean"),
        scale_rate=("scale_flag", "mean"),
        add_scale_rate=("add_scale_flag", "mean"),
        reduce_rate=("reduce_flag", "mean"),
        avg_bars_held=("bars_held", "mean"),
    ).reset_index()
    return summary


def _compound_returns(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0)
    return float((1.0 + values).prod() - 1.0)


def _gate_columns() -> dict[str, str]:
    return {
        "ungated_baseline": "ungated_baseline_flag",
        "risk_on_gate": "risk_on_gate_flag",
        "liquidity_expansion_gate": "liquidity_expansion_gate_flag",
        "broad_participation_gate": "broad_participation_gate_flag",
        "theme_leader_gate": "theme_leader_gate_flag",
        "strict_regime_gate": "strict_regime_gate_flag",
        "risk_off_suppression_gate": "risk_off_suppression_gate_flag",
    }


def _float_or_nan(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 393 regime-gated canonical continuation validation.")
    parser.add_argument("--task392-panel", type=Path, default=DEFAULT_TASK392_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_regime_gated_canonical_continuation_validation_393(
        task392_lifecycle_regime_panel_path=args.task392_panel,
        out_dir=args.out_dir,
    )
    row = artifacts.task_393_decision.iloc[0]
    print(
        "[TASK393] "
        f"status={row['evaluation_status']} lifecycles={row['canonical_lifecycle_count']} "
        f"best_gate={row['best_diagnostic_gate']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
