# TASK-4171 GPT Review Prompt

You are a professional software delivery architect, backend/data platform engineer, SRE-style operations reviewer, product engineering lead, and institutional trading-data infrastructure reviewer.

Important instruction:
- Do NOT read GitHub for this review.
- The local repository state is newer than GitHub.
- Use only the current local facts pasted below.
- This review is NOT only about L0-L4.
- The user corrected Codex: the desired direction is for the entire prime harness, not only the L0-L4 blocker burn-down harness.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence.

User correction:
The previous GPT review focused too narrowly on L0-L4 blocker burn-down.
The user means:

The whole prime harness should be designed so Codex work is outcome-contract driven.

Not just:
- L0 incomplete
- failed/retryable
- unmapped
- unsupported relation

But every task class:
- backend/data pipeline
- scheduler/ops
- bug fixes
- refactors
- UI/frontend
- docs/governance
- research/analysis
- GPT review loops
- trading-system safety

should avoid "diagnosis/report/validator pass" as fake progress.

Desired global principle:
Every task should define an outcome unit and prove actual movement:
- blocker count burn-down
- failing test before/after
- pending/failed/stale job reduction
- unmapped row reduction
- unsupported relation reduction
- UI defect/screenshot/vision QA improvement
- stale doc/registry violation reduction
- research claim/source gap reduction
- performance/runtime/retry-rate improvement
- harness invalid-closeout prevention test

Task types should include at least:
- OUTCOME_CHANGE
- TERMINALIZE
- RECLASSIFY
- DIAGNOSTIC_ONLY
- HARNESS_BOOTSTRAP
- EXPLORATORY_RESEARCH
- DESIGN_ONLY
- REVIEW_ONLY

Question:
How should the prime harness evolve so all Codex work is governed by a universal outcome contract, while still allowing valid diagnostic/research/design/harness tasks without pretending they solved the underlying problem?

Please review and design:

1. The correct abstraction
- Is "blocker" too narrow?
- Should the universal unit be outcome_unit, evidence_unit, or task_result_contract?
- What fields should every task carry regardless of domain?

2. Universal task taxonomy
Design task types across:
- code bug fix
- backend/data pipeline
- scheduler/ops
- UI/frontend
- docs/governance
- quant/research
- GPT review
- harness/bootstrap

For each task type, define:
- valid progress claim
- invalid progress claim
- required evidence
- validator or QA gate

3. Prime task template
Design a mandatory template with:
- task_id
- task_type
- domain
- outcome_unit
- baseline
- intended_change
- measurement_method
- allowed_actions
- forbidden_actions
- evidence_artifacts
- validators
- closeout_verdict
- report_format
- next_target

4. Prime report format
Design a concise Korean report format that forces:
- What changed?
- How much changed?
- What evidence proves it?
- What did not change?
- Is this actual progress or diagnostic/design/bootstrap only?
- What is the next concrete target?

5. Prime validators / guards
What validators should exist globally so Codex cannot close tasks by writing reports only?
Examples:
- outcome_contract_validator
- evidence_delta_validator
- report_progress_guard
- diagnostic_only_guard
- upstream_dependency_gate
- safety_authority_guard
- stale_baseline_guard
- scope_guard

6. GPT review rubric
How should GPT review future Codex work so GPT itself does not reward long explanations over measurable movement?

7. Immediate implementation
Recommend the next bounded Codex task to implement this prime harness in the repo.
Should TASK-4172 be "Prime Outcome Harness Bootstrap"?
What exact files/artifacts/tests should it create?

Important:
- Do not recommend a giant platform rewrite.
- Do not recommend a dashboard first.
- Do not require all task classes to have numeric deltas. Some tasks are valid as DIAGNOSTIC_ONLY, DESIGN_ONLY, REVIEW_ONLY, HARNESS_BOOTSTRAP, but they must not claim problem progress.
- The harness should make that distinction explicit.
- Output in Korean, direct and easy to understand.
