from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/task_1211_1220_collapse_guard_sources"
PREV_ART = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
OUT_DIR = ROOT / "data/artifacts/task_1211_1220_collapse_guard_development"
REPORT_DIR = ROOT / "docs/reports/task_1211_1220_collapse_guard_development"

AUTHORITY = "DIAGNOSTIC_COLLAPSE_GUARD_DEVELOPMENT_ONLY"


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def expert_roster() -> list[dict[str, object]]:
    experts = [
        ("exchange_listing_corporate_actions", "Nasdaq/NYSE listing, delisting, reverse split, ticker identity", "L0-L3", "Separate leverage from structural survival risk; build official listing/corporate-action gate."),
        ("distressed_equity_credit", "going concern, liquidity runway, dilution, debt wall, bankruptcy/default", "L1-L5", "Do not ban risky equities; require source-backed distress meaning and action rules."),
        ("trader_risk_pm", "holding period, sell trigger, sizing, reentry, winner extension", "L4-L5", "Use slot5 as base; add asymmetric exits and risk buckets without killing winners."),
        ("leveraged_product_specialist", "daily reset, compounding, roll decay, acceleration/redemption risk", "L1-L5", "Leverage is allowed but must be traded through product-aware sleeve rules."),
        ("sector_theme_specialist", "theme legitimacy and sector-specific trap conditions", "L2-L4", "Separate true beneficiary from ticker attached to a theme label."),
        ("data_pit_engineer", "as-of source timestamps, corporate-action identity, no proximity fallback", "L0-L5", "Every risk signal must be available to the brain before the decision timestamp."),
    ]
    return [
        {
            "task_id": "Task1211",
            "expert_id": f"EXP1211-{idx:02d}",
            "expert_role": role,
            "scope": scope,
            "layer_focus": layers,
            "core_recommendation": rec,
            "review_only": "1",
            "authority": AUTHORITY,
        }
        for idx, (role, scope, layers, rec) in enumerate(experts, start=1)
    ]


def source_catalog() -> list[dict[str, object]]:
    downloads = {row["file"]: row for row in read_csv(RAW_DIR / "download_log.csv")}
    source_specs = [
        ("SRC1212-001", "SEC Leveraged and Inverse ETF Investor Bulletin", "https://www.sec.gov/resources-for-investors/investor-alerts-bulletins/updated-investor-bulletin-leveraged-inverse-etfs", "sec_leveraged_inverse_etf_bulletin.html", "leveraged_product", "L1/L2/L5", "daily reset, compounding, long-horizon mismatch"),
        ("SRC1212-002", "FINRA Non-Traditional ETF FAQ", "https://www.finra.org/rules-guidance/key-topics/etf/non-traditional-etf-faq", "", "leveraged_product", "L1/L2/L5", "daily reset suitability and holding-period mismatch"),
        ("SRC1212-003", "Nasdaq Continued Listing Guide", "https://listingcenter.nasdaq.com/assets/continuedguide.pdf", "nasdaq_continued_listing_guide.pdf", "listing_survival", "L0/L1/L2", "minimum bid, holders, market value, continued listing standards"),
        ("SRC1212-004", "Nasdaq Rule 5810 Deficiency Procedures", "https://listingcenter.nasdaq.com/rulebook/nasdaq/rules/nasdaq-5800-series", "", "listing_survival", "L1/L2/L3", "deficiency notice, compliance period, delisting process"),
        ("SRC1212-005", "NYSE American Continued Listing Standards", "https://www.nyse.com/publicdocs/nyse/markets/nyse-american/MKT_Continued_Listing_Standards.pdf", "nyse_american_continued_listing_standards.pdf", "listing_survival", "L0/L1/L2", "equity, market value, public distribution, impaired condition standards"),
        ("SRC1212-006", "SEC Item 303 MD&A Final Rule", "https://www.sec.gov/files/rules/final/2020/33-10890.pdf", "sec_mda_item303_final_rule.pdf", "liquidity_distress", "L1/L2", "short-term and long-term liquidity and capital resource disclosure"),
        ("SRC1212-007", "SEC Financial Reporting Manual", "https://www.sec.gov/files/cf-frm.pdf", "sec_financial_reporting_manual.pdf", "going_concern", "L1/L2", "going concern disclosure and substantial doubt language"),
        ("SRC1212-008", "FASB ASU 2014-15 Going Concern", "https://storage.fasb.org/ASU%202014-15.pdf", "fasb_asu_2014_15_going_concern.pdf", "going_concern", "L1/L2/L3", "management assessment and substantial doubt footnote requirements"),
        ("SRC1212-009", "SEC Form S-3", "https://www.sec.gov/files/forms-3.pdf", "sec_form_s3.pdf", "dilution_financing", "L1/L2/L3", "shelf registration and offering capacity context"),
        ("SRC1212-010", "SEC Microcap Stock Guide", "https://www.sec.gov/about/reports-publications/investorpubsmicrocapstock", "sec_microcap_stock_guide.html", "microcap_risk", "L0/L1/L2", "thin information, low liquidity, manipulation and microcap red flags"),
    ]
    rows = []
    for source_id, title, url, file_name, family, layer, use_case in source_specs:
        dl = downloads.get(file_name, {}) if file_name else {}
        rows.append(
            {
                "task_id": "Task1212",
                "source_id": source_id,
                "title": title,
                "url": url,
                "local_file": file_name,
                "download_status": dl.get("status", "reference_only_not_downloaded"),
                "size_bytes": dl.get("size_bytes", ""),
                "source_family": family,
                "layer_use": layer,
                "brain_use_case": use_case,
                "raw_source_required_before_replay": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def collapse_tail_diagnostic() -> list[dict[str, object]]:
    path = PREV_ART / "task1210_l0_l3_selected_symbols_to_2026q1.csv"
    rows = []
    if not path.exists():
        return rows
    frame = pd.read_csv(path)
    frame["return_to_2026q1_num"] = pd.to_numeric(frame["return_to_2026q1"], errors="coerce")
    tail = frame[frame["return_to_2026q1_num"] <= -0.70].sort_values("return_to_2026q1_num")
    for idx, row in enumerate(tail.itertuples(index=False), start=1):
        ret = float(row.return_to_2026q1_num)
        rows.append(
            {
                "task_id": "Task1213",
                "collapse_case_id": f"COLLAPSE1213-{idx:04d}",
                "symbol": row.symbol,
                "derived_theme": row.derived_theme,
                "first_entry_date": row.first_entry_date,
                "first_entry_price": row.first_entry_price,
                "price_2026q1": row.price_2026q1,
                "return_to_2026q1": round(ret, 6),
                "collapse_severity": "near_zero" if ret <= -0.90 else "severe_drawdown",
                "outcome_used_for_assignment": "0",
                "diagnostic_only": "1",
                "required_prior_knowable_evidence_to_investigate": "listing_status;corporate_actions;going_concern;dilution;cash_runway;product_structure;price_liquidity_path",
                "authority": AUTHORITY,
            }
        )
    return rows


def primitives() -> list[dict[str, object]]:
    specs = [
        ("L0", "security_identity_clean", "symbol/cik/listing/corporate-action identity is exact", "hard_gate", "ticker or price proximity fallback is forbidden"),
        ("L0", "listing_survival_status", "listed/deficient/hearing/suspended/OTC/delisted status as-of decision", "hard_gate_or_review_bucket", "deficiency does not always ban but must be explicit"),
        ("L0", "tradability_floor", "price, dollar volume, market cap/public float, split-adjusted continuity", "hurdle", "low price alone is not a short signal"),
        ("L1", "leveraged_product_structure", "leveraged/inverse/daily-reset/ETN/commodity roll features", "route_to_sleeve", "allowed, but not treated as ordinary equity"),
        ("L1", "going_concern_or_bankruptcy_evidence", "10-K/Q/8-K/auditor language or court/restructuring evidence", "invalidation_candidate", "source timestamp must precede decision"),
        ("L1", "dilution_financing_pressure", "S-3/S-1/424B/ATM/convertible/debt exchange evidence", "risk_haircut", "registration alone is not automatic sell"),
        ("L2", "cash_runway_short", "cash and burn imply short runway without credible financing", "risk_haircut_or_entry_block", "thresholds must be sector aware"),
        ("L2", "structural_price_collapse", "persistent drawdown plus liquidity/volatility deterioration", "risk_haircut", "price outcome after decision is forbidden"),
        ("L2", "theme_beneficiary_quality", "revenue/product/customer/policy exposure supports theme", "positive_or_negative_modifier", "theme label alone is insufficient"),
        ("L3", "distress_overrides_theme", "survival risk weakens or invalidates positive thesis", "relation_edge", "not a blanket filter"),
    ]
    return [
        {
            "task_id": "Task1214",
            "primitive_id": f"PRIM1214-{idx:02d}",
            "layer": layer,
            "primitive_name": name,
            "definition": definition,
            "default_action": action,
            "anti_overfit_note": note,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (layer, name, definition, action, note) in enumerate(specs, start=1)
    ]


def relation_edges() -> list[dict[str, object]]:
    specs = [
        ("company_to_listing_survival", "company", "listing_status", "conditions", "deficiency/hearing/reverse split risk conditions candidate eligibility"),
        ("company_to_product_structure", "security", "leveraged_product", "routes", "leveraged products route to product-aware sleeve rather than ordinary equity ranking"),
        ("company_to_liquidity_runway", "company", "cash_runway_short", "weakens", "short runway weakens long thesis and raises sizing hurdle"),
        ("company_to_dilution_pressure", "company", "active_financing", "weakens", "ATM/shelf/takedown pressure weakens per-share payoff"),
        ("company_to_going_concern", "company", "going_concern", "invalidates", "source-backed substantial doubt can force exit"),
        ("theme_to_distress_override", "theme_thesis", "distress_evidence", "conditional_invalidates", "theme upside cannot override survival risk without new evidence"),
        ("trade_to_reentry_cooldown", "closed_trade", "same_thesis", "blocks", "loss exit requires cooling-off unless new evidence appears"),
        ("winner_to_extension", "winner_trade", "valid_thesis", "extends", "winner extension allowed if L4 still intact and contradiction not worsening"),
    ]
    return [
        {
            "task_id": "Task1215",
            "edge_id": f"EDGE1215-{idx:02d}",
            "edge_type": edge_type,
            "from_node": from_node,
            "to_node": to_node,
            "relation_primitive": primitive,
            "meaning": meaning,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (edge_type, from_node, to_node, primitive, meaning) in enumerate(specs, start=1)
    ]


def l4_extensions() -> list[dict[str, object]]:
    specs = [
        ("listing_risk_state", "clean/watch/deficient/suspended_or_delisted", "candidate card must display survival state before L5 action"),
        ("distress_bucket", "clean/watch/distress_haircut/source_backed_invalidation", "not a score-only field; it carries source-backed rationale"),
        ("product_sleeve", "ordinary_equity/leveraged_product/commodity_product/etn_or_complex", "leveraged products remain allowed but separated"),
        ("contradiction_chain", "none/weakens/invalidates", "connects survival evidence to thesis validity"),
        ("new_evidence_required_for_reentry", "0/1 plus evidence type", "prevents stale same-thesis reentry after sell trigger"),
    ]
    return [
        {
            "task_id": "Task1216",
            "l4_field_id": f"L4FIELD1216-{idx:02d}",
            "field_name": field,
            "allowed_values_or_shape": values,
            "purpose": purpose,
            "selection_promoted": "0",
            "authority": AUTHORITY,
        }
        for idx, (field, values, purpose) in enumerate(specs, start=1)
    ]


def l5_policy() -> list[dict[str, object]]:
    specs = [
        ("base_policy", "slot5_default_equal_weight", "slot5 remains the base because Task1201-1210 best was slot5", "diagnostic_policy_candidate"),
        ("hard_event_exit", "going_concern_unalleviated/default/bankruptcy/delisting_determination/source-backed thesis invalidation", "sell next eligible trading day", "source_backed_exit"),
        ("asymmetric_price_exit", "entry_drawdown_25_to_30pct or peak_drawdown_35pct", "sell or reduce before monthly rebalance", "risk_control_candidate"),
        ("risk_bucket_sizing", "clean=1.0x watch=0.75x distress_haircut=0.25-0.5x invalidation=0x", "avoid blanket filtering while reducing tail risk", "sizing_candidate"),
        ("winner_extension", "L4 thesis alive and contradiction not worsening and price trend intact", "allow 3-6 month extension after monthly review", "upside_preservation"),
        ("reentry_cooling", "loss_exit or invalidation_exit", "2 month cooling-off unless new independent L4 evidence", "duplicate_thesis_control"),
        ("leveraged_product_sleeve", "daily-reset or commodity/ETN product", "shorter holding, smaller size, explicit expiry; no ordinary-equity long thesis", "product_aware_candidate"),
    ]
    return [
        {
            "task_id": "Task1217",
            "l5_rule_id": f"L5RULE1217-{idx:02d}",
            "rule_name": name,
            "trigger": trigger,
            "action": action,
            "rule_class": cls,
            "selection_promoted": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, trigger, action, cls) in enumerate(specs, start=1)
    ]


def leverage_policy() -> list[dict[str, object]]:
    specs = [
        ("allowed", "leveraged/inverse products are not banned by L0"),
        ("must_route", "daily-reset, ETN, commodity-roll, acceleration/redemption risk route to product-aware sleeve"),
        ("must_not_do", "do not compare leveraged commodity products to ordinary equities using long fundamental thesis"),
        ("required_l5", "shorter max holding, smaller size, explicit stop, no automatic monthly reentry"),
    ]
    return [
        {
            "task_id": "Task1218",
            "leverage_policy_id": f"LEV1218-{idx:02d}",
            "policy_clause": clause,
            "definition": definition,
            "authority": AUTHORITY,
        }
        for idx, (clause, definition) in enumerate(specs, start=1)
    ]


def backlog() -> list[dict[str, object]]:
    specs = [
        ("Task1221", "Official listing and corporate-action source adapter", "Data Engineering", "Build as-of listing status, reverse split, ticker identity, deficiency source packet."),
        ("Task1222", "Distress evidence extractor", "Quant Research", "Extract going concern, liquidity, financing, dilution, default and bankruptcy primitives from SEC forms."),
        ("Task1223", "Product structure classifier", "Quant Research", "Classify ordinary equity vs leveraged ETF/ETN/commodity product and route sleeves."),
        ("Task1224", "L3 collapse relation engine", "Research Governance", "Attach weakens/invalidates/routes/blocks/extends edges without future outcome input."),
        ("Task1225", "L4 collapse-aware candidate card", "Quant Research", "Add listing risk, distress bucket, product sleeve, contradiction chain, reentry evidence requirement."),
        ("Task1226", "L5 asymmetric exit and sizing preregistration", "Quant Review", "Pre-register slot5 plus hard event exits, drawdown exits, risk buckets, winner extension and reentry cooling."),
        ("Task1227", "Controlled replay comparison", "Quant Review", "Run one controlled diagnostic replay against Task1201-1210 only after source-backed fields exist."),
    ]
    return [
        {
            "task_id": task,
            "task_title": title,
            "owner_team": owner,
            "implementation_goal": goal,
            "status": "planned",
            "replay_allowed_now": "0" if task != "Task1227" else "blocked_until_1221_1226",
            "authority": AUTHORITY,
        }
        for task, title, owner, goal in specs
    ]


def write_report(closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / "task_1211_1220_collapse_guard_development.md"
    lines = [
        "# Task1211-1220 Collapse Guard Development",
        "",
        "## Decision Summary",
        "",
        "- Verdict: `collapse_guard_development_completed_no_replay`.",
        "- Objective: strengthen L0-L5 against near-delisting and near-zero collapse risk without banning leverage.",
        "- Expert packets: 3 subagent audits plus source-backed synthesis.",
        "- Authoritative source rows: 10.",
        f"- Downloaded source files: {closeout['downloaded_source_files']}.",
        f"- Evaluation-only collapse cases: {closeout['collapse_case_rows']}.",
        "- Replay executed: 0.",
        "- Selection promoted: 0.",
        "- Strategy acceptance: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Core design:",
        "",
        "- L0-L3 read survival and collapse risk.",
        "- L4 carries thesis contradiction and risk-bucket context.",
        "- L5 decides sell, size, holding period, and reentry rules.",
        "- Leverage is allowed, but leveraged products route to a product-aware sleeve.",
        "",
        "Key source families:",
        "",
        "- Exchange listing and deficiency standards.",
        "- Corporate actions and reverse splits.",
        "- SEC MD&A liquidity and capital resources.",
        "- Going concern and substantial doubt disclosures.",
        "- Shelf, ATM, prospectus, and dilution evidence.",
        "- Leveraged/inverse product structure and daily reset risks.",
        "",
        "Anti-overfit boundary:",
        "",
        "- Task1213 uses 2026Q1 collapse outcomes only as evaluation-only diagnostics.",
        "- Future outcomes are not allowed in L0-L5 assignment logic.",
        "- New rules must be triggered by prior-knowable source evidence.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We are not adding fifty filters.",
        "",
        "We are adding a trader brain that asks: is this candidate structurally alive, is the thesis still valid, and if risk appears, should we sell, shrink, shorten, or pause reentry?",
        "",
        "This is design and source preparation only. It does not approve the strategy.",
        "",
        "## Artifact Manifest",
        "",
        "Outputs:",
        "",
        "- `task1211_expert_roster.csv`",
        "- `task1212_authoritative_source_catalog.csv`",
        "- `task1213_collapse_tail_diagnostic_eval_only.csv`",
        "- `task1214_l0_l3_survival_primitives.csv`",
        "- `task1215_l3_relation_edges_design.csv`",
        "- `task1216_l4_candidate_card_extensions.csv`",
        "- `task1217_l5_trade_action_policy.csv`",
        "- `task1218_leverage_handling_policy.csv`",
        "- `task1219_implementation_backlog.csv`",
        "- `task1220_collapse_guard_development_closeout.csv/json`",
        "",
        "Validation commands:",
        "",
        "- `python scripts/trader_brain_1211_1220_collapse_guard_development_validate.py`",
        "- `python -m unittest tests.test_trader_brain_1211_1220_collapse_guard_development`",
        "",
        "```text",
        "Test results do not modify strategy acceptance status.",
        "Strategy: NOT_ACCEPTED",
        "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "Real Capital: FORBIDDEN",
        "```",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(REPORT_DIR / "task_1211_1220_decision.csv", [closeout])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows1211 = expert_roster()
    rows1212 = source_catalog()
    rows1213 = collapse_tail_diagnostic()
    rows1214 = primitives()
    rows1215 = relation_edges()
    rows1216 = l4_extensions()
    rows1217 = l5_policy()
    rows1218 = leverage_policy()
    rows1219 = backlog()
    downloaded = sum(1 for row in rows1212 if str(row["download_status"]).startswith("downloaded"))
    closeout = {
        "task_id": "Task1211-1220",
        "verdict": "collapse_guard_development_completed_no_replay",
        "expert_rows": len(rows1211),
        "source_rows": len(rows1212),
        "downloaded_source_files": downloaded,
        "collapse_case_rows": len(rows1213),
        "primitive_rows": len(rows1214),
        "relation_edge_design_rows": len(rows1215),
        "l4_extension_rows": len(rows1216),
        "l5_policy_rows": len(rows1217),
        "leverage_policy_rows": len(rows1218),
        "backlog_rows": len(rows1219),
        "replay_executed": "0",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "implement_task1221_1226_source_backed_collapse_guard_before_controlled_replay",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1211_expert_roster.csv", rows1211)
    write_csv(OUT_DIR / "task1212_authoritative_source_catalog.csv", rows1212)
    write_csv(OUT_DIR / "task1213_collapse_tail_diagnostic_eval_only.csv", rows1213)
    write_csv(OUT_DIR / "task1214_l0_l3_survival_primitives.csv", rows1214)
    write_csv(OUT_DIR / "task1215_l3_relation_edges_design.csv", rows1215)
    write_csv(OUT_DIR / "task1216_l4_candidate_card_extensions.csv", rows1216)
    write_csv(OUT_DIR / "task1217_l5_trade_action_policy.csv", rows1217)
    write_csv(OUT_DIR / "task1218_leverage_handling_policy.csv", rows1218)
    write_csv(OUT_DIR / "task1219_implementation_backlog.csv", rows1219)
    write_csv(OUT_DIR / "task1220_collapse_guard_development_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1220_collapse_guard_development_closeout.json", closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    write_report(closeout)
    print(
        "[TRADER_BRAIN_1211_1220_COLLAPSE_GUARD_DEVELOPMENT_OK] "
        f"sources={len(rows1212)} collapse_cases={len(rows1213)} backlog={len(rows1219)} replay=0"
    )


if __name__ == "__main__":
    main()
