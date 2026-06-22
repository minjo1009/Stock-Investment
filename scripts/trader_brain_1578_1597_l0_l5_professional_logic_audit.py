from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1578_1597_l0_l5_professional_logic_audit"
REPORT_DIR = ROOT / "docs/reports/task_1578_1597_l0_l5_professional_logic_audit"
REPORT = REPORT_DIR / "task_1578_1597_l0_l5_professional_logic_audit.md"
DECISION = REPORT_DIR / "task_1578_1597_decision.csv"

TASK1191 = ROOT / "data/artifacts/task_1191_1200_l0_l3_candidate_compression"
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1468 = ROOT / "data/artifacts/task_1468_1487_complete_implementation_contract"
TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK1518 = ROOT / "data/artifacts/task_1518_1537_l5_position_operating_brain"
TASK1538 = ROOT / "data/artifacts/task_1538_1557_l5_hold_sizing_audit"
TASK1558 = ROOT / "data/artifacts/task_1558_1577_l5_damage_control_engine"

AUTHORITY = "DIAGNOSTIC_L0_L5_PROFESSIONAL_LOGIC_AUDIT_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def expert_source_standard_rows() -> list[dict[str, object]]:
    rows = [
        (
            "SEC Form 8-K material event standard",
            "L1/L2",
            "Material current reports require event-family context, timing, item type, and materiality, not a generic good-news score.",
            "https://www.sec.gov/files/form8-k.pdf",
        ),
        (
            "MacKinlay event study standard",
            "L2/L5",
            "Event impact requires abnormal return and event-window separation from normal factor/market movement.",
            "https://www.bu.edu/econ/files/2011/01/MacKinlay-1996-Event-Studies-in-Economics-and-Finance.pdf",
        ),
        (
            "Fama-French factor context",
            "L0/L2/L4",
            "Stock selection and acceptance need market, size, value/profitability/investment context rather than raw return alone.",
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html",
        ),
        (
            "ALFRED vintage macro standard",
            "L1/L3",
            "Macro and regime inputs must be vintage/as-of, not current revised values.",
            "https://alfred.stlouisfed.org/",
        ),
        (
            "Complete implementation contract",
            "L0-L5",
            "Local Task1468-1487 contract defines source-time, event family, expectation, absorption, mechanism, thesis, and validation completion.",
            "data/artifacts/task_1468_1487_complete_implementation_contract",
        ),
    ]
    return [
        {
            "task_id": "Task1578",
            "standard_id": f"PROSTD1578-{idx:03d}",
            "standard_name": name,
            "mapped_layers": layers,
            "professional_requirement": req,
            "source_or_local_artifact": source,
            "authority": AUTHORITY,
        }
        for idx, (name, layers, req, source) in enumerate(rows, 1)
    ]


def implementation_inventory_rows() -> list[dict[str, object]]:
    files = [
        ("L0", TASK1191 / "task1191_l0_security_filter.csv", "tradability/liquidity/momentum/volatility filter"),
        ("L1", TASK1488 / "task1490_source_evidence_audit.csv", "source evidence audit"),
        ("L2", TASK1488 / "task1491_l2_semantic_v6_panel.csv", "semantic event/expectation/absorption/materiality panel"),
        ("L3", TASK1488 / "task1492_l3_mechanism_v3_edges.csv", "mechanism edges"),
        ("L4", TASK1488 / "task1493_l4_thesis_cards_v6.csv", "thesis cards"),
        ("L5", TASK1518 / "task1524_policy_specs_final.csv", "entry/sizing policy specs"),
        ("L5", TASK1518 / "task1523_exit_decision_panel.csv", "position exit decision panel"),
        ("L5", TASK1558 / "task1561_damage_action_panel.csv", "damage hold/reduce/exit/no-reentry actions"),
    ]
    rows: list[dict[str, object]] = []
    for idx, (layer, path, purpose) in enumerate(files, 1):
        exists = path.exists()
        row_count = len(read_csv(path)) if exists else 0
        columns = list(read_csv(path)[0].keys()) if exists and row_count else []
        rows.append(
            {
                "task_id": "Task1579",
                "inventory_id": f"IMPLEMENT1579-{idx:03d}",
                "layer": layer,
                "artifact_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "purpose": purpose,
                "exists": "1" if exists else "0",
                "row_count": row_count,
                "column_count": len(columns),
                "key_columns": ";".join(columns[:12]),
                "authority": AUTHORITY,
            }
        )
    return rows


def current_metric_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    sources = [
        ("Task1201 base", TASK1201 / "task1207_replay_metrics.csv"),
        ("Task1488 semantic v6", TASK1488 / "task1497_replay_metrics.csv"),
        ("Task1518 L5 operating", TASK1518 / "task1525_replay_metrics.csv"),
        ("Task1558 damage control", TASK1558 / "task1563_damage_replay_metrics.csv"),
    ]
    idx = 1
    for label, path in sources:
        if not path.exists():
            continue
        for row in read_csv(path):
            rows.append(
                {
                    "task_id": "Task1580",
                    "metric_id": f"METRIC1580-{idx:04d}",
                    "source_run": label,
                    "policy_variant_id": row.get("policy_variant_id", ""),
                    "final_equity": row.get("final_equity", ""),
                    "cagr": row.get("cagr", ""),
                    "max_drawdown": row.get("max_drawdown", ""),
                    "beats_qqq": row.get("beats_benchmark", row.get("beats_qqq", "")),
                    "target_cagr_30pct_met": row.get("target_cagr_30pct_met", ""),
                    "target_mdd_minus30pct_met": row.get("target_mdd_minus30pct_met", ""),
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def l2_distribution_rows() -> list[dict[str, object]]:
    l2 = read_csv(TASK1488 / "task1491_l2_semantic_v6_panel.csv")
    rows: list[dict[str, object]] = []
    fields = [
        ("event_family", "L2 event family"),
        ("expectation_v6_state", "L2 expectation"),
        ("absorption_v6_state", "L2 absorption"),
        ("materiality_v6_state", "L2 materiality"),
        ("source_independence_v2_state", "L2 source independence"),
    ]
    idx = 1
    for field, label in fields:
        counts = Counter(row[field] for row in l2)
        total = sum(counts.values())
        for value, count in sorted(counts.items()):
            rows.append(
                {
                    "task_id": "Task1581",
                    "distribution_id": f"L2DIST1581-{idx:04d}",
                    "field": field,
                    "label": label,
                    "value": value,
                    "row_count": count,
                    "row_share": pct(count, total),
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def l3_distribution_rows() -> list[dict[str, object]]:
    l3 = read_csv(TASK1488 / "task1492_l3_mechanism_v3_edges.csv")
    rows: list[dict[str, object]] = []
    idx = 1
    for field in ["edge_type", "edge_target", "edge_direction"]:
        counts = Counter(row[field] for row in l3)
        total = sum(counts.values())
        for value, count in sorted(counts.items()):
            rows.append(
                {
                    "task_id": "Task1582",
                    "distribution_id": f"L3DIST1582-{idx:04d}",
                    "field": field,
                    "value": value,
                    "row_count": count,
                    "row_share": pct(count, total),
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def l4_distribution_rows() -> list[dict[str, object]]:
    l4 = read_csv(TASK1488 / "task1493_l4_thesis_cards_v6.csv")
    rows: list[dict[str, object]] = []
    idx = 1
    for field in ["route", "primary_invalidation", "economic_mechanism"]:
        counts = Counter(row[field] for row in l4)
        total = sum(counts.values())
        for value, count in sorted(counts.items()):
            rows.append(
                {
                    "task_id": "Task1583",
                    "distribution_id": f"L4DIST1583-{idx:04d}",
                    "field": field,
                    "value": value,
                    "row_count": count,
                    "row_share": pct(count, total),
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def l5_action_rows() -> list[dict[str, object]]:
    actions = read_csv(TASK1558 / "task1561_damage_action_panel.csv")
    trades = read_csv(TASK1558 / "task1562_damage_replay_trades.csv")
    pnl_by_action: dict[tuple[str, str], float] = defaultdict(float)
    trades_by_action: Counter[tuple[str, str]] = Counter()
    for row in trades:
        key = (row["policy_variant_id"], row["damage_action"])
        pnl_by_action[key] += to_float(row.get("pnl"))
        trades_by_action[key] += 1
    counts = Counter((row["policy_variant_id"], row["damage_action"], row.get("damage_reason", "")) for row in actions)
    rows: list[dict[str, object]] = []
    for idx, ((policy, action, reason), count) in enumerate(sorted(counts.items()), 1):
        action_key = (policy, action)
        rows.append(
            {
                "task_id": "Task1584",
                "action_audit_id": f"L5ACT1584-{idx:04d}",
                "policy_variant_id": policy,
                "damage_action": action,
                "damage_reason": reason,
                "action_count": count,
                "trade_count_for_action": trades_by_action.get(action_key, 0),
                "total_pnl_for_action": round(pnl_by_action.get(action_key, 0.0), 4),
                "authority": AUTHORITY,
            }
        )
    return rows


def requirement_gap_rows() -> list[dict[str, object]]:
    l2 = read_csv(TASK1488 / "task1491_l2_semantic_v6_panel.csv")
    l3 = read_csv(TASK1488 / "task1492_l3_mechanism_v3_edges.csv")
    l4 = read_csv(TASK1488 / "task1493_l4_thesis_cards_v6.csv")
    specs = read_csv(TASK1518 / "task1524_policy_specs_final.csv")
    metrics = read_csv(TASK1558 / "task1563_damage_replay_metrics.csv")
    criteria = {row["criterion_name"]: row for row in read_csv(TASK1468 / "task1470_completion_criteria.csv")}
    total_l2 = len(l2)
    true_surprise = sum(1 for row in l2 if row["expectation_v6_state"] == "true_surprise_proxy")
    analyst_like = sum(1 for row in l2 if "analyst" in row["expectation_v6_reason"].lower() or "analyst" in row["expectation_v6_state"].lower())
    sustained = sum(1 for row in l2 if row["absorption_v6_state"] == "sustained_market_acceptance")
    initial_only = sum(1 for row in l2 if row["absorption_v6_state"] == "initial_reaction_only")
    materiality_gap = sum(1 for row in l2 if row["materiality_v6_state"] in {"unconfirmed_materiality_capped", "materiality_source_gap_neutral"})
    source_independent = sum(1 for row in l2 if row["source_independence_v2_state"] == "independent_non_issuer_confirmation_present")
    generic_invalidation = sum(1 for row in l4 if row["primary_invalidation"] == "source_gap_or_thesis_decay")
    generic_mechanism = sum(1 for row in l4 if row["economic_mechanism"] in {"economic_receipt", "shareholder_transfer_risk", "source_gap"})
    source_gap_specs = sum(1 for row in specs if row["thesis_state"] in {"confirmation_wait", "source_gap_watch"})
    best_damage = max(metrics, key=lambda row: to_float(row["final_equity"]))
    gap_defs = [
        (
            "L0",
            "factor_regime_context",
            "missing_professional_logic",
            "Fama-French/AQR style factor and regime exposure are not a first-class state in current L0 selection.",
            "L0 currently filters tradability/liquidity but does not normalize expected return by factor, macro vintage, or regime exposure.",
            "Add source-time-safe factor/regime panel as context, not as overfit filter.",
            3,
        ),
        (
            "L1",
            "analyst_pit_and_external_expectation",
            "missing_data_and_logic",
            "Professional expectation gap needs PIT analyst/estimate/prior baseline data.",
            f"Only proxy surprise exists; analyst-like expectation rows detected={analyst_like}/{total_l2}.",
            "Acquire or explicitly stub licensed analyst PIT/estimate revision feed; keep proxy separate.",
            5,
        ),
        (
            "L2",
            "surprise_expectation_quality",
            "weak_logic_from_missing_inputs",
            criteria["expectation_quality"]["done_means"],
            f"true_surprise_proxy rows={true_surprise}/{total_l2}; good-words/proxy still dominate selected signals.",
            "Split true PIT surprise, explicit guidance change, and good words in scoring and L5 hold/re-risk.",
            5,
        ),
        (
            "L2",
            "market_absorption_quality",
            "partially_implemented_but_shallow",
            criteria["absorption_quality"]["done_means"],
            f"sustained_market_acceptance={sustained}/{total_l2}; initial_reaction_only={initial_only}/{total_l2}. No full volume/relative-strength/reversal ledger in L5 actions.",
            "Promote persistence/reversal/volume quality to L5 hold/re-risk, not just rank score.",
            4,
        ),
        (
            "L2",
            "materiality_denominator_quality",
            "partially_implemented_but_gap_heavy",
            criteria["materiality_conditionality"]["done_means"],
            f"materiality gap/capped rows={materiality_gap}/{total_l2}.",
            "Use verified revenue/market-cap/backlog denominators and sector-specific denominator fields.",
            4,
        ),
        (
            "L3",
            "causal_mechanism_precision",
            "weak_logic",
            criteria["mechanism_edges"]["done_means"],
            f"generic L4 mechanism rows={generic_mechanism}/{len(l4)}; L3 edges exist but remain mostly routing labels rather than quantified causal chains.",
            "Make mechanism edges carry expected payoff path: revenue timing, margin, dilution, cash runway, budget source.",
            4,
        ),
        (
            "L4",
            "thesis_card_invalidation_specificity",
            "weak_logic",
            criteria["thesis_card"]["done_means"],
            f"generic primary_invalidation source_gap_or_thesis_decay={generic_invalidation}/{len(l4)}.",
            "Replace generic invalidation with concrete thesis invalidators and update triggers.",
            4,
        ),
        (
            "L5",
            "position_operation_vs_alpha_tradeoff",
            "implementation_now_functional_but_incomplete",
            "L5 should convert thesis state to entry, hold, reduce, exit, no-reentry, and re-risk without chasing outcomes.",
            f"Damage control best final={best_damage['final_equity']} CAGR={best_damage['cagr']} MDD={best_damage['max_drawdown']}; MDD fixed but CAGR target still fails.",
            "Add source-confirmed re-risking and payoff-preserving recovery logic after reduce, with pre-registered gates.",
            4,
        ),
        (
            "Validation",
            "split_oos_overfit_controls",
            "incomplete_validation",
            "Professional validation requires split/OOS, cost/slippage, source audit, and overfit ledger before acceptance.",
            "Current runs are diagnostic single-policy progressions; validators preserve NOT_ACCEPTED.",
            "Freeze next policy family and run split/OOS plus cost/slippage once logic gap is addressed.",
            5,
        ),
    ]
    return [
        {
            "task_id": "Task1585",
            "gap_id": f"PROGAP1585-{idx:03d}",
            "layer": layer,
            "gap_name": name,
            "gap_type": gap_type,
            "professional_standard": standard,
            "current_evidence": evidence,
            "required_fix": fix,
            "severity_1_to_5": severity,
            "authority": AUTHORITY,
        }
        for idx, (layer, name, gap_type, standard, evidence, fix, severity) in enumerate(gap_defs, 1)
    ]


def root_cause_rows(gaps: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [
        (
            "ROOT1590-001",
            "not_mainly_file_generation_bug",
            "The implementation creates coherent artifacts and validators catch governance flags, so the failure is not simply broken CSV plumbing.",
            "Code structure is functional but professional decision logic remains incomplete.",
        ),
        (
            "ROOT1590-002",
            "core_missing_bridge_is_expectation_to_payoff",
            "L2 can label positive/mixed/risk, but it rarely proves why the market has not already priced the event.",
            "Without PIT expectation gap and factor-adjusted abnormal response, alpha and risk remain traded off manually.",
        ),
        (
            "ROOT1590-003",
            "risk_logic_is_actionable_before_alpha_logic_is_complete",
            "Damage control can lower MDD because price/source risk is easier to observe than future payoff magnitude.",
            "This explains the loop: risk-off reduces losses but also cuts upside because re-risk/re-acceleration logic is weak.",
        ),
        (
            "ROOT1590-004",
            "relationship_graph_is_semantic_not_yet_economic_sizing_graph",
            "L3 has edges, but not enough quantified causal pathway fields such as revenue timing, margin, dilution, cash runway, and market expectation path.",
            "The graph explains direction better than trade sizing or expected payoff.",
        ),
        (
            "ROOT1590-005",
            "validation_is_diagnostic_not_institutional_acceptance",
            "The repo correctly keeps NOT_ACCEPTED, but the current loop still uses sequential diagnostic tuning rather than a frozen OOS acceptance family.",
            "Need one professional logic repair, then freeze and test; not endless post-result tweaking.",
        ),
    ]
    return [
        {
            "task_id": "Task1590",
            "root_cause_id": rid,
            "root_cause": cause,
            "evidence": evidence,
            "decision": decision,
            "authority": AUTHORITY,
        }
        for rid, cause, evidence, decision in rows
    ]


def build_gate_closeout(gaps: list[dict[str, object]], roots: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    severe = [row for row in gaps if int(row["severity_1_to_5"]) >= 4]
    missing = [row for row in gaps if "missing" in row["gap_type"]]
    gate = [
        {
            "task_id": "Task1596",
            "audit_verdict": "professional_logic_gap_confirmed",
            "implementation_plumbing_broken": "0",
            "professional_logic_missing_or_weak": "1",
            "severe_gap_count": len(severe),
            "missing_logic_or_data_gap_count": len(missing),
            "primary_next_fix": "expectation_to_payoff_and_re_risk_bridge",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1597",
            "verdict": "l0_l5_professional_logic_audit_complete_not_accepted",
            "answer_to_user_question": "implementation_is_not_randomly_broken_but_professional_logic_is_incomplete_and_partly_shallow",
            "most_important_gap": "PIT expectation gap plus factor-adjusted market acceptance not connected to L5 re-risking",
            "next_action": "implement expectation-to-payoff-to-re-risk bridge before more MDD/CAGR toggling",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(
    standards: list[dict[str, object]],
    metrics: list[dict[str, object]],
    gaps: list[dict[str, object]],
    roots: list[dict[str, object]],
    gate: dict[str, object],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1578-1597 L0-L5 Professional Logic Audit",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        "- Direct answer: implementation plumbing is not the main failure; professional trading logic is incomplete and too shallow in key bridges.",
        "- Main weak point: expectation -> payoff -> L5 re-risk bridge.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Current run ladder:",
        "",
        "| Run | Policy | Final | CAGR | MDD | CAGR 30% | MDD -30% |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| {row['source_run']} | `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |"
        )
    lines.extend(
        [
            "",
            "Professional standards used:",
            "",
        ]
    )
    for row in standards:
        lines.append(f"- `{row['standard_name']}` ({row['mapped_layers']}): {row['professional_requirement']} Source: {row['source_or_local_artifact']}")
    lines.extend(
        [
            "",
            "Layer gaps:",
            "",
            "| Layer | Gap | Type | Severity | Current Evidence | Required Fix |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in gaps:
        lines.append(
            f"| {row['layer']} | `{row['gap_name']}` | `{row['gap_type']}` | {row['severity_1_to_5']} | {row['current_evidence']} | {row['required_fix']} |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. 코드가 완전히 엉터리라서 망한 것은 아닙니다.",
            "2. 파일 생성, row lineage, validator, 상태 보존은 꽤 작동합니다.",
            "3. 문제는 전문 트레이더 로직의 핵심 다리가 덜 구현된 것입니다.",
            "4. 가장 약한 다리는 `기대 대비 충격 -> 예상 payoff -> 줄인 포지션 재확대`입니다.",
            "5. 그래서 MDD를 줄이면 수익도 같이 줄고, 수익을 늘리면 MDD가 다시 커집니다.",
            "6. 다음은 새 필터가 아니라 expectation-to-payoff-to-re-risk bridge를 구현해야 합니다.",
            "",
            "## Root Causes",
            "",
        ]
    )
    for row in roots:
        lines.append(f"- `{row['root_cause']}`: {row['decision']} Evidence: {row['evidence']}")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "- `task1578_professional_source_standards.csv`",
            "- `task1579_implementation_inventory.csv`",
            "- `task1580_current_metric_ladder.csv`",
            "- `task1581_l2_distribution_audit.csv`",
            "- `task1582_l3_distribution_audit.csv`",
            "- `task1583_l4_distribution_audit.csv`",
            "- `task1584_l5_action_audit.csv`",
            "- `task1585_requirement_gap_matrix.csv`",
            "- `task1590_root_cause_matrix.csv`",
            "- `task1596_acceptance_gate.csv`",
            "- `task1597_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1578_1597_l0_l5_professional_logic_audit_validate.py`",
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
    standards = expert_source_standard_rows()
    inventory = implementation_inventory_rows()
    metrics = current_metric_rows()
    l2_dist = l2_distribution_rows()
    l3_dist = l3_distribution_rows()
    l4_dist = l4_distribution_rows()
    l5_actions = l5_action_rows()
    gaps = requirement_gap_rows()
    roots = root_cause_rows(gaps)
    gate, closeout = build_gate_closeout(gaps, roots)

    write_csv(OUT_DIR / "task1578_professional_source_standards.csv", standards)
    write_csv(OUT_DIR / "task1579_implementation_inventory.csv", inventory)
    write_csv(OUT_DIR / "task1580_current_metric_ladder.csv", metrics)
    write_csv(OUT_DIR / "task1581_l2_distribution_audit.csv", l2_dist)
    write_csv(OUT_DIR / "task1582_l3_distribution_audit.csv", l3_dist)
    write_csv(OUT_DIR / "task1583_l4_distribution_audit.csv", l4_dist)
    write_csv(OUT_DIR / "task1584_l5_action_audit.csv", l5_actions)
    write_csv(OUT_DIR / "task1585_requirement_gap_matrix.csv", gaps)
    write_csv(OUT_DIR / "task1590_root_cause_matrix.csv", roots)
    write_csv(OUT_DIR / "task1596_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1597_closeout.csv", closeout)
    write_json(OUT_DIR / "task1597_closeout.json", closeout[0])
    write_csv(DECISION, gate)
    write_report(standards, metrics, gaps, roots, gate[0], closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1578_1597] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
