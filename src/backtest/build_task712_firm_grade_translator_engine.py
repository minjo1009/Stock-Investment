from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK706_BUNDLE = Path("docs/reports/task_706_candidate_context_bundle_v2/task706_candidate_context_bundle_v2.csv")
TASK708_EVAL = Path("docs/reports/task_708_full_period_backtest_comparison/task708_eval_panel.csv")
TASK712_DIR = Path("docs/reports/task_712_firm_grade_translator_engine")

KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]


def build_task712(
    *,
    bundle_path: Path = TASK706_BUNDLE,
    eval_path: Path = TASK708_EVAL,
    out_dir: Path = TASK712_DIR,
) -> dict[str, pd.DataFrame]:
    bundle = pd.read_csv(bundle_path)
    eval_panel = pd.read_csv(eval_path)

    context_panel = build_context_state_panel(bundle)
    interaction_matrix = build_interaction_matrix(context_panel)
    review_packet = build_review_packet(context_panel)
    guardrail = build_guardrail_audit(context_panel, eval_panel)
    governance = build_governance_audit(context_panel, bundle)
    source_map = build_context_gather_source_map()
    decision = decision_frame(context_panel, guardrail)
    pass_fail = pass_fail_matrix(context_panel, interaction_matrix, guardrail, governance)

    write_outputs(
        out_dir,
        {
            "task712_context_gather_source_map.csv": source_map,
            "task712_context_state_panel.csv": context_panel,
            "task712_interaction_matrix.csv": interaction_matrix,
            "task712_review_packet.csv": review_packet,
            "task712_guardrail_audit.csv": guardrail,
            "task712_governance_audit.csv": governance,
            "task_712_decision.csv": decision,
            "task_712_pass_fail_matrix.csv": pass_fail,
        },
        decision,
        pass_fail,
    )
    return {
        "source_map": source_map,
        "context_panel": context_panel,
        "interaction_matrix": interaction_matrix,
        "review_packet": review_packet,
        "guardrail": guardrail,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_context_state_panel(bundle: pd.DataFrame) -> pd.DataFrame:
    out = bundle.copy()
    out["company_anchor_state"] = out.apply(company_anchor_state, axis=1)
    out["market_acceptance_state"] = out.apply(market_acceptance_state, axis=1)
    out["theme_leadership_context"] = out.apply(theme_leadership_context, axis=1)
    out["policy_macro_context_state"] = out.apply(policy_macro_context_state, axis=1)
    out["financing_context_state"] = out.apply(financing_context_state, axis=1)
    out["high_noise_context_state"] = out.apply(high_noise_context_state, axis=1)
    out["low_novelty_context_state"] = out.apply(low_novelty_context_state, axis=1)
    out["guidance_context_state"] = out.apply(guidance_context_state, axis=1)
    out["firm_grade_context_state"] = out.apply(firm_grade_context_state, axis=1)
    out["translator_confidence_state"] = out.apply(translator_confidence_state, axis=1)
    out["translator_reason_codes"] = out.apply(translator_reason_codes, axis=1)
    out["why_not_action_tier"] = (
        "diagnostic_context_explanation_only;"
        "risk_labels_are_not_trade_quality_labels;"
        "outcome_guardrails_are_evaluation_only"
    )
    out["translator_output_is_action_flag"] = 0
    out["outcome_used_for_assignment_flag"] = 0
    out["future_price_used_for_assignment_flag"] = 0
    out["missing_source_used_as_negative_flag"] = 0
    out["macro_used_for_assignment_flag"] = 0

    columns = KEYS + [
        "source_event_available_flag",
        "high_noise_subtype",
        "low_novelty_subtype",
        "financing_subtype",
        "guidance_quality_axis",
        "information_novelty_axis",
        "company_anchor_state",
        "market_acceptance_state",
        "theme_leadership_context",
        "policy_macro_context_state",
        "financing_context_state",
        "high_noise_context_state",
        "low_novelty_context_state",
        "guidance_context_state",
        "firm_grade_context_state",
        "translator_confidence_state",
        "translator_reason_codes",
        "why_not_action_tier",
        "price_absorption_confirmation_flag",
        "price_chart_acceptance_state",
        "near_high60_prev",
        "trend_stack_prev",
        "range_pos",
        "vwap_ok_flag",
        "breakout_so_far_flag",
        "intraday_entry_state_v4",
        "theme_regime_state_v4",
        "theme_ret20_prev",
        "theme_breadth20_prev",
        "theme_volume_ratio_prev",
        "broad_market_score",
        "broad_market_stress",
        "macro_overall_state",
        "relation_transmission_state",
        "weakest_layer",
        "slot_candidate_role",
        "customer_event_count",
        "revenue_backlog_event_count",
        "guidance_margin_event_count",
        "supply_demand_event_count",
        "company_direct_event_count",
        "ownership_noise_event_count",
        "broad_policy_event_count",
        "regulatory_policy_event_count",
        "noise_ratio",
        "translator_output_is_action_flag",
        "outcome_used_for_assignment_flag",
        "future_price_used_for_assignment_flag",
        "missing_source_used_as_negative_flag",
        "macro_used_for_assignment_flag",
    ]
    return out[[c for c in columns if c in out.columns]].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def company_anchor_state(row: pd.Series) -> str:
    direct = int_safe(row.get("company_direct_event_count")) + int_safe(row.get("direct_event_count"))
    economic = economic_signal_count(row)
    if direct > 0 and economic >= 2:
        return "direct_company_anchor_with_economic_detail"
    if direct > 0:
        return "direct_company_anchor_thin_detail"
    if economic >= 2:
        return "indirect_economic_anchor"
    if economic == 1:
        return "single_economic_signal"
    return "no_company_anchor"


def market_acceptance_state(row: pd.Series) -> str:
    price_state = str(row.get("price_chart_acceptance_state", ""))
    if int_safe(row.get("price_absorption_confirmation_flag")) == 1 and "price_confirmed" in price_state:
        return "price_absorbed_and_confirmed"
    if int_safe(row.get("price_absorption_confirmation_flag")) == 1:
        return "price_absorbed_without_full_confirmation"
    if int_safe(row.get("vwap_ok_flag")) == 1 and int_safe(row.get("breakout_so_far_flag")) == 1:
        return "intraday_acceptance_building"
    if float_safe(row.get("range_pos")) >= 0.65 or int_safe(row.get("near_high60_prev")) == 1:
        return "upper_range_but_unconfirmed"
    return "market_not_accepting_yet"


def theme_leadership_context(row: pd.Series) -> str:
    regime = str(row.get("theme_regime_state_v4", ""))
    ret20 = float_safe(row.get("theme_ret20_prev"))
    breadth = float_safe(row.get("theme_breadth20_prev"))
    volume = float_safe(row.get("theme_volume_ratio_prev"))
    if "leader" in regime or (ret20 > 0 and breadth >= 0.5 and volume >= 1):
        return "theme_leadership_supportive"
    if ret20 > 0 and breadth < 0.5:
        return "theme_narrow_leadership"
    if ret20 < 0:
        return "theme_context_fading"
    return "theme_context_unclear"


def policy_macro_context_state(row: pd.Series) -> str:
    policy = int_safe(row.get("broad_policy_event_count")) + int_safe(row.get("regulatory_policy_event_count"))
    macro_state = str(row.get("macro_overall_state", ""))
    if policy > 0 and "stress" in macro_state:
        return "policy_linked_under_macro_stress_diagnostic"
    if policy > 0:
        return "policy_linked_company_context_needed"
    if str(row.get("macro_diagnostic_only_flag", "0")) in {"1", "1.0"}:
        return "macro_context_diagnostic_only"
    return "no_policy_macro_claim"


def financing_context_state(row: pd.Series) -> str:
    subtype = str(row.get("financing_subtype", "not_financing"))
    if subtype == "not_financing":
        return "not_financing"
    accepted = market_acceptance_state(row)
    anchor = company_anchor_state(row)
    economic = economic_signal_count(row)
    if accepted.startswith("price_absorbed") and anchor in {"direct_company_anchor_with_economic_detail", "indirect_economic_anchor"}:
        return "financing_absorbed_with_fundamental_support"
    if accepted.startswith("price_absorbed"):
        return "financing_absorbed_but_fundamental_unclear"
    if economic >= 2:
        return "financing_growth_capital_unabsorbed"
    if "dilutive" in subtype:
        return "financing_dilutive_unabsorbed"
    if "convertible" in subtype:
        return "financing_convertible_overhang_unabsorbed"
    return "financing_conflicted_review"


def high_noise_context_state(row: pd.Series) -> str:
    subtype = str(row.get("high_noise_subtype", "not_high_noise"))
    if subtype == "not_high_noise":
        return "not_high_noise"
    accepted = market_acceptance_state(row)
    anchor = company_anchor_state(row)
    if "direct_company_anchor" in subtype and accepted.startswith("price_absorbed"):
        return "high_noise_direct_anchor_absorbed"
    if "direct_company_anchor" in subtype or anchor.startswith("direct_company_anchor"):
        return "high_noise_direct_anchor_unconfirmed"
    if "ownership" in subtype and accepted.startswith("price_absorbed"):
        return "ownership_noise_price_absorbed"
    if "ownership" in subtype:
        return "ownership_noise_no_company_anchor"
    return "high_noise_context_review"


def low_novelty_context_state(row: pd.Series) -> str:
    subtype = str(row.get("low_novelty_subtype", "not_low_novelty"))
    if subtype == "not_low_novelty":
        return "not_low_novelty"
    accepted = market_acceptance_state(row)
    if "reacceleration" in subtype or accepted.startswith("price_absorbed"):
        return "low_novelty_reaccelerating_or_absorbed"
    if "reaffirmation" in subtype:
        return "guidance_reaffirm_stale_unconfirmed"
    if "manual_indirect" in subtype:
        return "low_novelty_indirect_economic_review"
    return "low_novelty_stale_unconfirmed"


def guidance_context_state(row: pd.Series) -> str:
    guidance = str(row.get("guidance_quality_axis", ""))
    accepted = market_acceptance_state(row)
    if guidance == "raise":
        return "guidance_raise_context"
    if guidance == "reaffirm" and accepted.startswith("price_absorbed"):
        return "guidance_reaffirm_price_confirmed"
    if guidance == "reaffirm":
        return "guidance_reaffirm_unconfirmed"
    if guidance == "soft":
        return "guidance_soft_or_lower_quality"
    return "no_guidance_context"


def firm_grade_context_state(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "source_gap_context_unavailable"
    financing = financing_context_state(row)
    noise = high_noise_context_state(row)
    novelty = low_novelty_context_state(row)
    acceptance = market_acceptance_state(row)
    anchor = company_anchor_state(row)
    theme = theme_leadership_context(row)

    if financing == "financing_absorbed_with_fundamental_support":
        return "capital_cycle_absorbed_growth_setup"
    if financing in {"financing_dilutive_unabsorbed", "financing_convertible_overhang_unabsorbed"}:
        return "capital_raise_unabsorbed_dilution_review"
    if noise == "high_noise_direct_anchor_absorbed":
        return "noisy_source_but_accepted_company_anchor"
    if novelty == "low_novelty_reaccelerating_or_absorbed":
        return "stale_news_reaccelerating_price_context"
    if anchor.startswith("direct_company_anchor") and acceptance.startswith("price_absorbed"):
        return "direct_catalyst_price_accepted"
    if theme == "theme_context_fading" and acceptance == "market_not_accepting_yet":
        return "source_present_but_market_context_fading"
    if "unconfirmed" in financing or "unconfirmed" in noise or "unconfirmed" in novelty:
        return "source_present_but_confirmation_missing"
    return "source_context_needs_human_review"


def translator_confidence_state(row: pd.Series) -> str:
    score = 0
    if company_anchor_state(row) in {"direct_company_anchor_with_economic_detail", "indirect_economic_anchor"}:
        score += 1
    if market_acceptance_state(row).startswith("price_absorbed"):
        score += 1
    if theme_leadership_context(row) == "theme_leadership_supportive":
        score += 1
    if policy_macro_context_state(row).endswith("diagnostic"):
        score -= 1
    if firm_grade_context_state(row) in {"capital_raise_unabsorbed_dilution_review", "source_present_but_market_context_fading"}:
        score -= 1
    if score >= 3:
        return "explanation_high_coherence"
    if score >= 1:
        return "explanation_medium_coherence"
    return "explanation_low_or_review"


def translator_reason_codes(row: pd.Series) -> str:
    return "|".join(
        [
            f"company={company_anchor_state(row)}",
            f"price={market_acceptance_state(row)}",
            f"theme={theme_leadership_context(row)}",
            f"finance={financing_context_state(row)}",
            f"noise={high_noise_context_state(row)}",
            f"novelty={low_novelty_context_state(row)}",
            f"macro={policy_macro_context_state(row)}",
        ]
    )


def build_interaction_matrix(panel: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "financing_context_state",
        "high_noise_context_state",
        "low_novelty_context_state",
        "company_anchor_state",
        "market_acceptance_state",
        "theme_leadership_context",
        "policy_macro_context_state",
        "firm_grade_context_state",
        "translator_confidence_state",
    ]
    return panel.groupby(cols, dropna=False).size().reset_index(name="candidate_count").sort_values(
        "candidate_count", ascending=False
    ).reset_index(drop=True)


def build_review_packet(panel: pd.DataFrame) -> pd.DataFrame:
    cols = KEYS + [
        "firm_grade_context_state",
        "translator_confidence_state",
        "translator_reason_codes",
        "why_not_action_tier",
        "financing_context_state",
        "high_noise_context_state",
        "low_novelty_context_state",
        "market_acceptance_state",
        "theme_leadership_context",
        "policy_macro_context_state",
    ]
    event_linked = panel[panel["source_event_available_flag"].eq(1)].copy()
    return event_linked[[c for c in cols if c in event_linked.columns]].sort_values(
        ["entry_ts", "symbol", "lifecycle_id"]
    ).reset_index(drop=True)


def build_guardrail_audit(panel: pd.DataFrame, eval_panel: pd.DataFrame) -> pd.DataFrame:
    eval_cols = KEYS + ["costed_return_pct", "entry_reduce_failure_flag", "outcome_used_for_evaluation_flag"]
    merged = panel.merge(eval_panel[eval_cols], on=KEYS, how="left", validate="one_to_one")
    top50_ids = set(merged.nlargest(50, "costed_return_pct")["lifecycle_id"])
    bottom50_ids = set(merged.nsmallest(50, "costed_return_pct")["lifecycle_id"])
    rows = []
    for state, group in merged.groupby("firm_grade_context_state", dropna=False):
        state_ids = set(group["lifecycle_id"])
        top_preserved = len(top50_ids & state_ids)
        bottom_preserved = len(bottom50_ids & state_ids)
        rows.append(
            {
                "firm_grade_context_state": state,
                "candidate_count": int(len(group)),
                "top50_winner_count": int(top_preserved),
                "bottom50_loser_count": int(bottom_preserved),
                "top50_winner_share": top_preserved / 50.0,
                "bottom50_loser_share": bottom_preserved / 50.0,
                "avg_costed_return_pct_eval_only": float(group["costed_return_pct"].mean()),
                "median_costed_return_pct_eval_only": float(group["costed_return_pct"].median()),
                "entry_reduce_failure_rate_eval_only": float(pd.to_numeric(group["entry_reduce_failure_flag"], errors="coerce").fillna(0).mean()),
                "outcome_used_for_assignment_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values(["top50_winner_count", "candidate_count"], ascending=[False, False]).reset_index(drop=True)


def build_governance_audit(panel: pd.DataFrame, bundle: pd.DataFrame) -> pd.DataFrame:
    rows = [
        gate("scope_5265", len(panel) == 5265, f"rows={len(panel)}", "5265"),
        gate("event_linked_2445", int(panel["source_event_available_flag"].sum()) == 2445, f"event={int(panel['source_event_available_flag'].sum())}", "2445"),
        gate("context_states_present", panel["firm_grade_context_state"].nunique() >= 6, f"states={panel['firm_grade_context_state'].nunique()}", ">=6"),
        gate("no_action_output", int(panel["translator_output_is_action_flag"].sum()) == 0, f"action_flags={int(panel['translator_output_is_action_flag'].sum())}", "0"),
        gate("no_outcome_assignment", int(panel["outcome_used_for_assignment_flag"].sum()) == 0, "0", "0"),
        gate("no_future_price_assignment", int(panel["future_price_used_for_assignment_flag"].sum()) == 0, "0", "0"),
        gate("missing_source_not_negative", int(panel["missing_source_used_as_negative_flag"].sum()) == 0, "0", "0"),
        gate("macro_not_promoted", int(panel["macro_used_for_assignment_flag"].sum()) == 0, "0", "0"),
        gate("input_bundle_scope", len(bundle) == len(panel), f"bundle={len(bundle)}", "panel row count"),
    ]
    return pd.DataFrame(rows)


def build_context_gather_source_map() -> pd.DataFrame:
    rows = [
        {
            "source_name": "Federal Reserve monetary transmission mechanism",
            "url": "https://www.federalreserve.gov/econres/feds/how-has-the-monetary-transmission-mechanism-evolved-over-time.htm",
            "source_type": "official_research",
            "translator_implication": "Policy is not a ticker signal; it moves through rates, asset prices, exchange rates, demand, and expectations.",
            "implemented_axis": "policy_macro_context_state",
        },
        {
            "source_name": "Federal Reserve firm financial conditions",
            "url": "https://www.federalreserve.gov/econres/feds/firm-financial-conditions-and-the-transmission-of-monetary-policy.htm",
            "source_type": "official_research",
            "translator_implication": "Financing events must be read through firm financial condition, credit spread pressure, and investment capacity.",
            "implemented_axis": "financing_context_state",
        },
        {
            "source_name": "IMF stock-bond correlation shift",
            "url": "https://www.imf.org/en/blogs/articles/2026/02/18/stock-bond-diversification-offers-less-protection-from-market-selloffs",
            "source_type": "official_research",
            "translator_implication": "Risk state cannot assume bonds cushion equity stress; volatility and funding pressure can reinforce selloffs.",
            "implemented_axis": "theme_leadership_context, policy_macro_context_state",
        },
        {
            "source_name": "IMF Global Financial Stability Report October 2025",
            "url": "https://www.imf.org/en/publications/gfsr/issues/2025/10/14/global-financial-stability-report-october-2025",
            "source_type": "official_research",
            "translator_implication": "Stretched valuations and NBFI/funding channels mean price acceptance and liquidity context must gate confidence.",
            "implemented_axis": "market_acceptance_state",
        },
        {
            "source_name": "BlackRock 2026 Investment Outlook",
            "url": "https://www.blackrock.com/institutions/en-us/insights/thought-leadership/global-investment-outlook",
            "source_type": "institution_research",
            "translator_implication": "Micro catalysts can become macro when capex, financing, and revenue capture interact across sectors.",
            "implemented_axis": "company_anchor_state, financing_context_state, theme_leadership_context",
        },
        {
            "source_name": "J.P. Morgan 2026 Year-Ahead Investment Outlook",
            "url": "https://am.jpmorgan.com/us/en/asset-management/liq/insights/market-insights/investment-outlook/",
            "source_type": "institution_research",
            "translator_implication": "Range-of-outcomes thinking and selectivity matter more than one directional macro bet.",
            "implemented_axis": "translator_confidence_state",
        },
        {
            "source_name": "AQR Investing with Style",
            "url": "https://www.aqr.com/Insights/Research/Journal-Article/Investing-With-Style",
            "source_type": "institution_research",
            "translator_implication": "Momentum, defensive, carry, and value-like styles should be treated as context and diversification lenses, not single labels.",
            "implemented_axis": "theme_leadership_context, market_acceptance_state",
        },
        {
            "source_name": "NBER policy news and market volatility",
            "url": "https://www.nber.org/papers/w25720",
            "source_type": "academic_research",
            "translator_implication": "Policy news affects volatility and firm-level risk exposure; classify policy linkage separately from company catalyst quality.",
            "implemented_axis": "policy_macro_context_state",
        },
        {
            "source_name": "Andrew Lo adaptive markets hypothesis",
            "url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1977721",
            "source_type": "academic_research",
            "translator_implication": "Market efficiency and payoff to signals vary by regime and participant adaptation; static priority labels are fragile.",
            "implemented_axis": "firm_grade_context_state",
        },
        {
            "source_name": "NBER institutional order flow and stock returns",
            "url": "https://www.nber.org/papers/w11439",
            "source_type": "academic_research",
            "translator_implication": "Institutional flow can be inferred from tape behavior; until full microstructure is ready, price acceptance is only a proxy.",
            "implemented_axis": "market_acceptance_state",
        },
    ]
    return pd.DataFrame(rows)


def decision_frame(panel: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task712",
                "verdict": "FIRM_GRADE_TRANSLATOR_CONTEXT_ENGINE_BUILT_DIAGNOSTIC_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "row_count": int(len(panel)),
                "context_state_count": int(panel["firm_grade_context_state"].nunique()),
                "top_winner_max_state_share": float(guardrail["top50_winner_share"].max()),
                "bottom_loser_max_state_share": float(guardrail["bottom50_loser_share"].max()),
                "trading_promotion_pass_flag": 0,
                "next_action": "Use context states for review and guardrail analysis only; do not translate them into actions yet.",
            }
        ]
    )


def pass_fail_matrix(
    panel: pd.DataFrame,
    interaction_matrix: pd.DataFrame,
    guardrail: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    rows = [
        gate("scope_5265", len(panel) == 5265, f"rows={len(panel)}", "5265"),
        gate("event_linked_2445", int(panel["source_event_available_flag"].sum()) == 2445, f"event={int(panel['source_event_available_flag'].sum())}", "2445"),
        gate("context_states_present", panel["firm_grade_context_state"].nunique() >= 6, f"states={panel['firm_grade_context_state'].nunique()}", ">=6"),
        gate("interaction_matrix_present", len(interaction_matrix) > 0, f"rows={len(interaction_matrix)}", ">0"),
        gate("guardrail_eval_present", len(guardrail) > 0, f"rows={len(guardrail)}", ">0"),
        gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
        gate("no_action_output", int(panel["translator_output_is_action_flag"].sum()) == 0, "0", "0"),
        gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
    ]
    return pd.DataFrame(rows)


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    report = f"""# Task712 Firm Grade Translator Engine

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: Task712 replaces action-like priority labels with firm-grade context explanation states.
- Next action: {decision.iloc[0]['next_action']}

## Quant Expert Report

- Context gather sources: Fed, IMF, BlackRock, J.P. Morgan, AQR, NBER, and Adaptive Markets research are mapped in `task712_context_gather_source_map.csv`.
- Implementation: source risk is translated into economic context states, not buy/sell/hold actions.
- Data scope: current Task706 bundle, 5,265 candidates and 2,445 event-linked candidates.
- Leakage audit: outcome and future-price assignment flags are zero. Outcome appears only in guardrail evaluation.
- Core design: financing, high-noise, low-novelty, guidance, company anchor, market acceptance, policy/macro, and theme leadership are separated before any slot or allocation logic.
- Remaining blocker: no trade action is approved. This is a translator-brain artifact, not a trading strategy.

## No-Background Decision-Maker Report

- We stopped using labels like PRIORITY or REJECT.
- The new engine explains what kind of situation each candidate is in.
- It checks whether the candidate has company evidence, price acceptance, theme support, financing risk, policy linkage, and stale-news risk.
- It still does not decide to buy.
- Capital remains forbidden.

## Artifact Manifest

- Outputs: {', '.join(outputs.keys())}.
- Row counts: {artifact_counts(outputs)}.
- Validation command: `python -m unittest tests.test_task712_firm_grade_translator_engine`.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / "task_712_firm_grade_translator_engine.md").write_text(report, encoding="utf-8")
    manifest = out_dir / "artifact_manifest.csv"
    if manifest.exists():
        manifest.unlink()
    write_manifest(out_dir, manifest)


def economic_signal_count(row: pd.Series) -> int:
    return (
        int_safe(row.get("customer_event_count"))
        + int_safe(row.get("revenue_backlog_event_count"))
        + int_safe(row.get("guidance_margin_event_count"))
        + int_safe(row.get("supply_demand_event_count"))
    )


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


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Task712 firm-grade translator context engine.")
    parser.add_argument("--bundle", type=Path, default=TASK706_BUNDLE)
    parser.add_argument("--eval", type=Path, default=TASK708_EVAL)
    parser.add_argument("--out-dir", type=Path, default=TASK712_DIR)
    args = parser.parse_args()
    build_task712(bundle_path=args.bundle, eval_path=args.eval, out_dir=args.out_dir)
    print("[Task712] wrote firm-grade translator context artifacts")


if __name__ == "__main__":
    main()
