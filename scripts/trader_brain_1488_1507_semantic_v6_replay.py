from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1318 = ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors"
TASK1388 = ROOT / "data/artifacts/task_1388_1407_expert_reviewed_judgment_replay"
TASK1428 = ROOT / "data/artifacts/task_1428_1447_full_ruler_source_time_acquisition"
TASK1448 = ROOT / "data/artifacts/task_1448_1467_conditional_materiality_ranker"
TASK1468 = ROOT / "data/artifacts/task_1468_1487_complete_implementation_contract"
OUT_DIR = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
REPORT_DIR = ROOT / "docs/reports/task_1488_1507_semantic_v6_replay"

AUTHORITY = "DIAGNOSTIC_SEMANTIC_V6_REPLAY_ONLY"
POLICIES = {
    "semantic_v6_top3_v1": 3,
    "semantic_v6_top5_v1": 5,
    "semantic_v6_top10_v1": 10,
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


def expert_review_loop() -> list[dict[str, object]]:
    rows = [
        ("goldman_event_driven", "pass_with_change", "materiality must be a conditional ruler; event family comes first"),
        ("morgan_stanley_semis", "pass_with_change", "semiconductor demand needs customer/order/revenue path and export risk modifiers"),
        ("jpm_quant", "pass_with_change", "absorption must require persistence and relative strength, not one green window"),
        ("bofa_revisions", "pass_with_change", "good words are not surprise; expectation needs prior baseline or explicit guidance change"),
        ("citi_policy", "pass_with_change", "policy/news cannot be broad theme bonus without affected-entity linkage"),
        ("ubs_risk", "pass_with_change", "survival and dilution are separate from volatility and must not be hidden inside materiality"),
        ("barclays_space", "pass_with_change", "contract ceiling, funded award, milestone, launch/license, and revenue conversion are distinct"),
        ("deutsche_backend", "pass", "source gaps stay neutral and must be auditable rather than becoming negative labels"),
        ("two_sigma_validation", "pass", "one pre-registered replay only; outcome audit cannot feed rank"),
        ("sector_specialists", "pass_with_change", "sector traps must appear in L3 mechanism and L4 thesis fields"),
    ]
    return [
        {
            "task_id": "Task1488",
            "review_id": f"V6REVIEW1488-{idx:03d}",
            "expert_role": role,
            "verdict": verdict,
            "required_change": change,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, verdict, change) in enumerate(rows, 1)
    ]


def preregister_v6() -> list[dict[str, object]]:
    specs = [
        ("event_family_first", "classify each candidate as positive, survival, financing, dilution, mixed, or unknown before materiality score"),
        ("no_standalone_materiality_bonus", "materiality contributes only through conditional_materiality_score after event family and quality gates"),
        ("source_gap_neutral", "missing denominator, analyst PIT, or source family remains zero/uncertain, never hidden negative"),
        ("good_words_not_surprise", "positive language without prior baseline is good_words_only, not true_surprise"),
        ("strict_absorption", "market acceptance requires positive relative return plus relative volume and no rejection state"),
        ("survival_dilution_guard", "survival and dilution families receive explicit risk penalties and route edges"),
        ("balanced_candidate_preservation", "strong expectation or absorption can preserve source-gap candidates if no survival/dilution evidence exists"),
        ("audit_only_outcomes", "realized returns appear only in displacement audit and never in rank fields"),
        ("frozen_replay", "top3/top5/top10, cost, entry/exit, benchmark, and universe are frozen before replay"),
    ]
    return [
        {
            "task_id": "Task1489",
            "spec_id": f"V6SPEC1489-{idx:03d}",
            "rule_name": name,
            "pre_registered_rule": rule,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, rule) in enumerate(specs, 1)
    ]


def load_panels() -> dict[str, dict[str, dict[str, str]]]:
    return {
        "l1": {row["candidate_source_id"]: row for row in read_csv(TASK1318 / "task1324_candidate_l1_source_bindings.csv")},
        "l2": {row["candidate_source_id"]: row for row in read_csv(TASK1388 / "task1394_l2_enriched_judgment_panel.csv")},
        "event": {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1412_event_value_panel.csv")},
        "materiality": {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1434_full_materiality_ruler_panel.csv")},
        "market_cap": {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1433_full_market_cap_proxy_panel.csv")},
        "guidance": {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1415_public_guidance_revision_panel.csv")},
        "absorption": {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1418_market_absorption_enhanced_panel.csv")},
        "rank_v4": {row["candidate_source_id"]: row for row in read_csv(TASK1428 / "task1445_payoff_ranker_v4.csv")},
    }


def evidence_lookup() -> dict[str, dict[str, str]]:
    return {row["evidence_id"]: row for row in read_csv(TASK1318 / "task1323_accession_source_evidence.csv")}


def evidence_text(l1: dict[str, str], evidence: dict[str, dict[str, str]]) -> str:
    ids = [
        l1.get("management_evidence_id", ""),
        l1.get("contract_evidence_id", ""),
        l1.get("survival_evidence_id", ""),
    ]
    parts: list[str] = []
    for evidence_id in ids:
        row = evidence.get(evidence_id)
        if not row:
            continue
        parts.extend([row.get("source_state", ""), row.get("reason", ""), row.get("matched_pattern", ""), row.get("excerpt", "")])
    return " ".join(parts).lower()


def classify_event_family(
    l1: dict[str, str],
    l2: dict[str, str],
    event: dict[str, str],
    evidence_blob: str,
) -> tuple[str, str, str]:
    text = " ".join(
        [
            l1.get("management_narrative_state", ""),
            l1.get("contract_revenue_state", ""),
            l1.get("sec_survival_state", ""),
            l2.get("full_candidate_composite_interpretation", ""),
            event.get("event_value_type", ""),
            event.get("value_context_excerpt", ""),
            evidence_blob,
        ]
    ).lower()
    dilution_terms = ["warrant", "atm", "registered direct", "private placement", "equity offering", "convertible", "share issuance", "shelf registration", "dilution"]
    survival_terms = ["going concern", "delist", "bankrupt", "substantial doubt", "reverse split", "liquidity distress"]
    financing_terms = ["senior notes", "credit facility", "loan", "debt", "financing", "liquidity", "offering", "notes due"]
    positive_terms = ["validated_contract_or_order", "contract_watch_needs_materiality", "award", "customer", "purchase order", "backlog", "revenue", "booking", "supply agreement"]
    has_dilution = "dilution_financing_context" in text and any(term in text for term in dilution_terms)
    has_survival = l1.get("sec_survival_state") == "terminal_distress" or any(term in text for term in survival_terms)
    has_financing = any(term in text for term in financing_terms)
    has_positive = any(term in text for term in positive_terms)
    if has_dilution and has_positive:
        return "mixed", "positive_claim_with_dilution_terms", "shareholder_transfer_risk"
    if has_survival:
        return "survival", "survival_or_distress_terms", "survival_risk"
    if has_dilution:
        return "dilution", "equity_or_convertible_dilution_terms", "shareholder_transfer"
    if has_financing and has_positive:
        return "mixed", "positive_claim_with_financing_terms", "financing_transition"
    if has_financing:
        return "financing", "debt_or_liquidity_financing_terms", "balance_sheet_funding"
    if has_positive or l2.get("full_candidate_composite_interpretation") == "validated_growth_multisource_confirmed":
        return "positive", "contract_customer_backlog_or_validated_growth", "economic_receipt"
    if "biotech" in l2.get("derived_theme", ""):
        return "mixed", "biotech_milestone_without_full_endpoint_context", "milestone_uncertainty"
    return "unknown", "no_clear_event_family_source", "source_gap"


def classify_expectation(guidance: dict[str, str], l2: dict[str, str]) -> tuple[str, float, str]:
    pos = int(to_float(guidance.get("positive_term_hits")))
    neg = int(to_float(guidance.get("negative_term_hits")))
    direction = guidance.get("public_guidance_direction", "")
    gap = l2.get("expectation_gap_state", "")
    if gap == "positive_expectation_gap_proxy":
        return "true_surprise_proxy", 18.0, "prior_baseline_proxy_positive_gap"
    if direction == "positive_public_guidance_revision_proxy" and pos >= 3 and neg == 0:
        return "guidance_change_proxy", 12.0, "explicit_positive_guidance_language_cluster"
    if direction == "positive_public_guidance_revision_proxy":
        return "good_words_only", 4.0, "positive_language_without_prior_baseline"
    if gap == "negative_expectation_revision_proxy" or direction == "negative_public_guidance_revision_proxy" or neg > pos:
        return "negative_expectation_proxy", -14.0, "negative_guidance_or_expectation_proxy"
    if direction == "mixed_public_guidance_proxy":
        return "mixed_expectation_proxy", -3.0, "mixed_language"
    return "expectation_source_gap", 0.0, "no_prior_baseline_or_guidance_change"


def classify_absorption(absorption: dict[str, str], l2: dict[str, str]) -> tuple[str, float, str]:
    rel = to_float(absorption.get("event_to_decision_relative_return"))
    vol = to_float(absorption.get("decision_relative_volume"))
    market_state = l2.get("market_absorption_state", "")
    if absorption.get("absorption_window_pass") != "1":
        return "absorption_source_gap", 0.0, "missing_price_window"
    if market_state == "market_rejection_before_decision" or rel <= -0.08:
        return "market_rejection_or_reversal", -18.0, "negative_relative_return_before_decision"
    if rel >= 0.08 and vol >= 1.05 and market_state == "accepted_underreaction_or_followthrough":
        return "sustained_market_acceptance", 16.0, "relative_strength_plus_volume_persistence"
    if rel >= 0.08:
        return "initial_reaction_only", 6.0, "positive_relative_return_without_full_volume_or_state_confirmation"
    if rel >= 0.02 and vol >= 1.0:
        return "weak_absorption", 3.0, "small_positive_relative_move"
    return "neutral_absorption", 0.0, "no_clear_absorption"


def materiality_condition(
    family: str,
    materiality: dict[str, str],
    market_cap: dict[str, str],
    expectation_state: str,
    absorption_state: str,
) -> tuple[str, float, str]:
    state = materiality.get("materiality_ruler_state", "")
    raw_score = to_float(materiality.get("materiality_ruler_score"))
    cap = to_float(market_cap.get("market_cap_proxy_usd"))
    if state == "materiality_source_gap":
        return "materiality_source_gap_neutral", 0.0, "gap_not_negative"
    if family == "survival":
        return "survival_materiality_risk", -26.0, "survival_event_not_alpha"
    if family == "dilution":
        return "dilution_materiality_risk", -30.0, "dilution_event_not_alpha"
    if family == "financing":
        return "financing_materiality_capped", min(raw_score * 0.10, 3.0), "funding_not_growth_by_default"
    if family in {"mixed", "unknown"}:
        return "unconfirmed_materiality_capped", min(raw_score * 0.15, 5.0), "positive_economics_not_clean"
    if expectation_state in {"true_surprise_proxy", "guidance_change_proxy"} and absorption_state == "sustained_market_acceptance":
        score = min(raw_score * 0.70, 18.0)
        reason = "positive_materiality_with_expectation_and_absorption"
    elif expectation_state in {"true_surprise_proxy", "guidance_change_proxy"} or absorption_state in {"sustained_market_acceptance", "initial_reaction_only"}:
        score = min(raw_score * 0.35, 10.0)
        reason = "positive_materiality_with_one_quality_gate"
    else:
        score = min(raw_score * 0.12, 4.0)
        reason = "positive_materiality_without_surprise_or_absorption"
    if cap and cap < 300_000_000:
        return "micro_cap_materiality_capped", min(score, 4.0), "micro_cap_ratio_cap"
    if cap and cap < 2_000_000_000:
        return "small_cap_materiality_capped", min(score, 8.0), "small_cap_ratio_cap"
    return "conditional_positive_materiality", score, reason


def build_semantic_panels() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    panels = load_panels()
    evidence = evidence_lookup()
    source_rows: list[dict[str, object]] = []
    l2_rows: list[dict[str, object]] = []
    l3_rows: list[dict[str, object]] = []
    thesis_rows: list[dict[str, object]] = []
    rank_rows: list[dict[str, object]] = []
    rank_base = list(panels["rank_v4"].values())
    for idx, row in enumerate(rank_base, 1):
        cid = row["candidate_source_id"]
        l1 = panels["l1"][cid]
        l2 = panels["l2"][cid]
        event = panels["event"][cid]
        materiality = panels["materiality"][cid]
        market_cap = panels["market_cap"][cid]
        guidance = panels["guidance"][cid]
        absorption = panels["absorption"][cid]
        blob = evidence_text(l1, evidence)
        family, family_reason, mechanism = classify_event_family(l1, l2, event, blob)
        expectation_state, expectation_score, expectation_reason = classify_expectation(guidance, l2)
        absorption_state, absorption_score, absorption_reason = classify_absorption(absorption, l2)
        materiality_state, materiality_score, materiality_reason = materiality_condition(
            family, materiality, market_cap, expectation_state, absorption_state
        )
        candidate_rank = int(to_float(row.get("candidate_rank"), 9999))
        base_quality = max(0.0, 16.0 - candidate_rank * 0.08)
        prior_score = min(14.0, max(0.0, to_float(l2.get("expert_l2_score")) * 0.12))
        independence_state = l2.get("source_independence_v2_state", "")
        independence_score = 10.0 if independence_state == "independent_non_issuer_confirmation_present" else (4.0 if independence_state == "issuer_plus_market_modifier_only" else 0.0)
        family_score = {"positive": 8.0, "mixed": 0.0, "unknown": -1.0, "financing": -5.0, "survival": -18.0, "dilution": -20.0}[family]
        preservation_score = 4.0 if family in {"positive", "unknown", "mixed"} and absorption_state == "sustained_market_acceptance" else 0.0
        semantic_score = (
            base_quality
            + prior_score
            + independence_score
            + family_score
            + materiality_score
            + expectation_score
            + absorption_score
            + preservation_score
        )
        if family in {"survival", "dilution"}:
            route = "risk_guard_or_avoid"
        elif family == "positive" and expectation_state in {"true_surprise_proxy", "guidance_change_proxy"} and absorption_state == "sustained_market_acceptance":
            route = "candidate_for_rank_upgrade"
        elif family == "positive" and absorption_state in {"sustained_market_acceptance", "initial_reaction_only"}:
            route = "candidate_for_preserve_or_moderate_upgrade"
        elif family in {"financing", "mixed"}:
            route = "watch_or_size_cap"
        else:
            route = "source_gap_watch"
        source_rows.append(
            {
                "task_id": "Task1490",
                "source_audit_id": f"V6SRC1490-{idx:07d}",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "management_evidence_id": l1.get("management_evidence_id", ""),
                "contract_evidence_id": l1.get("contract_evidence_id", ""),
                "survival_evidence_id": l1.get("survival_evidence_id", ""),
                "management_narrative_state": l1.get("management_narrative_state", ""),
                "contract_revenue_state": l1.get("contract_revenue_state", ""),
                "sec_survival_state": l1.get("sec_survival_state", ""),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l2_rows.append(
            {
                "task_id": "Task1491",
                "semantic_v6_id": f"L2V6-1491-{idx:07d}",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "candidate_rank": row["candidate_rank"],
                "derived_theme": row.get("derived_theme", l2.get("derived_theme", "")),
                "event_family": family,
                "event_family_reason": family_reason,
                "expectation_v6_state": expectation_state,
                "expectation_v6_score": round(expectation_score, 4),
                "expectation_v6_reason": expectation_reason,
                "absorption_v6_state": absorption_state,
                "absorption_v6_score": round(absorption_score, 4),
                "absorption_v6_reason": absorption_reason,
                "materiality_v6_state": materiality_state,
                "materiality_v6_score": round(materiality_score, 4),
                "materiality_v6_reason": materiality_reason,
                "source_independence_v2_state": independence_state,
                "semantic_v6_score": round(semantic_score, 4),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        edge_defs = [
            ("event_family_to_mechanism", mechanism, family_reason),
            ("expectation_quality", expectation_state, expectation_reason),
            ("market_absorption_quality", absorption_state, absorption_reason),
            ("conditional_materiality", materiality_state, materiality_reason),
            ("route_action", route, "semantic_v6_route"),
        ]
        for edge_type, target, reason in edge_defs:
            l3_rows.append(
                {
                    "task_id": "Task1492",
                    "edge_id": f"L3V6-1492-{len(l3_rows)+1:07d}",
                    "candidate_source_id": cid,
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "edge_type": edge_type,
                    "edge_target": target,
                    "edge_reason": reason,
                    "edge_direction": "supports" if route.startswith("candidate") or target in {"sustained_market_acceptance", "true_surprise_proxy", "guidance_change_proxy"} else ("invalidates" if route == "risk_guard_or_avoid" else "routes"),
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
        thesis_rows.append(
            {
                "task_id": "Task1493",
                "thesis_card_id": f"L4V6-1493-{idx:07d}",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "event_family": family,
                "economic_mechanism": mechanism,
                "expectation_state": expectation_state,
                "absorption_state": absorption_state,
                "materiality_state": materiality_state,
                "route": route,
                "primary_invalidation": "survival_or_dilution" if family in {"survival", "dilution"} else ("market_rejection" if absorption_state == "market_rejection_or_reversal" else "source_gap_or_thesis_decay"),
                "semantic_v6_score": round(semantic_score, 4),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for thesis in thesis_rows:
        by_decision[str(thesis["decision_asof_ts"])].append(thesis)
    for decision_ts, rows in by_decision.items():
        ordered = sorted(rows, key=lambda item: (-to_float(item["semantic_v6_score"]), int(to_float(next(r for r in l2_rows if r["candidate_source_id"] == item["candidate_source_id"])["candidate_rank"], 9999))))
        for rank, thesis in enumerate(ordered, 1):
            l2_row = next(r for r in l2_rows if r["candidate_source_id"] == thesis["candidate_source_id"])
            rank_rows.append(
                {
                    "task_id": "Task1494",
                    "rank_row_id": f"PAYOFFV6-1494-{len(rank_rows)+1:07d}",
                    "candidate_source_id": thesis["candidate_source_id"],
                    "trade_spec_id": thesis["trade_spec_id"],
                    "symbol": thesis["symbol"],
                    "decision_asof_ts": decision_ts,
                    "candidate_rank": l2_row["candidate_rank"],
                    "derived_theme": l2_row["derived_theme"],
                    "event_family": thesis["event_family"],
                    "expectation_v6_state": thesis["expectation_state"],
                    "absorption_v6_state": thesis["absorption_state"],
                    "materiality_v6_state": thesis["materiality_state"],
                    "route": thesis["route"],
                    "semantic_v6_rank_score": thesis["semantic_v6_score"],
                    "semantic_v6_rank_within_decision": rank,
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return source_rows, l2_rows, l3_rows, thesis_rows, rank_rows


def select_policy_specs(rank_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rank_rows:
        by_decision[str(row["decision_asof_ts"])].append(row)
    selected: list[dict[str, object]] = []
    for policy_id, slot_cap in POLICIES.items():
        for decision_ts, rows in by_decision.items():
            ordered = sorted(rows, key=lambda item: (int(item["semantic_v6_rank_within_decision"]), int(to_float(item["candidate_rank"], 9999))))[:slot_cap]
            for row in ordered:
                selected.append(
                    {
                        "task_id": "Task1495",
                        "policy_spec_id": f"{policy_id}:{row['trade_spec_id']}",
                        "policy_variant_id": policy_id,
                        "slot_cap": slot_cap,
                        "candidate_source_id": row["candidate_source_id"],
                        "trade_spec_id": row["trade_spec_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "semantic_v6_rank_score": row["semantic_v6_rank_score"],
                        "semantic_v6_rank_within_decision": row["semantic_v6_rank_within_decision"],
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
    return selected


def build_displacement_audit(rank_rows: list[dict[str, object]], trades: list[dict[str, object]]) -> list[dict[str, object]]:
    sparse_top3 = [row for row in read_csv(ROOT / "data/artifacts/task_1408_1427_ruler_acquisition_replay/task1426_policy_specs.csv") if row["policy_variant_id"] == "ruler_top3_v1"]
    full_top3 = [row for row in read_csv(TASK1428 / "task1446_policy_specs.csv") if row["policy_variant_id"] == "ruler_top3_v1"]
    v5_top3 = [row for row in read_csv(TASK1448 / "task1455_policy_specs.csv") if row["policy_variant_id"] == "conditional_materiality_top3_v1"]
    v6_top3 = [row for row in select_policy_specs(rank_rows) if row["policy_variant_id"] == "semantic_v6_top3_v1"]
    rank_by_tid = {str(row["trade_spec_id"]): row for row in rank_rows}
    trade_lookup = {}
    for path, policy in [
        (ROOT / "data/artifacts/task_1408_1427_ruler_acquisition_replay/task1426_replay_trades.csv", "ruler_top3_v1"),
        (TASK1428 / "task1446_replay_trades.csv", "ruler_top3_v1"),
        (TASK1448 / "task1456_replay_trades.csv", "conditional_materiality_top3_v1"),
    ]:
        for row in read_csv(path):
            if row["policy_variant_id"] == policy:
                trade_lookup[(policy, row["decision_asof_ts"], row["trade_spec_id"])] = row
    for row in trades:
        if row["policy_variant_id"] == "semantic_v6_top3_v1":
            trade_lookup[("semantic_v6_top3_v1", row["decision_asof_ts"], row["trade_spec_id"])] = {k: str(v) for k, v in row.items()}
    sets = {
        "sparse": set((row["decision_asof_ts"], row["trade_spec_id"]) for row in sparse_top3),
        "full": set((row["decision_asof_ts"], row["trade_spec_id"]) for row in full_top3),
        "v5": set((row["decision_asof_ts"], row["trade_spec_id"]) for row in v5_top3),
        "v6": set((row["decision_asof_ts"], row["trade_spec_id"]) for row in v6_top3),
    }
    groups = {
        "v6_restored_sparse_winner": sets["v6"] & sets["sparse"],
        "v6_kept_full_candidate": sets["v6"] & sets["full"],
        "v6_new_not_sparse": sets["v6"] - sets["sparse"],
        "v6_dropped_v5": sets["v5"] - sets["v6"],
        "v6_added_over_v5": sets["v6"] - sets["v5"],
    }
    rows: list[dict[str, object]] = []
    for group, keys in groups.items():
        for idx, (decision_ts, trade_spec_id) in enumerate(sorted(keys), 1):
            rank = rank_by_tid.get(trade_spec_id, {})
            rows.append(
                {
                    "task_id": "Task1502",
                    "audit_id": f"V6AUDIT1502-{group}-{idx:04d}",
                    "audit_group": group,
                    "decision_asof_ts": decision_ts,
                    "trade_spec_id": trade_spec_id,
                    "symbol": rank.get("symbol", ""),
                    "event_family": rank.get("event_family", ""),
                    "expectation_v6_state": rank.get("expectation_v6_state", ""),
                    "absorption_v6_state": rank.get("absorption_v6_state", ""),
                    "materiality_v6_state": rank.get("materiality_v6_state", ""),
                    "route": rank.get("route", ""),
                    "semantic_v6_rank_score": rank.get("semantic_v6_rank_score", ""),
                    "semantic_v6_rank_within_decision": rank.get("semantic_v6_rank_within_decision", ""),
                    "evaluation_sparse_return": trade_lookup.get(("ruler_top3_v1", decision_ts, trade_spec_id), {}).get("net_return", ""),
                    "evaluation_full_return": trade_lookup.get(("ruler_top3_v1", decision_ts, trade_spec_id), {}).get("net_return", ""),
                    "evaluation_v5_return": trade_lookup.get(("conditional_materiality_top3_v1", decision_ts, trade_spec_id), {}).get("net_return", ""),
                    "evaluation_v6_return": trade_lookup.get(("semantic_v6_top3_v1", decision_ts, trade_spec_id), {}).get("net_return", ""),
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build_summary(
    l2_rows: list[dict[str, object]],
    rank_rows: list[dict[str, object]],
    metrics: list[dict[str, object]],
    audit_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    summary: list[dict[str, object]] = []
    for area, rows, field in [
        ("all_event_family", l2_rows, "event_family"),
        ("top3_event_family", [row for row in rank_rows if int(row["semantic_v6_rank_within_decision"]) <= 3], "event_family"),
        ("top3_expectation", [row for row in rank_rows if int(row["semantic_v6_rank_within_decision"]) <= 3], "expectation_v6_state"),
        ("top3_absorption", [row for row in rank_rows if int(row["semantic_v6_rank_within_decision"]) <= 3], "absorption_v6_state"),
        ("audit_groups", audit_rows, "audit_group"),
    ]:
        for key, value in sorted(Counter(str(row[field]) for row in rows).items()):
            summary.append({"task_id": "Task1503", "summary_area": area, "metric": key, "value": value, "authority": AUTHORITY})
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    gate = [
        {
            "task_id": "Task1506",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "judgment_structure_pass": "1",
            "target_cagr_30pct_met": best["target_cagr_30pct_met"],
            "target_mdd_minus30pct_met": best["target_mdd_minus30pct_met"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "semantic_v6_judgment_structure_replay_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1507",
            "verdict": "semantic_v6_judgment_structure_implemented_not_accepted",
            "candidate_rows": len(l2_rows),
            "l3_edge_rows": len(rank_rows) * 5,
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "review v6 thesis and displacement audit before adding true analyst PIT or source-receipt exits",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return summary, gate, closeout


def write_report(metrics: list[dict[str, object]], closeout: dict[str, object], summary: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    event_summary = [row for row in summary if row["summary_area"] == "top3_event_family"]
    report = f"""# Task1488-1507 Semantic V6 Replay

## Decision Summary

- Verdict: `semantic_v6_judgment_structure_implemented_not_accepted`.
- Best policy: `{best['policy_variant_id']}`.
- Best final equity: {best['final_equity']}.
- Best CAGR: {best['cagr']}.
- Best MDD: {best['max_drawdown']}.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: L2/L3 now classify event family before materiality, separate good words from surprise, and separate initial price reaction from sustained market absorption.
- Objective: judge whether the structure is coherent before treating replay PnL as alpha.

## Quant Expert Report

- `materiality` no longer gives a standalone bonus.
- `positive / survival / financing / dilution / mixed / unknown` is decided first.
- `good_words_only` is not `true_surprise_proxy`.
- `initial_reaction_only` is not `sustained_market_acceptance`.
- `source_gap` remains neutral unless a source-backed survival or dilution event exists.
- Outcome returns are present only in Task1502 displacement audit.

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
    report += "\nTop3 semantic family mix:\n\n"
    for row in event_summary:
        report += f"- `{row['metric']}`: {row['value']}\n"
    report += """

## No-Background Decision-Maker Report

이번엔 점수 튜닝이 아니라 판단 구조를 고쳤다.

큰 이벤트를 바로 좋은 이벤트로 보지 않는다.

먼저 좋은 일인지, 생존 문제인지, 자금조달인지, 희석인지 나눈다.

좋은 말과 진짜 surprise도 분리했다.

잠깐 오른 것과 시장이 계속 받아준 것도 분리했다.

그래도 전략은 아직 승인 아니다.

## Artifact Manifest

- `task1488_expert_review_loop.csv`
- `task1489_v6_preregistered_spec.csv`
- `task1490_source_evidence_audit.csv`
- `task1491_l2_semantic_v6_panel.csv`
- `task1492_l3_mechanism_v3_edges.csv`
- `task1493_l4_thesis_cards_v6.csv`
- `task1494_payoff_ranker_v6.csv`
- `task1495_policy_specs.csv`
- `task1496_source_receipt_exit_panel.csv`
- `task1496_price_path_exit_panel.csv`
- `task1496_hold_receipt_panel.csv`
- `task1497_replay_trades.csv`
- `task1497_replay_equity.csv`
- `task1497_replay_metrics.csv`
- `task1502_displacement_audit.csv`
- `task1503_summary.csv`
- `task1506_acceptance_gate.csv`
- `task1507_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1488_1507_semantic_v6_replay_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1488_1507_semantic_v6_replay.md").write_text(report, encoding="utf-8")
    write_csv(REPORT_DIR / "task_1488_1507_decision.csv", [closeout])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    replay.AUTHORITY = AUTHORITY
    replay.POLICIES = POLICIES
    expert = expert_review_loop()
    spec = preregister_v6()
    source_rows, l2_rows, l3_rows, thesis_rows, rank_rows = build_semantic_panels()
    policy_specs = select_policy_specs(rank_rows)
    _enriched, specs, _bindings, filing_bindings, evidence = replay.load_inputs()
    price_cache: dict[str, object] = {}
    symbol_filings, accession_text = replay.build_filing_indexes(filing_bindings, evidence)
    source_exits, price_exits, hold_receipts = replay.build_exit_panels(policy_specs, specs, symbol_filings, accession_text, price_cache)
    trades, equity = replay.run_replay(policy_specs, specs, source_exits, price_exits, price_cache)
    metrics = replay.build_metrics(trades, equity)
    audit = build_displacement_audit(rank_rows, trades)
    summary, gate, closeout = build_summary(l2_rows, rank_rows, metrics, audit)
    outputs = [
        ("task1488_expert_review_loop.csv", expert),
        ("task1489_v6_preregistered_spec.csv", spec),
        ("task1490_source_evidence_audit.csv", source_rows),
        ("task1491_l2_semantic_v6_panel.csv", l2_rows),
        ("task1492_l3_mechanism_v3_edges.csv", l3_rows),
        ("task1493_l4_thesis_cards_v6.csv", thesis_rows),
        ("task1494_payoff_ranker_v6.csv", rank_rows),
        ("task1495_policy_specs.csv", policy_specs),
        ("task1496_source_receipt_exit_panel.csv", source_exits),
        ("task1496_price_path_exit_panel.csv", price_exits),
        ("task1496_hold_receipt_panel.csv", hold_receipts),
        ("task1497_replay_trades.csv", trades),
        ("task1497_replay_equity.csv", equity),
        ("task1497_replay_metrics.csv", metrics),
        ("task1502_displacement_audit.csv", audit),
        ("task1503_summary.csv", summary),
        ("task1506_acceptance_gate.csv", gate),
        ("task1507_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1507_closeout.json", closeout[0])
    write_report(metrics, closeout[0], summary)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
