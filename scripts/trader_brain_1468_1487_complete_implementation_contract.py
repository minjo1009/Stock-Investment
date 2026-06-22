from __future__ import annotations

import csv
import json
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/task_1468_1487_complete_implementation_context"
OUT_DIR = ROOT / "data/artifacts/task_1468_1487_complete_implementation_contract"
REPORT_DIR = ROOT / "docs/reports/task_1468_1487_complete_implementation_contract"

AUTHORITY = "DIAGNOSTIC_COMPLETE_IMPLEMENTATION_CONTRACT_ONLY"


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


def source_catalog() -> list[dict[str, object]]:
    ledger = read_csv(RAW_DIR / "source_download_ledger.csv")
    roles = {
        "sec_form_8k.pdf": ("materiality_disclosure", "Form 8-K Item 1.01/2.03/3.02/5.02 style material event grounding"),
        "sec_reg_fd.html": ("fair_disclosure_expectation", "public availability and selective disclosure boundary"),
        "fama_french_data_library.html": ("factor_context", "size/value/market factor context for small-cap and style controls"),
        "fama_french_momentum_detail.html": ("market_acceptance", "momentum factor context for absorption and persistence"),
        "bis_semiconductor_export_controls.html": ("semiconductor_policy_risk", "export-control catalyst and invalidation context"),
        "nist_ai_rmf.pdf": ("ai_operating_risk", "AI risk, governance, and operational-risk context"),
        "faa_commercial_transportation_licensing.pdf": ("space_license_risk", "launch/reentry license and regulatory milestone context"),
        "doe_data_center_electricity_demand.html": ("power_grid_ai_demand", "data-center electricity demand and grid bottleneck context"),
        "fda_clinical_trials_guidance.html": ("biotech_clinical_risk", "trial design, endpoint, and FDA process context"),
        "sec_financial_reporting_manual_topic4.html": ("survival_going_concern", "going-concern and financial difficulty disclosure context"),
    }
    rows = []
    for idx, row in enumerate(ledger, 1):
        role, use = roles.get(row["source_name"], ("general_context", "supporting context"))
        rows.append(
            {
                "task_id": "Task1468",
                "source_id": f"SRC1468-{idx:03d}",
                "source_name": row["source_name"],
                "url": row["url"],
                "local_path": row["local_path"],
                "download_state": row["download_state"],
                "bytes": row["bytes"],
                "source_role": role,
                "implementation_use": use,
                "source_authority": "official_or_primary_reference_when_downloaded",
                "authority": AUTHORITY,
            }
        )
    return rows


def expert_definition() -> list[dict[str, object]]:
    rows = [
        ("institutional_quant_pm", "complete means materiality is a conditional feature, not a standalone alpha score", "must require event type, source quality, expectation, and absorption components"),
        ("event_driven_trader", "complete means the system can say big-good, big-dangerous, big-neutral, and big-unknown separately", "must not treat contract, financing, dilution, and survival events as the same"),
        ("semiconductor_specialist", "complete means export-control, customer capex, inventory cycle, and supply constraints are explicit modifiers", "must not treat AI/semiconductor demand language as positive without constraint checks"),
        ("ai_software_specialist", "complete means AI claims are tied to ARR, margin, retention, customer lock-in, or capacity access", "must not treat AI feature language as surprise"),
        ("space_specialist", "complete means funded backlog, launch license, mission success, and milestone payment are separated", "must not treat award headline value as cash-like revenue"),
        ("power_grid_specialist", "complete means order/backlog is checked against grid connection, lead time, input cost, and rate recovery", "must not treat demand growth as monetization by default"),
        ("biotech_specialist", "complete means endpoint/FDA/cash runway/dilution states are separated", "must not treat clinical milestone as positive without endpoint or capital context"),
        ("backend_data_auditor", "complete means every row has evidence ids, timestamps, gap states, and no outcome assignment", "must preserve audit-only outcome fields"),
        ("backtest_governance", "complete means the rule is pre-registered before replay and validated with invariant checks", "must not tune after seeing replay result"),
        ("risk_manager", "complete means source-gap is uncertainty, not negative evidence", "must not crowd out strong expectation/absorption candidates only because denominator is missing"),
    ]
    return [
        {
            "task_id": "Task1469",
            "expert_id": f"EXPERT1469-{idx:03d}",
            "expert_role": role,
            "complete_implementation_definition": definition,
            "non_negotiable_warning": warning,
            "review_authority": "GPT_SUBAGENT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, definition, warning) in enumerate(rows, 1)
    ]


def completion_criteria() -> list[dict[str, object]]:
    criteria = [
        ("L1", "source_time_evidence", "Every assigned primitive row links to source ids and available_to_brain_ts <= decision_asof_ts", "block_assignment_if_time_missing_for_positive_claim"),
        ("L1", "source_family_separation", "SEC filing, exhibit, IR/CEO, contract/order, policy/news, market data, analyst PIT are separate families", "issuer-only evidence cannot become independent confirmation"),
        ("L2", "event_family_semantics", "High materiality is split into positive, survival, financing, dilution, mixed, unknown with reason codes", "no keyword-only final classification without context fields"),
        ("L2", "materiality_conditionality", "Materiality is a magnitude input gated by event family, expectation, absorption, and source quality", "no standalone high-materiality bonus"),
        ("L2", "expectation_quality", "Expectation is split into good words, guidance change, prior-baseline change, analyst PIT gap, and true surprise", "good words are not surprise"),
        ("L2", "absorption_quality", "Absorption is split into initial reaction, persistence, reversal, relative strength, and volume quality", "one positive return window is not market acceptance"),
        ("L2", "small_cap_adjustment", "Ratio materiality is capped by as-of market cap/liquidity/float and not by realized performance", "small company ratio spike cannot dominate score"),
        ("L2", "source_gap_neutrality", "Missing denominator or analyst PIT is recorded as source_gap, not negative label", "gap cannot become hidden penalty"),
        ("L3", "mechanism_edges", "Edges explain why event affects revenue, margin, cash runway, dilution, budget, policy, or expectation", "generic supports/weakens edge is insufficient"),
        ("L3", "theme_modifiers", "Semis/AI/space/power/biotech/software/industrial modifiers are explicit and source-backed", "same materiality formula cannot mean same thing across themes"),
        ("L4", "thesis_card", "Candidate card contains event family, materiality condition, expectation state, absorption state, invalidation state, and gap state", "rank score alone is not a thesis"),
        ("L4", "winner_displacement_audit", "Old-only, new-only, overlap, restored, and dropped rows are audited with outcome-only returns", "audit outcomes cannot feed assignment"),
        ("L5", "policy_preregistration", "Policy formula, caps, tie-breakers, universe, costs, exits, and benchmark are frozen before replay", "no post-result weight changes"),
        ("L5", "exit_receipt_split", "Source receipt exit and price-path risk exit are separate families", "post-entry price path cannot influence L2-L4 assignment"),
        ("validation", "deterministic_fixtures", "Positive/survival/financing/dilution/unknown fixtures must test event-family extraction", "no untested semantic branch"),
        ("validation", "invariant_ledger", "No future leakage, no missing-as-negative, no outcome assignment, no fallback matching", "test pass does not mean acceptance"),
        ("report", "decision_maker_report", "Report says done/failed/next and preserves NOT_ACCEPTED/FORBIDDEN status", "diagnostic result cannot be called deployment-ready"),
        ("artifact", "row_level_manifest", "Every canonical output has manifest row and validation command", "ad hoc CSV without manifest is incomplete"),
    ]
    return [
        {
            "task_id": "Task1470",
            "criterion_id": f"CRITERION1470-{idx:03d}",
            "layer": layer,
            "criterion_name": name,
            "done_means": done,
            "not_complete_if": not_complete,
            "authority": AUTHORITY,
        }
        for idx, (layer, name, done, not_complete) in enumerate(criteria, 1)
    ]


def primitive_contract() -> list[dict[str, object]]:
    rows = [
        ("event_family", "positive", "contract/order/backlog/revenue/customer evidence with non-financing context and source-time pass", "L2"),
        ("event_family", "survival", "going concern, default, delisting, material weakness, cash runway stress, covenant distress", "L2"),
        ("event_family", "financing", "debt, credit facility, senior notes, liquidity raise, cash preservation without growth validation", "L2"),
        ("event_family", "dilution", "ATM, warrant, convertible, registered direct, equity offering, share issuance", "L2"),
        ("expectation", "good_words", "strong/record/raise words without prior baseline or analyst/guidance timestamp", "L2"),
        ("expectation", "guidance_change", "company guidance explicitly raised/lowered versus prior statement", "L2"),
        ("expectation", "true_surprise", "PIT estimate or explicit prior baseline breached by current source", "L2"),
        ("absorption", "initial_reaction", "pre-decision event-to-decision relative return", "L2"),
        ("absorption", "persistence", "multi-window relative strength that avoids full reversal before decision", "L2"),
        ("absorption", "reversal", "initial positive reaction later retraced before decision", "L2"),
        ("materiality", "absolute_size", "event value in USD with source context", "L2"),
        ("materiality", "ratio_size", "event value to revenue/market cap/cash/assets with as-of denominator", "L2"),
        ("materiality", "conditional_score", "ratio size only contributes after event family and quality gates", "L4"),
        ("audit", "displacement", "old-only/new-only/overlap/restored groups with outcome-only returns", "validation"),
    ]
    return [
        {
            "task_id": "Task1471",
            "primitive_id": f"PRIM1471-{idx:03d}",
            "primitive_family": family,
            "primitive_name": name,
            "required_evidence": evidence,
            "target_layer": layer,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (family, name, evidence, layer) in enumerate(rows, 1)
    ]


def sector_rulebook() -> list[dict[str, object]]:
    sectors = [
        (
            "semiconductor",
            "named customer design win; production qualification; volume shipment; long-term supply agreement; backlog or gross margin improvement",
            "inventory write-down; customer pushout; export restriction; capacity shortage; ATM or convertible funding",
            "customer_name; product; node_nm; units; ASP; backlog_usd; revenue_timing; gross_margin; capex_required; export_license_status; dilution_pct",
            "AI chip keyword, tape-out, and LOI are not revenue by themselves",
        ),
        (
            "ai_software",
            "signed enterprise contract; ARR/RPO growth; paid seat expansion; NRR improvement; usage-to-revenue conversion; gross margin improvement",
            "free pilot; usage cost surge; churn; CAC/payback deterioration; compute liability; down-round financing",
            "ARR; RPO; ACV; contract_term; paid_seats; NRR; churn; gross_margin; inference_cost; customer_name; renewal_status",
            "AI partnership or feature launch is noise unless paid conversion or margin context exists",
        ),
        (
            "space",
            "obligated funded award; launch success plus payload acceptance; FAA/FCC/DoD milestone approval; service revenue start",
            "launch delay/failure; milestone miss; going concern; ATM funding for launch cadence; debt maturity",
            "award_value; obligated_value; contract_type; agency; milestone; launch_date; payload_status; satellites_operational; cash_burn; runway_months",
            "contract ceiling is not obligated funding; successful launch is only partial without service revenue",
        ),
        (
            "power_grid",
            "signed PPA; interconnection approval; regulated rate-base approval; data-center load contract; firm delivery date",
            "permit delay; transformer shortage; cost overrun; wildfire liability; equity raise for project survival",
            "MW; PPA_price; tenor_years; counterparty; interconnect_status; COD_date; capex; project_IRR; rate_base; debt_cost",
            "AI power demand theme is not positive without PPA/interconnect/COD economics",
        ),
        (
            "biotech",
            "FDA approval; positive pivotal endpoint; label expansion; reimbursement; partnership upfront cash; commercial launch traction",
            "CRL; trial halt; safety signal; endpoint miss; runway under 12 months; going concern; ATM/PIPE after failure",
            "trial_phase; endpoint_primary; p_value_or_HR_CI; safety_AE; FDA_status; PDUFA_date; label; upfront_usd; cash; burn; runway; warrant_terms",
            "promising data or phase 1 biomarker is not commercial positive without endpoint and capital context",
        ),
        (
            "industrial",
            "firm order; backlog conversion; book-to-bill above 1; margin-accretive pricing; customer acceptance; obligated government award",
            "order cancellation; working-capital squeeze; inventory build; warranty charge; labor strike; covenant stress",
            "order_value; backlog; book_to_bill; delivery_schedule; margin; customer; cancellation_terms; working_capital; inventory_days; covenant",
            "backlog growth is weak without margin, cancellation terms, and conversion schedule",
        ),
    ]
    return [
        {
            "task_id": "Task1472",
            "sector_rule_id": f"SECTOR1472-{idx:03d}",
            "sector": sector,
            "positive_evidence": positive,
            "survival_financing_dilution_evidence": negative,
            "required_fields": fields,
            "trap": trap,
            "authority": AUTHORITY,
        }
        for idx, (sector, positive, negative, fields, trap) in enumerate(sectors, 1)
    ]


def validation_contract() -> list[dict[str, object]]:
    tests = [
        ("schema_test", "required columns, enums, null policy, and version fields exist"),
        ("source_time_test", "all assignment inputs have available_to_brain_ts <= decision_asof_ts"),
        ("no_future_leakage_test", "future return, future price, future filing, and label columns are unavailable to ranker"),
        ("audit_only_outcome_test", "outcome panel cannot be joined into score/rank/selection inputs"),
        ("deterministic_extractor_test", "same input and rule version produce same output and hash"),
        ("golden_fixture_test", "hand-reviewed positive/survival/financing/dilution/unknown cases exact match"),
        ("negative_fixture_test", "future source, missing source approximation, proximity fallback, and missing-as-negative fail"),
        ("row_lineage_test", "every output row traces to evidence/source/rule/artifact ids"),
        ("preregistration_hash_test", "replay config and rule spec hash are frozen before replay"),
        ("report_authority_footer_test", "test success does not change acceptance/deployment/real-capital status"),
    ]
    return [
        {
            "task_id": "Task1473",
            "validation_id": f"VALID1473-{idx:03d}",
            "test_name": name,
            "required_check": check,
            "pass_does_not_mean": "strategy_acceptance_or_deployment_ready",
            "authority": AUTHORITY,
        }
        for idx, (name, check) in enumerate(tests, 1)
    ]


def implementation_plan() -> list[dict[str, object]]:
    tasks = [
        ("Task1474", "Build source-context semantic extractor contract", "Map raw source fields to event family inputs without outcome data"),
        ("Task1475", "Create deterministic semantic fixtures", "Add positive/survival/financing/dilution/unknown examples and negative fixtures"),
        ("Task1476", "Implement event-family extractor v2", "Use source family, form item, amount context, and theme modifier instead of keyword-only classification"),
        ("Task1477", "Implement expectation-quality extractor v2", "Separate good words, guidance change, prior-baseline change, analyst PIT gap, and true surprise"),
        ("Task1478", "Implement absorption-quality extractor v2", "Separate initial reaction, persistence, reversal, relative strength, and volume quality"),
        ("Task1479", "Implement source-gap-neutral materiality v2", "Keep denominator gaps neutral and cap ratio effects by as-of market cap/liquidity"),
        ("Task1480", "Implement theme modifier table", "Semis/AI/space/power/biotech/software/industrial rule primitives"),
        ("Task1481", "Build L3 mechanism edge upgrade", "Generate revenue/margin/cash/dilution/policy/expectation mechanism edges"),
        ("Task1482", "Build L4 complete thesis card", "Expose event family, materiality condition, expectation, absorption, invalidation and gaps"),
        ("Task1483", "Pre-register balanced ranker v6", "Freeze formula, caps, gaps, tie-breakers, split/OOS, costs, exits and benchmark"),
        ("Task1484", "Run controlled replay once", "Same top3/top5/top10 replay; no mid-run tuning"),
        ("Task1485", "Build displacement audit v2", "Audit old/full/v5/v6 groups with returns audit-only"),
        ("Task1486", "Run invariant validator and report", "No future leakage, no missing-as-negative, no outcome assignment, no fallback matching"),
        ("Task1487", "Closeout gate", "Keep NOT_ACCEPTED unless full acceptance contract separately passes"),
    ]
    return [
        {
            "task_id": task,
            "sequence": idx,
            "title": title,
            "deliverable": deliverable,
            "status": "planned",
            "authority": AUTHORITY,
        }
        for idx, (task, title, deliverable) in enumerate(tasks, 1)
    ]


def acceptance_gate() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1487",
            "decision": "complete_implementation_contract_defined_not_strategy_acceptance",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_action": "implement Task1472-1487 semantic extractor and balanced v6 replay under this contract",
            "authority": AUTHORITY,
        }
    ]


def write_report(
    sources: list[dict[str, object]],
    experts: list[dict[str, object]],
    criteria: list[dict[str, object]],
    plan: list[dict[str, object]],
    gate: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = sum(1 for row in sources if row["download_state"] == "downloaded")
    report = f"""# Task1468-1487 Complete Implementation Contract

## Decision Summary

- Verdict: `complete_implementation_contract_defined_not_accepted`.
- Downloaded source context: {downloaded}/{len(sources)}.
- Expert review rows: {len(experts)}.
- Completion criteria rows: {len(criteria)}.
- Planned implementation tasks: {len(plan)}.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Meaning of complete implementation: semantic extraction must be source-time safe, theme-aware, deterministic, row-level auditable, and replay-frozen before results.

## Quant Expert Report

- `materiality` is not alpha by itself. It is a magnitude ruler.
- `high materiality` must first become event family: positive, survival, financing, dilution, mixed, or unknown.
- `expectation` must separate good language from prior-baseline change or PIT surprise.
- `absorption` must separate initial reaction from persistence, reversal, and relative-strength quality.
- `source_gap` is uncertainty and must not become a hidden negative.
- Outcome returns may appear only in displacement audit artifacts.

## No-Background Decision-Maker Report

완벽 구현은 점수식 튜닝이 아니다.

원문이 무엇을 뜻하는지 먼저 정확히 분해해야 한다.

그 다음에만 ranker와 replay가 의미 있다.

이번 task는 구현 완료 기준을 고정했다.

전략은 아직 승인되지 않았다.

## Artifact Manifest

- `task1468_source_catalog.csv`
- `task1469_expert_complete_implementation_definition.csv`
- `task1470_completion_criteria.csv`
- `task1471_primitive_contract.csv`
- `task1472_sector_rulebook.csv`
- `task1473_validation_contract.csv`
- `task1474_1487_implementation_plan.csv`
- `task1487_acceptance_gate.csv`
- `task1487_closeout.json`

Validation commands:

- `python scripts/trader_brain_1468_1487_complete_implementation_contract_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1468_1487_complete_implementation_contract.md").write_text(report, encoding="utf-8")
    write_csv(REPORT_DIR / "task_1468_1487_decision.csv", [gate])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sources = source_catalog()
    experts = expert_definition()
    criteria = completion_criteria()
    primitives = primitive_contract()
    sectors = sector_rulebook()
    validations = validation_contract()
    plan = implementation_plan()
    gate = acceptance_gate()
    closeout = {
        "task_id": "Task1487",
        "verdict": "complete_implementation_contract_defined_not_accepted",
        "source_rows": len(sources),
        "expert_rows": len(experts),
        "completion_criteria_rows": len(criteria),
        "primitive_rows": len(primitives),
        "sector_rule_rows": len(sectors),
        "validation_contract_rows": len(validations),
        "planned_task_rows": len(plan),
        **gate[0],
    }
    outputs = [
        ("task1468_source_catalog.csv", sources),
        ("task1469_expert_complete_implementation_definition.csv", experts),
        ("task1470_completion_criteria.csv", criteria),
        ("task1471_primitive_contract.csv", primitives),
        ("task1472_sector_rulebook.csv", sectors),
        ("task1473_validation_contract.csv", validations),
        ("task1474_1487_implementation_plan.csv", plan),
        ("task1487_acceptance_gate.csv", gate),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1487_closeout.json", closeout)
    write_report(sources, experts, criteria, plan, gate[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
