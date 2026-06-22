from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT_DIR = ROOT / "docs" / "reports" / "task_756_trader_brain_15_step_program"

STANDING = """Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
"""

STEPS = [
    {
        "task_id": "Task757",
        "slug": "brain_dependency_dag_supersession",
        "title": "Brain Dependency DAG And Supersession Audit",
        "brain_layer": "qa_resolver",
        "owner_team": "Research Governance",
        "objective": "Map Task727-742 files, reports, tests, current/superseded status, and dependency order before touching implementation.",
        "success_criteria": "One current/superseded map exists; no active brain file is reused without a stated owner and output contract.",
        "forbidden_actions": "No code promotion, no strategy claim, no deleting historical task files.",
        "minimal_artifacts": "brain_dependency_dag.csv; current_supersession_map.csv; task_757_decision.csv",
        "validation_command": "python scripts/trader_brain_program_validate.py",
        "overengineering_stop_rule": "Classify files and dependencies only; do not refactor the whole backtest folder.",
    },
    {
        "task_id": "Task758",
        "slug": "l1_evidence_contract",
        "title": "L1 Evidence Contract And Context Retention",
        "brain_layer": "source_evidence",
        "owner_team": "Data & Market Microstructure",
        "objective": "Define good-enough source evidence fields and keep non-operating sources as context instead of discarding them.",
        "success_criteria": "Evidence contract separates direct operating evidence, financing, ownership, Form4, 13D/G, macro/policy, and context-only evidence.",
        "forbidden_actions": "No source text to buy/sell jump; no source family blanket block.",
        "minimal_artifacts": "l1_evidence_contract.md; l1_source_family_policy.csv; task_758_decision.csv",
        "validation_command": "python -m unittest tests.test_task731_source_information_router",
        "overengineering_stop_rule": "Use source family, timestamp, trace, novelty, directness, contamination; do not demand every possible denominator.",
    },
    {
        "task_id": "Task759",
        "slug": "l2_primitive_fact_contract",
        "title": "L2 Primitive Fact Contract Unification",
        "brain_layer": "primitive_fact",
        "owner_team": "Data & Market Microstructure",
        "objective": "Unify Task730 and Task740 primitive outputs into source-local facts that do not imply bullish or bearish meaning.",
        "success_criteria": "PrimitiveFact contract declares field provenance, evidence span, as-of timestamp, and extraction confidence.",
        "forbidden_actions": "No economic promotion inside primitive extraction; no missing fact to negative conversion.",
        "minimal_artifacts": "l2_primitive_fact_contract.md; primitive_fact_catalog.csv; task_759_decision.csv",
        "validation_command": "python -m unittest tests.test_task730_economic_reality_packet_builder tests.test_task740_engineering_high_resolver_completion",
        "overengineering_stop_rule": "Extract facts traders can reasonably act on; do not make every unresolved comparator a blocker.",
    },
    {
        "task_id": "Task760",
        "slug": "l3_pragmatic_meaning_contract",
        "title": "L3 Pragmatic Economic Meaning Contract",
        "brain_layer": "economic_meaning",
        "owner_team": "Regime Research",
        "objective": "Make Task742 the review-only practical meaning candidate and define direction hints, confidence, ambiguity, and confirmation needs.",
        "success_criteria": "Meaning objects cannot emit buy/sell/rank/sizing/backtest eligibility; uncertainty remains explicit.",
        "forbidden_actions": "No infinite denominator gate; no direction hint as trade instruction.",
        "minimal_artifacts": "l3_pragmatic_meaning_contract.md; meaning_taxonomy.csv; task_760_decision.csv",
        "validation_command": "python -m unittest tests.test_task742_pragmatic_economic_meaning_layer",
        "overengineering_stop_rule": "Good-enough categories are allowed: growth funding, survival funding, non-plan insider sale, passive ownership, active control, reaffirmed guidance.",
    },
    {
        "task_id": "Task761",
        "slug": "task742_to_task729_adapter_contract",
        "title": "Task742 To Task729 Adapter Contract",
        "brain_layer": "relation_edge",
        "owner_team": "Backtest & Simulation Infra",
        "objective": "Design the adapter that feeds practical meaning packets into the relation engine without assigning trades.",
        "success_criteria": "Adapter maps evidence_id, primitive_id, meaning_state, confidence, and source trace to relation inputs.",
        "forbidden_actions": "No assignment output; no outcome fields; no price rescue of weak sources.",
        "minimal_artifacts": "task742_task729_adapter_contract.md; adapter_field_map.csv; task_761_decision.csv",
        "validation_command": "python -m unittest tests.test_task728_five_layer_interaction_logic_contract tests.test_task729_five_layer_interaction_engine_application",
        "overengineering_stop_rule": "Map existing packets first; do not build a new universal knowledge graph.",
    },
    {
        "task_id": "Task762",
        "slug": "primitive_gate_repair_design",
        "title": "Primitive Fact Gate Repair Design",
        "brain_layer": "relation_edge",
        "owner_team": "Backtest & Simulation Infra",
        "objective": "Replace fixed primitive_fact_gate_pass=0 behavior with explicit gate input from L2/L3 packets.",
        "success_criteria": "Gate states are pass, cap, context_only, not_ready, source_gap; all remain research-only.",
        "forbidden_actions": "No gate state may create backtest eligibility by itself.",
        "minimal_artifacts": "primitive_gate_repair_contract.md; gate_state_catalog.csv; task_762_decision.csv",
        "validation_command": "python -m unittest tests.test_task729_five_layer_interaction_engine_application",
        "overengineering_stop_rule": "Repair the hard-coded gate path only; do not rewrite the whole interaction engine in one task.",
    },
    {
        "task_id": "Task763",
        "slug": "typed_relation_edge_schema",
        "title": "Typed Relation Edge Schema",
        "brain_layer": "relation_edge",
        "owner_team": "Regime Research",
        "objective": "Define source_node, target_node, relation_type, precondition, confidence_cap, evidence_trace, and invalidation_link.",
        "success_criteria": "Edges express reinforcing, offsetting, prerequisite, blocker, sizing_modifier, confidence_cap, and invalidation without labels.",
        "forbidden_actions": "No giant brittle if/else tree; no future returns in edge creation.",
        "minimal_artifacts": "typed_relation_edge_schema.md; relation_type_catalog.csv; task_763_decision.csv",
        "validation_command": "python -m unittest tests.test_task727_economic_interaction_brain_contract tests.test_task728_five_layer_interaction_logic_contract",
        "overengineering_stop_rule": "Use typed node plus modifier structure; do not enumerate every possible world state.",
    },
    {
        "task_id": "Task764",
        "slug": "source_circuit_good_enough_interpreters",
        "title": "Source Circuit Good-Enough Interpreters",
        "brain_layer": "economic_meaning",
        "owner_team": "Data & Market Microstructure",
        "objective": "Set pragmatic interpretation rules for Form4, 13D/G, 13F, ownership, generic 8-K, financing 8-K, and macro/policy circuits.",
        "success_criteria": "Each circuit has good-enough states, uncertainty states, and stop rules.",
        "forbidden_actions": "No blanket block; no automatic bullish/bearish by source existence.",
        "minimal_artifacts": "source_circuit_good_enough_policy.md; circuit_state_catalog.csv; task_764_decision.csv",
        "validation_command": "python -m unittest tests.test_task732_source_circuit_interpreters",
        "overengineering_stop_rule": "For insider sales, planned/non-plan/purchase/compensation/tax is enough unless exact holdings are already available.",
    },
    {
        "task_id": "Task765",
        "slug": "modifier_contracts_regime_sector_price",
        "title": "Regime Sector Price Modifier Contracts",
        "brain_layer": "relation_edge",
        "owner_team": "Regime Research",
        "objective": "Define market regime, sector leadership, theme rotation, and price acceptance as modifiers, not standalone signals.",
        "success_criteria": "Modifiers can reinforce, cap, or require confirmation of L2 meaning, but cannot create candidates alone.",
        "forbidden_actions": "No regime-only or sector-only candidate creation; no price=meaning shortcut.",
        "minimal_artifacts": "modifier_contracts.md; modifier_state_catalog.csv; task_765_decision.csv",
        "validation_command": "python -m unittest tests.test_task728_five_layer_interaction_logic_contract",
        "overengineering_stop_rule": "Use a small modifier set: supportive, hostile, rotating, extended, accepted, rejected, unclear.",
    },
    {
        "task_id": "Task766",
        "slug": "compound_interaction_engine_contract",
        "title": "Compound Interaction Engine Contract",
        "brain_layer": "relation_edge",
        "owner_team": "Backtest & Simulation Infra",
        "objective": "Define how L1/L2/L3 modifiers combine through node+modifier rules instead of a giant rule tree.",
        "success_criteria": "Compound output explains thesis support, contradiction, confirmation, and invalidation path.",
        "forbidden_actions": "No single total score; no rank; no sizing; no backtest eligibility.",
        "minimal_artifacts": "compound_interaction_engine_contract.md; compound_rule_examples.csv; task_766_decision.csv",
        "validation_command": "python -m unittest tests.test_task729_five_layer_interaction_engine_application",
        "overengineering_stop_rule": "Cap rule families to a maintainable catalog; add examples before adding dimensions.",
    },
    {
        "task_id": "Task767",
        "slug": "candidate_bundle_contract",
        "title": "Candidate Thesis Bundle Contract",
        "brain_layer": "candidate_bundle",
        "owner_team": "Research Governance",
        "objective": "Create bundle requirements: thesis, evidence trail, relation edges, confirmations, contradictions, invalidations, weakest layer.",
        "success_criteria": "Bundles are explanatory objects only and expose why a candidate is not yet eligible.",
        "forbidden_actions": "No buy/sell action; no hidden rank; no missing context treated as rejection.",
        "minimal_artifacts": "candidate_thesis_bundle_contract.md; bundle_required_fields.csv; task_767_decision.csv",
        "validation_command": "python -m unittest tests.test_task737_semantic_modifier_bundle_attachment tests.test_task738_semantic_enrichment_requirements",
        "overengineering_stop_rule": "Require explanation fields, not a complete investment memo for every row.",
    },
    {
        "task_id": "Task768",
        "slug": "same_timestamp_slot_competition",
        "title": "Same-Timestamp Slot Competition Framework",
        "brain_layer": "slot_decision",
        "owner_team": "Backtest & Simulation Infra",
        "objective": "Define same timestamp cohort comparison inputs without global hindsight ranking.",
        "success_criteria": "Slot comparison only uses same entry_ts cohort, review-only bundle quality, and no outcomes.",
        "forbidden_actions": "No global top5 rank; no actual sizing; no future PnL.",
        "minimal_artifacts": "same_timestamp_slot_contract.md; slot_input_catalog.csv; task_768_decision.csv",
        "validation_command": "python -m unittest tests.test_task723_five_stage_decision_contract",
        "overengineering_stop_rule": "Compare relative readiness in cohort; do not build portfolio optimizer here.",
    },
    {
        "task_id": "Task769",
        "slug": "resolver_conflict_layer",
        "title": "Resolver And Conflict Layer",
        "brain_layer": "qa_resolver",
        "owner_team": "Research Governance",
        "objective": "Define how conflicting evidence, weak sources, missing comparators, and modifier disagreement create review packets.",
        "success_criteria": "Resolver emits repair_needed, review_needed, context_only, or ready_for_gate_review states.",
        "forbidden_actions": "No future data; no GPT-only resolution; no silent default pass.",
        "minimal_artifacts": "resolver_conflict_contract.md; conflict_state_catalog.csv; task_769_decision.csv",
        "validation_command": "python -m unittest tests.test_task739_semantic_resolver_upgrade_workbench",
        "overengineering_stop_rule": "Resolve to next action class, not to a perfect answer.",
    },
    {
        "task_id": "Task770",
        "slug": "brain_contract_validation",
        "title": "Brain Contract Validation",
        "brain_layer": "qa_resolver",
        "owner_team": "Research Governance",
        "objective": "Create validations for layer jumps, forbidden outputs, missing-as-negative, and outcome leakage.",
        "success_criteria": "Validation detects L1 to L5 bypass, buy/sell/rank/sizing outputs, outcome fields, and missing-to-negative behavior.",
        "forbidden_actions": "No performance test; no strategy acceptance wording.",
        "minimal_artifacts": "brain_validation_registry.csv; validation_gate_catalog.csv; task_770_decision.csv",
        "validation_command": "python scripts/trader_brain_program_validate.py",
        "overengineering_stop_rule": "Validate contracts and forbidden outputs first; do not run backtests here.",
    },
    {
        "task_id": "Task771",
        "slug": "canonical_brain_registry",
        "title": "Canonical Brain Registry And Backtest Gate Design",
        "brain_layer": "qa_resolver",
        "owner_team": "Research Governance",
        "objective": "Register the selected current brain contracts and define the future backtest eligibility gate without executing it.",
        "success_criteria": "Registry separates accepted current contract, superseded files, diagnostics, and future backtest prerequisites.",
        "forbidden_actions": "No acceptance status change; no deployment readiness; no live trading.",
        "minimal_artifacts": "canonical_brain_registry.csv; future_backtest_gate_contract.md; task_771_decision.csv",
        "validation_command": "python scripts/task_registry_validate.py",
        "overengineering_stop_rule": "Document the gate; do not connect to trading or backtest until engine split and validation gates are done.",
    },
]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row.get(col, "") for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def step_report(step: dict[str, str]) -> str:
    return f"""# {step['task_id']} {step['title']}

## Decision Summary

- Verdict: `PLANNED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `{step['brain_layer']}`
- Objective: {step['objective']}

## Quant Expert Report

This task is registered as part of the Task756 Trader Brain 15-step program.

Success criteria:

```text
{step['success_criteria']}
```

Forbidden actions:

```text
{step['forbidden_actions']}
```

Overengineering stop rule:

```text
{step['overengineering_stop_rule']}
```

Validation idea:

```text
{step['validation_command']}
```

## No-Background Decision-Maker Report

1. 이 단계는 Trader Brain을 더 단단하게 만들기 위한 연구/구조 작업입니다.
2. 매수/매도/랭킹/사이징/실거래 권한은 만들지 않습니다.
3. 필요한 산출물은 작게 만들고, 큰 패널은 manifest로만 관리합니다.

## Artifact Manifest

- Planned minimal artifacts: `{step['minimal_artifacts']}`
- Parent program: `docs/reports/task_756_trader_brain_15_step_program/task_756_trader_brain_15_step_program.md`
- Step registry: `docs/reports/task_756_trader_brain_15_step_program/step_registry.csv`

## Standing Footer

```text
{STANDING}```
"""


def write_step_reports() -> None:
    for step in STEPS:
        task_no = step["task_id"].replace("Task", "").lower()
        task_dir = ROOT / "docs" / "reports" / f"task_{task_no}_{step['slug']}"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / f"task_{task_no}_{step['slug']}.md").write_text(step_report(step), encoding="utf-8")
        write_csv(
            task_dir / f"task_{task_no}_decision.csv",
            [
                {"field": "task_id", "value": step["task_id"]},
                {"field": "decision", "value": "planned_research_only"},
                {"field": "brain_layer", "value": step["brain_layer"]},
                {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
                {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
                {"field": "real_capital", "value": "FORBIDDEN"},
            ],
            ["field", "value"],
        )


def write_parent_report() -> None:
    PARENT_DIR.mkdir(parents=True, exist_ok=True)
    compact = [
        {
            "task_id": step["task_id"],
            "title": step["title"],
            "layer": step["brain_layer"],
            "stop_rule": step["overengineering_stop_rule"],
        }
        for step in STEPS
    ]
    report = f"""# Task756 Trader Brain 15-Step Program

## Decision Summary

- Verdict: `TRADER_BRAIN_15_STEP_PROGRAM_DEFINED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Steps: 15
- Scope: Trader Brain reinspection, review, and development plan after Task754, while preserving Task755 as the engine strategy-adapter/shell split lane.

## Quant Expert Report

The program keeps the brain sequence explicit:

```text
L1 Source evidence
-> L2 Primitive fact
-> L3 Economic meaning
-> L4 Relation edge
-> L5 Candidate bundle / slot decision
-> Backtest/deployment gate
```

This plan follows the project rule that Task727-742 remain review-only until a smaller current subset is selected. It also incorporates the key code finding that Task729 currently has a fixed primitive gate path, while Task730/740/742 create better primitive/economic meaning packets that are not yet strongly reinjected into Task729.

Program steps:

{markdown_table(compact, ["task_id", "title", "layer", "stop_rule"])}

Core design rule:

```text
Do not build a giant brittle rule tree.
Build typed nodes plus modifiers:
source evidence + primitive fact + economic meaning + regime/sector/price/financing modifiers + slot context.
```

Good-enough interpretation examples:

```text
Form4: planned sale, non-plan sale, purchase, compensation/tax context.
Financing: growth funding, survival funding, refinance, working capital, dilution overhang.
13D/G/13F/ownership: passive, active/control, float/context, ownership noise.
Guidance/news: raise, reaffirm, cut, stale, new, direct operating, indirect context.
```

Hard guardrails:

```text
Economic interpretation != candidate selection.
Candidate selection != trade execution.
Trade execution != strategy acceptance.
GPT review != source-of-truth.
Missing data != negative label.
Price acceptance cannot rescue weak source evidence.
No outcome field enters assignment logic.
```

## No-Background Decision-Maker Report

1. 지금 뇌는 부품은 많지만, 부품끼리 연결이 약합니다.
2. 특히 Task742의 좋은 해석이 Task729 관계엔진으로 강하게 이어지지 않습니다.
3. 그래서 15단계는 새 데이터를 무한히 모으는 계획이 아닙니다.
4. 좋은 해석이 관계엔진, 후보 bundle, slot 판단까지 새지 않고 흐르게 만드는 계획입니다.
5. 그래도 이건 아직 매매 허가가 아닙니다.

## Artifact Manifest

- `step_registry.csv`
- `task756_summary.csv`
- `task_756_decision.csv`
- `gpt_review_notes.md`
- `subagent_packet_plan.md`
- `validation_log.md`
- child task placeholder reports: Task757-Task771
- `artifact_manifest.csv`

## Standing Footer

```text
{STANDING}```
"""
    (PARENT_DIR / "task_756_trader_brain_15_step_program.md").write_text(report, encoding="utf-8")


def write_parent_artifacts() -> None:
    step_fields = [
        "task_id",
        "slug",
        "title",
        "brain_layer",
        "owner_team",
        "objective",
        "success_criteria",
        "forbidden_actions",
        "minimal_artifacts",
        "validation_command",
        "overengineering_stop_rule",
    ]
    write_csv(PARENT_DIR / "step_registry.csv", STEPS, step_fields)
    write_csv(
        PARENT_DIR / "task756_summary.csv",
        [
            {"field": "task_id", "value": "Task756"},
            {"field": "verdict", "value": "TRADER_BRAIN_15_STEP_PROGRAM_DEFINED_RESEARCH_ONLY"},
            {"field": "step_count", "value": str(len(STEPS))},
            {"field": "child_range", "value": "Task757-Task771"},
            {"field": "task755_reserved_for", "value": "engine strategy adapter and shell split"},
            {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
            {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
            {"field": "real_capital", "value": "FORBIDDEN"},
            {"field": "next_safe_subagent_work", "value": "Task757, Task758, Task761"},
        ],
        ["field", "value"],
    )
    write_csv(
        PARENT_DIR / "task_756_decision.csv",
        [
            {"field": "task_id", "value": "Task756"},
            {"field": "decision", "value": "define_trader_brain_15_step_program_research_only"},
            {"field": "child_tasks", "value": "Task757-Task771"},
            {"field": "new_alpha_allowed", "value": "no"},
            {"field": "backtest_allowed", "value": "no"},
            {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
            {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
            {"field": "real_capital", "value": "FORBIDDEN"},
        ],
        ["field", "value"],
    )
    (PARENT_DIR / "gpt_review_notes.md").write_text(
        """# Task756 GPT Review Notes

GPT was given onboarding-level project context and asked to review the program as five roles:

1. Institutional PM/trader.
2. Equity strategist.
3. Quant risk reviewer.
4. Professional backend architect.
5. Research governance reviewer.

Applied conclusions:

1. Keep Task755 reserved for engine strategy adapter/shell split.
2. Use Task756 as the Trader Brain 15-step parent.
3. Use Task757-Task771 for the 15 brain steps.
4. Do not overdesign with infinite denominators.
5. Use good-enough interpretation plus explicit uncertainty.
6. Make Task742 -> Task729 adapter/gate repair a core part of the plan.
7. Use node + modifier interaction instead of a giant brittle rule tree.
""",
        encoding="utf-8",
    )
    (PARENT_DIR / "subagent_packet_plan.md").write_text(
        """# Task756 Subagent Packet Plan

Use bounded packets from `docs/ownership/subagent_packet_standard.md`.

## Packet 1

Objective: Task757 brain dependency DAG and supersession audit.
Owner Team: Research Governance.
Reviewer Team: Backtest & Simulation Infra.
Read Scope: Task727-742 source files, reports, tests, registry rows.
Write Scope: `docs/reports/task_757_brain_dependency_dag_supersession/`.
Forbidden Actions: no code edits, no task file deletion, no strategy/deployment claim.
Validation Command: `python scripts/trader_brain_program_validate.py`.
Validation Authority: Research-only governance validation.

## Packet 2

Objective: Task758 L1 evidence contract and context retention.
Owner Team: Data & Market Microstructure.
Reviewer Team: Research Governance.
Read Scope: Task722, Task731, Task735 reports and source router code.
Write Scope: `docs/reports/task_758_l1_evidence_contract/`.
Forbidden Actions: no source family blanket block, no source-to-trade jump.
Validation Command: `python -m unittest tests.test_task731_source_information_router`.
Validation Authority: Research-only source routing validation.

## Packet 3

Objective: Task761 Task742-to-Task729 adapter contract.
Owner Team: Backtest & Simulation Infra.
Reviewer Team: Research Governance + Regime Research.
Read Scope: Task742 packets, Task728 contract, Task729 interaction engine reports/code.
Write Scope: `docs/reports/task_761_task742_to_task729_adapter_contract/`.
Forbidden Actions: no assignment output, no outcome fields, no backtest eligibility.
Validation Command: `python -m unittest tests.test_task728_five_layer_interaction_logic_contract tests.test_task729_five_layer_interaction_engine_application`.
Validation Authority: Research-only interaction validation.
""",
        encoding="utf-8",
    )
    (PARENT_DIR / "validation_log.md").write_text(
        """# Task756 Validation Log

Planned commands:

```text
python scripts\\task756_trader_brain_program_plan.py
python scripts\\trader_brain_program_validate.py
python scripts\\task_artifact_manifest.py --task-dir docs\\reports\\task_756_trader_brain_15_step_program
python scripts\\task_registry_validate.py
python scripts\\operating_closeout_validate.py
```
""",
        encoding="utf-8",
    )


def main() -> None:
    write_parent_report()
    write_parent_artifacts()
    write_step_reports()
    print(f"[TASK756] wrote={PARENT_DIR}")


if __name__ == "__main__":
    main()
