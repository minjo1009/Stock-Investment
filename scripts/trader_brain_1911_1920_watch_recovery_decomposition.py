from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1878 = ROOT / "data/artifacts/task_1878_1885_desk_specific_policy_replay"
TASK1896 = ROOT / "data/artifacts/task_1896_1900_watch_subtype_calibration"
TASK1901 = ROOT / "data/artifacts/task_1901_1910_watch_recovery_replay"
OUT_DIR = ROOT / "data/artifacts/task_1911_1920_watch_recovery_decomposition"
REPORT_DIR = ROOT / "docs/reports/task_1911_1920_watch_recovery_decomposition"
REPORT = REPORT_DIR / "task_1911_1920_watch_recovery_decomposition.md"
DECISION = REPORT_DIR / "task_1911_1920_decision.csv"

AUTHORITY = "DIAGNOSTIC_WATCH_RECOVERY_DECOMPOSITION_ONLY"


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


def input_manifest_rows() -> list[dict[str, object]]:
    inputs = [
        ("desk_specific_trades", TASK1878 / "task1885_controlled_desk_replay_trades.csv"),
        ("watch_recovery_trades", TASK1901 / "task1905_watch_recovery_replay_trades.csv"),
        ("watch_recovery_budget", TASK1901 / "task1904_watch_recovery_budget.csv"),
        ("watch_subtype_panel", TASK1896 / "task1896_watch_subtype_panel.csv"),
        ("watch_recovery_metrics", TASK1901 / "task1906_watch_recovery_metrics.csv"),
    ]
    return [
        {
            "task_id": "Task1911",
            "input_manifest_id": f"WATCHDECOMPINPUT-1911-{idx:03d}",
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


def desk_policy_for_recovery(policy_id: str) -> str:
    return "desk_specific_top3_v1" if policy_id == "watch_recovery_top3_v1" else "desk_specific_top5_v1"


def recovery_policy_for_desk(policy_id: str) -> str:
    return "watch_recovery_top3_v1" if policy_id == "desk_specific_top3_v1" else "watch_recovery_top5_v1"


def joined_delta_rows() -> list[dict[str, object]]:
    desk = {
        (recovery_policy_for_desk(row["policy_variant_id"]), row["trade_spec_id"]): row
        for row in read_csv(TASK1878 / "task1885_controlled_desk_replay_trades.csv")
    }
    recovery = {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1901 / "task1905_watch_recovery_replay_trades.csv")
    }
    budget = {
        (("watch_recovery_top3_v1" if row["target_policy_variant_id"].endswith("top3_v1") else "watch_recovery_top5_v1"), row["trade_spec_id"]): row
        for row in read_csv(TASK1901 / "task1904_watch_recovery_budget.csv")
    }
    keys = sorted(set(desk) | set(recovery) | set(budget))
    rows: list[dict[str, object]] = []
    for idx, key in enumerate(keys, 1):
        policy, spec = key
        d = desk.get(key, {})
        r = recovery.get(key, {})
        b = budget.get(key, {})
        desk_pnl = to_float(d.get("pnl"))
        rec_pnl = to_float(r.get("pnl"))
        desk_alloc = to_float(d.get("capital_allocated"))
        rec_alloc = to_float(r.get("capital_allocated"))
        rows.append(
            {
                "task_id": "Task1912",
                "recovery_delta_id": f"WATCHDELTA-1912-{idx:06d}",
                "policy_variant_id": policy,
                "desk_policy_variant_id": desk_policy_for_recovery(policy),
                "slot_group": "top3" if policy.endswith("top3_v1") else "top5",
                "trade_spec_id": spec,
                "candidate_source_id": r.get("candidate_source_id", d.get("candidate_source_id", b.get("candidate_source_id", ""))),
                "symbol": r.get("symbol", d.get("symbol", b.get("symbol", ""))),
                "decision_asof_ts": r.get("decision_asof_ts", d.get("decision_asof_ts", b.get("decision_asof_ts", ""))),
                "decision_month": str(r.get("decision_asof_ts", d.get("decision_asof_ts", b.get("decision_asof_ts", ""))))[:7],
                "strategy_sleeve": r.get("strategy_sleeve", d.get("strategy_sleeve", b.get("strategy_sleeve", ""))),
                "watch_subtype": r.get("watch_subtype", b.get("watch_subtype", "")) or "not_applicable",
                "recovery_action": r.get("recovery_action", b.get("recovery_action", "")) or "not_applicable",
                "financing_specificity_state": r.get("financing_specificity_state", b.get("financing_specificity_state", "")),
                "theme_breadth_state": r.get("theme_breadth_state", b.get("theme_breadth_state", "")),
                "net_return_audit_only": r.get("net_return", d.get("net_return", "")),
                "desk_multiplier": b.get("previous_desk_budget_multiplier", ""),
                "recovery_multiplier": b.get("watch_recovery_budget_multiplier", ""),
                "multiplier_delta": round(to_float(b.get("watch_recovery_budget_multiplier")) - to_float(b.get("previous_desk_budget_multiplier")), 6),
                "desk_capital_allocated": round(desk_alloc, 4),
                "recovery_capital_allocated": round(rec_alloc, 4),
                "capital_delta": round(rec_alloc - desk_alloc, 4),
                "desk_pnl_audit_only": round(desk_pnl, 4),
                "recovery_pnl_audit_only": round(rec_pnl, 4),
                "incremental_pnl_vs_desk_audit_only": round(rec_pnl - desk_pnl, 4),
                "desk_trade_present": "1" if d else "0",
                "recovery_trade_present": "1" if r else "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def group_rows(rows: list[dict[str, object]], fields: list[str], task_id: str, prefix: str) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(field, "")) for field in fields)].append(row)
    out = []
    for idx, (key, items) in enumerate(sorted(grouped.items()), 1):
        out.append(
            {
                "task_id": task_id,
                "analysis_id": f"{prefix}-{idx:05d}",
                **{field: value for field, value in zip(fields, key)},
                "row_count": len(items),
                "capital_delta_sum": round(sum(to_float(row["capital_delta"]) for row in items), 4),
                "incremental_pnl_sum_audit_only": round(sum(to_float(row["incremental_pnl_vs_desk_audit_only"]) for row in items), 4),
                "positive_incremental_count": sum(1 for row in items if to_float(row["incremental_pnl_vs_desk_audit_only"]) > 0),
                "negative_incremental_count": sum(1 for row in items if to_float(row["incremental_pnl_vs_desk_audit_only"]) < 0),
                "avg_net_return_audit_only": round(sum(to_float(row["net_return_audit_only"]) for row in items) / len(items), 6) if items else 0,
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return out


def cohort_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    top3_specs = {row["trade_spec_id"] for row in rows if row["policy_variant_id"] == "watch_recovery_top3_v1"}
    top5_specs = {row["trade_spec_id"] for row in rows if row["policy_variant_id"] == "watch_recovery_top5_v1"}
    out = []
    idx = 1
    for row in rows:
        if row["policy_variant_id"] == "watch_recovery_top3_v1":
            cohort = "common_top3_top5" if row["trade_spec_id"] in top5_specs else "top3_only"
        else:
            cohort = "common_top3_top5" if row["trade_spec_id"] in top3_specs else "top5_only"
        out.append({**row, "task_id": "Task1915", "cohort_id": f"WATCHCOHORT-1915-{idx:06d}", "slot_overlap_cohort": cohort})
        idx += 1
    return out


def ranking_rows(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    recoverable = [row for row in rows if row["recovery_action"] in {"near_full_hold", "restore_full_hold"}]
    best = sorted(recoverable, key=lambda row: to_float(row["incremental_pnl_vs_desk_audit_only"]), reverse=True)[:30]
    worst = sorted(recoverable, key=lambda row: to_float(row["incremental_pnl_vs_desk_audit_only"]))[:30]
    best_rows = [{**row, "task_id": "Task1916", "rank": idx, "rank_type": "best_recovery_increment"} for idx, row in enumerate(best, 1)]
    worst_rows = [{**row, "task_id": "Task1916", "rank": idx, "rank_type": "worst_recovery_increment"} for idx, row in enumerate(worst, 1)]
    return best_rows, worst_rows


def narrowed_candidate_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    candidates = []
    for row in rows:
        if row["recovery_action"] not in {"near_full_hold", "restore_full_hold"}:
            continue
        net_return = to_float(row["net_return_audit_only"])
        mult_delta = to_float(row["multiplier_delta"])
        # Outcome appears only in this audit artifact. The narrowed candidate set is for review,
        # not assignment; any future replay must freeze a rule using source fields only.
        audit_pass = net_return > 0 and mult_delta > 0
        candidates.append(
            {
                "task_id": "Task1917",
                "narrow_candidate_id": f"NARROWWATCH-1917-{len(candidates)+1:05d}",
                "policy_variant_id": row["policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_month": row["decision_month"],
                "watch_subtype": row["watch_subtype"],
                "recovery_action": row["recovery_action"],
                "financing_specificity_state": row["financing_specificity_state"],
                "theme_breadth_state": row["theme_breadth_state"],
                "net_return_audit_only": row["net_return_audit_only"],
                "incremental_pnl_vs_desk_audit_only": row["incremental_pnl_vs_desk_audit_only"],
                "audit_filter_pass": "1" if audit_pass else "0",
                "review_use_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return candidates


def diagnosis_rows(rows: list[dict[str, object]], cohort_attr: list[dict[str, object]], subtype_attr: list[dict[str, object]]) -> list[dict[str, object]]:
    metrics = {row["policy_variant_id"]: row for row in read_csv(TASK1901 / "task1906_watch_recovery_metrics.csv")}
    top3_delta = to_float(metrics["watch_recovery_top3_v1"]["delta_vs_desk_final"])
    top5_delta = to_float(metrics["watch_recovery_top5_v1"]["delta_vs_desk_final"])
    top5_only = [row for row in cohort_attr if row.get("policy_variant_id") == "watch_recovery_top5_v1" and row.get("slot_overlap_cohort") == "top5_only"]
    top3_recovery = [row for row in rows if row["policy_variant_id"] == "watch_recovery_top3_v1" and row["recovery_action"] in {"near_full_hold", "restore_full_hold"}]
    top5_recovery = [row for row in rows if row["policy_variant_id"] == "watch_recovery_top5_v1" and row["recovery_action"] in {"near_full_hold", "restore_full_hold"}]
    rows_out = [
        {
            "task_id": "Task1918",
            "diagnosis_id": "WATCHDECOMP-1918-001",
            "view": "policy_result",
            "finding": "top3_recovery_helped_but_top5_recovery_hurt",
            "evidence": f"top3_delta_vs_desk={top3_delta:.4f};top5_delta_vs_desk={top5_delta:.4f}",
            "interpretation": "Recovery rule is useful in concentrated book but weak in broader book.",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1918",
            "diagnosis_id": "WATCHDECOMP-1918-002",
            "view": "candidate_count",
            "finding": "top5_has_more_recovered_rows_but_lower_increment_quality",
            "evidence": f"top3_recovery_rows={len(top3_recovery)};top5_recovery_rows={len(top5_recovery)}",
            "interpretation": "The recovery rule expands into lower-quality candidates in top5.",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1918",
            "diagnosis_id": "WATCHDECOMP-1918-003",
            "view": "root",
            "finding": "do_not_expand_recovery_beyond_top3_without_source_field_rule",
            "evidence": "Top5 deterioration means recovery candidates need a stricter predeclared source-field filter.",
            "interpretation": "Next rule should be top3-focused or add stricter eligibility before top5 use.",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        },
    ]
    if top5_only:
        rows_out.append(
            {
                "task_id": "Task1918",
                "diagnosis_id": "WATCHDECOMP-1918-004",
                "view": "slot_overlap",
                "finding": "top5_only_bucket_is_the_first_place_to_audit",
                "evidence": f"top5_only_increment={top5_only[0]['incremental_pnl_sum_audit_only']}",
                "interpretation": "Names admitted only by the wider book likely explain top5 fragility.",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows_out


def next_task_rows() -> list[dict[str, object]]:
    tasks = [
        ("Task1921", "Top3-Only Recovery Rule Freeze", "Research Governance", "Freeze a top3-only recovery rule using source fields, not audit outcomes."),
        ("Task1922", "Top5-Only Fragility Audit", "Quant Review", "Decompose top5-only recovered rows by source fields before any rerisk."),
        ("Task1923", "Recovery Eligibility Source Filter", "Winner Desk", "Create stricter source-field eligibility for recovery candidates."),
        ("Task1924", "Narrow Recovery Replay", "Backtest Infra", "Replay only the predeclared narrow source-field candidate set."),
        ("Task1925", "Drawdown Neutrality Check", "Risk", "Confirm recovery improves return without increasing MDD or cost fragility."),
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


def closeout_rows(diagnosis: list[dict[str, object]]) -> list[dict[str, object]]:
    metrics = {row["policy_variant_id"]: row for row in read_csv(TASK1901 / "task1906_watch_recovery_metrics.csv")}
    return [
        {
            "task_id": "Task1920",
            "verdict": "watch_recovery_decomposition_complete",
            "top3_delta_vs_desk_final": metrics["watch_recovery_top3_v1"]["delta_vs_desk_final"],
            "top5_delta_vs_desk_final": metrics["watch_recovery_top5_v1"]["delta_vs_desk_final"],
            "primary_bottleneck": "top5_recovery_candidate_quality_and_overlap_fragility",
            "next_action": "freeze top3-only or stricter source-field recovery before any additional replay",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def write_report(
    subtype_attr: list[dict[str, object]],
    cohort_attr: list[dict[str, object]],
    symbol_attr: list[dict[str, object]],
    diagnosis: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1911-1920 Watch Recovery Decomposition",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Top3 delta vs desk: {closeout['top3_delta_vs_desk_final']}.",
        f"- Top5 delta vs desk: {closeout['top5_delta_vs_desk_final']}.",
        f"- Primary bottleneck: `{closeout['primary_bottleneck']}`.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Subtype view:",
        "",
        "| Policy | Subtype | Rows | Capital Delta | Incremental PnL | Positive | Negative | Avg Return |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(subtype_attr, key=lambda item: (str(item.get("policy_variant_id")), str(item.get("watch_subtype")))):
        lines.append(
            f"| `{row['policy_variant_id']}` | `{row['watch_subtype']}` | {row['row_count']} | {row['capital_delta_sum']} | {row['incremental_pnl_sum_audit_only']} | {row['positive_incremental_count']} | {row['negative_incremental_count']} | {row['avg_net_return_audit_only']} |"
        )
    lines.extend(["", "Overlap/cohort view:", "", "| Policy | Cohort | Rows | Incremental PnL | Avg Return |", "| --- | --- | ---: | ---: | ---: |"])
    for row in sorted(cohort_attr, key=lambda item: (str(item.get("policy_variant_id")), str(item.get("slot_overlap_cohort")))):
        lines.append(
            f"| `{row['policy_variant_id']}` | `{row['slot_overlap_cohort']}` | {row['row_count']} | {row['incremental_pnl_sum_audit_only']} | {row['avg_net_return_audit_only']} |"
        )
    lines.extend(["", "Worst symbol view:", "", "| Policy | Symbol | Rows | Incremental PnL | Avg Return |", "| --- | --- | ---: | ---: | ---: |"])
    for row in sorted(symbol_attr, key=lambda item: to_float(item["incremental_pnl_sum_audit_only"]))[:12]:
        lines.append(
            f"| `{row['policy_variant_id']}` | `{row['symbol']}` | {row['row_count']} | {row['incremental_pnl_sum_audit_only']} | {row['avg_net_return_audit_only']} |"
        )
    lines.extend(["", "Diagnosis:", ""])
    for row in diagnosis:
        lines.append(f"- `{row['view']}`: {row['finding']} ({row['evidence']}).")
    lines.extend(
        [
            "",
            "Leakage audit:",
            "",
            "- This decomposition uses outcome deltas only for audit.",
            "- It does not create an assignment rule.",
            "- Any future narrowed replay must freeze source-field eligibility first.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Top3 improved because recovery was applied to a concentrated set where added capital helped.",
            "2. Top5 worsened because the same recovery rule reached weaker extra rows.",
            "3. The next filter must be stricter than just subtype.",
            "4. Do not expand recovery broadly.",
            "5. The top5-only bucket is the first fragility bucket to audit.",
            "6. Either keep recovery top3-only or create a source-field filter for top5.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1911_input_manifest.csv`",
            "- `task1912_policy_trade_delta.csv`",
            "- `task1913_subtype_view.csv`",
            "- `task1914_symbol_month_views.csv`",
            "- `task1915_overlap_cohort_view.csv`",
            "- `task1916_best_worst_recovery_rows.csv`",
            "- `task1917_narrow_candidate_audit.csv`",
            "- `task1918_diagnosis.csv`",
            "- `task1919_next_task_plan.csv`",
            "- `task1920_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1911_1920_watch_recovery_decomposition_validate.py`",
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
    joined = joined_delta_rows()
    cohort = cohort_rows(joined)
    subtype_attr = group_rows(joined, ["policy_variant_id", "watch_subtype"], "Task1913", "SUBTYPEVIEW-1913")
    action_attr = group_rows(joined, ["policy_variant_id", "recovery_action"], "Task1913", "ACTIONVIEW-1913")
    symbol_attr = group_rows(joined, ["policy_variant_id", "symbol"], "Task1914", "SYMBOLVIEW-1914")
    month_attr = group_rows(joined, ["policy_variant_id", "decision_month"], "Task1914", "MONTHVIEW-1914")
    cohort_attr = group_rows(cohort, ["policy_variant_id", "slot_overlap_cohort"], "Task1915", "COHORTVIEW-1915")
    best, worst = ranking_rows(joined)
    narrow = narrowed_candidate_rows(joined)
    diagnosis = diagnosis_rows(joined, cohort_attr, subtype_attr)
    next_tasks = next_task_rows()
    closeout = closeout_rows(diagnosis)
    outputs = [
        ("task1911_input_manifest.csv", input_manifest_rows()),
        ("task1912_policy_trade_delta.csv", joined),
        ("task1913_subtype_view.csv", subtype_attr),
        ("task1913_action_view.csv", action_attr),
        ("task1914_symbol_view.csv", symbol_attr),
        ("task1914_month_view.csv", month_attr),
        ("task1915_overlap_cohort_detail.csv", cohort),
        ("task1915_overlap_cohort_view.csv", cohort_attr),
        ("task1916_best_recovery_rows.csv", best),
        ("task1916_worst_recovery_rows.csv", worst),
        ("task1917_narrow_candidate_audit.csv", narrow),
        ("task1918_diagnosis.csv", diagnosis),
        ("task1919_next_task_plan.csv", next_tasks),
        ("task1920_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task1920_closeout.json", closeout[0])
    write_report(subtype_attr, cohort_attr, symbol_attr, diagnosis, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1911_1920] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
