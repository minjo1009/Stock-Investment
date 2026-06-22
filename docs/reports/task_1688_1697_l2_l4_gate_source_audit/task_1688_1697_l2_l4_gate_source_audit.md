# Task1688-1697 L2/L3/L4 Gate Source Audit

## Decision Summary

- Verdict: `direction_validated_review_only_not_implemented`.
- Reviewed direction: strengthen bad-trade prevention plus top3 payoff concentration through L2/L3/L4 before another L5-only tightening pass.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: external source context and review-only expert roles confirm that the next bottleneck is not another blanket MDD toggle. The next implementation should build pre-entry downside filters, payoff-quality compression, and thesis-break rules that L5 can use.
- Next action: implement Task1698-1717 as a source-time-safe L2/L3/L4 candidate-quality and collapse-risk gate, then replay top3/top5 against Task1668-1687.

## Quant Expert Report

### Source Basis

| Source | Local status | Use in next design |
| --- | --- | --- |
| SEC Form 8-K | reused existing official raw after direct 403 | Material event taxonomy; event type before score. |
| MacKinlay event-study paper | downloaded | Abnormal-return and event-window framing; avoid treating news existence as alpha. |
| Kenneth French Data Library | downloaded | Factor, size, value, profitability, investment, momentum context. |
| Fama-French archive page | downloaded | PIT/vintage caution for factor files and monthly reconstruction. |
| AQR Value and Momentum Everywhere | downloaded | Momentum and value as broad market acceptance context, not single-name proof. |
| Campbell-Hilscher-Szilagyi distress risk | downloaded | Failure/delisting risk primitives: leverage, profitability, size, volatility, cash, price. |
| Investor.gov microcap risk | downloaded | Microcap liquidity, no revenue, unproven business, manipulation risk flags. |
| Nasdaq continued listing guide | downloaded | Listing compliance and minimum bid/market-value warning states. |
| Bailey et al. backtest overfitting | downloaded | Policy-freeze and trial-count discipline before claiming improvement. |
| Harvey-Liu-Zhu backtesting | downloaded | Multiple-testing haircut and selection-bias caution. |

Source download manifest:

- `data/raw/task_1688_1697_l2_l4_gate_source_audit/source_download_manifest.csv`

### Review-Only Expert Verdict

| Role | Verdict | Reason |
| --- | --- | --- |
| Quant PM | Approve direction | MDD cannot be solved only by later exits; entry quality and payoff concentration must improve. |
| Goldman-style risk trader | Approve with guardrail | Risk veto must distinguish terminal damage from ordinary volatility. |
| Bank of America-style portfolio strategist | Approve | Top3 needs expected payoff and factor regime context, not only source count. |
| Event-study quant | Approve | Candidate promotion needs abnormal-return and event-window interpretation. |
| Distress-risk researcher | Strong approve | Collapse-risk primitives belong before ranking, not after large drawdown. |
| Microcap/liquidity analyst | Strong approve | Small-cap materiality can be a trap unless liquidity, dilution, and listing risk are checked. |
| Semiconductor/AI theme analyst | Conditional approve | Do not overfilter high-volatility winners; separate theme-valid volatility from financing distress. |
| Macro/factor strategist | Approve | Market/sector regime should modulate selection and hold, not replace thesis. |
| Backend/data engineer | Approve with strict contract | Features must be row-level, deterministic, source-time-safe, and auditable. |
| Research governance reviewer | Approve review-only | No acceptance/deployment wording may follow from this audit. |

### Current Bottleneck Interpretation

1. L5 thesis-aware action improved MDD from `-27.93%` to `-25.39%` and final equity from `2485.18` to `2740.12`.
2. CAGR is still only `21.57%`, so further exit tightening alone is likely to trade away upside.
3. The next bottleneck is earlier: the top3 still admits trades whose downside risk or payoff quality should have been visible before entry.
4. Therefore L2/L3/L4 should produce better candidates, while L5 should mostly police thesis breaks rather than constantly optimize exits.

### Professional Logic Gaps To Close

| Gap | Current weakness | Required primitive |
| --- | --- | --- |
| Bad candidate prevention | L5 reacts after drawdown appears. | Pre-entry collapse-risk state from accounting, market, liquidity, dilution, and listing signals. |
| Payoff concentration | Top3 has signal, but not enough CAGR. | L4 rank must prioritize magnitude, timing, expectation gap, and confirmation. |
| Volatility vs terminal damage | Risk controls can cut winners. | L2 classify `theme_volatility`, `liquidity_noise`, `financing_stress`, `listing_failure`, `thesis_invalidated`. |
| Market acceptance | Prior absorption proxy is too easy. | Sustained relative strength plus volume quality plus drawdown recovery, not one bounce. |
| Source independence | Issuer evidence can be too promotional. | Separate issuer, customer, regulator, analyst, and market confirmation. |
| Overfit risk | Many replay attempts have happened. | Freeze one policy family, log attempt count, compare to Task1668 baseline and QQQ. |

## No-Background Decision-Maker Report

1. The proposed direction is right.
2. But it must not become "more filters."
3. The correct next brain upgrade is:
   - avoid obvious bad trades before buying,
   - keep high-volatility winners alive,
   - push only real payoff candidates into top3,
   - sell only when the original thesis breaks.
4. This is L2/L3/L4 first, L5 second.
5. No capital/deployment status changes.

## Implementation Contract For Next Work

Task1698-1717 should implement one frozen family:

1. `L2 collapse_risk_v2`
   - Uses prior-known accounting/price/liquidity/listing/dilution signals.
   - Must separate `ordinary_volatility`, `theme_volatility`, `financing_stress`, `dilution_pressure`, `listing_compliance_risk`, `terminal_business_risk`.
2. `L2 payoff_quality_v2`
   - Uses event type, expectation gap, scale denominator, source independence, and market confirmation.
   - Good words without surprise do not pass as payoff.
3. `L3 risk_payoff_mechanism_edges`
   - Edges must state why a fact increases payoff, reduces payoff, invalidates thesis, or routes to smaller size.
4. `L4 top3 candidate compressor`
   - Candidate rank must demote terminal-risk names unless payoff confirmation is strong.
   - Candidate rank must avoid replacing proven winners with source-rich but economically weak names.
5. `L5 thesis-break-only action`
   - Starts from Task1668 no-rerisk leader.
   - L5 exits only on source/time-safe thesis break, not isolated price noise.
6. Validation
   - No future outcomes in assignment.
   - No missing labels as negatives.
   - No symbol/date/price/time fallback matching.
   - Compare against Task1668-1687, Task1518-1537, QQQ, and scheduled-only where available.

## Artifact Manifest

- `data/raw/task_1688_1697_l2_l4_gate_source_audit/source_download_manifest.csv`
- `data/artifacts/task_1688_1697_l2_l4_gate_source_audit/task1688_expert_source_review.csv`
- `data/artifacts/task_1688_1697_l2_l4_gate_source_audit/task1689_development_contract.csv`
- `data/artifacts/task_1688_1697_l2_l4_gate_source_audit/task1697_closeout.csv`
- `data/artifacts/task_1688_1697_l2_l4_gate_source_audit/task1697_closeout.json`
- `docs/reports/task_1688_1697_l2_l4_gate_source_audit/task_1688_1697_decision.csv`

Validation command:

- `powershell -NoProfile -Command "Import-Csv data/raw/task_1688_1697_l2_l4_gate_source_audit/source_download_manifest.csv | Where-Object { $_.status -match 'failed' }; Test-Path docs/reports/task_1688_1697_l2_l4_gate_source_audit/task_1688_1697_l2_l4_gate_source_audit.md"`

Validation authority:

- `GOVERNANCE_HEALTH` for report/registry/source-manifest presence only.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
