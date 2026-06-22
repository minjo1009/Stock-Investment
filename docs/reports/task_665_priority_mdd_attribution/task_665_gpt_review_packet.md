# Task665 GPT Review Packet

Role requested: professional quant PM / risk manager.

Review-only constraints:

- Use only supplied facts.
- Do not invent data.
- Do not propose entry/exit changes.
- Do not use returns or labels in assignment.

Project facts supplied:

- Task639 baseline with existing timing/exit and 50bp cost: `$1,000 -> $7,639.62`, MDD `-23.76%`.
- Task664 relation priority changes only same-entry-timestamp ordering for max5 capacity.
- No entry timing change, no exit change, no fixed-hold rule.
- Task664 `predeclared_relation_ladder`: `$1,000 -> $8,797.73`.
- Validation improves from `$1,069.23` to `$1,304.40`.
- Recent OOS improves from `$1,531.90` to `$1,539.82`.
- Entry-reduce improves from `37.0%` to `29.6%`.
- Full-period MDD worsens from `-23.76%` to `-33.63%`.
- Accepted set changed by `27 added / 27 removed`.

Proposed Task665:

1. Do not analyze all 27 changed trades equally.
2. Identify priority candidate MDD peak/trough interval first.
3. Within that interval, identify added trades, removed trades, and same-entry displacement pairs.
4. Separate trades that improved return from trades that worsened drawdown.
5. Only then design non-return-tuned risk caps.
