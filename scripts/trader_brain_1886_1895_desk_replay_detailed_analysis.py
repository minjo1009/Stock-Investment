from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1808 = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
TASK1848 = ROOT / "data/artifacts/task_1848_1867_source_attached_policy_replay"
TASK1878 = ROOT / "data/artifacts/task_1878_1885_desk_specific_policy_replay"
OUT_DIR = ROOT / "data/artifacts/task_1886_1895_desk_replay_detailed_analysis"
REPORT_DIR = ROOT / "docs/reports/task_1886_1895_desk_replay_detailed_analysis"
REPORT = REPORT_DIR / "task_1886_1895_desk_replay_detailed_analysis.md"
DECISION = REPORT_DIR / "task_1886_1895_decision.csv"

AUTHORITY = "DIAGNOSTIC_DESK_REPLAY_DETAILED_ANALYSIS_ONLY"

POLICY_MAP = {
    "desk_specific_top3_v1": {
        "baseline": "sleeve_split_top3_v1",
        "source_attached": "source_attached_top3_v1",
        "slot": "top3",
    },
    "desk_specific_top5_v1": {
        "baseline": "sleeve_split_top5_v1",
        "source_attached": "source_attached_top5_v1",
        "slot": "top5",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def trade_key(row: dict[str, str]) -> tuple[str, str]:
    return row["policy_variant_id"], row["trade_spec_id"]


def load_trade_maps() -> tuple[dict[tuple[str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]:
    baseline = {trade_key(row): row for row in read_csv(TASK1808 / "task1822_controlled_sleeve_replay_trades.csv")}
    source = {trade_key(row): row for row in read_csv(TASK1848 / "task1857_controlled_source_attached_replay_trades.csv")}
    desk = {trade_key(row): row for row in read_csv(TASK1878 / "task1885_controlled_desk_replay_trades.csv")}
    return baseline, source, desk


def budget_maps() -> tuple[dict[tuple[str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]:
    source_budget = {
        (row["target_policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1848 / "task1855_l5_source_attached_budget.csv")
    }
    desk_budget = {
        (row["target_policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1878 / "task1884_l5_desk_specific_budget.csv")
    }
    return source_budget, desk_budget


def input_manifest_rows() -> list[dict[str, object]]:
    inputs = [
        ("baseline_trades", TASK1808 / "task1822_controlled_sleeve_replay_trades.csv"),
        ("source_attached_trades", TASK1848 / "task1857_controlled_source_attached_replay_trades.csv"),
        ("desk_specific_trades", TASK1878 / "task1885_controlled_desk_replay_trades.csv"),
        ("source_attached_budget", TASK1848 / "task1855_l5_source_attached_budget.csv"),
        ("desk_specific_budget", TASK1878 / "task1884_l5_desk_specific_budget.csv"),
        ("desk_specific_metrics", TASK1878 / "task1885_desk_replay_metrics.csv"),
    ]
    return [
        {
            "task_id": "Task1886",
            "analysis_input_id": f"DESKANALYSISINPUT-1886-{idx:03d}",
            "input_name": name,
            "input_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "exists": "1" if path.exists() else "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
        for idx, (name, path) in enumerate(inputs, 1)
    ]


def joined_trade_rows() -> list[dict[str, object]]:
    baseline, source, desk = load_trade_maps()
    source_budget, desk_budget = budget_maps()
    rows: list[dict[str, object]] = []
    idx = 1
    for desk_policy, mapped in POLICY_MAP.items():
        baseline_policy = mapped["baseline"]
        source_policy = mapped["source_attached"]
        baseline_keys = {spec for policy, spec in baseline if policy == baseline_policy}
        source_keys = {spec for policy, spec in source if policy == source_policy}
        desk_keys = {spec for policy, spec in desk if policy == desk_policy}
        source_budget_keys = {spec for policy, spec in source_budget if policy == mapped_source_policy(desk_policy)}
        desk_budget_keys = {spec for policy, spec in desk_budget if policy == mapped_source_policy(desk_policy)}
        for spec in sorted(baseline_keys | source_keys | desk_keys | source_budget_keys | desk_budget_keys):
            base = baseline.get((baseline_policy, spec), {})
            src = source.get((source_policy, spec), {})
            dsk = desk.get((desk_policy, spec), {})
            sb = source_budget.get((mapped_source_policy(desk_policy), spec), {})
            db = desk_budget.get((mapped_source_policy(desk_policy), spec), {})
            symbol = first_nonempty(dsk.get("symbol"), src.get("symbol"), base.get("symbol"), db.get("symbol"), sb.get("symbol"))
            sleeve = first_nonempty(dsk.get("strategy_sleeve"), src.get("strategy_sleeve"), base.get("strategy_sleeve"), db.get("strategy_sleeve"), sb.get("strategy_sleeve"))
            baseline_pnl = to_float(base.get("pnl"))
            source_pnl = to_float(src.get("pnl"))
            desk_pnl = to_float(dsk.get("pnl"))
            rows.append(
                {
                    "task_id": "Task1887",
                    "joined_trade_id": f"DESKJOIN-1887-{idx:06d}",
                    "policy_variant_id": desk_policy,
                    "slot_group": mapped["slot"],
                    "baseline_policy_variant_id": baseline_policy,
                    "source_attached_policy_variant_id": source_policy,
                    "trade_spec_id": spec,
                    "candidate_source_id": first_nonempty(dsk.get("candidate_source_id"), src.get("candidate_source_id"), base.get("candidate_source_id"), db.get("candidate_source_id"), sb.get("candidate_source_id")),
                    "symbol": symbol,
                    "decision_asof_ts": first_nonempty(dsk.get("decision_asof_ts"), src.get("decision_asof_ts"), base.get("decision_asof_ts"), db.get("decision_asof_ts"), sb.get("decision_asof_ts")),
                    "strategy_sleeve": sleeve,
                    "baseline_action": base.get("sleeve_action", ""),
                    "source_attached_action": src.get("source_attached_action", sb.get("source_attached_action", "")),
                    "desk_action": dsk.get("desk_action", db.get("desk_action", "")),
                    "desk_thesis_state": dsk.get("desk_thesis_state", db.get("desk_thesis_state", "")),
                    "financing_specificity_state": dsk.get("financing_specificity_state", db.get("financing_specificity_state", "")),
                    "theme_breadth_state": dsk.get("theme_breadth_state", db.get("theme_breadth_state", "")),
                    "baseline_multiplier": base.get("sleeve_budget_multiplier", ""),
                    "source_attached_multiplier": src.get("source_attached_budget_multiplier", sb.get("source_attached_budget_multiplier", "")),
                    "desk_multiplier": dsk.get("desk_budget_multiplier", db.get("desk_budget_multiplier", "")),
                    "net_return_audit_only": first_nonempty(dsk.get("net_return"), src.get("net_return"), base.get("net_return")),
                    "baseline_capital_allocated": round(to_float(base.get("capital_allocated")), 4),
                    "source_attached_capital_allocated": round(to_float(src.get("capital_allocated")), 4),
                    "desk_capital_allocated": round(to_float(dsk.get("capital_allocated")), 4),
                    "baseline_pnl_audit_only": round(baseline_pnl, 4),
                    "source_attached_pnl_audit_only": round(source_pnl, 4),
                    "desk_pnl_audit_only": round(desk_pnl, 4),
                    "desk_delta_vs_baseline_pnl_audit_only": round(desk_pnl - baseline_pnl, 4),
                    "desk_delta_vs_source_attached_pnl_audit_only": round(desk_pnl - source_pnl, 4),
                    "baseline_trade_present": "1" if base else "0",
                    "source_attached_trade_present": "1" if src else "0",
                    "desk_trade_present": "1" if dsk else "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def mapped_source_policy(desk_policy: str) -> str:
    return "winner_defense_budget_top3_v1" if desk_policy.endswith("top3_v1") else "winner_defense_budget_top5_v1"


def first_nonempty(*values: object) -> str:
    for value in values:
        if value not in {"", None}:
            return str(value)
    return ""


def group_attribution(rows: list[dict[str, object]], group_fields: list[str], task_id: str, prefix: str) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(field, "")) for field in group_fields)].append(row)
    out = []
    for idx, (key, items) in enumerate(sorted(grouped.items()), 1):
        out.append(
            {
                "task_id": task_id,
                "attribution_id": f"{prefix}-{idx:05d}",
                **{field: value for field, value in zip(group_fields, key)},
                "row_count": len(items),
                "baseline_pnl_sum_audit_only": round(sum(to_float(item["baseline_pnl_audit_only"]) for item in items), 4),
                "source_attached_pnl_sum_audit_only": round(sum(to_float(item["source_attached_pnl_audit_only"]) for item in items), 4),
                "desk_pnl_sum_audit_only": round(sum(to_float(item["desk_pnl_audit_only"]) for item in items), 4),
                "desk_delta_vs_baseline_sum_audit_only": round(sum(to_float(item["desk_delta_vs_baseline_pnl_audit_only"]) for item in items), 4),
                "desk_delta_vs_source_attached_sum_audit_only": round(sum(to_float(item["desk_delta_vs_source_attached_pnl_audit_only"]) for item in items), 4),
                "negative_delta_vs_baseline_count": sum(1 for item in items if to_float(item["desk_delta_vs_baseline_pnl_audit_only"]) < 0),
                "positive_delta_vs_source_count": sum(1 for item in items if to_float(item["desk_delta_vs_source_attached_pnl_audit_only"]) > 0),
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return out


def top_driver_rows(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    losses = sorted(rows, key=lambda item: to_float(item["desk_delta_vs_baseline_pnl_audit_only"]))[:50]
    improvements = sorted(rows, key=lambda item: to_float(item["desk_delta_vs_source_attached_pnl_audit_only"]), reverse=True)[:50]
    loss_rows = []
    for idx, row in enumerate(losses, 1):
        loss_rows.append({**row, "task_id": "Task1891", "driver_rank": idx, "driver_type": "largest_loss_vs_baseline", "authority": AUTHORITY})
    improvement_rows = []
    for idx, row in enumerate(improvements, 1):
        improvement_rows.append({**row, "task_id": "Task1892", "driver_rank": idx, "driver_type": "largest_improvement_vs_source_attached", "authority": AUTHORITY})
    return loss_rows, improvement_rows


def equity_delta_rows() -> list[dict[str, object]]:
    baseline_eq = read_csv(TASK1808 / "task1822_controlled_sleeve_replay_equity.csv")
    source_eq = read_csv(TASK1848 / "task1857_controlled_source_attached_replay_equity.csv")
    desk_eq = read_csv(TASK1878 / "task1885_controlled_desk_replay_equity.csv")
    baseline = {(row["policy_variant_id"], row["decision_asof_ts"]): row for row in baseline_eq}
    source = {(row["policy_variant_id"], row["decision_asof_ts"]): row for row in source_eq}
    desk = {(row["policy_variant_id"], row["decision_asof_ts"]): row for row in desk_eq}
    rows = []
    idx = 1
    for desk_policy, mapped in POLICY_MAP.items():
        dates = sorted({date for policy, date in desk if policy == desk_policy})
        for decision_ts in dates:
            dsk = desk[(desk_policy, decision_ts)]
            base = baseline.get((mapped["baseline"], decision_ts), {})
            src = source.get((mapped["source_attached"], decision_ts), {})
            rows.append(
                {
                    "task_id": "Task1890",
                    "equity_delta_id": f"EQUITYDELTA-1890-{idx:05d}",
                    "policy_variant_id": desk_policy,
                    "decision_asof_ts": decision_ts,
                    "baseline_equity": base.get("equity", ""),
                    "source_attached_equity": src.get("equity", ""),
                    "desk_equity": dsk.get("equity", ""),
                    "desk_delta_vs_baseline_equity": round(to_float(dsk.get("equity")) - to_float(base.get("equity")), 4),
                    "desk_delta_vs_source_attached_equity": round(to_float(dsk.get("equity")) - to_float(src.get("equity")), 4),
                    "baseline_allocated_count": base.get("allocated_count", ""),
                    "source_attached_allocated_count": src.get("allocated_count", ""),
                    "desk_allocated_count": dsk.get("allocated_count", ""),
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def diagnosis_rows(joined: list[dict[str, object]], sleeve_attr: list[dict[str, object]], action_attr: list[dict[str, object]]) -> list[dict[str, object]]:
    by_policy = defaultdict(list)
    for row in joined:
        by_policy[str(row["policy_variant_id"])].append(row)
    rows = []
    idx = 1
    for policy, items in sorted(by_policy.items()):
        winner = [row for row in items if row["strategy_sleeve"] == "winner_compounder"]
        watch = [row for row in winner if row["desk_action"] == "watch"]
        hold = [row for row in winner if row["desk_action"] == "hold"]
        rows.append(
            {
                "task_id": "Task1893",
                "diagnosis_id": f"DESKDIAG-1893-{idx:03d}",
                "policy_variant_id": policy,
                "diagnosis_level": "primary",
                "finding": "winner_trim_repaired_but_winner_budget_not_fully_restored",
                "evidence": f"winner_hold={len(hold)};winner_watch={len(watch)};watch_delta_vs_baseline={sum(to_float(row['desk_delta_vs_baseline_pnl_audit_only']) for row in watch):.4f}",
                "next_implication": "Need separate thesis-damaged watch from high-quality non-live financing watch before changing sizing.",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
        no_entry = [row for row in items if row["desk_action"] == "no_entry"]
        rows.append(
            {
                "task_id": "Task1893",
                "diagnosis_id": f"DESKDIAG-1893-{idx:03d}",
                "policy_variant_id": policy,
                "diagnosis_level": "secondary",
                "finding": "speculative_live_financing_block_is_targeted_but_needs_payoff_audit",
                "evidence": f"no_entry_rows={len(no_entry)};no_entry_delta_vs_baseline={sum(to_float(row['desk_delta_vs_baseline_pnl_audit_only']) for row in no_entry):.4f}",
                "next_implication": "Audit whether blocked speculative names were true avoided damage or missed optionality.",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    rows.append(
        {
            "task_id": "Task1893",
            "diagnosis_id": f"DESKDIAG-1893-{idx:03d}",
            "policy_variant_id": "all",
            "diagnosis_level": "root",
            "finding": "the current bottleneck is not broad trim anymore; it is calibration between thesis damage and winner preservation",
            "evidence": "validator blocked broad trim recurrence; metrics still trail baseline CAGR",
            "next_implication": "Next work should analyze watch-state subtypes before adding new data families or micro sizing.",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    )
    return rows


def next_task_rows() -> list[dict[str, object]]:
    tasks = [
        ("Task1896", "Winner Watch Subtype Split", "Winner Desk", "Split winner watch into live-damage, shelf-watch, macro-volatility, and insufficient-quality watch."),
        ("Task1897", "Watch State Counterfactual Audit", "Quant Review", "Audit watch rows that lost most vs baseline without using results for assignment."),
        ("Task1898", "Live Dilution Precision Upgrade", "Capital Markets Desk", "Add filing item/form/term specificity so live dilution does not over-penalize real compounders."),
        ("Task1899", "Speculative Block Payoff Audit", "Capital Markets / Risk", "Check whether no-entry prevented real damage or removed convex winners."),
        ("Task1900", "Thesis Intact Hold Calibration", "Winner Desk", "Pre-register one calibration that can restore budget only when no live damage and quality/breadth support agree."),
    ]
    return [
        {
            "task_id": task_id,
            "title": title,
            "owner_team": owner,
            "goal": goal,
            "status": "planned",
            "authority": AUTHORITY,
        }
        for task_id, title, owner, goal in tasks
    ]


def closeout_rows(metrics: list[dict[str, str]], diagnosis: list[dict[str, object]]) -> list[dict[str, object]]:
    top3 = next(row for row in metrics if row["policy_variant_id"] == "desk_specific_top3_v1")
    return [
        {
            "task_id": "Task1895",
            "verdict": "desk_replay_detailed_analysis_complete",
            "primary_bottleneck": "winner_watch_calibration_after_broad_trim_repair",
            "top3_final_equity": top3["final_equity"],
            "top3_cagr": top3["cagr"],
            "top3_max_drawdown": top3["max_drawdown"],
            "top3_delta_vs_baseline_final": top3["delta_vs_baseline_final"],
            "top3_delta_vs_source_attached_final": top3["delta_vs_source_attached_final"],
            "next_action": "Task1896-1900 watch subtype split and calibration audit before any new replay",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def write_report(
    sleeve_attr: list[dict[str, object]],
    action_attr: list[dict[str, object]],
    finance_attr: list[dict[str, object]],
    diagnosis: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    top_sleeves = sorted(sleeve_attr, key=lambda row: to_float(row["desk_delta_vs_baseline_sum_audit_only"]))[:8]
    top_actions = sorted(action_attr, key=lambda row: to_float(row["desk_delta_vs_baseline_sum_audit_only"]))[:8]
    lines = [
        "# Task1886-1895 Desk Replay Detailed Analysis",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Primary bottleneck: `{closeout['primary_bottleneck']}`.",
        f"- Top3 final equity: {closeout['top3_final_equity']}.",
        f"- Top3 CAGR: {closeout['top3_cagr']}.",
        f"- Top3 MDD: {closeout['top3_max_drawdown']}.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "This task does not add a new trading rule. It decomposes the Task1878-1885 replay after implementation.",
        "",
        "Largest desk-specific losses vs baseline by sleeve/action:",
        "",
        "| Group | Rows | Desk PnL | Baseline PnL | Delta vs Baseline | Delta vs Source |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in top_sleeves:
        group = f"{row.get('policy_variant_id', '')}/{row.get('strategy_sleeve', '')}"
        lines.append(
            f"| `{group}` | {row['row_count']} | {row['desk_pnl_sum_audit_only']} | {row['baseline_pnl_sum_audit_only']} | {row['desk_delta_vs_baseline_sum_audit_only']} | {row['desk_delta_vs_source_attached_sum_audit_only']} |"
        )
    lines.extend(["", "Largest action-level losses vs baseline:", "", "| Group | Rows | Desk PnL | Baseline PnL | Delta vs Baseline |", "| --- | ---: | ---: | ---: | ---: |"])
    for row in top_actions:
        group = f"{row.get('policy_variant_id', '')}/{row.get('strategy_sleeve', '')}/{row.get('desk_action', '')}"
        lines.append(
            f"| `{group}` | {row['row_count']} | {row['desk_pnl_sum_audit_only']} | {row['baseline_pnl_sum_audit_only']} | {row['desk_delta_vs_baseline_sum_audit_only']} |"
        )
    lines.extend(["", "Core diagnosis:", ""])
    for row in diagnosis:
        lines.append(f"- `{row['policy_variant_id']}`: {row['finding']} ({row['evidence']}).")
    lines.extend(
        [
            "",
            "Leakage audit:",
            "",
            "- This is outcome audit only.",
            "- PnL/delta fields are not used for assignment.",
            "- No new price matching or inferred lifecycle matching is introduced.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Broad trim problem is mostly fixed.",
            "2. But the brain still puts too many winners into watch instead of full hold.",
            "3. That watch state protects MDD, but it leaves return on the table.",
            "4. The next bottleneck is not micro sizing.",
            "5. The next bottleneck is splitting watch into real damage vs normal winner volatility.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1886_analysis_input_manifest.csv`",
            "- `task1887_policy_delta_trade_join.csv`",
            "- `task1888_sleeve_attribution.csv`",
            "- `task1889_action_attribution.csv`",
            "- `task1890_equity_delta_by_period.csv`",
            "- `task1891_lost_vs_baseline_top_drivers.csv`",
            "- `task1892_improved_vs_source_attached_top_drivers.csv`",
            "- `task1893_failure_diagnosis.csv`",
            "- `task1894_next_task_plan.csv`",
            "- `task1895_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1886_1895_desk_replay_detailed_analysis_validate.py`",
            "- `python scripts/task_registry_validate.py`",
            "",
            "```text",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "```",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    joined = joined_trade_rows()
    sleeve_attr = group_attribution(joined, ["policy_variant_id", "strategy_sleeve"], "Task1888", "SLEEVEATTR-1888")
    action_attr = group_attribution(joined, ["policy_variant_id", "strategy_sleeve", "desk_action"], "Task1889", "ACTIONATTR-1889")
    finance_attr = group_attribution(joined, ["policy_variant_id", "financing_specificity_state", "desk_action"], "Task1889", "FINATTR-1889")
    thesis_attr = group_attribution(joined, ["policy_variant_id", "desk_thesis_state", "desk_action"], "Task1889", "THESISATTR-1889")
    loss_rows, improvement_rows = top_driver_rows(joined)
    equity_rows = equity_delta_rows()
    diagnosis = diagnosis_rows(joined, sleeve_attr, action_attr)
    metrics = read_csv(TASK1878 / "task1885_desk_replay_metrics.csv")
    closeout = closeout_rows(metrics, diagnosis)
    outputs = [
        ("task1886_analysis_input_manifest.csv", input_manifest_rows()),
        ("task1887_policy_delta_trade_join.csv", joined),
        ("task1888_sleeve_attribution.csv", sleeve_attr),
        ("task1889_action_attribution.csv", action_attr),
        ("task1889_financing_attribution.csv", finance_attr),
        ("task1889_thesis_attribution.csv", thesis_attr),
        ("task1890_equity_delta_by_period.csv", equity_rows),
        ("task1891_lost_vs_baseline_top_drivers.csv", loss_rows),
        ("task1892_improved_vs_source_attached_top_drivers.csv", improvement_rows),
        ("task1893_failure_diagnosis.csv", diagnosis),
        ("task1894_next_task_plan.csv", next_task_rows()),
        ("task1895_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task1895_closeout.json", closeout[0])
    write_report(sleeve_attr, action_attr, finance_attr, diagnosis, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1886_1895] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
