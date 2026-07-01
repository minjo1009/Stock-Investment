# TASK-4182 L1 Article Entity Feature Hardening

## Result

TASK-4182 separated the L1 hardening proof from the upstream L0 worker-liveness proof.

| Check | Before | After | Result |
|---|---:|---:|---|
| L1 article packets | 1093 | 6036 | expanded |
| L1 ready article packets | 1093 | 6036 | expanded |
| Article source families | 1 | 3 | broadened |
| Diagnostic feature rows | 1842 | 4959 | expanded |
| Feature materialization gap rows | 181 | 0 | closed in diagnostic ledger |
| Recall review queue rows | 0 | 447 | explicit review queue |

## Still Not Hidden

| Item | Status |
|---|---|
| Upstream L0 worker liveness blockers | 1 |
| Blocked lanes | public_newswire_backfill |
| Forced ticker mapping | 0 |
| LLM entity inference | 0 |
| Trading/action authority rows | 0 |

This task does not claim L0 backfill completion. It only proves the L1 article/entity/feature path was broadened and that remaining ambiguous source recall rows are explicit review work, not silent leakage to later layers.
