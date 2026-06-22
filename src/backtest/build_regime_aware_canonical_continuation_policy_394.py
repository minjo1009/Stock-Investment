from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_TASK392_PANEL = Path("docs/reports/task_392_macro_vol_theme_regime_overlay/lifecycle_regime_panel.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_394_regime_aware_canonical_continuation_policy")


@dataclass(frozen=True)
class RegimeAwareCanonicalContinuationPolicy394Artifacts:
    regime_policy_rulebook: pd.DataFrame
    policy_lifecycle_simulation_panel: pd.DataFrame
    policy_split_quality: pd.DataFrame
    policy_monthly_quality: pd.DataFrame
    policy_transition_audit: pd.DataFrame
    policy_weak_regime_audit: pd.DataFrame
    policy_validation_audit: pd.DataFrame
    task_394_decision: pd.DataFrame


def build_regime_aware_canonical_continuation_policy_394(
    *,
    task392_lifecycle_regime_panel_path: Path = DEFAULT_TASK392_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> RegimeAwareCanonicalContinuationPolicy394Artifacts:
    panel = pd.read_csv(task392_lifecycle_regime_panel_path, encoding="utf-8-sig")
    rulebook = build_regime_policy_rulebook()
    simulation = build_policy_lifecycle_simulation_panel(panel)
    split_quality = summarize_policy_split_quality(simulation)
    monthly_quality = summarize_policy_monthly_quality(simulation)
    transition_audit = summarize_policy_transition_audit(simulation)
    weak_regime_audit = summarize_policy_weak_regime_audit(simulation)
    validation_audit = build_policy_validation_audit(split_quality, transition_audit, weak_regime_audit)
    decision = build_task_394_decision(simulation, validation_audit)
    artifacts = RegimeAwareCanonicalContinuationPolicy394Artifacts(
        regime_policy_rulebook=rulebook,
        policy_lifecycle_simulation_panel=simulation,
        policy_split_quality=split_quality,
        policy_monthly_quality=monthly_quality,
        policy_transition_audit=transition_audit,
        policy_weak_regime_audit=weak_regime_audit,
        policy_validation_audit=validation_audit,
        task_394_decision=decision,
    )
    write_task_394_artifacts(artifacts, out_dir)
    return artifacts


def build_regime_policy_rulebook() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "policy_state": "aggressive_continuation",
                "condition": "risk_on_broad + broad_participation + liquidity_expansion_or_theme_leader",
                "entry_policy": "allow",
                "add_policy": "allow",
                "scale_policy": "allow",
                "reduce_policy": "normal",
            },
            {
                "policy_state": "risk_on_constrained",
                "condition": "risk_on_broad without strict confirmation",
                "entry_policy": "allow_entry_only",
                "add_policy": "block",
                "scale_policy": "block",
                "reduce_policy": "strengthened",
            },
            {
                "policy_state": "mixed_defensive",
                "condition": "mixed_market or mixed_breadth",
                "entry_policy": "block_for_continuation",
                "add_policy": "block",
                "scale_policy": "block",
                "reduce_policy": "strengthened",
            },
            {
                "policy_state": "risk_off_blocked",
                "condition": "risk_off_weak or weak_breadth",
                "entry_policy": "block",
                "add_policy": "block",
                "scale_policy": "block",
                "reduce_policy": "strengthened",
            },
        ]
    )


def build_policy_lifecycle_simulation_panel(panel: pd.DataFrame) -> pd.DataFrame:
    base = _prepare_panel(panel)
    frames = []
    for policy_name in _policy_names():
        scoped = base.copy()
        scoped["policy_name"] = policy_name
        scoped = _attach_policy_permissions(scoped, policy_name)
        scoped["policy_transition_violation_flag"] = (
            ((scoped["add_flag"] == 1) & (scoped["policy_add_allowed_flag"] == 0))
            | ((scoped["scale_flag"] == 1) & (scoped["policy_scale_allowed_flag"] == 0))
        ).astype(int)
        scoped["policy_accepted_lifecycle_flag"] = (
            (scoped["policy_entry_allowed_flag"] == 1) & (scoped["policy_transition_violation_flag"] == 0)
        ).astype(int)
        scoped["blocked_weak_regime_flag"] = (
            (scoped["weak_regime_flag"] == 1) & (scoped["policy_accepted_lifecycle_flag"] == 0)
        ).astype(int)
        scoped["policy_simulation_mode"] = "canonical_lifecycle_filter_only_no_repricing"
        scoped["reconstruction_used_flag"] = 0
        scoped["symbol_session_inference_used_flag"] = 0
        scoped["threshold_relaxation_flag"] = 0
        frames.append(scoped)
    return pd.concat(frames, ignore_index=True)


def summarize_policy_split_quality(simulation: pd.DataFrame) -> pd.DataFrame:
    accepted = simulation[simulation["policy_accepted_lifecycle_flag"].eq(1)].copy()
    summary = _summarize(accepted, ["policy_name", "anchored_split"])
    total = simulation.groupby(["policy_name", "anchored_split"], dropna=False).agg(
        candidate_lifecycle_count=("lifecycle_id", "nunique"),
        blocked_lifecycle_count=("policy_accepted_lifecycle_flag", lambda s: int((s == 0).sum())),
        transition_violation_count=("policy_transition_violation_flag", "sum"),
        weak_regime_blocked_count=("blocked_weak_regime_flag", "sum"),
    ).reset_index()
    out = total.merge(summary, on=["policy_name", "anchored_split"], how="left")
    out["accepted_lifecycle_count"] = out["trade_count"].fillna(0).astype(int)
    out["trade_reduction_rate"] = 1.0 - out["accepted_lifecycle_count"] / out["candidate_lifecycle_count"].replace(0, pd.NA)
    return out


def summarize_policy_monthly_quality(simulation: pd.DataFrame) -> pd.DataFrame:
    accepted = simulation[simulation["policy_accepted_lifecycle_flag"].eq(1)].copy()
    return _summarize(accepted, ["policy_name", "entry_month"])


def summarize_policy_transition_audit(simulation: pd.DataFrame) -> pd.DataFrame:
    accepted = simulation[simulation["policy_accepted_lifecycle_flag"].eq(1)].copy()
    accepted["reinforcement_group"] = "entry_only_or_reduce"
    accepted.loc[(accepted["add_flag"] == 1) & (accepted["scale_flag"] == 0), "reinforcement_group"] = "add_only"
    accepted.loc[(accepted["add_flag"] == 1) & (accepted["scale_flag"] == 1), "reinforcement_group"] = "add_scale"
    return _summarize(accepted, ["policy_name", "anchored_split", "reinforcement_group"])


def summarize_policy_weak_regime_audit(simulation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (policy_name, split), group in simulation.groupby(["policy_name", "anchored_split"], dropna=False):
        weak = group[group["weak_regime_flag"].eq(1)]
        accepted_weak = weak[weak["policy_accepted_lifecycle_flag"].eq(1)]
        blocked_weak = weak[weak["policy_accepted_lifecycle_flag"].eq(0)]
        rows.append(
            {
                "policy_name": policy_name,
                "anchored_split": split,
                "weak_regime_candidate_count": len(weak),
                "weak_regime_accepted_count": len(accepted_weak),
                "weak_regime_blocked_count": len(blocked_weak),
                "weak_regime_block_rate": len(blocked_weak) / len(weak) if len(weak) else 0.0,
                "accepted_weak_avg_return": float(accepted_weak["return_from_entry"].mean()) if len(accepted_weak) else float("nan"),
                "blocked_weak_avg_return": float(blocked_weak["return_from_entry"].mean()) if len(blocked_weak) else float("nan"),
                "blocked_weak_compounded_pnl": _compound_returns(blocked_weak["return_from_entry"]) if len(blocked_weak) else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def build_policy_validation_audit(
    split_quality: pd.DataFrame,
    transition_audit: pd.DataFrame,
    weak_regime_audit: pd.DataFrame,
) -> pd.DataFrame:
    baseline = _split_row(split_quality, "ungated_baseline", "validation")
    baseline_add_scale = _transition_row(transition_audit, "ungated_baseline", "validation", "add_scale")
    rows = []
    for policy_name in sorted(split_quality["policy_name"].dropna().unique()):
        validation = _split_row(split_quality, policy_name, "validation")
        recent_oos = _split_row(split_quality, policy_name, "recent_oos")
        add_scale = _transition_row(transition_audit, policy_name, "validation", "add_scale")
        weak = _weak_row(weak_regime_audit, policy_name, "validation")
        val_avg = _float_or_nan(validation.get("avg_return_from_entry"))
        base_avg = _float_or_nan(baseline.get("avg_return_from_entry"))
        val_pnl = _float_or_nan(validation.get("compounded_pnl"))
        base_pnl = _float_or_nan(baseline.get("compounded_pnl"))
        oos_avg = _float_or_nan(recent_oos.get("avg_return_from_entry"))
        add_scale_avg = _float_or_nan(add_scale.get("avg_return_from_entry"))
        baseline_add_scale_avg = _float_or_nan(baseline_add_scale.get("avg_return_from_entry"))
        trade_count = int(validation.get("accepted_lifecycle_count", 0) or 0)
        reduction = _float_or_nan(validation.get("trade_reduction_rate"))
        rows.append(
            {
                "policy_name": policy_name,
                "validation_trade_count": trade_count,
                "validation_trade_reduction_rate": reduction,
                "validation_avg_return": val_avg,
                "validation_compounded_pnl": val_pnl,
                "recent_oos_avg_return": oos_avg,
                "recent_oos_compounded_pnl": _float_or_nan(recent_oos.get("compounded_pnl")),
                "validation_avg_lift_vs_ungated": val_avg - base_avg,
                "validation_pnl_lift_vs_ungated": val_pnl - base_pnl,
                "validation_add_scale_avg_return": add_scale_avg,
                "validation_add_scale_avg_degradation_vs_ungated": baseline_add_scale_avg - add_scale_avg,
                "weak_regime_block_rate": _float_or_nan(weak.get("weak_regime_block_rate")),
                "weak_regime_blocked_avg_return": _float_or_nan(weak.get("blocked_weak_avg_return")),
                "validation_collapse_reduced_flag": int(pd.notna(val_avg) and pd.notna(base_avg) and val_avg > base_avg),
                "recent_oos_positive_flag": int(pd.notna(oos_avg) and oos_avg > 0),
                "add_scale_quality_preserved_flag": int(
                    pd.notna(add_scale_avg)
                    and pd.notna(baseline_add_scale_avg)
                    and add_scale_avg >= baseline_add_scale_avg - 0.005
                ),
                "policy_diagnostic_pass_flag": int(
                    policy_name != "ungated_baseline"
                    and trade_count >= 100
                    and pd.notna(val_avg)
                    and pd.notna(base_avg)
                    and val_avg > base_avg
                    and pd.notna(oos_avg)
                    and oos_avg > 0
                    and pd.notna(add_scale_avg)
                    and pd.notna(baseline_add_scale_avg)
                    and add_scale_avg >= baseline_add_scale_avg - 0.005
                    and pd.notna(reduction)
                    and reduction < 0.90
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["policy_diagnostic_pass_flag", "validation_avg_lift_vs_ungated", "recent_oos_avg_return"],
        ascending=[False, False, False],
    )


def build_task_394_decision(simulation: pd.DataFrame, validation_audit: pd.DataFrame) -> pd.DataFrame:
    passing = validation_audit[validation_audit["policy_diagnostic_pass_flag"].eq(1)]
    best = passing.iloc[0].to_dict() if not passing.empty else {}
    return pd.DataFrame(
        [
            {
                "task_394_verdict": "COMPLETE_PASS",
                "evaluation_status": "REGIME_AWARE_POLICY_DIAGNOSTIC_COMPLETE",
                "canonical_lifecycle_count": int(simulation["lifecycle_id"].nunique()),
                "policy_count": len(_policy_names()),
                "policy_diagnostic_pass_count": len(passing),
                "best_policy": best.get("policy_name", ""),
                "best_validation_avg_lift_vs_ungated": best.get("validation_avg_lift_vs_ungated", ""),
                "best_recent_oos_avg_return": best.get("recent_oos_avg_return", ""),
                "best_validation_trade_reduction_rate": best.get("validation_trade_reduction_rate", ""),
                "reconstruction_used_flag": 0,
                "symbol_session_inference_used_flag": 0,
                "threshold_relaxation_flag": 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "POLICY_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT",
                "next_priority": "policy_holdout_costs_and_capital_constraints",
            }
        ]
    )


def write_task_394_artifacts(
    artifacts: RegimeAwareCanonicalContinuationPolicy394Artifacts,
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.regime_policy_rulebook.to_csv(out_dir / "regime_policy_rulebook.csv", index=False, encoding="utf-8-sig")
    artifacts.policy_lifecycle_simulation_panel.to_csv(out_dir / "policy_lifecycle_simulation_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.policy_split_quality.to_csv(out_dir / "policy_split_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.policy_monthly_quality.to_csv(out_dir / "policy_monthly_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.policy_transition_audit.to_csv(out_dir / "policy_transition_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.policy_weak_regime_audit.to_csv(out_dir / "policy_weak_regime_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.policy_validation_audit.to_csv(out_dir / "policy_validation_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_394_decision.to_csv(out_dir / "task_394_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 394 - Regime-Aware Canonical Continuation Policy",
        "",
        "## Required Answers",
        "- Did Task 394 use canonical lifecycle stream only? `YES`",
        "- Did Task 394 use reconstruction or symbol/session matching? `NO`",
        "- Did Task 394 relax thresholds or promote themes? `NO`",
        "- Did Task 394 make a deployment claim? `NO`",
        "- Did Task 394 reprice blocked ADD/SCALE transitions? `NO`",
        "",
        "## Decision",
        artifacts.task_394_decision.to_csv(index=False).strip(),
        "",
        "## Rulebook",
        artifacts.regime_policy_rulebook.to_csv(index=False).strip(),
        "",
        "## Policy Validation Audit",
        artifacts.policy_validation_audit.to_csv(index=False).strip(),
        "",
        "## Policy Split Quality",
        artifacts.policy_split_quality.to_csv(index=False).strip(),
    ]
    (out_dir / "task_394_regime_aware_canonical_continuation_policy.md").write_text(
        "\n".join(lines),
        encoding="utf-8-sig",
    )


def _prepare_panel(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    for column in ["market_regime", "breadth_regime", "liquidity_regime", "theme_leadership_regime"]:
        if column not in out.columns:
            out[column] = "unknown"
        out[column] = out[column].fillna("unknown").astype(str)
    for column in ["add_flag", "scale_flag", "reduce_flag", "add_scale_flag"]:
        if column not in out.columns:
            out[column] = 0
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0).astype(int)
    out["return_from_entry"] = pd.to_numeric(out["return_from_entry"], errors="coerce").fillna(0.0)
    out["entry_month"] = pd.to_datetime(out["entry_ts"], errors="coerce", utc=True).dt.strftime("%Y-%m")
    out["strict_regime_flag"] = (
        out["market_regime"].eq("risk_on_broad")
        & out["breadth_regime"].eq("broad_participation")
        & (out["liquidity_regime"].eq("liquidity_expansion") | out["theme_leadership_regime"].eq("theme_leader"))
    ).astype(int)
    out["weak_regime_flag"] = (
        out["market_regime"].eq("risk_off_weak") | out["breadth_regime"].eq("weak_breadth")
    ).astype(int)
    return out


def _attach_policy_permissions(frame: pd.DataFrame, policy_name: str) -> pd.DataFrame:
    out = frame.copy()
    if policy_name == "ungated_baseline":
        out["policy_state"] = "ungated"
        out["policy_entry_allowed_flag"] = 1
        out["policy_add_allowed_flag"] = 1
        out["policy_scale_allowed_flag"] = 1
        out["policy_reduce_strengthened_flag"] = 0
    elif policy_name == "risk_on_gate":
        allowed = out["market_regime"].eq("risk_on_broad")
        _set_basic_policy(out, allowed, add_allowed=allowed, scale_allowed=allowed, reduce_strengthened=~allowed)
    elif policy_name == "broad_participation_gate":
        allowed = out["breadth_regime"].eq("broad_participation")
        _set_basic_policy(out, allowed, add_allowed=allowed, scale_allowed=allowed, reduce_strengthened=~allowed)
    elif policy_name == "theme_leader_gate":
        allowed = out["theme_leadership_regime"].eq("theme_leader")
        _set_basic_policy(out, allowed, add_allowed=allowed, scale_allowed=allowed, reduce_strengthened=~allowed)
    elif policy_name == "strict_regime_gate":
        allowed = out["strict_regime_flag"].eq(1)
        _set_basic_policy(out, allowed, add_allowed=allowed, scale_allowed=allowed, reduce_strengthened=~allowed)
    elif policy_name == "new_regime_aware_policy":
        strict = out["strict_regime_flag"].eq(1)
        weak = out["weak_regime_flag"].eq(1)
        risk_on_constrained = out["market_regime"].eq("risk_on_broad") & ~strict
        entry_allowed = strict | risk_on_constrained
        add_allowed = strict
        scale_allowed = strict
        reduce_strengthened = weak | out["market_regime"].eq("mixed_market") | out["breadth_regime"].eq("mixed_breadth") | risk_on_constrained
        out["policy_state"] = "mixed_defensive"
        out.loc[strict, "policy_state"] = "aggressive_continuation"
        out.loc[risk_on_constrained, "policy_state"] = "risk_on_constrained"
        out.loc[weak, "policy_state"] = "risk_off_blocked"
        _set_basic_policy(out, entry_allowed, add_allowed=add_allowed, scale_allowed=scale_allowed, reduce_strengthened=reduce_strengthened)
    else:
        raise ValueError(f"Unknown policy: {policy_name}")
    if "policy_state" not in out.columns:
        out["policy_state"] = policy_name
    return out


def _set_basic_policy(
    frame: pd.DataFrame,
    entry_allowed: pd.Series,
    *,
    add_allowed: pd.Series,
    scale_allowed: pd.Series,
    reduce_strengthened: pd.Series,
) -> None:
    frame["policy_state"] = "gate_allowed"
    frame.loc[~entry_allowed, "policy_state"] = "gate_blocked"
    frame["policy_entry_allowed_flag"] = entry_allowed.astype(int)
    frame["policy_add_allowed_flag"] = add_allowed.astype(int)
    frame["policy_scale_allowed_flag"] = scale_allowed.astype(int)
    frame["policy_reduce_strengthened_flag"] = reduce_strengthened.astype(int)


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
    scoped["positive_return_flag"] = (scoped["return_from_entry"] > 0).astype(int)
    return scoped.groupby(keys, dropna=False).agg(
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
    ).reset_index().reindex(columns=columns)


def _policy_names() -> list[str]:
    return [
        "ungated_baseline",
        "risk_on_gate",
        "broad_participation_gate",
        "theme_leader_gate",
        "strict_regime_gate",
        "new_regime_aware_policy",
    ]


def _split_row(frame: pd.DataFrame, policy_name: str, split: str) -> dict[str, object]:
    rows = frame[frame["policy_name"].eq(policy_name) & frame["anchored_split"].eq(split)]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def _transition_row(frame: pd.DataFrame, policy_name: str, split: str, group: str) -> dict[str, object]:
    rows = frame[
        frame["policy_name"].eq(policy_name)
        & frame["anchored_split"].eq(split)
        & frame["reinforcement_group"].eq(group)
    ]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def _weak_row(frame: pd.DataFrame, policy_name: str, split: str) -> dict[str, object]:
    rows = frame[frame["policy_name"].eq(policy_name) & frame["anchored_split"].eq(split)]
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
    parser = argparse.ArgumentParser(description="Task 394 regime-aware canonical continuation policy.")
    parser.add_argument("--task392-panel", type=Path, default=DEFAULT_TASK392_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_regime_aware_canonical_continuation_policy_394(
        task392_lifecycle_regime_panel_path=args.task392_panel,
        out_dir=args.out_dir,
    )
    row = artifacts.task_394_decision.iloc[0]
    print(
        "[TASK394] "
        f"status={row['evaluation_status']} lifecycles={row['canonical_lifecycle_count']} "
        f"best_policy={row['best_policy']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
