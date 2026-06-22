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
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio
from src.backtest.build_task622_source_semantic_interpretation_sidecar import TASK617_PANEL, load_panel, within_window
from src.backtest.build_task627_source_text_theme_linkage_validation import (
    REPORT_DIR as TASK627_DIR,
    read_raw_text,
)


TASK_ID = "Task629"
REPORT_DIR = Path("docs/reports/task_629_firm_grade_event_linkage_action_taxonomy")
TASK627_SCORE_PATH = TASK627_DIR / "task_627_source_text_linkage_scores.csv"
SCOPES = ("full_panel", "validation", "recent_oos")
MAX_POSITIONS = (5, 10, 20, 50)
INITIAL_CAPITAL_USD = 1000.0
DECISION_COST_BPS = 50


SYMBOL_LINKAGE_TERMS: dict[str, dict[str, tuple[str, ...]]] = {
    "BA": {
        "entity": ("boeing", "the boeing company"),
        "product": ("737", "787", "aircraft", "airplane", "commercial aviation", "aviation safety"),
        "customer": ("airline", "airlines", "air force", "nasa", "dod", "department of defense"),
        "supplier": ("supply chain", "supplier", "engine", "parts"),
        "contract": ("contract", "award", "order", "backlog"),
        "funding": ("budget", "funding", "appropriation"),
        "regulator": ("faa", "federal aviation administration", "ntsb"),
        "geography": ("china", "russia", "iran", "europe", "middle east"),
        "competitor": ("airbus",),
    },
    "RKLB": {
        "entity": ("rocket lab", "rocketlab", "rklb"),
        "product": ("rocket", "launch", "satellite", "space launch", "electron", "neutron", "propulsion"),
        "customer": ("nasa", "space force", "dod", "department of defense", "commercial satellite"),
        "supplier": ("supply chain", "supplier", "component", "propulsion"),
        "contract": ("contract", "award", "order", "mission"),
        "funding": ("budget", "funding", "appropriation"),
        "regulator": ("faa", "fcc", "federal communications commission"),
        "geography": ("new zealand", "virginia", "russia", "china"),
        "competitor": ("spacex", "blue origin"),
    },
    "ASTS": {
        "entity": ("ast spacemobile", "asts", "spacemobile"),
        "product": ("satellite", "cellular", "broadband", "direct-to-device", "space-based", "telecom"),
        "customer": ("wireless carrier", "mobile network", "telecom", "government"),
        "supplier": ("supply chain", "supplier", "component", "launch"),
        "contract": ("contract", "award", "order", "agreement"),
        "funding": ("funding", "financing", "capital", "budget"),
        "regulator": ("fcc", "federal communications commission", "spectrum"),
        "geography": ("united states", "europe", "india", "global"),
        "competitor": ("starlink", "spacex"),
    },
    "RTX": {
        "entity": ("rtx", "raytheon", "pratt & whitney", "pratt and whitney", "collins aerospace"),
        "product": ("missile", "patriot", "air defense", "aircraft engine", "engine", "radar", "defense system"),
        "customer": ("air force", "army", "navy", "dod", "department of defense", "nato"),
        "supplier": ("supply chain", "supplier", "component", "parts"),
        "contract": ("contract", "award", "order", "backlog"),
        "funding": ("budget", "funding", "appropriation"),
        "regulator": ("faa", "department of justice", "justice department"),
        "geography": ("ukraine", "russia", "iran", "middle east", "china"),
        "competitor": ("lockheed", "northrop", "boeing"),
    },
}

THEME_TERMS = (
    "defense",
    "military",
    "air force",
    "armed forces",
    "aviation",
    "aircraft",
    "aerospace",
    "space",
    "satellite",
    "rocket",
    "missile",
    "propulsion",
    "drone",
    "uav",
    "launch",
)

NEGATIVE_CLAIM_TERMS = (
    "sanction",
    "designation",
    "export control",
    "restricted",
    "delay",
    "grounding",
    "investigation",
    "failure",
    "accident",
    "crash",
    "defect",
    "attack",
    "war",
    "conflict",
    "budget cut",
    "blocked",
)

POSITIVE_CLAIM_TERMS = (
    "contract",
    "award",
    "order",
    "funding",
    "budget",
    "appropriation",
    "approval",
    "authorization",
    "launch success",
    "backlog",
    "production",
    "delivery",
)


def build_task629_firm_grade_event_linkage_action_taxonomy(
    *,
    task617_panel_path: Path = TASK617_PANEL,
    task627_score_path: Path = TASK627_SCORE_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task617_panel_path)
    source_scores = pd.read_csv(task627_score_path)
    source_scores["event_date_obj"] = pd.to_datetime(source_scores["event_date_obj"], errors="coerce").dt.date
    source_scores["event_timestamp_dt"] = pd.to_datetime(source_scores["event_timestamp_dt"], utc=True, errors="coerce")

    linkage = build_event_symbol_linkage_registry(source_scores)
    attachment = build_trade_action_attachment(panel, linkage)
    enriched = panel.merge(attachment, on="lifecycle_id", how="left")
    action_eval = build_action_variant_evaluation(enriched)
    cost_account = build_cost_account_matrix(enriched)
    pass_fail = build_pass_fail(linkage, attachment, action_eval, cost_account)
    decision = build_decision(pass_fail, attachment, cost_account)
    gpt_review = build_gpt_review_record()

    out_dir.mkdir(parents=True, exist_ok=True)
    linkage.to_csv(out_dir / "task_629_event_symbol_linkage_registry.csv", index=False)
    attachment.to_csv(out_dir / "task_629_trade_action_attachment.csv", index=False)
    action_eval.to_csv(out_dir / "task_629_action_variant_evaluation.csv", index=False)
    cost_account.to_csv(out_dir / "task_629_cost_account_matrix.csv", index=False)
    pass_fail.to_csv(out_dir / "task_629_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_629_decision.csv", index=False)
    gpt_review.to_csv(out_dir / "task_629_gpt_review_capture.csv", index=False)
    (out_dir / "task_629_firm_grade_event_linkage_action_taxonomy.md").write_text(
        render_report(linkage, attachment, action_eval, cost_account, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")

    return {
        "task_629_event_symbol_linkage_registry": linkage,
        "task_629_trade_action_attachment": attachment,
        "task_629_action_variant_evaluation": action_eval,
        "task_629_cost_account_matrix": cost_account,
        "task_629_pass_fail_matrix": pass_fail,
        "task_629_decision": decision,
        "task_629_gpt_review_capture": gpt_review,
    }


def build_event_symbol_linkage_registry(source_scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    certified = source_scores[source_scores["source_text_certified_flag"].fillna(0).astype(int).eq(1)].copy()
    for _, event in certified.iterrows():
        text = read_raw_text(event.get("raw_text_path", ""))
        for symbol in SYMBOL_LINKAGE_TERMS:
            row = event.to_dict()
            row["symbol"] = symbol
            row.update(classify_symbol_linkage(text, symbol))
            row["source_presence_only_used_flag_task629"] = 0
            row["gpt_score_used_as_source_flag_task629"] = 0
            row["label_used_in_assignment_flag_task629"] = 0
            rows.append(row)
    return pd.DataFrame(rows)


def classify_symbol_linkage(text: str, symbol: str) -> dict[str, object]:
    terms = SYMBOL_LINKAGE_TERMS[symbol]
    layer_hits = {layer: keyword_count(text, values) for layer, values in terms.items()}
    theme_hits = keyword_count(text, THEME_TERMS)
    negative_hits = keyword_count(text, NEGATIVE_CLAIM_TERMS)
    positive_hits = keyword_count(text, POSITIVE_CLAIM_TERMS)

    entity_hit = layer_hits["entity"] > 0
    economic_layer_count = sum(1 for layer, hits in layer_hits.items() if layer != "entity" and hits > 0)
    has_negative = negative_hits > 0
    has_positive = positive_hits > 0

    if entity_hit:
        linkage_grade = "direct_company"
    elif economic_layer_count >= 2:
        linkage_grade = "economic_link"
    elif economic_layer_count == 1:
        linkage_grade = "single_channel_link"
    elif theme_hits > 0:
        linkage_grade = "theme_only"
    else:
        linkage_grade = "no_link"

    claim_type = claim_type_from_hits(layer_hits, has_negative, has_positive, theme_hits)
    action_template = action_from_linkage(linkage_grade, claim_type, has_negative, has_positive)
    evidence_tier = evidence_tier_from_linkage(linkage_grade, claim_type, layer_hits)

    return {
        **{f"{layer}_hit_count": int(count) for layer, count in layer_hits.items()},
        "theme_hit_count": int(theme_hits),
        "negative_claim_hit_count": int(negative_hits),
        "positive_claim_hit_count": int(positive_hits),
        "linkage_grade": linkage_grade,
        "claim_type": claim_type,
        "evidence_tier": evidence_tier,
        "action_template": action_template,
        "firm_grade_actionable_flag": int(action_template in {"BLOCK_HOLD", "SIZE_DOWN", "DELAY_ENTRY", "CONFIRMATION_REQUIRED"}),
        "theme_only_no_action_flag": int(linkage_grade == "theme_only" and action_template == "NO_ACTION"),
    }


def keyword_count(text: str, terms: tuple[str, ...]) -> int:
    if not text:
        return 0
    return sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", text))


def claim_type_from_hits(layer_hits: dict[str, int], has_negative: bool, has_positive: bool, theme_hits: int) -> str:
    if layer_hits["entity"] > 0 and has_negative:
        return "direct_company_negative_claim"
    if layer_hits["entity"] > 0 and has_positive:
        return "direct_company_positive_or_material_claim"
    if layer_hits["contract"] > 0 or layer_hits["funding"] > 0:
        return "contract_or_funding_claim"
    if layer_hits["regulator"] > 0:
        return "regulator_claim"
    if layer_hits["customer"] > 0:
        return "customer_demand_claim"
    if layer_hits["supplier"] > 0:
        return "supply_chain_claim"
    if layer_hits["competitor"] > 0:
        return "competitor_claim"
    if layer_hits["product"] > 0:
        return "product_market_claim"
    if layer_hits["geography"] > 0:
        return "geography_exposure_claim"
    if theme_hits > 0 and (has_negative or has_positive):
        return "theme_claim_only"
    return "no_interpretable_claim"


def action_from_linkage(linkage_grade: str, claim_type: str, has_negative: bool, has_positive: bool) -> str:
    if linkage_grade == "direct_company" and has_negative:
        return "BLOCK_HOLD"
    if linkage_grade in {"economic_link", "single_channel_link"} and has_negative:
        if claim_type in {"regulator_claim", "supply_chain_claim", "geography_exposure_claim"}:
            return "DELAY_ENTRY"
        return "SIZE_DOWN"
    if linkage_grade in {"direct_company", "economic_link"} and has_positive and not has_negative:
        return "CONFIRMATION_REQUIRED"
    return "NO_ACTION"


def evidence_tier_from_linkage(linkage_grade: str, claim_type: str, layer_hits: dict[str, int]) -> str:
    if linkage_grade == "direct_company":
        return "tier_1_direct_company"
    if linkage_grade == "economic_link" and claim_type != "theme_claim_only":
        return "tier_2_multi_channel_economic"
    if linkage_grade == "single_channel_link" and claim_type != "theme_claim_only":
        return "tier_3_single_channel_economic"
    if linkage_grade == "theme_only":
        return "tier_4_theme_only_no_trade"
    return "tier_5_no_link"


def build_trade_action_attachment(panel: pd.DataFrame, linkage: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, entry in panel.iterrows():
        linked = linked_events_for_entry(linkage, entry)
        selected = select_strongest_event(linked)
        rows.append(build_attachment_row(entry, linked, selected))
    return pd.DataFrame(rows)


def linked_events_for_entry(linkage: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    symbol = str(entry["symbol"])
    if symbol not in SYMBOL_LINKAGE_TERMS:
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
    priority = {
        "BLOCK_HOLD": 5,
        "DELAY_ENTRY": 4,
        "SIZE_DOWN": 3,
        "CONFIRMATION_REQUIRED": 2,
        "NO_ACTION": 1,
    }
    grade_priority = {
        "direct_company": 5,
        "economic_link": 4,
        "single_channel_link": 3,
        "theme_only": 1,
        "no_link": 0,
    }
    ranked = linked.copy()
    ranked["_action_priority"] = ranked["action_template"].map(priority).fillna(0)
    ranked["_grade_priority"] = ranked["linkage_grade"].map(grade_priority).fillna(0)
    ranked["_score"] = pd.to_numeric(ranked["composite_interpretation_score"], errors="coerce").fillna(0.0)
    ranked = ranked.sort_values(["_action_priority", "_grade_priority", "_score", "event_timestamp_dt"], ascending=[False, False, False, False])
    return ranked.iloc[0]


def build_attachment_row(entry: pd.Series, linked: pd.DataFrame, selected: pd.Series | None) -> dict[str, object]:
    action = "NO_ACTION" if selected is None else str(selected["action_template"])
    return {
        "lifecycle_id": entry["lifecycle_id"],
        "symbol": entry["symbol"],
        "firm_grade_linked_event_count": int(len(linked)),
        "firm_grade_actionable_event_count": int(linked["firm_grade_actionable_flag"].sum()) if not linked.empty else 0,
        "selected_event_id": "" if selected is None else selected["event_id"],
        "selected_linkage_grade": "no_link" if selected is None else selected["linkage_grade"],
        "selected_claim_type": "no_interpretable_claim" if selected is None else selected["claim_type"],
        "selected_evidence_tier": "tier_5_no_link" if selected is None else selected["evidence_tier"],
        "action_bucket": action,
        "block_hold_flag": int(action == "BLOCK_HOLD"),
        "size_down_flag": int(action == "SIZE_DOWN"),
        "delay_entry_flag": int(action == "DELAY_ENTRY"),
        "confirmation_required_flag": int(action == "CONFIRMATION_REQUIRED"),
        "no_action_flag": int(action == "NO_ACTION"),
        "theme_only_no_action_flag": int(selected is not None and selected["theme_only_no_action_flag"] == 1),
        "source_presence_only_used_flag_task629": 0,
        "gpt_score_used_as_source_flag_task629": 0,
        "label_used_in_assignment_flag_task629": 0,
    }


def build_action_variant_evaluation(enriched: pd.DataFrame) -> pd.DataFrame:
    variants = {
        "original_turboquant": enriched,
        "block_direct_negative": enriched[~enriched["block_hold_flag"].fillna(0).astype(int).eq(1)],
        "block_delay_size_down_half": apply_size_down(
            enriched[~enriched["block_hold_flag"].fillna(0).astype(int).eq(1)]
        ),
    }
    rows = []
    for variant_name, variant_df in variants.items():
        for split in SCOPES:
            group = variant_df if split == "full_panel" else variant_df[variant_df["split_name"].astype(str).eq(split)]
            metrics = aggregate(group) if not group.empty else {}
            rows.append(
                {
                    "policy_variant": variant_name,
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


def apply_size_down(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    size_down = out["size_down_flag"].fillna(0).astype(int).eq(1)
    delay = out["delay_entry_flag"].fillna(0).astype(int).eq(1)
    out.loc[size_down, "net_return_from_entry"] = pd.to_numeric(out.loc[size_down, "net_return_from_entry"], errors="coerce") * 0.5
    return out[~delay].copy()


def build_cost_account_matrix(enriched: pd.DataFrame) -> pd.DataFrame:
    universes = {
        "turboquant_original": enriched,
        "firm_grade_action_taxonomy": apply_size_down(enriched[~enriched["block_hold_flag"].fillna(0).astype(int).eq(1)]),
    }
    rows = []
    for universe, base in universes.items():
        for scope in SCOPES:
            scoped = base if scope == "full_panel" else base[base["split_name"].astype(str).eq(scope)]
            for max_positions in MAX_POSITIONS:
                costed = scoped.copy()
                costed["net_return_from_entry"] = pd.to_numeric(costed["net_return_from_entry"], errors="coerce") - (
                    DECISION_COST_BPS / 10000.0
                )
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


def metric(action_eval: pd.DataFrame, variant: str, split: str, column: str) -> float:
    return float(action_eval[action_eval["policy_variant"].eq(variant) & action_eval["split_name"].eq(split)].iloc[0][column])


def capital_wins(cost_account: pd.DataFrame, scope: str) -> tuple[int, pd.DataFrame]:
    original = cost_account[cost_account["universe"].eq("turboquant_original") & cost_account["scope"].eq(scope)]
    taxonomy = cost_account[cost_account["universe"].eq("firm_grade_action_taxonomy") & cost_account["scope"].eq(scope)]
    merged = taxonomy[["max_positions", "final_capital_usd"]].merge(
        original[["max_positions", "final_capital_usd"]],
        on="max_positions",
        suffixes=("_taxonomy", "_original"),
    )
    return int((merged["final_capital_usd_taxonomy"] > merged["final_capital_usd_original"]).sum()), merged


def build_pass_fail(
    linkage: pd.DataFrame,
    attachment: pd.DataFrame,
    action_eval: pd.DataFrame,
    cost_account: pd.DataFrame,
) -> pd.DataFrame:
    action_count = int(attachment["firm_grade_actionable_event_count"].gt(0).sum())
    theme_only_actions = int(
        linkage[linkage["linkage_grade"].eq("theme_only") & linkage["firm_grade_actionable_flag"].astype(int).eq(1)].shape[0]
    )
    recent_original = metric(action_eval, "original_turboquant", "recent_oos", "avg_net_return_pct")
    recent_taxonomy = metric(action_eval, "block_delay_size_down_half", "recent_oos", "avg_net_return_pct")
    validation_original = metric(action_eval, "original_turboquant", "validation", "avg_net_return_pct")
    validation_taxonomy = metric(action_eval, "block_delay_size_down_half", "validation", "avg_net_return_pct")
    full_wins, full_pairs = capital_wins(cost_account, "full_panel")
    recent_wins, recent_pairs = capital_wins(cost_account, "recent_oos")
    validation_wins, validation_pairs = capital_wins(cost_account, "validation")
    return pd.DataFrame(
        [
            {
                "gate": "economic_linkage_not_theme_only",
                "pass_flag": int(theme_only_actions == 0),
                "observed_value": f"theme_only_actionable_events={theme_only_actions}",
                "required_value": "theme-only events must not create trading actions",
            },
            {
                "gate": "action_taxonomy_exists",
                "pass_flag": int(action_count > 0),
                "observed_value": f"trades_with_actionable_event={action_count}",
                "required_value": "at least one trade must receive deterministic non-NO_ACTION bucket",
            },
            {
                "gate": "recent_oos_not_worse_gross",
                "pass_flag": int(recent_taxonomy >= recent_original),
                "observed_value": f"recent {recent_taxonomy:.2f}% vs original {recent_original:.2f}%",
                "required_value": "action taxonomy should not reduce recent OOS gross average",
            },
            {
                "gate": "validation_not_broken_gross",
                "pass_flag": int(validation_taxonomy >= validation_original),
                "observed_value": f"validation {validation_taxonomy:.2f}% vs original {validation_original:.2f}%",
                "required_value": "action taxonomy should not reduce validation gross average",
            },
            {
                "gate": "recent_oos_50bp_account_edge",
                "pass_flag": int(recent_wins >= 3),
                "observed_value": f"taxonomy_wins={recent_wins}/4; {format_capital_pairs(recent_pairs)}",
                "required_value": "taxonomy must beat original in at least 3 of 4 recent-OOS capacities at 50bp",
            },
            {
                "gate": "validation_50bp_not_broken",
                "pass_flag": int(validation_wins >= 2),
                "observed_value": f"taxonomy_wins={validation_wins}/4; {format_capital_pairs(validation_pairs)}",
                "required_value": "taxonomy must be at least mixed on validation account performance at 50bp",
            },
            {
                "gate": "full_panel_50bp_account_edge",
                "pass_flag": int(full_wins >= 2),
                "observed_value": f"taxonomy_wins={full_wins}/4; {format_capital_pairs(full_pairs)}",
                "required_value": "taxonomy must be at least mixed on full-panel account performance at 50bp",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "firm-grade action taxonomy diagnostic only",
                "required_value": "requires exact delayed-entry replay, broader entity coverage, split robustness, and live-source readiness",
            },
        ]
    )


def format_capital_pairs(rows: pd.DataFrame) -> str:
    return "; ".join(
        f"max{int(r.max_positions)} taxonomy=${float(r.final_capital_usd_taxonomy):.2f} original=${float(r.final_capital_usd_original):.2f}"
        for r in rows.itertuples()
    )


def build_decision(pass_fail: pd.DataFrame, attachment: pd.DataFrame, cost_account: pd.DataFrame) -> pd.DataFrame:
    recent_pass = int(pass_fail[pass_fail["gate"].eq("recent_oos_50bp_account_edge")]["pass_flag"].iloc[0])
    validation_pass = int(pass_fail[pass_fail["gate"].eq("validation_50bp_not_broken")]["pass_flag"].iloc[0])
    full_pass = int(pass_fail[pass_fail["gate"].eq("full_panel_50bp_account_edge")]["pass_flag"].iloc[0])
    taxonomy_counts = attachment["action_bucket"].value_counts().to_dict()
    decision = "FAIL_FIRM_GRADE_ACTION_TAXONOMY_NOT_ACCEPTED"
    if recent_pass and validation_pass and full_pass:
        decision = "PASS_FIRM_GRADE_ACTION_TAXONOMY_DIAGNOSTIC_NOT_ACCEPTED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "recent_oos_50bp_account_edge_pass_flag": recent_pass,
                "validation_50bp_not_broken_pass_flag": validation_pass,
                "full_panel_50bp_account_edge_pass_flag": full_pass,
                "block_hold_trade_count": int(taxonomy_counts.get("BLOCK_HOLD", 0)),
                "size_down_trade_count": int(taxonomy_counts.get("SIZE_DOWN", 0)),
                "delay_entry_trade_count": int(taxonomy_counts.get("DELAY_ENTRY", 0)),
                "confirmation_required_trade_count": int(taxonomy_counts.get("CONFIRMATION_REQUIRED", 0)),
                "no_action_trade_count": int(taxonomy_counts.get("NO_ACTION", 0)),
                "source_presence_only_used_flag": 0,
                "gpt_score_used_as_source_flag": 0,
                "label_used_in_assignment_flag": 0,
                "trading_promotion_pass_flag": 0,
                "next_action": "Expand entity dictionaries and run exact delayed-entry/confirmation replay instead of using diagnostic hold approximations.",
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
                    "Firm-grade upgrade requires event-to-ticker economic linkage, claim extraction, "
                    "and action taxonomy; broad theme words and source presence must default to NO_ACTION."
                ),
            }
        ]
    )


def render_report(
    linkage: pd.DataFrame,
    attachment: pd.DataFrame,
    action_eval: pd.DataFrame,
    cost_account: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    counts = attachment["action_bucket"].value_counts().to_dict()
    rows50 = cost_account[cost_account["round_trip_cost_bps"].astype(int).eq(DECISION_COST_BPS)]
    lines = [
        "# Task629 Firm Grade Event Linkage Action Taxonomy",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- GPT/Chrome was used only as review input, not source truth or score input.",
        f"- Action counts: BLOCK/HOLD {int(counts.get('BLOCK_HOLD', 0))}, SIZE_DOWN {int(counts.get('SIZE_DOWN', 0))}, DELAY_ENTRY {int(counts.get('DELAY_ENTRY', 0))}, CONFIRMATION_REQUIRED {int(counts.get('CONFIRMATION_REQUIRED', 0))}, NO_ACTION {int(counts.get('NO_ACTION', 0))}.",
        "",
        "## Quant Expert Report",
        "",
        "Task629 replaces the Task627 theme-risk hold with an economic-linkage chain:",
        "",
        "`official source text -> symbol/entity/product/customer/supplier/contract/funding/regulator/geography/competitor links -> claim type -> action bucket`",
        "",
        "Broad theme words alone are demoted to `NO_ACTION`. Actions require at least one symbol-specific economic channel.",
        "",
        "### Gross Action Variant Evaluation",
        "",
        "| Variant | Split | Trades | Avg Net Return | Win Rate | Entry-Reduce Failure |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, row in action_eval.iterrows():
        lines.append(
            f"| `{row['policy_variant']}` | `{row['split_name']}` | {int(row['trade_count'])} | "
            f"{float(row['avg_net_return_pct']):.2f}% | {float(row['win_rate']):.2f}% | "
            f"{float(row['entry_reduce_failure_rate']):.2f}% |"
        )
    lines.extend(
        [
            "",
            f"### {DECISION_COST_BPS}bp $1000 Account Matrix",
            "",
            "| Scope | Universe | Max Positions | Final $ | Return |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for _, row in rows50.sort_values(["scope", "max_positions", "universe"]).iterrows():
        lines.append(
            f"| `{row['scope']}` | `{row['universe']}` | {int(row['max_positions'])} | "
            f"${float(row['final_capital_usd']):,.2f} | {float(row['capital_return_pct']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- 이번 업그레이드는 뉴스 단어 필터가 아니라 연결고리 필터입니다.",
            "- 회사/제품/고객/계약/규제 같은 돈의 연결고리가 없으면 행동하지 않습니다.",
            "- 아직 승인 아닙니다. 비용/계좌와 정확한 지연진입 재생 검증이 남았습니다.",
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
            "",
            "### Outputs",
            "",
            "- `task_629_event_symbol_linkage_registry.csv`",
            "- `task_629_trade_action_attachment.csv`",
            "- `task_629_action_variant_evaluation.csv`",
            "- `task_629_cost_account_matrix.csv`",
            "- `task_629_pass_fail_matrix.csv`",
            "- `task_629_decision.csv`",
            "- `task_629_gpt_review_capture.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task629_firm_grade_event_linkage_action_taxonomy`",
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
    artifacts = build_task629_firm_grade_event_linkage_action_taxonomy(out_dir=args.out_dir)
    row = artifacts["task_629_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"block={int(row['block_hold_trade_count'])} "
        f"size_down={int(row['size_down_trade_count'])} "
        f"delay={int(row['delay_entry_trade_count'])}"
    )


if __name__ == "__main__":
    main()
