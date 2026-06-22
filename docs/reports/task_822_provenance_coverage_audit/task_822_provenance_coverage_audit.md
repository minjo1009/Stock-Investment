# Task822 Provenance Coverage Audit

## Decision Summary

- Verdict: `PROVENANCE_COVERAGE_AUDIT_IMPLEMENTED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 44 graph evidence references audited; 0 orphan references detected.
- What changed: Added a provenance coverage audit that checks graph node and edge evidence ids against the provenance manifest.
- Next action: Rerun audit whenever fixture evidence ids change.

## Quant Expert Report

The audit checks explicit evidence ids only. It covers `evidence_id` and `edge_evidence_id` fields in node and edge files across Task813 and Task821 graph fixtures.

No inferred matching, fuzzy artifact matching, raw source approximation, labels, PnL, rank, score, buy/sell, sizing, backtest eligibility, runtime, broker integration, or real-capital permission is introduced.

## No-Background Decision-Maker Report

1. Done: graph evidence id 44개를 점검했다.
2. Done: orphan evidence는 0개다.
3. Important: 명시 id만 본다. 추정 매칭은 없다.
4. Next: fixture가 늘어나면 다시 실행한다.

## Artifact Manifest

- Inputs: Task813 and Task821 graph fixtures; Task816 provenance manifest.
- Outputs: `provenance_coverage_audit.csv`; `scripts/trader_brain_provenance_coverage_audit.py`.
- Validation commands: `python scripts/trader_brain_provenance_coverage_audit.py --graph-dir docs/reports/task_813_golden_graph_fixture_pack/fixtures/ai_capex_mechanism_graph --graph-dir docs/reports/task_813_golden_graph_fixture_pack/fixtures/macro_policy_source_gap_graph --graph-dir docs/reports/task_821_graph_fixture_corpus_expansion/fixtures/semiconductor_export_control_graph --graph-dir docs/reports/task_821_graph_fixture_corpus_expansion/fixtures/space_defense_policy_graph --provenance-manifest docs/reports/task_816_provenance_manifest_linker_contract/provenance_manifest.csv --output docs/reports/task_822_provenance_coverage_audit/provenance_coverage_audit.csv`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
