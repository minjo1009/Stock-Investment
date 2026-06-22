from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from backtest.analysis_drawdown_control_094 import (
    _f,
    _metrics_from_trade_pnl,
    _positions_df,
    _simulate_risk_architecture,
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _overlay_flags(overlay: str) -> tuple[dict[str, Any], dict[str, Any]]:
    mapping: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
        "BASELINE": (
            {
                "enable_loss_breaker": False,
                "enable_regime_throttle": False,
                "enable_decorrelation": False,
                "enable_adaptive_exposure": False,
            },
            {},
        ),
        "DECORRELATION_ONLY": (
            {
                "enable_loss_breaker": False,
                "enable_regime_throttle": False,
                "enable_decorrelation": True,
                "enable_adaptive_exposure": False,
            },
            {},
        ),
        "FULL_COMBINED": (
            {
                "enable_loss_breaker": True,
                "enable_regime_throttle": True,
                "enable_decorrelation": True,
                "enable_adaptive_exposure": True,
            },
            {},
        ),
        "DECORRELATION_PLUS_POSITION_THROTTLE": (
            {
                "enable_loss_breaker": False,
                "enable_regime_throttle": True,
                "enable_decorrelation": True,
                "enable_adaptive_exposure": False,
            },
            {},
        ),
        "DECORRELATION_PLUS_LIGHT_LOSS_BREAKER": (
            {
                "enable_loss_breaker": True,
                "enable_regime_throttle": False,
                "enable_decorrelation": True,
                "enable_adaptive_exposure": False,
            },
            {"loss_streak_threshold": 4, "cooldown_trades": 1},
        ),
    }
    return mapping.get(overlay, mapping["DECORRELATION_PLUS_LIGHT_LOSS_BREAKER"])


def _extract_graphify_context() -> dict[str, Any]:
    graph_path = Path("graphify-out/graph.json")
    labels_path = Path("docs/graphify/community_labels.json")
    packs_path = Path("docs/graphify/context_packs.json")

    context_pack = {
        "core_files": [
            "src/backtest/engine_full.py",
            "src/backtest/analysis_capital_backtest_093.py",
            "src/backtest/analysis_drawdown_control_094.py",
            "src/backtest/analysis_risk_adoption_095.py",
            "src/risk/policies.py",
            "src/portfolio/allocator.py",
            "docs/reports/task_093/task_093_capital_backtest.json",
            "docs/reports/task_093/task_093_capital_backtest.md",
            "docs/reports/task_093_review/task_093_review_failure_analysis.json",
            "docs/reports/task_093_review/task_093_review_failure_analysis.md",
            "docs/reports/task_095/task_095_risk_adoption.json",
            "docs/reports/task_095/task_095_risk_adoption.md",
        ],
        "related_tests": [],
    }
    if packs_path.exists():
        packs = _load_json(packs_path)
        t094_pack = packs.get("T094_RISK_OVERLAY", {})
        for key in ("core_files", "related_tests"):
            if key in t094_pack:
                context_pack[key] = list(dict.fromkeys(list(context_pack.get(key, [])) + list(t094_pack.get(key, []))))

    communities: dict[str, list[dict[str, Any]]] = {
        "Backtest / Strategy": [],
        "Risk / Portfolio": [],
        "Evidence / Paper Ops": [],
        "Reports / Docs": [],
    }
    if labels_path.exists():
        labels = _load_json(labels_path)
        for row in labels:
            label = str(row.get("label", ""))
            tops = " | ".join(row.get("top_files", []))
            entry = {"community_id": row.get("community_id"), "label": label}
            lower = f"{label} {tops}".lower()
            if "backtest" in lower or "strategy" in lower:
                communities["Backtest / Strategy"].append(entry)
            if "risk" in lower or "portfolio" in lower or "allocator" in lower:
                communities["Risk / Portfolio"].append(entry)
            if "paper ops" in lower or "evidence" in lower or "task_087" in lower or "task_088" in lower:
                communities["Evidence / Paper Ops"].append(entry)
            if "docs" in lower or "reports" in lower or "task_" in lower:
                communities["Reports / Docs"].append(entry)

    graph_meta = {}
    if graph_path.exists():
        graph = _load_json(graph_path)
        graph_meta = {"nodes": len(graph.get("nodes", [])), "links": len(graph.get("links", []))}

    return {
        "graph_file": str(graph_path),
        "graph_meta": graph_meta,
        "relevant_communities": communities,
        "context_pack": context_pack,
    }


def _status(
    *,
    ret: float,
    mdd: float,
    sharpe: float,
    baseline_ret: float,
    baseline_mdd: float,
    baseline_loss_streak: int,
    overlay_loss_streak: int,
    t092_status: str,
    unknown_events: int,
    recon_critical: int,
) -> str:
    if (
        t092_status != "PASS"
        or unknown_events > 0
        or recon_critical > 0
        or ret < (baseline_ret * 0.5)
        or mdd > (baseline_mdd * 1.2)
    ):
        return "FAIL"
    if (
        mdd < 10.0
        and sharpe >= 0.7
        and ret >= (baseline_ret * 0.8)
        and overlay_loss_streak <= baseline_loss_streak
    ):
        return "PASS"
    return "WARNING"


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T096 - Risk Overlay Revalidation")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- adopted_overlay: {report['overlay']}")
    lines.append(f"- final_verdict: {report['status']}")
    lines.append(f"- answer: {report['answer']}")
    lines.append("")
    lines.append("## 2. Performance Comparison")
    lines.append("| Metric | Baseline | Overlay | Delta |")
    lines.append("|---|---:|---:|---:|")
    for row in report["performance_comparison"]:
        lines.append(f"| {row['metric']} | {row['baseline']} | {row['overlay']} | {row['delta']} |")
    lines.append("")
    lines.append("## 3. Drawdown Behavior")
    lines.append(f"- baseline_mdd_pct: {report['stability']['baseline_mdd_pct']}")
    lines.append(f"- overlay_mdd_pct: {report['stability']['overlay_mdd_pct']}")
    lines.append(f"- mdd_change_pct: {report['stability']['mdd_change_pct']}")
    lines.append("")
    lines.append("## 4. Stability Analysis")
    lines.append(f"- baseline_loss_streak: {report['stability']['baseline_loss_streak']}")
    lines.append(f"- overlay_loss_streak: {report['stability']['overlay_loss_streak']}")
    lines.append(f"- blocked_entries_count: {report['stability']['blocked_entries_count']}")
    lines.append(f"- blocked_by_reason: {report['stability']['blocked_by_reason']}")
    lines.append(f"- scaled_pnl_volatility: {report['stability']['scaled_pnl_volatility']}")
    lines.append("")
    lines.append("## 5. Capital Efficiency")
    lines.append(f"- baseline_capital_utilization: {report['capital_efficiency']['baseline_capital_utilization']}")
    lines.append(f"- overlay_capital_utilization: {report['capital_efficiency']['overlay_capital_utilization']}")
    lines.append("")
    lines.append("## 6. System Consistency")
    lines.append(f"- t092_status: {report['consistency']['t092_status']}")
    lines.append(f"- t092_answer: {report['consistency']['t092_answer']}")
    lines.append(f"- evidence_unknown_events: {report['consistency']['evidence_unknown_events']}")
    lines.append(f"- evidence_reconciliation_critical_count: {report['consistency']['evidence_reconciliation_critical_count']}")
    lines.append("")
    lines.append("## 7. Decision")
    lines.append(f"- {report['status']}")
    lines.append("")
    lines.append("## 8. Final Answer")
    lines.append(f"Is the adopted risk overlay ready for real paper operation? {report['answer']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T096: Adopted risk overlay revalidation")
    parser.add_argument("--input-t093", type=str, default="docs/reports/task_093/task_093_capital_backtest.json")
    parser.add_argument("--input-t095", type=str, default="docs/reports/task_095/task_095_risk_adoption.json")
    parser.add_argument("--input-t092", type=str, default="docs/reports/task_092/task_092_signal_alignment.json")
    parser.add_argument("--input-t088", type=str, default="docs/reports/task_088/task_088_evidence_summary.json")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_096/task_096_revalidation.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_096/task_096_revalidation.md")
    args = parser.parse_args(argv)

    t093 = _load_json(Path(args.input_t093))
    t095 = _load_json(Path(args.input_t095))
    t092 = _load_json(Path(args.input_t092))
    t088 = _load_json(Path(args.input_t088))

    primary_scenario = str(t093.get("primary_scenario", "A_BASE_10K_HIGH_COST"))
    scenario = t093["scenarios"][primary_scenario]
    positions = _positions_df(scenario.get("closed_positions", []))
    if positions.empty:
        raise SystemExit("No closed positions available from T093.")

    initial_capital = float(scenario["initial_capital"])
    baseline_metrics = _metrics_from_trade_pnl(
        pnls=positions["net_pnl"].tolist(),
        exit_times=positions["exit_time"].tolist(),
        initial_capital=initial_capital,
    )

    overlay = str(t095.get("selected_overlay", "DECORRELATION_PLUS_LIGHT_LOSS_BREAKER"))
    flags, overrides = _overlay_flags(overlay)
    sim = _simulate_risk_architecture(positions, initial_capital=initial_capital, **flags, **overrides)
    overlay_metrics = _metrics_from_trade_pnl(
        pnls=sim["scaled_trade_pnls"],
        exit_times=sim["scaled_exit_times"],
        initial_capital=initial_capital,
    )

    baseline_ret = float(baseline_metrics["return_pct"])
    overlay_ret = float(overlay_metrics["return_pct"])
    baseline_mdd = float(baseline_metrics["mdd_pct"])
    overlay_mdd = float(overlay_metrics["mdd_pct"])
    baseline_sharpe = float(baseline_metrics["sharpe"])
    overlay_sharpe = float(overlay_metrics["sharpe"])
    baseline_streak = int(baseline_metrics["max_loss_streak"])
    overlay_streak = int(sim["loss_streak_after"])

    evidence_agg = t088.get("aggregate_metrics", {})
    unknown_events = int(evidence_agg.get("unknown_events", 0))
    recon_critical = int(evidence_agg.get("reconciliation_critical_count", 0))
    t092_status = str(t092.get("status", "FAIL"))
    status = _status(
        ret=overlay_ret,
        mdd=overlay_mdd,
        sharpe=overlay_sharpe,
        baseline_ret=baseline_ret,
        baseline_mdd=baseline_mdd,
        baseline_loss_streak=baseline_streak,
        overlay_loss_streak=overlay_streak,
        t092_status=t092_status,
        unknown_events=unknown_events,
        recon_critical=recon_critical,
    )
    answer = "YES" if status == "PASS" else "NO"

    pnl_std = statistics.pstdev(sim["scaled_trade_pnls"]) if len(sim["scaled_trade_pnls"]) >= 2 else 0.0

    report = {
        "task": "T096",
        "status": status,
        "answer": answer,
        "overlay": overlay,
        "baseline_scenario": primary_scenario,
        "graphify": _extract_graphify_context(),
        "performance_comparison": [
            {"metric": "Return %", "baseline": _f(baseline_ret), "overlay": _f(overlay_ret), "delta": _f(overlay_ret - baseline_ret)},
            {"metric": "MDD %", "baseline": _f(baseline_mdd), "overlay": _f(overlay_mdd), "delta": _f(overlay_mdd - baseline_mdd)},
            {
                "metric": "Sharpe",
                "baseline": _f(baseline_sharpe),
                "overlay": _f(overlay_sharpe),
                "delta": _f(overlay_sharpe - baseline_sharpe),
            },
            {
                "metric": "Profit Factor",
                "baseline": _f(float(baseline_metrics["profit_factor"])),
                "overlay": _f(float(overlay_metrics["profit_factor"])),
                "delta": _f(float(overlay_metrics["profit_factor"]) - float(baseline_metrics["profit_factor"])),
            },
            {
                "metric": "Trade Count",
                "baseline": int(baseline_metrics["trade_count"]),
                "overlay": int(overlay_metrics["trade_count"]),
                "delta": int(overlay_metrics["trade_count"]) - int(baseline_metrics["trade_count"]),
            },
        ],
        "stability": {
            "baseline_mdd_pct": _f(baseline_mdd),
            "overlay_mdd_pct": _f(overlay_mdd),
            "mdd_change_pct": _f(overlay_mdd - baseline_mdd),
            "baseline_loss_streak": baseline_streak,
            "overlay_loss_streak": overlay_streak,
            "blocked_entries_count": int(sim["blocked_entries_count"]),
            "blocked_by_reason": sim["blocked_by_reason"],
            "scaled_pnl_volatility": _f(pnl_std),
        },
        "capital_efficiency": {
            "baseline_capital_utilization": _f(float(scenario.get("capital_utilization", 0.0))),
            "overlay_capital_utilization": _f(float(sim["utilization_after"])),
            "overlay_max_exposure": _f(float(sim["max_exposure_after"])),
        },
        "consistency": {
            "t092_status": t092_status,
            "t092_answer": str(t092.get("answer", "NO")),
            "t092_major_diff_count": int(t092.get("major_diff_count", 0)),
            "evidence_decision_status": str(t088.get("final_decision", {}).get("status", "WARNING")),
            "evidence_unknown_events": unknown_events,
            "evidence_reconciliation_critical_count": recon_critical,
        },
        "criteria": {
            "mdd_lt_10": overlay_mdd < 10.0,
            "sharpe_gte_0_7": overlay_sharpe >= 0.7,
            "return_gte_80pct_baseline": overlay_ret >= (baseline_ret * 0.8),
            "loss_clustering_mitigated": overlay_streak <= baseline_streak,
        },
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={status}")
    print(f"answer={answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
