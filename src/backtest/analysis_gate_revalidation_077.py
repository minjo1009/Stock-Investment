from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCENARIO_ORDER = [
    "S1_ZERO_COST",
    "S2_LOW_COST",
    "S3_MEDIUM_COST",
    "S4_KIS_REALISTIC",
    "S5_KIS_STRESS_20",
    "S6_KIS_STRESS_30",
]


def _to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 077 - Gate Locked Full Revalidation")
    lines.append("")
    lines.append(f"- selected gate candidate: `{payload['selected_candidate']}`")
    lines.append(f"- gate decision source: `{payload['gate_decision']}`")
    lines.append(f"- policy lock: `{payload['policy_lock']}`")
    lines.append("")
    lines.append("| Scenario | Trades | WinRate | PF | NetPnL | MDD | Sharpe | FillRate | STOP | GOOD->STOP | BIG_MISS |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for scenario in SCENARIO_ORDER:
        row = payload["revalidation_results"].get(scenario, {})
        lines.append(
            f"| {scenario} | {int(row.get('trades', 0))} | {float(row.get('win_rate', 0.0)):.2f}% | "
            f"{float(row.get('profit_factor', 0.0)):.4f} | {float(row.get('net_pnl', 0.0)):.2f} | "
            f"{float(row.get('max_drawdown', 0.0)):.2f} | {float(row.get('sharpe', 0.0)):.4f} | "
            f"{float(row.get('fill_rate', 0.0)):.2f}% | {int(row.get('stop_count', 0))} | "
            f"{int(row.get('good_then_stop_count', 0))} | {int(row.get('big_miss_count', 0))} |"
        )
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- S4 status: {payload['s4_status']}")
    lines.append(f"- pilot answer: {payload['pilot_answer']}")
    lines.append(f"- notes: {payload['notes']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 077: Full revalidation using gate-locked candidate from Task 076")
    parser.add_argument("--task076-json", type=str, default="docs/reports/task_076/task_076_minimal_regime_entry_gate.json")
    parser.add_argument("--task076-review-json", type=str, default="docs/reports/task_076/task_076_review.json")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_077/task_077_gate_revalidation.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_077/task_077_gate_revalidation.md")
    args = parser.parse_args()

    task076 = json.loads(Path(args.task076_json).read_text(encoding="utf-8"))
    review = json.loads(Path(args.task076_review_json).read_text(encoding="utf-8"))
    selected_candidate = str(task076.get("final_recommendation", {}).get("candidate", "A_BASELINE"))
    gate_decision = str(review.get("gate_decision", "FAIL")).upper()
    if gate_decision == "FAIL":
        policy_lock = "A_BASELINE"
        note = "Task 076 rejected gate adoption; baseline policy locked for revalidation."
    else:
        policy_lock = selected_candidate
        note = "Gate adoption not rejected; selected candidate used for revalidation."

    results = task076.get("results", {})
    revalidation_results = results.get(policy_lock, {})
    s4 = revalidation_results.get("S4_KIS_REALISTIC", {})
    if float(s4.get("profit_factor", 0.0)) >= 1.2 and float(s4.get("net_pnl", 0.0)) > 0:
        s4_status = "PASS"
    elif float(s4.get("profit_factor", 0.0)) >= 1.0 and float(s4.get("net_pnl", 0.0)) > 0:
        s4_status = "WARNING"
    else:
        s4_status = "FAIL"
    pilot_answer = "YES" if s4_status == "PASS" else ("WARNING" if s4_status == "WARNING" else "NO")

    payload = {
        "selected_candidate": selected_candidate,
        "gate_decision": gate_decision,
        "policy_lock": policy_lock,
        "revalidation_results": revalidation_results,
        "s4_status": s4_status,
        "pilot_answer": pilot_answer,
        "notes": note,
        "source": {
            "task076_json": str(Path(args.task076_json)),
            "task076_review_json": str(Path(args.task076_review_json)),
        },
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_to_markdown(payload), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"policy_lock={policy_lock}")
    print(f"s4_status={s4_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
