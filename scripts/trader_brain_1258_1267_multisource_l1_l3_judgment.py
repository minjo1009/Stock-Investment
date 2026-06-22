from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1228 = ROOT / "data/artifacts/task_1228_1237_volatility_terminal_discriminator"
TASK1238 = ROOT / "data/artifacts/task_1238_1247_raw_text_terminal_evidence"
TASK1141 = ROOT / "data/artifacts/task_1141_1150_external_source_acquisition"
OUT_DIR = ROOT / "data/artifacts/task_1258_1267_multisource_l1_l3_judgment"
REPORT_DIR = ROOT / "docs/reports/task_1258_1267_multisource_l1_l3_judgment"

AUTHORITY = "DIAGNOSTIC_MULTISOURCE_L1_L3_JUDGMENT_ONLY"
LOOKBACK_DAYS = 180


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


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    cleaned = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(value + "T00:00:00+00:00")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def expert_rulebook() -> list[dict[str, object]]:
    rules = [
        ("sec_survival", "survival_risk", "accepted accession, primary document, available timestamp, hash, and excerpt are mandatory", "no hard block without source lineage", "missing filing is not negative", "180-365d or resolved filing"),
        ("sec_survival", "survival_risk", "substantial doubt, actual default, acceleration, unresolved deficiency, bankruptcy, or failed restructuring can invalidate", "hard block allowed only for active adverse issuer event", "boilerplate legal language is common in normal issuers", "until resolved"),
        ("sec_survival", "dilution_pressure", "ATM, shelf, warrants, PIPE, and converts are watch unless paired with cash need or survival runway stress", "dilution alone cannot block", "growth financing can look like distress financing", "90-180d"),
        ("sec_survival", "listing_compliance", "Item 3.01, deficiency notice, minimum bid, cure period, and reverse split need event_state and issuer scope", "title-only Item 3.01 is not block", "transfer/listing-standard boilerplate can false trigger", "until compliance/resolution"),
        ("sec_survival", "survival_risk", "mitigated, historical, hypothetical, and boilerplate context lowers polarity and cannot become terminal by itself", "context polarity overrides keyword", "keyword-only extractors overclassify", "immediate"),
        ("ir_ceo_earnings_call", "management_narrative", "CEO, CFO, and analyst speaker roles must be separated", "speaker identity required before scoring", "promotional language can distort", "45-90d"),
        ("ir_ceo_earnings_call", "management_narrative", "guidance change, backlog specificity, bookings, renewal, churn, margin bridge, and capacity detail reinforce narrative", "optimism without numbers cannot boost", "scripted confidence is weak", "one reporting cycle"),
        ("ir_ceo_earnings_call", "narrative_quality", "Q&A evasiveness, repeated non-answer, financing avoidance, or customer-loss avoidance weakens thesis", "tone alone cannot hard block", "transcript summaries can omit nuance", "45-90d"),
        ("ir_ceo_earnings_call", "expectation_revision", "next call must refresh or the narrative decays", "stale narrative cannot re-rank", "old bullish call can linger after facts changed", "45-90d"),
        ("ir_ceo_earnings_call", "contradiction", "CEO claims must be checked against SEC liquidity, contract facts, and market acceptance", "management cannot override hard SEC risk", "management may frame bad facts positively", "current quarter"),
        ("contract_orders_customer", "revenue_validation", "signed contract, named customer, amount, term, binding status, and cancellation rights are required", "MOU/LOI/pilot alone cannot validate revenue", "headline contract can be non-binding", "90-180d"),
        ("contract_orders_customer", "revenue_validation", "delivery window, revenue recognition, cash collection, and margin/capacity path must be separated", "bookings are not revenue", "large backlog can be low margin or delayed", "until milestone"),
        ("contract_orders_customer", "customer_quality", "counterparty quality and customer concentration must be recorded", "single customer win can route to concentration watch", "customer logo can hide tiny economics", "90-180d"),
        ("contract_orders_customer", "materiality", "contract size must be compared with issuer revenue, backlog, and market cap", "immaterial awards cannot boost rank", "small contract PR can be overmarketed", "90d"),
        ("contract_orders_customer", "contradiction", "customer PR or award database should confirm issuer PR where possible", "issuer-only PR is lower confidence", "self-reported deals can be noisy", "until external confirmation"),
        ("analyst_institution", "expectation_change", "estimate revision beats target-price change for ranking", "target price alone cannot boost", "price targets are often lagging", "30-60d"),
        ("analyst_institution", "expectation_change", "rating change must include reason, estimate delta, and consensus context", "upgrade/downgrade alone cannot route", "analyst language can follow price", "30-60d"),
        ("analyst_institution", "priced_expectations", "clustered revisions and dispersion changes identify priced/not-priced state", "analyst facts need primary-source verification", "consensus can be stale", "30-60d"),
        ("analyst_institution", "contradiction", "analyst bullishness cannot override hard survival event", "hard risk dominates soft upgrade", "crowded upgrades can mark late-cycle optimism", "30-60d"),
        ("analyst_institution", "source_gap", "licensed report gaps must be explicit and cannot be fabricated from headlines", "missing analyst data is not negative", "partial snippets mislead", "n/a"),
        ("policy_news_catalyst", "external_catalyst", "policy stage must separate rumor, proposal, passed, enacted, funded, and implemented", "headline policy cannot route by itself", "broad policy can already be priced", "10-60d"),
        ("policy_news_catalyst", "external_catalyst", "official source, agency, jurisdiction, effective window, funding/enforcement mechanism, and affected entities are required", "theme-only policy is shadow only", "sector benefit may not reach issuer", "10-180d"),
        ("policy_news_catalyst", "policy_risk", "export control, sanctions, investigations, complaints, and restrictions weaken only through revenue/cost/supply-chain mechanism", "policy risk must connect to exposure chain", "keyword policy hits are broad", "10-90d"),
        ("policy_news_catalyst", "catalyst_stage", "funding or award execution is stronger than announcement", "proposal cannot be treated as implemented", "political reversals happen", "stage-dependent"),
        ("policy_news_catalyst", "contradiction", "policy tailwind must be checked against SEC survival and market acceptance", "policy cannot save active default alone", "theme optimism can mask issuer weakness", "10-60d"),
        ("market_price_volume", "market_acceptance", "relative strength, 126d/252d momentum, dollar volume, and pullback defense confirm market acceptance", "price cannot become source truth", "squeeze can mimic acceptance", "10-30d"),
        ("market_price_volume", "market_acceptance", "market confirms source-backed thesis timing but cannot create thesis alone", "price-only buy rule forbidden", "momentum can reverse", "10-30d"),
        ("market_price_volume", "liquidity_quality", "low ADV, spread widening, sub-dollar price, and volume collapse condition execution risk", "liquidity alone is not terminal", "microcap rallies can be fragile", "10-30d"),
        ("market_price_volume", "contradiction", "source-positive but market-rejected state weakens entry timing", "do not overwrite source evidence with one-day move", "market may lag real information", "10-30d"),
        ("market_price_volume", "winner_preservation", "high volatility with positive trend and liquidity should be preserved unless active hard event exists", "volatility-alone penalty forbidden", "alpha often lives in high-vol winners", "10-30d"),
    ]
    rows: list[dict[str, object]] = []
    for idx, (family, primitive, rule, hard_boundary, false_positive, decay) in enumerate(rules, start=1):
        rows.append(
            {
                "task_id": "Task1258",
                "rule_id": f"MSRULE1258-{idx:03d}",
                "source_family": family,
                "l2_primitive": primitive,
                "professional_rule": rule,
                "hard_boundary": hard_boundary,
                "false_positive_warning": false_positive,
                "time_decay": decay,
                "required_time_fields": "published_ts;received_ts;available_to_brain_ts;effective_window",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def source_contracts() -> list[dict[str, object]]:
    specs = [
        ("sec_survival", "available", "Task1238 raw SEC filing text", "symbol;cik;decision_asof;accession;available_to_brain_ts;hash;excerpt", "shadow_and_diagnostic_modifier"),
        ("ir_ceo_earnings_call", "gap", "IR releases, earnings call transcripts, investor day, CEO/CFO statements", "symbol;event_ts;speaker;transcript_hash;guidance_field;qa_context", "gap_no_assignment"),
        ("contract_orders_customer", "gap", "company press releases, 8-K exhibits, customer announcements, award databases", "symbol;customer;contract_size;duration;binding_status;delivery_window", "gap_no_assignment"),
        ("analyst_institution", "gap", "licensed institutional reports and estimate revision feeds", "symbol;broker;published_ts;rating;estimate_revision;consensus_delta", "gap_no_assignment"),
        ("policy_news_catalyst", "shadow_available", "Federal Register official policy archive by theme", "theme;publication_date;agency;title;document_number;url;hash", "theme_shadow_only"),
        ("market_price_volume", "available", "Task1228 decision-time market features", "symbol;decision_asof;momentum_126d;momentum_252d;adv_60d;vol_90d", "shadow_and_diagnostic_modifier"),
    ]
    rows = []
    for idx, (family, availability, source, keys, use_state) in enumerate(specs, start=1):
        rows.append(
            {
                "task_id": "Task1259",
                "contract_id": f"MSCON1259-{idx:03d}",
                "source_family": family,
                "availability_state": availability,
                "source_description": source,
                "required_join_keys": keys,
                "use_state": use_state,
                "missing_is_negative": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def load_federal_register_events() -> dict[str, list[dict[str, object]]]:
    rows = read_csv(TASK1141 / "task1145_federal_register_policy_archive_panel.csv")
    events_by_theme: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        raw_path = ROOT / row["raw_source_path"]
        if not raw_path.exists() or row["download_status"] != "downloaded":
            continue
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        for result in payload.get("results", []):
            pub = parse_ts(result.get("publication_date", ""))
            if pub is None:
                continue
            agencies = ";".join(agency.get("name", "") for agency in result.get("agencies", []))
            text = " ".join([str(result.get("title", "")), str(result.get("abstract", ""))]).lower()
            polarity = "supportive_or_attention"
            if any(token in text for token in ["restrict", "sanction", "prohibit", "export control", "investigation", "complaint"]):
                polarity = "restrictive_or_risk"
            if any(token in text for token in ["grant", "funding", "loan", "guarantee", "award", "incentive"]):
                polarity = "supportive_or_funding"
            events_by_theme[row["theme"]].append(
                {
                    "theme": row["theme"],
                    "publication_ts": pub,
                    "agency": agencies,
                    "title": result.get("title", ""),
                    "document_number": result.get("document_number", ""),
                    "html_url": result.get("html_url", ""),
                    "source_hash": row["source_hash"],
                    "policy_polarity": polarity,
                }
            )
    for theme in events_by_theme:
        events_by_theme[theme].sort(key=lambda item: item["publication_ts"])
    return events_by_theme


def policy_shadow_for_theme(events_by_theme: dict[str, list[dict[str, object]]], theme: str, decision_ts: datetime) -> dict[str, object]:
    start = decision_ts - timedelta(days=LOOKBACK_DAYS)
    candidates = [event for event in events_by_theme.get(theme, []) if start <= event["publication_ts"] <= decision_ts]
    if not candidates:
        return {
            "policy_event_count_180d": 0,
            "policy_support_count_180d": 0,
            "policy_risk_count_180d": 0,
            "latest_policy_title": "",
            "latest_policy_url": "",
            "policy_catalyst_state": "no_theme_policy_shadow_event",
        }
    support = sum(1 for event in candidates if event["policy_polarity"] == "supportive_or_funding")
    risk = sum(1 for event in candidates if event["policy_polarity"] == "restrictive_or_risk")
    latest = candidates[-1]
    if support > risk and support >= 2:
        state = "theme_policy_shadow_supportive"
    elif risk > support and risk >= 2:
        state = "theme_policy_shadow_risk"
    else:
        state = "theme_policy_shadow_attention"
    return {
        "policy_event_count_180d": len(candidates),
        "policy_support_count_180d": support,
        "policy_risk_count_180d": risk,
        "latest_policy_title": latest["title"],
        "latest_policy_url": latest["html_url"],
        "policy_catalyst_state": state,
    }


def market_state(row: dict[str, str]) -> tuple[str, str]:
    mom126 = to_float(row.get("momentum_126d"))
    mom252 = to_float(row.get("momentum_252d"))
    adv = to_float(row.get("avg_dollar_volume_60d"))
    vol = to_float(row.get("realized_vol_90d"))
    if mom126 > 0 and mom252 > 0 and adv >= 25_000_000:
        if vol >= 0.85:
            return "market_acceptance_high_vol_upside", "confirms_but_requires_volatility_awareness"
        return "market_acceptance_confirmed", "confirms"
    if mom126 < -0.2 and mom252 < -0.2:
        return "market_rejection_or_broken_trend", "contradicts"
    if adv < 10_000_000:
        return "market_acceptance_liquidity_weak", "conditions"
    return "market_acceptance_mixed", "conditions"


def build_packets() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    base_specs = read_csv(TASK1228 / "task1233_policy_specs.csv")
    signals = {row["selection_id"]: row for row in read_csv(TASK1228 / "task1230_l1_prior_knowable_signals.csv")}
    survival = {row["selection_id"]: row for row in read_csv(TASK1238 / "task1242_l2_survival_primitives.csv")}
    events_by_theme = load_federal_register_events()

    l1_rows: list[dict[str, object]] = []
    policy_rows: list[dict[str, object]] = []
    l2_rows: list[dict[str, object]] = []
    l3_rows: list[dict[str, object]] = []

    for idx, spec in enumerate(base_specs, start=1):
        sid = spec["selection_id"]
        decision_ts = parse_ts(spec["decision_asof_ts"]) or datetime.now(timezone.utc)
        theme = spec.get("derived_theme", "unclassified")
        signal = signals.get(sid, {})
        surv = survival.get(sid, {})
        policy_shadow = policy_shadow_for_theme(events_by_theme, theme, decision_ts)
        market, market_relation = market_state(signal)
        survival_route = surv.get("terminal_interpretation_route", "missing_sec_survival")
        source_gap_count = 3  # IR/CEO, contracts, analyst are not attached as historical source-time rows.

        if survival_route == "terminal_distress":
            composite = "survival_risk_overrides_until_reviewed"
            confidence = "capped"
        elif market.startswith("market_acceptance_confirmed") or market.startswith("market_acceptance_high"):
            if policy_shadow["policy_catalyst_state"] == "theme_policy_shadow_supportive":
                composite = "policy_supported_market_accepted"
            else:
                composite = "market_accepted_but_nonsec_gap_capped"
            confidence = "medium_shadow"
        elif policy_shadow["policy_catalyst_state"] == "theme_policy_shadow_risk":
            composite = "policy_risk_market_needs_confirmation"
            confidence = "low_shadow"
        else:
            composite = "incomplete_multisource_context"
            confidence = "low"

        l1_rows.append(
            {
                "task_id": "Task1260",
                "multisource_packet_id": f"MSL1-1260-{idx:06d}",
                "selection_id": sid,
                "symbol": spec["symbol"],
                "decision_asof_ts": spec["decision_asof_ts"],
                "derived_theme": theme,
                "sec_survival_state": survival_route,
                "policy_catalyst_state": policy_shadow["policy_catalyst_state"],
                "market_acceptance_state": market,
                "management_narrative_state": "missing_historical_source_time_gap",
                "contract_revenue_state": "missing_historical_source_time_gap",
                "analyst_expectation_state": "missing_licensed_or_historical_source_gap",
                "policy_event_count_180d": policy_shadow["policy_event_count_180d"],
                "policy_support_count_180d": policy_shadow["policy_support_count_180d"],
                "policy_risk_count_180d": policy_shadow["policy_risk_count_180d"],
                "latest_policy_title": policy_shadow["latest_policy_title"],
                "latest_policy_url": policy_shadow["latest_policy_url"],
                "source_gap_count": source_gap_count,
                "missing_is_negative": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
        if policy_shadow["latest_policy_title"]:
            policy_rows.append(
                {
                    "task_id": "Task1261",
                    "policy_shadow_id": f"MSPOL1261-{len(policy_rows)+1:06d}",
                    "selection_id": sid,
                    "symbol": spec["symbol"],
                    "decision_asof_ts": spec["decision_asof_ts"],
                    "derived_theme": theme,
                    **policy_shadow,
                    "project_historical_receipt_available": "0",
                    "theme_shadow_only": "1",
                    "selection_use_allowed": "0",
                    "replay_use_allowed": "0",
                    "authority": AUTHORITY,
                }
            )
        l2_rows.append(
            {
                "task_id": "Task1262",
                "l2_multisource_id": f"MSL2-1262-{idx:06d}",
                "selection_id": sid,
                "symbol": spec["symbol"],
                "decision_asof_ts": spec["decision_asof_ts"],
                "composite_interpretation": composite,
                "confidence_state": confidence,
                "survival_primitive": survival_route,
                "policy_primitive": policy_shadow["policy_catalyst_state"],
                "market_primitive": market,
                "missing_management_contract_analyst_gap": "1",
                "assignment_uses_future_outcome": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
        edge_specs = [
            ("sec_survival", survival_route, "candidate_survival_assumption", "invalidates" if survival_route == "terminal_distress" else "conditions"),
            ("policy_news_catalyst", policy_shadow["policy_catalyst_state"], "theme_thesis", "supports" if "supportive" in policy_shadow["policy_catalyst_state"] else "conditions"),
            ("market_price_volume", market, "market_acceptance_assumption", market_relation),
            ("ir_ceo_earnings_call", "missing_historical_source_time_gap", "confidence_state", "caps_confidence"),
            ("contract_orders_customer", "missing_historical_source_time_gap", "revenue_validation", "caps_confidence"),
            ("analyst_institution", "missing_licensed_or_historical_source_gap", "priced_expectations", "caps_confidence"),
        ]
        for family, from_node, to_node, relation in edge_specs:
            l3_rows.append(
                {
                    "task_id": "Task1263",
                    "l3_multisource_edge_id": f"MSL3-1263-{len(l3_rows)+1:07d}",
                    "selection_id": sid,
                    "symbol": spec["symbol"],
                    "decision_asof_ts": spec["decision_asof_ts"],
                    "source_family": family,
                    "from_node": from_node,
                    "to_node": to_node,
                    "relation_primitive": relation,
                    "selection_use_allowed": "0",
                    "replay_use_allowed": "0",
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return l1_rows, policy_rows, l2_rows, l3_rows


def gap_queue() -> list[dict[str, object]]:
    gaps = [
        ("ir_ceo_earnings_call", "Quartr/transcript feed or company IR press release archive", "speaker/time stamped transcript plus guidance fields", "management narrative quality and Q&A consistency"),
        ("contract_orders_customer", "company PR, 8-K exhibit, customer PR, government award databases", "customer, contract value, binding status, delivery window", "revenue validation and fake-contract filter"),
        ("analyst_institution", "licensed analyst estimate/rating revision feed", "broker, timestamp, rating, estimate delta, target delta", "market expectation change and priced/not-priced separation"),
        ("policy_news_catalyst", "symbol/theme extractor over official policy/news archives", "affected entities, effective window, funding/enforcement mechanism", "theme-to-symbol catalyst precision"),
    ]
    return [
        {
            "task_id": "Task1264",
            "gap_id": f"MSGAP1264-{idx:03d}",
            "source_family": family,
            "needed_source": needed,
            "required_fields": fields,
            "why_needed": why,
            "current_state": "not_attached_to_historical_symbol_decision_l1",
            "missing_is_negative": "0",
            "selection_use_allowed": "0",
            "replay_use_allowed": "0",
            "authority": AUTHORITY,
        }
        for idx, (family, needed, fields, why) in enumerate(gaps, start=1)
    ]


def audit_rows(l1_rows: list[dict[str, object]], l2_rows: list[dict[str, object]], l3_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    composite_counts: dict[str, int] = defaultdict(int)
    for row in l2_rows:
        composite_counts[str(row["composite_interpretation"])] += 1
    return [
        {
            "task_id": "Task1265",
            "audit_role": "distressed_trader_panel",
            "finding": "SEC survival evidence is only one axis; hard events can invalidate but boilerplate and soft warnings only condition or cap confidence.",
            "upgrade_rule": "separate hard-event invalidation from multi-source confirmation",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1265",
            "audit_role": "quant_trader_panel",
            "finding": "Market acceptance should confirm whether the tape believes the narrative; price strength cannot replace source evidence.",
            "upgrade_rule": "market acceptance confirms or contradicts but does not become source truth",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1265",
            "audit_role": "backend_source_panel",
            "finding": "IR/CEO, contract, and analyst families are explicit gaps and cannot be inferred from SEC or price proxies.",
            "upgrade_rule": "missing source families cap confidence and create acquisition queue rows without negative assignment",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1265",
            "audit_role": "coverage_summary",
            "finding": "; ".join(f"{key}={value}" for key, value in sorted(composite_counts.items())),
            "upgrade_rule": "use this as shadow L1-L3 judgment layer before any replay policy",
            "authority": AUTHORITY,
        },
    ]


def validation_gate(l1_rows: list[dict[str, object]], policy_rows: list[dict[str, object]], l2_rows: list[dict[str, object]], l3_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1266",
            "l1_rows": len(l1_rows),
            "policy_shadow_rows": len(policy_rows),
            "l2_rows": len(l2_rows),
            "l3_rows": len(l3_rows),
            "selection_promoted": "0",
            "replay_executed": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task1258-1267 Multi-Source L1-L3 Judgment Layer

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: SEC survival, policy catalyst, market acceptance, and explicit IR/contract/analyst gaps are now represented as a time-aware L1-L3 judgment layer.
- Key metrics: {closeout['l1_rows']} L1 packets, {closeout['policy_shadow_rows']} policy shadow rows, {closeout['l2_rows']} L2 interpretations, {closeout['l3_rows']} L3 edges.
- Next action: attach real IR/CEO/transcript, contract/order, and analyst expectation sources before using this for replay.

## Quant Expert Report

- Data source and source readiness: Task1238 SEC raw evidence, Task1228 decision-time market features, Task1145 Federal Register theme-level policy archive.
- Exact join keys: `selection_id`, `symbol`, `decision_asof_ts`, `derived_theme`.
- Leakage audit: no future return, PnL, or outcome fields are used; Federal Register policy events are theme-shadow only because project historical receipt remains incomplete.
- Split/OOS metrics: not applicable; no replay was executed.
- Failure decomposition: IR/CEO/earnings call, contract/order, and analyst expectation source families are explicit gaps and only cap confidence.
- Remaining blockers: source-time extractors for transcripts/IR, contracts/orders, analyst estimate revisions, and symbol-level policy mapping.

## No-Background Decision-Maker Report

We stopped treating SEC as the whole brain.

The brain now has separate lanes for survival risk, management narrative, contract validation, market expectations, policy catalyst, and market acceptance.

Only three lanes have usable local evidence today: SEC survival, policy shadow, and price/volume acceptance.

## Artifact Manifest

- `task1258_expert_multisource_rulebook.csv`
- `task1259_source_family_contracts.csv`
- `task1260_l1_multisource_packets.csv`
- `task1261_policy_catalyst_shadow_panel.csv`
- `task1262_l2_multisource_interpretation.csv`
- `task1263_l3_multisource_relation_edges.csv`
- `task1264_source_gap_acquisition_queue.csv`
- `task1265_expert_audit_upgrade.csv`
- `task1266_validation_gate.csv`
- `task1267_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1258_1267_multisource_l1_l3_judgment_validate.py`
- `python -m unittest tests.test_trader_brain_1258_1267_multisource_l1_l3_judgment`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1258_1267_multisource_l1_l3_judgment.md").write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    l1_rows, policy_rows, l2_rows, l3_rows = build_packets()
    closeout = {
        "task_id": "Task1267",
        "verdict": "multisource_l1_l3_judgment_layer_implemented_no_replay",
        "rulebook_rows": len(expert_rulebook()),
        "source_contract_rows": len(source_contracts()),
        "l1_rows": len(l1_rows),
        "policy_shadow_rows": len(policy_rows),
        "l2_rows": len(l2_rows),
        "l3_rows": len(l3_rows),
        "gap_rows": len(gap_queue()),
        "selection_promoted": "0",
        "replay_executed": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "Attach historical source-time IR/CEO/transcript, contract/order, and analyst expectation feeds before replay.",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1258_expert_multisource_rulebook.csv", expert_rulebook())
    write_csv(OUT_DIR / "task1259_source_family_contracts.csv", source_contracts())
    write_csv(OUT_DIR / "task1260_l1_multisource_packets.csv", l1_rows)
    write_csv(OUT_DIR / "task1261_policy_catalyst_shadow_panel.csv", policy_rows)
    write_csv(OUT_DIR / "task1262_l2_multisource_interpretation.csv", l2_rows)
    write_csv(OUT_DIR / "task1263_l3_multisource_relation_edges.csv", l3_rows)
    write_csv(OUT_DIR / "task1264_source_gap_acquisition_queue.csv", gap_queue())
    write_csv(OUT_DIR / "task1265_expert_audit_upgrade.csv", audit_rows(l1_rows, l2_rows, l3_rows))
    write_csv(OUT_DIR / "task1266_validation_gate.csv", validation_gate(l1_rows, policy_rows, l2_rows, l3_rows))
    write_csv(OUT_DIR / "task1267_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1267_closeout.json", closeout)
    write_csv(REPORT_DIR / "task_1258_1267_decision.csv", [closeout])
    write_report(closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
