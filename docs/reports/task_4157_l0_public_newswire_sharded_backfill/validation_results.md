# TASK-4157 Validation Results

## 통과

```text
python scripts/run_l0_public_newswire_sharded_backfill.py --start-month 2016-01 --end-month 2026-06 --sources businesswire,globenewswire,prnewswire --mode smoke --concurrency 2 --dry-run

dry_run: true
legacy_completed_units: 1771
pending_units: 2330
scheduled_shards: 320
total_units: 4101
```

```text
python scripts/aggregate_l0_public_newswire_shards.py --shard-artifact-root data/artifacts/l0_public_newswire_backfill_shards --shard-raw-root data/raw/l0_public_newswire_backfill_shards --legacy-artifact-root data/artifacts/l0_public_newswire_backfill --inventory-path data/artifacts/l0_public_newswire_backfill_shards/shard_inventory.json --out data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json --skip-raw-dedupe

progress_pct: 43.1846
status: RUNNING
```

```text
python scripts/validate_l0_public_newswire_sharded_backfill.py --shard-artifact-root data/artifacts/l0_public_newswire_backfill_shards --shard-raw-root data/raw/l0_public_newswire_backfill_shards --inventory-path data/artifacts/l0_public_newswire_backfill_shards/shard_inventory.json --aggregate-progress data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json

PASS shards_checked: 379
PASS unique_paths_seen: 1516
PASS safety_flags_closed
WARN l1_unclassified_or_pending_count > 0
RESULT: PASS
```

```text
python -m unittest tests.test_l0_public_newswire_sharded_backfill

Ran 4 tests in 0.071s
OK
```

```text
syntax compile via in-memory compile()

SYNTAX_OK 6
```

## 참고 경고

`python -m py_compile ...`는 실행 중인 background worker와 `__pycache__` 파일 교체가 충돌해 Windows `Access denied`가 발생했다. 동일 파일들은 테스트 import와 in-memory compile로 문법 검증했다.

validator 경고 `l1_unclassified_or_pending_count > 0`은 L0 수집 자체 실패가 아니다. L1 mapping/분류에서 계속 줄여야 하는 후속 품질 이슈다.

