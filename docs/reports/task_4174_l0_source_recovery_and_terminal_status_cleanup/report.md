# TASK-4174 L0 Source Recovery and Terminal Status Cleanup

## Goal

GPT 검수 결론에 따라 L0 incomplete/retryable source 상태를 완료, 진행 중, 또는 명시적 blocker 상태로 정리한다. Federal Register 2020-10 offset 32는 bounded retry proof를 남기고, BW/PRN은 미완료 상태를 완료로 오판하지 않는다.

## Results

| 항목 | 결과 |
|---|---:|
| L0 source ledger rows | 25 |
| unclassified terminal status | 0 |
| terminalized/reclassified source states | 16 |
| safety violation count | 0 |

| 상태 | 건수 | 의미 |
|---|---:|---|
| COMPLETED | 9 | 이미 완료로 확인된 source 상태 |
| BOUNDED_RETRY_PROOF_CAPTURED | 1 | Federal Register 2020-10 offset 32 proof 저장 |
| FAILED_RETRYABLE_TERMINAL_BLOCKER | 7 | bounded retry 후 terminal blocker로 명시 |
| RUNNING_OR_EXPORTED_INCOMPLETE | 6 | runner가 계속 처리해야 하는 미완료 상태 |
| RUNNING_RETRYABLE_INCOMPLETE | 2 | retry 가능한 실행 중 미완료 상태 |

Federal Register 2020-10 page 32는 API 재요청 결과 HTTP 200, total_pages 25, page 32 result_count 0이었다. 즉 32번째 page는 실제 데이터 누락이 아니라 유효한 범위 밖 빈 page로 proof가 저장됐다.

## What This Does Not Claim

- BusinessWire/PRNewswire backfill 완료를 주장하지 않는다.
- 미수집 데이터나 stale 데이터를 negative evidence로 쓰지 않는다.
- L4 thesis, trading signal, ranking, sizing, order는 생성하지 않는다.

## Next

다음 L0 대상은 현재 BW/PRN pending unit 수를 baseline으로 삼아 incomplete_backfill_units를 실제로 줄이는 별도 outcome task다.
