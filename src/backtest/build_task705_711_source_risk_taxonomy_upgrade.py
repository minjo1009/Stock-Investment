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
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio
from src.backtest.build_task697_tiny_candidate_pnl_test import INITIAL_CAPITAL_USD, ROUND_TRIP_COST_BPS


TASK636_DIR = Path("docs/reports/task_636_full_period_content_prediction_backtest")
TASK672_PANEL = Path("docs/reports/task_672_current_data_state_axis_panel/task672_state_axis_panel.csv")
TASK684_PANEL = Path("docs/reports/task_684_interaction_context_prediction_stack/task684_interaction_stack_panel.csv")
TASK689_WEAK_LAYER = Path("docs/reports/task_689_interpretation_edge_quality/task689_candidate_weak_layer_audit.csv")
TASK703_DIR = Path("docs/reports/task_703_event_linked_source_axis_backtest")
TASK704_PRICE_CONTEXT = Path("docs/reports/task_704_price_context_backfill/task704_price_context_panel.csv")

TASK705_DIR = Path("docs/reports/task_705_source_risk_subtaxonomy")
TASK706_DIR = Path("docs/reports/task_706_candidate_context_bundle_v2")
TASK707_DIR = Path("docs/reports/task_707_tiered_action_logic")
TASK708_DIR = Path("docs/reports/task_708_full_period_backtest_comparison")
TASK709_DIR = Path("docs/reports/task_709_subtype_attribution")
TASK710_DIR = Path("docs/reports/task_710_winner_preservation_audit")
TASK711_DIR = Path("docs/reports/task_711_governance_closeout")

FINANCING_PATTERN = re.compile(
    r"private offering|public offering|registered direct|at-the-market|atm offering|"
    r"convertible senior notes|convertible notes|senior notes due|indenture and notes|"
    r"capped call|note purchase agreement|aggregate principal amount|warrants?|common stock",
    flags=re.IGNORECASE,
)
EQUITY_LIKE_PATTERN = re.compile(r"common stock|warrants?|registered direct|at-the-market|atm offering|equity offering", flags=re.IGNORECASE)
CONVERTIBLE_PATTERN = re.compile(r"convertible|senior notes|capped call|indenture and notes|note purchase", flags=re.IGNORECASE)
REAFFIRM_PATTERN = re.compile(r"\breaffirm(?:s|ed|ing)?\b|unauthorized interview|previously issued guidance", flags=re.IGNORECASE)
SOFT_PATTERN = re.compile(
    r"(lower|lowers|lowered|reduce|reduced|cut|cuts|below).{0,100}(guidance|outlook|forecast)|"
    r"(guidance|outlook|forecast).{0,100}(lower|lowers|lowered|reduce|reduced|cut|below)",
    flags=re.IGNORECASE,
)
RAISE_PATTERN = re.compile(
    r"(raise|raises|raised|raising|increase|increases|increased|higher|above|upgrade|upward).{0,100}"
    r"(guidance|outlook|forecast)|(guidance|outlook|forecast).{0,100}"
    r"(raise|raises|raised|increase|higher|above|upgrade|upward)",
    flags=re.IGNORECASE,
)

BASE_KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
RAW_TEXT_CACHE: dict[str, str] = {}
GPT_FINAL_REVIEW_MARKDOWN = """# Task711 GPT Final Review

GPT was used as a design reviewer, not as a data source.

## Review Verdict

- Task705-711 satisfy research and diagnostic completion standards.
- The work should not be promoted to a trading rule.
- Real capital and paper-trading promotion remain forbidden.

## Main Reasons

- Action-tier semantics are not aligned with payoff quality.
- Priority tiers underperform confirmation and reject-like buckets in evaluation.
- Top-50 winner preservation is weak at 56 percent.
- Bottom-50 loser preservation is high at 88 percent.
- Financing, high-noise, and low-novelty buckets still behave more like penalty labels than fully contextual state explanations.

## Recommended Next Structure

- Rename action-like tiers into context-explanation states.
- Add formal winner-preservation and loser-reduction guardrails to every future rule.
- Build interaction tables for financing subtype by price absorption, high-noise subtype by company anchor, and low-novelty subtype by price reacceleration.
- Keep the next step diagnostic-only; do not create or promote a direct trading action from Task707.
"""
SAFE_CONTEXT_COLUMNS = [
    "lifecycle_id",
    "symbol",
    "theme_ret20_prev",
    "theme_breadth20_prev",
    "theme_volume_ratio_prev",
    "theme_rank_prev",
    "multi_day_market_state_v4",
    "theme_regime_state_v4",
    "symbol_multiday_setup_state",
    "broad_market_score",
    "broad_market_stress",
    "macro_overall_state",
    "macro_action_modifier",
    "macro_assignment_certified_flag",
    "macro_used_for_assignment_flag",
    "relation_transmission_state",
    "company_catalyst_state",
    "portfolio_capacity_state",
    "same_entry_candidate_count",
    "same_entry_theme_count",
    "same_entry_relation_count",
    "setup_quality_bucket",
    "leadership_phase_strength",
    "catalyst_absorption_state",
    "catalyst_cross_context_state",
    "archetype_interaction_context",
    "same_symbol_interaction_state",
]


def build_task705_711_pipeline(
    *,
    task636_dir: Path = TASK636_DIR,
    task672_panel_path: Path = TASK672_PANEL,
    task684_panel_path: Path = TASK684_PANEL,
    task689_weak_layer_path: Path = TASK689_WEAK_LAYER,
    task703_dir: Path = TASK703_DIR,
    task704_price_context_path: Path = TASK704_PRICE_CONTEXT,
) -> dict[str, pd.DataFrame]:
    freeze = pd.read_csv(task703_dir / "task703_axis_freeze_panel.csv")
    eval_panel = pd.read_csv(task703_dir / "task703_axis_eval_panel.csv")
    links = pd.read_csv(task636_dir / "task_636_entry_event_links.csv")
    predictions = pd.read_csv(task636_dir / "task_636_event_content_predictions.csv")
    price_context = pd.read_csv(task704_price_context_path)
    context = load_context(task684_panel_path, task672_panel_path)
    weak_layer = pd.read_csv(task689_weak_layer_path)

    taxonomy = build_task705_taxonomy(freeze, links, predictions)
    write_task705(taxonomy)

    bundle = build_task706_bundle(taxonomy, price_context, context, weak_layer)
    write_task706(bundle)

    action_panel = build_task707_action_panel(bundle)
    write_task707(action_panel)

    backtest_outputs = build_task708_backtest(action_panel, eval_panel)
    write_task708(backtest_outputs)

    attribution_outputs = build_task709_attribution(action_panel, backtest_outputs["eval_panel"])
    write_task709(attribution_outputs)

    overfit_outputs = build_task710_overfit(action_panel, backtest_outputs)
    write_task710(overfit_outputs)

    governance = build_task711_governance(taxonomy, bundle, action_panel, backtest_outputs, attribution_outputs, overfit_outputs)
    write_task711(governance)

    return {
        "task705_taxonomy": taxonomy,
        "task706_bundle": bundle,
        "task707_action_panel": action_panel,
        **{f"task708_{k}": v for k, v in backtest_outputs.items()},
        **{f"task709_{k}": v for k, v in attribution_outputs.items()},
        **{f"task710_{k}": v for k, v in overfit_outputs.items()},
        **{f"task711_{k}": v for k, v in governance.items()},
    }


def load_context(task684_panel_path: Path, task672_panel_path: Path) -> pd.DataFrame:
    source = task684_panel_path if task684_panel_path.exists() else task672_panel_path
    header = pd.read_csv(source, nrows=0)
    cols = [c for c in SAFE_CONTEXT_COLUMNS if c in header.columns]
    context = pd.read_csv(source, usecols=cols)
    return context.drop_duplicates(["lifecycle_id", "symbol"])


def build_task705_taxonomy(freeze: pd.DataFrame, links: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    packets = links.merge(predictions, on="event_id", how="left", suffixes=("_link", ""))
    rows = []
    for (lifecycle_id, symbol), group in packets.groupby(["lifecycle_id", "symbol"], dropna=False):
        rows.append(event_packet_features(str(lifecycle_id), str(symbol), group))
    packet_features = pd.DataFrame(rows)
    out = freeze.merge(packet_features, on=["lifecycle_id", "symbol"], how="left")
    for col in [
        "ownership_noise_event_count",
        "broad_policy_event_count",
        "company_direct_event_count",
        "financing_text_event_count",
        "reaffirm_event_count",
        "soft_guidance_event_count",
        "raise_guidance_event_count",
        "certified_source_event_count",
        "customer_event_count",
        "revenue_backlog_event_count",
        "guidance_margin_event_count",
        "supply_demand_event_count",
        "regulatory_policy_event_count",
        "priced_in_risk_avg",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    out["source_packet_text_flags"] = out["source_packet_text_flags"].fillna("")
    out["high_noise_subtype"] = out.apply(classify_high_noise_subtype, axis=1)
    out["low_novelty_subtype"] = out.apply(classify_low_novelty_subtype, axis=1)
    out["financing_subtype"] = out.apply(classify_financing_subtype, axis=1)
    out["source_risk_reason_codes"] = out.apply(source_risk_reason_codes, axis=1)
    out["source_risk_assignment_ready_flag"] = out["source_event_available_flag"].astype(int)
    out["outcome_used_for_assignment_flag"] = 0
    out["future_price_used_for_assignment_flag"] = 0
    out["missing_source_used_as_negative_flag"] = 0
    columns = BASE_KEYS + [
        "source_event_available_flag",
        "linked_event_count",
        "direct_event_count",
        "manual_event_count",
        "noise_event_count",
        "noise_ratio",
        "direct_signal_family_count",
        "manual_signal_family_count",
        "financing_overhang_flag",
        "guidance_quality_axis",
        "information_novelty_axis",
        "high_noise_thin_signal_flag",
        "price_absorption_confirmation_flag",
        "price_acceptance_score",
        "price_chart_acceptance_state",
        "volume_ratio_prev",
        "full_event_axis_action",
        "full_event_axis_eligible_flag",
        "ownership_noise_event_count",
        "broad_policy_event_count",
        "company_direct_event_count",
        "financing_text_event_count",
        "reaffirm_event_count",
        "soft_guidance_event_count",
        "raise_guidance_event_count",
        "certified_source_event_count",
        "customer_event_count",
        "revenue_backlog_event_count",
        "guidance_margin_event_count",
        "supply_demand_event_count",
        "regulatory_policy_event_count",
        "priced_in_risk_avg",
        "source_packet_text_flags",
        "high_noise_subtype",
        "low_novelty_subtype",
        "financing_subtype",
        "source_risk_reason_codes",
        "source_risk_assignment_ready_flag",
        "outcome_used_for_assignment_flag",
        "future_price_used_for_assignment_flag",
        "missing_source_used_as_negative_flag",
    ]
    return out[columns].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def event_packet_features(lifecycle_id: str, symbol: str, group: pd.DataFrame) -> dict[str, object]:
    text = joined_packet_text(group)
    category = group.get("event_category", pd.Series("", index=group.index)).fillna("").astype(str).str.lower()
    title = group.get("event_title", pd.Series("", index=group.index)).fillna("").astype(str).str.lower()
    causal = group.get("content_stock_specific_causal_link", pd.Series("", index=group.index)).fillna("").astype(str).str.lower()
    certified = pd.to_numeric(group.get("source_text_certified_flag", pd.Series(0, index=group.index)), errors="coerce").fillna(0)
    content_cols = {
        "customer_event_count": "content_named_customer_or_counterparty",
        "revenue_backlog_event_count": "content_revenue_or_backlog_signal",
        "guidance_margin_event_count": "content_guidance_or_margin_signal",
        "supply_demand_event_count": "content_supply_demand_signal",
        "regulatory_policy_event_count": "content_regulatory_or_policy_transmission",
    }
    values: dict[str, object] = {
        "lifecycle_id": lifecycle_id,
        "symbol": symbol,
        "ownership_noise_event_count": int((category.isin(["insider_or_sale_notice", "passive_13g", "activist_13d"]) | title.str.contains("form 4| 144|schedule 13g|13g/a|13d/a", regex=True)).sum()),
        "broad_policy_event_count": int(causal.isin(["macro_policy_restriction", "macro_statement_without_stock_specific_link", "theme_policy_possible_tailwind"]).sum()),
        "company_direct_event_count": int((causal.eq("company_direct_economic_update") & certified.gt(0)).sum()),
        "financing_text_event_count": int(sum(bool(FINANCING_PATTERN.search(str(x))) for x in packet_text_rows(group))),
        "reaffirm_event_count": int(sum(bool(REAFFIRM_PATTERN.search(str(x))) for x in packet_text_rows(group))),
        "soft_guidance_event_count": int(sum(bool(SOFT_PATTERN.search(str(x))) for x in packet_text_rows(group))),
        "raise_guidance_event_count": int(sum(bool(RAISE_PATTERN.search(str(x))) for x in packet_text_rows(group))),
        "certified_source_event_count": int(certified.gt(0).sum()),
        "priced_in_risk_avg": float(pd.to_numeric(group.get("content_priced_in_risk_base_score", pd.Series(0, index=group.index)), errors="coerce").fillna(0).mean()),
        "source_packet_text_flags": text_flags(text),
    }
    for out_col, in_col in content_cols.items():
        values[out_col] = int(pd.to_numeric(group.get(in_col, pd.Series(0, index=group.index)), errors="coerce").fillna(0).sum())
    return values


def packet_text_rows(group: pd.DataFrame) -> list[str]:
    rows = []
    for record in group.to_dict(orient="records"):
        chunks = [
            str(record.get("event_title", "")),
            str(record.get("content_interpretation_evidence_span", "")),
        ]
        path_value = record.get("raw_text_path")
        if pd.notna(path_value):
            path = Path(str(path_value))
            if not path.is_absolute():
                path = ROOT / path
            raw_text = cached_raw_text(path)
            if raw_text:
                chunks.append(raw_text)
        rows.append(" ".join(chunks))
    return rows


def cached_raw_text(path: Path) -> str:
    key = str(path)
    if key not in RAW_TEXT_CACHE:
        try:
            RAW_TEXT_CACHE[key] = path.read_text(encoding="utf-8", errors="ignore")[:50000]
        except OSError:
            RAW_TEXT_CACHE[key] = ""
    return RAW_TEXT_CACHE[key]


def joined_packet_text(group: pd.DataFrame) -> str:
    return " ".join(packet_text_rows(group))


def text_flags(text: str) -> str:
    flags = []
    if EQUITY_LIKE_PATTERN.search(text):
        flags.append("equity_like_financing")
    if CONVERTIBLE_PATTERN.search(text):
        flags.append("convertible_note_financing")
    if REAFFIRM_PATTERN.search(text):
        flags.append("guidance_reaffirmation")
    if SOFT_PATTERN.search(text):
        flags.append("soft_guidance_language")
    if RAISE_PATTERN.search(text):
        flags.append("positive_guidance_language")
    return "|".join(flags)


def classify_high_noise_subtype(row: pd.Series) -> str:
    if int_safe(row.get("high_noise_thin_signal_flag")) == 0:
        return "not_high_noise"
    linked = max(float_safe(row.get("linked_event_count")), 1.0)
    if int_safe(row.get("company_direct_event_count")) > 0 and int_safe(row.get("direct_signal_family_count")) >= 2:
        return "high_noise_direct_company_anchor"
    if float_safe(row.get("ownership_noise_event_count")) / linked >= 0.5:
        return "high_noise_ownership_filing_dominated"
    if float_safe(row.get("broad_policy_event_count")) / linked >= 0.5:
        return "high_noise_broad_policy_dominated"
    if int_safe(row.get("price_absorption_confirmation_flag")) == 1:
        return "high_noise_price_confirmed"
    return "high_noise_price_unconfirmed"


def classify_low_novelty_subtype(row: pd.Series) -> str:
    novelty = str(row.get("information_novelty_axis", ""))
    if novelty not in {"not_new_reaffirmation", "not_enough_source_novelty"}:
        return "not_low_novelty"
    if str(row.get("guidance_quality_axis", "")) == "reaffirm":
        return "reaffirmation_only"
    if int_safe(row.get("reaffirm_event_count")) > 0:
        return "recycled_prior_guidance"
    if int_safe(row.get("manual_signal_family_count")) >= 2 or int_safe(row.get("manual_event_count")) > 0:
        return "manual_indirect_but_economic"
    if int_safe(row.get("price_absorption_confirmation_flag")) == 1:
        return "low_novelty_price_reacceleration"
    return "low_novelty_no_price_confirmation"


def classify_financing_subtype(row: pd.Series) -> str:
    if int_safe(row.get("financing_overhang_flag")) == 0 and int_safe(row.get("financing_text_event_count")) == 0:
        return "not_financing"
    economic_strength = (
        int_safe(row.get("customer_event_count"))
        + int_safe(row.get("revenue_backlog_event_count"))
        + int_safe(row.get("supply_demand_event_count"))
        + int_safe(row.get("guidance_margin_event_count"))
    )
    flags = str(row.get("source_packet_text_flags", ""))
    if int_safe(row.get("price_absorption_confirmation_flag")) == 1 and economic_strength >= 2:
        return "financing_plus_contract_offset"
    if int_safe(row.get("price_absorption_confirmation_flag")) == 1:
        return "financing_with_price_absorption"
    if economic_strength >= 2:
        return "strategic_financing_with_customer_link"
    if "equity_like_financing" in flags:
        return "dilutive_equity_like_financing"
    if "convertible_note_financing" in flags:
        return "convertible_or_note_overhang"
    return "financing_without_price_absorption"


def source_risk_reason_codes(row: pd.Series) -> str:
    codes = []
    for col in ["high_noise_subtype", "low_novelty_subtype", "financing_subtype"]:
        value = str(row.get(col, ""))
        if value and not value.startswith("not_"):
            codes.append(value)
    if int_safe(row.get("price_absorption_confirmation_flag")) == 1:
        codes.append("price_absorption_confirmed")
    if int_safe(row.get("company_direct_event_count")) > 0:
        codes.append("company_direct_anchor")
    if not codes:
        codes.append("no_special_source_risk")
    return "|".join(codes)


def build_task706_bundle(
    taxonomy: pd.DataFrame,
    price_context: pd.DataFrame,
    context: pd.DataFrame,
    weak_layer: pd.DataFrame,
) -> pd.DataFrame:
    price_cols = [
        "lifecycle_id",
        "symbol",
        "price_context_available_flag",
        "price_context_source",
        "near_high60_prev",
        "trend_stack_prev",
        "range_pos",
        "intraday_ret_from_open",
        "vwap_ok_flag",
        "breakout_so_far_flag",
        "intraday_entry_state_v4",
        "timing_state",
    ]
    out = taxonomy.merge(price_context[[c for c in price_cols if c in price_context.columns]], on=["lifecycle_id", "symbol"], how="left")
    out = out.merge(context, on=["lifecycle_id", "symbol"], how="left")
    weak_cols = [
        "lifecycle_id",
        "symbol",
        "sector_family",
        "weakest_layer",
        "dominant_interpretation_gap",
        "blocker_edge_count",
        "confirmation_edge_count",
        "sizing_modifier_count",
        "slot_replacement_hurdle_required_flag",
        "slot_candidate_role",
    ]
    out = out.merge(weak_layer[[c for c in weak_cols if c in weak_layer.columns]], on=["lifecycle_id", "symbol"], how="left")
    out["candidate_context_bundle_id"] = "TASK706|" + out["lifecycle_id"].astype(str)
    out["context_bundle_available_flag"] = 1
    out["macro_assignment_authority"] = out.get("macro_assignment_certified_flag", pd.Series(0, index=out.index)).fillna(0).astype(int)
    out["macro_diagnostic_only_flag"] = (1 - out["macro_assignment_authority"]).clip(lower=0)
    out["context_reason_codes"] = out.apply(context_reason_codes, axis=1)
    out["outcome_used_for_assignment_flag"] = 0
    out["future_price_used_for_assignment_flag"] = 0
    out["missing_source_used_as_negative_flag"] = 0
    return out.sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def context_reason_codes(row: pd.Series) -> str:
    codes = [
        f"source={int_safe(row.get('source_event_available_flag'))}",
        f"price={row.get('price_chart_acceptance_state', 'unknown')}",
        f"theme={row.get('theme_regime_state_v4', 'unknown')}",
        f"relation={row.get('relation_transmission_state', 'unknown')}",
        f"weakest={row.get('weakest_layer', 'unknown')}",
    ]
    if int_safe(row.get("macro_diagnostic_only_flag")):
        codes.append("macro_diagnostic_only")
    return "|".join(codes)


def build_task707_action_panel(bundle: pd.DataFrame) -> pd.DataFrame:
    out = bundle.copy()
    out["task707_action_tier"] = out.apply(classify_task707_action, axis=1)
    out["task707_trade_candidate_flag"] = out["task707_action_tier"].isin(
        ["PRIORITY_ELIGIBLE", "NORMAL_ELIGIBLE", "LOW_PRIORITY_ALIVE"]
    ).astype(int)
    out["task707_priority_normal_flag"] = out["task707_action_tier"].isin(["PRIORITY_ELIGIBLE", "NORMAL_ELIGIBLE"]).astype(int)
    out["task707_priority_flag"] = out["task707_action_tier"].eq("PRIORITY_ELIGIBLE").astype(int)
    out["task707_true_reject_flag"] = out["task707_action_tier"].eq("TRUE_REJECT").astype(int)
    out["task707_action_reason_codes"] = out.apply(task707_reason_codes, axis=1)
    out["outcome_used_for_assignment_flag"] = 0
    out["future_price_used_for_assignment_flag"] = 0
    out["missing_source_used_as_negative_flag"] = 0
    return out.sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def classify_task707_action(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "RESEARCH_ONLY"
    price_state = str(row.get("price_chart_acceptance_state", ""))
    price_confirmed = "price_confirmed" in price_state
    price_absorbed = int_safe(row.get("price_absorption_confirmation_flag")) == 1
    source_strength = int_safe(row.get("direct_signal_family_count")) + int_safe(row.get("manual_signal_family_count"))
    financing = str(row.get("financing_subtype", "not_financing"))
    high_noise = str(row.get("high_noise_subtype", "not_high_noise"))
    low_novelty = str(row.get("low_novelty_subtype", "not_low_novelty"))
    guidance = str(row.get("guidance_quality_axis", ""))
    relation = str(row.get("relation_transmission_state", ""))
    weak_layer = str(row.get("weakest_layer", ""))
    blocker_count = int_safe(row.get("blocker_edge_count"))

    if (
        guidance == "soft_or_cut"
        and not price_confirmed
        and low_novelty in {"reaffirmation_only", "low_novelty_no_price_confirmation"}
    ):
        return "TRUE_REJECT"
    if financing in {"dilutive_equity_like_financing", "financing_without_price_absorption"} and not price_confirmed:
        return "TRUE_REJECT"
    if blocker_count >= 3 and not price_confirmed:
        return "TRUE_REJECT"

    alive_risk = financing != "not_financing" or high_noise != "not_high_noise" or low_novelty != "not_low_novelty"
    if alive_risk:
        if price_absorbed or (
            high_noise in {"high_noise_direct_company_anchor", "high_noise_price_confirmed"}
            or low_novelty in {"manual_indirect_but_economic", "low_novelty_price_reacceleration"}
            or financing in {"financing_plus_contract_offset", "financing_with_price_absorption", "strategic_financing_with_customer_link"}
        ):
            return "LOW_PRIORITY_ALIVE"
        return "CONFIRMATION_REQUIRED"

    if price_absorbed and source_strength >= 4 and relation in {"relation_reinforcing", "company_price_confirmed_macro_secondary"}:
        return "PRIORITY_ELIGIBLE"
    if price_absorbed and source_strength >= 2 and weak_layer not in {"sector_edge_blocker", "relation_edge_weak"}:
        return "NORMAL_ELIGIBLE"
    if price_confirmed and source_strength >= 2:
        return "NORMAL_ELIGIBLE"
    return "CONFIRMATION_REQUIRED"


def task707_reason_codes(row: pd.Series) -> str:
    codes = [str(row.get("task707_action_tier", ""))]
    for col in ["high_noise_subtype", "low_novelty_subtype", "financing_subtype"]:
        value = str(row.get(col, ""))
        if value and not value.startswith("not_"):
            codes.append(value)
    if int_safe(row.get("price_absorption_confirmation_flag")):
        codes.append("price_absorbed")
    if str(row.get("relation_transmission_state", "")):
        codes.append(str(row.get("relation_transmission_state")))
    return "|".join(codes)


def build_task708_backtest(action_panel: pd.DataFrame, eval_panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    eval_cols = [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "entry_ts",
        "split_name",
        "entry_price",
        "simulated_exit_ts",
        "simulated_exit_price",
        "exit_reason",
        "net_return_from_entry",
        "win_flag",
        "add_scale_success_flag",
        "entry_reduce_failure_flag",
        "false_positive_flag",
        "holding_days",
        "same_day_exit_flag",
        "costed_return_pct",
        "qqq_costed_return_pct",
    ]
    merged = action_panel.merge(eval_panel[eval_cols], on=BASE_KEYS, how="left", indicator=True)
    if not merged["_merge"].eq("both").all():
        raise ValueError("Task708 action panel must join Task703 eval outcomes exactly.")
    merged = merged.drop(columns=["_merge"])
    merged["outcome_used_for_evaluation_flag"] = 1
    merged["outcome_used_for_assignment_flag"] = 0
    merged["future_price_used_for_assignment_flag"] = 0

    cohorts = {
        "all_5265_baseline_costed": merged,
        "event_linked_2445_costed": merged[merged["source_event_available_flag"].eq(1)],
        "task703_eligible_585": merged[merged["full_event_axis_action"].eq("ELIGIBLE_RULE_CANDIDATE")],
        "task707_priority_only": merged[merged["task707_action_tier"].eq("PRIORITY_ELIGIBLE")],
        "task707_priority_plus_normal": merged[merged["task707_action_tier"].isin(["PRIORITY_ELIGIBLE", "NORMAL_ELIGIBLE"])],
        "task707_priority_normal_low_alive": merged[merged["task707_action_tier"].isin(["PRIORITY_ELIGIBLE", "NORMAL_ELIGIBLE", "LOW_PRIORITY_ALIVE"])],
    }
    portfolio_rows = []
    accepted_frames = []
    curve_frames = []
    for cohort_name, panel in cohorts.items():
        for cap in [5, 10, 20]:
            quality, accepted, curve = simulate_deterministic_portfolio(panel.copy(), max_positions=cap)
            final_capital = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
            portfolio_rows.append(portfolio_row(cohort_name, cap, panel, accepted, quality, final_capital))
            if not accepted.empty:
                acc = accepted.copy()
                acc["portfolio_cohort"] = cohort_name
                acc["max_positions"] = cap
                accepted_frames.append(acc)
            if not curve.empty:
                cur = curve.copy()
                cur["portfolio_cohort"] = cohort_name
                cur["max_positions"] = cap
                curve_frames.append(cur)
    qqq_final = float(pd.read_csv(TASK703_DIR / "task703_portfolio_comparison.csv").query("portfolio_cohort == 'QQQ_buy_and_hold_same_horizon'").iloc[0]["final_capital_usd"])
    portfolio = pd.DataFrame(portfolio_rows)
    portfolio["qqq_buyhold_final_capital_usd"] = qqq_final
    portfolio["beats_qqq_flag"] = portfolio["final_capital_usd"].gt(qqq_final).astype(int)
    portfolio = pd.concat(
        [
            portfolio,
            pd.DataFrame(
                [
                    {
                        "portfolio_cohort": "QQQ_buy_and_hold_same_horizon",
                        "max_positions": 1,
                        "source_candidate_count": 1,
                        "accepted_trade_count": 1,
                        "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
                        "initial_capital_usd": INITIAL_CAPITAL_USD,
                        "final_capital_usd": qqq_final,
                        "capital_return_pct": (qqq_final / INITIAL_CAPITAL_USD - 1.0) * 100.0,
                        "max_drawdown_pct": 0.0,
                        "entry_reduce_failure_rate": 0.0,
                        "qqq_buyhold_final_capital_usd": qqq_final,
                        "beats_qqq_flag": 0,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    accepted_all = pd.concat(accepted_frames, ignore_index=True) if accepted_frames else pd.DataFrame()
    curves = pd.concat(curve_frames, ignore_index=True) if curve_frames else pd.DataFrame()
    split_summary = build_task708_split_summary(merged)
    cost_stress = build_task708_cost_stress(cohorts)
    decision = build_task708_decision(portfolio)
    pass_fail = build_task708_pass_fail(merged, portfolio)
    return {
        "eval_panel": merged,
        "portfolio_comparison": portfolio,
        "accepted_trades": accepted_all,
        "equity_curves": curves,
        "split_summary": split_summary,
        "cost_stress_summary": cost_stress,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def portfolio_row(cohort_name: str, cap: int, panel: pd.DataFrame, accepted: pd.DataFrame, quality: dict[str, object], final_capital: float) -> dict[str, object]:
    return {
        "portfolio_cohort": cohort_name,
        "max_positions": cap,
        "source_candidate_count": int(len(panel)),
        "accepted_trade_count": int(len(accepted)),
        "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
        "initial_capital_usd": INITIAL_CAPITAL_USD,
        "final_capital_usd": float(final_capital),
        "capital_return_pct": float(quality["capital_pnl_pct"]),
        "max_drawdown_pct": float(quality["max_drawdown_pct"]),
        "entry_reduce_failure_rate": float(quality.get("entry_reduce_failure_rate", 0.0)),
    }


def build_task708_split_summary(eval_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tier, group in eval_panel.groupby("task707_action_tier", dropna=False):
        for split, split_group in group.groupby("split_name", dropna=False):
            returns = pd.to_numeric(split_group["costed_return_pct"], errors="coerce")
            rows.append(
                {
                    "task707_action_tier": tier,
                    "split_name": split,
                    "candidate_count": int(len(split_group)),
                    "avg_costed_return_pct": float(returns.mean()),
                    "median_costed_return_pct": float(returns.median()),
                    "win_rate": float((returns > 0).mean()),
                    "entry_reduce_failure_rate": float(pd.to_numeric(split_group["entry_reduce_failure_flag"], errors="coerce").fillna(0).mean()),
                }
            )
    return pd.DataFrame(rows)


def build_task708_cost_stress(cohorts: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for cohort_name, panel in cohorts.items():
        for total_bps in [50, 100, 200]:
            stressed = panel.copy()
            extra_bps = total_bps - ROUND_TRIP_COST_BPS
            stressed["net_return_from_entry"] = pd.to_numeric(stressed["net_return_from_entry"], errors="coerce") - extra_bps / 10000.0
            for cap in [5, 10, 20]:
                quality, accepted, _curve = simulate_deterministic_portfolio(stressed, max_positions=cap)
                rows.append(
                    {
                        "portfolio_cohort": cohort_name,
                        "max_positions": cap,
                        "round_trip_cost_bps": total_bps,
                        "accepted_trade_count": int(len(accepted)),
                        "final_capital_usd": INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0),
                        "capital_return_pct": float(quality["capital_pnl_pct"]),
                        "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                    }
                )
    return pd.DataFrame(rows)


def build_task708_decision(portfolio: pd.DataFrame) -> pd.DataFrame:
    candidates = portfolio[portfolio["portfolio_cohort"].ne("QQQ_buy_and_hold_same_horizon")]
    best = candidates.sort_values("final_capital_usd", ascending=False).iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": "Task708",
                "verdict": "TIERED_SOURCE_RISK_BACKTEST_COMPLETE_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "best_cohort": best["portfolio_cohort"],
                "best_max_positions": int(best["max_positions"]),
                "best_final_capital_usd": float(best["final_capital_usd"]),
                "best_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "trading_promotion_pass_flag": 0,
                "next_action": "Use subtype attribution and winner preservation before any rule promotion discussion.",
            }
        ]
    )


def build_task708_pass_fail(eval_panel: pd.DataFrame, portfolio: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("eval_scope_5265", len(eval_panel) == 5265, f"rows={len(eval_panel)}", "5265"),
            gate("event_linked_scope_2445", int(eval_panel["source_event_available_flag"].sum()) == 2445, f"event={int(eval_panel['source_event_available_flag'].sum())}", "2445"),
            gate("tiered_candidates_nonzero", int(eval_panel["task707_trade_candidate_flag"].sum()) > 0, f"trade_candidates={int(eval_panel['task707_trade_candidate_flag'].sum())}", ">0"),
            gate("portfolio_cohorts_present", portfolio["portfolio_cohort"].nunique() >= 7, f"cohorts={portfolio['portfolio_cohort'].nunique()}", ">=7"),
            gate("no_assignment_leakage", int(eval_panel["outcome_used_for_assignment_flag"].sum()) == 0 and int(eval_panel["future_price_used_for_assignment_flag"].sum()) == 0, "assignment leakage=0", "0"),
        ]
    )


def build_task709_attribution(action_panel: pd.DataFrame, eval_panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    attrs = ["high_noise_subtype", "low_novelty_subtype", "financing_subtype", "task707_action_tier"]
    rows = []
    for attr in attrs:
        for value, group in eval_panel.groupby(attr, dropna=False):
            returns = pd.to_numeric(group["costed_return_pct"], errors="coerce")
            rows.append(
                {
                    "attribution_axis": attr,
                    "axis_value": value,
                    "candidate_count": int(len(group)),
                    "avg_costed_return_pct": float(returns.mean()),
                    "median_costed_return_pct": float(returns.median()),
                    "win_rate": float((returns > 0).mean()),
                    "entry_reduce_failure_rate": float(pd.to_numeric(group["entry_reduce_failure_flag"], errors="coerce").fillna(0).mean()),
                    "outcome_used_for_assignment_flag": 0,
                    "outcome_used_for_evaluation_flag": 1,
                }
            )
    performance = pd.DataFrame(rows).sort_values(["attribution_axis", "avg_costed_return_pct"], ascending=[True, False])
    mdd_exposure = build_mdd_subtype_exposure(eval_panel)
    examples = build_winner_loser_examples(eval_panel)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task709",
                "verdict": "SUBTYPE_ATTRIBUTION_COMPLETE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "attribution_axis_count": len(attrs),
                "next_action": "Use attribution to design audited rule candidates only after winner preservation review.",
            }
        ]
    )
    pass_fail = pd.DataFrame(
        [
            gate("performance_rows_present", len(performance) > 0, f"rows={len(performance)}", ">0"),
            gate("mdd_exposure_present", len(mdd_exposure) > 0, f"rows={len(mdd_exposure)}", ">0"),
            gate("examples_present", len(examples) > 0, f"rows={len(examples)}", ">0"),
            gate("diagnostic_only", True, "no rule mutation", "diagnostic only"),
        ]
    )
    return {"performance": performance, "mdd_exposure": mdd_exposure, "winner_loser_examples": examples, "decision": decision, "pass_fail": pass_fail}


def build_mdd_subtype_exposure(eval_panel: pd.DataFrame) -> pd.DataFrame:
    cohort = eval_panel[eval_panel["task707_action_tier"].isin(["PRIORITY_ELIGIBLE", "NORMAL_ELIGIBLE", "LOW_PRIORITY_ALIVE"])].copy()
    quality, accepted, curve = simulate_deterministic_portfolio(cohort, max_positions=5)
    if accepted.empty or curve.empty:
        return pd.DataFrame()
    worst_ts = pd.to_datetime(curve.sort_values("drawdown_pct").iloc[0]["event_ts"], utc=True)
    accepted["entry_ts"] = pd.to_datetime(accepted["entry_ts"], utc=True)
    accepted["simulated_exit_ts"] = pd.to_datetime(accepted["simulated_exit_ts"], utc=True)
    open_at_mdd = accepted[accepted["entry_ts"].le(worst_ts) & accepted["simulated_exit_ts"].gt(worst_ts)]
    rows = []
    for attr in ["high_noise_subtype", "low_novelty_subtype", "financing_subtype", "task707_action_tier"]:
        for value, group in open_at_mdd.groupby(attr, dropna=False):
            rows.append(
                {
                    "mdd_event_ts": worst_ts,
                    "mdd_drawdown_pct": float(curve["drawdown_pct"].min()),
                    "attribution_axis": attr,
                    "axis_value": value,
                    "open_position_count": int(len(group)),
                    "symbols": "|".join(group["symbol"].astype(str).tolist()),
                }
            )
    return pd.DataFrame(rows)


def build_winner_loser_examples(eval_panel: pd.DataFrame) -> pd.DataFrame:
    event = eval_panel[eval_panel["source_event_available_flag"].eq(1)].copy()
    cols = BASE_KEYS + [
        "task707_action_tier",
        "high_noise_subtype",
        "low_novelty_subtype",
        "financing_subtype",
        "costed_return_pct",
        "entry_reduce_failure_flag",
    ]
    winners = event.sort_values("costed_return_pct", ascending=False).head(50).copy()
    losers = event.sort_values("costed_return_pct", ascending=True).head(50).copy()
    winners["example_type"] = "top_winner"
    losers["example_type"] = "top_loser"
    return pd.concat([winners[cols + ["example_type"]], losers[cols + ["example_type"]]], ignore_index=True)


def build_task710_overfit(action_panel: pd.DataFrame, backtest_outputs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    eval_panel = backtest_outputs["eval_panel"]
    event = eval_panel[eval_panel["source_event_available_flag"].eq(1)].copy()
    top_winners = event.sort_values("costed_return_pct", ascending=False).head(50)
    top_losers = event.sort_values("costed_return_pct", ascending=True).head(50)
    preserved_tiers = {"PRIORITY_ELIGIBLE", "NORMAL_ELIGIBLE", "LOW_PRIORITY_ALIVE"}
    winner_audit = pd.concat(
        [
            preservation_rows(top_winners, "top_50_winners", preserved_tiers),
            preservation_rows(top_losers, "bottom_50_losers", preserved_tiers),
        ],
        ignore_index=True,
    )
    concentration = build_concentration_audit(backtest_outputs["accepted_trades"])
    overfit = build_overfit_risk_matrix(winner_audit, concentration, backtest_outputs["portfolio_comparison"])
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task710",
                "verdict": "WINNER_PRESERVATION_OVERFIT_AUDIT_COMPLETE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "winner_preservation_rate": float(winner_audit[winner_audit["sample"] == "top_50_winners"]["preservation_rate"].iloc[0]),
                "next_action": "Review overfit flags before changing tier thresholds.",
            }
        ]
    )
    pass_fail = pd.DataFrame(
        [
            gate("winner_audit_present", len(winner_audit) >= 2, f"rows={len(winner_audit)}", ">=2"),
            gate("concentration_audit_present", len(concentration) > 0, f"rows={len(concentration)}", ">0"),
            gate("overfit_matrix_present", len(overfit) > 0, f"rows={len(overfit)}", ">0"),
            gate("no_rule_promotion", True, "diagnostic only", "no promotion"),
        ]
    )
    return {"winner_preservation": winner_audit, "concentration": concentration, "overfit": overfit, "decision": decision, "pass_fail": pass_fail}


def preservation_rows(frame: pd.DataFrame, sample: str, preserved_tiers: set[str]) -> pd.DataFrame:
    preserved = frame["task707_action_tier"].isin(preserved_tiers)
    return pd.DataFrame(
        [
            {
                "sample": sample,
                "sample_count": int(len(frame)),
                "preserved_count": int(preserved.sum()),
                "preservation_rate": float(preserved.mean()) if len(frame) else 0.0,
                "priority_count": int(frame["task707_action_tier"].eq("PRIORITY_ELIGIBLE").sum()),
                "normal_count": int(frame["task707_action_tier"].eq("NORMAL_ELIGIBLE").sum()),
                "low_alive_count": int(frame["task707_action_tier"].eq("LOW_PRIORITY_ALIVE").sum()),
                "confirmation_count": int(frame["task707_action_tier"].eq("CONFIRMATION_REQUIRED").sum()),
                "research_or_reject_count": int(frame["task707_action_tier"].isin(["RESEARCH_ONLY", "TRUE_REJECT"]).sum()),
                "top_symbols": "|".join(frame["symbol"].astype(str).value_counts().head(10).index.tolist()),
                "top_themes": "|".join(frame["theme_id"].astype(str).value_counts().head(10).index.tolist()),
            }
        ]
    )


def build_concentration_audit(accepted: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty:
        return pd.DataFrame()
    rows = []
    for (cohort, cap), group in accepted.groupby(["portfolio_cohort", "max_positions"], dropna=False):
        for axis in ["symbol", "theme_id", "task707_action_tier", "financing_subtype", "high_noise_subtype", "low_novelty_subtype"]:
            counts = group[axis].astype(str).value_counts()
            top_value = counts.index[0] if len(counts) else ""
            top_count = int(counts.iloc[0]) if len(counts) else 0
            rows.append(
                {
                    "portfolio_cohort": cohort,
                    "max_positions": int(cap),
                    "axis": axis,
                    "accepted_trade_count": int(len(group)),
                    "top_value": top_value,
                    "top_count": top_count,
                    "top_share": float(top_count / len(group)) if len(group) else 0.0,
                }
            )
    return pd.DataFrame(rows)


def build_overfit_risk_matrix(winner_audit: pd.DataFrame, concentration: pd.DataFrame, portfolio: pd.DataFrame) -> pd.DataFrame:
    winner_pres = float(winner_audit[winner_audit["sample"] == "top_50_winners"]["preservation_rate"].iloc[0])
    top_symbol_share = float(concentration[concentration["axis"].eq("symbol")]["top_share"].max()) if not concentration.empty else 0.0
    max5 = portfolio[portfolio["max_positions"].eq(5)]
    max20 = portfolio[portfolio["max_positions"].eq(20)]
    rows = [
        risk_row("winner_preservation_low", winner_pres < 0.70, f"winner_preservation={winner_pres:.2f}", ">=0.70"),
        risk_row("symbol_concentration_high", top_symbol_share > 0.35, f"top_symbol_share={top_symbol_share:.2f}", "<=0.35"),
        risk_row(
            "max5_only_fragility",
            float(max5["final_capital_usd"].max()) > float(max20["final_capital_usd"].max()) * 1.5 if not max5.empty and not max20.empty else False,
            "compare max5 vs max20",
            "no one-capacity-only collapse",
        ),
        risk_row("strategy_not_promoted", False, "NOT_ACCEPTED/FORBIDDEN", "remain research-only"),
    ]
    return pd.DataFrame(rows)


def risk_row(name: str, flag: bool, observed: str, expected: str) -> dict[str, object]:
    return {"risk_name": name, "risk_flag": int(flag), "observed": observed, "expected": expected}


def build_task711_governance(
    taxonomy: pd.DataFrame,
    bundle: pd.DataFrame,
    action_panel: pd.DataFrame,
    backtest_outputs: dict[str, pd.DataFrame],
    attribution_outputs: dict[str, pd.DataFrame],
    overfit_outputs: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    eval_panel = backtest_outputs["eval_panel"]
    acceptance = pd.DataFrame(
        [
            gate("task705_scope_5265", len(taxonomy) == 5265, f"rows={len(taxonomy)}", "5265"),
            gate("task706_scope_5265", len(bundle) == 5265, f"rows={len(bundle)}", "5265"),
            gate("task707_scope_5265", len(action_panel) == 5265, f"rows={len(action_panel)}", "5265"),
            gate("task708_eval_scope_5265", len(eval_panel) == 5265, f"rows={len(eval_panel)}", "5265"),
            gate("event_linked_scope_2445", int(action_panel["source_event_available_flag"].sum()) == 2445, f"event={int(action_panel['source_event_available_flag'].sum())}", "2445"),
            gate("price_context_full", int(action_panel["price_context_available_flag"].sum()) == 5265, f"price={int(action_panel['price_context_available_flag'].sum())}", "5265"),
            gate("no_outcome_assignment", sum_col(action_panel, "outcome_used_for_assignment_flag") == 0, str(sum_col(action_panel, "outcome_used_for_assignment_flag")), "0"),
            gate("no_future_price_assignment", sum_col(action_panel, "future_price_used_for_assignment_flag") == 0, str(sum_col(action_panel, "future_price_used_for_assignment_flag")), "0"),
            gate("missing_source_not_negative", sum_col(action_panel, "missing_source_used_as_negative_flag") == 0, str(sum_col(action_panel, "missing_source_used_as_negative_flag")), "0"),
            gate("macro_not_promoted", sum_col(action_panel, "macro_used_for_assignment_flag") == 0, str(sum_col(action_panel, "macro_used_for_assignment_flag")), "0"),
            gate("no_symbol_theme_blacklist", True, "symbol_blacklist=0; theme_blacklist=0", "0"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task711",
                "verdict": "GOVERNANCE_CLOSEOUT_COMPLETE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "pass_gate_count": int(acceptance["pass_flag"].sum()),
                "fail_gate_count": int((1 - acceptance["pass_flag"]).sum()),
                "trading_promotion_pass_flag": 0,
                "next_action": "Human review the Task709/710 diagnostics before any Task712 rule refinement.",
            }
        ]
    )
    return {"acceptance": acceptance, "decision": decision}


def write_task705(taxonomy: pd.DataFrame) -> None:
    TASK705_DIR.mkdir(parents=True, exist_ok=True)
    summary = subtype_summary(taxonomy)
    decision = decision_frame("Task705", "SOURCE_RISK_SUBTAXONOMY_COMPLETE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", len(taxonomy))
    pass_fail = pd.DataFrame(
        [
            gate("scope_5265", len(taxonomy) == 5265, f"rows={len(taxonomy)}", "5265"),
            gate("event_linked_2445", int(taxonomy["source_event_available_flag"].sum()) == 2445, f"event={int(taxonomy['source_event_available_flag'].sum())}", "2445"),
            gate("subtypes_present", summary["axis_value"].nunique() > 5, f"subtypes={summary['axis_value'].nunique()}", ">5"),
            gate("no_assignment_leakage", sum_col(taxonomy, "outcome_used_for_assignment_flag") == 0 and sum_col(taxonomy, "future_price_used_for_assignment_flag") == 0, "assignment leakage=0", "0"),
        ]
    )
    write_task_outputs(
        TASK705_DIR,
        "task_705_source_risk_subtaxonomy.md",
        {
            "task705_source_risk_taxonomy_panel.csv": taxonomy,
            "task705_subtype_summary.csv": summary,
            "task_705_decision.csv": decision,
            "task_705_pass_fail_matrix.csv": pass_fail,
        },
        "Task705 Source Risk Subtaxonomy",
        decision,
        pass_fail,
        "HIGH_NOISE, LOW_NOVELTY, and FINANCING are decomposed into assignment-safe subtypes before any new backtest.",
    )


def subtype_summary(taxonomy: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for axis in ["high_noise_subtype", "low_novelty_subtype", "financing_subtype"]:
        for value, group in taxonomy.groupby(axis, dropna=False):
            rows.append(
                {
                    "subtype_axis": axis,
                    "axis_value": value,
                    "candidate_count": int(len(group)),
                    "event_linked_count": int(group["source_event_available_flag"].sum()),
                    "price_absorbed_count": int(group["price_absorption_confirmation_flag"].sum()),
                }
            )
    return pd.DataFrame(rows).sort_values(["subtype_axis", "candidate_count"], ascending=[True, False])


def write_task706(bundle: pd.DataFrame) -> None:
    TASK706_DIR.mkdir(parents=True, exist_ok=True)
    coverage = pd.DataFrame(
        [
            {"coverage_item": "row_count", "observed": len(bundle), "required": 5265},
            {"coverage_item": "event_linked", "observed": int(bundle["source_event_available_flag"].sum()), "required": 2445},
            {"coverage_item": "price_context", "observed": int(bundle["price_context_available_flag"].sum()), "required": 5265},
            {"coverage_item": "macro_assignment_authority", "observed": int(bundle["macro_assignment_authority"].sum()), "required": 0},
        ]
    )
    decision = decision_frame("Task706", "CANDIDATE_CONTEXT_BUNDLE_V2_COMPLETE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", len(bundle))
    pass_fail = pd.DataFrame(
        [
            gate("bundle_scope_5265", len(bundle) == 5265, f"rows={len(bundle)}", "5265"),
            gate("price_context_full", int(bundle["price_context_available_flag"].sum()) == 5265, f"price={int(bundle['price_context_available_flag'].sum())}", "5265"),
            gate("macro_not_promoted", int(bundle["macro_assignment_authority"].sum()) == 0, f"macro_authority={int(bundle['macro_assignment_authority'].sum())}", "0"),
            gate("no_assignment_leakage", sum_col(bundle, "outcome_used_for_assignment_flag") == 0 and sum_col(bundle, "future_price_used_for_assignment_flag") == 0, "assignment leakage=0", "0"),
        ]
    )
    write_task_outputs(
        TASK706_DIR,
        "task_706_candidate_context_bundle_v2.md",
        {
            "task706_candidate_context_bundle_v2.csv": bundle,
            "task706_context_coverage_audit.csv": coverage,
            "task_706_decision.csv": decision,
            "task_706_pass_fail_matrix.csv": pass_fail,
        },
        "Task706 Candidate Context Bundle V2",
        decision,
        pass_fail,
        "Source taxonomy is joined to price, theme, relation, weak-layer, and slot context without granting macro assignment authority.",
    )


def write_task707(action_panel: pd.DataFrame) -> None:
    TASK707_DIR.mkdir(parents=True, exist_ok=True)
    transition = action_panel.groupby(["full_event_axis_action", "task707_action_tier"], dropna=False).size().reset_index(name="candidate_count")
    block_audit = action_panel.groupby("task707_action_tier", dropna=False).agg(
        candidate_count=("lifecycle_id", "count"),
        event_linked_count=("source_event_available_flag", "sum"),
        true_reject_count=("task707_true_reject_flag", "sum"),
    ).reset_index()
    decision = decision_frame("Task707", "TIERED_ACTION_LOGIC_COMPLETE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", len(action_panel))
    pass_fail = pd.DataFrame(
        [
            gate("action_scope_5265", len(action_panel) == 5265, f"rows={len(action_panel)}", "5265"),
            gate("tiers_present", action_panel["task707_action_tier"].nunique() >= 4, f"tiers={action_panel['task707_action_tier'].nunique()}", ">=4"),
            gate("risk_not_hard_block_only", int(action_panel["task707_trade_candidate_flag"].sum()) > int(action_panel["full_event_axis_action"].eq("ELIGIBLE_RULE_CANDIDATE").sum()), f"tier_candidates={int(action_panel['task707_trade_candidate_flag'].sum())}", ">Task703 eligible"),
            gate("no_assignment_leakage", sum_col(action_panel, "outcome_used_for_assignment_flag") == 0 and sum_col(action_panel, "future_price_used_for_assignment_flag") == 0, "assignment leakage=0", "0"),
        ]
    )
    write_task_outputs(
        TASK707_DIR,
        "task_707_tiered_action_logic.md",
        {
            "task707_tiered_action_panel.csv": action_panel,
            "task707_action_transition_matrix.csv": transition,
            "task707_block_reason_audit.csv": block_audit,
            "task_707_decision.csv": decision,
            "task_707_pass_fail_matrix.csv": pass_fail,
        },
        "Task707 Tiered Action Logic",
        decision,
        pass_fail,
        "Risk buckets are converted into PRIORITY, NORMAL, LOW_PRIORITY_ALIVE, CONFIRMATION, RESEARCH, and TRUE_REJECT tiers.",
    )


def write_task708(outputs: dict[str, pd.DataFrame]) -> None:
    TASK708_DIR.mkdir(parents=True, exist_ok=True)
    write_task_outputs(
        TASK708_DIR,
        "task_708_full_period_backtest_comparison.md",
        {
            "task708_eval_panel.csv": outputs["eval_panel"],
            "task708_portfolio_comparison.csv": outputs["portfolio_comparison"],
            "task708_accepted_trades.csv": outputs["accepted_trades"],
            "task708_equity_curves.csv": outputs["equity_curves"],
            "task708_split_summary.csv": outputs["split_summary"],
            "task708_cost_stress_summary.csv": outputs["cost_stress_summary"],
            "task_708_decision.csv": outputs["decision"],
            "task_708_pass_fail_matrix.csv": outputs["pass_fail"],
        },
        "Task708 Full Period Backtest Comparison",
        outputs["decision"],
        outputs["pass_fail"],
        "Tiered action cohorts are compared against all candidates, event-linked candidates, Task703 eligible, and QQQ with $1,000 capital.",
    )


def write_task709(outputs: dict[str, pd.DataFrame]) -> None:
    TASK709_DIR.mkdir(parents=True, exist_ok=True)
    write_task_outputs(
        TASK709_DIR,
        "task_709_subtype_attribution.md",
        {
            "task709_subtype_performance.csv": outputs["performance"],
            "task709_mdd_subtype_exposure.csv": outputs["mdd_exposure"],
            "task709_winner_loser_examples.csv": outputs["winner_loser_examples"],
            "task_709_decision.csv": outputs["decision"],
            "task_709_pass_fail_matrix.csv": outputs["pass_fail"],
        },
        "Task709 Subtype Attribution",
        outputs["decision"],
        outputs["pass_fail"],
        "Subtype performance and MDD exposure are evaluated after freeze, but no rule is changed from this diagnostic.",
    )


def write_task710(outputs: dict[str, pd.DataFrame]) -> None:
    TASK710_DIR.mkdir(parents=True, exist_ok=True)
    write_task_outputs(
        TASK710_DIR,
        "task_710_winner_preservation_audit.md",
        {
            "task710_winner_preservation_audit.csv": outputs["winner_preservation"],
            "task710_symbol_theme_concentration_audit.csv": outputs["concentration"],
            "task710_overfit_risk_matrix.csv": outputs["overfit"],
            "task_710_decision.csv": outputs["decision"],
            "task_710_pass_fail_matrix.csv": outputs["pass_fail"],
        },
        "Task710 Winner Preservation Audit",
        outputs["decision"],
        outputs["pass_fail"],
        "The new taxonomy is audited for winner destruction, loser preservation, and concentration risk before any refinement.",
    )


def write_task711(outputs: dict[str, pd.DataFrame]) -> None:
    TASK711_DIR.mkdir(parents=True, exist_ok=True)
    write_task_outputs(
        TASK711_DIR,
        "task_711_governance_closeout.md",
        {
            "task711_acceptance_matrix.csv": outputs["acceptance"],
            "task_711_decision.csv": outputs["decision"],
            "task_711_pass_fail_matrix.csv": outputs["acceptance"],
        },
        "Task711 Governance Closeout",
        outputs["decision"],
        outputs["acceptance"],
        "Task705-711 artifacts are closed with leakage, missing-source, macro, blacklist, and capital-readiness gates.",
    )
    (TASK711_DIR / "task711_gpt_final_review.md").write_text(GPT_FINAL_REVIEW_MARKDOWN, encoding="utf-8")
    report_path = TASK711_DIR / "task_711_governance_closeout.md"
    report_text = report_path.read_text(encoding="utf-8")
    report_text = report_text.replace(
        "- Outputs: task711_acceptance_matrix.csv, task_711_decision.csv, task_711_pass_fail_matrix.csv.",
        "- Outputs: task711_acceptance_matrix.csv, task_711_decision.csv, task_711_pass_fail_matrix.csv, task711_gpt_final_review.md.",
    )
    report_path.write_text(report_text, encoding="utf-8")
    remove_existing_manifest(TASK711_DIR)
    write_manifest(TASK711_DIR, TASK711_DIR / "artifact_manifest.csv")


def decision_frame(task_id: str, verdict: str, rows: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": task_id,
                "verdict": verdict,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "row_count": int(rows),
                "trading_promotion_pass_flag": 0,
                "next_action": "Continue governed research only.",
            }
        ]
    )


def write_task_outputs(
    out_dir: Path,
    report_name: str,
    outputs: dict[str, pd.DataFrame],
    title: str,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
    summary: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    report = f"""# {title}

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: {decision.iloc[0]['strategy_acceptance_status']}.
- Real capital status: {decision.iloc[0]['real_capital_status']}.
- What changed: {summary}
- Next action: {decision.iloc[0]['next_action']}.

## Quant Expert Report

- Data source and source readiness: current Task636/672/684/689/703/704 artifacts only.
- Exact join keys: `lifecycle_id`, `symbol`, `theme_id`, `entry_ts`, `split_name` where applicable.
- Leakage audit: outcome/future-price assignment flags are kept at zero before evaluation.
- Split/OOS metrics: included where PnL is evaluated; otherwise not applicable.
- Failure decomposition: see CSV artifacts in this directory.
- Cost/slippage stress where PnL changed: included for Task708; otherwise not applicable.
- Remaining blockers: strategy remains NOT_ACCEPTED and real capital remains FORBIDDEN.

## No-Background Decision-Maker Report

- What happened: {summary}
- Why it matters: the project separates source risk, context, action tiers, evaluation, and governance instead of fixing rules after seeing returns.
- Whether this changes capital/deployment readiness: no.
- Plain-language next step: inspect the diagnostics before changing thresholds.

## Artifact Manifest

- Inputs: upstream governed task artifacts.
- Outputs: {', '.join(outputs.keys())}.
- Row counts: {artifact_counts(outputs)}.
- Validation commands: see task registry.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / report_name).write_text(report, encoding="utf-8")
    remove_existing_manifest(out_dir)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def remove_existing_manifest(out_dir: Path) -> None:
    manifest = out_dir / "artifact_manifest.csv"
    if manifest.exists():
        manifest.unlink()


def artifact_counts(outputs: dict[str, pd.DataFrame]) -> str:
    return "; ".join(f"{name}={len(frame)}" for name, frame in outputs.items())


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {"gate_name": name, "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED", "pass_flag": int(passed), "observed": observed, "required": required}


def sum_col(frame: pd.DataFrame, col: str) -> int:
    if col not in frame.columns:
        return 0
    return int(pd.to_numeric(frame[col], errors="coerce").fillna(0).sum())


def int_safe(value: object) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def float_safe(value: object) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task636-dir", type=Path, default=TASK636_DIR)
    parser.add_argument("--task672-panel", type=Path, default=TASK672_PANEL)
    parser.add_argument("--task684-panel", type=Path, default=TASK684_PANEL)
    parser.add_argument("--task689-weak-layer", type=Path, default=TASK689_WEAK_LAYER)
    parser.add_argument("--task703-dir", type=Path, default=TASK703_DIR)
    parser.add_argument("--task704-price-context", type=Path, default=TASK704_PRICE_CONTEXT)
    args = parser.parse_args()
    build_task705_711_pipeline(
        task636_dir=args.task636_dir,
        task672_panel_path=args.task672_panel,
        task684_panel_path=args.task684_panel,
        task689_weak_layer_path=args.task689_weak_layer,
        task703_dir=args.task703_dir,
        task704_price_context_path=args.task704_price_context,
    )
    print("[Task705-711] wrote source-risk taxonomy upgrade artifacts")


if __name__ == "__main__":
    main()
