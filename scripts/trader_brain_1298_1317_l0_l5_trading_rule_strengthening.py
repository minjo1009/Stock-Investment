from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1228 = ROOT / "data/artifacts/task_1228_1237_volatility_terminal_discriminator"
TASK1268 = ROOT / "data/artifacts/task_1268_1287_source_extractors"
TASK1288 = ROOT / "data/artifacts/task_1288_1297_multisource_policy_replay"
OUT_DIR = ROOT / "data/artifacts/task_1298_1317_l0_l5_trading_rule_strengthening"
REPORT_DIR = ROOT / "docs/reports/task_1298_1317_l0_l5_trading_rule_strengthening"

AUTHORITY = "DIAGNOSTIC_L0_L5_TRADING_RULE_STRENGTHENING_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0


SOURCE_CONTEXT = [
    {
        "source_id": "sec_edgar_submissions",
        "source_family": "sec_survival",
        "source_name": "SEC EDGAR submissions / company filings",
        "url": "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        "trading_rule_use": "L0/L1 public-filer source timestamp and accession evidence",
        "limitation": "Public-filer proxy is not full exchange-listed PIT universe",
    },
    {
        "source_id": "sec_form_8k",
        "source_family": "ir_ceo_earnings_call",
        "source_name": "SEC Form 8-K current reports",
        "url": "https://www.sec.gov/files/form8-k.pdf",
        "trading_rule_use": "L1 management narrative and material event evidence",
        "limitation": "Exhibit text may include promotional language and must be interpreted",
    },
    {
        "source_id": "sec_ex10_ex99",
        "source_family": "contract_orders_customer",
        "source_name": "SEC exhibits including EX-10 and EX-99",
        "url": "https://www.sec.gov/files/form8-k.pdf",
        "trading_rule_use": "L1 contract/order/customer validation and materiality tags",
        "limitation": "Company-side evidence only; counterparty confirmation remains missing",
    },
    {
        "source_id": "federal_register_api",
        "source_family": "policy_news_catalyst",
        "source_name": "Federal Register API",
        "url": "https://www.federalregister.gov/developers/documentation/api/v1",
        "trading_rule_use": "L1/L2 theme policy catalyst shadow evidence",
        "limitation": "Theme-level policy is not symbol-level revenue confirmation",
    },
    {
        "source_id": "federal_reserve_fomc",
        "source_family": "macro_policy",
        "source_name": "Federal Reserve FOMC calendars and statements",
        "url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "trading_rule_use": "L0/L2 macro regime context and rate-cycle stress",
        "limitation": "Not yet wired into this selected-row replay",
    },
    {
        "source_id": "nasdaq_listing_rules",
        "source_family": "lifecycle_tradability",
        "source_name": "Nasdaq continued listing rules",
        "url": "https://listingcenter.nasdaq.com/rulebook/nasdaq/rules/Nasdaq%205800%20Series",
        "trading_rule_use": "L0 lifecycle and delisting-risk future source requirement",
        "limitation": "Historical exchange-listed PIT feed still required",
    },
    {
        "source_id": "nyse_listed_company_manual",
        "source_family": "lifecycle_tradability",
        "source_name": "NYSE listed company manual",
        "url": "https://nyseguide.srorules.com/listed-company-manual",
        "trading_rule_use": "L0 lifecycle and continued-listing diagnostics",
        "limitation": "Historical constituent/listing events remain vendor/API gap",
    },
    {
        "source_id": "analyst_vendor_gap",
        "source_family": "analyst_institution",
        "source_name": "Institutional estimates and analyst revisions",
        "url": "vendor_required",
        "trading_rule_use": "L1/L2 expectation reset and estimate-revision confirmation",
        "limitation": "No PIT vendor feed attached in repo; missing data is never negative",
    },
]


PLAN_ROWS = [
    ("Task1298", "Expert Source Context", "Record source authority and GPT/expert role basis for L0-L5 rules"),
    ("Task1299", "L0-L5 Strengthening Plan", "Map each layer to a concrete trading decision and no-leakage boundary"),
    ("Task1300", "L0 Coverage Gate", "Separate usable shadow evidence from source gaps without treating gaps as negatives"),
    ("Task1301", "L1 Signal Quality", "Score source specificity, confirmation count, and watch flags from prior-known sources"),
    ("Task1302", "L2 Trading Judgment", "Convert evidence into conviction/risk/uncertainty scores without outcome labels"),
    ("Task1303", "L3 Rule Action Edges", "Attach relation actions: reinforce, haircut, cap, watch, or no-change"),
    ("Task1304", "L4 Rank Route Panel", "Build rank-adjusted route scores inside the selected slot5 universe"),
    ("Task1305", "L5 Policy Specs", "Pre-register L5 sizing/hold rules from the L0-L4 panels"),
    ("Task1306", "Diagnostic Replay Trades", "Run policy replay with inherited exits and explicit diagnostic authority"),
    ("Task1307", "Diagnostic Equity Curves", "Build monthly equity curves for policy variants"),
    ("Task1308", "Policy Metrics", "Compare against Task1228 and QQQ without acceptance claims"),
    ("Task1309", "Layer Gap Ledger", "Record what remains missing before true candidate replacement"),
    ("Task1310", "Acceptance Gate", "Keep NOT_ACCEPTED and real-capital forbidden unless formal acceptance is later met"),
    ("Task1311", "Artifact Manifest", "Hash and list produced artifacts"),
    ("Task1312", "Validation Script", "Validate row counts, no outcome assignment, and status wording"),
    ("Task1313", "Unit Test", "Add regression tests for output contracts"),
    ("Task1314", "Operating State Update", "Update project state with concise current result"),
    ("Task1315", "Registry Update", "Append active diagnostic task rows"),
    ("Task1316", "Expert Audit Capture", "Capture GPT review as advisory-only, not source-of-truth"),
    ("Task1317", "Closeout", "Close task as diagnostic-only with next candidate-expansion action"),
]

EXPERT_AUDIT_FINDINGS = [
    (
        "source_interpretation_audit",
        "L1 matched_pattern alone is insufficient",
        "future extractor must bind section speaker_or_counterparty event_verb materiality locator and raw_hash",
        "open_gap",
    ),
    (
        "source_interpretation_audit",
        "L2 validated growth is too broad unless contract plus management plus market_or_policy are jointly present",
        "keep current bucket diagnostic and add stricter full_candidate extractor pass before promotion",
        "open_gap",
    ),
    (
        "source_interpretation_audit",
        "L3 relation edges should be evidence_id based not only source_family templates",
        "next pass must emit evidence_id relation edges for reinforces weakens invalidates and source_gap_for",
        "open_gap",
    ),
    (
        "trader_quant_audit",
        "main alpha bottleneck is L4 replacement not another L5 size overlay",
        "extend multisource features to all 3100 candidates so weak selected rows can be replaced inside the same decision cohort",
        "open_gap",
    ),
    (
        "trader_quant_audit",
        "hard survival events may cap or cash but soft watch should not automatically force exit",
        "current implementation uses cap and sizing haircut rather than hard sell",
        "implemented",
    ),
    (
        "trader_quant_audit",
        "validated growth can be full size but policy-only company-source gaps must be capped",
        "current L5 multipliers cap policy gap and incomplete watch routes",
        "implemented",
    ),
    (
        "backend_validation_audit",
        "PASS is not acceptance and replay is diagnostic only",
        "validator enforces NOT_ACCEPTED DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY and FORBIDDEN",
        "implemented",
    ),
    (
        "backend_validation_audit",
        "post-entry price may appear only inside replay not L0-L4 assignment",
        "validator checks assignment_uses_future_outcome flags and policy specs separate replay fields",
        "implemented",
    ),
    (
        "backend_validation_audit",
        "report must keep layer gaps visible rather than hide blockers",
        "gap ledger records candidate replacement analyst expectation dynamic exit source locator and evidence-edge blockers",
        "implemented",
    ),
]

LAYER_RULES = [
    ("L0", "source_and_tradability_gate", "entry_allowed_only_if_price_and_prior_known_source_exist", "missing_raw_source_reported_not_negative"),
    ("L0", "pit_universe_boundary", "selected_slot5_only_until_full_candidate_sources_are_attached", "no_exchange_pit_claim"),
    ("L1", "source_quality", "specific_management_or_validated_contract_increases_evidence_quality", "promotional_generic_text_does_not_become_high_conviction"),
    ("L1", "source_family_count", "independent_source_families_raise_confidence", "missing_analyst_vendor_feed_not_a_short_signal"),
    ("L2", "economic_meaning", "validated_revenue_or_market_confirmed_growth_raises_conviction", "terminal_distress_without_current_materiality_is_watch_not_auto_exit"),
    ("L2", "uncertainty", "incomplete_or_watch_state_reduces_position_until confirmed", "do_not_fill_unknowns_with_defaults_that_imply_negative"),
    ("L3", "relation_action", "policy_plus_market_acceptance_reinforces_theme", "theme_policy_without_company_source_is capped"),
    ("L3", "contradiction_action", "survival_watch_or weak_contract caps conviction", "no hard veto without source-backed invalidation"),
    ("L4", "rank_route", "combine original rank with conviction and risk scores", "do_not_use_future_return_or_pnl"),
    ("L5", "sizing_hold_rule", "size_up confirmed growth and size_down uncertainty; preserve inherited exit for diagnostics", "no_live_or_real_capital_authority"),
]

POLICY_DEFS = {
    "l0_l5_shadow_slot5_v1": {
        "intent": "control_same_as_multisource_shadow",
        "base_multiplier": "shadow",
        "conviction_tilt": 0.0,
        "risk_haircut": 0.0,
        "weak_cash_threshold": None,
        "max_multiplier": 1.0,
    },
    "l0_l5_conviction_tilt_slot5_v1": {
        "intent": "tilt_size_by_L1_L4_trading_judgment",
        "base_multiplier": "source_complete",
        "conviction_tilt": 0.18,
        "risk_haircut": 0.12,
        "weak_cash_threshold": None,
        "max_multiplier": 1.15,
    },
    "l0_l5_quality_hurdle_slot5_v1": {
        "intent": "reduce_incomplete_watch_rows_but_do_not_hard_veto_growth_rows",
        "base_multiplier": "source_complete",
        "conviction_tilt": 0.12,
        "risk_haircut": 0.18,
        "weak_cash_threshold": -0.35,
        "max_multiplier": 1.05,
    },
    "l0_l5_trader_rulebook_slot5_v1": {
        "intent": "balanced_trader_rulebook_confirmed_growth_up_incomplete_down",
        "base_multiplier": "source_complete",
        "conviction_tilt": 0.22,
        "risk_haircut": 0.18,
        "weak_cash_threshold": -0.55,
        "max_multiplier": 1.20,
    },
}

SOURCE_COMPLETE_BASE = {
    "hard_survival_review_required": 0.25,
    "validated_growth_multisource_confirmed": 1.00,
    "revenue_validation_market_confirmed": 0.90,
    "management_narrative_market_confirmed": 0.85,
    "policy_market_confirmed_but_company_source_gap": 0.70,
    "multisource_incomplete_or_watch": 0.50,
}


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


def cagr(start_value: float, end_value: float, start: date, end: date) -> float:
    years = (end - start).days / 365.25
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1.0 / years) - 1.0


def max_drawdown(values: list[float]) -> float:
    peak = -float("inf")
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def base_multiplier(policy_base: str, interpretation: str, inherited_multiplier: float) -> float:
    if policy_base == "shadow":
        return inherited_multiplier
    return inherited_multiplier * SOURCE_COMPLETE_BASE.get(interpretation, 1.0)


def build_source_context() -> list[dict[str, object]]:
    rows = []
    expert_roles = [
        "distressed_growth_trader",
        "institutional_quant_risk",
        "backend_validation_engineer",
        "policy_macro_specialist",
        "sector_theme_specialist",
    ]
    for idx, source in enumerate(SOURCE_CONTEXT, 1):
        rows.append(
            {
                "task_id": "Task1298",
                "source_context_id": f"SRCCTX1298-{idx:03d}",
                "expert_review_role": expert_roles[(idx - 1) % len(expert_roles)],
                "gpt_review_authority": "review_only_not_source_of_truth",
                **source,
                "authority": AUTHORITY,
            }
        )
    return rows


def build_plan() -> list[dict[str, object]]:
    return [
        {
            "task_id": task_id,
            "task_name": name,
            "implementation_goal": goal,
            "status": "implemented" if task_id not in {"Task1314", "Task1315"} else "implemented_by_this_run",
            "authority": AUTHORITY,
        }
        for task_id, name, goal in PLAN_ROWS
    ]


def build_layer_rules() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1299",
            "rule_id": f"L0L5RULE1299-{idx:03d}",
            "brain_layer": layer,
            "rule_name": name,
            "positive_action": action,
            "guardrail": guardrail,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (layer, name, action, guardrail) in enumerate(LAYER_RULES, 1)
    ]


def build_expert_audit_findings() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1316",
            "audit_finding_id": f"AUDIT1316-{idx:03d}",
            "audit_role": role,
            "finding": finding,
            "implementation_response": response,
            "resolution_state": state,
            "gpt_review_authority": "review_only_not_source_of_truth",
            "authority": AUTHORITY,
        }
        for idx, (role, finding, response, state) in enumerate(EXPERT_AUDIT_FINDINGS, 1)
    ]


def build_l0_gate(base_specs: list[dict[str, str]], readiness: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for spec in base_specs:
        ready = readiness[spec["selection_id"]]
        coverage_count = sum(
            int(ready[field])
            for field in [
                "has_sec_survival",
                "has_policy_shadow",
                "has_market_acceptance",
                "has_ir_ceo_exhibit",
                "has_contract_exhibit",
                "has_analyst_pit",
            ]
        )
        has_minimum = int(ready["has_sec_survival"]) and int(ready["has_market_acceptance"])
        rows.append(
            {
                "task_id": "Task1300",
                "selection_id": spec["selection_id"],
                "symbol": spec["symbol"],
                "decision_asof_ts": spec["decision_asof_ts"],
                "coverage_count": coverage_count,
                "backtest_readiness_state": ready["backtest_readiness_state"],
                "l0_shadow_rule_state": "l0_shadow_usable" if has_minimum else "l0_source_gap",
                "candidate_replacement_allowed": "0",
                "candidate_replacement_reason": "full_3100_candidate_multisource_extractors_not_attached",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_l1_quality(base_specs: list[dict[str, str]], l2: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for spec in base_specs:
        row = l2[spec["selection_id"]]
        source_family_count = 0
        source_family_count += 1 if row["sec_survival_state"] else 0
        source_family_count += 1 if row["management_narrative_state"] not in {"", "no_management_narrative"} else 0
        source_family_count += 1 if row["contract_revenue_state"] not in {"", "no_contract_evidence"} else 0
        source_family_count += 1 if row["policy_catalyst_state"] != "no_theme_policy_shadow_event" else 0
        source_family_count += 1 if row["market_acceptance_state"] else 0
        source_family_count += 1 if row["analyst_expectation_state"] != "vendor_required_gap" else 0

        specificity = 0.0
        if row["management_narrative_state"] == "specific_management_narrative":
            specificity += 0.35
        elif row["management_narrative_state"] == "limited_management_narrative":
            specificity += 0.10
        elif row["management_narrative_state"] == "promotional_low_specificity":
            specificity -= 0.15
        if row["contract_revenue_state"] == "validated_contract_or_order":
            specificity += 0.40
        elif row["contract_revenue_state"] == "contract_watch_needs_materiality":
            specificity += 0.05
        elif row["contract_revenue_state"] == "weak_nonbinding_or_pilot":
            specificity -= 0.25
        if row["policy_catalyst_state"] == "theme_policy_shadow_attention":
            specificity += 0.08
        if row["market_acceptance_state"] == "market_acceptance_high_vol_upside":
            specificity += 0.18
        elif row["market_acceptance_state"] == "market_acceptance_confirmed":
            specificity += 0.10
        if row["sec_survival_state"] == "terminal_distress":
            specificity -= 0.45
        elif row["sec_survival_state"] == "watch_distress":
            specificity -= 0.15

        quality = max(-1.0, min(1.0, 0.08 * source_family_count + specificity))
        rows.append(
            {
                "task_id": "Task1301",
                "selection_id": spec["selection_id"],
                "symbol": spec["symbol"],
                "decision_asof_ts": spec["decision_asof_ts"],
                "source_family_count": source_family_count,
                "l1_source_quality_score": round(quality, 6),
                "management_narrative_state": row["management_narrative_state"],
                "contract_revenue_state": row["contract_revenue_state"],
                "market_acceptance_state": row["market_acceptance_state"],
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_l2_judgment(
    base_specs: list[dict[str, str]],
    l2: dict[str, dict[str, str]],
    l1_quality: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    rows = []
    for spec in base_specs:
        interp = l2[spec["selection_id"]]["enhanced_composite_interpretation"]
        conviction = to_float(l1_quality[spec["selection_id"]]["l1_source_quality_score"])
        risk = 0.0
        uncertainty = 0.0
        if interp == "validated_growth_multisource_confirmed":
            conviction += 0.45
        elif interp == "revenue_validation_market_confirmed":
            conviction += 0.25
        elif interp == "management_narrative_market_confirmed":
            conviction += 0.12
            uncertainty += 0.05
        elif interp == "policy_market_confirmed_but_company_source_gap":
            conviction += 0.05
            uncertainty += 0.25
        elif interp == "multisource_incomplete_or_watch":
            conviction -= 0.15
            uncertainty += 0.35
        elif interp == "hard_survival_review_required":
            conviction -= 0.25
            risk += 0.45
            uncertainty += 0.20

        if l2[spec["selection_id"]]["sec_survival_state"] == "terminal_distress":
            risk += 0.40
        elif l2[spec["selection_id"]]["sec_survival_state"] == "watch_distress":
            risk += 0.12

        conviction = max(-1.0, min(1.0, conviction))
        risk = max(0.0, min(1.0, risk))
        uncertainty = max(0.0, min(1.0, uncertainty))
        trading_judgment_score = conviction - 0.65 * risk - 0.35 * uncertainty
        if trading_judgment_score >= 0.55:
            route = "increase_or_hold_full_size"
        elif trading_judgment_score >= 0.15:
            route = "hold_standard_size"
        elif trading_judgment_score >= -0.25:
            route = "haircut_size_watch"
        else:
            route = "cash_or_micro_size_until_confirmed"

        rows.append(
            {
                "task_id": "Task1302",
                "selection_id": spec["selection_id"],
                "symbol": spec["symbol"],
                "decision_asof_ts": spec["decision_asof_ts"],
                "enhanced_composite_interpretation": interp,
                "l2_conviction_score": round(conviction, 6),
                "l2_risk_score": round(risk, 6),
                "l2_uncertainty_score": round(uncertainty, 6),
                "l2_trading_judgment_score": round(trading_judgment_score, 6),
                "l2_trading_route": route,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_l3_edges(base_specs: list[dict[str, str]], l2: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    edges = []
    families = [
        ("sec_survival_state", "sec_survival"),
        ("management_narrative_state", "ir_ceo_earnings_call"),
        ("contract_revenue_state", "contract_orders_customer"),
        ("policy_catalyst_state", "policy_news_catalyst"),
        ("market_acceptance_state", "market_price_volume"),
        ("analyst_expectation_state", "analyst_institution"),
    ]
    for spec in base_specs:
        row = l2[spec["selection_id"]]
        for field, family in families:
            state = row[field]
            action = "no_change"
            if state in {"validated_contract_or_order", "specific_management_narrative", "market_acceptance_high_vol_upside"}:
                action = "reinforce"
            elif state in {"contract_watch_needs_materiality", "limited_management_narrative", "theme_policy_shadow_attention"}:
                action = "conditional_reinforce"
            elif state in {"weak_nonbinding_or_pilot", "promotional_low_specificity", "watch_distress"}:
                action = "haircut"
            elif state == "terminal_distress":
                action = "cap_or_cash"
            elif state == "vendor_required_gap":
                action = "gap_no_negative_inference"
            edges.append(
                {
                    "task_id": "Task1303",
                    "l3_rule_edge_id": f"L3RULE1303-{len(edges)+1:07d}",
                    "selection_id": spec["selection_id"],
                    "symbol": spec["symbol"],
                    "decision_asof_ts": spec["decision_asof_ts"],
                    "source_family": family,
                    "source_state": state,
                    "relation_action": action,
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return edges


def build_l4_routes(
    base_specs: list[dict[str, str]],
    l2_judgment: dict[str, dict[str, object]],
    l0_gate: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    rows = []
    by_decision: dict[str, list[dict[str, str]]] = defaultdict(list)
    for spec in base_specs:
        by_decision[spec["decision_asof_ts"]].append(spec)
    for decision_ts, specs in sorted(by_decision.items()):
        tmp = []
        for spec in specs:
            rank_score = (6 - int(spec["candidate_rank"])) / 5.0
            judgment = to_float(l2_judgment[spec["selection_id"]]["l2_trading_judgment_score"])
            coverage = to_float(l0_gate[spec["selection_id"]]["coverage_count"]) / 6.0
            route_score = 0.45 * rank_score + 0.40 * judgment + 0.15 * coverage
            tmp.append((route_score, spec))
        tmp.sort(key=lambda item: (-item[0], int(item[1]["candidate_rank"]), item[1]["symbol"]))
        for route_rank, (route_score, spec) in enumerate(tmp, 1):
            rows.append(
                {
                    "task_id": "Task1304",
                    "selection_id": spec["selection_id"],
                    "trade_spec_id": spec["trade_spec_id"],
                    "symbol": spec["symbol"],
                    "decision_asof_ts": decision_ts,
                    "original_candidate_rank": spec["candidate_rank"],
                    "l4_route_rank_within_slot5": route_rank,
                    "l4_route_score": round(route_score, 6),
                    "l4_replacement_allowed": "0",
                    "l4_replacement_blocker": "enhanced_multisource_features_exist_only_for_selected_310_not_all_3100_candidates",
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build_policy_specs(
    base_specs: list[dict[str, str]],
    l2: dict[str, dict[str, str]],
    l2_judgment: dict[str, dict[str, object]],
    l4_routes: dict[str, dict[str, object]],
    readiness: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    specs = []
    for policy_id, policy in POLICY_DEFS.items():
        for spec in sorted(base_specs, key=lambda item: (item["decision_asof_ts"], int(item["candidate_rank"]))):
            interp = l2[spec["selection_id"]]["enhanced_composite_interpretation"]
            judgment = to_float(l2_judgment[spec["selection_id"]]["l2_trading_judgment_score"])
            risk = to_float(l2_judgment[spec["selection_id"]]["l2_risk_score"])
            base = base_multiplier(str(policy["base_multiplier"]), interp, to_float(spec["position_multiplier"], 1.0))
            multiplier = base
            multiplier *= 1.0 + to_float(policy["conviction_tilt"]) * max(0.0, judgment)
            multiplier *= 1.0 - to_float(policy["risk_haircut"]) * max(0.0, risk)
            threshold = policy["weak_cash_threshold"]
            if threshold is not None and judgment < float(threshold):
                multiplier = min(multiplier, 0.15)
            multiplier = max(0.0, min(to_float(policy["max_multiplier"], 1.0), multiplier))
            if policy_id == "l0_l5_shadow_slot5_v1":
                exit_reason = spec["exit_reason"]
            else:
                exit_reason = f"l0_l5_trading_rule:{spec['exit_reason']}"
            specs.append(
                {
                    "task_id": "Task1305",
                    "policy_spec_id": f"L0L5SPEC1305-{len(specs)+1:07d}",
                    "policy_variant_id": policy_id,
                    "policy_intent": policy["intent"],
                    "selection_id": spec["selection_id"],
                    "trade_spec_id": spec["trade_spec_id"],
                    "decision_asof_ts": spec["decision_asof_ts"],
                    "symbol": spec["symbol"],
                    "candidate_rank": spec["candidate_rank"],
                    "l4_route_rank_within_slot5": l4_routes[spec["selection_id"]]["l4_route_rank_within_slot5"],
                    "derived_theme": spec["derived_theme"],
                    "enhanced_composite_interpretation": interp,
                    "backtest_readiness_state": readiness[spec["selection_id"]]["backtest_readiness_state"],
                    "l2_trading_judgment_score": l2_judgment[spec["selection_id"]]["l2_trading_judgment_score"],
                    "entry_date": spec["entry_date"],
                    "entry_price": spec["entry_price"],
                    "scheduled_exit_date": spec["scheduled_exit_date"],
                    "scheduled_exit_price": spec["scheduled_exit_price"],
                    "adjusted_exit_date": spec["adjusted_exit_date"],
                    "adjusted_exit_price": spec["adjusted_exit_price"],
                    "exit_reason": exit_reason,
                    "base_position_multiplier": base,
                    "l0_l5_position_multiplier": round(multiplier, 6),
                    "position_multiplier": round(multiplier, 6),
                    "selection_promoted": "0",
                    "assignment_uses_future_outcome": "0",
                    "exit_uses_post_entry_price_path": "1",
                    "authority": AUTHORITY,
                }
            )
    return specs


def run_replay(specs: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    trades = []
    equity = []
    specs_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for spec in specs:
        specs_by_policy[str(spec["policy_variant_id"])].append(spec)
    for policy_id, policy_specs in sorted(specs_by_policy.items()):
        by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
        for spec in policy_specs:
            by_decision[str(spec["decision_asof_ts"])].append(spec)
        capital = INITIAL_CAPITAL
        for decision_ts, items in sorted(by_decision.items()):
            base_slot = capital / 5.0
            invested = 0.0
            period_pnl = 0.0
            new_capital = capital
            for item in sorted(items, key=lambda row: int(str(row["candidate_rank"]))):
                allocation = base_slot * to_float(item["position_multiplier"])
                invested += allocation
                entry = to_float(item["entry_price"])
                exit_ = to_float(item["adjusted_exit_price"])
                net_return = exit_ / entry - 1.0 - ROUND_TRIP_COST_BPS / 10000.0 if allocation > 0 and entry > 0 else 0.0
                pnl = allocation * net_return
                period_pnl += pnl
                new_capital += pnl
                trades.append(
                    {
                        "task_id": "Task1306",
                        "trade_id": f"L0L5TRADE1306-{len(trades)+1:07d}",
                        **item,
                        "capital_allocated": round(allocation, 4),
                        "net_return": round(net_return, 8),
                        "pnl": round(pnl, 4),
                        "authority": AUTHORITY,
                    }
                )
            cash_weight = max(0.0, 1.0 - invested / capital) if capital > 0 else 0.0
            period_return = new_capital / capital - 1.0 if capital > 0 else 0.0
            capital = max(new_capital, 0.01)
            equity.append(
                {
                    "task_id": "Task1307",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_return": round(period_return, 8),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "cash_weight_after_routing": round(cash_weight, 6),
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    task1288_metrics = read_csv(TASK1288 / "task1292_replay_metrics.csv")
    task1228_metric = read_csv(TASK1228 / "task1234_replay_metrics.csv")[0]
    base_metrics = read_csv(TASK1201 / "task1207_replay_metrics.csv")
    base_slot5 = next(row for row in base_metrics if row["policy_variant_id"] == "l0_l3_slot5_v1")
    source_complete = next(row for row in task1288_metrics if row["policy_variant_id"] == "multisource_source_complete_slot5_v1")
    trades_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trades_by_policy[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    rows = []
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = datetime.fromisoformat(str(eq_rows[0]["decision_asof_ts"]).replace("Z", "+00:00")).date()
        end = max(datetime.fromisoformat(str(row["adjusted_exit_date"])).date() for row in tr_rows)
        executed = [row for row in tr_rows if to_float(row["capital_allocated"]) > 0]
        rows.append(
            {
                "task_id": "Task1308",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr(INITIAL_CAPITAL, final, start, end), 6),
                "max_drawdown": round(max_drawdown(values), 6),
                "trade_count": len(executed),
                "task1228_final_equity": task1228_metric["final_equity"],
                "task1228_delta": round(final - float(task1228_metric["final_equity"]), 4),
                "task1288_best_final_equity": source_complete["final_equity"],
                "task1288_best_delta": round(final - float(source_complete["final_equity"]), 4),
                "beats_task1228": "1" if final > float(task1228_metric["final_equity"]) else "0",
                "beats_task1288_best": "1" if final > float(source_complete["final_equity"]) else "0",
                "benchmark_symbol": base_slot5["benchmark_symbol"],
                "benchmark_final_equity": base_slot5["benchmark_final_equity"],
                "benchmark_cagr": base_slot5["benchmark_cagr"],
                "beats_benchmark": "1" if final > float(base_slot5["benchmark_final_equity"]) else "0",
                "target_cagr_30pct_met": "1" if cagr(INITIAL_CAPITAL, final, start, end) >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if max_drawdown(values) >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_gap_ledger(base_specs: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1309",
            "gap_id": "GAP1309-001",
            "gap_area": "candidate_replacement",
            "current_state": f"{len(base_specs)} selected slot5 rows have enhanced multisource features",
            "required_state": "all 3100 candidate trade specs need L0-L3 multisource extractor attachment",
            "why_it_matters": "without this, L5 can resize current picks but cannot pick better alternatives",
            "next_task": "extend source extractors from selected 310 to full candidate pool",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1309",
            "gap_id": "GAP1309-002",
            "gap_area": "analyst_expectations",
            "current_state": "analyst_expectation_state is vendor_required_gap",
            "required_state": "PIT analyst revision and estimate change feed",
            "why_it_matters": "institutional expectation reset is central to entry timing and exit timing",
            "next_task": "attach vendor/API PIT analyst feed or keep explicit gap",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1309",
            "gap_id": "GAP1309-003",
            "gap_area": "exit_logic",
            "current_state": "replay inherits scheduled Task1228 exits",
            "required_state": "source-backed dynamic hold/sell rule with post-entry source receipt timestamps",
            "why_it_matters": "current brain sizes positions better than it exits them",
            "next_task": "build post-entry as-of source receipt and dynamic exit simulation",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1309",
            "gap_id": "GAP1309-004",
            "gap_area": "l1_source_locator",
            "current_state": "selected-row extractor states are available but not every L1 decision row has speaker counterparty locator materiality and raw hash exposed in this task",
            "required_state": "each evidence row carries available_ts source_id document_id section locator excerpt_hash and materiality fields",
            "why_it_matters": "without locator-grade evidence the brain can overcount generic exhibit language",
            "next_task": "promote extractor evidence rows into locator-grade L1 bindings for every candidate",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1309",
            "gap_id": "GAP1309-005",
            "gap_area": "l3_evidence_edges",
            "current_state": "this task emits state-based relation actions for 310 selected rows",
            "required_state": "L3 edges must reference evidence_id and relation mechanism for reinforces weakens invalidates and source_gap_for",
            "why_it_matters": "template edges are useful diagnostics but are not yet a trader-grade relationship graph",
            "next_task": "rebuild L3 from evidence_id level source bindings after full candidate extraction",
            "authority": AUTHORITY,
        },
    ]


def build_acceptance_gate(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    return [
        {
            "task_id": "Task1310",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "target_cagr_30pct_met": best["target_cagr_30pct_met"],
            "target_mdd_minus30pct_met": best["target_mdd_minus30pct_met"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "diagnostic_only_not_accepted",
            "next_action": "extend_multisource_extractors_to_full_candidate_pool_before_true_replacement",
            "authority": AUTHORITY,
        }
    ]


def write_report(metrics: list[dict[str, object]], gate: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    report = f"""# Task1298-1317 L0-L5 Trading Rule Strengthening

## Decision Summary

- Verdict: `diagnostic_l0_l5_trading_rules_implemented_not_accepted`.
- Best policy: `{best['policy_variant_id']}`.
- Best final equity: {best['final_equity']}.
- Best CAGR: {best['cagr']}.
- Best MDD: {best['max_drawdown']}.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: L0-L5 rules now convert source quality into trading judgment, rank routes, and L5 sizing.
- Next action: extend multisource extractors from selected 310 rows to all 3100 candidate rows before true candidate replacement.

## Quant Expert Report

Data source and readiness:

- SEC EDGAR submission and exhibit evidence remains the main company source.
- Federal Register policy evidence and market price/volume acceptance remain attached as shadow source families.
- Analyst PIT source and full exchange-listed PIT universe remain explicit gaps.

Exact join keys:

- `selection_id`
- `trade_spec_id`
- `decision_asof_ts`
- `symbol`

Leakage audit:

- Assignment uses L0 readiness, L1 source-quality states, L2 interpretation states, L3 relation actions, and original candidate rank.
- Assignment does not use future return, PnL, labels, adjusted exit price, or post-entry price path.
- Post-entry prices are used only by the inherited diagnostic replay engine.

Policy metrics:

| Policy | Final | CAGR | MDD | Beats Task1288 Best | Beats QQQ |
| --- | ---: | ---: | ---: | ---: | ---: |
"""
    for row in sorted(metrics, key=lambda item: str(item["policy_variant_id"])):
        report += (
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | "
            f"{row['max_drawdown']} | {row['beats_task1288_best']} | {row['beats_benchmark']} |\n"
        )
    report += f"""
Remaining blockers:

- Full candidate replacement is still blocked because enhanced multisource extractors cover selected slot5 rows, not the full 3100-candidate pool.
- Analyst expectation PIT feed is still absent.
- Dynamic sell/hold rules need post-entry source receipt timestamps.

## No-Background Decision-Maker Report

We strengthened the brain from source evidence to actual trading rules.

The system now says:

1. Strong source + market confirmation means larger or normal size.
2. Weak/incomplete evidence means smaller size or cash.
3. Survival-risk evidence caps size instead of blindly buying.
4. It still cannot choose a better replacement outside the current selected five until every candidate has the same source extraction.

This does not approve the strategy.

## Artifact Manifest

- `task1298_expert_source_context.csv`
- `task1299_l0_l5_strengthening_plan.csv`
- `task1299_l0_l5_layer_rulebook.csv`
- `task1300_l0_coverage_gate.csv`
- `task1301_l1_signal_quality_scores.csv`
- `task1302_l2_trading_judgment_scores.csv`
- `task1303_l3_rule_action_edges.csv`
- `task1304_l4_rank_route_panel.csv`
- `task1305_l5_rule_policy_specs.csv`
- `task1306_replay_trades.csv`
- `task1307_replay_equity.csv`
- `task1308_replay_metrics.csv`
- `task1309_layer_gap_ledger.csv`
- `task1310_acceptance_gate.csv`
- `task1316_expert_audit_findings.csv`
- `task1317_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1298_1317_l0_l5_trading_rule_strengthening_validate.py`
- `python -m unittest tests.test_trader_brain_1298_1317_l0_l5_trading_rule_strengthening`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1298_1317_l0_l5_trading_rule_strengthening.md").write_text(report, encoding="utf-8")
    decision = [
        {
            "task_id": "Task1317",
            "verdict": "diagnostic_l0_l5_trading_rules_implemented_not_accepted",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    write_csv(REPORT_DIR / "task_1298_1317_decision.csv", decision)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    base_specs = read_csv(TASK1228 / "task1233_policy_specs.csv")
    l2 = {row["selection_id"]: row for row in read_csv(TASK1268 / "task1274_enhanced_l2_multisource_interpretation.csv")}
    readiness = {row["selection_id"]: row for row in read_csv(TASK1268 / "task1276_backtest_readiness_panel.csv")}

    source_context = build_source_context()
    expert_audit_findings = build_expert_audit_findings()
    plan = build_plan()
    layer_rules = build_layer_rules()
    l0_gate_rows = build_l0_gate(base_specs, readiness)
    l0_gate = {row["selection_id"]: row for row in l0_gate_rows}
    l1_quality_rows = build_l1_quality(base_specs, l2)
    l1_quality = {row["selection_id"]: row for row in l1_quality_rows}
    l2_judgment_rows = build_l2_judgment(base_specs, l2, l1_quality)
    l2_judgment = {row["selection_id"]: row for row in l2_judgment_rows}
    l3_edges = build_l3_edges(base_specs, l2)
    l4_route_rows = build_l4_routes(base_specs, l2_judgment, l0_gate)
    l4_routes = {row["selection_id"]: row for row in l4_route_rows}
    policy_specs = build_policy_specs(base_specs, l2, l2_judgment, l4_routes, readiness)
    trades, equity = run_replay(policy_specs)
    metrics = build_metrics(trades, equity)
    gap_ledger = build_gap_ledger(base_specs)
    gate = build_acceptance_gate(metrics)
    closeout = [
        {
            "task_id": "Task1317",
            "closeout_state": "complete_diagnostic_only",
            "best_policy_variant_id": gate[0]["best_policy_variant_id"],
            "best_final_equity": gate[0]["best_final_equity"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "required_next_action": "extend_multisource_extractors_to_full_candidate_pool",
            "authority": AUTHORITY,
        }
    ]

    write_csv(OUT_DIR / "task1298_expert_source_context.csv", source_context)
    write_csv(OUT_DIR / "task1316_expert_audit_findings.csv", expert_audit_findings)
    write_csv(OUT_DIR / "task1299_l0_l5_strengthening_plan.csv", plan)
    write_csv(OUT_DIR / "task1299_l0_l5_layer_rulebook.csv", layer_rules)
    write_csv(OUT_DIR / "task1300_l0_coverage_gate.csv", l0_gate_rows)
    write_csv(OUT_DIR / "task1301_l1_signal_quality_scores.csv", l1_quality_rows)
    write_csv(OUT_DIR / "task1302_l2_trading_judgment_scores.csv", l2_judgment_rows)
    write_csv(OUT_DIR / "task1303_l3_rule_action_edges.csv", l3_edges)
    write_csv(OUT_DIR / "task1304_l4_rank_route_panel.csv", l4_route_rows)
    write_csv(OUT_DIR / "task1305_l5_rule_policy_specs.csv", policy_specs)
    write_csv(OUT_DIR / "task1306_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1307_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1308_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1309_layer_gap_ledger.csv", gap_ledger)
    write_csv(OUT_DIR / "task1310_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1317_closeout.csv", closeout)
    write_json(OUT_DIR / "task1317_closeout.json", closeout[0])
    write_report(metrics, gate)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")

    print(json.dumps(gate[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
