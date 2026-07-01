# Backtest Replay Contract

Before any backtest/replay work, read:

- [Backtest Harness Operating Discipline](../operating_system/backtest_harness_operating_discipline.md)
- [Project Operating State](../operating_system/project_operating_state.md)
- latest relevant task report

## Replay Must Declare

- experiment ID
- selector policy
- sizing policy
- exit policy
- capital path
- cost/slippage model
- source feature set
- frozen inputs
- what changed from the previous run

If nothing changed, do not rerun the same experiment.

## Forbidden

- inferred lifecycle matching
- symbol/date/price/time proximity fallback
- missing label to negative conversion
- future price/source/outcome in assignment logic
- GPT/Chrome as source of truth
- deployment or acceptance claims from replay

## Current Memory

- Task2381 repaired +8000 exit-chain parity and produced the current best diagnostic candidate.
- Task2401-2500 built research-to-paper readiness but conclusion remained `NO_GO`.
- Task2501 applied Korea Investment Securities cost basis and MDD worsened.
- Task2581-2600 joined SEC and liquidity/rates into selector-only diagnostics. No replay was run.

