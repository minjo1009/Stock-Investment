# TASK-4148 GPT Pro Post-Implementation Review Prompt

You are GPT Pro reviewing a local L0/L1/L2 data-pipeline recovery patch.

Important constraints:
- Do not use GitHub.
- Do not browse or inspect any repository.
- The GitHub repo is stale and does not include the latest local work.
- Use only the context pasted below.
- Avoid overengineering. Recommend only P0/P1 fixes that directly improve worker recovery, pid-alive proof, validator coverage, or operational clarity.
- This is diagnostic/source-acquisition infrastructure. Do not open signal, order, broker, paper/live, deployment, strategy acceptance, or real-capital authority.
- Please answer in Korean, using simple/direct wording.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data is UNKNOWN/BLOCKER, never negative evidence.

## Original problem

Two critical L0 historical backfill workers were incomplete and actually dead:

- public_newswire_backfill: 42.9617% complete, previous proof STOPPED.
- public_market_macro_news_backfill: 29.1076% complete, previous proof STOPPED.

The old evidence was misleading:

- background_process.json had a pid, but the pid was stale/dead.
- L1/L2 loops kept running, but they only processed existing L0 evidence.
- Existing validators accepted "pid recorded" instead of "pid alive".
- Therefore L1/L2 could look healthy while L0 backfill collection was not actually running.

## What Codex changed

TASK-4148 implemented:

1. New recovery runner:
   - scripts/run_l0_backfill_worker_recovery_4148.py
   - Checks public_newswire_backfill and public_market_macro_news_backfill.
   - Reads each lane's background_process.json.
   - Checks whether the recorded pid is alive through the OS.
   - If incomplete and pid is dead, starts the existing lane start script.
   - Writes:
     - data/artifacts/task_4148_l0_backfill_worker_recovery_health_gate/l0_worker_recovery_ledger.csv
     - data/artifacts/task_4148_l0_backfill_worker_recovery_health_gate/l0_worker_health_gate.csv
     - summary.json

2. New validator:
   - scripts/validate_l0_backfill_worker_recovery_4148.py
   - Fails if a critical incomplete lane has no live pid.
   - Fails if stop file exists.
   - Fails if trade/broker/real-capital authority opens.
   - Does not tail huge logs.

3. Existing supervisor hardened:
   - scripts/run_l0_backfill_supervisor.ps1
   - After restart request, waits briefly and writes RESTART_CONFIRMED_ALIVE or RESTART_STALE_OR_DEAD.

4. Reliability audit hardened:
   - scripts/run_l0_backfill_reliability_audit.py
   - Does not rely only on stale current_status.json background_processes.
   - Directly reads lane background_process.json and verifies pid alive.
   - lane_reliability.csv now includes pid_recorded and pid_alive.

5. Existing L1/L2 validators hardened:
   - scripts/run_l0_l2_wide_handoff_4146.py now writes background_pid_alive_after_supervisor.
   - scripts/validate_l0_l2_wide_handoff_4146.py fails if critical incomplete L0 worker is not alive.
   - scripts/run_l0_l2_hardening_4147.py writes pid_recorded/pid_alive in backfill proof and BLOCKED_WORKER_NOT_ALIVE when appropriate.
   - scripts/validate_l0_l2_hardening_4147.py fails on critical incomplete dead workers.

6. Project management updated:
   - ops/task_registry.yaml
   - ops/doc_registry.yaml
   - docs/active/ACTIVE_SSOT_INDEX.md
   - docs/active/CURRENT_TASKS.md
   - docs/active/PROJECT_STATUS.md
   - docs/reports/task_4148_l0_backfill_worker_recovery_health_gate/*

## Current proof

Current lane reliability:

| lane | health | running | pid_recorded | pid_alive | complete | progress_pct | completed_units | total_units |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| daily | RUNNING | 1 | 20848 | 1 | 0 | 99.3688 | 11964 | 12040 |
| five_min | RUNNING | 1 | 34128 | 1 | 0 | 15.0319 | 57965 | 385280 |
| public_context_news_backfill | RUNNING | 1 | 32256 | 1 | 0 | 99.3289 | 148 | 149 |
| public_newswire_backfill | RUNNING | 1 | 29248 | 1 | 0 | 42.9617 | 1761 | 4099 |
| public_market_macro_news_backfill | RUNNING | 1 | 19148 | 1 | 0 | 29.1076 | 760 | 2611 |

TASK-4148 summary:

- lanes_checked: 2
- after_pid_alive_lanes: 2
- incomplete_dead_lanes: []
- authority_flags_opened: 0
- reliability audit: alerts=0, recommendations=0

Validation results:

- TASK-4148 validator: PASS_WITH_WARNINGS
  - warning: current validation run did not reproduce stale pid because the workers are already alive.
- TASK-4146 validator: PASS
  - background_pid_rows_recorded: 5
  - background_pid_rows_alive: 5
- TASK-4147 validator: PASS
  - critical_incomplete_backfill_workers_alive_or_complete
- closeout validator: PASS_WITH_WARNINGS
  - warning: dirty files outside TASK-4148 manifest ignored by scope gate.
  - warning: TASK-4148 validator warning above.

## Review questions

Please answer:

1. Does TASK-4148 now solve the real problem: L1/L2 cannot claim healthy L0 coverage while critical incomplete L0 workers are dead?
2. Are there any P0/P1 missing safeguards?
3. Is there any overengineering to remove?
4. Should the stale-pid warning remain a warning, or should Codex keep an explicit stale-pid regression fixture/artifact?
5. Is the reliability-audit change enough, or should current_status.json generation also be patched?
6. Does the closeout state look acceptable with PASS_WITH_WARNINGS?
7. Give a concrete Codex patch plan only if something must be changed.

Output format:

1. PASS / FAIL / BLOCKED
2. P0 issues
3. P1 issues
4. Optional improvements
5. Things to avoid
6. Final recommendation
