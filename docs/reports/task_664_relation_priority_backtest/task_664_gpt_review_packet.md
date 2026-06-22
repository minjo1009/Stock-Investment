# Task664 GPT Review Packet

Role requested: professional quant PM/trader and macro strategist.

Review-only constraints:

- Use only supplied project facts.
- Do not invent data.
- Do not change entry timing or exit.
- Do not add fixed-hold exits.
- Do not use returns or labels in assignment.
- Relation priority may only reorder same-entry-timestamp candidates before max5 capacity simulation.

Project facts supplied:

- Task639 baseline uses existing timing and exit: `$1,000 -> $7,639.62`, MDD `-23.76%`.
- Task661 relation engine only labels relation states.
- Task663 selection/withholding test produced no promotion candidate.
- Recent OOS relation-state returns were separated: reinforcing `+18.5%`, offsetting `+10.9%`, needs-confirmation `+6.1%`, quality-price-confirmed `-4.9%`.

Questions:

1. Whether priority-within-existing-candidates is the right next step.
2. What predeclared priority ladder is defensible without return tuning.
3. Which variants must be diagnostic-only.
4. What Task664 pass/fail gates should be.
5. What artifacts should be produced.
