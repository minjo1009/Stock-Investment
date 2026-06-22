# Task3082 External Tool Layer Utilization Plan

## Decision Summary

- Verdict: `external_tool_layer_utilization_plan_completed_diagnostic_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: Task3081's external MCP/open-source review was converted into concrete Trader Brain layer usage contracts.
- What did not change: no MCP install, source acquisition, replay, selector change, sizing change, paper order, live order, or deployment state changed.
- Key conclusion: external tools should be used as layer-specific sidecars, with source identity, timestamp, raw payload, hash, and forbidden-output rules preserved at every boundary.
- Next action: implement only the P0 `external_source_sidecar` pilot before any replay or policy comparison.

## Quant Expert Report

### Layer-by-Layer Utilization Contract

| Brain Layer | Tool Use | Concrete Input | Concrete Output | Forbidden Output | First Pilot |
| --- | --- | --- | --- | --- | --- |
| Raw source evidence | OpenBB, Alpha Vantage MCP, Financial Datasets MCP | `provider`, `tool_name`, `query`, `requested_at`, `received_at`, raw payload | `external_source_receipt` row with payload path, hash, provider, endpoint, terms note | interpreted signal, rank, score, buy/sell, label | collect one official market/fundamental/news sample per 10 symbols |
| Primitive fact extraction | OpenBB Python/API output, official MCP payloads | retained raw payload and schema-normalized rows | source-local facts such as price bars, statement fields, news metadata, filing/event metadata | economic meaning, thesis verdict, negative label | build extractor fixture from the retained source receipts |
| Economic meaning | Qlib only as offline feature audit reference; no direct MCP decisioning | primitive facts plus current Task742 meaning schema | interpretation candidates with confidence, uncertainty, and required confirmation | score/rank/sizing/backtest eligibility | compare whether external fields fill missing confirmation needs |
| Relation edge | GitHub MCP read-only for upstream logic/security context; NautilusTrader as replay architecture reference | reviewed repo issue/PR/security notes and current relation schema | engineering review notes or relation schema improvement proposals | direct edge mutation from external text | produce read-only upstream watch packet |
| Candidate bundle | OpenBB/MCP source receipts attached to current candidate context | `trade_spec_id`, `symbol`, `decision_asof_ts`, source receipt IDs | candidate evidence bundle with traceable source references | assignment-ready feature without as-of check | attach receipts to a small non-trading sample bundle |
| Resolver and QA | GitHub MCP read-only, repo validators, source manifest checks | upstream repo status, MCP tool metadata, local manifest rows | blocker list, missing-source state, security review lane, validation command | acceptance claim, broker truth claim | run sidecar manifest validation only |
| Slot decision | No external tool as decision maker; vectorbt only as post-hoc diagnostic mirror | frozen candidate bundles and existing slot-decision contract | diagnostic comparison artifact outside canonical assignment | changed ranking, changed slot winner, changed allocation | no pilot until source sidecar passes |
| Backtest or deployment gate | NautilusTrader/vectorbt/Lean as comparison labs only | frozen policy, frozen inputs, declared experiment class | same/different-experiment diagnostic report | acceptance, deployment readiness, real-capital permission | defer until strict raw/as-of blocker policy is resolved |
| Read-only cockpit | OpenBB/GitHub MCP status summaries after local normalization | validated sidecar status rows only | UI-visible source health, connector status, blocker count | live order mutation or broker action | show connector health in Risk/Settings only |

### Concrete P0 Pilot Shape

The first useful pilot is not "connect many MCPs." It is one small governed source sidecar.

Required object:

```text
external_source_receipt
```

Minimum fields:

```text
receipt_id
provider
tool_name
query_scope
symbol
requested_at_utc
received_at_utc
source_published_at_utc
tradable_after_ts_utc
raw_payload_path
raw_payload_sha256
normalized_row_count
provider_terms_note
point_in_time_status
source_time_status
allowed_layer
forbidden_use
```

Allowed output:

```text
source evidence only
```

Forbidden use:

```text
buy
sell
rank
size
label
selector input
paper order
live order
acceptance evidence by itself
```

### Tool-Specific Placement

#### OpenBB

- Use in `Raw source evidence` and `Primitive fact extraction`.
- Purpose: unify vendor/public data calls behind one local integration layer.
- Concrete first use: fetch a tiny sample of historical price/fundamental/news metadata, retain raw responses, normalize into `external_source_receipt`.
- Success means: data can be traced, hashed, and time-stamped.
- Success does not mean: source is accepted for strategy assignment.

#### Alpha Vantage MCP or Financial Datasets MCP

- Use in `Raw source evidence` only at first.
- Purpose: test whether MCP-delivered market/fundamental/news payloads can satisfy the same source discipline as repo-native collectors.
- Concrete first use: run side-by-side receipt capture against the same symbols queried through OpenBB.
- Success means: MCP payloads can be retained with provider and time metadata.
- Success does not mean: MCP data is price truth or PIT-complete.

#### GitHub MCP Read-Only

- Use in `Resolver and QA`, `Relation edge`, and governance monitoring.
- Purpose: watch upstream repos, security issues, MCP server changes, and implementation patterns without granting write access.
- Concrete first use: read-only monitor list for OpenBB, Alpha Vantage MCP, Financial Datasets MCP, NautilusTrader, vectorbt, Qlib.
- Success means: upstream change notes become review packets.
- Success does not mean: external GitHub content changes local source truth.

#### NautilusTrader

- Use as `Backtest or deployment gate` architecture reference only.
- Purpose: borrow deterministic replay/event-log ideas for audit design.
- Concrete first use: map its event/replay concepts to our existing policy freeze and same/different-experiment gate.
- Success means: better replay audit checklist.
- Success does not mean: we migrate engines or enable live trading.

#### vectorbt

- Use only as `Slot decision` or `Backtest` diagnostic mirror after canonical artifacts exist.
- Purpose: fast independent sanity check of frozen candidate panels.
- Concrete first use: reproduce a frozen diagnostic panel without changing assignment logic.
- Success means: discrepancy report versus canonical harness.
- Success does not mean: vectorbt result can approve a rule.

#### Qlib

- Use as offline research reference for feature pipelines and model diagnostics.
- Purpose: study factor pipeline discipline, not import a model stack.
- Concrete first use: compare its pipeline concepts to our primitive/economic meaning boundaries.
- Success means: clearer feature registry ideas.
- Success does not mean: ML model output enters slot decision.

### Implementation Order

1. `external_source_receipt` schema and manifest validator.
2. OpenBB sample capture with raw payload retention.
3. One financial MCP sample capture using the same receipt schema.
4. GitHub MCP read-only upstream watch packet.
5. Candidate bundle attachment for a small non-trading sample.
6. Only after those pass, consider vectorbt/NautilusTrader diagnostic mirrors.

### Stop Rules

- Stop if raw payload cannot be retained.
- Stop if `received_at` or `source_published_at` cannot be represented.
- Stop if provider terms do not allow retained research use.
- Stop if tool output includes recommendations that cannot be separated from source facts.
- Stop if any downstream code tries to write external output into selector, rank, sizing, paper order, or live order fields.

## No-Background Decision-Maker Report

Conclusion first: external tools have a place, but only as controlled sidecars.

Use OpenBB and one financial MCP to improve source memory. Use GitHub MCP read-only to monitor useful repos and risks. Use NautilusTrader and vectorbt later as comparison labs. Do not use any of them as the trading brain itself.

The first concrete build should be `external_source_receipt`. If that object cannot preserve raw payload, timestamp, provider, and hash, the tool should not enter the brain.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `docs/operating_system/project_operating_state.md`
  - `docs/architecture/brain_layer_map.md`
  - `docs/reports/task_3081_external_mcp_open_source_brain_review/task_3081_external_mcp_open_source_brain_review.md`
- Outputs:
  - `docs/reports/task_3082_external_tool_layer_utilization_plan/task_3082_external_tool_layer_utilization_plan.md`
- Row counts:
  - Layer utilization rows: 9.
  - Tool placement sections: 6.
- Validation commands:
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Not applicable. No external raw datasets were acquired.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
