# Task816 Provenance Manifest Linker Contract

## Decision Summary

- Verdict: `PROVENANCE_MANIFEST_LINKER_CONTRACT_DESIGNED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: provenance linker implemented; 14 evidence rows mapped; explicit evidence ids checked against graph nodes and edges.
- What changed: Task816 now links relationship graph nodes and edges to a provenance manifest without inventing raw source truth.
- Next action: Add only explicit evidence ids; do not add fuzzy artifact matching.

## Quant Expert Report

The linker checks whether each node or edge evidence reference can be traced to a manifest row or declared source_gap. Missing raw sources are reported, not approximated. Expert opinion nodes remain review notes and cannot become source evidence without explicit source-family backing.

No inferred matching is allowed. Linkage should be by explicit ids, relative paths, source family, and asof timestamp only.

## No-Background Decision-Maker Report

1. Done: 출처 연결 validator와 manifest를 만들었다.
2. Why: 관계망은 edge만 많아지면 위험하고, 출처까지 연결돼야 쓸 수 있다.
3. Not done: 원천 데이터가 없는 것을 추정으로 채우지 않는다.
4. Next: Task817 failure report가 누락을 사람이 읽게 만든다.

## Artifact Manifest

- Inputs: Task792 relationship graph contracts and Task807 validator.
- Outputs: `provenance_manifest.csv`; `scripts/trader_brain_provenance_manifest_linker_validate.py`.
- Validation commands: `python scripts/trader_brain_provenance_manifest_linker_validate.py --graph-dir docs/reports/task_813_golden_graph_fixture_pack/fixtures/ai_capex_mechanism_graph --provenance-manifest docs/reports/task_816_provenance_manifest_linker_contract/provenance_manifest.csv`.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
