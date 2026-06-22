from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _s4_gate_judgement(s4: dict[str, Any], baseline_s4: dict[str, Any]) -> dict[str, Any]:
    trades_ok = float(s4.get("trades", 0.0)) >= float(baseline_s4.get("trades", 0.0)) * 0.50
    pf_improved = float(s4.get("profit_factor", 0.0)) > float(baseline_s4.get("profit_factor", 0.0))
    sharpe_improved = float(s4.get("sharpe", 0.0)) > float(baseline_s4.get("sharpe", 0.0))
    mdd_improved = float(s4.get("max_drawdown", 0.0)) < float(baseline_s4.get("max_drawdown", 0.0))
    net_reasonable = float(s4.get("net_pnl", 0.0)) >= float(baseline_s4.get("net_pnl", 0.0)) * 0.90
    return {
        "trade_count_ok": trades_ok,
        "pf_improved": pf_improved,
        "sharpe_improved": sharpe_improved,
        "mdd_improved": mdd_improved,
        "net_reasonable": net_reasonable,
    }


def _status_from_checks(checks: dict[str, bool]) -> str:
    if not checks["trade_count_ok"]:
        return "FAIL"
    if checks["pf_improved"] and checks["sharpe_improved"] and checks["mdd_improved"] and checks["net_reasonable"]:
        return "PASS"
    if checks["pf_improved"] or checks["sharpe_improved"] or checks["mdd_improved"]:
        return "WARNING"
    return "FAIL"


def _final_answer(status: str) -> str:
    if status == "PASS":
        return "YES"
    if status == "WARNING":
        return "WARNING"
    return "NO"


def _to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 076 Review")
    lines.append("")
    lines.append(f"- source report: `{payload['source_report']}`")
    lines.append(f"- baseline candidate: `{payload['baseline_candidate']}`")
    lines.append(f"- selected candidate: `{payload['selected_candidate']}`")
    lines.append("")
    lines.append("## S4 Snapshot")
    lines.append("")
    b = payload["s4"]["baseline"]
    c = payload["s4"]["candidate"]
    lines.append(
        f"- baseline PF/Net/MDD/Sharpe/Trades: {b['profit_factor']:.4f} / {b['net_pnl']:.2f} / "
        f"{b['max_drawdown']:.2f} / {b['sharpe']:.4f} / {int(b['trades'])}"
    )
    lines.append(
        f"- candidate PF/Net/MDD/Sharpe/Trades: {c['profit_factor']:.4f} / {c['net_pnl']:.2f} / "
        f"{c['max_drawdown']:.2f} / {c['sharpe']:.4f} / {int(c['trades'])}"
    )
    lines.append("")
    lines.append("## Checks")
    for key, value in payload["checks"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Decision")
    lines.append(f"- gate decision: {payload['gate_decision']}")
    lines.append(f"- pilot answer: {payload['pilot_answer']}")
    lines.append(f"- recommendation: {payload['recommendation']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 076 Review: adopt/hold/discard gate candidate")
    parser.add_argument(
        "--input-json",
        type=str,
        default="docs/reports/task_076/task_076_minimal_regime_entry_gate.json",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/reports/task_076/task_076_review.json",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default="docs/reports/task_076/task_076_review.md",
    )
    args = parser.parse_args()

    report_path = Path(args.input_json)
    report = _load_report(report_path)
    selected_candidate = str((report.get("final_recommendation") or {}).get("candidate", "A_BASELINE"))
    baseline_candidate = "A_BASELINE"
    results = report.get("results", {})
    baseline_s4 = ((results.get(baseline_candidate) or {}).get("S4_KIS_REALISTIC") or {})
    selected_s4 = ((results.get(selected_candidate) or {}).get("S4_KIS_REALISTIC") or {})

    checks = _s4_gate_judgement(selected_s4, baseline_s4)
    status = _status_from_checks(checks)
    pilot_answer = _final_answer(status)
    if status == "PASS":
        recommendation = "APPLY"
    elif status == "WARNING":
        recommendation = "HOLD_WITH_RESTRICTED_PILOT"
    else:
        recommendation = "DISCARD_AND_KEEP_BASELINE"

    payload = {
        "source_report": str(report_path),
        "baseline_candidate": baseline_candidate,
        "selected_candidate": selected_candidate,
        "s4": {"baseline": baseline_s4, "candidate": selected_s4},
        "checks": checks,
        "gate_decision": status,
        "pilot_answer": pilot_answer,
        "recommendation": recommendation,
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_to_markdown(payload), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"gate_decision={status}")
    print(f"pilot_answer={pilot_answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
