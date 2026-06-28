# L2 Canonical Primitive Contract

## Purpose

L2 is the canonical primitive fact and source-local feature layer between L1 source receipt/freshness/lineage and L3 economic meaning. L2 does not emit strategy decisions, rankings, scores, BUY/SELL signals, paper orders, live orders, or broker mutations.

## Required Object

Every L2 row must conform to `L2PrimitiveFact`:

| Field | Required | Rule |
|---|---:|---|
| `primitive_id` | yes | Stable unique primitive id. |
| `primitive_batch_id` | yes | Stable batch id. |
| `source_receipt_id` | yes | Receipt, artifact receipt, or L1 source receipt id. |
| `source_family` | yes | Source family such as `market_bar`, `indicator`, `news_event`, `sec_event`, `macro`, `microstructure_quote`, `microstructure_trade`, `broker_state`, or `historical_artifact`. |
| `provider` | yes | Provider or artifact path/source namespace. |
| `symbol` | nullable | Market symbol when applicable. |
| `entity_id` | nullable | Issuer/entity id when applicable. |
| `event_time` | yes | Time the primitive event happened. |
| `source_ts` | yes | Time from the source system or artifact row. |
| `capture_ts` | yes | Time the repo captured or ingested the source. |
| `available_to_brain_ts` | yes | First time L3 or later layers may consume the row. |
| `asof_ts` | yes | As-of timestamp for downstream filtering. |
| `primitive_type` | yes | Broad primitive type. |
| `primitive_subtype` | yes | Concrete primitive subtype. |
| `primitive_payload_json` | yes | Source-local payload JSON. It must not contain order intent. |
| `freshness_status` | yes | One of `FRESH`, `CURRENT_OR_RECENT`, `STALE`, `MISSING`, `BLOCKED`, `UNKNOWN`. |
| `source_time_certified` | yes | `1` only when the source/event time is known. |
| `closed_bar_only` | yes | `1` for market bar and market-bar-derived primitives. |
| `runtime_context` | yes | One allowed runtime context. |
| `input_hash` | yes | Hash of source input payload. |
| `output_hash` | yes | Hash of generated primitive payload. |
| `lineage_edge_id` | yes | Link from receipt/input to primitive. |
| `missing_source_is_negative` | yes | Must be `0`. |
| `diagnostic_only` | yes | Must be `1` for this task. |
| `trade_output_flag` | yes | Must be `0`. |
| `score_output_flag` | yes | Must be `0`. |
| `order_intent_flag` | yes | Must be `0`. |

## Allowed Runtime Contexts

- `HISTORICAL_RESEARCH`
- `BACKTEST_RESEARCH`
- `LIVE_INTRADAY_DIAGNOSTIC`
- `OPERATOR_REPLAY_DIAGNOSTIC`

## Mandatory Rules

- L3 must not consume primitive rows without `runtime_context`.
- L3 must not consume primitive rows without `source_receipt_id` or `lineage_edge_id`.
- L3 must not consume stale primitive rows unless explicitly running a stale-data diagnostic.
- Historical artifacts and live intraday evidence must never be mixed in the same primitive batch.
- Missing data must never become negative evidence.
- L2 must not emit BUY/SELL, rank, score, order intent, paper order, live order, or broker mutation.
- Market-bar primitives must be closed-bar only.
- Indicator primitives are local features and remain diagnostic-only.

## Current Implementation

The canonical Python contract lives in `src/l2/contracts.py`. SQLite schema setup lives in `src/l2/stores/sqlite_l2_store.py` and is also called by `tools/db/apply_management_schema.py`.
