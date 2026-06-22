# Task680 Professional Trader Panel Diagnosis

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: five professional trader perspectives reviewed the current Task639/active cap3/Task678/Task679 evidence.
- Key conclusion: the project should stop adding filters and caps. The next work is to rebuild the prediction stack using entry-time information hierarchy.
- Next action: build Winner Archetype Engine, Same Symbol Divergence Matrix, Leadership Lifecycle Panel, Catalyst Quality Matrix, and Slot Qualification Study.

## Quant Expert Report

### Data source and source readiness

- Inputs reviewed: Task639, active relation cap3, Task678, Task679.
- GPT/Chrome was used as an external review-only discussion partner.
- GPT output is not used as source truth, market data, label, or assignment input.
- Historical quote/trade/microstructure data remains excluded because collection is still pending.

### Exact join keys

- No new data join was performed in this diagnostic task.
- Reviewed prior artifacts that use `lifecycle_id`, `entry_ts`, existing exit timestamps, and existing state panels.

### Leakage audit

- No new trading rule was built.
- No future returns, labels, or future prices were used for assignment.
- Historical outcomes were reviewed only to diagnose current model weakness and define next research tasks.

### Split/OOS metrics reviewed

- Task639: $1,000 -> $7,639.62, MDD -23.76%.
- Active relation cap3: $1,000 -> $10,887.47, MDD -30.52%.
- Active cap3 max10: $1,000 -> $3,397.55, MDD -23.14%.
- Task679 top5 priority v1: $1,000 -> $6,499.90, MDD -31.05%.
- Task679 elite-only probe: $1,000 -> $6,824.94, MDD -19.93%.

### Five-trader panel diagnosis

#### 1. Systematic Quant Trader

- Weakness: the system confuses good average trades with rare large winners.
- Task679 showed `elite_top5_candidate` had better average return, but many large winners still lived in normal and contender buckets.
- Required change: separate expected-return ranking from tail-opportunity ranking.

#### 2. Discretionary Growth/Momentum PM

- Weakness: chart states are named too defensively.
- `fragile` may sometimes mean early acceleration, not bad setup.
- Required change: replace confirmed/fragile labels with market-behavior modes such as early acceleration, accepted trend, late extension, and failed acceptance.

#### 3. Event-Driven Equity Analyst

- Weakness: catalyst taxonomy is too shallow.
- Current labels such as hard company, medium signal, and high quality do not explain economic impact enough.
- Required change: rebuild catalyst quality around contract quality, customer quality, backlog durability, guidance impact, and supply-demand shock.

#### 4. Macro/Sector Rotation Trader

- Weakness: sector/theme states are too broad.
- Theme participation is not enough. The engine must distinguish new leader emergence, existing leader persistence, late leader exhaustion, and fading leadership.
- Required change: build a leadership lifecycle panel.

#### 5. Portfolio Risk Manager

- Weakness: drawdown is treated as a trade-quality problem, but much of it is slot construction and cohort selection.
- Required change: analyze timestamp cohorts. The unit is not one trade alone, but which candidates competed for the same five slots.

### Failure decomposition

- Task678 showed max10 diluted alpha. More trades did not help.
- Task679 showed simple top5 qualification removed active cap3 big winners.
- The current issue is not missing information. The issue is weak hierarchy between macro, theme leadership, catalyst quality, price acceptance, and slot qualification.

### Cost/slippage stress

- No new backtest was performed in Task680.
- Prior reviewed tests preserved existing cost assumptions.
- Any future implementation must keep cost/slippage stress and split/OOS gates.

### Remaining blockers

- Winner archetypes are still descriptive, not predictive.
- Catalyst semantics are not sufficiently economic.
- Leadership lifecycle is not yet encoded.
- Slot competition is not yet framed as a cohort decision.
- Strategy remains NOT_ACCEPTED and real capital remains FORBIDDEN.

## No-Background Decision-Maker Report

- What happened: five trader perspectives reviewed why the project keeps losing progress after active cap3.
- Why it matters: we have many data fields, but they are not combined in the right order.
- Main point: do not chase the past winners. Use entry-time information to improve rational prediction.
- Capital readiness: unchanged. NOT_ACCEPTED and FORBIDDEN.
- Plain-language next step: rebuild the stack from “state labels” into “prediction logic.”

## Artifact Manifest

- Inputs: Task639, active relation cap3, Task678, Task679 summary metrics.
- Outputs: this report, decision CSV, GPT review notes, artifact manifest.
- Row counts: decision CSV 1 row.
- Validation command: `python scripts\task_registry_validate.py`.

## Prioritized Next Tasks

1. Winner Archetype Engine
   - Goal: classify entry-time setup structures without using future returns.
   - Output: entry-time archetype candidate and confidence.

2. Same Symbol Divergence Matrix
   - Goal: explain why the same symbol can produce both winner and loser setups.
   - Output: symbol-level setup difference matrix.

3. Leadership Lifecycle Panel
   - Goal: separate emerging, persistent, late, and fading leadership.
   - Output: theme leadership lifecycle state at entry.

4. Catalyst Quality Matrix
   - Goal: replace vague catalyst labels with economic mechanism.
   - Output: contract/customer/backlog/guidance/supply-demand quality fields.

5. Slot Qualification Study
   - Goal: decide which candidates deserve scarce top-five portfolio slots.
   - Output: timestamp cohort comparison and slot decision audit.

## Required Guardrails

- No result-defined features.
- No symbol/theme blacklist.
- No MDD-only cap.
- No average-return-only ranking.
- No deployment claim before split/OOS, leakage, cost/slippage, and artifact audit.
