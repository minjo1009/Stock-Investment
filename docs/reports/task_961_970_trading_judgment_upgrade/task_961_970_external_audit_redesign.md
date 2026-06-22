# Task961-970 External Audit Redesign

## Decision Summary

- Verdict: the prior Task961-970 hard-suppression design is rejected.
- Root cause: Codex converted diagnostic weakness flags into exclusion rules without proving that the flags separate bad trades from good trades.
- External audit stance: GPT/subagents are external auditors only. They may criticize design and missing evidence. They may not be source of truth, acceptance authority, or trade decision authority.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Failure Diagnosis

The prior design did this:

```text
source gap / stale / duplicate / thin packet
-> assume bad
-> hard suppress
-> replay
```

That was the wrong mental model.

Actual diagnostic decomposition showed:

| Flag | Slot10 Trades | Winners | Losers | Total PnL |
| --- | ---: | ---: | ---: | ---: |
| source_gap_heavy | 450 | 244 | 206 | 1939.23 |
| duplicate_thesis | 435 | 232 | 203 | 1748.74 |
| low_independent_evidence | 433 | 234 | 199 | 1587.83 |
| thin_packet | 433 | 234 | 199 | 1587.83 |
| stale_source | 242 | 132 | 110 | 825.60 |

This means the flags were not bad-trade labels. They were mostly broad coverage/structure labels. Hard suppression cut alpha.

## External Auditor Consensus

### Institutional Trader Audit

1. Task961-970 failed because panels were translated directly into hard suppression.
2. Good traders do not automatically discard weak-looking facts.
3. They classify: enter, wait, reduce priority, substitute, monitor, or reject.
4. Duplicate thesis can mean conviction, not only crowding.
5. Freshness is a timing lens, not a veto.

### Theme/Macro/Policy Audit

1. Source gap can mean data limitation, not a false thesis.
2. Stale source can mean long-duration structural thesis, not expired information.
3. Political, macro, policy, defense budget, export control, rates, and energy constraints often change timing, not direction.
4. AI semiconductors and space/defense themes can repeat because the structural thesis persists.

### Quant/Backend Audit

1. Diagnostic flags must default to `diagnostic_only`.
2. Hard blocks are allowed only for future evidence, missing required lineage, and source-backed invalidation.
3. Duplicate calculations must be explicitly as-of sorted; CSV order dependency is not acceptable.
4. Validators must block flag-to-veto misuse, not merely check cash/equity/status.
5. Candidate attrition must be audited before any replay.

## Redesigned Task961-970

### Task961: Baseline Winner/Loser Meaning Audit

Purpose:

```text
Do not filter.
First learn what made winners and losers different.
```

Outputs:

- `task961_baseline_winner_loser_semantic_audit.csv`
- PnL is allowed only for evaluation/decomposition, never future selection.
- Required fields: `trade_spec_id`, `symbol`, `theme`, `winner_loser_bucket`, `weakness_flags`, `economic_meaning_class`, `evaluation_only_pnl`.

Audit question:

```text
Is this flag actually predictive, or just broadly attached to almost every candidate?
```

### Task962: Weakness Flag Semantic Reclassification

Purpose:

```text
Convert weakness flags into meanings, not punishments.
```

Allowed semantic classes:

- `bad`
- `data_limitation`
- `structural_thesis`
- `conviction_repeat`
- `timing_issue`
- `unknown`

Output:

- `task962_weakness_semantic_reclassification.csv`

Hard rule:

```text
source_gap / stale / duplicate / thin / low_evidence cannot be hard reject by themselves.
```

### Task963: Duplicate Thesis Meaning Classifier

Purpose:

```text
Repeated thesis can be conviction or crowding.
Classify before using.
```

Allowed duplicate meanings:

- `conviction_repeat`
- `crowding_risk`
- `redundant_same_trade`
- `stale_echo`
- `unknown`

Output:

- `task963_asof_duplicate_thesis_meaning_ledger.csv`

Validation:

- Must sort by `decision_asof_ts`, `entry_date`, `trade_spec_id`.
- Must prove prior-only cluster counts.

### Task964: Source Gap Limitation Ledger

Purpose:

```text
Source gap is not a negative label.
It is a missing-evidence contract.
```

Fields:

- `source_gap_reason`
- `source_gap_materiality`
- `required_missing_artifact`
- `blocks_confidence`
- `blocks_trade`

Output:

- `task964_source_gap_limitation_ledger.csv`

Hard rule:

```text
Missing raw source is reported.
It is not approximated.
It is not automatically treated as a loser.
```

### Task965: Stale Thesis Duration Audit

Purpose:

```text
Separate expired catalyst from durable structural thesis.
```

Allowed duration classes:

- `expired_catalyst`
- `aging_catalyst_needs_refresh`
- `long_duration_structural_thesis`
- `evergreen_quality`
- `unknown`

Output:

- `task965_stale_thesis_duration_audit.csv`

Audit question:

```text
Is stale actually stale, or is the thesis long-cycle?
```

### Task966: Theme/Macro/Policy Timing Interpreter

Purpose:

```text
Macro/politics/theme expert layer changes timing interpretation.
It does not directly buy/sell.
```

Expert lenses:

- politics/policy
- economy/rates
- semiconductor
- AI infrastructure
- space/defense
- software
- energy/power
- healthcare
- consumer
- financials

Output:

- `task966_theme_macro_policy_timing_interpreter.csv`

Fields:

- `policy_macro_condition`
- `timing_effect`
- `direction_effect`
- `expert_lens_owner`
- `source_required_for_confidence`

### Task967: Trader Action Taxonomy

Purpose:

```text
Replace hard reject with trader actions.
```

Allowed actions:

- `enter`
- `wait`
- `reduce_priority`
- `substitute`
- `monitor`
- `hard_block`

Hard block allowed only for:

- `future_evidence`
- `missing_required_lineage`
- `source_backed_invalidation`

Output:

- `task967_trader_action_taxonomy.csv`

### Task968: Cohort Attrition And Audit Ledger

Purpose:

```text
Before replay, show how many candidates are lost and why.
```

Output:

- `task968_cohort_attrition_ledger.csv`
- `task968_reason_marginal_attribution.csv`

Required checks:

- candidate count before ranking
- hard blocked count
- ranked count
- selected shadow count
- one primary reason per blocked row

### Task969: Shadow Ranking, Not Replay First

Purpose:

```text
Build shadow ranking beside Task941 baseline.
Do not change trades yet.
```

Output:

- `task969_shadow_trader_ranking.csv`
- `task969_shadow_vs_baseline_comparison.csv`

Rules:

- No future return.
- No realized PnL.
- No post-entry price change.
- No outcome rank.
- No broad veto.

### Task970: External Audit Governance Closeout

Purpose:

```text
Close the redesigned program before any new replay.
```

Output:

- `task970_external_audit_closeout.csv`

Must state:

- GPT/subagents were review-only.
- No acceptance.
- No deployment readiness.
- No real capital.
- Whether replay is allowed next.
- Which policy, if any, is pre-registered for later controlled replay.

## Implementation Guardrails

1. Do not implement another hard suppression replay first.
2. Do not convert diagnostic flags into hard blocks.
3. Do not use winner/loser/PnL labels inside assignment or selection logic.
4. Do not infer missing labels as negatives.
5. Do not use symbol/date/price/time proximity fallback.
6. Do not overload L5 adapter input with all interpretation fields.
7. Keep interpretation artifacts separate from trade-spec inputs.
8. Any replay must be a later, pre-registered controlled policy.

## Required Validator Upgrades

The redesigned validator must fail if:

1. `source_gap_heavy`, `stale_source`, `duplicate_thesis`, `thin_packet`, or `low_independent_evidence` appears as a standalone hard-block reason.
2. Duplicate counts are not prior-only and as-of sorted.
3. Candidate attrition is not reported before replay.
4. PnL, realized return, post-entry price change, or outcome rank enters selection fields.
5. GPT/subagent text is treated as source truth.
6. Status fields differ from:
   - `NOT_ACCEPTED`
   - `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
   - `FORBIDDEN`

## Next Action

Implement redesigned Task961-970 in this order:

```text
961 winner/loser semantic audit
962 weakness semantic reclassification
963 duplicate meaning classifier
964 source gap limitation ledger
965 stale thesis duration audit
966 theme/macro/policy timing interpreter
967 trader action taxonomy
968 cohort attrition ledger
969 shadow ranking only
970 external audit closeout
```

Do not run a new controlled replay until Task970 explicitly allows one as the next task.

## Implementation Closeout

The redesigned pass has been implemented as review-only artifacts under:

`data/artifacts/task_961_970_external_audit_redesign/`

Implemented result:

- Input trade specs reviewed: 3689.
- Task941 slot10 baseline trades evaluated: 450.
- Shadow slot10 selections: 630.
- Task941/shadow overlap: 313.
- Replay executed: 0.
- Next replay allowed: 0.
- Trader action labels: `enter` 1456, `monitor` 2229, `wait` 4.

The implementation did not run a controlled replay. The output is a semantic interpretation and shadow ranking layer only.

Current required next action:

```text
Review shadow ranking.
Pre-register exactly one controlled policy.
Only then consider a later replay task.
```

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
