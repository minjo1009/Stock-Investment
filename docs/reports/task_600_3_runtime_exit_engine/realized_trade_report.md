## Problem

- Closed runtime rows must populate realized_pnl and holding_minutes from exact entry and exit lifecycle timestamps.

## Evidence

- LIFECYCLE|AMD|2026-05-19|0000036477: AMD TIMEOUT realized_pnl=37.62 holding_minutes=1337.8838
- LIFECYCLE|AMD|2026-05-19|0000036731: AMD TIMEOUT realized_pnl=28.705 holding_minutes=1337.9061
- LIFECYCLE|AMD|2026-05-19|0000036857: AMD TIMEOUT realized_pnl=25.22 holding_minutes=1331.6192
- LIFECYCLE|AMZN|2026-05-20|0000035811: AMZN TIMEOUT realized_pnl=-2.405 holding_minutes=1306.1364
- LIFECYCLE|AMZN|2026-05-20|0000036025: AMZN TIMEOUT realized_pnl=-2.605 holding_minutes=1296.7858
- LIFECYCLE|AMD|2026-05-20|0000036698: AMD TIMEOUT realized_pnl=-6.555 holding_minutes=1097.1902
- LIFECYCLE|AMZN|2026-05-21|0000036548: AMZN TIMEOUT realized_pnl=4.22 holding_minutes=1427.416
- LIFECYCLE|AMZN|2026-05-21|0000036625: AMZN TIMEOUT realized_pnl=4.3 holding_minutes=1427.3482
- LIFECYCLE|AMZN|2026-05-21|0000036643: AMZN TIMEOUT realized_pnl=4.19 holding_minutes=1421.4553
- LIFECYCLE|AMZN|2026-05-22|0000035451: AMZN TIMEOUT realized_pnl=-4.901 holding_minutes=5729.2891
- LIFECYCLE|AMD|2026-05-22|0000035396: AMD TIMEOUT realized_pnl=19.0901 holding_minutes=7203.4851
- LIFECYCLE|AMZN|2026-05-27|0000038518: AMZN TIMEOUT realized_pnl=-0.68 holding_minutes=1432.9014
- LIFECYCLE|AMZN|2026-05-27|0000038693: AMZN TIMEOUT realized_pnl=-1.2 holding_minutes=1429.3316
- LIFECYCLE|AMZN|2026-05-27|0000038718: AMZN TIMEOUT realized_pnl=-0.925 holding_minutes=1427.6822
- LIFECYCLE|MSFT|2026-05-28|0000038238: MSFT TIMEOUT realized_pnl=19.1372 holding_minutes=1353.3526
- LIFECYCLE|AMD|2026-05-28|0000037813: AMD TIMEOUT realized_pnl=-7.92 holding_minutes=1415.1682
- LIFECYCLE|AMD|2026-05-28|0000037867: AMD TIMEOUT realized_pnl=-8.03 holding_minutes=1399.5812
- LIFECYCLE|MSFT|2026-05-29|0000035543: MSFT TIMEOUT realized_pnl=15.79 holding_minutes=4232.3696
- LIFECYCLE|MSFT|2026-06-01|0000036992: MSFT TIMEOUT realized_pnl=-14.1043 holding_minutes=1399.6992
- LIFECYCLE|MSFT|2026-06-01|0000037419: MSFT TIMEOUT realized_pnl=-17.7443 holding_minutes=1379.1098
- LIFECYCLE|MSFT|2026-06-01|0000037482: MSFT TIMEOUT realized_pnl=-19.0093 holding_minutes=1379.0561
- LIFECYCLE|AMD|2026-06-02|0000040987: AMD TIMEOUT realized_pnl=3.68 holding_minutes=580.1322
- LIFECYCLE|AMD|2026-06-02|0000041006: AMD TIMEOUT realized_pnl=4.108 holding_minutes=569.4007

## Root Cause

- OPEN-only lifecycle state prevented realized trade reporting before T600-3.

## Fix Candidate

- Update only exact-linked lifecycle rows with exit_order_id, exit_fill_id, exit_reason, realized_pnl, and holding_minutes.

## Acceptance Impact

- realized_pnl_populated=23
- Inferred lifecycle matching used flag remains 0.
