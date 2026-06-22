# Task2021-2030 SEC 8-K Exhibit 99.1 IR/CEO Extractor

## Decision Summary

- Verdict: `sec_8k_ex99_ir_ceo_extractor_complete_diagnostic_only`.
- Aggressive scope rows: 116.
- Exhibit/reference candidate docs: 396.
- Strict EX-99.1 docs: 175.
- Loose EX-99.1 docs: 2.
- Reference-only docs: 219.
- IR/CEO L2 semantic rows: 102.
- IR/CEO family gate pass rows: 102.
- Rejection rows: 75.
- Paper shadow policy status: `BLOCKED_OTHER_SOURCE_FAMILIES_STILL_REQUIRED`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task attaches the first missing source family for the aggressive policy: issuer IR/CEO evidence from SEC 8-K Exhibit 99.1 documents.

Press-release-like 8-K body text and other EX-99 family documents are retained as reference-only diagnostics. They do not pass the IR/CEO family gate.

Rules:

- Only existing trade-spec, CIK, accession, and local raw filing paths are used.
- `available_to_brain_ts <= decision_asof_ts` is required.
- No symbol/date/price/time proximity fallback is used.
- Only strict or loose EX-99.1 documents can pass the IR/CEO family gate.
- Missing Exhibit 99.1 is a neutral source gap, not a negative signal.
- Speaker role is a deterministic proxy from text, not a certified transcript speaker label.
- This does not open paper shadow because earnings call, customer confirmation, and policy/news gates remain required.

## No-Background Decision-Maker Report

1. Company announcement / CEO-style evidence has now been attached from SEC EX-99.1 documents.
2. This improves source backing for the aggressive policy.
3. It still does not allow paper trading automation by itself.
4. Next source family should be official policy/news or customer-confirmation fixtures.

## Artifact Manifest

- `task2021_aggressive_ir_ceo_scope.csv`
- `task2022_sec_8k_ex99_candidate_docs.csv`
- `task2023_ir_ceo_statement_snippets.csv`
- `task2024_l2_ir_ceo_semantics.csv`
- `task2025_l3_ir_ceo_edges.csv`
- `task2026_ir_ceo_gate_delta.csv`
- `task2027_negative_fixture_rejections.csv`
- `task2028_subagent_audit.csv`
- `task2030_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
