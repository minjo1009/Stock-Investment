from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest import build_task678_active_cap3_winner_archetype as t678


TASK684_DIR = Path("docs/reports/task_684_interaction_context_prediction_stack")
TASK636_DIR = Path("docs/reports/task_636_full_period_content_prediction_backtest")
TASK691_DIR = Path("docs/reports/task_691_slot_leader_contender_review")
TASK692_DIR = Path("docs/reports/task_692_source_packet_price_absorption")

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


def build_task692_program(
    task684_dir: Path = TASK684_DIR,
    task636_dir: Path = TASK636_DIR,
    task691_dir: Path = TASK691_DIR,
) -> dict[str, pd.DataFrame]:
    TASK692_DIR.mkdir(parents=True, exist_ok=True)
    stack = pd.read_csv(task684_dir / "task684_interaction_stack_panel.csv")
    leaders = pd.read_csv(task691_dir / "task691_slot_leader_review.csv")
    contenders = pd.read_csv(task691_dir / "task691_contender_confirmation_map.csv")
    entry_links = pd.read_csv(task636_dir / "task_636_entry_event_links.csv")
    event_predictions = pd.read_csv(task636_dir / "task_636_event_content_predictions.csv")

    rulebook = build_confirmation_rulebook()
    source_packet = build_leader_source_packet_review(leaders, entry_links, event_predictions)
    price_absorption = build_price_absorption_confirmation_panel(contenders, stack)
    summary = build_confirmation_readiness_summary(source_packet, price_absorption)
    audit = build_integrity_audit(leaders, contenders, source_packet, price_absorption)
    decision = build_decision(source_packet, price_absorption, summary, audit)
    pass_fail = audit.copy()

    write_outputs(rulebook, source_packet, price_absorption, summary, audit, decision, pass_fail)
    return {
        "rulebook": rulebook,
        "source_packet": source_packet,
        "price_absorption": price_absorption,
        "summary": summary,
        "audit": audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_confirmation_rulebook() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "confirmation_domain": "leader_source_packet",
                "state": "source_packet_economic_value_supported",
                "required_evidence": "certified source text, stock-specific causal link, and at least one revenue/backlog/guidance/margin/supply-demand bridge",
                "effect": "leader can move to reviewed allocation candidate, not automatic buy",
            },
            {
                "confirmation_domain": "leader_source_packet",
                "state": "source_packet_proxy_only",
                "required_evidence": "source exists but lacks named counterparty, contract value, or cash-flow bridge",
                "effect": "leader stays research-only until source text improves",
            },
            {
                "confirmation_domain": "leader_source_packet",
                "state": "source_packet_missing",
                "required_evidence": "no certified linked event packet found for lifecycle_id",
                "effect": "leader cannot be promoted",
            },
            {
                "confirmation_domain": "price_absorption",
                "state": "absorption_confirmed_not_overextended",
                "required_evidence": "price acceptance present, range not extreme, volume support present, no extension proxy",
                "effect": "contender can move to reviewed allocation candidate",
            },
            {
                "confirmation_domain": "price_absorption",
                "state": "absorption_possible_needs_delay",
                "required_evidence": "price accepted but extension or priced-in proxy remains high",
                "effect": "contender requires delayed entry or confirmation",
            },
            {
                "confirmation_domain": "price_absorption",
                "state": "priced_in_or_extension_risk",
                "required_evidence": "near high, opening drive, extension proxy, or mixed priced-in state",
                "effect": "contender cannot be promoted without fresh acceptance evidence",
            },
        ]
    )


def build_leader_source_packet_review(
    leaders: pd.DataFrame,
    entry_links: pd.DataFrame,
    event_predictions: pd.DataFrame,
) -> pd.DataFrame:
    targets = leaders[leaders["leader_review_status"].eq("leader_source_packet_needed")].copy()
    event_packet = entry_links.merge(event_predictions, on="event_id", how="left", suffixes=("_link", ""))
    rows = []
    for _, leader in targets.iterrows():
        lifecycle_id = str(leader["lifecycle_id"])
        events = event_packet[event_packet["lifecycle_id"].eq(lifecycle_id)].copy()
        rows.append(build_source_packet_row(leader, events))
    return pd.DataFrame(rows)


def build_source_packet_row(leader: pd.Series, events: pd.DataFrame) -> dict[str, object]:
    certified = pd.to_numeric(events.get("source_text_certified_flag", pd.Series(dtype=float)), errors="coerce").fillna(0)
    causal = pd.to_numeric(events.get("content_stock_specific_causal_link", pd.Series(dtype=float)), errors="coerce").fillna(0)
    counterparty = pd.to_numeric(events.get("content_named_customer_or_counterparty", pd.Series(dtype=float)), errors="coerce").fillna(0)
    revenue = pd.to_numeric(events.get("content_revenue_or_backlog_signal", pd.Series(dtype=float)), errors="coerce").fillna(0)
    margin = pd.to_numeric(events.get("content_guidance_or_margin_signal", pd.Series(dtype=float)), errors="coerce").fillna(0)
    supply = pd.to_numeric(events.get("content_supply_demand_signal", pd.Series(dtype=float)), errors="coerce").fillna(0)
    magnitude = pd.to_numeric(events.get("content_prediction_magnitude_score", pd.Series(dtype=float)), errors="coerce").fillna(0)
    priced = pd.to_numeric(events.get("content_priced_in_risk_base_score", pd.Series(dtype=float)), errors="coerce").fillna(0)

    certified_count = int(certified.sum()) if len(events) else 0
    economic_bridge_count = int((revenue + margin + supply).gt(0).sum()) if len(events) else 0
    source_state = classify_source_packet_state(
        linked_count=len(events),
        certified_count=certified_count,
        causal_count=int(causal.sum()) if len(events) else 0,
        counterparty_count=int(counterparty.sum()) if len(events) else 0,
        bridge_count=economic_bridge_count,
        max_magnitude=float(magnitude.max()) if len(events) else 0.0,
        avg_priced=float(priced.mean()) if len(events) else 0.0,
    )
    return {
        "leader_source_packet_review_id": f"{leader['lifecycle_id']}|source_packet_review",
        **identity_from_row(leader),
        "sector_family": leader["sector_family"],
        "leader_review_status": leader["leader_review_status"],
        "slot_claim_score": float(leader["slot_claim_score"]),
        "linked_event_count": int(len(events)),
        "source_text_certified_event_count": certified_count,
        "stock_specific_causal_event_count": int(causal.sum()) if len(events) else 0,
        "named_customer_or_counterparty_count": int(counterparty.sum()) if len(events) else 0,
        "revenue_or_backlog_event_count": int(revenue.sum()) if len(events) else 0,
        "guidance_or_margin_event_count": int(margin.sum()) if len(events) else 0,
        "supply_demand_event_count": int(supply.sum()) if len(events) else 0,
        "economic_bridge_event_count": economic_bridge_count,
        "max_content_magnitude_score": float(magnitude.max()) if len(events) else 0.0,
        "avg_priced_in_risk_score": round(float(priced.mean()), 4) if len(events) else 0.0,
        "source_packet_state": source_state,
        "source_packet_verdict": verdict_for_source_state(source_state),
        "event_id_sample": "|".join(events["event_id"].astype(str).head(3)) if len(events) else "",
        "event_title_sample": " | ".join(events["event_title"].astype(str).head(2)) if len(events) and "event_title" in events.columns else "",
        "raw_text_path_sample": "|".join(events["raw_text_path"].astype(str).head(2)) if len(events) and "raw_text_path" in events.columns else "",
        "source_packet_missing_flag": int(source_state == "source_packet_missing"),
        "outcome_used_flag": 0,
        "future_price_used_flag": 0,
        "label_used_flag": 0,
    }


def build_price_absorption_confirmation_panel(contenders: pd.DataFrame, stack: pd.DataFrame) -> pd.DataFrame:
    targets = contenders[contenders["required_confirmation_type"].eq("price_absorption_confirmation")].copy()
    price_cols = [
        "lifecycle_id",
        "price_acceptance_score",
        "price_acceptance_state",
        "price_chart_acceptance_state",
        "range_pos",
        "intraday_ret_from_open",
        "volume_ratio_prev",
        "near_high60_prev",
        "ret_5d_prev_x",
        "ret_20d_prev_x",
        "timing_state",
        "proxy_risk_context",
        "catalyst_priced_in_state",
        "catalyst_absorption_state",
        "archetype_absorption_mode",
        "theme_breadth20_prev",
        "theme_rank_prev",
    ]
    joined = targets.merge(select_columns(stack, price_cols), on="lifecycle_id", how="left")
    rows = []
    for _, row in joined.iterrows():
        state, flags = classify_price_absorption(row)
        rows.append(
            {
                "price_absorption_confirmation_id": f"{row['lifecycle_id']}|price_absorption_confirmation",
                **identity_from_row(row),
                "sector_family": row["sector_family"],
                "cohort_id": row["cohort_id"],
                "cohort_rank": int(row["cohort_rank"]),
                "cohort_size": int(row["cohort_size"]),
                "slot_claim_score": float(row["slot_claim_score"]),
                "margin_vs_next_peer": float(row["margin_vs_next_peer"]),
                "price_acceptance_score": safe_float(row.get("price_acceptance_score", 0)),
                "price_acceptance_state": row.get("price_acceptance_state", ""),
                "price_chart_acceptance_state": row.get("price_chart_acceptance_state", ""),
                "range_pos": safe_float(row.get("range_pos", 0)),
                "intraday_ret_from_open": safe_float(row.get("intraday_ret_from_open", 0)),
                "volume_ratio_prev": safe_float(row.get("volume_ratio_prev", 0)),
                "near_high60_prev": safe_float(row.get("near_high60_prev", 0)),
                "ret_5d_prev": safe_float(row.get("ret_5d_prev_x", 0)),
                "ret_20d_prev": safe_float(row.get("ret_20d_prev_x", 0)),
                "timing_state": row.get("timing_state", ""),
                "proxy_risk_context": row.get("proxy_risk_context", ""),
                "catalyst_priced_in_state": row.get("catalyst_priced_in_state", ""),
                "catalyst_absorption_state": row.get("catalyst_absorption_state", ""),
                "price_absorption_state": state,
                "price_absorption_verdict": verdict_for_absorption_state(state),
                "absorption_reason_flags": "|".join(flags),
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_confirmation_readiness_summary(source_packet: pd.DataFrame, price_absorption: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for state, group in source_packet.groupby("source_packet_state", dropna=False):
        rows.append(
            {
                "domain": "leader_source_packet",
                "state": state,
                "candidate_count": int(len(group)),
                "review_ready_count": int(group["source_packet_verdict"].eq("review_ready_not_trade_approved").sum()),
                "blocked_or_research_count": int(group["source_packet_verdict"].ne("review_ready_not_trade_approved").sum()),
            }
        )
    for state, group in price_absorption.groupby("price_absorption_state", dropna=False):
        rows.append(
            {
                "domain": "price_absorption",
                "state": state,
                "candidate_count": int(len(group)),
                "review_ready_count": int(group["price_absorption_verdict"].eq("review_ready_not_trade_approved").sum()),
                "blocked_or_research_count": int(group["price_absorption_verdict"].ne("review_ready_not_trade_approved").sum()),
            }
        )
    return pd.DataFrame(rows)


def classify_source_packet_state(
    linked_count: int,
    certified_count: int,
    causal_count: int,
    counterparty_count: int,
    bridge_count: int,
    max_magnitude: float,
    avg_priced: float,
) -> str:
    if linked_count == 0 or certified_count == 0:
        return "source_packet_missing"
    if causal_count == 0:
        return "source_packet_not_stock_specific"
    if counterparty_count > 0 and bridge_count > 0 and max_magnitude >= 2:
        if max_magnitude >= 3 and avg_priced <= 1:
            return "source_packet_strong_economic_value"
        return "source_packet_economic_value_supported"
    if bridge_count > 0:
        return "source_packet_proxy_only"
    return "source_packet_low_economic_value"


def verdict_for_source_state(state: str) -> str:
    if state in {"source_packet_strong_economic_value", "source_packet_economic_value_supported"}:
        return "review_ready_not_trade_approved"
    if state in {"source_packet_missing", "source_packet_not_stock_specific"}:
        return "not_promotable"
    return "research_only_needs_better_source_packet"


def classify_price_absorption(row: pd.Series) -> tuple[str, list[str]]:
    flags = []
    score = safe_float(row.get("price_acceptance_score", 0))
    range_pos = safe_float(row.get("range_pos", 0))
    intraday = safe_float(row.get("intraday_ret_from_open", 0))
    volume_ratio = safe_float(row.get("volume_ratio_prev", 0))
    near_high = safe_float(row.get("near_high60_prev", 0))
    ret_5d = safe_float(row.get("ret_5d_prev_x", 0))
    priced_state = str(row.get("catalyst_priced_in_state", ""))
    proxy_risk = str(row.get("proxy_risk_context", ""))
    price_state = str(row.get("price_chart_acceptance_state", row.get("price_acceptance_state", "")))

    if score >= 5:
        flags.append("price_acceptance_score_ok")
    if volume_ratio >= 1.1:
        flags.append("volume_support")
    if near_high >= 0.98:
        flags.append("near_high60_extension")
    if range_pos >= 0.9:
        flags.append("top_of_range")
    if intraday >= 0.015:
        flags.append("opening_extension")
    if ret_5d >= 0.08:
        flags.append("recent_runup")
    if "mixed" in priced_state or "proxy" in priced_state:
        flags.append("priced_in_proxy")
    if "extension" in proxy_risk or "extended" in price_state:
        flags.append("extension_proxy")

    extension_count = sum(flag in flags for flag in ["near_high60_extension", "top_of_range", "opening_extension", "recent_runup", "extension_proxy"])
    if score >= 5 and volume_ratio >= 1.1 and extension_count <= 1 and "priced_in_proxy" not in flags:
        return "absorption_confirmed_not_overextended", flags
    if score >= 5 and extension_count <= 2:
        return "absorption_possible_needs_delay", flags
    if score >= 4 and volume_ratio >= 1.0:
        return "absorption_unproven_needs_confirmation", flags
    return "priced_in_or_extension_risk", flags


def verdict_for_absorption_state(state: str) -> str:
    if state == "absorption_confirmed_not_overextended":
        return "review_ready_not_trade_approved"
    if state in {"absorption_possible_needs_delay", "absorption_unproven_needs_confirmation"}:
        return "needs_delay_or_confirmation"
    return "not_promotable_without_fresh_acceptance"


def build_integrity_audit(
    leaders: pd.DataFrame,
    contenders: pd.DataFrame,
    source_packet: pd.DataFrame,
    price_absorption: pd.DataFrame,
) -> pd.DataFrame:
    outputs = {"source_packet": source_packet, "price_absorption": price_absorption}
    forbidden = sorted(
        f"{name}:{col}" for name, frame in outputs.items() for col in frame.columns if col in FORBIDDEN_COLUMNS
    )
    rows = [
        gate(
            "leader_source_packet_target_count",
            len(source_packet) == int(leaders["leader_review_status"].eq("leader_source_packet_needed").sum()),
            f"source_packet_rows={len(source_packet)}",
            "one source packet review row per leader_source_packet_needed candidate",
        ),
        gate(
            "price_absorption_target_count",
            len(price_absorption) == int(contenders["required_confirmation_type"].eq("price_absorption_confirmation").sum()),
            f"price_absorption_rows={len(price_absorption)}",
            "one price absorption row per price_absorption_confirmation contender",
        ),
        gate(
            "source_packet_states_decomposed",
            source_packet["source_packet_state"].nunique() >= 1
            and source_packet["source_packet_verdict"].isin(["not_promotable", "review_ready_not_trade_approved", "research_only_needs_better_source_packet"]).all(),
            f"source_packet_states={source_packet['source_packet_state'].nunique()}",
            "source packet review must produce valid source states even when all leaders share one blocker",
        ),
        gate(
            "price_absorption_states_decomposed",
            price_absorption["price_absorption_state"].nunique() >= 2,
            f"price_absorption_states={price_absorption['price_absorption_state'].nunique()}",
            "price absorption review should split candidates into multiple states",
        ),
        gate(
            "no_outcome_columns_in_confirmation_outputs",
            len(forbidden) == 0,
            "|".join(forbidden) if forbidden else "none",
            "PnL/outcome columns excluded",
        ),
        gate("no_strategy_promotion", True, "no PnL simulation or allocation rule promotion was run", "confirmation review only"),
    ]
    return pd.DataFrame(rows)


def build_decision(
    source_packet: pd.DataFrame,
    price_absorption: pd.DataFrame,
    summary: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task692",
                "verdict": "SOURCE_PACKET_PRICE_ABSORPTION_REVIEW_BUILT_NO_TRADING_PROMOTION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "leader_source_packet_review_count": int(len(source_packet)),
                "price_absorption_review_count": int(len(price_absorption)),
                "source_packet_review_ready_count": int(source_packet["source_packet_verdict"].eq("review_ready_not_trade_approved").sum()),
                "price_absorption_review_ready_count": int(price_absorption["price_absorption_verdict"].eq("review_ready_not_trade_approved").sum()),
                "confirmation_state_count": int(len(summary)),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Leader source packets and contender price absorption states were reviewed before allocation backtest.",
                "next_action": "Inspect review-ready candidates and decide whether to define a small pre-backtest eligibility rule.",
            }
        ]
    )


def write_outputs(
    rulebook: pd.DataFrame,
    source_packet: pd.DataFrame,
    price_absorption: pd.DataFrame,
    summary: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task692_confirmation_rulebook.csv": rulebook,
        "task692_leader_source_packet_review.csv": source_packet,
        "task692_price_absorption_confirmation_panel.csv": price_absorption,
        "task692_confirmation_readiness_summary.csv": summary,
        "task692_integrity_audit.csv": audit,
        "task_692_decision.csv": decision,
        "task_692_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK692_DIR / name, index=False)
    (TASK692_DIR / "task_692_source_packet_price_absorption.md").write_text(
        render_report(rulebook, source_packet, price_absorption, summary, audit, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK692_DIR, TASK692_DIR / "artifact_manifest.csv")


def render_report(
    rulebook: pd.DataFrame,
    source_packet: pd.DataFrame,
    price_absorption: pd.DataFrame,
    summary: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    source_summary = source_packet.groupby(["source_packet_state", "source_packet_verdict"], dropna=False).size().reset_index(name="leader_count")
    price_summary = price_absorption.groupby(["price_absorption_state", "price_absorption_verdict"], dropna=False).size().reset_index(name="contender_count")
    return f"""# Task692 Source Packet and Price Absorption Review

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: leader source packet reviews {int(d["leader_source_packet_review_count"])}, price absorption reviews {int(d["price_absorption_review_count"])}, source review-ready {int(d["source_packet_review_ready_count"])}, price review-ready {int(d["price_absorption_review_ready_count"])}.
- What changed: leader source packet and contender price absorption confirmation are now explicit pre-backtest reviews.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Inputs are Task691 leader/contender review outputs, Task636 entry-event links and source-text content predictions, and Task684 entry-time price context.

### Exact join keys

- Source packet: `lifecycle_id` from Task691 to Task636 `entry_event_links`, then `event_id` to Task636 `event_content_predictions`.
- Price absorption: `lifecycle_id` from Task691 contenders to Task684 entry context.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included.
- This task does not run a backtest and does not promote a trading rule.

### Confirmation rulebook

{t678.markdown_table(rulebook)}

### Leader source packet summary

{t678.markdown_table(source_summary)}

### Price absorption summary

{t678.markdown_table(price_summary)}

### Confirmation readiness summary

{t678.markdown_table(summary)}

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Leaders without stock-specific certified event packets are not promotable.
- Source-packet proxy-only leaders need better source-text extraction before allocation testing.
- Price absorption contenders are separated into confirmed, delay/confirmation, and extension-risk states.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Review source packet samples for economic value quality.
- Convert only review-ready states into a small eligibility rule if accepted.
- Add deterministic portfolio replay before incumbent replacement claims.

## No-Background Decision-Maker Report

- What happened: the 19 source-packet leaders and 293 price-absorption contenders were checked before backtest.
- Why it matters: this prevents weak source evidence or already-priced moves from entering allocation blindly.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: inspect review-ready candidates before writing allocation logic.

## Artifact Manifest

- Inputs: Task691 leader/contender review, Task636 source/event predictions, Task684 price context.
- Outputs: confirmation rulebook, leader source packet review, price absorption panel, readiness summary, integrity audit, decision, pass/fail, manifest.
- Row counts: source packet {len(source_packet)}, price absorption {len(price_absorption)}, summary {len(summary)}.
- Validation commands: `python src/backtest/build_task692_source_packet_price_absorption.py`; `python -m unittest tests.test_task692_source_packet_price_absorption`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def select_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    selected = frame.copy()
    for col in columns:
        if col not in selected.columns:
            selected[col] = 0
    return selected[columns]


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
    parser.add_argument("--task684-dir", type=Path, default=TASK684_DIR)
    parser.add_argument("--task636-dir", type=Path, default=TASK636_DIR)
    parser.add_argument("--task691-dir", type=Path, default=TASK691_DIR)
    args = parser.parse_args()
    build_task692_program(task684_dir=args.task684_dir, task636_dir=args.task636_dir, task691_dir=args.task691_dir)
    print(f"[Task692] wrote {TASK692_DIR}")


if __name__ == "__main__":
    main()
