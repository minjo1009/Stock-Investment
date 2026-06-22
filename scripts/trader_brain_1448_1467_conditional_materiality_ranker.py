from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1388 = ROOT / "data/artifacts/task_1388_1407_expert_reviewed_judgment_replay"
TASK1408 = ROOT / "data/artifacts/task_1408_1427_ruler_acquisition_replay"
TASK1428 = ROOT / "data/artifacts/task_1428_1447_full_ruler_source_time_acquisition"
OUT_DIR = ROOT / "data/artifacts/task_1448_1467_conditional_materiality_ranker"
REPORT_DIR = ROOT / "docs/reports/task_1448_1467_conditional_materiality_ranker"

AUTHORITY = "DIAGNOSTIC_CONDITIONAL_MATERIALITY_RANKER_ONLY"

POLICIES = {"conditional_materiality_top3_v1": 3, "conditional_materiality_top5_v1": 5, "conditional_materiality_top10_v1": 10}


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


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def expert_review_rows() -> list[dict[str, object]]:
    rows = [
        ("institutional_quant", "adopt", "materiality alone is not alpha; gate it by event type, expectation, and market acceptance"),
        ("institutional_risk", "modify", "small-cap ratio winsorization is necessary but must be pre-registered and as-of"),
        ("sector_semiconductor", "adopt", "contract size needs customer, supply constraint, margin, and export-control context"),
        ("sector_ai_software", "adopt", "AI mentions are weak unless ARR, gross margin, customer lock-in, or capacity access improves"),
        ("sector_space", "adopt", "contract value must be split from funded backlog, launch/license, and milestone payment risk"),
        ("sector_power_grid", "adopt", "orders are positive only when capacity, grid connection, and cost recovery are not the main issue"),
        ("sector_biotech", "adopt", "trial/FDA milestones are not automatically positive; cash runway and dilution must dominate survival events"),
        ("backend_data", "adopt", "winner displacement audit is allowed only as outcome-audit and cannot feed assignment directly"),
        ("backtest_governance", "adopt", "one pre-registered v5 replay; no result-driven reweighting inside this task"),
        ("source_time", "adopt", "keep available_to_brain_ts <= decision_asof_ts and missing labels non-negative"),
    ]
    return [
        {
            "task_id": "Task1448",
            "review_id": f"REVIEW1448-{idx:03d}",
            "expert_role": role,
            "verdict": verdict,
            "critique": critique,
            "review_authority": "GPT_SUBAGENT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, verdict, critique) in enumerate(rows, 1)
    ]


def preregister_spec() -> list[dict[str, object]]:
    specs = [
        ("materiality_gate", "high materiality receives full credit only when event type is positive and expectation/absorption are strict"),
        ("small_cap_cap", "micro-cap ratio effects are capped; small-cap ratio effects are partially capped"),
        ("event_type_split", "public money events split into positive, survival, financing, dilution, mixed, or unknown"),
        ("expectation_strictness", "positive guidance proxy requires at least two positive term hits and no negative term hit"),
        ("absorption_strictness", "strict absorption requires event-to-decision relative return >= 8pct and relative volume >= 1.05"),
        ("audit_only_outcomes", "old winner/new promoted loser realized returns are recorded only in audit artifacts"),
        ("replay_freeze", "top3/top5/top10 policy, costs, entry/exit, universe, and benchmark are unchanged from prior replay"),
    ]
    return [
        {
            "task_id": "Task1449",
            "spec_id": f"V5SPEC1449-{idx:03d}",
            "rule_name": name,
            "pre_registered_rule": rule,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, rule) in enumerate(specs, 1)
    ]


def event_family(row: dict[str, str], enriched: dict[str, dict[str, str]]) -> tuple[str, str]:
    text = " ".join(
        [
            row.get("event_value_type", ""),
            row.get("value_context_excerpt", ""),
            enriched.get(row["candidate_source_id"], {}).get("full_candidate_composite_interpretation", ""),
            enriched.get(row["candidate_source_id"], {}).get("derived_theme", ""),
        ]
    ).lower()
    dilution_terms = ["warrant", "atm", "registered direct", "private placement", "equity offering", "convertible", "share issuance", "dilution"]
    survival_terms = ["going concern", "delist", "bankrupt", "default", "material weakness", "restructuring", "covenant", "cash runway"]
    financing_terms = ["senior notes", "credit facility", "loan", "debt", "financing", "liquidity", "cash", "offering"]
    positive_terms = ["contract", "award", "purchase order", "customer", "backlog", "revenue", "booking", "approval", "supply agreement"]
    if any(term in text for term in dilution_terms):
        return "dilution", "dilution_or_convertible_equity_language"
    if any(term in text for term in survival_terms):
        return "survival", "survival_or_distress_language"
    if any(term in text for term in financing_terms):
        return "financing", "financing_or_balance_sheet_language"
    if any(term in text for term in positive_terms):
        return "positive", "contract_customer_backlog_or_revenue_language"
    if "clinical" in text or "phase" in text or "fda" in text:
        return "mixed", "biotech_milestone_without_endpoint_confirmation"
    return "unknown", "no_clear_event_family"


def strict_expectation(guidance: dict[str, str]) -> tuple[str, float]:
    pos = int(to_float(guidance.get("positive_term_hits")))
    neg = int(to_float(guidance.get("negative_term_hits")))
    direction = guidance.get("public_guidance_direction", "")
    if direction.startswith("positive") and pos >= 2 and neg == 0:
        return "strict_positive_expectation_proxy", 12.0
    if direction.startswith("positive"):
        return "broad_positive_words_only", 3.0
    if direction.startswith("negative") or neg > pos:
        return "negative_expectation_proxy", -12.0
    if direction.startswith("mixed"):
        return "mixed_expectation_proxy", -4.0
    return "expectation_source_gap_or_weak", 0.0


def strict_absorption(absorption: dict[str, str]) -> tuple[str, float]:
    rel = to_float(absorption.get("event_to_decision_relative_return"))
    vol = to_float(absorption.get("decision_relative_volume"))
    if absorption.get("absorption_window_pass") != "1":
        return "absorption_source_gap", 0.0
    if rel >= 0.08 and vol >= 1.05:
        return "strict_sustained_market_acceptance", 12.0
    if rel >= 0.05:
        return "broad_price_followthrough_only", 3.0
    if rel <= -0.08:
        return "pre_decision_market_rejection", -16.0
    return "neutral_absorption", 0.0


def materiality_component(mat: dict[str, str], market: dict[str, str], family: str, exp_state: str, abs_state: str) -> tuple[str, float, str]:
    state = mat.get("materiality_ruler_state", "")
    mcap = to_float(market.get("market_cap_proxy_usd"))
    if state == "materiality_source_gap":
        return "materiality_source_gap_zero", 0.0, "source_gap_not_negative"
    base = {"high_verified_materiality": 18.0, "medium_verified_materiality": 8.0, "low_verified_materiality": 2.0}.get(state, 0.0)
    cap_reason = "none"
    if family in {"dilution", "survival"}:
        return f"{family}_materiality_penalty", -18.0 if family == "survival" else -24.0, "negative_event_family"
    if family == "financing":
        return "financing_materiality_capped", min(base, 2.0), "financing_not_alpha_by_default"
    if family in {"mixed", "unknown"}:
        base = min(base, 4.0)
        cap_reason = "event_family_not_confirmed_positive"
    if exp_state != "strict_positive_expectation_proxy":
        base = min(base, 6.0)
        cap_reason = "expectation_not_strict"
    if abs_state != "strict_sustained_market_acceptance":
        base = min(base, 6.0)
        cap_reason = "absorption_not_strict"
    if mcap and mcap < 300_000_000:
        base = min(base, 4.0)
        cap_reason = "micro_cap_ratio_cap"
    elif mcap and mcap < 2_000_000_000:
        base = min(base, 8.0)
        cap_reason = "small_cap_ratio_cap"
    return "conditional_positive_materiality", base, cap_reason


def build_v5_panels() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    full_rank = read_csv(TASK1428 / "task1445_payoff_ranker_v4.csv")
    mat = {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1434_full_materiality_ruler_panel.csv")}
    market = {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1433_full_market_cap_proxy_panel.csv")}
    event = {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1412_event_value_panel.csv")}
    guidance = {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1415_public_guidance_revision_panel.csv")}
    absorption = {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1418_market_absorption_enhanced_panel.csv")}
    enriched = {row["candidate_source_id"]: row for row in read_csv(TASK1388 / "task1394_l2_enriched_judgment_panel.csv")}
    event_rows: list[dict[str, object]] = []
    score_rows: list[dict[str, object]] = []
    for idx, row in enumerate(full_rank, 1):
        cid = row["candidate_source_id"]
        family, reason = event_family(event[cid], enriched)
        exp_state, exp_score = strict_expectation(guidance[cid])
        abs_state, abs_score = strict_absorption(absorption[cid])
        mat_state, mat_score, cap_reason = materiality_component(mat[cid], market[cid], family, exp_state, abs_state)
        candidate_rank = int(to_float(row.get("candidate_rank"), 9999))
        base_quality = max(0.0, 14.0 - candidate_rank * 0.10)
        independence = 7.0 if row.get("source_independence_v2_state") == "independent_non_issuer_confirmation_present" else 2.0
        family_bonus = 6.0 if family == "positive" else 0.0
        family_penalty = -10.0 if family in {"survival", "dilution"} else (-3.0 if family == "financing" else 0.0)
        score = base_quality + mat_score + exp_score + abs_score + independence + family_bonus + family_penalty
        event_rows.append(
            {
                "task_id": "Task1450",
                "event_type_row_id": f"EVENTTYPE1450-{idx:07d}",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "event_family": family,
                "event_family_reason": reason,
                "event_value_usd": event[cid].get("event_value_usd", ""),
                "market_cap_proxy_usd": market[cid].get("market_cap_proxy_usd", ""),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        score_rows.append(
            {
                "task_id": "Task1453",
                "score_row_id": f"V5SCORE1453-{idx:07d}",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "candidate_rank": candidate_rank,
                "derived_theme": row.get("derived_theme", ""),
                "event_family": family,
                "materiality_ruler_state": mat[cid]["materiality_ruler_state"],
                "conditional_materiality_state": mat_state,
                "conditional_materiality_score": round(mat_score, 4),
                "materiality_cap_reason": cap_reason,
                "expectation_strict_state": exp_state,
                "expectation_v5_score": round(exp_score, 4),
                "absorption_strict_state": abs_state,
                "absorption_v5_score": round(abs_score, 4),
                "source_independence_score": round(independence, 4),
                "event_family_bonus": round(family_bonus, 4),
                "event_family_penalty": round(family_penalty, 4),
                "base_quality_score": round(base_quality, 4),
                "conditional_materiality_rank_score": round(score, 4),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in score_rows:
        by_decision[str(row["decision_asof_ts"])].append(row)
    rank_rows: list[dict[str, object]] = []
    for decision_ts, rows in by_decision.items():
        ordered = sorted(rows, key=lambda item: (-to_float(item["conditional_materiality_rank_score"]), int(item["candidate_rank"])))
        for rank, row in enumerate(ordered, 1):
            rank_rows.append(
                {
                    "task_id": "Task1454",
                    "rank_row_id": f"V5RANK1454-{len(rank_rows)+1:07d}",
                    **{key: row[key] for key in row if key not in {"task_id", "score_row_id"}},
                    "conditional_materiality_rank_within_decision": rank,
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return event_rows, score_rows, rank_rows


def select_policy_specs(rank_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rank_rows:
        by_decision[str(row["decision_asof_ts"])].append(row)
    selected: list[dict[str, object]] = []
    for policy_id, slot_cap in POLICIES.items():
        for decision_ts, rows in by_decision.items():
            ordered = sorted(rows, key=lambda item: (int(item["conditional_materiality_rank_within_decision"]), int(item["candidate_rank"])))[:slot_cap]
            for row in ordered:
                selected.append(
                    {
                        "task_id": "Task1455",
                        "policy_spec_id": f"{policy_id}:{row['trade_spec_id']}",
                        "policy_variant_id": policy_id,
                        "slot_cap": slot_cap,
                        "candidate_source_id": row["candidate_source_id"],
                        "trade_spec_id": row["trade_spec_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "conditional_materiality_rank_score": row["conditional_materiality_rank_score"],
                        "conditional_materiality_rank_within_decision": row["conditional_materiality_rank_within_decision"],
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
    return selected


def build_displacement_audit(rank_rows: list[dict[str, object]], trades: list[dict[str, object]]) -> list[dict[str, object]]:
    old = [row for row in read_csv(TASK1408 / "task1426_policy_specs.csv") if row["policy_variant_id"] == "ruler_top3_v1"]
    full = [row for row in read_csv(TASK1428 / "task1446_policy_specs.csv") if row["policy_variant_id"] == "ruler_top3_v1"]
    v5 = [row for row in select_policy_specs(rank_rows) if row["policy_variant_id"] == "conditional_materiality_top3_v1"]
    trade_lookup = {
        (row["policy_variant_id"], row["decision_asof_ts"], row["trade_spec_id"]): row
        for row in list(read_csv(TASK1408 / "task1426_replay_trades.csv")) + list(read_csv(TASK1428 / "task1446_replay_trades.csv"))
    }
    for row in trades:
        trade_lookup[(str(row["policy_variant_id"]), str(row["decision_asof_ts"]), str(row["trade_spec_id"]))] = {k: str(v) for k, v in row.items()}
    rank_by_tid = {str(row["trade_spec_id"]): row for row in rank_rows}
    sets = {
        "sparse_top3": set((row["decision_asof_ts"], row["trade_spec_id"]) for row in old),
        "full_top3": set((row["decision_asof_ts"], row["trade_spec_id"]) for row in full),
        "v5_top3": set((row["decision_asof_ts"], row["trade_spec_id"]) for row in v5),
    }
    groups = {
        "displaced_by_full_coverage": sets["sparse_top3"] - sets["full_top3"],
        "promoted_by_full_coverage": sets["full_top3"] - sets["sparse_top3"],
        "restored_or_kept_by_v5": sets["v5_top3"] & sets["sparse_top3"],
        "new_v5_not_sparse": sets["v5_top3"] - sets["sparse_top3"],
    }
    rows: list[dict[str, object]] = []
    for group, keys in groups.items():
        for idx, (decision_ts, trade_spec_id) in enumerate(sorted(keys), 1):
            rank = rank_by_tid.get(trade_spec_id, {})
            old_trade = trade_lookup.get(("ruler_top3_v1", decision_ts, trade_spec_id), {})
            full_trade = trade_lookup.get(("ruler_top3_v1", decision_ts, trade_spec_id), old_trade)
            v5_trade = trade_lookup.get(("conditional_materiality_top3_v1", decision_ts, trade_spec_id), {})
            rows.append(
                {
                    "task_id": "Task1458",
                    "audit_id": f"AUDIT1458-{group}-{idx:04d}",
                    "audit_group": group,
                    "decision_asof_ts": decision_ts,
                    "trade_spec_id": trade_spec_id,
                    "symbol": rank.get("symbol", ""),
                    "event_family": rank.get("event_family", ""),
                    "conditional_materiality_state": rank.get("conditional_materiality_state", ""),
                    "materiality_cap_reason": rank.get("materiality_cap_reason", ""),
                    "expectation_strict_state": rank.get("expectation_strict_state", ""),
                    "absorption_strict_state": rank.get("absorption_strict_state", ""),
                    "conditional_materiality_rank_score": rank.get("conditional_materiality_rank_score", ""),
                    "conditional_materiality_rank_within_decision": rank.get("conditional_materiality_rank_within_decision", ""),
                    "evaluation_sparse_return": old_trade.get("net_return", ""),
                    "evaluation_full_return": full_trade.get("net_return", ""),
                    "evaluation_v5_return": v5_trade.get("net_return", ""),
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build_summary(metrics: list[dict[str, object]], event_rows: list[dict[str, object]], rank_rows: list[dict[str, object]], audit_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    event_counts = Counter(str(row["event_family"]) for row in event_rows)
    top3 = [row for row in rank_rows if int(row["conditional_materiality_rank_within_decision"]) <= 3]
    top3_events = Counter(str(row["event_family"]) for row in top3)
    summary = [
        {"task_id": "Task1459", "summary_area": "event_family_all_candidates", "metric": key, "value": value, "authority": AUTHORITY}
        for key, value in sorted(event_counts.items())
    ] + [
        {"task_id": "Task1459", "summary_area": "event_family_top3", "metric": key, "value": value, "authority": AUTHORITY}
        for key, value in sorted(top3_events.items())
    ]
    audit_counts = Counter(str(row["audit_group"]) for row in audit_rows)
    summary += [
        {"task_id": "Task1459", "summary_area": "audit_group_rows", "metric": key, "value": value, "authority": AUTHORITY}
        for key, value in sorted(audit_counts.items())
    ]
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    gate = [
        {
            "task_id": "Task1466",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "target_cagr_30pct_met": best["target_cagr_30pct_met"],
            "target_mdd_minus30pct_met": best["target_mdd_minus30pct_met"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "diagnostic_conditional_materiality_ranker_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1467",
            "verdict": "conditional_materiality_ranker_diagnostic_not_accepted",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "candidate_rows": len(event_rows),
            "audit_rows": len(audit_rows),
            "next_action": "review v5 displacement audit and add true expectation/source receipt data before acceptance claims",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return summary, gate, closeout


def write_report(metrics: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    report = f"""# Task1448-1467 Conditional Materiality Ranker

## Decision Summary

- Verdict: `conditional_materiality_ranker_diagnostic_not_accepted`.
- Best policy: `{best['policy_variant_id']}`.
- Best final equity: {best['final_equity']}.
- Best CAGR: {best['cagr']}.
- Best MDD: {best['max_drawdown']}.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: high materiality is no longer a standalone bonus. It is gated by event family, small-cap cap, strict expectation, and strict absorption.
- Next action: review v5 displacement audit and acquire true expectation/source-receipt data before any acceptance claim.

## Quant Expert Report

- Data source: Task1428 full-coverage SEC companyfacts denominator panel and Task1318 source evidence.
- Pre-registration: score rules, caps, tie-breakers, and replay policies were fixed before this replay.
- Leakage audit: realized returns appear only in Task1458 audit columns and are not used for assignment.
- Expert review: institutional, sector, and backend reviews are review-only and not source-of-truth.
- Replay setup: top3/top5/top10, entry/exit, cost, benchmark, and universe are unchanged.

Policy metrics:

| Policy | Final | CAGR | MDD | Trades | Source Exit | Price Exit | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for row in sorted(metrics, key=lambda item: str(item["policy_variant_id"])):
        report += (
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | "
            f"{row['trade_count']} | {row['source_receipt_exit_count']} | {row['price_path_exit_count']} | "
            f"{row['beats_benchmark']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |\n"
        )
    report += """
## No-Background Decision-Maker Report

처방은 구현했다.

materiality를 단독 점수에서 조건부 점수로 바꿨다.

결과는 diagnostic이다.

전략은 아직 승인되지 않았다.

## Artifact Manifest

- `task1448_expert_review_synthesis.csv`
- `task1449_v5_preregistered_spec.csv`
- `task1450_event_family_panel.csv`
- `task1453_conditional_materiality_score_panel.csv`
- `task1454_payoff_ranker_v5.csv`
- `task1455_policy_specs.csv`
- `task1456_replay_trades.csv`
- `task1456_replay_equity.csv`
- `task1456_replay_metrics.csv`
- `task1458_displacement_audit.csv`
- `task1459_summary.csv`
- `task1466_acceptance_gate.csv`
- `task1467_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1448_1467_conditional_materiality_ranker_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1448_1467_conditional_materiality_ranker.md").write_text(report, encoding="utf-8")
    write_csv(REPORT_DIR / "task_1448_1467_decision.csv", [closeout])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    replay.AUTHORITY = AUTHORITY
    replay.POLICIES = POLICIES
    enriched, specs, _bindings, filing_bindings, evidence = replay.load_inputs()
    expert = expert_review_rows()
    spec = preregister_spec()
    event_rows, score_rows, rank_rows = build_v5_panels()
    policy_specs = select_policy_specs(rank_rows)
    price_cache: dict[str, object] = {}
    symbol_filings, accession_text = replay.build_filing_indexes(filing_bindings, evidence)
    source_exits, price_exits, hold_receipts = replay.build_exit_panels(policy_specs, specs, symbol_filings, accession_text, price_cache)
    trades, equity = replay.run_replay(policy_specs, specs, source_exits, price_exits, price_cache)
    metrics = replay.build_metrics(trades, equity)
    audit = build_displacement_audit(rank_rows, trades)
    summary, gate, closeout = build_summary(metrics, event_rows, rank_rows, audit)
    outputs = [
        ("task1448_expert_review_synthesis.csv", expert),
        ("task1449_v5_preregistered_spec.csv", spec),
        ("task1450_event_family_panel.csv", event_rows),
        ("task1453_conditional_materiality_score_panel.csv", score_rows),
        ("task1454_payoff_ranker_v5.csv", rank_rows),
        ("task1455_policy_specs.csv", policy_specs),
        ("task1456_source_receipt_exit_panel.csv", source_exits),
        ("task1456_price_path_exit_panel.csv", price_exits),
        ("task1456_hold_receipt_panel.csv", hold_receipts),
        ("task1456_replay_trades.csv", trades),
        ("task1456_replay_equity.csv", equity),
        ("task1456_replay_metrics.csv", metrics),
        ("task1458_displacement_audit.csv", audit),
        ("task1459_summary.csv", summary),
        ("task1466_acceptance_gate.csv", gate),
        ("task1467_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1467_closeout.json", closeout[0])
    write_report(metrics, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
