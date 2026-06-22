# Task814 Graph Batch Runner Contract

## Decision Summary

- Verdict: `GRAPH_BATCH_RUNNER_CONTRACT_DESIGNED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: batch runner implemented as `scripts/trader_brain_graph_batch_validate.py`; 4 packet manifest rows; expected-pass and expected-fail handling supported.
- What changed: Task814 now provides manifest-driven validation across graph and attention packets.
- Next action: Use the batch runner for small diagnostic packet sets only.

## Quant Expert Report

The batch runner reads a manifest of packet directories and runs existing validators against each packet. It aggregates pass/fail counts, file paths, and failure classes. It does not assign alpha quality, confidence score, rank, buy/sell signal, backtest eligibility, or production readiness.

The batch runner must preserve asof order and packet identity. It may not merge packets through symbol/date/price/time proximity.

## No-Background Decision-Maker Report

1. Done: 여러 packet을 한 번에 검사하는 CLI를 만들었다.
2. Why: 한 개 샘플 통과만으로 운영 가능하다고 착각하지 않기 위해서다.
3. Not done: 런타임, 브로커, 백테스트는 붙이지 않는다.
4. Next: Task817 failure report와 연결한다.

## Artifact Manifest

- Inputs: Task813 fixture design.
- Outputs: `batch_manifest.csv`; `scripts/trader_brain_graph_batch_validate.py`.
- Validation commands: `python scripts/trader_brain_graph_batch_validate.py --manifest docs/reports/task_814_graph_batch_runner_contract/batch_manifest.csv --output docs/reports/task_817_graph_failure_report_contract/sample_failure_report.csv`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
