# Task3121 External Tool Necessity Cost Benefit Review

## Decision Summary

- Verdict: `selective_external_tool_adoption_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: Task3082's layer-utilization plan was filtered through necessity, speed, API cadence, rate-limit, and existing-system comparison.
- What did not change: no MCP install, API call, source acquisition, replay, selector change, sizing change, paper order, live order, or deployment state changed.
- Key conclusion: most external tools are not worth attaching as production data paths now. Use only narrow, low-frequency pilots where they reduce integration/audit burden.

## Quant Expert Report

### Existing Baseline

Current repo evidence already shows three important facts:

- Task2251-2280 acquired a 3,100-candidate full-source panel with 2,420 API call rows, 753 usable calls, 1,667 blocked/retry rows, 4,588,915 normalized rows, 3,100 feature rows, and 2,983 non-gap feature rows. The bottleneck was provider entitlement/rate blocking, not lack of orchestration.
- Task2561-2580 acquired liquidity/rates regime efficiently: 49 raw responses produced 768,841 normalized packet rows and 3,100 strict feature rows.
- Task646 defines a high-throughput Alpaca SIP raw microstructure lane with a bounded worker runner and a shared limiter set to 150 requests/minute by default. The blocker is coverage completion and feature permission, not MCP access.

### Necessity Matrix

| Candidate | Need Now? | Speed / Cadence View | Existing-Baseline Comparison | Decision |
| --- | --- | --- | --- | --- |
| OpenBB ODP | Partial | It does not host data; speed depends on underlying provider. It standardizes connectors, not quotas. | Useful only if it reduces custom connector code and improves provider interchange. It does not fix Task2251 entitlement/rate blocks. | `PILOT_ONLY_FOR_CONNECTOR_ABSTRACTION` |
| Alpha Vantage MCP | Mostly no | Official free service is up to 25 requests/day; quote endpoint is one ticker/request. Bulk quotes are premium and can accept up to 100 symbols/request. | Too slow for 3,100-symbol backfill on free tier. Better for spot checks or paid premium quote sampling only. | `DO_NOT_USE_FOR_FULL_POOL_FREE_TIER` |
| Financial Datasets MCP | Unknown/paid-dependent | Public page advertises broad coverage, but rate limit is subscription-dependent. | Could help if paid plan covers statements/news with raw retention and PIT fields. Cannot assume better than SEC/Finnhub/FMP lanes without trial. | `TRIAL_ONLY_IF_PLAN_LIMITS_DISCLOSED` |
| GitHub MCP read-only | Yes, but low-frequency | GitHub REST limit is high enough for repo monitoring when authenticated, but search/secondary limits require batching. | Adds governance value, not market-data value. Useful for weekly/daily upstream watch of MCP/security/framework changes. | `KEEP_READ_ONLY_MONITOR` |
| NautilusTrader | Not now | Local engine; speed not API-bound. Integration/migration cost is high. | Existing blocker is strict source/as-of and same-experiment replay governance, not event-engine throughput. | `REFERENCE_ONLY` |
| vectorbt | Later | Fast local vectorized diagnostics. | Useful only after canonical artifacts exist. It can cross-check results but cannot improve source completeness. | `DEFER_DIAGNOSTIC_MIRROR` |
| Qlib | Not now | Heavy ML pipeline; local speed depends on dataset/model. | Current problem is source truth and decision governance, not lack of model complexity. | `REFERENCE_ONLY` |
| Yahoo Finance MCP / MaverickMCP | No | Convenience wrappers; reliability/rate/legal status are weaker for governed evidence. | Adds source-truth risk. Existing raw-source discipline is stricter. | `DO_NOT_ATTACH_TO_GOVERNED_BRAIN` |

### Tool-by-Tool Verdict

#### OpenBB

Use only if the goal is connector maintainability.

Need:

- Medium.
- It can reduce custom provider glue and make source adapters easier to swap.

Not a speed win:

- OpenBB documentation says provider extensions expand coverage and can be inserted or removed independently, but many providers still require API keys and provider availability varies by subscription.
- OpenBB says its Workspace does not provide financial data; the main value is connecting an organization's own datasets.

Decision:

- Do not make it a hot path.
- Run a tiny connector-abstraction pilot only.
- Success metric: less adapter code, same raw payload retention, same timestamp/hash discipline.

#### Alpha Vantage MCP

Do not use for full-pool collection on the free tier.

Need:

- Low for full universe.
- Medium only for paid premium spot quote/news experiments.

Call math:

- 3,100 symbols at one ticker per quote request is 3,100 calls.
- At 25 requests/day, this is at least 124 days before retries.
- Endpoints that allow 5 symbols/request on free keys still need about 620 calls, or about 25 days.
- Premium bulk quotes can reduce quote-only calls to about 31 at 100 symbols/request, but that is a premium quote lane, not proof of full PIT source readiness.

Decision:

- Do not attach as a production source path now.
- If tested, test only 10-symbol receipt capture and provider metadata.

#### Financial Datasets MCP

Use only after plan limits are known.

Need:

- Unknown.
- Potentially useful if it provides paid, stable statement/news data with historical coverage and retained raw payloads.

Risk:

- Rate limits and terms are subscription-dependent.
- Without plan details, it cannot be judged better than current SEC/Finnhub/FMP fallback stack.

Decision:

- No integration until rate limit, historical depth, redistribution/retention terms, and timestamp fields are documented.

#### GitHub MCP Read-Only

This is the cleanest "yes," but not for trading data.

Need:

- High for governance monitoring.
- Low for market data.

Cadence:

- Weekly is enough for quant frameworks.
- Daily is enough for MCP/server security watch.
- Intraday is unnecessary.

Decision:

- Use read-only, scoped to context/issues/pull_requests/security/release monitoring.
- It should produce review packets only.

#### NautilusTrader / vectorbt

Use only after canonical inputs exist.

Need:

- Low now.
- Medium later for independent replay/result sanity checks.

Reason:

- They do not solve source gaps.
- They can create false confidence if used before strict raw/as-of and experiment-class blockers are resolved.

Decision:

- Keep as architecture/reference tools.
- Do not migrate the harness.

### Adoption Rules

Adopt an external tool only if it passes all four tests:

1. It improves one named blocker versus the existing repo path.
2. It preserves raw payload, timestamp, provider, hash, and terms metadata.
3. Its call budget can cover the intended universe within the required cadence.
4. It does not write buy/sell/rank/size/selector/order fields.

If any answer is no, keep it out of the governed brain.

### Recommended Practical Plan

1. Do not attach Alpha Vantage MCP as a full-pool source.
2. Do not attach Yahoo/Maverick MCP to governed evidence.
3. Use GitHub MCP read-only for low-frequency upstream monitoring.
4. Run OpenBB only as a connector-abstraction pilot, not a speed upgrade.
5. Consider Financial Datasets only if a paid plan's exact limits and retention terms are acceptable.
6. Defer vectorbt/NautilusTrader until canonical replay artifacts are ready for diagnostic mirroring.

## No-Background Decision-Maker Report

Conclusion first: most tools should not be attached now.

The best immediate "yes" is GitHub MCP read-only, because it helps monitor repos and security without touching trading decisions.

OpenBB is a maybe. It may reduce adapter complexity, but it will not magically improve API speed because it depends on the underlying providers.

Alpha Vantage MCP is not suitable for the 3,100-symbol pool on the free tier. The free call budget is too small.

Financial Datasets MCP is undecided until exact plan limits and raw-retention terms are known.

NautilusTrader and vectorbt should stay as later diagnostic mirrors, not current engine replacements.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `docs/operating_system/project_operating_state.md`
  - `docs/reports/task_2251_2280_plus8000_full_source_acquisition/task_2251_2280_plus8000_full_source_acquisition.md`
  - `docs/reports/task_2561_2580_liquidity_rates_regime_acquisition/task_2561_2580_liquidity_rates_regime_acquisition.md`
  - `docs/reports/task_646_full_microstructure_data_lake/task_646_full_microstructure_data_lake.md`
  - `docs/reports/task_3082_external_tool_layer_utilization_plan/task_3082_external_tool_layer_utilization_plan.md`
  - Alpha Vantage support/API docs
  - OpenBB provider/pricing docs
  - GitHub REST API rate-limit docs
- Outputs:
  - `docs/reports/task_3121_external_tool_necessity_cost_benefit_review/task_3121_external_tool_necessity_cost_benefit_review.md`
- Row counts:
  - Necessity matrix rows: 8.
- Validation commands:
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Not applicable. No external raw datasets were acquired.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
