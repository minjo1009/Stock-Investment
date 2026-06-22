# Task1268-1287 Source Extractor Attachment

## Decision Summary

- Verdict: `source_extractors_attached_partial_backtest_readiness_no_replay`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: backtest source data schema was clarified and SEC complete-submission exhibit extractors were attached for IR/CEO narrative and contract/order evidence.
- Key metrics: 700 complete submissions cached, 2747 exhibit documents indexed, 1117 IR/CEO evidence rows, 1645 contract/order evidence rows, 310 enhanced L1 rows, 1860 enhanced L3 edges.
- Next action: preregister a shadow-only multisource policy or attach licensed analyst/full transcript feeds before controlled replay.

## Quant Expert Report

- Data source and source readiness: SEC complete submission `.txt` archives were used to parse EX-99/EX-10/press release style exhibits; Task1258 policy and market panels were reused.
- Exact join keys: `selection_id`, `symbol`, `decision_asof_ts`, `cik`, `accession`, `document_id`.
- Leakage audit: all exhibit evidence inherits SEC `available_to_brain_ts <= decision_asof_ts`; no PnL, future return, or outcome columns are used for assignment.
- Split/OOS metrics: not applicable; no replay was executed.
- Remaining blockers: analyst/institution PIT data, full earnings-call transcript Q&A, customer-side contract confirmation, symbol-level policy affected-entity extractor.

## No-Background Decision-Maker Report

We clarified exactly what data the brain needs.

Then we attached the first real non-SEC-like company source lane by parsing SEC exhibit documents that often contain press releases, CEO quotes, guidance, contracts, and customer announcements.

This is enough for a shadow policy preregistration, but not enough for final strategy acceptance.

## Artifact Manifest

- `task1268_backtest_source_data_schema.csv`
- `task1269_sec_complete_submission_download_ledger.csv`
- `task1270_sec_exhibit_document_index.csv`
- `task1271_ir_ceo_exhibit_evidence.csv`
- `task1272_contract_order_exhibit_evidence.csv`
- `task1273_enhanced_l1_multisource_packets.csv`
- `task1274_enhanced_l2_multisource_interpretation.csv`
- `task1275_enhanced_l3_relation_edges.csv`
- `task1276_backtest_readiness_panel.csv`
- `task1277_remaining_source_gap_ledger.csv`
- `task1278_backtest_readiness_gate.csv`
- `task1287_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1268_1287_source_extractors_validate.py`
- `python -m unittest tests.test_trader_brain_1268_1287_source_extractors`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
