# Task681 GPT Review

## Review Role

- External review-only professional trader and senior quant engineer.
- GPT output is not source truth, market data, label, or assignment input.

## Key Review Finding

The current code is not failing because the idea is wrong. It is failing because the five concepts are not modular engines. They are currently compressed into diagnostic labels and global ranks.

Current structure:

```text
state axis
-> diagnostic archetype label
-> top5 tier
-> global priority rank
-> simulator
```

Required structure:

```text
Leadership Lifecycle
-> Catalyst Quality
-> Archetype Candidate
-> Same Symbol Context
-> Cohort Slot Qualification
-> Simulation
```

## Most Important Critique

- `classify_winner_archetype` was built for Task678 diagnostic reporting and should not drive assignment directly.
- `classify_top5_tier` decides elite/contender/normal/reject too early.
- `top5_priority_rank` is a global rank, but the actual decision is a same-timestamp cohort problem.
- The five engines need strict data contracts.

## Implementation Direction

- Rename and redesign `classify_winner_archetype` as `classify_archetype_candidate`.
- Retire `classify_top5_tier`.
- Build separate artifacts for leadership, catalyst, archetype, same-symbol context, and slot qualification.
- Build slot assignment around entry-time cohorts, not global row ranking.
- Use active cap3 priority only as a final tiebreaker, not as the main order.

## Guardrails

- No result-defined features.
- No future returns in assignment.
- No symbol or theme blacklist.
- No MDD-only cap.
- No average-return-only ranking.
- No microstructure until raw source readiness is complete.
