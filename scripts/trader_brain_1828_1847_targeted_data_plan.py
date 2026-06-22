from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1808 = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
OUT_DIR = ROOT / "data/artifacts/task_1828_1847_targeted_data_plan"
REPORT_DIR = ROOT / "docs/reports/task_1828_1847_targeted_data_plan"
REPORT = REPORT_DIR / "task_1828_1847_targeted_data_plan.md"
DECISION = REPORT_DIR / "task_1828_1847_decision.csv"

AUTHORITY = "DIAGNOSTIC_TARGETED_DATA_PLAN_ONLY"


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


def to_float(value: object) -> float:
    try:
        if value in {"", None, "nan"}:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def source_context_rows() -> list[dict[str, object]]:
    rows = [
        (
            "rates_liquidity",
            "ALFRED",
            "https://alfred.stlouisfed.org/",
            "Vintage macro/rates data; use for as-of rate and liquidity regime rather than current revised values.",
            "official_public",
            "high",
        ),
        (
            "rates_liquidity",
            "FRED DGS10",
            "https://fred.stlouisfed.org/series/DGS10",
            "Daily 10-year Treasury yield; useful for valuation-compression and duration-sensitive sleeve states.",
            "official_public",
            "high",
        ),
        (
            "rates_liquidity",
            "FINRA Margin Statistics",
            "https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics",
            "Monthly margin debit/free-credit balances; use as market leverage/liquidity stress context.",
            "official_public",
            "medium",
        ),
        (
            "earnings_revision",
            "Nasdaq Data Link Zacks Analyst Revisions",
            "https://data.nasdaq.com/databases/ZREV",
            "Analyst estimate and rating revisions; likely vendor-gated but directly maps to expectation gap.",
            "vendor_or_paid",
            "high_if_available",
        ),
        (
            "earnings_revision",
            "Nasdaq Data Link Zacks Earnings Trends",
            "https://data.nasdaq.com/databases/ZET",
            "Consensus earnings estimate revision trends; likely vendor-gated but high value for winner/cyclical sleeves.",
            "vendor_or_paid",
            "high_if_available",
        ),
        (
            "financing_dilution",
            "SEC EDGAR APIs",
            "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
            "Official submissions, companyfacts, and bulk archives; use for S-3, 424B5, ATM, 8-K financing, shares, debt, cash.",
            "official_public",
            "very_high",
        ),
        (
            "sector_breadth",
            "Kenneth French Data Library",
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html",
            "Research factor/portfolio context; use for factor-aware regime and breadth sanity checks, not single-name truth.",
            "academic_public",
            "medium",
        ),
        (
            "sector_breadth",
            "AQR Quality Minus Junk",
            "https://www.aqr.com/Insights/Datasets/Quality-Minus-Junk-Factors-Monthly",
            "Quality factor context built from profitability, growth, safety, and payout; useful for winner quality beta calibration.",
            "academic_public",
            "medium",
        ),
    ]
    return [
        {
            "task_id": "Task1830",
            "source_context_id": f"TARGETSRC-1830-{idx:03d}",
            "data_family": family,
            "source_name": name,
            "source_url": url,
            "use_case": use_case,
            "access_type": access,
            "expected_impact": impact,
            "authority": AUTHORITY,
        }
        for idx, (family, name, url, use_case, access, impact) in enumerate(rows, 1)
    ]


def expert_rows() -> list[dict[str, object]]:
    rows = [
        ("portfolio_pm", "Do not return to micro sizing; use attribution to identify which sleeve needs missing data.", "adopt"),
        ("rates_macro", "Rates/liquidity is first priority because it directly conditions valuation-compression, broad-selloff, and sleeve budget states.", "adopt_first"),
        ("earnings_analyst", "Earnings revision is highest value for expectation gap but may be vendor-blocked.", "adopt_with_access_gate"),
        ("capital_markets_analyst", "Financing/dilution is mandatory for speculative_event and terminal-risk no-entry, but it is narrower than rates/liquidity for current MDD budget.", "adopt_sec_first_after_rates"),
        ("sector_specialist", "Sector breadth should decide whether winner volatility is idiosyncratic or theme-wide; start lightweight from existing OHLC.", "adopt_lightweight"),
        ("data_engineer", "Each source needs published/received/as-of timestamps and exact CIK/symbol mapping; no proximity matching.", "adopt"),
        ("governance_reviewer", "All attribution PnL fields must remain audit-only and cannot enter the next assignment rules.", "adopt"),
    ]
    return [
        {
            "task_id": "Task1829",
            "expert_review_id": f"TARGETEXPERT-1829-{idx:03d}",
            "expert_role": role,
            "critique": critique,
            "implementation_decision": decision,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, critique, decision) in enumerate(rows, 1)
    ]


def attribution_rows() -> list[dict[str, object]]:
    ledger = read_csv(TASK1808 / "task1808_trade_drawdown_attribution_ledger.csv")
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in ledger:
        grouped[(row["policy_variant_id"], row["strategy_sleeve"])].append(row)
    rows: list[dict[str, object]] = []
    idx = 1
    for (policy, sleeve), group in sorted(grouped.items()):
        pnl = sum(to_float(row["pnl"]) for row in group)
        dd = sum(to_float(row["trade_drawdown_contribution"]) for row in group)
        capital = sum(to_float(row["capital_allocated"]) for row in group)
        avg_ret = sum(to_float(row["net_return"]) for row in group if row["net_return"] != "") / max(1, sum(1 for row in group if row["net_return"] != ""))
        rows.append(
            {
                "task_id": "Task1828",
                "sleeve_attribution_id": f"SLEEVEATTRPLAN-1828-{idx:04d}",
                "policy_variant_id": policy,
                "strategy_sleeve": sleeve,
                "trade_count": len(group),
                "pnl_sum_audit_only": round(pnl, 4),
                "drawdown_contribution_sum_audit_only": round(dd, 4),
                "capital_allocated_sum_audit_only": round(capital, 4),
                "avg_net_return_audit_only": round(avg_ret, 6),
                "dominant_gap": dominant_gap_for_sleeve(sleeve),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def dominant_gap_for_sleeve(sleeve: str) -> str:
    return {
        "winner_compounder": "earnings_revision_plus_sector_breadth",
        "cyclical_beta": "rates_liquidity_plus_sector_breadth",
        "speculative_event": "financing_dilution_plus_catalyst_validation",
        "defensive_quality": "rates_liquidity_plus_quality_stability",
    }.get(sleeve, "unknown")


def priority_rows() -> list[dict[str, object]]:
    rows = [
        (
            1,
            "rates_liquidity",
            "largest immediate link to valuation_compression, broad_selloff, winner_macro_pressure, and sleeve budget changes",
            "L0 regime; L5 sleeve exposure; risk-on/risk-off budget",
            "ALFRED/FRED yields, yield changes, curve, FINRA margin balances, QQQ liquidity proxies",
            "public_first",
        ),
        (
            2,
            "earnings_revision",
            "largest expected CAGR quality impact for winner_compounder, but likely vendor-gated",
            "expectation gap; guidance change; winner quality beta",
            "Nasdaq/Zacks revision feeds, IBES/FactSet if licensed, transcript/guidance proxy if vendor blocked",
            "vendor_gate",
        ),
        (
            3,
            "financing_dilution",
            "highest public-source safety impact for speculative_event and issuer-specific damage",
            "speculative_event; terminal risk; no-entry; dilution override",
            "SEC submissions, 8-K, S-3, S-1, 424B5, ATM prospectus, companyfacts shares/cash/debt",
            "public_first",
        ),
        (
            4,
            "sector_breadth",
            "useful for cyclical_beta and winner-volatility diagnosis, but much can be derived from existing OHLC first",
            "winner_compounder hold; cyclical beta on/off; sector confirmation",
            "theme basket breadth, Fama-French/AQR factor context, sector ETF breadth from local prices",
            "mostly_public_or_local",
        ),
    ]
    return [
        {
            "task_id": "Task1831",
            "priority_rank": rank,
            "data_family": family,
            "why_priority": why,
            "l0_l5_target": target,
            "source_candidates": sources,
            "access_plan": access,
            "authority": AUTHORITY,
        }
        for rank, family, why, target, sources, access in rows
    ]


def field_contract_rows() -> list[dict[str, object]]:
    rows = [
        ("rates_liquidity", "L0", "rate_regime_state", "as-of Treasury/yield regime state", "published_date <= decision_asof"),
        ("rates_liquidity", "L0", "liquidity_stress_state", "margin/leverage/liquidity pressure", "release_month <= decision_asof"),
        ("rates_liquidity", "L5", "sleeve_regime_budget_multiplier", "winner/cyclical/defensive exposure adjustment", "no PnL fields"),
        ("financing_dilution", "L1", "financing_source_packet_id", "exact SEC accession/source packet", "CIK/accession exact only"),
        ("financing_dilution", "L2", "dilution_pressure_state", "ATM/S-3/424B5/share issuance risk", "acceptedDateTime <= decision_asof"),
        ("financing_dilution", "L5", "terminal_financing_override", "no-entry/reduce guard for speculative sleeve", "no missing-as-negative"),
        ("sector_breadth", "L0", "theme_breadth_state", "theme-wide participation vs isolated move", "basket constituents predeclared"),
        ("sector_breadth", "L3", "theme_confirms_or_weakens_edge", "theme supports winner hold or warns isolated damage", "same-decision only"),
        ("earnings_revision", "L2", "revision_surprise_state", "consensus/guidance revision direction and magnitude", "vendor/public timestamp <= decision_asof"),
        ("earnings_revision", "L4", "expectation_gap_quality", "winner thesis card expectation validation", "blocked if vendor history missing"),
    ]
    return [
        {
            "task_id": "Task1832",
            "field_contract_id": f"TARGETFIELD-1832-{idx:03d}",
            "data_family": family,
            "brain_layer": layer,
            "field_name": field,
            "field_meaning": meaning,
            "asof_guard": guard,
            "authority": AUTHORITY,
        }
        for idx, (family, layer, field, meaning, guard) in enumerate(rows, 1)
    ]


def validation_rows() -> list[dict[str, object]]:
    rows = [
        ("exact_key_join_only", "CIK/accession/symbol mapping must be exact; no date/price proximity fallback"),
        ("source_time_gate", "published/accepted/received/asof timestamps must be explicit before L2 use"),
        ("audit_only_guard", "PnL/drawdown contribution fields cannot enter assignment"),
        ("vendor_block_guard", "earnings revision remains blocked if PIT vendor data is unavailable"),
        ("no_missing_negative", "missing data is source_gap, not bearish signal"),
        ("split_oos_required", "any replay after data attachment requires IS/OOS and cost stress"),
        ("status_preservation", "no diagnostic result changes NOT_ACCEPTED/FORBIDDEN statuses"),
    ]
    return [
        {
            "task_id": "Task1833",
            "validation_rule_id": f"TARGETVAL-1833-{idx:03d}",
            "validation_rule": rule,
            "meaning": meaning,
            "authority": AUTHORITY,
        }
        for idx, (rule, meaning) in enumerate(rows, 1)
    ]


def task_plan_rows() -> list[dict[str, object]]:
    rows = [
        ("Task1828", "Sleeve Attribution Audit", "Quant Review", "Summarize sleeve/regime/action PnL and drawdown audit-only; identify dominant gaps"),
        ("Task1829", "Expert Review Packet", "Research Governance", "Capture GPT/institutional/sector/data expert review-only conclusions"),
        ("Task1830", "Professional Source Context Catalog", "Data & Market Microstructure", "Catalog public/vendor source candidates and access limits"),
        ("Task1831", "Targeted Data Priority Decision", "Research Governance", "Rank financing/dilution rates/liquidity sector breadth earnings revision"),
        ("Task1832", "L0-L5 Field Contract", "Quant Engineering", "Define exact fields and layer ownership for each data family"),
        ("Task1833", "Validation And Leakage Contract", "Validation Engineering", "Define source-time exact-key audit-only and vendor-block checks"),
        ("Task1834", "Rates Liquidity Source Contract", "Data & Market Microstructure", "Acquire ALFRED/FRED/FINRA source contract and release-calendar map first"),
        ("Task1835", "Rates Liquidity Vintage Loader Plan", "Data & Market Microstructure", "Plan DGS2/DGS10/curve/margin vintage/as-of loader with stale observation flags"),
        ("Task1836", "SEC Financing Dilution Source Plan", "Data & Market Microstructure", "Acquire official SEC source packets for S-1/S-3/424B/8-K/10-Q/10-K financing dilution"),
        ("Task1837", "Financing Dilution Extractor Contract", "Quant Engineering", "Design dilution/financing text and companyfacts extractor with negative fixtures"),
        ("Task1838", "Earnings Revision Access Gate", "Data & Market Microstructure", "Check vendor availability; design schema stub only if no license"),
        ("Task1839", "Sector Breadth Local Plan", "Regime Research", "Build theme/sector breadth from existing OHLC and predeclared mappings only"),
        ("Task1840", "Source Packet Schema", "Data Engineering", "Unify published_ts received_ts asof_ts source_family and exact entity keys"),
        ("Task1841", "L2 Targeted Meaning Extractors", "Quant Engineering", "Implement data-family-specific L2 states only after source packets exist"),
        ("Task1842", "L3 Sleeve Data Edges", "Quant Engineering", "Attach source-backed edges to winner/cyclical/speculative/defensive sleeves"),
        ("Task1843", "L4 Thesis Card Upgrade", "Quant Engineering", "Add targeted-data fields to sleeve thesis cards"),
        ("Task1844", "Frozen Policy Preregistration", "Research Governance", "Freeze one source-attached sleeve policy before replay"),
        ("Task1845", "Controlled Replay With Targeted Data", "Backtest & Simulation Infra", "Run only after Task1834-1844 pass"),
        ("Task1846", "Artifact Registry Validation", "Research Governance", "Write report manifest registry and validation output"),
        ("Task1847", "Decision Gate", "Research Governance", "Decide next branch without acceptance/deployment overclaim"),
    ]
    return [
        {
            "task_id": task_id,
            "title": title,
            "owner_team": owner,
            "task_goal": goal,
            "status": "planned",
            "authority": AUTHORITY,
        }
        for task_id, title, owner, goal in rows
    ]


def gate_closeout_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    gate = [
        {
            "task_id": "Task1846",
            "decision": "targeted_data_plan_complete_no_replay",
            "next_allowed_work": "Task1834 rates/liquidity source contract first, with SEC financing/dilution planned next and earnings revision behind a vendor gate",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1847",
            "verdict": "targeted_data_plan_ready_no_replay_executed",
            "priority_1": "rates_liquidity",
            "priority_2": "earnings_revision_vendor_gate",
            "priority_3": "financing_dilution",
            "priority_4": "sector_breadth_lightweight",
            "next_action": "implement rates/liquidity source contract and vintage loader plan before any new replay",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(
    attribution: list[dict[str, object]],
    sources: list[dict[str, object]],
    priorities: list[dict[str, object]],
    fields: list[dict[str, object]],
    tasks: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1828-1847 Targeted Data Plan",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        "- What changed: sleeve attribution is converted into a targeted data acquisition plan.",
        "- No replay executed.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        f"- Next action: {closeout['next_action']}.",
        "",
        "## Quant Expert Report",
        "",
        "### Sleeve Attribution",
        "",
        "| Policy | Sleeve | Trades | PnL Audit Only | Drawdown Audit Only | Dominant Gap |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in attribution:
        lines.append(
            f"| `{row['policy_variant_id']}` | `{row['strategy_sleeve']}` | {row['trade_count']} | {row['pnl_sum_audit_only']} | {row['drawdown_contribution_sum_audit_only']} | `{row['dominant_gap']}` |"
        )
    lines.extend(["", "### Source Basis", ""])
    for row in sources:
        lines.append(f"- `{row['data_family']}` / {row['source_name']}: {row['source_url']} ({row['access_type']}, impact={row['expected_impact']})")
    lines.extend(["", "### Priority", "", "| Rank | Family | Why | Access |", "| ---: | --- | --- | --- |"])
    for row in priorities:
        lines.append(f"| {row['priority_rank']} | `{row['data_family']}` | {row['why_priority']} | `{row['access_plan']}` |")
    lines.extend(["", "### L0-L5 Field Contract", "", "| Family | Layer | Field | Asof Guard |", "| --- | --- | --- | --- |"])
    for row in fields:
        lines.append(f"| `{row['data_family']}` | `{row['brain_layer']}` | `{row['field_name']}` | {row['asof_guard']} |")
    lines.extend(
        [
            "",
            "Leakage and validation discipline:",
            "",
            "- Attribution PnL and drawdown fields remain audit-only.",
            "- Missing source fields are source gaps, not negative labels.",
            "- Vendor-gated earnings revision cannot be approximated as true consensus.",
            "- Future replay is blocked until source packets have explicit published/received/as-of timestamps.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Do not go back to micro sizing.",
            "2. The next high-impact work is targeted data, not broad data hoarding.",
            "3. Start with official/public rates-liquidity because it directly controls sleeve budget and MDD states.",
            "4. Earnings revision is high-alpha but vendor-gated.",
            "5. SEC financing/dilution comes next for speculative and terminal-risk control.",
            "6. Sector breadth starts lightweight from existing OHLC.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1828_sleeve_attribution_decision.csv`",
            "- `task1829_expert_review.csv`",
            "- `task1830_professional_source_context.csv`",
            "- `task1831_targeted_data_priority.csv`",
            "- `task1832_l0_l5_field_contract.csv`",
            "- `task1833_validation_contract.csv`",
            "- `task1834_1847_task_plan.csv`",
            "- `task1846_acceptance_gate.csv`",
            "- `task1847_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1828_1847_targeted_data_plan_validate.py`",
            "",
            "```text",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "```",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    attribution = attribution_rows()
    experts = expert_rows()
    sources = source_context_rows()
    priorities = priority_rows()
    fields = field_contract_rows()
    validation = validation_rows()
    tasks = task_plan_rows()
    gate, closeout = gate_closeout_rows()
    outputs = [
        ("task1828_sleeve_attribution_decision.csv", attribution),
        ("task1829_expert_review.csv", experts),
        ("task1830_professional_source_context.csv", sources),
        ("task1831_targeted_data_priority.csv", priorities),
        ("task1832_l0_l5_field_contract.csv", fields),
        ("task1833_validation_contract.csv", validation),
        ("task1834_1847_task_plan.csv", tasks),
        ("task1846_acceptance_gate.csv", gate),
        ("task1847_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task1847_closeout.json", closeout[0])
    write_report(attribution, sources, priorities, fields, tasks, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1828_1847] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
