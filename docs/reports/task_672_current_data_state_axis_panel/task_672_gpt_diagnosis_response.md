# Task672 GPT Diagnosis Response

Captured via Chrome ChatGPT in the `1. 코딩/투자` tab.

Status: external model interpretation only. Not a source of market facts. Not a trading decision.

## Core Diagnosis

[interpretation] The project is blocked because it has decomposed states, but it has not yet explained when a state deserves a portfolio slot and when the same state becomes dangerous.

[interpretation] Task672 is a useful state decomposition step, but it is not a trading rule. The missing intermediate chain is:

```text
State Axis
-> Setup Quality
-> Slot Value
-> Portfolio Exposure Risk
-> Action Permission
```

## What The Project Is Failing To Do

[interpretation] First, the current engine cannot distinguish a good state from a good trade.

Example:

```text
price_fragile_or_unconfirmed
all-period active cap3 avg +148.59%
MDD interval avg -22.42%
```

This state is not always bad and not always good.

[interpretation] Second, state labels are being treated too much like action permissions. Good-sounding labels such as `relation_reinforcing`, `price_confirmed`, or `market_mixed` cannot directly justify priority, sizing, or entry.

[interpretation] Third, capacity is still being treated like an alpha problem. There are 1,621 candidates, only 51 accepted active-cap3 trades, and 1,534 candidates blocked by max positions. The central problem is not only finding good candidates. It is deciding which five candidates deserve capital at the same time.

[interpretation] Fourth, sparse cells are too large. Task672 produced 764 sparse cross-axis cells. A finely decomposed state combination cannot become an action rule unless it has enough repeated evidence.

## Why State Decomposition Is Not Yet A Trading Rule

[interpretation] State decomposition is an explanation table, not an action table.

The weak pattern is:

```text
state looks good
-> priority / cap / sizing
```

This fails because good states can still break in MDD windows.

Examples:

```text
multi_signal_medium_catalyst
all-period avg +53.11%
MDD interval avg -13.05%

company_positive_confirmation_needed
all-period avg +56.34%
MDD interval avg -9.92%

extension_proxy
all-period avg +56.24%
MDD interval avg -26.97%
```

[inference] The engine can find some setups with positive average expectancy, but it does not yet control simultaneous exposures that create portfolio drawdown.

## Required Intermediate Layers

### 1. Setup Quality Layer

[implementation] Convert the eight state axes into setup quality before any action mapping.

Inputs:

```text
company catalyst strength
relation/transmission support
price/chart acceptance
theme leadership
```

Outputs:

```text
high_quality_setup
medium_quality_setup
uncertain_setup
fragile_setup
```

### 2. Slot Value Layer

[implementation] Because this is a max5 strategy, every candidate must prove it deserves one of five slots.

Allowed entry-time inputs:

```text
mechanism_support_count
mechanism_pressure_count
catalyst_quality_score
price_acceptance_score
theme_rank_prev
portfolio_capacity_state
```

Outputs:

```text
slot_priority_high
slot_priority_normal
slot_priority_low
```

This must be an entry-time quality ranking, not a return-ranked rule.

### 3. Exposure Risk Layer

[implementation] Good candidates can still create MDD when they carry similar risks at the same time.

Inputs:

```text
same timestamp
theme concentration
relation concentration
macro/driver exposure concentration
price_extended / fragile flags
```

Outputs:

```text
exposure_clean
exposure_concentrated
exposure_fragile_cluster
```

### 4. Action Permission Layer

[implementation] Only after setup quality, slot value, and exposure risk are known should action permissions be assigned.

Examples:

```text
slot_priority_high + exposure_clean
-> eligible_priority

slot_priority_high + exposure_concentrated
-> cap_limited

fragile_setup + exposure_concentrated
-> diagnostic_only / reduced_admission

source_gap / sparse_cell
-> research_only
```

## Proposed Next Tasks

### Task673 - Setup Quality Layer

Purpose: convert the eight state axes into setup quality.

Artifacts:

```text
task673_setup_quality_panel.csv
```

Validation:

```text
return/label/future price used in assignment = 0
sparse cells are research_only
validation/recent OOS performance by setup bucket is reported
```

Failure:

```text
bucket names or thresholds changed after looking at average returns
```

### Task674 - Slot Value / Displacement Engine

Purpose: redefine priority only within the same entry timestamp.

Artifacts:

```text
task674_slot_priority_panel.csv
task674_displacement_audit.csv
```

Validation:

```text
entry timing, exit, and cost unchanged
only same-timestamp ordering changes
Task639 final improves
Task639 MDD does not worsen
validation/recent OOS stay above QQQ
```

Failure:

```text
global candidate filter
symbol/theme blacklist
```

### Task675 - Exposure Cluster Risk Audit

Purpose: explain why MDD happens even in good states by simultaneous exposure.

Artifacts:

```text
task675_exposure_cluster_report.csv
```

Fields:

```text
timestamp
active_theme_count
active_relation_count
active_driver_count
price_fragile_count
extension_proxy_count
mdd_window_flag
```

Validation:

```text
MDD interval loss is decomposed by simultaneous exposure structure
assignment still does not use realized returns
```

Failure:

```text
MDD-window-only rules are created from hindsight
```

### Task676 - Conservative Capacity Cap Test

Purpose: limit only simultaneous over-concentration.

Allowed caps:

```text
same timestamp theme concentration cap
same timestamp relation concentration cap
same timestamp fragile/extended cluster cap
```

Artifacts:

```text
task676_capacity_cap_backtest.csv
task676_added_removed_trade_audit.csv
```

Validation:

```text
final capital > Task639
MDD not worse than -23.76%
validation/recent improve
return_tuned_flag = 0
```

Failure:

```text
active cap3-like return remains but MDD is still worse than Task639
```

### Task677 - Action Permission Matrix

Purpose: document state -> setup -> exposure -> action permission.

Artifact:

```text
task677_action_permission_matrix.csv
```

Examples:

```text
high_quality_setup + exposure_clean -> priority_eligible
high_quality_setup + exposure_concentrated -> cap_limited
fragile_setup + exposure_concentrated -> research_only
sparse_cell -> no_promotion
```

Validation:

```text
all actions are based on entry-time features
return/label used in assignment = 0
```

Failure:

```text
good state name directly grants full entry or size boost
```

## Interpretation Of Good States Breaking In MDD

[interpretation] This does not mean the state is useless.

It means:

```text
Individual trade expectancy can be good,
but portfolio drawdown can still grow
when similar risks are held at the same time.
```

[inference] A good setup can lose because of wrong timing, simultaneous exposure, price extension, fragile price acceptance, or too many similar risks in the same capital window.

## Why Simple Rules Keep Breaking

[interpretation] Simple rules look at one axis at a time.

Examples:

```text
good state -> buy more
risky state -> buy less
theme cap -> reduce
dynamic cap -> reduce
```

[inference] The actual failures are multi-axis clusters:

```text
medium/strong catalyst
+ price extended or fragile
+ relation confidence
+ same timestamp/capacity concentration
+ same theme/driver exposure
```

That is why simple caps either cut winners with losers, or increase return while also increasing MDD.

## Final Status

[interpretation] Task672 is not a failure. It exposed the limit of state decomposition.

[inference] The next improvement is likely not another state name. It is the missing setup quality, slot value, and exposure risk layer.

[source_gap] Microstructure remains source pending and must not be used.

```text
Strategy = NOT_ACCEPTED
Real Capital = FORBIDDEN
```
