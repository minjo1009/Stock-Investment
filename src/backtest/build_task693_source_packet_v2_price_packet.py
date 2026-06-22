from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest import build_task678_active_cap3_winner_archetype as t678


TASK636_DIR = Path("docs/reports/task_636_full_period_content_prediction_backtest")
TASK691_DIR = Path("docs/reports/task_691_slot_leader_contender_review")
TASK692_DIR = Path("docs/reports/task_692_source_packet_price_absorption")
TASK693_DIR = Path("docs/reports/task_693_source_packet_v2_price_packet")

FORBIDDEN_COLUMNS = {
    "net_return_from_entry",
    "net_return_pct",
    "return_pct",
    "win_flag",
    "win_eval_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
    "simulated_exit_price",
    "simulated_exit_ts",
}

IDENTITY = ["lifecycle_id", "symbol", "entry_ts", "entry_ts_utc", "theme_id", "split_name"]
ECONOMIC_PATTERNS = {
    "contract": r"\b(contract|agreement|award|awarded|deal|partnership|purchase order)\b",
    "customer": r"\b(customer|client|counterparty|partner|department of defense|dod|nasa|government|enterprise)\b",
    "order_backlog": r"\b(order|orders|backlog|bookings|reservation|pipeline)\b",
    "revenue": r"\b(revenue|sales|arr|annual recurring|subscription|monetization)\b",
    "guidance": r"\b(guidance|forecast|outlook|raise|raised|expects|expectation)\b",
    "margin": r"\b(margin|profitability|gross profit|operating income|ebitda|cost savings)\b",
    "supply_demand": r"\b(demand|supply|capacity|shortage|utilization|production)\b",
}
GENERIC_FILING_TERMS = ["form 4", " 4 ", "144", "schedule 13g", "sc 13g", "13g/a", "13d/a"]


def build_task693_program(
    task636_dir: Path = TASK636_DIR,
    task691_dir: Path = TASK691_DIR,
    task692_dir: Path = TASK692_DIR,
) -> dict[str, pd.DataFrame]:
    TASK693_DIR.mkdir(parents=True, exist_ok=True)
    leaders = pd.read_csv(task691_dir / "task691_slot_leader_review.csv")
    source_packet = pd.read_csv(task692_dir / "task692_leader_source_packet_review.csv")
    price_absorption = pd.read_csv(task692_dir / "task692_price_absorption_confirmation_panel.csv")
    links = pd.read_csv(task636_dir / "task_636_entry_event_links.csv")
    predictions = pd.read_csv(task636_dir / "task_636_event_content_predictions.csv")

    rulebook = build_interpreter_rulebook()
    event_evidence = build_source_event_v2_evidence(leaders, links, predictions)
    leader_v2 = build_leader_source_packet_v2(source_packet, event_evidence)
    price_packet = build_price_absorption_review_ready_packet(price_absorption)
    audit = build_integrity_audit(event_evidence, leader_v2, price_packet)
    decision = build_decision(event_evidence, leader_v2, price_packet, audit)
    pass_fail = audit.copy()

    write_outputs(rulebook, event_evidence, leader_v2, price_packet, audit, decision, pass_fail)
    return {
        "rulebook": rulebook,
        "event_evidence": event_evidence,
        "leader_v2": leader_v2,
        "price_packet": price_packet,
        "audit": audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_interpreter_rulebook() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rule_id": "ownership_sale_noise_guard",
                "purpose": "Prevent Form 4, 144, 13G, and ownership filings from becoming bullish catalysts by default.",
                "positive_requirement": "Must include independent economic bridge; ownership filing alone is not enough.",
            },
            {
                "rule_id": "direct_company_bridge",
                "purpose": "Promote only source packets with direct company linkage plus contract/customer/order/backlog/revenue/guidance/margin signal.",
                "positive_requirement": "Company-direct source, certified text, not generic filing, and at least two economic evidence families.",
            },
            {
                "rule_id": "policy_breadth_guard",
                "purpose": "White House or political events must not be mapped to one stock unless direct symbol or sector mechanism is explicit.",
                "positive_requirement": "Policy text must name the company or contain sector-specific mechanism and direct stock linkage.",
            },
            {
                "rule_id": "manual_review_bucket",
                "purpose": "Keep ambiguous 8-K or IR filings out of allocation while preserving them for human packet review.",
                "positive_requirement": "Economic terms exist but direct causal bridge is incomplete.",
            },
        ]
    )


def build_source_event_v2_evidence(
    leaders: pd.DataFrame,
    links: pd.DataFrame,
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    targets = leaders[leaders["leader_review_status"].eq("leader_source_packet_needed")][IDENTITY + ["sector_family"]]
    event_packet = links.merge(predictions, on="event_id", how="left", suffixes=("_link", ""))
    event_packet = event_packet[event_packet["lifecycle_id"].isin(targets["lifecycle_id"])].copy()
    event_packet = event_packet.merge(targets, on="lifecycle_id", how="left", suffixes=("", "_leader"))
    rows = []
    for _, row in event_packet.iterrows():
        rows.append(classify_event_v2(row))
    return pd.DataFrame(rows)


def classify_event_v2(row: pd.Series) -> dict[str, object]:
    raw_text = read_raw_text(row.get("raw_text_path", ""))
    searchable = " ".join(
        [
            str(row.get("event_title", "")),
            str(row.get("event_category", "")),
            str(row.get("content_interpretation_evidence_span", "")),
            raw_text[:20000],
        ]
    )
    lower = searchable.lower()
    title_lower = str(row.get("event_title", "")).lower()
    source_lane = str(row.get("source_lane", ""))
    event_category = str(row.get("event_category", ""))
    symbol = str(row.get("symbol", row.get("symbol_leader", "")))
    is_generic_filing = event_category in {"insider_or_sale_notice", "passive_13g", "activist_13d"} or any(
        term in title_lower for term in GENERIC_FILING_TERMS
    )
    is_broad_policy = "political" in source_lane or "whitehouse" in source_lane or "trump" in str(row.get("event_id", "")).lower()
    economic_hits = {name: int(re.search(pattern, lower, flags=re.IGNORECASE) is not None) for name, pattern in ECONOMIC_PATTERNS.items()}
    economic_family_count = int(sum(economic_hits.values()))
    symbol_mentioned = symbol.lower() in lower if symbol else False
    certified = int(safe_float(row.get("source_text_certified_flag", 0)) > 0)
    existing_causal = int(safe_float(row.get("content_stock_specific_causal_link", 0)) > 0)
    existing_bridge = int(
        safe_float(row.get("content_revenue_or_backlog_signal", 0))
        + safe_float(row.get("content_guidance_or_margin_signal", 0))
        + safe_float(row.get("content_supply_demand_signal", 0))
        > 0
    )

    event_state = classify_event_state(
        certified=certified,
        generic=is_generic_filing,
        broad_policy=is_broad_policy,
        economic_family_count=economic_family_count,
        symbol_mentioned=symbol_mentioned,
        existing_causal=existing_causal,
        existing_bridge=existing_bridge,
    )
    return {
        "source_event_v2_evidence_id": f"{row['lifecycle_id']}|{row['event_id']}|v2",
        "lifecycle_id": row["lifecycle_id"],
        "symbol": symbol,
        "entry_ts": row.get("entry_ts", ""),
        "entry_ts_utc": row.get("entry_ts_utc", ""),
        "theme_id": row.get("theme_id_leader", row.get("theme_id", "")),
        "split_name": row.get("split_name_leader", row.get("split_name", "")),
        "sector_family": row.get("sector_family", ""),
        "event_id": row["event_id"],
        "event_title": row.get("event_title", ""),
        "event_category": event_category,
        "source_lane": source_lane,
        "raw_text_path": row.get("raw_text_path", ""),
        "source_text_certified_flag": certified,
        "generic_filing_noise_flag": int(is_generic_filing),
        "broad_policy_not_symbol_specific_flag": int(is_broad_policy and not symbol_mentioned),
        "symbol_mentioned_in_text_flag": int(symbol_mentioned),
        "economic_family_count": economic_family_count,
        "contract_signal_v2": economic_hits["contract"],
        "customer_signal_v2": economic_hits["customer"],
        "order_backlog_signal_v2": economic_hits["order_backlog"],
        "revenue_signal_v2": economic_hits["revenue"],
        "guidance_signal_v2": economic_hits["guidance"],
        "margin_signal_v2": economic_hits["margin"],
        "supply_demand_signal_v2": economic_hits["supply_demand"],
        "existing_stock_specific_causal_flag": existing_causal,
        "existing_economic_bridge_flag": existing_bridge,
        "source_event_v2_state": event_state,
        "evidence_snippet": evidence_snippet(searchable),
        "outcome_used_flag": 0,
        "future_price_used_flag": 0,
        "label_used_flag": 0,
    }


def classify_event_state(
    certified: int,
    generic: bool,
    broad_policy: bool,
    economic_family_count: int,
    symbol_mentioned: bool,
    existing_causal: int,
    existing_bridge: int,
) -> str:
    if not certified:
        return "source_text_not_certified"
    if generic and economic_family_count < 2:
        return "ownership_or_sale_filing_noise"
    if broad_policy and not symbol_mentioned:
        return "broad_policy_not_symbol_specific"
    if not generic and (existing_causal or symbol_mentioned) and (existing_bridge or economic_family_count >= 2):
        return "direct_economic_source_supported"
    if not generic and economic_family_count >= 2:
        return "economic_terms_manual_review"
    if generic:
        return "ownership_filing_with_weak_economic_terms"
    return "no_direct_economic_bridge"


def build_leader_source_packet_v2(source_packet: pd.DataFrame, event_evidence: pd.DataFrame) -> pd.DataFrame:
    grouped = event_evidence.groupby("lifecycle_id")
    rows = []
    for _, packet in source_packet.iterrows():
        lifecycle_id = packet["lifecycle_id"]
        events = grouped.get_group(lifecycle_id) if lifecycle_id in grouped.groups else pd.DataFrame()
        direct = int(events["source_event_v2_state"].eq("direct_economic_source_supported").sum()) if len(events) else 0
        manual = int(events["source_event_v2_state"].eq("economic_terms_manual_review").sum()) if len(events) else 0
        noise = int(events["source_event_v2_state"].isin(["ownership_or_sale_filing_noise", "broad_policy_not_symbol_specific"]).sum()) if len(events) else 0
        economic_terms = int(events["economic_family_count"].gt(0).sum()) if len(events) else 0
        state = classify_packet_v2_state(direct, manual, noise, len(events), economic_terms)
        rows.append(
            {
                "leader_source_packet_v2_review_id": f"{lifecycle_id}|source_packet_v2",
                **identity_from_row(packet),
                "sector_family": packet["sector_family"],
                "linked_event_count": int(len(events)),
                "direct_economic_source_event_count": direct,
                "manual_review_economic_event_count": manual,
                "noise_event_count": noise,
                "event_with_economic_terms_count": economic_terms,
                "source_packet_v2_state": state,
                "source_packet_v2_verdict": verdict_for_packet_v2(state),
                "top_event_state_sample": "|".join(events["source_event_v2_state"].astype(str).head(5)) if len(events) else "",
                "top_event_title_sample": " | ".join(events["event_title"].astype(str).head(3)) if len(events) else "",
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_price_absorption_review_ready_packet(price_absorption: pd.DataFrame) -> pd.DataFrame:
    ready = price_absorption[price_absorption["price_absorption_verdict"].eq("review_ready_not_trade_approved")].copy()
    rows = []
    for _, row in ready.iterrows():
        rows.append(
            {
                "price_absorption_review_ready_packet_id": f"{row['lifecycle_id']}|review_ready_price_packet",
                **identity_from_row(row),
                "sector_family": row["sector_family"],
                "cohort_id": row["cohort_id"],
                "slot_claim_score": float(row["slot_claim_score"]),
                "price_absorption_state": row["price_absorption_state"],
                "price_acceptance_score": float(row["price_acceptance_score"]),
                "range_pos": float(row["range_pos"]),
                "intraday_ret_from_open": float(row["intraday_ret_from_open"]),
                "volume_ratio_prev": float(row["volume_ratio_prev"]),
                "near_high60_prev": float(row["near_high60_prev"]),
                "ret_5d_prev": float(row["ret_5d_prev"]),
                "ret_20d_prev": float(row["ret_20d_prev"]),
                "absorption_reason_flags": row["absorption_reason_flags"],
                "human_packet_summary": build_price_packet_summary(row),
                "residual_review_risk": residual_price_packet_risk(row),
                "packet_verdict": "manual_review_ready_not_allocation_approved",
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def classify_packet_v2_state(direct: int, manual: int, noise: int, total: int, economic_terms: int) -> str:
    if total == 0:
        return "source_packet_missing"
    if direct > 0:
        return "source_packet_direct_economic_supported"
    if manual > 0:
        return "source_packet_manual_economic_review"
    if economic_terms > 0:
        return "source_packet_economic_terms_but_no_direct_bridge"
    if noise == total:
        return "source_packet_all_noise"
    return "source_packet_no_direct_economic_bridge"


def verdict_for_packet_v2(state: str) -> str:
    if state == "source_packet_direct_economic_supported":
        return "review_ready_not_trade_approved"
    if state == "source_packet_manual_economic_review":
        return "manual_review_required"
    return "not_promotable"


def build_price_packet_summary(row: pd.Series) -> str:
    parts = [
        f"symbol={row['symbol']}",
        f"price_score={float(row['price_acceptance_score']):.1f}",
        f"range_pos={float(row['range_pos']):.2f}",
        f"volume_ratio={float(row['volume_ratio_prev']):.2f}",
        f"near_high60={float(row['near_high60_prev']):.2f}",
        f"flags={row['absorption_reason_flags']}",
    ]
    return "|".join(parts)


def residual_price_packet_risk(row: pd.Series) -> str:
    risks = []
    if float(row["near_high60_prev"]) >= 0.98:
        risks.append("near_high_extension")
    if float(row["intraday_ret_from_open"]) >= 0.02:
        risks.append("opening_extension")
    if float(row["range_pos"]) >= 0.88:
        risks.append("upper_range_entry")
    return "|".join(risks) if risks else "no_major_price_absorption_risk"


def build_integrity_audit(
    event_evidence: pd.DataFrame,
    leader_v2: pd.DataFrame,
    price_packet: pd.DataFrame,
) -> pd.DataFrame:
    outputs = {"event_evidence": event_evidence, "leader_v2": leader_v2, "price_packet": price_packet}
    forbidden = sorted(
        f"{name}:{col}" for name, frame in outputs.items() for col in frame.columns if col in FORBIDDEN_COLUMNS
    )
    return pd.DataFrame(
        [
            gate(
                "source_event_evidence_present",
                len(event_evidence) > 0 and event_evidence["lifecycle_id"].nunique() == 19,
                f"events={len(event_evidence)}; lifecycles={event_evidence['lifecycle_id'].nunique()}",
                "source event v2 evidence for all 19 leader source packets",
            ),
            gate(
                "source_packet_v2_states_present",
                leader_v2["source_packet_v2_state"].nunique() >= 2,
                f"packet_states={leader_v2['source_packet_v2_state'].nunique()}",
                "v2 interpreter should separate noise/manual/direct states where data supports it",
            ),
            gate(
                "price_review_ready_packet_count",
                len(price_packet) == 2,
                f"price_packets={len(price_packet)}",
                "one packet for each Task692 review-ready price absorption candidate",
            ),
            gate(
                "no_outcome_columns_in_task693_outputs",
                len(forbidden) == 0,
                "|".join(forbidden) if forbidden else "none",
                "PnL/outcome columns excluded",
            ),
            gate("no_strategy_promotion", True, "no PnL simulation or allocation rule promotion was run", "packet review only"),
        ]
    )


def build_decision(
    event_evidence: pd.DataFrame,
    leader_v2: pd.DataFrame,
    price_packet: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task693",
                "verdict": "SOURCE_PACKET_V2_AND_PRICE_PACKET_REVIEW_BUILT_NO_TRADING_PROMOTION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "source_event_v2_count": int(len(event_evidence)),
                "leader_source_packet_v2_count": int(len(leader_v2)),
                "direct_economic_supported_leader_count": int(
                    leader_v2["source_packet_v2_state"].eq("source_packet_direct_economic_supported").sum()
                ),
                "manual_review_leader_count": int(
                    leader_v2["source_packet_v2_state"].eq("source_packet_manual_economic_review").sum()
                ),
                "price_absorption_packet_count": int(len(price_packet)),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Source packet interpreter v2 and two price absorption packets are ready for manual review.",
                "next_action": "Review v2 source packet states and the two price packets before defining any allocation eligibility rule.",
            }
        ]
    )


def write_outputs(
    rulebook: pd.DataFrame,
    event_evidence: pd.DataFrame,
    leader_v2: pd.DataFrame,
    price_packet: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task693_source_packet_interpreter_v2_rulebook.csv": rulebook,
        "task693_source_event_v2_evidence.csv": event_evidence,
        "task693_leader_source_packet_v2_review.csv": leader_v2,
        "task693_price_absorption_review_ready_packet.csv": price_packet,
        "task693_integrity_audit.csv": audit,
        "task_693_decision.csv": decision,
        "task_693_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK693_DIR / name, index=False)
    (TASK693_DIR / "task_693_source_packet_v2_price_packet.md").write_text(
        render_report(rulebook, event_evidence, leader_v2, price_packet, audit, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK693_DIR, TASK693_DIR / "artifact_manifest.csv")


def render_report(
    rulebook: pd.DataFrame,
    event_evidence: pd.DataFrame,
    leader_v2: pd.DataFrame,
    price_packet: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    event_summary = event_evidence.groupby(["source_event_v2_state"], dropna=False).size().reset_index(name="event_count")
    packet_summary = leader_v2.groupby(["source_packet_v2_state", "source_packet_v2_verdict"], dropna=False).size().reset_index(name="leader_count")
    price_summary = price_packet[["symbol", "entry_ts", "human_packet_summary", "residual_review_risk"]]
    return f"""# Task693 Source Packet V2 and Price Packet Review

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: source events {int(d["source_event_v2_count"])}, leader packets {int(d["leader_source_packet_v2_count"])}, direct supported leaders {int(d["direct_economic_supported_leader_count"])}, manual-review leaders {int(d["manual_review_leader_count"])}, price packets {int(d["price_absorption_packet_count"])}.
- What changed: source packet interpretation now re-reads certified raw text and guards against ownership-filing noise.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Inputs are Task636 entry-event links and source-text predictions, Task691 leader review, and Task692 price absorption confirmation output.

### Exact join keys

- Source packet v2: `lifecycle_id` to entry-event links, then `event_id` to event predictions and raw text paths.
- Price packet: Task692 review-ready price candidates by `lifecycle_id`.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included.
- This task does not run a backtest and does not promote a trading rule.

### Source Packet V2 Rulebook

{t678.markdown_table(rulebook)}

### Source Event V2 Summary

{t678.markdown_table(event_summary)}

### Leader Packet V2 Summary

{t678.markdown_table(packet_summary)}

### Price Absorption Review-Ready Packets

{t678.markdown_table(price_summary)}

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Ownership and sale filings dominate many leader packets and are not treated as bullish catalysts.
- Broad policy items remain non-promotable unless directly tied to the company or sector mechanism.
- Price absorption packets are review-ready only, not allocation-approved.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Manually review source packet v2 `manual_review_required` cases.
- Decide whether TEAM and LMT price packets are economically coherent before any allocation test.
- Add deterministic incumbent replay before replacement claims.

## No-Background Decision-Maker Report

- What happened: source packets were re-read with stronger guards, and the two price-ready candidates became readable packets.
- Why it matters: we avoid treating ownership filings or broad policy as direct company catalysts.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: review v2 packets before writing any trading rule.

## Artifact Manifest

- Inputs: Task636 event links/predictions, Task691 leader review, Task692 price absorption panel.
- Outputs: v2 rulebook, event evidence, leader packet v2 review, price packet review, integrity audit, decision, pass/fail, manifest.
- Row counts: event evidence {len(event_evidence)}, leader packets {len(leader_v2)}, price packets {len(price_packet)}.
- Validation commands: `python src/backtest/build_task693_source_packet_v2_price_packet.py`; `python -m unittest tests.test_task693_source_packet_v2_price_packet`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def read_raw_text(path_value: object) -> str:
    path_text = str(path_value)
    if not path_text or path_text == "nan":
        return ""
    path = Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:50000]
    except OSError:
        return ""


def evidence_snippet(text: str) -> str:
    lower = text.lower()
    for pattern in ECONOMIC_PATTERNS.values():
        match = re.search(pattern, lower, flags=re.IGNORECASE)
        if match:
            start = max(match.start() - 80, 0)
            end = min(match.end() + 160, len(text))
            return re.sub(r"\s+", " ", text[start:end]).strip()
    return ""


def identity_from_row(row: pd.Series) -> dict[str, object]:
    return {col: row[col] if col in row.index else "" for col in IDENTITY}


def safe_float(value: object) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task636-dir", type=Path, default=TASK636_DIR)
    parser.add_argument("--task691-dir", type=Path, default=TASK691_DIR)
    parser.add_argument("--task692-dir", type=Path, default=TASK692_DIR)
    args = parser.parse_args()
    build_task693_program(task636_dir=args.task636_dir, task691_dir=args.task691_dir, task692_dir=args.task692_dir)
    print(f"[Task693] wrote {TASK693_DIR}")


if __name__ == "__main__":
    main()
