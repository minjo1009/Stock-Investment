# Task817 Graph Failure Report Contract

## Decision Summary

- Verdict: `GRAPH_FAILURE_REPORT_CONTRACT_DESIGNED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: sample failure report generated; failure classes include `missing_required_evidence`; expected failure fixture included.
- What changed: Task817 now provides a human-readable and machine-readable validator failure report through the batch runner.
- Next action: Keep failure classes stable before adding new validator rules.

## Quant Expert Report

Validator failures are actionable without allowing manual waiver drift. Failure classes include schema_missing, bad_reference, missing_required_evidence, unsafe_layer_jump, temporal_order_error, source_gap_conversion, forbidden_output, and manifest_orphan.

PASS remains diagnostic. FAIL blocks the packet from downstream research review but does not make any trading statement.

## No-Background Decision-Maker Report

1. Done: 실패 리포트 샘플을 생성했다.
2. Why: validator가 틀렸다고만 하면 운영이 안 된다. 누가 무엇을 고쳐야 하는지 보여야 한다.
3. Not done: 실패나 통과를 매매 성과로 해석하지 않는다.
4. Next: Task818 CI governance gate로 연결한다.

## Artifact Manifest

- Inputs: Task814 batch runner contract.
- Outputs: `sample_failure_report.csv`; `fixtures/bad_missing_edge_evidence/`.
- Validation commands: `python scripts/trader_brain_graph_batch_validate.py --manifest docs/reports/task_814_graph_batch_runner_contract/batch_manifest.csv --output docs/reports/task_817_graph_failure_report_contract/sample_failure_report.csv`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
