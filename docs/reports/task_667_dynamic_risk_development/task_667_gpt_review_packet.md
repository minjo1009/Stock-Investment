# Task667 GPT Review Packet

- captured_via: Chrome ChatGPT
- tab: 1. 코딩/투자
- source_type: external_model_interpretation
- use_rule: GPT output is review input only. Local backtest gates decide acceptance.

## Supplied Facts

- Task639 baseline: $1,000 -> $7,639.62, MDD -23.76%.
- Task664 relation priority: $1,000 -> $8,797.73, MDD -33.63%.
- Task666 active relation cap3: $1,000 -> $10,887.47, MDD -30.52%.
- Task666 active theme cap2: $1,000 -> $4,496.08, MDD -28.63%.
- Diagnostic bad-theme block: $1,000 -> $11,233.49, MDD -31.70%, not promotion eligible.

## Requested Review

Review firm-grade but implementable Task667 designs for:

- dynamic relation cap
- scarce-slot admission hurdle
- risk-proxy sizing
- active relation cap3 MDD audit

Constraints:

- no future returns or labels in assignment
- no symbol blacklist
- no return-tuned theme blacklist
- preserve Task639 entry timing and exits
- promotion only if return, drawdown, validation, and recent OOS gates all pass

