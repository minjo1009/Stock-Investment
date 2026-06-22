from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1981_1990_current_2026_calibration_pack"
RAW_DIR = ROOT / "data/raw/task_1981_1990_current_2026_calibration_pack"
REPORT_DIR = ROOT / "docs/reports/task_1981_1990_current_2026_calibration_pack"
REPORT = REPORT_DIR / "task_1981_1990_current_2026_calibration_pack.md"
DECISION = REPORT_DIR / "task_1981_1990_decision.csv"
AUTHORITY = "DESIGN_CALIBRATION_ONLY_NOT_BACKTEST_ASSIGNMENT"


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


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return cleaned[:80] or "source"


SOURCE_CATALOG: list[dict[str, object]] = [
    {
        "source_id": "CUR2026-GS-AI-CAPEX-001",
        "institution": "Goldman Sachs",
        "source_title": "Why AI Companies May Invest More than $500 Billion in 2026",
        "url": "https://www.goldmansachs.com/insights/articles/why-ai-companies-may-invest-more-than-500-billion-in-2026",
        "source_date": "2025-12-01",
        "market_axis": "ai_capex_scale_selectivity",
        "current_design_takeaway": "AI capex remains structurally large, but investors are becoming more selective about AI beneficiaries.",
        "l0_l5_implication": "Add winner-acceleration sleeve criteria that require direct beneficiary status and valuation/crowding checks.",
    },
    {
        "source_id": "CUR2026-GS-SP500-AI-002",
        "institution": "Goldman Sachs",
        "source_title": "US Stocks Are Forecast to Rise 6% in 2026",
        "url": "https://www.goldmansachs.com/insights/articles/us-stocks-forecast-to-rise-in-2026",
        "source_date": "2026-04-29",
        "market_axis": "earnings_growth_ai_contribution",
        "current_design_takeaway": "AI investment is expected to be a major contributor to S&P 500 earnings growth in 2026.",
        "l0_l5_implication": "Separate broad market beta from idiosyncratic AI earnings acceleration before sizing top winners.",
    },
    {
        "source_id": "CUR2026-JPM-OUTLOOK-003",
        "institution": "J.P. Morgan",
        "source_title": "Outlook 2026: Promise and Pressure",
        "url": "https://www.jpmorgan.com/content/dam/jpmorgan/documents/wealth-management/outlook-2026.pdf",
        "source_date": "2025-11-01",
        "market_axis": "ai_infrastructure_power_capex",
        "current_design_takeaway": "AI buildout is large, power-intensive, and tied to infrastructure bottlenecks.",
        "l0_l5_implication": "Route power, grid, cooling, data center, and semiconductor equipment names into an AI-infrastructure sleeve, not only semis.",
    },
    {
        "source_id": "CUR2026-JPM-EOTM-004",
        "institution": "J.P. Morgan",
        "source_title": "Eye on the Market Outlook 2026: Smothering Heights",
        "url": "https://privatebank.jpmorgan.com/nam/en/insights/latest-and-featured/eotm/outlook",
        "source_date": "2026-01-01",
        "market_axis": "concentration_crowding",
        "current_design_takeaway": "AI-related market capitalization and profit contribution are highly concentrated.",
        "l0_l5_implication": "Add concentration/crowding guardrails while allowing high-conviction top1/top2 concentration only when thesis quality is high.",
    },
    {
        "source_id": "CUR2026-MS-MIDYEAR-005",
        "institution": "Morgan Stanley",
        "source_title": "Midyear Economic Outlook 2026: AI Drives Resilient Growth",
        "url": "https://www.morganstanley.com/insights/articles/economic-outlook-midyear-2026",
        "source_date": "2026-05-01",
        "market_axis": "macro_growth_ai_capex_energy",
        "current_design_takeaway": "AI capex supports growth, but energy shocks, rates, and supply chain risk remain macro constraints.",
        "l0_l5_implication": "Macro sleeve must distinguish AI tailwind from energy/rate headwind before allowing aggressive winner sizing.",
    },
    {
        "source_id": "CUR2026-MS-MARKET-RISK-006",
        "institution": "Morgan Stanley",
        "source_title": "Stock Market Outlook 2026: Political Risks Loom",
        "url": "https://www.morganstanley.com/insights/articles/2026-market-optimism-and-risks",
        "source_date": "2026-02-01",
        "market_axis": "policy_geopolitical_margin_of_error",
        "current_design_takeaway": "AI and policy tailwinds coexist with political/geopolitical risks and narrow error margins.",
        "l0_l5_implication": "Add thesis invalidation rules for policy/geopolitical shocks instead of only price-damage exits.",
    },
    {
        "source_id": "CUR2026-FED-FSR-007",
        "institution": "Federal Reserve",
        "source_title": "Financial Stability Report, May 2026",
        "url": "https://www.federalreserve.gov/publications/files/financial-stability-report-20260508.pdf",
        "source_date": "2026-05-08",
        "market_axis": "valuation_liquidity_financial_stability",
        "current_design_takeaway": "Asset valuation pressures remain elevated and liquidity/funding vulnerabilities matter for drawdown risk.",
        "l0_l5_implication": "Keep rates/liquidity vintage state as a portfolio risk budget input, not as a stock-level alpha score.",
    },
    {
        "source_id": "CUR2026-FED-GENAI-008",
        "institution": "Federal Reserve",
        "source_title": "Financial Stability Implications of Generative AI: Taming the Animal Spirits",
        "url": "https://www.federalreserve.gov/econres/feds/financial-stability-implications-of-generative-ai-taming-the-animal-spirits.htm",
        "source_date": "2025-01-01",
        "market_axis": "ai_sentiment_financial_stability",
        "current_design_takeaway": "AI sentiment can amplify valuation pressure, crowding, and correlated de-risking.",
        "l0_l5_implication": "Add AI-sentiment/crowding as a portfolio state that caps simultaneous same-theme exposure.",
    },
    {
        "source_id": "CUR2026-BNP-SEMI-009",
        "institution": "BNP Paribas",
        "source_title": "Semiconductor market 2026: it is not solely about AI",
        "url": "https://cib.bnpparibas/semiconductor-market-2026-it-is-not-solely-about-ai/",
        "source_date": "2026-04-01",
        "market_axis": "semiconductor_cycle_broadening",
        "current_design_takeaway": "Semiconductor growth is expected to broaden through ASP, memory, and non-AI drivers, not only AI logic chips.",
        "l0_l5_implication": "Split semiconductor sleeve into accelerator, memory, equipment, analog/power, and broad-cycle beneficiaries.",
    },
    {
        "source_id": "CUR2026-SIA-AI-010",
        "institution": "Semiconductor Industry Association",
        "source_title": "Semiconductors Account for 95% of an AI Data Server Rack's Value",
        "url": "https://www.semiconductors.org/new-report-finds-semiconductors-account-for-95-of-an-ai-data-server-racks-value-encompassing-the-full-stack-of-chip-technologies/",
        "source_date": "2026-06-01",
        "market_axis": "ai_datacenter_semiconductor_stack",
        "current_design_takeaway": "AI data center value spans the full semiconductor stack rather than a single chip class.",
        "l0_l5_implication": "Expand relation graph from AI-chip winner to full-stack AI infrastructure beneficiaries.",
    },
    {
        "source_id": "CUR2026-DELOITTE-SEMI-011",
        "institution": "Deloitte",
        "source_title": "2026 Global Semiconductor Industry Outlook",
        "url": "https://www.deloitte.com/us/en/insights/industry/technology/technology-media-telecom-outlooks/semiconductor-industry-outlook.html",
        "source_date": "2026-02-01",
        "market_axis": "genai_chip_revenue",
        "current_design_takeaway": "Generative AI chips are projected to be a very large share of semiconductor revenue.",
        "l0_l5_implication": "Require revenue linkage, capacity linkage, or customer confirmation before treating AI exposure as winner quality.",
    },
    {
        "source_id": "CUR2026-TROWE-AI-INFRA-012",
        "institution": "T. Rowe Price",
        "source_title": "Global Market Outlook 2026",
        "url": "https://www.troweprice.com/en/us/insights/global-market-outlook",
        "source_date": "2026-01-01",
        "market_axis": "ai_infrastructure_breadth",
        "current_design_takeaway": "AI opportunity is expanding beyond semiconductors into infrastructure and industrial beneficiaries.",
        "l0_l5_implication": "Add sector breadth confirmation and beneficiary-chain scoring before concentration.",
    },
    {
        "source_id": "CUR2026-AQR-MOMENTUM-013",
        "institution": "AQR",
        "source_title": "Value and Momentum Everywhere",
        "url": "https://www.aqr.com/Insights/Research/Journal-Article/Value-and-Momentum-Everywhere",
        "source_date": "2013-06-01",
        "market_axis": "momentum_persistence_research",
        "current_design_takeaway": "Momentum is a persistent cross-asset effect, but it must be combined with risk controls and context.",
        "l0_l5_implication": "Winner acceleration should use prior-known momentum persistence as confirmation, not as a standalone reason to buy.",
    },
]


def download_sources() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 current-2026-calibration-pack diagnostic research"}
    for idx, item in enumerate(SOURCE_CATALOG, start=1):
        source_id = str(item["source_id"])
        url = str(item["url"])
        suffix = ".pdf" if url.lower().endswith(".pdf") else ".html"
        raw_path = RAW_DIR / f"{idx:02d}_{slug(source_id)}{suffix}"
        downloaded = "0"
        status = "not_attempted"
        size = 0
        digest = ""
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=25) as response:
                payload = response.read(8 * 1024 * 1024)
            raw_path.write_bytes(payload)
            downloaded = "1"
            status = "downloaded"
            size = len(payload)
            digest = sha256_bytes(payload)
            time.sleep(0.2)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            status = f"download_failed:{type(exc).__name__}"
        rows.append(
            {
                "task_id": "Task1982",
                "source_id": source_id,
                "url": url,
                "download_attempted": "1",
                "downloaded": downloaded,
                "download_status": status,
                "raw_path": str(raw_path.relative_to(ROOT)).replace("\\", "/") if downloaded == "1" else "",
                "size_bytes": size,
                "sha256": digest,
                "assignment_uses_future_outcome": "0",
                "backtest_assignment_permission": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def source_catalog_rows(download_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_id = {row["source_id"]: row for row in download_rows}
    rows: list[dict[str, object]] = []
    for item in SOURCE_CATALOG:
        dl = by_id[str(item["source_id"])]
        rows.append(
            {
                "task_id": "Task1981",
                **item,
                "downloaded": dl["downloaded"],
                "raw_path": dl["raw_path"],
                "design_use_permission": "1",
                "historical_backtest_input_permission": "0",
                "reason_not_backtest_input": "current_or_post_period_design_calibration_source_not_decision_asof_evidence",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def boundary_rows() -> list[dict[str, object]]:
    rules = [
        ("current_2026_sources", "allowed", "for_l0_l5_rule_design_only", "blocked", "do_not_score_2021_2026Q1_trade_rows"),
        ("historical_asof_sources", "allowed", "for_backtest_assignment_if_receipt_time_passes", "allowed", "source_ts_must_be_on_or_before_decision_ts"),
        ("current_price_or_outcome", "blocked", "cannot_tune_rules_directly_to_known_winners", "blocked", "outcomes_evaluation_only"),
        ("GPT_or_expert_review", "allowed", "review_only_for_logic_gaps", "blocked", "not_raw_source_truth_or_acceptance"),
        ("current_market_structure", "allowed", "defines_required_primitives_and_sleeves", "blocked", "must_be_translated_into_prior_knowable_features_before_replay"),
    ]
    return [
        {
            "task_id": "Task1983",
            "boundary_id": f"BOUNDARY-1983-{idx:03d}",
            "information_type": info_type,
            "design_calibration_permission": design_perm,
            "design_use": design_use,
            "historical_assignment_permission": hist_perm,
            "historical_assignment_rule": hist_rule,
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (info_type, design_perm, design_use, hist_perm, hist_rule) in enumerate(rules, start=1)
    ]


def calibration_map_rows() -> list[dict[str, object]]:
    rows = [
        ("L0", "universe_and_source_admission", "Add current-era beneficiary-chain taxonomy: accelerator, memory, equipment, power, grid, cooling, data center, hyperscaler supplier.", "Do not use 2026 source text to admit 2021 candidates; convert only into historical-source requirements."),
        ("L1", "source_packets", "Require as-of evidence for AI capex, customer demand, orders/backlog, capacity, policy, power bottleneck, rates/liquidity, and market acceptance.", "Current pack only defines required source families."),
        ("L2", "economic_meaning", "Separate AI exposure from monetized revenue linkage; add acceleration, breadth, supply constraint, crowding, valuation, and energy/rate headwind primitives.", "No source-count bonus."),
        ("L3", "relation_graph", "Build mechanism edges: capex_to_order, power_bottleneck_to_infrastructure, memory_asp_to_margin, crowding_to_air_pocket, rates_to_duration_multiple.", "Relations must be prior-knowable in replay."),
        ("L4", "candidate_thesis", "Split stable compounder, winner acceleration, cyclical rebound, policy/infrastructure, and survival/financing sleeves.", "No one-score ranker may mix sleeve logic."),
        ("L5", "trading_decision", "Allow top1/top2 concentration only when winner acceleration, market acceptance persistence, thesis quality, and crowding budget all pass.", "Dynamic exit must track thesis break, not just drawdown."),
    ]
    return [
        {
            "task_id": "Task1984",
            "layer": layer,
            "object": obj,
            "current_2026_calibration_change": change,
            "leakage_guard": guard,
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for layer, obj, change, guard in rows
    ]


def winner_requirements_rows() -> list[dict[str, object]]:
    requirements = [
        ("winner_acceleration", "revenue_or_guidance_acceleration_plus_market_acceptance", "SEC/IR/call/order/news plus price receipt if certified", "high"),
        ("monetization_link", "AI exposure must connect to revenue, margin, backlog, capacity, or customer spend", "SEC/IR/customer/contract/equipment order", "high"),
        ("supply_constraint_quality", "Supply shortage or bottleneck should support pricing power or backlog durability", "call transcript/industry source/policy/power-grid source", "medium"),
        ("market_acceptance_persistence", "Prior-known relative strength should persist beyond one-day reaction", "certified historical price source", "high"),
        ("crowding_budget", "Crowded AI basket can be sized only with high thesis quality and liquidity support", "portfolio correlation/breadth/valuation state", "high"),
        ("macro_liquidity_context", "Rates/liquidity condition controls total risk budget, not standalone stock alpha", "ALFRED/FRED vintage", "high"),
        ("invalidation_trigger", "Exit/reduce only when thesis mechanism breaks or crowding shock overwhelms thesis quality", "updated as-of source packet", "high"),
    ]
    return [
        {
            "task_id": "Task1985",
            "requirement_id": f"WINREQ-1985-{idx:03d}",
            "primitive": primitive,
            "definition": definition,
            "required_historical_source_family": source_family,
            "priority": priority,
            "design_source_pack_derived": "1",
            "historical_assignment_ready_now": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (primitive, definition, source_family, priority) in enumerate(requirements, start=1)
    ]


def expert_review_rows() -> list[dict[str, object]]:
    reviews = [
        ("macro_pm", "Approve separating current design calibration from historical replay assignment.", "Do not let 2026 optimism directly raise 2021 scores."),
        ("semiconductor_specialist", "Approve splitting semis into accelerator, memory, equipment, analog/power, and broad-cycle sleeves.", "AI label alone is too weak."),
        ("ai_infrastructure_specialist", "Approve power/grid/cooling/data-center beneficiary chain.", "Need customer or backlog confirmation."),
        ("rates_liquidity_trader", "Approve using rates/liquidity as portfolio budget.", "Do not score individual AI stocks only from macro tailwind."),
        ("risk_manager", "Approve crowding and valuation pressure as air-pocket controls.", "Do not overcut true winners only because volatility is high."),
        ("quant_engineer", "Approve hard boundary: current pack is design-only, replay needs prior-known translated features.", "Validator must enforce zero backtest assignment permission."),
    ]
    return [
        {
            "task_id": "Task1986",
            "review_id": f"REVIEW-1986-{idx:03d}",
            "role": role,
            "approval": approval,
            "critique": critique,
            "gpt_or_expert_review_authority": "review_only_not_source_of_truth",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (role, approval, critique) in enumerate(reviews, start=1)
    ]


def backlog_rows() -> list[dict[str, object]]:
    tasks = [
        ("Task1991", "Winner Acceleration Historical Source Contract", "Define historical source families needed to compute winner acceleration as-of."),
        ("Task1992", "AI Beneficiary Chain Extractor", "Extract prior-known AI capex/customer/backlog/capacity/power-grid links."),
        ("Task1993", "Semiconductor Sleeve Splitter", "Classify accelerator/memory/equipment/analog-power/broad-cycle exposures."),
        ("Task1994", "Certified Market Acceptance Momentum Gate", "Replace Yahoo cross-check with assignment-grade price receipt or keep shadow-only."),
        ("Task1995", "Crowding And Concentration Budget", "Use breadth/correlation/valuation state to cap same-theme concentration."),
        ("Task1996", "Top1 Top2 Convex Sizing Replay", "Pre-register concentration variants after source contracts pass."),
        ("Task1997", "Thesis Break Exit Upgrade", "Exit on mechanism break and crowding shock, not only drawdown."),
        ("Task1998", "Split OOS Cost Overfit Ledger", "Run freeze/OOS/cost and overfit attempt ledger."),
        ("Task1999", "Diagnostic Report And Failure Attribution", "Explain winner miss, false positive, crowding loss, and exit quality."),
        ("Task2000", "Acceptance Gate Remains Closed", "Keep NOT_ACCEPTED unless full acceptance contract is separately met."),
    ]
    return [
        {
            "task_id": task_id,
            "sequence": idx,
            "title": title,
            "objective": objective,
            "depends_on": "Task1981-1990",
            "status": "planned",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (task_id, title, objective) in enumerate(tasks, start=1)
    ]


def write_report(metrics: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    text = f"""# Task1981-1990 Current 2026 Calibration Pack

## Decision Summary

- Verdict: `current_2026_calibration_pack_complete_design_only`.
- Current source rows: {metrics['source_count']}.
- Raw download attempts: {metrics['download_attempts']}.
- Raw downloads succeeded: {metrics['downloaded_count']}.
- L0-L5 calibration rows: {metrics['calibration_rows']}.
- Winner acceleration requirements: {metrics['winner_requirements']}.
- Historical backtest assignment permission from this pack: `0`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task separates two things that must not be mixed:

1. Current 2026 market-structure learning is allowed for brain design.
2. Historical 2021-2026Q1 replay assignment still requires prior-known as-of evidence.

Main 2026 calibration conclusions:

- AI capex is still a dominant market structure, but selectivity, valuation, and crowding matter.
- Semiconductors must be split into accelerator, memory, equipment, analog/power, and broad-cycle sleeves.
- AI infrastructure now includes power, grid, cooling, data-center, and industrial beneficiaries.
- Rates and liquidity should control portfolio risk budget, not act as standalone stock alpha.
- Winner acceleration needs monetization linkage, market acceptance persistence, and thesis-quality defense.

## No-Background Decision-Maker Report

1. We were leaning too much on old backtest-period sources for designing today's brain.
2. That is now fixed structurally.
3. 2026 sources can improve the rules.
4. They cannot directly change old trade scores.
5. Next work should build the historical source contract for winner acceleration.

## Artifact Manifest

- `task1981_current_2026_source_catalog.csv`
- `task1982_current_source_download_manifest.csv`
- `task1983_design_backtest_boundary.csv`
- `task1984_l0_l5_current_calibration_map.csv`
- `task1985_winner_acceleration_requirements.csv`
- `task1986_expert_review_matrix.csv`
- `task1987_task1991_2000_backlog.csv`
- `task1990_acceptance_gate.csv`
- `task1990_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    existing = registry.read_text(encoding="utf-8")
    rows: list[dict[str, object]] = []
    for task_num in range(1981, 1991):
        rows.append(
            {
                "task_id": f"Task{task_num}",
                "title": "Current 2026 Calibration Pack" if task_num == 1981 else f"Current 2026 Calibration Step {task_num}",
                "owner_team": "Research Governance / L0-L5 Trader Brain",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "design-calibration-only-not-backtest-assignment",
                "parent_task": "Task1980" if task_num == 1981 else f"Task{task_num - 1}",
                "key_report": "docs/reports/task_1981_1990_current_2026_calibration_pack/task_1981_1990_current_2026_calibration_pack.md",
                "key_decision": "docs/reports/task_1981_1990_current_2026_calibration_pack/task_1981_1990_decision.csv",
                "key_artifacts": "data/artifacts/task_1981_1990_current_2026_calibration_pack",
                "validation_command": "python scripts/trader_brain_1981_1990_current_2026_calibration_pack_validate.py",
                "notes": "Separates current 2026 market-structure learning from historical replay assignment and maps L0-L5 calibration requirements.",
            }
        )
    if "Task1981," not in existing:
        with registry.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writerows(rows)


def update_operating_state(metrics: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "98. Task1981-Task1990"
    row = (
        f"98. Task1981-Task1990 created a current-2026 design calibration pack: "
        f"{metrics['source_count']} current source rows, {metrics['downloaded_count']} raw downloads, "
        f"{metrics['calibration_rows']} L0-L5 calibration rows, and {metrics['winner_requirements']} winner-acceleration requirements; "
        "all rows are design-only and blocked from historical backtest assignment, while strategy remains "
        "NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    if marker not in text:
        anchor = "97. Task1971-Task1980"
        if anchor in text:
            lines = text.splitlines(keepends=True)
            insert_at = 0
            for idx, line in enumerate(lines):
                if line.startswith("97. Task1971-Task1980"):
                    insert_at = idx + 1
                    break
            lines.insert(insert_at, row)
            path.write_text("".join(lines), encoding="utf-8")
        else:
            path.write_text(text.rstrip() + "\n" + row, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    downloads = download_sources()
    source_rows = source_catalog_rows(downloads)
    boundary = boundary_rows()
    calibration = calibration_map_rows()
    requirements = winner_requirements_rows()
    reviews = expert_review_rows()
    backlog = backlog_rows()

    write_csv(OUT_DIR / "task1981_current_2026_source_catalog.csv", source_rows)
    write_csv(OUT_DIR / "task1982_current_source_download_manifest.csv", downloads)
    write_csv(OUT_DIR / "task1983_design_backtest_boundary.csv", boundary)
    write_csv(OUT_DIR / "task1984_l0_l5_current_calibration_map.csv", calibration)
    write_csv(OUT_DIR / "task1985_winner_acceleration_requirements.csv", requirements)
    write_csv(OUT_DIR / "task1986_expert_review_matrix.csv", reviews)
    write_csv(OUT_DIR / "task1987_task1991_2000_backlog.csv", backlog)

    acceptance = [
        {
            "task_id": "Task1990",
            "verdict": "current_2026_calibration_pack_complete_design_only",
            "historical_backtest_assignment_permission": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            **acceptance[0],
            "next_action": "Task1991-2000 winner acceleration historical source contract and diagnostic replay only after source contract passes",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
        }
    ]
    write_csv(OUT_DIR / "task1990_acceptance_gate.csv", acceptance)
    write_csv(OUT_DIR / "task1990_closeout.csv", closeout)
    write_json(OUT_DIR / "task1990_closeout.json", closeout[0])

    metrics = {
        "source_count": len(source_rows),
        "download_attempts": len(downloads),
        "downloaded_count": sum(1 for row in downloads if row["downloaded"] == "1"),
        "calibration_rows": len(calibration),
        "winner_requirements": len(requirements),
    }
    write_report(metrics)
    write_csv(
        DECISION,
        [
            {
                **metrics,
                "verdict": "current_2026_calibration_pack_complete_design_only",
                "historical_backtest_assignment_permission": "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
            }
        ],
    )
    update_registry()
    update_operating_state(metrics)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1981_1990_OK] sources={metrics['source_count']} downloaded={metrics['downloaded_count']}")


if __name__ == "__main__":
    main()
