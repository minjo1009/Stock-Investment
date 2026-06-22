# Task3081 External MCP And Open Source Brain Review

## Decision Summary

- Verdict: `external_mcp_open_source_brain_review_completed_diagnostic_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: report-only review of MCP and open-source tools that may help the Trader Brain.
- What did not change: no source acquisition, replay, selector, sizing, paper order, live order, deployment, or acceptance state changed.
- Key conclusion: the brain can be developed further, but external tools should be attached as audited sidecars to specific layers, not as direct trading decision authority.
- Next action: run a small P0 pilot map for OpenBB, read-only GitHub MCP, and one market-data MCP under raw-response retention and no assignment writes.

## Quant Expert Report

### Current Brain Diagnosis

The current Trader Brain has the right high-level shape:

```text
Raw source evidence
-> Primitive fact extraction
-> Economic meaning
-> Relation edge
-> Candidate bundle
-> Slot decision
-> Backtest or deployment gate
```

This is structurally sound because it prevents direct jumps from source text or LLM commentary into buy, sell, rank, sizing, or replay eligibility.

Observed strengths:

- L4 thesis invalidation is outcome-blind and uses pre-trade L2/L3/source-time fields.
- Baseline and challenger policy identities are frozen before performance comparison.
- Shadow journal and runtime catalog surfaces exist for read-only inspection.
- Status boundaries are explicit: tests, reports, MCPs, and GPT-style reviewers do not create acceptance.

Observed blockers:

- Strict raw/as-of complete rows remain `0/3100` in the latest policy compare chain.
- L2/L3 attribution showed that bad trades can survive even when source-integrated context exists.
- Runtime evidence quality is still partial in the shadow journal contract.
- Performance comparison for the L4 challenger is blocked until governed replay artifacts exist.

### External Tool Fit

| Tier | Candidate | Best Brain Layer Fit | Use | Risk |
| --- | --- | --- | --- | --- |
| P0 | OpenBB Open Data Platform | Source evidence / primitive facts | Vendor/public data integration, local API, analyst/agent data surface | Must preserve raw response, timestamp, provider, and license boundaries |
| P0 | GitHub MCP read-only | Governance / code review / external repo monitoring | Track relevant repos, issues, PRs, security notes, and implementation examples | Write tools must stay disabled for exploration |
| P0 | Alpha Vantage MCP or Financial Datasets MCP | Source evidence sidecar | Market/fundamental/news query testing through MCP | API limits, provider terms, and point-in-time gaps must be audited |
| P0 | NautilusTrader | Replay architecture reference | Deterministic event/replay design reference, not replacement engine | Integration cost is high; live-trading features must stay disabled |
| P1 | vectorbt | Research cross-check | Fast vectorized sweep outside canonical acceptance | Easy to overfit; diagnostic-only |
| P1 | Qlib | ML research sandbox | Factor/model pipeline and model diagnostics | Heavy ML/RL surface can violate simplicity and leakage discipline |
| P1 | Zipline-reloaded | Event-driven backtest reference | Event-driven benchmark and PyData compatibility | Not a direct fit for current strict source/journal architecture |
| P2 | Yahoo Finance MCP / MaverickMCP | Convenience research only | Quick lookup and watchlist-style analysis | Unofficial or convenience data cannot become source truth |
| P2 | FinRL | Research reading only | RL framework ideas | RL policy learning is not aligned with current blocker-first governance |
| P2 | Backtrader | Legacy reference only | Simple Python backtest patterns | GPL/license and older broker assumptions reduce fit |

### Recommended Development Path

1. Build an `external_source_sidecar` contract.
   - Inputs: provider, endpoint/tool, requested_at, received_at, query, raw payload path, payload hash, license note.
   - Output: source evidence rows only.
   - Forbidden output: buy/sell/rank/size/label.

2. Pilot OpenBB first.
   - Reason: strongest fit to the existing source integration problem.
   - Scope: one provider family, one cached raw-response manifest, zero assignment writes.

3. Add read-only GitHub MCP second.
   - Reason: useful for monitoring MCP servers, quant frameworks, security issues, and upstream changes.
   - Scope: context/issues/pull_requests only, read-only header or equivalent.

4. Test one financial MCP third.
   - Preferred order: Alpha Vantage official MCP, then Financial Datasets MCP.
   - Scope: compare returned data against existing raw-source discipline; do not use it as price truth until timestamp and provider terms pass.

5. Use NautilusTrader/vectorbt only as comparison laboratories.
   - NautilusTrader: deterministic replay ideas.
   - vectorbt: fast diagnostic sweeps.
   - Neither should supersede the current governed backtest harness without a separate migration plan.

### Leakage And Safety Audit

- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback.
- Missing labels are not negatives.
- External MCP output is source evidence or review context only.
- LLM/MCP output must not enter assignment logic.
- MCP servers must be sandboxed, allowlisted, and read-only unless a separate security review approves writes.
- Secrets and broker credentials must not be exposed to third-party MCP servers.

## No-Background Decision-Maker Report

Conclusion first: yes, the Trader Brain can be developed further.

The strongest opportunity is not a smarter trading bot. It is better source plumbing and better audit memory.

Use OpenBB for data integration experiments. Use GitHub MCP in read-only mode to monitor useful repos and implementation changes. Use one official or narrow financial MCP as a source sidecar. Use NautilusTrader and vectorbt as comparison labs only.

Do not let any MCP or open-source engine decide trades. The current strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`.

## Artifact Manifest

- Inputs:
  - `docs/operating_system/project_operating_state.md`
  - `docs/architecture/brain_layer_map.md`
  - `docs/architecture/project_status_authority_matrix.md`
  - `docs/ownership/current_operating_model.md`
  - `docs/reports/task_2861_2900_shadow_journal_runtime_contract/task_2861_2900_shadow_journal_runtime_contract.md`
  - `docs/reports/task_2921_2940_l2_l3_mdd_attribution_pack/task_2921_2940_l2_l3_mdd_attribution_pack.md`
  - `docs/reports/task_2941_2960_l4_thesis_invalidation/task_2941_2960_l4_thesis_invalidation.md`
  - `docs/reports/task_2961_2980_frozen_policy_l4_challenger_compare_plan/task_2961_2980_frozen_policy_l4_challenger_compare_plan.md`
  - Public web/GitHub sources listed in `source_manifest.csv`.
- Outputs:
  - `docs/reports/task_3081_external_mcp_open_source_brain_review/task_3081_external_mcp_open_source_brain_review.md`
  - `docs/reports/task_3081_external_mcp_open_source_brain_review/source_manifest.csv`
- Row counts:
  - Source manifest rows: 13.
  - External repos checked through GitHub API: 12.
- Validation commands:
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Not applicable. No external raw datasets were acquired.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
