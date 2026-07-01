# TASK-4175 L1 Newswire Recall Mapping and Feature Gap Repair

## Goal

L1에서 반복되던 unmapped/recall pending/feature gap을 하나의 뭉뚱그린 blocker로 두지 않고, deterministic decision state로 분리한다. 강제 ticker mapping이나 LLM entity 추론은 하지 않는다.

## Results

| 항목 | 결과 |
|---|---:|
| input gap rows | 4,627 |
| pending before | 4,627 |
| pending after | 0 |
| reclassified rows | 4,627 |
| safety violation count | 0 |

| decision state | 건수 | 의미 |
|---|---:|---|
| NEEDS_ALIAS | 3,994 | alias/ticker/parser 보강 후보 |
| AMBIGUOUS_BLOCKER | 447 | 사람 또는 rule 보강 없이는 단정 불가 |
| FEATURE_BACKFILL_REQUIRED | 181 | mapping은 가능하나 feature materialization 보강 필요 |
| INSUFFICIENT_CONTEXT | 5 | 원천 context 부족으로 보류 |

후보 빈도표를 별도 artifact로 저장했다. 이는 다음 alias/ticker/parser 보강의 입력이며, 이번 task에서는 ambiguous row를 억지로 ticker로 확정하지 않았다.

## What This Does Not Claim

- 모든 row가 trading feature가 되었다고 주장하지 않는다.
- ambiguous row가 해결됐다고 주장하지 않는다.
- LLM entity inference, forced ticker mapping, broker mutation은 없다.

## Next

다음 L1 대상은 FEATURE_BACKFILL_REQUIRED 181건을 baseline으로 삼아 실제 feature builder/backfill을 보강하는 task다.
