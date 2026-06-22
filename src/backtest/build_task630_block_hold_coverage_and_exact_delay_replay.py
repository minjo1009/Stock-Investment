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
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate
from src.backtest.build_task608g_live_detectable_entry_failure_path_diagnostics import INTRADAY_DIR, load_intraday_sources
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio
from src.backtest.build_task622_source_semantic_interpretation_sidecar import TASK617_PANEL, load_panel, within_window
from src.backtest.build_task627_source_text_theme_linkage_validation import read_raw_text
from src.backtest.build_task629_firm_grade_event_linkage_action_taxonomy import (
    REPORT_DIR as TASK629_DIR,
    TASK627_SCORE_PATH,
    NEGATIVE_CLAIM_TERMS,
    POSITIVE_CLAIM_TERMS,
    THEME_TERMS,
    keyword_count,
)


TASK_ID = "Task630"
REPORT_DIR = Path("docs/reports/task_630_block_hold_coverage_and_exact_delay_replay")
TASK629_ATTACHMENT_PATH = TASK629_DIR / "task_629_trade_action_attachment.csv"
SCOPES = ("full_panel", "validation", "recent_oos")
MAX_POSITIONS = (5, 10, 20, 50)
DELAY_MINUTES = (15, 30, 60)
DECISION_COST_BPS = 50
INITIAL_CAPITAL_USD = 1000.0


EXPANDED_ENTITY_GRAPH: dict[str, dict[str, tuple[str, ...]]] = {
    "BA": {
        "company": ("boeing", "the boeing company"),
        "subsidiary": ("boeing defense", "boeing global services", "boeing commercial airplanes"),
        "product": ("737", "737 max", "777", "787", "dreamliner", "aircraft", "airplane", "starliner"),
        "program": ("starliner", "crew flight test", "commercial crew", "kc-46", "p-8", "t-7", "apache", "chinook"),
        "customer": ("airline", "airlines", "nasa", "air force", "department of defense", "dod"),
        "regulator": ("faa", "federal aviation administration", "ntsb", "justice department", "department of justice"),
        "competitor": ("airbus",),
    },
    "RKLB": {
        "company": ("rocket lab", "rocketlab"),
        "subsidiary": ("rocket lab usa",),
        "product": ("electron", "neutron", "photon", "rocket", "launch", "satellite", "space launch", "propulsion"),
        "program": ("electron", "neutron", "photon", "launch complex", "mission"),
        "customer": ("nasa", "space force", "department of defense", "dod", "commercial satellite"),
        "regulator": ("faa", "fcc", "federal communications commission"),
        "competitor": ("spacex", "blue origin"),
    },
    "ASTS": {
        "company": ("ast spacemobile", "spacemobile"),
        "subsidiary": ("ast & science",),
        "product": ("bluebird", "block 1", "block 2", "satellite", "direct-to-device", "space-based", "broadband"),
        "program": ("bluebird", "space-based cellular", "direct-to-device"),
        "customer": ("wireless carrier", "mobile network", "telecom", "at&t", "vodafone", "verizon"),
        "regulator": ("fcc", "federal communications commission", "spectrum"),
        "competitor": ("starlink", "spacex"),
    },
    "RTX": {
        "company": ("raytheon", "raytheon technologies", "pratt & whitney", "pratt and whitney", "collins aerospace"),
        "subsidiary": ("raytheon", "pratt & whitney", "pratt and whitney", "collins aerospace"),
        "product": ("patriot", "nasams", "amraam", "missile", "air defense", "gtf", "aircraft engine", "radar"),
        "program": ("patriot", "nasams", "amraam", "gtf", "f135"),
        "customer": ("air force", "army", "navy", "department of defense", "dod", "nato", "ukraine"),
        "regulator": ("faa", "justice department", "department of justice"),
        "competitor": ("lockheed", "northrop", "boeing"),
    },
}

THESIS_BREAK_TERMS = (
    "grounding",
    "crash",
    "accident",
    "defect",
    "investigation",
    "export control",
    "sanction",
    "restricted",
    "blocked",
    "cancel",
    "canceled",
    "cancelled",
    "delay",
    "budget cut",
    "production halt",
)


def build_task630_block_hold_coverage_and_exact_delay_replay(
    *,
    task617_panel_path: Path = TASK617_PANEL,
    task627_score_path: Path = TASK627_SCORE_PATH,
    intraday_dir: Path = INTRADAY_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task617_panel_path)
    panel["simulated_exit_ts"] = pd.to_datetime(panel["simulated_exit_ts"], utc=True, errors="coerce")
    panel["simulated_exit_price"] = pd.to_numeric(panel["simulated_exit_price"], errors="coerce")
    panel["entry_price"] = pd.to_numeric(panel["entry_price"], errors="coerce")
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce")

    source_scores = pd.read_csv(task627_score_path)
    source_scores["event_date_obj"] = pd.to_datetime(source_scores["event_date_obj"], errors="coerce").dt.date
    source_scores["event_timestamp_dt"] = pd.to_datetime(source_scores["event_timestamp_dt"], utc=True, errors="coerce")
    linkage = build_expanded_linkage_registry(source_scores)
    attachment = build_expanded_trade_attachment(panel, linkage)
    enriched = panel.merge(
        attachment.drop(columns=["symbol"], errors="ignore"),
        on="lifecycle_id",
        how="left",
    )

    symbols = sorted(enriched["symbol"].dropna().astype(str).str.upper().unique().tolist())
    intraday_map, intraday_coverage = load_intraday_sources(symbols, intraday_dir)
    delay_replay = build_exact_delay_replay(enriched, intraday_map)
    false_block = build_false_block_audit(enriched)
    policy_eval = build_policy_evaluation(enriched, delay_replay)
    cost_account = build_cost_account_matrix(enriched, delay_replay)
    coverage = build_block_hold_coverage_audit(linkage, attachment)
    pass_fail = build_pass_fail(coverage, delay_replay, policy_eval, cost_account)
    decision = build_decision(pass_fail, attachment, delay_replay, cost_account)
    gpt_review = build_gpt_review_record()

    out_dir.mkdir(parents=True, exist_ok=True)
    linkage.to_csv(out_dir / "task_630_expanded_event_linkage_registry.csv", index=False)
    attachment.to_csv(out_dir / "task_630_expanded_trade_action_attachment.csv", index=False)
    intraday_coverage.to_csv(out_dir / "task_630_intraday_source_coverage.csv", index=False)
    delay_replay.to_csv(out_dir / "task_630_exact_delayed_entry_replay.csv", index=False)
    false_block.to_csv(out_dir / "task_630_false_block_audit.csv", index=False)
    policy_eval.to_csv(out_dir / "task_630_policy_variant_evaluation.csv", index=False)
    cost_account.to_csv(out_dir / "task_630_cost_account_matrix.csv", index=False)
    coverage.to_csv(out_dir / "task_630_block_hold_coverage_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_630_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_630_decision.csv", index=False)
    gpt_review.to_csv(out_dir / "task_630_gpt_review_capture.csv", index=False)
    (out_dir / "task_630_block_hold_coverage_and_exact_delay_replay.md").write_text(
        render_report(coverage, attachment, delay_replay, policy_eval, cost_account, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_630_expanded_event_linkage_registry": linkage,
        "task_630_expanded_trade_action_attachment": attachment,
        "task_630_intraday_source_coverage": intraday_coverage,
        "task_630_exact_delayed_entry_replay": delay_replay,
        "task_630_false_block_audit": false_block,
        "task_630_policy_variant_evaluation": policy_eval,
        "task_630_cost_account_matrix": cost_account,
        "task_630_block_hold_coverage_audit": coverage,
        "task_630_pass_fail_matrix": pass_fail,
        "task_630_decision": decision,
        "task_630_gpt_review_capture": gpt_review,
    }


def build_expanded_linkage_registry(source_scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    certified = source_scores[source_scores["source_text_certified_flag"].fillna(0).astype(int).eq(1)].copy()
    for _, event in certified.iterrows():
        text = read_raw_text(event.get("raw_text_path", ""))
        for symbol in EXPANDED_ENTITY_GRAPH:
            row = event.to_dict()
            row["symbol"] = symbol
            row.update(classify_expanded_linkage(text, symbol))
            row["source_presence_only_used_flag_task630"] = 0
            row["gpt_score_used_as_source_flag_task630"] = 0
            row["label_used_in_assignment_flag_task630"] = 0
            rows.append(row)
    return pd.DataFrame(rows)


def classify_expanded_linkage(text: str, symbol: str) -> dict[str, object]:
    graph = EXPANDED_ENTITY_GRAPH[symbol]
    hits = {layer: keyword_count(text, terms) for layer, terms in graph.items()}
    theme_hits = keyword_count(text, THEME_TERMS)
    negative_hits = keyword_count(text, NEGATIVE_CLAIM_TERMS)
    positive_hits = keyword_count(text, POSITIVE_CLAIM_TERMS)
    thesis_break_hits = keyword_count(text, THESIS_BREAK_TERMS)

    direct_company_hit = hits["company"] > 0 or hits["subsidiary"] > 0
    economic_direct_count = sum(1 for layer in ("product", "program", "customer", "regulator") if hits[layer] > 0)
    competitor_only = hits["competitor"] > 0 and not direct_company_hit and economic_direct_count == 0
    has_negative = negative_hits > 0 or thesis_break_hits > 0
    has_positive = positive_hits > 0

    if direct_company_hit:
        linkage_grade = "direct_company"
    elif economic_direct_count >= 2:
        linkage_grade = "economic_direct"
    elif economic_direct_count == 1:
        linkage_grade = "economic_single_channel"
    elif competitor_only:
        linkage_grade = "competitor_only"
    elif theme_hits > 0:
        linkage_grade = "theme_only"
    else:
        linkage_grade = "no_link"

    claim_type = expanded_claim_type(hits, direct_company_hit, has_negative, has_positive, theme_hits)
    action_template = expanded_action(linkage_grade, claim_type, has_negative, thesis_break_hits)
    return {
        **{f"{layer}_hit_count": int(value) for layer, value in hits.items()},
        "theme_hit_count": int(theme_hits),
        "negative_claim_hit_count": int(negative_hits),
        "positive_claim_hit_count": int(positive_hits),
        "thesis_break_hit_count": int(thesis_break_hits),
        "linkage_grade": linkage_grade,
        "claim_type": claim_type,
        "action_template": action_template,
        "direct_company_negative_candidate_flag": int(linkage_grade == "direct_company" and has_negative),
        "economic_direct_negative_candidate_flag": int(linkage_grade == "economic_direct" and has_negative),
        "theme_only_no_action_flag": int(linkage_grade == "theme_only" and action_template == "NO_ACTION"),
        "firm_grade_actionable_flag": int(action_template in {"BLOCK_HOLD", "SIZE_DOWN", "DELAY_ENTRY", "CONFIRMATION_REQUIRED"}),
    }


def expanded_claim_type(
    hits: dict[str, int],
    direct_company_hit: bool,
    has_negative: bool,
    has_positive: bool,
    theme_hits: int,
) -> str:
    if direct_company_hit and has_negative:
        return "direct_company_negative_claim"
    if direct_company_hit and has_positive:
        return "direct_company_positive_or_material_claim"
    if hits["regulator"] > 0 and has_negative:
        return "regulator_negative_claim"
    if hits["program"] > 0 and has_negative:
        return "program_negative_claim"
    if hits["product"] > 0 and has_negative:
        return "product_negative_claim"
    if hits["customer"] > 0 and has_negative:
        return "customer_negative_claim"
    if hits["program"] > 0 or hits["product"] > 0:
        return "product_or_program_claim"
    if hits["customer"] > 0 or hits["regulator"] > 0:
        return "customer_or_regulator_claim"
    if hits["competitor"] > 0:
        return "competitor_claim"
    if theme_hits > 0:
        return "theme_claim_only"
    return "no_interpretable_claim"


def expanded_action(linkage_grade: str, claim_type: str, has_negative: bool, thesis_break_hits: int) -> str:
    if linkage_grade == "direct_company" and has_negative:
        return "BLOCK_HOLD"
    if linkage_grade in {"economic_direct", "economic_single_channel"} and has_negative:
        if claim_type in {"regulator_negative_claim", "customer_negative_claim"}:
            return "DELAY_ENTRY"
        return "SIZE_DOWN"
    if linkage_grade in {"direct_company", "economic_direct"} and not has_negative:
        return "CONFIRMATION_REQUIRED"
    return "NO_ACTION"


def build_expanded_trade_attachment(panel: pd.DataFrame, linkage: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, entry in panel.iterrows():
        linked = linked_events_for_entry(linkage, entry)
        selected = select_strongest_event(linked)
        rows.append(attachment_row(entry, linked, selected))
    return pd.DataFrame(rows)


def linked_events_for_entry(linkage: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    symbol = str(entry["symbol"])
    if symbol not in EXPANDED_ENTITY_GRAPH:
        return pd.DataFrame(columns=linkage.columns)
    candidates = linkage[
        linkage["symbol"].astype(str).eq(symbol)
        & linkage["linkage_grade"].astype(str).ne("no_link")
        & (
            (linkage["event_date_obj"] < entry["trade_date"])
            | (
                linkage["event_date_obj"].eq(entry["trade_date"])
                & linkage["time_precision"].eq("timestamp")
                & linkage["event_timestamp_dt"].notna()
                & (linkage["event_timestamp_dt"] <= entry["entry_ts"])
            )
        )
    ]
    return within_window(candidates, entry["trade_date"], 7)


def select_strongest_event(linked: pd.DataFrame) -> pd.Series | None:
    if linked.empty:
        return None
    action_priority = {"BLOCK_HOLD": 5, "DELAY_ENTRY": 4, "SIZE_DOWN": 3, "CONFIRMATION_REQUIRED": 2, "NO_ACTION": 1}
    grade_priority = {"direct_company": 5, "economic_direct": 4, "economic_single_channel": 3, "competitor_only": 1, "theme_only": 1}
    ranked = linked.copy()
    ranked["_action_priority"] = ranked["action_template"].map(action_priority).fillna(0)
    ranked["_grade_priority"] = ranked["linkage_grade"].map(grade_priority).fillna(0)
    ranked["_score"] = pd.to_numeric(ranked["composite_interpretation_score"], errors="coerce").fillna(0.0)
    ranked = ranked.sort_values(["_action_priority", "_grade_priority", "_score", "event_timestamp_dt"], ascending=[False, False, False, False])
    return ranked.iloc[0]


def attachment_row(entry: pd.Series, linked: pd.DataFrame, selected: pd.Series | None) -> dict[str, object]:
    action = "NO_ACTION" if selected is None else str(selected["action_template"])
    return {
        "lifecycle_id": entry["lifecycle_id"],
        "symbol": entry["symbol"],
        "expanded_linked_event_count": int(len(linked)),
        "expanded_actionable_event_count": int(linked["firm_grade_actionable_flag"].sum()) if not linked.empty else 0,
        "selected_event_id": "" if selected is None else selected["event_id"],
        "selected_linkage_grade": "no_link" if selected is None else selected["linkage_grade"],
        "selected_claim_type": "no_interpretable_claim" if selected is None else selected["claim_type"],
        "action_bucket": action,
        "block_hold_flag": int(action == "BLOCK_HOLD"),
        "size_down_flag": int(action == "SIZE_DOWN"),
        "delay_entry_flag": int(action == "DELAY_ENTRY"),
        "confirmation_required_flag": int(action == "CONFIRMATION_REQUIRED"),
        "no_action_flag": int(action == "NO_ACTION"),
        "theme_only_no_action_flag": int(selected is not None and selected["theme_only_no_action_flag"] == 1),
        "source_presence_only_used_flag_task630": 0,
        "gpt_score_used_as_source_flag_task630": 0,
        "label_used_in_assignment_flag_task630": 0,
    }


def build_exact_delay_replay(enriched: pd.DataFrame, intraday_map: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for item in enriched.to_dict(orient="records"):
        base_return = float(item["net_return_from_entry"])
        for delay in DELAY_MINUTES:
            delayed = delayed_entry_price(item, intraday_map.get(str(item["symbol"]).upper(), pd.DataFrame()), delay)
            if delayed is None:
                delayed_return = pd.NA
                available = 0
                missing_reason = "not_delay_action" if int(item.get("delay_entry_flag", 0) or 0) != 1 else "delayed_intraday_bar_missing"
                delayed_ts = pd.NaT
                delayed_price = pd.NA
            else:
                delayed_ts, delayed_price = delayed
                delayed_return = float(item["simulated_exit_price"]) / float(delayed_price) - 1.0
                available = 1
                missing_reason = ""
            rows.append(
                {
                    "lifecycle_id": item["lifecycle_id"],
                    "symbol": item["symbol"],
                    "split_name": item["split_name"],
                    "action_bucket": item.get("action_bucket", "NO_ACTION"),
                    "delay_minutes": int(delay),
                    "delay_action_flag": int(item.get("delay_entry_flag", 0) or 0),
                    "delayed_price_available_flag": available,
                    "original_entry_ts": item["entry_ts"],
                    "delayed_entry_ts": delayed_ts,
                    "original_entry_price": float(item["entry_price"]),
                    "delayed_entry_price": delayed_price,
                    "simulated_exit_ts": item["simulated_exit_ts"],
                    "simulated_exit_price": float(item["simulated_exit_price"]),
                    "original_return": base_return,
                    "delayed_return": delayed_return,
                    "delta_return": (float(delayed_return) - base_return) if available else pd.NA,
                    "missing_reason": missing_reason,
                    "label_used_in_assignment_flag": 0,
                    "gpt_score_used_as_source_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_false_block_audit(enriched: pd.DataFrame) -> pd.DataFrame:
    blocked = enriched[enriched["block_hold_flag"].fillna(0).astype(int).eq(1)].copy()
    if blocked.empty:
        return pd.DataFrame(
            columns=[
                "lifecycle_id",
                "symbol",
                "split_name",
                "net_return_from_entry",
                "blocked_winner_flag",
                "selected_event_id",
                "selected_linkage_grade",
                "selected_claim_type",
            ]
        )
    blocked["blocked_winner_flag"] = pd.to_numeric(blocked["net_return_from_entry"], errors="coerce").gt(0).astype(int)
    return blocked[
        [
            "lifecycle_id",
            "symbol",
            "split_name",
            "net_return_from_entry",
            "blocked_winner_flag",
            "selected_event_id",
            "selected_linkage_grade",
            "selected_claim_type",
        ]
    ].sort_values(["split_name", "symbol", "lifecycle_id"])


def delayed_entry_price(item: dict[str, object], frame: pd.DataFrame, delay: int) -> tuple[pd.Timestamp, float] | None:
    if int(item.get("delay_entry_flag", 0) or 0) != 1 or frame.empty:
        return None
    entry_ts = pd.Timestamp(item["entry_ts"])
    exit_ts = pd.Timestamp(item["simulated_exit_ts"])
    target_ts = entry_ts + pd.Timedelta(minutes=delay)
    session_date = entry_ts.tz_convert("America/New_York").date().isoformat()
    session = frame[frame["session_date_et"].eq(session_date)].copy()
    if session.empty or target_ts >= exit_ts:
        return None
    bar = session[(session["timestamp"].ge(target_ts)) & (session["timestamp"].lt(exit_ts))].head(1)
    if bar.empty:
        return None
    return pd.Timestamp(bar.iloc[0]["timestamp"]), float(bar.iloc[0]["close"])


def build_policy_evaluation(enriched: pd.DataFrame, delay_replay: pd.DataFrame) -> pd.DataFrame:
    rows = []
    variants = {"original_turboquant": enriched, "block_and_size_down_only": apply_block_size(enriched)}
    for delay in DELAY_MINUTES:
        variants[f"block_size_exact_delay_{delay}m"] = apply_block_size_delay(enriched, delay_replay, delay)
    for name, frame in variants.items():
        for split in SCOPES:
            group = frame if split == "full_panel" else frame[frame["split_name"].astype(str).eq(split)]
            metrics = aggregate(group) if not group.empty else {}
            rows.append(
                {
                    "policy_variant": name,
                    "split_name": split,
                    "trade_count": int(len(group)),
                    "avg_net_return_pct": float(metrics.get("avg_net_return_pct", 0.0)),
                    "win_rate": float(metrics.get("win_rate", 0.0)),
                    "entry_reduce_failure_rate": float(metrics.get("entry_reduce_failure_rate", 0.0)),
                    "label_used_in_assignment_flag": 0,
                    "gpt_score_used_as_source_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def apply_block_size(enriched: pd.DataFrame) -> pd.DataFrame:
    frame = enriched[~enriched["block_hold_flag"].fillna(0).astype(int).eq(1)].copy()
    size_down = frame["size_down_flag"].fillna(0).astype(int).eq(1)
    frame.loc[size_down, "net_return_from_entry"] = pd.to_numeric(frame.loc[size_down, "net_return_from_entry"], errors="coerce") * 0.5
    return frame


def apply_block_size_delay(enriched: pd.DataFrame, delay_replay: pd.DataFrame, delay: int) -> pd.DataFrame:
    frame = apply_block_size(enriched)
    replay = delay_replay[
        delay_replay["delay_minutes"].astype(int).eq(delay)
        & delay_replay["delay_action_flag"].astype(int).eq(1)
    ][["lifecycle_id", "delayed_price_available_flag", "delayed_return"]]
    frame = frame.merge(replay, on="lifecycle_id", how="left")
    missing_delay = frame["delay_entry_flag"].fillna(0).astype(int).eq(1) & ~frame["delayed_price_available_flag"].fillna(0).astype(int).eq(1)
    frame = frame[~missing_delay].copy()
    has_delay = frame["delayed_price_available_flag"].fillna(0).astype(int).eq(1)
    frame.loc[has_delay, "net_return_from_entry"] = pd.to_numeric(frame.loc[has_delay, "delayed_return"], errors="coerce")
    return frame.drop(columns=[c for c in ["delayed_price_available_flag", "delayed_return"] if c in frame.columns])


def build_cost_account_matrix(enriched: pd.DataFrame, delay_replay: pd.DataFrame) -> pd.DataFrame:
    variants = {"turboquant_original": enriched}
    for delay in DELAY_MINUTES:
        variants[f"firm_grade_exact_delay_{delay}m"] = apply_block_size_delay(enriched, delay_replay, delay)
    rows = []
    for universe, base in variants.items():
        for scope in SCOPES:
            scoped = base if scope == "full_panel" else base[base["split_name"].astype(str).eq(scope)]
            costed = scoped.copy()
            costed["net_return_from_entry"] = pd.to_numeric(costed["net_return_from_entry"], errors="coerce") - (
                DECISION_COST_BPS / 10000.0
            )
            for max_positions in MAX_POSITIONS:
                quality, accepted, _curve = simulate_deterministic_portfolio(costed, max_positions=max_positions)
                rows.append(
                    {
                        "universe": universe,
                        "scope": scope,
                        "round_trip_cost_bps": DECISION_COST_BPS,
                        "initial_capital_usd": INITIAL_CAPITAL_USD,
                        "max_positions": int(max_positions),
                        "source_trade_count": int(len(scoped)),
                        "accepted_trade_count": int(len(accepted)),
                        "final_capital_usd": INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0),
                        "capital_return_pct": float(quality["capital_pnl_pct"]),
                        "avg_net_return_pct": float(quality["avg_net_return_pct"]),
                        "win_rate": float(quality["win_rate"]),
                        "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                        "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                        "label_used_in_assignment_flag": 0,
                        "gpt_score_used_as_source_flag": 0,
                    }
                )
    return pd.DataFrame(rows)


def build_block_hold_coverage_audit(linkage: pd.DataFrame, attachment: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for symbol in EXPANDED_ENTITY_GRAPH:
        registry = linkage[linkage["symbol"].eq(symbol)]
        trades = attachment[attachment["symbol"].eq(symbol)]
        rows.append(
            {
                "symbol": symbol,
                "direct_company_negative_registry_count": int(registry["direct_company_negative_candidate_flag"].sum()),
                "economic_direct_negative_registry_count": int(registry["economic_direct_negative_candidate_flag"].sum()),
                "block_hold_trade_count": int(trades["block_hold_flag"].sum()),
                "size_down_trade_count": int(trades["size_down_flag"].sum()),
                "delay_entry_trade_count": int(trades["delay_entry_flag"].sum()),
                "confirmation_required_trade_count": int(trades["confirmation_required_flag"].sum()),
                "no_action_trade_count": int(trades["no_action_flag"].sum()),
            }
        )
    rows.append(
        {
            "symbol": "ALL",
            "direct_company_negative_registry_count": int(linkage["direct_company_negative_candidate_flag"].sum()),
            "economic_direct_negative_registry_count": int(linkage["economic_direct_negative_candidate_flag"].sum()),
            "block_hold_trade_count": int(attachment["block_hold_flag"].sum()),
            "size_down_trade_count": int(attachment["size_down_flag"].sum()),
            "delay_entry_trade_count": int(attachment["delay_entry_flag"].sum()),
            "confirmation_required_trade_count": int(attachment["confirmation_required_flag"].sum()),
            "no_action_trade_count": int(attachment["no_action_flag"].sum()),
        }
    )
    return pd.DataFrame(rows)


def metric(policy_eval: pd.DataFrame, variant: str, split: str, column: str) -> float:
    return float(policy_eval[policy_eval["policy_variant"].eq(variant) & policy_eval["split_name"].eq(split)].iloc[0][column])


def capital_wins(cost_account: pd.DataFrame, universe: str, scope: str) -> tuple[int, str]:
    original = cost_account[cost_account["universe"].eq("turboquant_original") & cost_account["scope"].eq(scope)]
    variant = cost_account[cost_account["universe"].eq(universe) & cost_account["scope"].eq(scope)]
    merged = variant[["max_positions", "final_capital_usd"]].merge(
        original[["max_positions", "final_capital_usd"]],
        on="max_positions",
        suffixes=("_variant", "_original"),
    )
    wins = int((merged["final_capital_usd_variant"] > merged["final_capital_usd_original"]).sum())
    pairs = "; ".join(
        f"max{int(r.max_positions)} variant=${float(r.final_capital_usd_variant):.2f} original=${float(r.final_capital_usd_original):.2f}"
        for r in merged.itertuples()
    )
    return wins, pairs


def best_delay_variant(policy_eval: pd.DataFrame) -> str:
    rows = policy_eval[
        policy_eval["policy_variant"].str.startswith("block_size_exact_delay_")
        & policy_eval["split_name"].eq("recent_oos")
    ].copy()
    rows = rows.sort_values("avg_net_return_pct", ascending=False)
    return str(rows.iloc[0]["policy_variant"])


def build_pass_fail(
    coverage: pd.DataFrame,
    delay_replay: pd.DataFrame,
    policy_eval: pd.DataFrame,
    cost_account: pd.DataFrame,
) -> pd.DataFrame:
    all_row = coverage[coverage["symbol"].eq("ALL")].iloc[0]
    best_variant = best_delay_variant(policy_eval)
    best_universe = "firm_grade_exact_delay_" + best_variant.rsplit("_", 1)[-1]
    original_recent = metric(policy_eval, "original_turboquant", "recent_oos", "avg_net_return_pct")
    best_recent = metric(policy_eval, best_variant, "recent_oos", "avg_net_return_pct")
    original_validation = metric(policy_eval, "original_turboquant", "validation", "avg_net_return_pct")
    best_validation = metric(policy_eval, best_variant, "validation", "avg_net_return_pct")
    delayed_actions = delay_replay[delay_replay["delay_action_flag"].astype(int).eq(1)]
    coverage_rate = float(delayed_actions["delayed_price_available_flag"].astype(int).mean()) if not delayed_actions.empty else 0.0
    recent_wins, recent_pairs = capital_wins(cost_account, best_universe, "recent_oos")
    validation_wins, validation_pairs = capital_wins(cost_account, best_universe, "validation")
    full_wins, full_pairs = capital_wins(cost_account, best_universe, "full_panel")
    return pd.DataFrame(
        [
            {
                "gate": "block_hold_coverage_audited",
                "pass_flag": 1,
                "observed_value": (
                    f"registry_direct_negative={int(all_row['direct_company_negative_registry_count'])}; "
                    f"registry_economic_direct_negative={int(all_row['economic_direct_negative_registry_count'])}; "
                    f"trade_block_hold={int(all_row['block_hold_trade_count'])}"
                ),
                "required_value": "coverage is measured before claiming BLOCK_HOLD effectiveness",
            },
            {
                "gate": "theme_only_not_actionable",
                "pass_flag": 1,
                "observed_value": "theme-only remains NO_ACTION by construction",
                "required_value": "broad theme words cannot create BLOCK_HOLD",
            },
            {
                "gate": "exact_delay_price_coverage",
                "pass_flag": int(coverage_rate >= 0.95),
                "observed_value": f"delayed_action_price_coverage={coverage_rate:.2%}",
                "required_value": "at least 95% of delayed actions must have real intraday delayed prices",
            },
            {
                "gate": "recent_oos_best_delay_improves",
                "pass_flag": int(best_recent >= original_recent),
                "observed_value": f"{best_variant} recent {best_recent:.2f}% vs original {original_recent:.2f}%",
                "required_value": "best exact delay scenario must not reduce recent OOS gross average",
            },
            {
                "gate": "validation_best_delay_not_broken",
                "pass_flag": int(best_validation >= original_validation),
                "observed_value": f"{best_variant} validation {best_validation:.2f}% vs original {original_validation:.2f}%",
                "required_value": "best exact delay scenario must not reduce validation gross average",
            },
            {
                "gate": "recent_oos_50bp_account_edge",
                "pass_flag": int(recent_wins >= 3),
                "observed_value": f"{best_universe} wins={recent_wins}/4; {recent_pairs}",
                "required_value": "best exact delay universe beats original in at least 3 of 4 recent-OOS capacities at 50bp",
            },
            {
                "gate": "validation_50bp_not_broken",
                "pass_flag": int(validation_wins >= 2),
                "observed_value": f"{best_universe} wins={validation_wins}/4; {validation_pairs}",
                "required_value": "best exact delay universe is at least mixed on validation account performance at 50bp",
            },
            {
                "gate": "full_panel_50bp_account_edge",
                "pass_flag": int(full_wins >= 2),
                "observed_value": f"{best_universe} wins={full_wins}/4; {full_pairs}",
                "required_value": "best exact delay universe is at least mixed on full-panel account performance at 50bp",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "coverage and exact delay replay diagnostic only",
                "required_value": "requires source-owned entity expansion, split robustness, and live-source readiness",
            },
        ]
    )


def build_decision(
    pass_fail: pd.DataFrame,
    attachment: pd.DataFrame,
    delay_replay: pd.DataFrame,
    cost_account: pd.DataFrame,
) -> pd.DataFrame:
    best = pass_fail[pass_fail["gate"].eq("recent_oos_best_delay_improves")]["observed_value"].iloc[0].split()[0]
    recent_pass = int(pass_fail[pass_fail["gate"].eq("recent_oos_50bp_account_edge")]["pass_flag"].iloc[0])
    validation_pass = int(pass_fail[pass_fail["gate"].eq("validation_50bp_not_broken")]["pass_flag"].iloc[0])
    full_pass = int(pass_fail[pass_fail["gate"].eq("full_panel_50bp_account_edge")]["pass_flag"].iloc[0])
    coverage_rate = float(
        delay_replay[delay_replay["delay_action_flag"].astype(int).eq(1)]["delayed_price_available_flag"].astype(int).mean()
    )
    decision = "FAIL_EXACT_DELAY_AND_BLOCK_HOLD_COVERAGE_NOT_ACCEPTED"
    if recent_pass and validation_pass and full_pass:
        decision = "PASS_EXACT_DELAY_DIAGNOSTIC_NOT_ACCEPTED"
    counts = attachment["action_bucket"].value_counts().to_dict()
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "best_exact_delay_variant": best,
                "exact_delay_price_coverage_rate": coverage_rate,
                "block_hold_trade_count": int(counts.get("BLOCK_HOLD", 0)),
                "size_down_trade_count": int(counts.get("SIZE_DOWN", 0)),
                "delay_entry_trade_count": int(counts.get("DELAY_ENTRY", 0)),
                "confirmation_required_trade_count": int(counts.get("CONFIRMATION_REQUIRED", 0)),
                "no_action_trade_count": int(counts.get("NO_ACTION", 0)),
                "recent_oos_50bp_account_edge_pass_flag": recent_pass,
                "validation_50bp_not_broken_pass_flag": validation_pass,
                "full_panel_50bp_account_edge_pass_flag": full_pass,
                "source_presence_only_used_flag": 0,
                "gpt_score_used_as_source_flag": 0,
                "label_used_in_assignment_flag": 0,
                "trading_promotion_pass_flag": 0,
                "next_action": "Source-own the expanded entity graph and rerun split robustness before accepting any BLOCK_HOLD or exact-delay rule.",
            }
        ]
    )


def build_gpt_review_record() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reviewer": "Chrome ChatGPT 1. coding/investment tab",
                "captured_at_kst": "2026-06-07",
                "source_type": "external_model_interpretation_not_source_truth",
                "used_as_source_flag": 0,
                "review_summary": (
                    "BLOCK_HOLD=0 should be treated as unobserved coverage, not proof of no effect. "
                    "Task630 should audit coverage, separate direct_company from economic_direct, and replay delayed entries with real intraday prices."
                ),
            }
        ]
    )


def render_report(
    coverage: pd.DataFrame,
    attachment: pd.DataFrame,
    delay_replay: pd.DataFrame,
    policy_eval: pd.DataFrame,
    cost_account: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task630 Block Hold Coverage And Exact Delay Replay",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- GPT/Chrome was used only as review input, not source truth or score input.",
        f"- Best exact delay variant: `{d['best_exact_delay_variant']}`",
        f"- Exact delay price coverage: {float(d['exact_delay_price_coverage_rate']):.2%}",
        f"- Action counts: BLOCK/HOLD {int(d['block_hold_trade_count'])}, SIZE_DOWN {int(d['size_down_trade_count'])}, DELAY_ENTRY {int(d['delay_entry_trade_count'])}, CONFIRMATION_REQUIRED {int(d['confirmation_required_trade_count'])}, NO_ACTION {int(d['no_action_trade_count'])}.",
        "",
        "## Quant Expert Report",
        "",
        "Task630 treats `BLOCK_HOLD = 0` as a coverage question first. It then tests delayed entries with real intraday prices instead of deleting delayed-entry trades.",
        "",
        "### Block Hold Coverage",
        "",
        "| Symbol | Direct Neg Registry | Economic Direct Neg Registry | BLOCK/HOLD Trades | SIZE_DOWN | DELAY_ENTRY | CONFIRM | NO_ACTION |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in coverage.iterrows():
        lines.append(
            f"| `{row['symbol']}` | {int(row['direct_company_negative_registry_count'])} | "
            f"{int(row['economic_direct_negative_registry_count'])} | {int(row['block_hold_trade_count'])} | "
            f"{int(row['size_down_trade_count'])} | {int(row['delay_entry_trade_count'])} | "
            f"{int(row['confirmation_required_trade_count'])} | {int(row['no_action_trade_count'])} |"
        )
    lines.extend(
        [
            "",
            "### Exact Delay Gross Evaluation",
            "",
            "| Variant | Split | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for _, row in policy_eval.iterrows():
        lines.append(
            f"| `{row['policy_variant']}` | `{row['split_name']}` | {int(row['trade_count'])} | "
            f"{float(row['avg_net_return_pct']):.2f}% | {float(row['win_rate']):.2f}% | {float(row['entry_reduce_failure_rate']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "### 50bp Account Matrix",
            "",
            "| Scope | Universe | Max Positions | Final $ | Return |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for _, row in cost_account.sort_values(["scope", "max_positions", "universe"]).iterrows():
        lines.append(
            f"| `{row['scope']}` | `{row['universe']}` | {int(row['max_positions'])} | "
            f"${float(row['final_capital_usd']):,.2f} | {float(row['capital_return_pct']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- `BLOCK_HOLD`가 0인 건 아직 발동 기회가 거의 없다는 뜻입니다.",
            "- 억지로 BLOCK을 늘리지 않았습니다. 직접/경제 직접 연결을 분리해서 감사했습니다.",
            "- `DELAY_ENTRY`는 이제 실제 분봉 가격으로 15/30/60분 뒤 진입을 재생했습니다.",
            "- 그래도 전략 승인은 아닙니다. 전체 계좌와 커버리지 검증이 더 필요합니다.",
            "",
            "## Pass/Fail Matrix",
            "",
            "| Gate | Pass | Observed | Required |",
            "|---|---:|---|---|",
        ]
    )
    for _, row in pass_fail.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "### Inputs",
            "",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "- `docs/reports/task_627_source_text_theme_linkage_validation/task_627_source_text_linkage_scores.csv`",
            "- `data/raw/us_intraday/`",
            "",
            "### Outputs",
            "",
            "- `task_630_expanded_event_linkage_registry.csv`",
            "- `task_630_expanded_trade_action_attachment.csv`",
            "- `task_630_intraday_source_coverage.csv`",
            "- `task_630_exact_delayed_entry_replay.csv`",
            "- `task_630_false_block_audit.csv`",
            "- `task_630_policy_variant_evaluation.csv`",
            "- `task_630_cost_account_matrix.csv`",
            "- `task_630_block_hold_coverage_audit.csv`",
            "- `task_630_pass_fail_matrix.csv`",
            "- `task_630_decision.csv`",
            "- `task_630_gpt_review_capture.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task630_block_hold_coverage_and_exact_delay_replay`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
            "- `python scripts/governance_completion_audit.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task630_block_hold_coverage_and_exact_delay_replay(out_dir=args.out_dir)
    row = artifacts["task_630_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"best={row['best_exact_delay_variant']} "
        f"block={int(row['block_hold_trade_count'])} "
        f"delay={int(row['delay_entry_trade_count'])}"
    )


if __name__ == "__main__":
    main()
