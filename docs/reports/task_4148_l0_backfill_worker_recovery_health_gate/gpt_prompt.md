# TASK-4148 GPT Pro Review Prompt

You are GPT Pro reviewing a local L0-L2 data pipeline recovery problem.

Important constraint:
- Do not use GitHub.
- Do not browse or inspect any repository.
- Assume the GitHub repository is stale and does not include the latest local work.
- Use only the context pasted below.
- Avoid overengineering. Recommend fixes that directly improve reliability, proof, and recovery.
- This is a diagnostic/source-acquisition pipeline. Do not open signal, order, broker, paper/live, or real-capital authority.

Please answer in Korean, using simple/direct wording.

## Project hard state

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data is UNKNOWN/BLOCKER, never negative evidence.

## Current problem

After TASK-4147, two critical L0 backfill lanes look very bad:

- `public_newswire_backfill`: 42.9617% complete, latest proof says STOPPED.
- `public_market_macro_news_backfill`: 29.1076% complete, latest proof says STOPPED.

This is not just stale reporting:

- `data/artifacts/l0_public_newswire_backfill/background_process.json` records pid `9276`.
- `data/artifacts/l0_public_market_macro_news_backfill/background_process.json` records pid `21684`.
- Direct process check shows neither pid is alive.
- Only the L1/L2 handoff loop pid `32576` is alive.

So the problem is:

1. The L0 backfill workers are actually dead.
2. The `background_process.json` pid files are stale.
3. Existing validators accepted “pid recorded” instead of “pid alive”.
4. L1/L2 loops keep running, but they only process existing L0 evidence. They do not revive dead L0 collectors.

## Current evidence

`data/artifacts/l0_backfill_orchestration/lane_reliability.csv` says:

| lane | health | running | complete | progress_pct | completed_units | total_units | last_status | last_event_at |
|---|---|---:|---:|---:|---:|---:|---|---|
| daily | RUNNING | 1 | 0 | 99.3688 | 11964 | 12040 | EXHAUSTED | 2026-06-30T05:25:51Z |
| five_min | RUNNING | 1 | 0 | 13.4915 | 52030 | 385280 | EMPTY_PROVIDER_RESPONSE | 2026-06-30T05:28:09Z |
| public_context_news_backfill | RUNNING | 1 | 0 | 99.3289 | 148 | 149 | RUNNING | 2026-06-30T05:23:53Z |
| public_newswire_backfill | STOPPED | 0 | 0 | 42.9617 | 1761 | 4099 | RUNNING | 2026-06-28T22:50:12Z |
| public_market_macro_news_backfill | STOPPED | 0 | 0 | 29.1076 | 760 | 2611 | RUNNING | 2026-06-28T22:57:27Z |

`current_alerts.md` already says:
- P0 `public_newswire_backfill` lane_not_running_incomplete.
- P0 `public_market_macro_news_backfill` lane_not_running_incomplete.

But TASK-4146 validator still passed because it checked `background_pid_recorded_after_supervisor > 0`, not whether the pid is alive.

## Existing scripts

Existing supervisor:
- `scripts/run_l0_backfill_supervisor.ps1`
- It calls `scripts/run_l0_backfill_reliability_audit.py --write`.
- It reads `data/artifacts/l0_backfill_orchestration/supervisor_recommendations.json`.
- For stopped incomplete lanes, it calls:
  - `scripts/start_l0_public_newswire_backfill.ps1`
  - `scripts/start_l0_public_market_macro_news_backfill.ps1`
- Each start script writes a `background_process.json` with pid and safety flags.

Existing start scripts:
- `scripts/start_l0_public_newswire_backfill.ps1`
  - Starts `python scripts/run_l0_public_newswire_collector.py --mode backfill`.
  - Writes `data/artifacts/l0_public_newswire_backfill/background_process.json`.
  - Removes STOP file.
  - Diagnostic flags remain closed.
- `scripts/start_l0_public_market_macro_news_backfill.ps1`
  - Starts `python scripts/run_l0_public_market_macro_news_collector.py --mode backfill`.
  - Writes `data/artifacts/l0_public_market_macro_news_backfill/background_process.json`.
  - Removes STOP file.
  - Diagnostic flags remain closed.

Known weakness:
- audit/proof can say stopped, but supervisor/restart result was not hardened enough.
- validators do not fail on stale pid.
- stale pid files can mislead downstream reports.
- L1/L2 validators pass even when L0 backfill workers are dead.

## TASK-4147 current outputs

TASK-4147 created:
- 1,093 L1 article packets.
- 1,842 L2 diagnostic feature schema rows.
- 189 newswire mapping review/proof rows.
- 2,646 existing L0 newswire mapped rows.
- safe realtime config.
- 15-minute Windows task: `TraderBrainL0L2Hardening4147`.

But TASK-4147 did not solve the L0 backfill worker death.

## What I need from GPT Pro

Give a concrete repair plan for TASK-4148.

Please cover:

1. How to recover the two stopped lanes now.
2. How to prevent stale pid files from being accepted.
3. How to make supervisor proof include `pid_recorded`, `pid_alive`, `restart_attempted`, `restart_pid`, `restart_alive`, `last_event_age`, `progress_delta`, and blocker reason.
4. How to update validators so L1/L2 cannot claim healthy L0 coverage when critical L0 workers are dead.
5. Whether to patch existing TASK-4146/TASK-4147 validators or create a new TASK-4148 validator only.
6. How to handle logs that are slow/large/UTF-16 without making the validator fragile.
7. What to avoid as overengineering.
8. Done definition for TASK-4148.

Keep the answer practical. Use tables where helpful.
