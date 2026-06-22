# Task650 Relation State Machine Design

## Decision Summary

- Verdict: `RELATION_STATE_MACHINE_DESIGN_READY_IMPLEMENTATION_BLOCKED_TO_TASK651`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Task650 is a design task only.
- Task651 should implement a deterministic relation-state assignment engine.
- GPT/Chrome was used as external design review only, not as source truth or trading authority.

## Quant Expert Report

The next algorithm should not add more scores together. It should resolve relationships between information layers.

Current evidence:

| Observation | Interpretation |
|---|---|
| `conflicted_alignment` recent OOS cells averaged roughly -18% to -20% with 0% win rate and 100% entry-reduce failure | Potential blocker/avoid hypothesis, not yet rule-locked |
| `mixed_alignment_macro_supportive` had positive recent OOS evidence | Macro may act as a company-signal multiplier |
| `supportive_alignment_macro_confirmed` had positive but sparse evidence | Strong candidate type, but too thin for promotion |
| `macro_hostile` had only 6 observations | Do not overinterpret |
| FRED latest-vintage and exact release timestamp gaps remain | Strategy promotion forbidden |

### Required State Machine

```text
Source Integrity
-> Macro Context
-> Policy/Geopolitics Conflict
-> Sector/Theme Alignment
-> Company Catalyst Quality
-> Chart Confirmation
-> Relation Resolver
-> Action Mapper
```

### Relation Model

| Relation | Meaning | Action Direction |
|---|---|---|
| `reinforcing` | independent layers point in the same direction | normal/full/staged candidate |
| `offsetting` | company positive but context pushes against it | size down or confirmation |
| `prerequisite` | catalyst exists but a required confirmation is missing | delay or confirmation |
| `blocker` | risk or source problem invalidates entry | no action or block |
| `sizing_modifier` | context changes size more than direction | full/normal/reduced/staged |
| `source_gap` | critical input not usable as-of | research only |

### Important Design Rule

The future Task651 algorithm must use rule tables and gate outputs, not realized returns, labels, future prices, or future source revisions.

## No-Background Decision-Maker Report

- We should stop thinking in simple news scores.
- A good company news item is not enough.
- The system must ask:
  - Is the macro background helping?
  - Is policy or war risk blocking it?
  - Is the sector also moving?
  - Is the company catalyst real and direct?
  - Is price confirming?
- If these line up, it can become a strong candidate.
- If they fight each other, we delay, reduce, confirm, or block.
- This is still research only. No live trading approval.

## Artifact Manifest

- `task_650_decision.csv`
- `task_650_gate_spec.csv`
- `task_650_relation_taxonomy.csv`
- `task_650_action_taxonomy.csv`
- `task_650_validation_protocol.csv`
- `task_650_gpt_round1_packet.txt`
- `task_650_gpt_round1_response.md`
- `task_650_gpt_round2_packet.txt`
- `task_650_gpt_round2_response.md`
- `task_650_relation_state_machine_design.md`
- `artifact_manifest.csv`
