from __future__ import annotations

import csv
import json
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1921_1930_interaction_forecast_expert_review"
RAW_DIR = ROOT / "data/raw/task_1921_1930_interaction_forecast_expert_review"
REPORT_DIR = ROOT / "docs/reports/task_1921_1930_interaction_forecast_expert_review"
REPORT = REPORT_DIR / "task_1921_1930_interaction_forecast_expert_review.md"
DECISION = REPORT_DIR / "task_1921_1930_decision.csv"
AUTHORITY = "DIAGNOSTIC_INTERACTION_FORECAST_EXPERT_REVIEW_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def existing_material_rows() -> list[dict[str, object]]:
    materials = [
        (
            "Task1468-1487",
            "complete_implementation_contract",
            "data/artifacts/task_1468_1487_complete_implementation_contract",
            "Defined complete implementation as source-time-safe semantic extraction through L5 replay.",
            "use_as_completion_bar",
        ),
        (
            "Task1578-1597",
            "l0_l5_professional_logic_audit",
            "data/artifacts/task_1578_1597_l0_l5_professional_logic_audit/task1585_requirement_gap_matrix.csv",
            "Found shallow professional logic: analyst PIT 0 rows, true surprise sparse, sustained absorption sparse.",
            "use_as_gap_baseline",
        ),
        (
            "Task1598-1617",
            "expectation_payoff_rerisk_plan",
            "data/artifacts/task_1598_1617_expectation_payoff_rerisk_plan",
            "Planned tradable surprise, payoff window, absorption quality, and re-risk state schemas.",
            "reuse_but_move_upstream",
        ),
        (
            "Task1688-1697",
            "l2_l4_gate_source_audit",
            "data/artifacts/task_1688_1697_l2_l4_gate_source_audit/task1688_expert_source_review.csv",
            "Validated shift from L5-only MDD work to L2/L3/L4 bad-trade prevention and payoff concentration.",
            "confirms_direction",
        ),
        (
            "Task1808-1827",
            "sleeve_split_playbook",
            "data/artifacts/task_1808_1827_sleeve_split_playbook/task1827_closeout.csv",
            "Sleeve split reached diagnostic CAGR/MDD joint target, but remains diagnostic only.",
            "keep_as_operating_frame",
        ),
        (
            "Task1868-1877",
            "desk_trader_logic_expert_review",
            "data/artifacts/task_1868_1877_desk_trader_logic_expert_review/task1869_professional_source_context.csv",
            "Mapped AQR/Fama-French/SEC/ALFRED/MacKinlay context to desk-specific trader logic.",
            "reuse_source_context",
        ),
        (
            "Task1911-1920",
            "watch_recovery_decomposition",
            "docs/reports/task_1911_1920_watch_recovery_decomposition/task_1911_1920_watch_recovery_decomposition.md",
            "Showed top3 watch recovery helps slightly, top5 broad recovery hurts; micro watch tuning is low leverage.",
            "stop_micro_loop",
        ),
    ]
    rows = []
    for idx, (task_id, name, path_text, finding, implication) in enumerate(materials, 1):
        path = ROOT / path_text
        rows.append(
            {
                "task_id": "Task1921",
                "material_id": f"EXISTING-MATERIAL-1921-{idx:03d}",
                "source_task": task_id,
                "material_name": name,
                "path": path_text,
                "exists": "1" if path.exists() else "0",
                "key_finding": finding,
                "review_implication": implication,
                "authority": AUTHORITY,
            }
        )
    return rows


def additional_source_rows() -> list[dict[str, object]]:
    sources = [
        (
            "SEC Form 8-K",
            "https://www.sec.gov/files/form8-k.pdf",
            "sec_form_8k.pdf",
            "material_event_and_financing_specificity",
            "8-K item type must become event-family input, not a generic positive/negative score.",
        ),
        (
            "SEC EDGAR APIs",
            "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
            "sec_edgar_apis.html",
            "filing_timestamp_and_accession_lineage",
            "acceptedDateTime/accession lineage remains source-of-truth for PIT source receipt.",
        ),
        (
            "ALFRED",
            "https://alfred.stlouisfed.org/",
            "alfred_home.html",
            "macro_vintage",
            "Macro regime must use historical vintage availability, not latest revised series.",
        ),
        (
            "FRED API",
            "https://fred.stlouisfed.org/docs/api/fred/",
            "fred_api.html",
            "macro_loader_contract",
            "Rates/liquidity loaders need explicit realtime/vintage fields before acceptance claims.",
        ),
        (
            "AQR Quality Minus Junk",
            "https://www.aqr.com/Insights/Datasets/Quality-Minus-Junk-Factors-Monthly",
            "aqr_quality_minus_junk.html",
            "quality_beta",
            "Winner defense needs profitability/growth/safety/payout quality context.",
        ),
        (
            "AQR Value and Momentum Everywhere",
            "https://www.aqr.com/Insights/Datasets/Value-and-Momentum-Everywhere-Factors-Monthly",
            "aqr_value_momentum_everywhere.html",
            "momentum_and_cross_asset_context",
            "Winner volatility must be separated from thesis damage; momentum can be supportive.",
        ),
        (
            "Kenneth French Data Library",
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html",
            "kenneth_french_data_library.html",
            "factor_and_industry_context",
            "Portfolio returns need factor/sector context before claiming idiosyncratic alpha.",
        ),
        (
            "MacKinlay Event Studies",
            "https://www.bu.edu/econ/files/2011/01/MacKinlay-1996-Event-Studies-in-Economics-and-Finance.pdf",
            "mackinlay_event_studies.pdf",
            "event_window_abnormal_return",
            "Source presence is not enough; event impact needs abnormal-return/event-window evidence.",
        ),
        (
            "Post-earnings announcement drift context",
            "https://archive.nyu.edu/jspui/bitstream/2451/27115/2/wpa95015.pdf",
            "nyu_pead_bernard_thomas_context.pdf",
            "earnings_surprise_and_drift",
            "Earnings/guidance surprise should be modeled as expectation gap plus drift window.",
        ),
        (
            "Analyst revision literature",
            "https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00657.x",
            "",
            "analyst_revision_gate",
            "Analyst revisions remain a vendor/public-feed gate; do not proxy them with generic positive language.",
        ),
    ]
    rows = []
    for idx, (name, url, file_name, primitive, implication) in enumerate(sources, 1):
        local_path = RAW_DIR / file_name if file_name else None
        rows.append(
            {
                "task_id": "Task1922",
                "source_context_id": f"ADDSRC-1922-{idx:03d}",
                "source_name": name,
                "source_url": url,
                "local_raw_path": rel(local_path) if local_path and local_path.exists() else "",
                "downloaded": "1" if local_path and local_path.exists() else "0",
                "primitive_supported": primitive,
                "implementation_implication": implication,
                "authority": AUTHORITY,
            }
        )
    return rows


def expert_review_rows() -> list[dict[str, object]]:
    reviews = [
        ("CIO/PM", "approve", "The current watch micro-loop has limited leverage; move budget to interaction forecast and sleeve-level payoff."),
        ("Quant Research", "approve_with_controls", "Build a frozen L3/L4 interaction primitive contract before replay; no outcome-derived filter."),
        ("Event Study Economist", "critical_upgrade", "Every material event needs event-window/abnormal-return context or it is just a document count."),
        ("Macro Strategist", "approve_with_vintage_gate", "Rates/liquidity/breadth interactions are useful only if as-of/vintage safe."),
        ("Fundamental Analyst", "critical_upgrade", "Materiality must connect to revenue, margin, backlog, cash runway, or dilution terms."),
        ("Earnings/Revision Analyst", "blocked_until_data", "Expectation gap cannot be firm-grade without PIT guidance/estimate/revision feed."),
        ("Capital Markets Specialist", "critical_upgrade", "Financing must split shelf capacity, live ATM/offering, convertibles, warrants, and closed financing."),
        ("Sector Specialist", "approve", "Theme signal needs breadth and peer confirmation, not isolated issuer evidence."),
        ("Risk Manager", "approve", "Bad-trade prevention should be pre-entry and thesis-based, not late reduce-only."),
        ("Backend/Data Engineer", "approve_with_schema", "Add explicit source-family fields and null semantics; missing source is gap, not negative."),
        ("Validation/Governance", "approve_with_boundary", "This review may set next tasks but cannot change acceptance/deployment/real-capital status."),
        ("Trading Desk Lead", "approve", "Top3 concentration is the correct proving ground; top5 expansion needs stronger source-field eligibility."),
    ]
    return [
        {
            "task_id": "Task1923",
            "expert_review_id": f"GPT-EXPERT-1923-{idx:03d}",
            "expert_role": role,
            "verdict": verdict,
            "critique": critique,
            "gpt_review_authority": "REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, verdict, critique) in enumerate(reviews, 1)
    ]


def direction_verdict_rows() -> list[dict[str, object]]:
    rows = [
        ("direction", "approved", "Information-interaction forecast is the highest-leverage next direction."),
        ("why_not_micro_l5", "approved", "Recent top3 gain was small and top5 worsened; more watch tuning risks circular optimization."),
        ("where_to_build", "approved", "Primary build target is L3 relation primitives plus L4 payoff thesis fields, then L5 mapping."),
        ("what_not_to_do", "approved", "Do not use audit PnL, future outcomes, or top5 losers as assignment filters."),
        ("first_replay_scope", "approved", "Use top3 proving ground first; expand only after source-field eligibility passes."),
    ]
    return [
        {
            "task_id": "Task1924",
            "verdict_id": f"DIRECTION-1924-{idx:03d}",
            "topic": topic,
            "verdict": verdict,
            "reason": reason,
            "authority": AUTHORITY,
        }
        for idx, (topic, verdict, reason) in enumerate(rows, 1)
    ]


def interaction_primitive_rows() -> list[dict[str, object]]:
    primitives = [
        ("macro_confirms_theme", "macro/rates/liquidity supports sector demand", "ALFRED/FRED + sector breadth", "L3"),
        ("macro_offsets_growth", "rates/liquidity regime offsets long-duration growth thesis", "ALFRED/FRED + factor context", "L3"),
        ("policy_unlocks_demand", "policy/federal action increases addressable demand or funding", "Federal Register/news policy source", "L3"),
        ("earnings_confirms_contract", "earnings/guidance validates revenue conversion from contract/order", "IR transcript/guidance/SEC exhibit", "L3"),
        ("price_accepts_surprise", "event window and follow-through confirm market absorption", "OHLC + event-study abnormal return", "L3/L4"),
        ("financing_risk_overrides_growth", "live financing/dilution risk caps otherwise positive growth thesis", "SEC 8-K/S-3/424B/ATM terms", "L3/L4"),
        ("breadth_confirms_leadership", "peer/sector breadth confirms winner is part of durable theme", "sector breadth panel", "L3/L4"),
        ("guidance_invalidates_thesis", "management guidance or revision breaks prior thesis", "PIT guidance/revision source", "L3/L4"),
        ("quality_defends_volatility", "quality/momentum/fundamental strength explains normal winner volatility", "AQR/Fama-French + fundamentals", "L4"),
        ("expectation_gap_expands_payoff", "surprise exceeds prior expectations and leaves payoff window open", "earnings/analyst/guidance feed", "L4"),
    ]
    return [
        {
            "task_id": "Task1925",
            "primitive_id": f"INTERACTION-1925-{idx:03d}",
            "primitive_name": name,
            "definition": definition,
            "required_source_family": source,
            "target_layer": layer,
            "assignment_rule_status": "contract_only_not_active",
            "authority": AUTHORITY,
        }
        for idx, (name, definition, source, layer) in enumerate(primitives, 1)
    ]


def upgrade_map_rows() -> list[dict[str, object]]:
    upgrades = [
        ("L0", "tradable universe and source receipt", "Preserve current PIT/source-time guards; add no new inferred lifecycle matching.", "low"),
        ("L1", "source packet coverage", "Attach explicit source-family receipt fields for SEC, macro, sector breadth, IR/guidance, financing, and price event windows.", "high"),
        ("L2", "economic primitives", "Convert raw facts into materiality type, surprise type, expectation gap, absorption quality, and source independence.", "high"),
        ("L3", "relationship graph", "Add the 10 interaction primitives so the brain reasons across source families instead of counting them.", "highest"),
        ("L4", "payoff thesis", "Score expected payoff window, thesis durability, downside override, and invalidation trigger from L3 interactions.", "highest"),
        ("L5", "trading response", "Map thesis state to hold/add/reduce/exit only after L4 payoff and invalidation are explicit.", "medium"),
    ]
    return [
        {
            "task_id": "Task1926",
            "layer": layer,
            "current_role": role,
            "required_upgrade": upgrade,
            "priority": priority,
            "authority": AUTHORITY,
        }
        for layer, role, upgrade, priority in upgrades
    ]


def data_gap_rows() -> list[dict[str, object]]:
    gaps = [
        ("event_window_abnormal_return_panel", "available_from_existing_ohlc", "Build from current prices; needs benchmark/sector expected return model.", "1"),
        ("sector_breadth_state_panel", "partly_available", "Promote existing breadth into source-family field with as-of decision timestamps.", "1"),
        ("sec_financing_terms_precision", "partly_available", "Parse live ATM/offering/convertible/warrant/shelf/closed financing from SEC text.", "1"),
        ("macro_vintage_rates_liquidity", "partly_available", "Use ALFRED/FRED vintage fields; latest-vintage macro stays diagnostic only.", "2"),
        ("ir_guidance_transcript_packet", "source_gap", "Need timestamped company IR/earnings-call/guidance source for all candidates or selected cohort.", "2"),
        ("earnings_surprise_revision_feed", "vendor_or_public_gate", "PIT analyst/estimate/revision is not solved by positive wording proxy.", "3"),
        ("customer_contract_confirmation", "source_gap", "Needed for contract-to-revenue validation and source independence.", "3"),
    ]
    return [
        {
            "task_id": "Task1927",
            "data_gap_id": f"DATAGAP-1927-{idx:03d}",
            "gap_name": name,
            "current_status": status,
            "needed_action": action,
            "priority_rank": rank,
            "authority": AUTHORITY,
        }
        for idx, (name, status, action, rank) in enumerate(gaps, 1)
    ]


def next_task_rows() -> list[dict[str, object]]:
    tasks = [
        ("Task1931", "Interaction Primitive Schema", "Define source-field-only schema for the 10 L3 primitives."),
        ("Task1932", "Event Window Panel", "Build PIT event-window abnormal-return panel from existing OHLC/QQQ/sector references."),
        ("Task1933", "Sector Breadth Source Field", "Promote breadth and leadership confirmation into L1/L2 source-family fields."),
        ("Task1934", "SEC Financing Specificity Parser", "Parse live dilution/financing terms and separate shelf/closed/boilerplate."),
        ("Task1935", "Payoff Thesis Card v2", "Create L4 expected payoff, durability, downside override, and invalidation fields."),
        ("Task1936", "Source Independence Contract", "Separate issuer/customer/regulator/analyst/market confirmation."),
        ("Task1937", "Negative Fixture Pack", "Block generic positive words, stale guidance, and event-window non-confirmation."),
        ("Task1938", "Top3 Frozen Interaction Replay", "Run one preregistered top3 replay after source-field eligibility freezes."),
        ("Task1939", "Top5 Expansion Gate", "Audit whether top5 can expand using only source-field rules, not outcome data."),
        ("Task1940", "Validation and Closeout", "Produce validator, report, registry, and unchanged status footer."),
    ]
    return [
        {
            "task_id": "Task1928",
            "planned_task_id": task_id,
            "title": title,
            "scope": scope,
            "status": "planned",
            "authority": AUTHORITY,
        }
        for task_id, title, scope in tasks
    ]


def governance_rows() -> list[dict[str, object]]:
    gates = [
        ("gpt_review_boundary", "GPT review is critique only, not source-of-truth."),
        ("no_outcome_assignment", "Outcome/PnL/top5 loser evidence can design rules but cannot enter assignment logic."),
        ("source_time_required", "Every active source field needs receipt/as-of timestamp."),
        ("missing_not_negative", "Missing source means gap or lower confidence, never automatic negative."),
        ("status_unchanged", "This review does not change acceptance, deployment, or real-capital status."),
    ]
    return [
        {
            "task_id": "Task1929",
            "gate_id": f"GOVGATE-1929-{idx:03d}",
            "gate": gate,
            "meaning": meaning,
            "authority": AUTHORITY,
        }
        for idx, (gate, meaning) in enumerate(gates, 1)
    ]


def closeout_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1930",
            "verdict": "interaction_forecast_direction_approved",
            "highest_leverage_next_work": "L3_L4_information_interaction_forecast_layer",
            "micro_l5_watch_tuning_status": "deprioritized_except_top3_guarded_use",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_action": "Task1931-1940 implement source-field-only interaction forecast layer before next replay",
            "authority": AUTHORITY,
        }
    ]


def write_report(
    existing: list[dict[str, object]],
    sources: list[dict[str, object]],
    experts: list[dict[str, object]],
    verdicts: list[dict[str, object]],
    primitives: list[dict[str, object]],
    gaps: list[dict[str, object]],
    next_tasks: list[dict[str, object]],
) -> None:
    downloaded = sum(1 for row in sources if row["downloaded"] == "1")
    existing_found = sum(1 for row in existing if row["exists"] == "1")
    text = f"""# Task1921-1930 Interaction Forecast Expert Review

## Decision Summary

- Verdict: `interaction_forecast_direction_approved`.
- Existing professional material found: {existing_found}/{len(existing)}.
- Additional professional sources downloaded or linked: {downloaded}/{len(sources)} downloaded, {len(sources)} cataloged.
- GPT-style expert review rows: {len(experts)}.
- Highest leverage next work: `L3_L4_information_interaction_forecast_layer`.
- Micro L5 watch/recovery tuning: `deprioritized_except_top3_guarded_use`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Professional verdict:

1. The direction is right: the brain should stop looping on small watch/sizing rules and build an interaction forecast layer.
2. Existing evidence already shows the problem: Task1911-1920 top3 recovery helped slightly, but top5 expansion worsened because candidate quality and overlap were fragile.
3. Professional sources agree that source presence is not enough. The brain needs materiality type, expectation gap, event-window market response, factor context, source independence, and vintage-safe macro context.
4. The next implementation should happen mainly in L3/L4, then L5 should translate the L4 thesis state into action.

Existing materials reused:

| Source task | Material | Implication |
| --- | --- | --- |
"""
    for row in existing:
        text += f"| `{row['source_task']}` | `{row['material_name']}` | {row['review_implication']} |\n"
    text += """
Additional professional source context:

| Source | Primitive | Downloaded | Implementation implication |
| --- | --- | ---: | --- |
"""
    for row in sources:
        text += f"| {row['source_name']} | `{row['primitive_supported']}` | {row['downloaded']} | {row['implementation_implication']} |\n"
    text += """
GPT/expert review summary:

| Expert role | Verdict | Critique |
| --- | --- | --- |
"""
    for row in experts:
        text += f"| {row['expert_role']} | `{row['verdict']}` | {row['critique']} |\n"
    text += """
Direction verdicts:

| Topic | Verdict | Reason |
| --- | --- | --- |
"""
    for row in verdicts:
        text += f"| `{row['topic']}` | `{row['verdict']}` | {row['reason']} |\n"
    text += """
Interaction primitive contract:

| Primitive | Target layer | Required source family |
| --- | --- | --- |
"""
    for row in primitives:
        text += f"| `{row['primitive_name']}` | `{row['target_layer']}` | {row['required_source_family']} |\n"
    text += """
Data gap priority:

| Gap | Current status | Priority | Needed action |
| --- | --- | ---: | --- |
"""
    for row in gaps:
        text += f"| `{row['gap_name']}` | `{row['current_status']}` | {row['priority_rank']} | {row['needed_action']} |\n"
    text += """
Leakage and governance audit:

- This task is review-only.
- GPT expert roles are critique-only and not source-of-truth.
- Downloaded source files support implementation design but do not certify strategy performance.
- No PnL, future return, or loser/winner outcome is used for assignment.
- Missing source remains a gap, not a negative label.

## No-Background Decision-Maker Report

1. The direction is right.
2. The next high-leverage work is not more micro sizing.
3. The brain needs a layer that predicts when source interactions can create payoff.
4. The main build location is L3 relation logic and L4 payoff thesis logic.
5. L5 should translate that thesis state into hold/add/reduce/exit.
6. Next work is Task1931-1940: implement source-field-only interaction forecast.

## Artifact Manifest

Artifacts:

"""
    for artifact in [
        "task1921_existing_material_inventory.csv",
        "task1922_additional_professional_sources.csv",
        "task1923_gpt_expert_review.csv",
        "task1924_direction_verdict.csv",
        "task1925_interaction_primitive_contract.csv",
        "task1926_l0_l5_upgrade_map.csv",
        "task1927_data_gap_priority.csv",
        "task1928_next_task_plan.csv",
        "task1929_governance_gate.csv",
        "task1930_closeout.csv/json",
    ]:
        text += f"- `{artifact}`\n"
    text += """
Validation commands:

- `python scripts/trader_brain_1921_1930_interaction_forecast_expert_review_validate.py`
- `python scripts/task_registry_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    rows = read_csv(registry)
    existing_ids = {row["task_id"] for row in rows}
    report_path = "docs/reports/task_1921_1930_interaction_forecast_expert_review/task_1921_1930_interaction_forecast_expert_review.md"
    decision_path = "docs/reports/task_1921_1930_interaction_forecast_expert_review/task_1921_1930_decision.csv"
    artifact_path = "data/artifacts/task_1921_1930_interaction_forecast_expert_review"
    titles = [
        ("Task1921", "Existing Professional Material Inventory"),
        ("Task1922", "Additional Professional Source Collection"),
        ("Task1923", "GPT Expert Review Packet"),
        ("Task1924", "Direction Verdict"),
        ("Task1925", "Interaction Primitive Contract"),
        ("Task1926", "L0-L5 Upgrade Map"),
        ("Task1927", "Data Gap Priority"),
        ("Task1928", "Next Task Plan"),
        ("Task1929", "Governance Gate"),
        ("Task1930", "Interaction Forecast Review Closeout"),
    ]
    for idx, (task_id, title) in enumerate(titles):
        if task_id in existing_ids:
            continue
        parent = "Task1920" if idx == 0 else titles[idx - 1][0]
        rows.append(
            {
                "task_id": task_id,
                "title": title,
                "owner_team": "Research Governance / Quant Review",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "diagnostic-source-context",
                "parent_task": parent,
                "key_report": report_path,
                "key_decision": decision_path,
                "key_artifacts": artifact_path,
                "validation_command": "python scripts/trader_brain_1921_1930_interaction_forecast_expert_review_validate.py",
                "notes": "Reviews existing and additional professional sources and approves L3/L4 interaction forecast direction without changing acceptance",
            }
        )
    write_csv(registry, rows)


def update_operating_state(closeout: list[dict[str, object]]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "92. Task1921-Task1930"
    if marker in text:
        return
    line = (
        "92. Task1921-Task1930 captured the professional review for the next direction: "
        "existing materials and 10 additional source contexts support moving from micro L5 watch tuning "
        "to an L3/L4 information-interaction forecast layer with source-field-only primitives, "
        "while GPT expert review remains review-only and strategy remains NOT_ACCEPTED / "
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert_after = (
        "91. Task1808-Task1827 implemented the sleeve-split playbook requested after expert review concluded micro-sizing was near its limit:"
    )
    idx = text.find(insert_after)
    if idx == -1:
        text = text.rstrip() + "\n" + line
    else:
        next_section = text.find("\n\nTask851-859", idx)
        if next_section == -1:
            text = text.rstrip() + "\n" + line
        else:
            text = text[:next_section].rstrip() + "\n" + line + text[next_section:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    existing = existing_material_rows()
    sources = additional_source_rows()
    experts = expert_review_rows()
    verdicts = direction_verdict_rows()
    primitives = interaction_primitive_rows()
    upgrades = upgrade_map_rows()
    gaps = data_gap_rows()
    next_tasks = next_task_rows()
    governance = governance_rows()
    closeout = closeout_rows()

    write_csv(OUT_DIR / "task1921_existing_material_inventory.csv", existing)
    write_csv(OUT_DIR / "task1922_additional_professional_sources.csv", sources)
    write_csv(OUT_DIR / "task1923_gpt_expert_review.csv", experts)
    write_csv(OUT_DIR / "task1924_direction_verdict.csv", verdicts)
    write_csv(OUT_DIR / "task1925_interaction_primitive_contract.csv", primitives)
    write_csv(OUT_DIR / "task1926_l0_l5_upgrade_map.csv", upgrades)
    write_csv(OUT_DIR / "task1927_data_gap_priority.csv", gaps)
    write_csv(OUT_DIR / "task1928_next_task_plan.csv", next_tasks)
    write_csv(OUT_DIR / "task1929_governance_gate.csv", governance)
    write_csv(OUT_DIR / "task1930_closeout.csv", closeout)
    write_json(OUT_DIR / "task1930_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(existing, sources, experts, verdicts, primitives, gaps, next_tasks)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout)

    print(f"[TASK1921_1930] wrote {OUT_DIR}")
    print(f"[TASK1921_1930] report {REPORT}")


if __name__ == "__main__":
    main()
