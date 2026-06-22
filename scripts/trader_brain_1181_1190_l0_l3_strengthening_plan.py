from __future__ import annotations

import csv
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/task_1181_1190_l0_l3_context"
OUT_DIR = ROOT / "data/artifacts/task_1181_1190_l0_l3_strengthening_plan"
REPORT_DIR = ROOT / "docs/reports/task_1181_1190_l0_l3_strengthening_plan"

AUTHORITY = "DIAGNOSTIC_L0_L3_STRENGTHENING_PLAN_ONLY"
USER_AGENT = "minjo-trader-brain-research contact@example.com"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def download(url: str, path: Path, timeout: int = 45) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return {
            "download_status": "already_downloaded",
            "http_status": "",
            "content_type": "",
            "downloaded_at_utc": now_utc(),
            "size_bytes": path.stat().st_size,
            "raw_source_path": rel(path),
            "source_hash": sha256(path),
            "error": "",
        }
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    started = now_utc()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read()
            status = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
        path.write_bytes(body)
        return {
            "download_status": "downloaded",
            "http_status": status,
            "content_type": content_type,
            "downloaded_at_utc": started,
            "size_bytes": len(body),
            "raw_source_path": rel(path),
            "source_hash": sha256(path),
            "error": "",
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "download_status": "failed",
            "http_status": "",
            "content_type": "",
            "downloaded_at_utc": started,
            "size_bytes": 0,
            "raw_source_path": rel(path),
            "source_hash": "",
            "error": str(exc)[:500],
        }


def source_catalog() -> list[dict[str, object]]:
    rows = [
        ("SRC1181-001", "SEC EDGAR API documentation", "official", "source/fundamental", "SEC company facts, submissions, and XBRL API fields", "L1/L2", "https://www.sec.gov/search-filings/edgar-application-programming-interfaces", "sec_api.html"),
        ("SRC1181-002", "SEC developer resources", "official", "source/fundamental", "SEC JSON data access boundary and API source authority", "L1", "https://www.sec.gov/about/developer-resources", "sec_developer_resources.html"),
        ("SRC1181-003", "Fama French data library", "academic", "factor/industry", "factor and industry portfolio benchmark context", "L0/L2", "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html", "fama_french_data_library.html"),
        ("SRC1181-004", "Fama French 10 industry portfolios", "academic", "factor/industry", "industry definitions and industry return benchmark context", "L0/L3", "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library/det_10_ind_port.html", "fama_french_10_industries.html"),
        ("SRC1181-005", "ALFRED archival FRED", "official", "macro/vintage", "real-time macro vintage source concept", "L1/L2", "https://alfred.stlouisfed.org/", "alfred_home.html"),
        ("SRC1181-006", "FRED realtime period docs", "official", "macro/vintage", "realtime_start and realtime_end as-of macro semantics", "L1/L2", "https://fred.stlouisfed.org/docs/api/fred/realtime_period.html", "fred_realtime_period.html"),
        ("SRC1181-007", "FRED observations vintage docs", "official", "macro/vintage", "vintage_dates and observation access contract", "L1/L2", "https://fred.stlouisfed.org/docs/api/fred/series_observations.html", "fred_series_observations.html"),
        ("SRC1181-008", "BEA developer resources", "official", "macro/industry", "BEA API for industry and national accounts", "L1/L2", "https://www.bea.gov/resources/for-developers", "bea_developer_resources.html"),
        ("SRC1181-009", "BEA GDP by industry", "official", "macro/industry", "industry GDP and NAICS/industry context", "L0/L2", "https://www.bea.gov/itable/gdp-by-industry", "bea_gdp_by_industry.html"),
        ("SRC1181-010", "Federal Register API docs", "official", "policy", "official policy document retrieval and publication dates", "L1/L2", "https://www.federalregister.gov/developers/documentation/api/v1", "federal_register_api.html"),
        ("SRC1181-011", "CHIPS for America", "official", "semiconductor/policy", "semiconductor industrial policy and funding context", "L0/L3", "https://www.nist.gov/chips", "nist_chips.html"),
        ("SRC1181-012", "BIS semiconductor export-control clarification", "official", "semiconductor/geopolitics", "advanced computing and semiconductor export-control mechanism", "L2/L3", "https://www.bis.gov/press-release/commerce-releases-clarifications-export-control-rules-restrict-prcs-access-advanced-computing", "bis_semiconductor_export_controls.html"),
        ("SRC1181-013", "GAO advanced semiconductor export controls", "official", "semiconductor/geopolitics", "export-control implementation and risk context", "L2/L3", "https://www.gao.gov/products/gao-25-107386", "gao_semiconductor_export_controls.html"),
        ("SRC1181-014", "DOE data center electricity demand", "official", "power_grid/ai", "AI/data center electricity demand mechanism", "L0/L3", "https://www.energy.gov/oe/clean-energy-resources-meet-data-center-electricity-demand", "doe_data_center_power.html"),
        ("SRC1181-015", "DoD DIB cybersecurity strategy PDF", "official", "cybersecurity/defense", "defense industrial base cyber resilience demand context", "L0/L3", "https://dodcio.defense.gov/Portals/0/Documents/Library/DIB-CS-Strategy.pdf", "dod_dib_cybersecurity_strategy.pdf"),
        ("SRC1181-016", "National Defense Industrial Strategy implementation PDF", "official", "defense/aerospace", "defense industrial capacity, supply chain, and acquisition context", "L0/L3", "https://www.govinfo.gov/content/pkg/GOVPUB-D-PURL-gpo234260/pdf/GOVPUB-D-PURL-gpo234260.pdf", "ndis_implementation_plan.pdf"),
        ("SRC1181-017", "SIA state of semiconductor industry report", "industry", "semiconductor", "semiconductor demand, supply chain, and policy context", "L0/L3", "https://www.semiconductors.org/wp-content/uploads/2024/10/SIA_2024_State-of-Industry-Report.pdf", "sia_2024_semiconductor_report.pdf"),
        ("SRC1181-018", "Grid Strategies load growth report", "industry", "power_grid", "data center and electrification load-growth context", "L0/L3", "https://gridstrategiesllc.com/wp-content/uploads/Grid-Strategies-National-Load-Growth-Report-2025.pdf", "grid_strategies_load_growth_2025.pdf"),
    ]
    return [
        {
            "source_id": source_id,
            "source_title": title,
            "authority_tier": tier,
            "domain": domain,
            "why_collected": why,
            "brain_layer_use": layer,
            "source_url": url,
            "download_filename": filename,
            "authority": AUTHORITY,
        }
        for source_id, title, tier, domain, why, layer, url, filename in rows
    ]


def download_sources(catalog: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in catalog:
        path = RAW_DIR / str(row["source_id"]) / str(row["download_filename"])
        result = download(str(row["source_url"]), path, timeout=25)
        rows.append({**row, **result})
    return rows


def project_context_packet() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1182",
            "context_id": "CTX1182-001",
            "topic": "end_goal",
            "current_state": "US equity quant trading automation through source evidence economic meaning relation network candidate thesis validated backtest and paper/live gate",
            "critical_constraint": "strategy remains NOT_ACCEPTED deployment DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY real capital FORBIDDEN",
            "implication_for_l0_l3": "front brain must create broad-universe candidate compression before L4/L5 trading decisions",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1182",
            "context_id": "CTX1182-002",
            "topic": "latest_broad_universe_failure",
            "current_state": "Task1171-1180 best public_filer_proxy_slot10_v1 ended 1000 to 355.68 with CAGR -18.15 and MDD -83.42 versus QQQ 1847.03",
            "critical_constraint": "old 10x7 winner basket is blocked as selection basis",
            "implication_for_l0_l3": "current scoring cannot identify winners in broad public-filer universe",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1182",
            "context_id": "CTX1182-003",
            "topic": "available_universe",
            "current_state": "SEC bulk submissions generated 8129 public-filer entities and 592936 as-of proxy rows across 63 month-end decisions",
            "critical_constraint": "true exchange-listed PIT remains missing",
            "implication_for_l0_l3": "use SEC public-filer proxy for research while continuing vendor/exchange listing gap tracking",
            "authority": AUTHORITY,
        },
    ]


def expert_roster() -> list[dict[str, object]]:
    experts = [
        ("EXP1183-001", "Goldman-style quant PM", "Quant portfolio architecture", "Define L0 candidate funnel, liquidity/quality gates, and benchmark-aware selection diagnostics", "L0/L3"),
        ("EXP1183-002", "BOA-style macro strategist", "Macro cycle and rates", "Map FRED/ALFRED/BEA vintage features to sector-relative candidate pressure", "L0/L2/L3"),
        ("EXP1183-003", "Morgan Stanley-style equity strategist", "Factor and industry rotation", "Map Fama-French industry/factor context into broad-universe compression", "L0/L2"),
        ("EXP1183-004", "JPM-style risk manager", "Risk and drawdown", "Define fragility, dilution, volatility, and liquidity exclusion gates", "L0/L3"),
        ("EXP1183-005", "SEC/XBRL data engineer", "Fundamental extraction", "Convert SEC companyfacts/submissions into growth, quality, and filing-event features", "L1/L2"),
        ("EXP1183-006", "Semiconductor expert", "AI semiconductor supply chain", "Collect CHIPS/export-control/SIA context and define chip supply-chain relation primitives", "L0/L3"),
        ("EXP1183-007", "Power/grid expert", "Data center power and electrification", "Collect DOE/Grid context and define load-growth beneficiary and bottleneck relations", "L0/L3"),
        ("EXP1183-008", "Cybersecurity expert", "Cyber and defense demand", "Collect DoD/BIS/agency context and define breach/regulation/defense demand relations", "L0/L3"),
        ("EXP1183-009", "Aerospace/defense/space expert", "Defense industrial base and space", "Collect NDIS/DoD procurement context and define backlog/capacity/geopolitical relations", "L0/L3"),
        ("EXP1183-010", "Policy and political-risk expert", "US industrial policy and geopolitics", "Map Federal Register, BIS, CHIPS, defense, and energy policy to investable catalysts", "L1/L2/L3"),
        ("EXP1183-011", "AI/software expert", "AI platform and software monetization", "Define AI capex beneficiaries, software monetization evidence, and hype-risk invalidators", "L0/L3"),
        ("EXP1183-012", "Healthcare/biotech expert", "GLP-1, biologics, medtech", "Define FDA/clinical/reimbursement source needs and biotech exclusion rules", "L0/L3"),
        ("EXP1183-013", "Crypto/fintech expert", "Digital assets and fintech", "Define regulatory/cycle/liquidity source needs and high-fragility filters", "L0/L3"),
        ("EXP1183-014", "Backend data engineer", "Pipeline reliability", "Design schemas, validators, and artifact boundaries for L0-L3 implementation", "L1/L3"),
    ]
    return [
        {
            "task_id": "Task1183",
            "expert_id": expert_id,
            "role": role,
            "specialty": specialty,
            "assigned_context_gathering": assignment,
            "layer_scope": layer,
            "gpt_review_status": "packet_prepared_review_only",
            "authority": AUTHORITY,
        }
        for expert_id, role, specialty, assignment, layer in experts
    ]


def gap_matrix() -> list[dict[str, object]]:
    gaps = [
        ("GAP1184-001", "L0", "tradable_object_filter", "SEC public-filer proxy includes SPACs warrants ADRs thin liquidity and fragile tickers", "build security-type/liquidity/survivorship filters before ranking"),
        ("GAP1184-002", "L0", "candidate_compression", "29k broad feature rows were ranked directly with shallow momentum and filing counts", "compress 1500+ symbols to 50-150 candidates through quality growth liquidity and thematic relevance gates"),
        ("GAP1184-003", "L0", "sector_theme_mapping", "broad universe lacks robust sector industry theme exposure labels", "attach SIC/NAICS/SEC description/Fama-French/BEA industry mapping and theme ontology"),
        ("GAP1184-004", "L1", "source_family_coverage", "SEC filings exist but policy macro industry catalyst source families are not attached per broad symbol", "create source packets for macro policy theme company and price context"),
        ("GAP1184-005", "L2", "economic_meaning", "filing frequency is not economic meaning", "extract growth quality capital intensity profitability dilution backlog R&D and demand-supply primitives"),
        ("GAP1184-006", "L2", "macro_vintage", "macro context lacks vintage-as-of integration in selection", "attach ALFRED/FRED real-time series with decision-asof timestamps"),
        ("GAP1184-007", "L3", "relation_network", "current relation graph does not connect company to demand driver policy bottleneck customer/supplier and risk invalidator", "implement typed edges with confidence source_time and decay"),
        ("GAP1184-008", "L3", "theme_policy_links", "policy documents are not converted into investable company/industry impact relations", "build policy-to-industry-to-company mapper"),
        ("GAP1184-009", "L0-L3", "negative_filters", "bad objects are entering selection before brain scoring", "hard gate warrants rights SPAC units low ADV severe dilution missing price history and extreme drawdown"),
        ("GAP1184-010", "L0-L3", "evaluation", "candidate generation has no hit-rate diagnostics before full PnL replay", "measure top50/top100 forward distribution only after no-leakage candidate formation"),
    ]
    return [
        {
            "task_id": "Task1184",
            "gap_id": gap_id,
            "layer": layer,
            "gap_name": name,
            "current_failure": failure,
            "required_fix": fix,
            "authority": AUTHORITY,
        }
        for gap_id, layer, name, failure, fix in gaps
    ]


def strengthening_plan() -> list[dict[str, object]]:
    steps = [
        ("Task1191", "L0 security-type exclusion gate", "Remove warrants rights units SPAC shells OTC/ADR where unsupported low liquidity and broken price histories", "clean_candidate_universe"),
        ("Task1192", "L0 broad universe industry mapper", "Attach SIC/NAICS/Fama-French/BEA industry and initial theme exposure labels to public-filer symbols", "industry_theme_map"),
        ("Task1193", "L1 multi-source packet builder", "Build per-symbol source packets from SEC fundamentals filing events macro/policy/theme documents and price context", "l1_source_packets"),
        ("Task1194", "L2 fundamental meaning extractor", "Extract revenue growth margin quality cash burn dilution capex R&D profitability and balance-sheet stress primitives", "l2_meaning_panel"),
        ("Task1195", "L2 macro/policy as-of feature bridge", "Attach ALFRED/FRED/BEA/Federal Register/CHIPS/BIS/DOE/DoD policy context with source-time controls", "macro_policy_features"),
        ("Task1196", "L3 relation primitive expansion for broad universe", "Create company-industry-policy-demand-supply-risk relation edges with source hashes and confidence", "l3_relation_edges"),
        ("Task1197", "L0-L3 candidate compression engine", "Rank broad universe into top 50/100/150 candidate lists before L4 thesis generation", "compressed_candidates"),
        ("Task1198", "Expert audit and negative fixture suite", "Use expert packets to create negative cases for hype traps weak liquidity fake catalysts and policy overreach", "fixtures_validators"),
        ("Task1199", "No-PnL candidate quality diagnostic", "Measure forward hit-rate distributions after candidate compression without tuning on outcomes", "candidate_quality_report"),
        ("Task1200", "Controlled replay preregistration", "Only after candidate diagnostics pass pre-register one policy for broad-universe proxy replay", "replay_preregistration"),
    ]
    return [
        {
            "task_id": task_id,
            "task_title": title,
            "objective": objective,
            "primary_artifact": artifact,
            "status": "planned",
            "acceptance_boundary": "diagnostic_only_no_strategy_acceptance",
            "authority": AUTHORITY,
        }
        for task_id, title, objective, artifact in steps
    ]


def subagent_packets(experts: list[dict[str, object]]) -> list[dict[str, object]]:
    packets = []
    for expert in experts:
        packets.append(
            {
                "task_id": "Task1186",
                "packet_id": expert["expert_id"].replace("EXP", "PKT"),
                "assignee_role": expert["role"],
                "read_scope": "docs/operating_system/project_operating_state.md;docs/reports/task_1171_1180_public_filer_proxy_backtest/task_1171_1180_public_filer_proxy_backtest.md;data/artifacts/task_1181_1190_l0_l3_strengthening_plan/task1181_source_catalog.csv",
                "write_scope": "docs/reports/task_1181_1190_l0_l3_strengthening_plan/expert_packets/",
                "deliverable": expert["assigned_context_gathering"],
                "validation_authority": "review_only_does_not_accept_strategy",
                "pass_does_not_mean": "strategy acceptance deployment readiness PnL validity or real-capital permission",
                "authority": AUTHORITY,
            }
        )
    return packets


def write_expert_packet_docs(experts: list[dict[str, object]], context_rows: list[dict[str, object]]) -> None:
    packet_dir = REPORT_DIR / "expert_packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    context_text = "\n".join(f"- {row['topic']}: {row['current_state']}" for row in context_rows)
    for expert in experts:
        text = "\n".join(
            [
                f"# {expert['role']} Packet",
                "",
                "## Project Context",
                "",
                context_text,
                "",
                "## Assignment",
                "",
                str(expert["assigned_context_gathering"]),
                "",
                "## Boundary",
                "",
                "- Review-only.",
                "- No strategy acceptance.",
                "- No deployment readiness.",
                "- No buy/sell/sizing authority.",
                "- Provide source-backed context and L0-L3 schema suggestions only.",
                "",
            ]
        )
        filename = str(expert["expert_id"]).lower() + "_" + str(expert["role"]).lower().replace(" ", "_").replace("/", "_") + ".md"
        (packet_dir / filename).write_text(text, encoding="utf-8")


def write_report(closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / "task_1181_1190_l0_l3_strengthening_plan.md"
    lines = [
        "# Task1181-1190 L0-L3 Strengthening Plan",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Sources cataloged: {closeout['sources_cataloged']}.",
        f"- Sources downloaded: {closeout['sources_downloaded']}.",
        f"- Expert packets prepared: {closeout['expert_packets_prepared']}.",
        f"- L0-L3 gaps recorded: {closeout['l0_l3_gaps_recorded']}.",
        f"- Planned next tasks: {closeout['planned_next_tasks']}.",
        "- Replay executed: 0.",
        "- Strategy acceptance: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "The broad public-filer proxy backtest failed because the project had a broad universe without a serious L0-L3 front brain.",
        "",
        "The new plan separates the front brain into:",
        "",
        "1. L0 tradable-object and candidate-compression layer.",
        "2. L1 source packet layer.",
        "3. L2 economic meaning extractor.",
        "4. L3 relation network for company-industry-policy-demand-risk links.",
        "",
        "Expert packets are prepared for thematic, policy, macro, quant, and engineering review. GPT/expert review is review-only and cannot accept the strategy.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "The model failed because it was asked to choose from a big market without a real front brain.",
        "",
        "This task gathers the source base and turns the failure into a concrete L0-L3 build plan.",
        "",
        "Next work should implement candidate filtering and compression before any new PnL replay.",
        "",
        "## Artifact Manifest",
        "",
        "- `data/artifacts/task_1181_1190_l0_l3_strengthening_plan/task1181_source_catalog.csv`",
        "- `data/artifacts/task_1181_1190_l0_l3_strengthening_plan/task1181_download_ledger.csv`",
        "- `data/artifacts/task_1181_1190_l0_l3_strengthening_plan/task1182_project_context_packet.csv`",
        "- `data/artifacts/task_1181_1190_l0_l3_strengthening_plan/task1183_expert_roster.csv`",
        "- `data/artifacts/task_1181_1190_l0_l3_strengthening_plan/task1184_l0_l3_gap_matrix.csv`",
        "- `data/artifacts/task_1181_1190_l0_l3_strengthening_plan/task1185_l0_l3_strengthening_plan.csv`",
        "- `data/artifacts/task_1181_1190_l0_l3_strengthening_plan/task1186_subagent_packet_index.csv`",
        "- `data/artifacts/task_1181_1190_l0_l3_strengthening_plan/task1190_l0_l3_plan_closeout.csv`",
        "- `data/artifacts/task_1181_1190_l0_l3_strengthening_plan/task1190_l0_l3_plan_closeout.json`",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(REPORT_DIR / "task_1181_1190_decision.csv", [closeout])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    catalog = source_catalog()
    downloads = download_sources(catalog)
    context = project_context_packet()
    experts = expert_roster()
    gaps = gap_matrix()
    plan = strengthening_plan()
    packets = subagent_packets(experts)
    write_expert_packet_docs(experts, context)
    closeout = {
        "task_id": "Task1181-1190",
        "verdict": "l0_l3_front_brain_strengthening_plan_ready",
        "sources_cataloged": len(catalog),
        "sources_downloaded": sum(1 for row in downloads if row["download_status"] in {"downloaded", "already_downloaded"}),
        "expert_packets_prepared": len(experts),
        "l0_l3_gaps_recorded": len(gaps),
        "planned_next_tasks": len(plan),
        "replay_executed": "0",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "implement_task1191_1200_l0_l3_candidate_compression_before_any_new_replay",
        "authority": AUTHORITY,
    }

    write_csv(OUT_DIR / "task1181_source_catalog.csv", catalog)
    write_csv(OUT_DIR / "task1181_download_ledger.csv", downloads)
    write_csv(OUT_DIR / "task1182_project_context_packet.csv", context)
    write_csv(OUT_DIR / "task1183_expert_roster.csv", experts)
    write_csv(OUT_DIR / "task1184_l0_l3_gap_matrix.csv", gaps)
    write_csv(OUT_DIR / "task1185_l0_l3_strengthening_plan.csv", plan)
    write_csv(OUT_DIR / "task1186_subagent_packet_index.csv", packets)
    write_csv(OUT_DIR / "task1190_l0_l3_plan_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1190_l0_l3_plan_closeout.json", closeout)
    write_report(closeout)
    print(
        "[TRADER_BRAIN_1181_1190_L0_L3_STRENGTHENING_PLAN_OK] "
        f"sources={closeout['sources_downloaded']}/{closeout['sources_cataloged']} "
        f"experts={closeout['expert_packets_prepared']} "
        f"gaps={closeout['l0_l3_gaps_recorded']} "
        f"next_tasks={closeout['planned_next_tasks']} "
        "replay=0"
    )


if __name__ == "__main__":
    main()
