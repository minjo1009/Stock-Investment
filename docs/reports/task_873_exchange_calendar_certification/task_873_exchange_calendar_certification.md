# Task873 Exchange Calendar Certification

## Decision Summary

- Verdict: executed for diagnostic controlled replay.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: certify exchange sessions from `2021-01-01` through latest completed US session plus 30 days.

## Quant Expert Report

Required fields:

```text
calendar_id
exchange
session_date
open_ts_utc
close_ts_utc
early_close_flag
holiday_flag
source
source_hash
calendar_version
```

Task858 found the current `config/nasdaq_market_calendar.csv` covers 2026 holiday/early-close rows only. It is not enough for replay from 2021.

## No-Background Decision-Maker Report

Before entry timing can be tested, the system must know actual market sessions.

Execution update:

- A data-derived QQQ session calendar was built for the diagnostic controlled replay.
- Calendar status: `certified_for_controlled_replay_diagnostic`.
- This is not a full production exchange-calendar certification.

## Artifact Manifest

- Output: `data/artifacts/task_870_879_full_controlled_replay/calendar_certification_manifest.csv`.
- Validation command: `python scripts/trader_brain_870_879_full_replay_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
