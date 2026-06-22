# Task756 Trader Brain 15-Step Program

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

| task_id | title | layer | stop_rule |
| --- | --- | --- | --- |
| Task757 | Brain Dependency DAG And Supersession Audit | qa_resolver | Classify files and dependencies only; do not refactor the whole backtest folder. |
| Task758 | L1 Evidence Contract And Context Retention | source_evidence | Use source family, timestamp, trace, novelty, directness, contamination; do not demand every possible denominator. |
| Task759 | L2 Primitive Fact Contract Unification | primitive_fact | Extract facts traders can reasonably act on; do not make every unresolved comparator a blocker. |
| Task760 | L3 Pragmatic Economic Meaning Contract | economic_meaning | Good-enough categories are allowed: growth funding, survival funding, non-plan insider sale, passive ownership, active control, reaffirmed guidance. |
| Task761 | Task742 To Task729 Adapter Contract | relation_edge | Map existing packets first; do not build a new universal knowledge graph. |
| Task762 | Primitive Fact Gate Repair Design | relation_edge | Repair the hard-coded gate path only; do not rewrite the whole interaction engine in one task. |
| Task763 | Typed Relation Edge Schema | relation_edge | Use typed node plus modifier structure; do not enumerate every possible world state. |
| Task764 | Source Circuit Good-Enough Interpreters | economic_meaning | For insider sales, planned/non-plan/purchase/compensation/tax is enough unless exact holdings are already available. |
| Task765 | Regime Sector Price Modifier Contracts | relation_edge | Use a small modifier set: supportive, hostile, rotating, extended, accepted, rejected, unclear. |
| Task766 | Compound Interaction Engine Contract | relation_edge | Cap rule families to a maintainable catalog; add examples before adding dimensions. |
| Task767 | Candidate Thesis Bundle Contract | candidate_bundle | Require explanation fields, not a complete investment memo for every row. |
| Task768 | Same-Timestamp Slot Competition Framework | slot_decision | Compare relative readiness in cohort; do not build portfolio optimizer here. |
| Task769 | Resolver And Conflict Layer | qa_resolver | Resolve to next action class, not to a perfect answer. |
| Task770 | Brain Contract Validation | qa_resolver | Validate contracts and forbidden outputs first; do not run backtests here. |
| Task771 | Canonical Brain Registry And Backtest Gate Design | qa_resolver | Document the gate; do not connect to trading or backtest until engine split and validation gates are done. |

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
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
