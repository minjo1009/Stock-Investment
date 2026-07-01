# TASK-4158 Validation Results

## 통과

```text
python -m unittest tests.test_l0_public_newswire_sharded_backfill

Ran 5 tests
OK
```

```text
python scripts/run_l0_public_newswire_sharded_backfill.py --start-month 2016-01 --end-month 2026-06 --sources businesswire,globenewswire,prnewswire --mode smoke --concurrency 4 --source-lanes businesswire=2,globenewswire=1,prnewswire=1 --dry-run

schedule_strategy: source_round_robin
source_lanes:
  businesswire: 2
  globenewswire: 1
  prnewswire: 1
total_units: 4101
pending_units: 2240
```

```text
python scripts/aggregate_l0_public_newswire_shards.py --shard-artifact-root data/artifacts/l0_public_newswire_backfill_shards --shard-raw-root data/raw/l0_public_newswire_backfill_shards --legacy-artifact-root data/artifacts/l0_public_newswire_backfill --inventory-path data/artifacts/l0_public_newswire_backfill_shards/shard_inventory.json --out data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json --skip-raw-dedupe

progress_pct: 45.4036
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

## 실제 운영 확인

재시작 후 RUNNING worker 분포:

- BusinessWire 2
- GlobeNewswire 1
- PRNewswire 1

구 런처 PID `34700`과 BusinessWire 독점 worker들은 중지했고, 새 런처 PID `33036`을 띄웠다. 구 TASK-4157 모니터 PID `22868`은 중지했고, 새 TASK-4158 모니터 PID `24952`를 띄웠다.

