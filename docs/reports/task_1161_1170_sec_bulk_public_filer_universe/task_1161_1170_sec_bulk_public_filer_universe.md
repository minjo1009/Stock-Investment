# Task1161-1170 SEC Bulk Public-Filer Universe

## Decision Summary

- Verdict: `sec_public_filer_asof_proxy_acquired_true_exchange_listing_still_missing`.
- SEC bulk download status: `downloaded`.
- SEC bulk zip bytes: 1545902430.
- Zip JSON members: 978261.
- Files processed: 978261.
- Public-filer entities: 8129.
- Membership event rows: 21208.
- Asof membership rows: 592936.
- Symbols per decision range: 7198 to 10540.
- Public-filer proxy universe ready: `1`.
- True exchange-listed universe ready: `0`.
- Replay executed: 0.
- Selection promoted: 0.

## Quant Expert Report

This task downloads the official SEC bulk submissions ZIP and builds a broad public-filer as-of proxy universe.

Important distinction:

- This is stronger than the old custom 10x7 universe.
- It is still not the same as a true exchange-listed PIT universe.
- It uses SEC filing acceptance time plus current ticker metadata from submissions JSON.
- It does not fully solve historical ticker changes, delistings, or exchange listing date history.

Leakage decision:

- Current ticker metadata is not treated as true historical listing proof.
- Public-filer proxy rows are prepared for future policy pre-registration.
- No backtest or selection promotion was executed in this task.

## No-Background Decision-Maker Report

We acquired the big official SEC dataset.

That gives us a much wider universe than the handpicked 70 names.

Now the model can be prepared to choose from a broad public-company universe, not from a winner basket.

But this is still a proxy. To claim true exchange-listed PIT, we still need historical exchange listing and ticker-change data.

## Artifact Manifest

- `data/raw/task_1161_1170_sec_bulk_submissions/submissions.zip`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1161_sec_bulk_download_ledger.csv`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1162_sec_bulk_zip_inventory.csv`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1163_public_filer_entity_panel.csv`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1164_public_filer_membership_events.csv`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1165_decision_calendar.csv`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1166_public_filer_asof_universe_panel.csv`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1167_public_filer_universe_coverage.csv`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1168_vendor_exchange_listing_gap.csv`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1169_public_filer_proxy_readiness.csv`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1170_sec_bulk_public_filer_closeout.csv`
- `data/artifacts/task_1161_1170_sec_bulk_public_filer_universe/task1170_sec_bulk_public_filer_closeout.json`
