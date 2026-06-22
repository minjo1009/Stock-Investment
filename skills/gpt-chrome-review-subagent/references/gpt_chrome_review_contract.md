# GPT/Chrome Review Contract

## Role

GPT/Chrome is a bounded review and ideation layer. It can find overclaims, missing evidence, unclear UI, weak report wording, and reviewer questions. It cannot certify facts.

## Source Of Truth

Use only repo-native evidence for decisions:

- `docs/ownership/current_operating_model.md`
- `tasks/task_registry.csv`
- `docs/ownership/readiness_registry.yaml`
- raw/runtime market source files
- broker/order/fill/lifecycle/replay artifacts
- exact IDs: `decision_id`, `order_id`, `fill_id`, `position_id`, `lifecycle_id`, `source_snapshot_id`
- validation command output
- Chrome screenshots only for human UI visibility, not metrics

## Browser Reliability Rule

Use the existing `1. 코딩/투자` ChatGPT tab first when it is responsive. If it times out, freezes, or cannot return a response, open a fresh ChatGPT tab in the same logged-in Chrome profile and retry the same bounded packet once. This is a reliability fallback, not permission to loosen source or secrecy rules.

Record one of these statuses in the task artifact:

- `EXISTING_TAB_CAPTURED`
- `FRESH_TAB_CAPTURED_AFTER_TIMEOUT`
- `ATTEMPTED_BUT_CHROME_TIMEOUT`

When the status is `ATTEMPTED_BUT_CHROME_TIMEOUT`, do not write as if GPT reviewed the task. Continue from repo-native evidence only.

## Priority

| Priority | Allowed Use | Output |
|---|---|---|
| P0 | Acceptance overclaim review, broker/replay blocker review, frontend five-second blocker visibility, blocker-first Slack/EOD review | review_notes |
| P1 | Backtest/replay failure taxonomy, report standard review, chart packet QA, UX flow review | review_notes or ideation_notes |
| P2 | Strategy hypothesis brainstorming after blocker discipline is preserved, UI polish, document wording | ideation_notes |

## Required Review Questions

Ask GPT/Chrome reviewers to answer only these classes of questions:

- What claim sounds stronger than the evidence?
- Which raw source, exact ID, validation command, or manifest is missing?
- Could a reader mistake diagnostic evidence for strategy acceptance?
- Could proxy PnL, runtime synthetic SELL, Slack success, UI polish, or screenshot success be confused with broker truth?
- Does the UI show status, first blocker, owner, freshness, and next validation before positive metrics?
- What next repo-native validation would prove or disprove the finding?

## Investment Brain Circuit Review Rule

When the user asks to develop the investment brain, source-family interpreters, relation engines, or firm-grade trader logic, GPT/Chrome review must be split into two passes:

1. `overall_brain_strategy_review`: review the full five-layer brain direction, source/evidence boundaries, relation-edge design, and acceptance blockers.
2. `circuit_detail_review`: review each affected circuit separately before implementation, including primitive fields, interpretation states, layer links, cross-circuit edges, alive/review states, and guardrails.

Do not use one broad GPT answer as permission to implement all details. For source-family work, each relevant source family must be routed to a dedicated brain circuit. Sources are not discarded merely because they cannot create operating catalyst facts. Instead, only unsafe extractor permissions are denied.

Required distinction:

- `source_preserved`: the raw or linked source remains available as context.
- `extractor_denied`: the source cannot create a specific fact family, such as revenue, order, backlog, guidance, or margin.
- `context_alive`: the source can still modify confidence, risk, slot, crowding, special-situation routing, or macro/theme context through typed edges.

## Forbidden Findings

Reject any GPT output that:

- declares a strategy good, accepted, profitable, or deployment-ready
- calculates or validates metrics without repo artifacts
- infers lifecycle identity by nearby symbol/date/price/time
- fills missing raw sources or labels with reasoning
- proposes fake chart markers or guessed entry/exit lines
- changes task registry, readiness registry, or blocker status by conversation alone
- treats passing tests as strategy acceptance, deployment readiness, broker truth completion, or real-capital permission

## Test Authority Boundary

When GPT/Chrome reviews tests, CI, validation, or closeout language, use:

- `docs/architecture/test_validation_canonicalization_map.md`

Validation wording must preserve:

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```

GPT findings should include:

- validation authority lane
- what PASS means
- what PASS does not mean

## Closeout

Any useful GPT/Chrome finding must be converted to:

1. owner team
2. reviewer team
3. artifact path
4. validation command
5. validation authority
6. status: `review_notes`, `ideation_notes`, `accepted_to_backlog`, or `rejected`
