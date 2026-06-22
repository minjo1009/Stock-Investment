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


TASK682_DIR = Path("docs/reports/task_682_integrated_prediction_stack")
TASK683_DIR = Path("docs/reports/task_683_firm_grade_context_gather_5_engine_review")
ACTIVE_CAP3 = "active_relation_cap3_reference"


def build_task683_program(task682_dir: Path = TASK682_DIR) -> dict[str, pd.DataFrame]:
    TASK683_DIR.mkdir(parents=True, exist_ok=True)
    stack = pd.read_csv(task682_dir / "task682_integrated_stack_panel.csv")
    accepted = pd.read_csv(task682_dir / "task682_accepted_trades.csv")
    grid = pd.read_csv(task682_dir / "task682_simulation_result.csv")
    guardrail = pd.read_csv(task682_dir / "task682_guardrail_audit.csv")

    active = accepted[
        accepted["candidate_name"].eq(ACTIVE_CAP3) & accepted["split_scope"].eq("all")
    ].copy()

    distributions = build_distribution_audit(stack, active)
    gap_audit = build_engine_context_gap_audit(distributions)
    mixed = build_mixed_context_decomposition(active)
    catalyst_low = build_catalyst_low_reinterpretation(active)
    same_symbol = build_same_symbol_conflict_interpreter(active)
    superiority = build_context_superiority_contract()
    sources = build_method_context_sources()
    decision = build_decision(grid, guardrail, mixed, catalyst_low, same_symbol)
    pass_fail = build_pass_fail(distributions, mixed, catalyst_low, same_symbol)

    write_outputs(
        distributions,
        gap_audit,
        mixed,
        catalyst_low,
        same_symbol,
        superiority,
        sources,
        decision,
        pass_fail,
        grid,
        guardrail,
    )
    return {
        "distributions": distributions,
        "gap_audit": gap_audit,
        "mixed": mixed,
        "catalyst_low": catalyst_low,
        "same_symbol": same_symbol,
        "superiority": superiority,
        "sources": sources,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_distribution_audit(stack: pd.DataFrame, active: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cols = [
        "leadership_lifecycle_state",
        "catalyst_economic_quality",
        "archetype_candidate",
        "same_symbol_state_variant",
        "price_chart_acceptance_state",
        "relation_transmission_state",
    ]
    for col in cols:
        for scope, frame in [("universe", stack), ("active_cap3", active)]:
            counts = frame[col].value_counts(dropna=False)
            total = max(int(len(frame)), 1)
            for value, count in counts.items():
                rows.append(
                    {
                        "field_name": col,
                        "scope": scope,
                        "state_value": value,
                        "row_count": int(count),
                        "share_pct": float(count / total * 100.0),
                    }
                )
    return pd.DataFrame(rows)


def build_engine_context_gap_audit(distributions: pd.DataFrame) -> pd.DataFrame:
    active_mixed = count_state(distributions, "archetype_candidate", "active_cap3", "mixed_or_unclear_candidate")
    active_low = count_state(distributions, "catalyst_economic_quality", "active_cap3", "low")
    active_downgrade = count_state(distributions, "same_symbol_state_variant", "active_cap3", "same_symbol_context_downgrade")
    participating = count_state(distributions, "leadership_lifecycle_state", "universe", "participating_theme")
    rows = [
        {
            "engine_name": "Leadership Lifecycle Panel",
            "observed_gap": f"participating_theme universe_count={participating}",
            "firm_grade_missing_question": "Is this theme emerging, persistent, late, fading, or neutral after considering breadth, volume confirmation, and market backdrop?",
            "required_context_contract": "Add phase strength, breadth confirmation, rotation risk, and reason codes; reduce neutral warehouse behavior.",
            "assignment_status": "context_only_until_validated",
        },
        {
            "engine_name": "Catalyst Quality Matrix",
            "observed_gap": f"active_cap3_low_count={active_low}",
            "firm_grade_missing_question": "Is low catalyst truly weak, or is the event already being absorbed through price, theme, or relation support?",
            "required_context_contract": "Split true_low, weak_but_price_confirmed, weak_but_theme_supported, weak_but_relation_supported, delayed_absorption_candidate, conflicted_low.",
            "assignment_status": "do_not_reject_low_without_absorption_context",
        },
        {
            "engine_name": "Archetype Candidate Engine",
            "observed_gap": f"active_cap3_mixed_count={active_mixed}",
            "firm_grade_missing_question": "Which continuation structure is hidden inside mixed: price-led, catalyst-led, theme-led, relation-led, delayed absorption, conflict, or true unclear?",
            "required_context_contract": "Create mixed sub-context fields before using archetype for slot superiority.",
            "assignment_status": "mixed_is_not_negative",
        },
        {
            "engine_name": "Same Symbol Context Matrix",
            "observed_gap": f"active_cap3_downgrade_count={active_downgrade}",
            "firm_grade_missing_question": "Is the same symbol worse, or is today a different setup variant?",
            "required_context_contract": "Use as conflict interpreter only: same-symbol downgrade must explain context shift, not directly reduce rank.",
            "assignment_status": "interpreter_not_ranker",
        },
        {
            "engine_name": "Cohort Slot Qualification",
            "observed_gap": "v2 preserves active cap3 winners but adds no better candidates",
            "firm_grade_missing_question": "Does a challenger have a complete context superiority packet versus the incumbent inside the same entry_ts cohort?",
            "required_context_contract": "Compare candidate and incumbent packets across source, catalyst absorption, archetype clarity, leadership, price, relation, same-symbol conflict, and concentration.",
            "assignment_status": "replacement_requires_superiority_packet",
        },
    ]
    return pd.DataFrame(rows)


def build_mixed_context_decomposition(active: pd.DataFrame) -> pd.DataFrame:
    rows = []
    mixed = active[active["archetype_candidate"].eq("mixed_or_unclear_candidate")].copy()
    for row in mixed.to_dict(orient="records"):
        sub_context, reasons = mixed_sub_context(row)
        rows.append(
            {
                "lifecycle_id": row.get("lifecycle_id", ""),
                "symbol": row.get("symbol", ""),
                "entry_ts": row.get("entry_ts", ""),
                "theme_id": row.get("theme_id", ""),
                "mixed_sub_context": sub_context,
                "mixed_reason_codes": "|".join(reasons),
                "price_chart_acceptance_state": row.get("price_chart_acceptance_state", ""),
                "leadership_lifecycle_state": row.get("leadership_lifecycle_state", ""),
                "catalyst_economic_quality": row.get("catalyst_economic_quality", ""),
                "relation_transmission_state": row.get("relation_transmission_state", ""),
                "net_return_costed_eval_only": row.get("net_return_costed", ""),
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def mixed_sub_context(row: dict[str, object]) -> tuple[str, list[str]]:
    price = s(row.get("price_chart_acceptance_state", ""))
    leadership = s(row.get("leadership_lifecycle_state", ""))
    catalyst = s(row.get("catalyst_economic_quality", ""))
    overhang = s(row.get("catalyst_negative_overhang", ""))
    relation = s(row.get("relation_transmission_state", ""))
    support = i(row.get("mechanism_support_count", row.get("support_count", 0)))
    pressure = i(row.get("mechanism_pressure_count", row.get("conflict_count", 0)))
    reasons = []
    if price in {"price_confirmed_basic", "price_confirmed_not_extended"}:
        reasons.append("price_acceptance_present")
    if leadership in {"persistent_leadership", "participating_theme", "emerging_leadership"}:
        reasons.append("leadership_not_late")
    if catalyst == "low":
        reasons.append("catalyst_low")
    if relation in {"relation_reinforcing", "company_positive_confirmation_needed", "company_price_confirmed_macro_secondary"}:
        reasons.append("relation_supportive")
    if pressure > support:
        reasons.append("pressure_gt_support")
    if price == "price_confirmed_but_extended":
        reasons.append("extension_risk")

    if catalyst == "low" and price in {"price_confirmed_basic", "price_confirmed_not_extended"} and relation in {"relation_reinforcing", "company_positive_confirmation_needed"}:
        return "mixed_delayed_absorption_or_price_led", reasons
    if price in {"price_confirmed_basic", "price_confirmed_not_extended"}:
        return "mixed_price_led_continuation", reasons
    if relation in {"relation_reinforcing", "company_positive_confirmation_needed", "company_price_confirmed_macro_secondary"}:
        return "mixed_relation_led_continuation", reasons
    if leadership in {"persistent_leadership", "emerging_leadership"}:
        return "mixed_theme_led_continuation", reasons
    if overhang in {"moderate", "severe"} and support >= pressure:
        return "mixed_conflicted_but_alive", reasons
    if price == "price_confirmed_but_extended":
        return "mixed_due_to_late_extension", reasons
    return "mixed_true_unclear", reasons if reasons else ["no_clear_context"]


def build_catalyst_low_reinterpretation(active: pd.DataFrame) -> pd.DataFrame:
    rows = []
    low = active[active["catalyst_economic_quality"].eq("low")].copy()
    for row in low.to_dict(orient="records"):
        state, reasons = catalyst_low_state(row)
        rows.append(
            {
                "lifecycle_id": row.get("lifecycle_id", ""),
                "symbol": row.get("symbol", ""),
                "entry_ts": row.get("entry_ts", ""),
                "theme_id": row.get("theme_id", ""),
                "catalyst_low_reinterpretation": state,
                "catalyst_low_reason_codes": "|".join(reasons),
                "catalyst_path_type": row.get("catalyst_path_type", ""),
                "catalyst_negative_overhang": row.get("catalyst_negative_overhang", ""),
                "catalyst_signal_density": row.get("catalyst_signal_density", ""),
                "price_chart_acceptance_state": row.get("price_chart_acceptance_state", ""),
                "relation_transmission_state": row.get("relation_transmission_state", ""),
                "net_return_costed_eval_only": row.get("net_return_costed", ""),
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def catalyst_low_state(row: dict[str, object]) -> tuple[str, list[str]]:
    price = s(row.get("price_chart_acceptance_state", ""))
    relation = s(row.get("relation_transmission_state", ""))
    leadership = s(row.get("leadership_lifecycle_state", ""))
    overhang = s(row.get("catalyst_negative_overhang", ""))
    reasons = [f"overhang={overhang}"]
    if price in {"price_confirmed_basic", "price_confirmed_not_extended"}:
        reasons.append("price_confirmed")
    if relation in {"relation_reinforcing", "company_positive_confirmation_needed", "company_price_confirmed_macro_secondary"}:
        reasons.append("relation_supportive")
    if leadership in {"persistent_leadership", "participating_theme", "emerging_leadership"}:
        reasons.append("theme_not_fading")
    if overhang == "severe" and "price_confirmed" not in reasons:
        return "true_low_or_blocker_context", reasons
    if "price_confirmed" in reasons and "relation_supportive" in reasons:
        return "weak_but_price_relation_confirmed", reasons
    if "price_confirmed" in reasons and "theme_not_fading" in reasons:
        return "weak_but_price_theme_supported", reasons
    if "relation_supportive" in reasons:
        return "weak_but_relation_supported", reasons
    return "true_low_unconfirmed", reasons


def build_same_symbol_conflict_interpreter(active: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in active.to_dict(orient="records"):
        state = s(row.get("same_symbol_state_variant", ""))
        interpretation, reasons = same_symbol_interpretation(row)
        rows.append(
            {
                "lifecycle_id": row.get("lifecycle_id", ""),
                "symbol": row.get("symbol", ""),
                "entry_ts": row.get("entry_ts", ""),
                "same_symbol_state_variant": state,
                "same_symbol_conflict_interpretation": interpretation,
                "same_symbol_interpreter_reason_codes": "|".join(reasons),
                "symbol_context_signature": row.get("symbol_context_signature", ""),
                "same_symbol_prior_signature": row.get("same_symbol_prior_signature", ""),
                "net_return_costed_eval_only": row.get("net_return_costed", ""),
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def same_symbol_interpretation(row: dict[str, object]) -> tuple[str, list[str]]:
    state = s(row.get("same_symbol_state_variant", ""))
    price = s(row.get("price_chart_acceptance_state", ""))
    relation = s(row.get("relation_transmission_state", ""))
    reasons = [state]
    if "downgrade" in state:
        if price in {"price_confirmed_basic", "price_confirmed_not_extended"} or relation in {"relation_reinforcing", "company_positive_confirmation_needed"}:
            reasons.append("downgrade_but_current_setup_has_support")
            return "context_shift_not_direct_negative", reasons
        return "same_symbol_context_conflict", reasons
    if "upgrade" in state:
        return "context_upgrade_interpretation_only", reasons
    if "unclear" in state:
        return "same_symbol_unclear_do_not_rank", reasons
    return "same_symbol_repeat_or_neutral_interpretation", reasons


def build_context_superiority_contract() -> pd.DataFrame:
    rows = [
        ("source_asof", "candidate_source_not_worse", "asof_valid_flag and sparse_action_block_flag", "hard eligibility"),
        ("catalyst_absorption", "candidate_not_worse_and_absorption_explained", "catalyst_low_reinterpretation and catalyst_conflict_state", "confirmation not primary rank"),
        ("archetype_context", "candidate_has_clearer_sub_context", "archetype_candidate plus mixed_sub_context", "primary superiority dimension"),
        ("leadership_lifecycle", "candidate_not_later_or_more_fading", "leadership_lifecycle_state and rotation risk", "supporting dimension"),
        ("price_acceptance", "candidate_price_not_worse", "price_chart_acceptance_state", "confirmation dimension"),
        ("relation_transmission", "candidate_pressure_not_worse", "relation_transmission_state and support/pressure counts", "blocker/support dimension"),
        ("same_symbol", "conflict_interpreted_not_ranked", "same_symbol_conflict_interpretation", "interpreter only"),
        ("capacity", "concentration_not_worse", "open theme/relation/driver counts", "portfolio risk dimension"),
        ("tiebreak", "priority_rank_last_only", "priority_rank", "final tie-breaker only"),
    ]
    return pd.DataFrame(
        [
            {
                "packet_dimension": dim,
                "required_comparison": comp,
                "current_data_fields": fields,
                "slot_usage": usage,
                "return_used_in_assignment_flag": 0,
            }
            for dim, comp, fields, usage in rows
        ]
    )


def build_method_context_sources() -> pd.DataFrame:
    rows = [
        {
            "source_name": "MacKinlay 1997 Event Studies in Economics and Finance",
            "source_url": "https://ideas.repec.org/a/aea/jeclit/v35y1997i1p13-39.html",
            "method_takeaway": "Event context requires event window, expected return baseline, abnormal reaction, and confounding-event awareness.",
            "engine_implication": "Catalyst Quality must separate catalyst existence from absorption state and price reaction.",
        },
        {
            "source_name": "Jegadeesh and Titman 1993 Momentum",
            "source_url": "https://www.researchgate.net/publication/4992307_Returns_to_Buying_Winners_and_Selling_Losers_Implications_for_Stock_Market_Efficiency",
            "method_takeaway": "Intermediate-horizon winners can continue, but later reversal risk exists.",
            "engine_implication": "Archetype and Leadership must treat continuation and extension risk together.",
        },
        {
            "source_name": "Moskowitz, Ooi, Pedersen 2012 Time Series Momentum",
            "source_url": "https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID2089463_code753937.pdf?abstractid=2089463&mirid=1",
            "method_takeaway": "Trend persistence and reversal can coexist across assets.",
            "engine_implication": "Leadership Lifecycle needs phase and reversal-risk fields, not only strength labels.",
        },
        {
            "source_name": "Moskowitz and Grinblatt 1999 Industry Momentum",
            "source_url": "https://onlinelibrary.wiley.com/doi/pdf/10.1111/0022-1082.00146",
            "method_takeaway": "Industry momentum can explain much of individual stock momentum.",
            "engine_implication": "Leadership Lifecycle and Cohort Slot Qualification must compare theme/sector context inside the same timestamp.",
        },
        {
            "source_name": "Bernard and Thomas 1989 Post-Earnings-Announcement Drift",
            "source_url": "https://ideas.repec.org/a/bla/joares/v27y1989ip1-36.html",
            "method_takeaway": "Information can be incorporated with delay after earnings/catalyst events.",
            "engine_implication": "Catalyst low cannot be rejected without delayed absorption and price/relation support checks.",
        },
    ]
    return pd.DataFrame(rows)


def build_decision(
    grid: pd.DataFrame,
    guardrail: pd.DataFrame,
    mixed: pd.DataFrame,
    catalyst_low: pd.DataFrame,
    same_symbol: pd.DataFrame,
) -> pd.DataFrame:
    active = grid[grid["candidate_name"].eq(ACTIVE_CAP3) & grid["split_name"].eq("all")].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": "Task683",
                "decision": "FIRM_GRADE_CONTEXT_GATHER_COMPLETE_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "active_cap3_final_capital_usd": float(active["final_capital_usd"]),
                "active_cap3_max_drawdown_pct": float(active["max_drawdown_pct"]),
                "active_mixed_decomposed_count": int(len(mixed)),
                "active_catalyst_low_reinterpreted_count": int(len(catalyst_low)),
                "active_same_symbol_interpreted_count": int(len(same_symbol)),
                "trading_promotion_pass_flag": 0,
                "next_action": "Use the Task683 contracts to deepen the same five engines before any further trading-rule promotion.",
            }
        ]
    )


def build_pass_fail(
    distributions: pd.DataFrame,
    mixed: pd.DataFrame,
    catalyst_low: pd.DataFrame,
    same_symbol: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("five_engine_context_gather_built", True, "context artifacts created", "all five engines covered"),
            gate("active_mixed_decomposition_built", len(mixed) >= 1, f"rows={len(mixed)}", "active mixed rows decomposed"),
            gate("active_catalyst_low_reinterpretation_built", len(catalyst_low) >= 1, f"rows={len(catalyst_low)}", "active catalyst low rows reinterpreted"),
            gate("same_symbol_interpreter_built", len(same_symbol) >= 1, f"rows={len(same_symbol)}", "same-symbol rows interpreted"),
            gate("no_assignment_promotion", True, "research only", "no strategy promotion"),
            gate("distribution_audit_built", len(distributions) >= 1, f"rows={len(distributions)}", "distribution rows"),
        ]
    )


def write_outputs(
    distributions: pd.DataFrame,
    gap_audit: pd.DataFrame,
    mixed: pd.DataFrame,
    catalyst_low: pd.DataFrame,
    same_symbol: pd.DataFrame,
    superiority: pd.DataFrame,
    sources: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
    grid: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> None:
    files = {
        "task683_engine_distribution_audit.csv": distributions,
        "task683_engine_context_gap_audit.csv": gap_audit,
        "task683_active_mixed_context_decomposition.csv": mixed,
        "task683_active_catalyst_low_reinterpretation.csv": catalyst_low,
        "task683_same_symbol_conflict_interpreter.csv": same_symbol,
        "task683_context_superiority_contract.csv": superiority,
        "task683_method_context_sources.csv": sources,
        "task_683_decision.csv": decision,
        "task_683_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK683_DIR / name, index=False)
    (TASK683_DIR / "task_683_firm_grade_context_gather_5_engine_review.md").write_text(
        render_report(distributions, gap_audit, mixed, catalyst_low, same_symbol, superiority, sources, decision, pass_fail, grid, guardrail),
        encoding="utf-8",
    )
    write_manifest(TASK683_DIR, TASK683_DIR / "artifact_manifest.csv")


def render_report(
    distributions: pd.DataFrame,
    gap_audit: pd.DataFrame,
    mixed: pd.DataFrame,
    catalyst_low: pd.DataFrame,
    same_symbol: pd.DataFrame,
    superiority: pd.DataFrame,
    sources: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
    grid: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> str:
    active = grid[grid["candidate_name"].eq(ACTIVE_CAP3) & grid["split_name"].eq("all")].iloc[0]
    return f"""# Task683 Firm Grade Context Gather Five Engine Review

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: active cap3 ${float(active['final_capital_usd']):,.2f} / MDD {float(active['max_drawdown_pct']):.2f}%.
- What changed: this task does not promote a rule. It builds firm-grade context contracts for the same five engines and decomposes the active cap3 cases that Task682 treated too shallowly.
- Next action: deepen the same five engines using the context contracts before any further slot promotion.

## Quant Expert Report

### Data source and source readiness

- Inputs: Task682 integrated stack, Task682 accepted trades, Task682 simulation results, Task682 guardrail audit.
- External method context was used only as research framework, not as market data.
- GPT was used only as an external review panel, not as source truth or assignment input.
- No microstructure, quote, trade, NBBO, future return, label, symbol blacklist, or theme blacklist is used.

### Exact join keys

- Task683 reads Task682 artifacts.
- Active cap3 decomposition uses `lifecycle_id`.
- Same-timestamp slot guidance remains scoped to `entry_ts`.

### Leakage audit

- All decomposition return fields are marked `eval_only`.
- Assignment promotion is zero.
- Context contracts are research-only until tested in the five-engine implementation.

### Method context gathered

{t678.markdown_table(sources)}

Source interpretation:

- MacKinlay's event-study framework supports separating catalyst existence from event-window absorption and confounding-event risk.
- Jegadeesh/Titman and Moskowitz/Ooi/Pedersen support treating continuation and reversal risk together rather than making a one-way momentum label.
- Moskowitz/Grinblatt supports industry/theme context as a first-class part of single-name momentum.
- Bernard/Thomas supports delayed information absorption after earnings-like events, so weak catalyst labels cannot be hard rejects without price/relation checks.

### Current distribution audit

{t678.markdown_table(distributions.head(80))}

### Five engine gap audit

{t678.markdown_table(gap_audit)}

### Active mixed context decomposition

Task682's most important failure is that active cap3 contains many profitable candidates whose archetype is still `mixed_or_unclear_candidate`. Task683 decomposes these without calling them winners or using them for assignment.

{t678.markdown_table(mixed.head(50))}

### Active catalyst low reinterpretation

Task682's second failure is that active cap3 contains many `catalyst_economic_quality=low` candidates. Low catalyst is not automatically bad; it may mean price-led, theme-supported, relation-supported, or delayed absorption.

{t678.markdown_table(catalyst_low.head(50))}

### Same symbol conflict interpreter

Same-symbol downgrade is not a sell/avoid score. It is an explanation that today's setup differs from the prior setup.

{t678.markdown_table(same_symbol.head(60))}

### Context superiority contract

{t678.markdown_table(superiority)}

### Split/OOS metrics reference

{t678.markdown_table(grid)}

### Guardrail reference

{t678.markdown_table(guardrail)}

### Remaining blockers

- Task683 is context gather and design development, not a tradable strategy.
- The five engines still need implementation changes that use these context contracts without adding global rank, label leakage, or direct winner preservation as assignment logic.
- The next acceptable code change must reduce `mixed_true_unclear`, reinterpret catalyst low, and build a context superiority packet while staying inside the same five engines.

## No-Background Decision-Maker Report

- What happened: the project now has a real diagnosis of why the five engines are shallow.
- Why it matters: active cap3's best trades often look `mixed`, `low catalyst`, or `same-symbol downgrade` under the current labels. Treating those labels as bad would kill winners.
- Whether this changes capital readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: do not add a new filter. Split the unclear buckets into understandable sub-contexts and only then retest slot replacement.

## Artifact Manifest

- Inputs: Task682 stack, accepted trades, simulation, guardrail.
- Outputs: context distribution audit, five-engine gap audit, active mixed decomposition, catalyst-low reinterpretation, same-symbol interpreter, context superiority contract, method source ledger, decision CSV, pass/fail CSV, report, manifest.
- Row counts: distributions={len(distributions)}, gap_audit={len(gap_audit)}, mixed={len(mixed)}, catalyst_low={len(catalyst_low)}, same_symbol={len(same_symbol)}, superiority={len(superiority)}.
- Validation commands: `python src/backtest/build_task683_firm_grade_context_gather_5_engine_review.py`; `python -m unittest tests.test_task683_firm_grade_context_gather_5_engine_review`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def count_state(distributions: pd.DataFrame, field: str, scope: str, state: str) -> int:
    row = distributions[
        distributions["field_name"].eq(field)
        & distributions["scope"].eq(scope)
        & distributions["state_value"].eq(state)
    ]
    if row.empty:
        return 0
    return int(row.iloc[0]["row_count"])


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {"gate_name": name, "pass_flag": int(bool(passed)), "observed": observed, "required": required}


def i(value: object, default: int = 0) -> int:
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def s(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task682-dir", type=Path, default=TASK682_DIR)
    args = parser.parse_args()
    build_task683_program(args.task682_dir)
    print(f"[Task683] wrote {TASK683_DIR}")


if __name__ == "__main__":
    main()
