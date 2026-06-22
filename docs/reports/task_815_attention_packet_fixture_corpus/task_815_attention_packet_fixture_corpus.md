# Task815 Attention Packet Fixture Corpus

## Decision Summary

- Verdict: `ATTENTION_FIXTURE_CORPUS_DESIGNED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 5 attention fixture rows; states cover enough_for_review, defer, source_gap, block, and noise.
- What changed: Task815 now includes a bounded Task773 attention packet corpus.
- Next action: Use the corpus to prevent source_gap collapse and input over-collection.

## Quant Expert Report

This corpus tests whether the brain can say enough, wait, gap, block, or ignore noise. It is not a data collection expansion. The corpus preserves missing source families as source_gap and fails if missing evidence is converted into a negative label.

Exact join keys are packet ids and evidence ids only. No outcome labels, PnL, ranks, scores, sizing, or buy/sell states are allowed.

## No-Background Decision-Maker Report

1. Done: 주의예산 샘플 corpus를 만들었다.
2. Why: 트레이더 머리처럼 중요한 것만 남기려면 입력 제한이 검증돼야 한다.
3. Not done: 더 많은 뉴스를 먹이는 작업이 아니다.
4. Next: Task816 provenance linker와 같이 쓴다.

## Artifact Manifest

- Inputs: Task809 attention packet validator.
- Outputs: `fixtures/attention_packets.csv`.
- Validation commands: `python scripts/trader_brain_attention_packet_validate.py --packet docs/reports/task_815_attention_packet_fixture_corpus/fixtures/attention_packets.csv`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
