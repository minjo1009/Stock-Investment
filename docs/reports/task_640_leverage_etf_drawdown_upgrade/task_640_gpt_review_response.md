Bottom line

Task641 should not chase the MDB exclusion. Treat it as an overfit suspect until there is a pre-entry causal rule that would have excluded MDB before seeing returns.

Next tests should focus on execution-time quality filters and risk-normalized sizing, not new symbols/themes or after-the-fact exclusions.

What to test next
1. Entry quality confirmation

Test only rules observable before or at entry:

next-day entry allowed only if price holds above VWAP / opening range

reject if early gap fades before entry

reject if relative strength vs QQQ/theme proxy is negative at entry

require volume confirmation on entry day

Goal:

same Task639 signal
+ better entry tape
= fewer drawdown trades
2. Volatility / ATR-based position sizing

Equal max5 is simple but may over-size high-volatility names.

Test:

equal max5 baseline

ATR-normalized sizing

max position cap by realized volatility bucket

lower size for high-gap / high-ATR entries

This is better than drawdown throttle because it is pre-trade risk control, not after-loss reaction.

3. Signal-strength tiering

Task639 uses:

positive_contract_customer OR content_supply_demand

Split into tiers:

Tier 1: both features present

Tier 2: only positive_contract_customer

Tier 3: only content_supply_demand

Then test:

Tier 1 full size

Tier 2 normal size

Tier 3 reduced size or confirmation required

This is economically cleaner than excluding one ticker.

What to avoid

Single-symbol exclusion like exclude MDB unless explained by a pre-entry, repeatable rule.

Excluding symbols because they hurt backtest.

Leveraged ETF overlays. Task640 already showed worse return/DD profile.

Simple realized drawdown throttle as primary fix. It did not improve Task639.

Any rule based on after-the-fact loss, return, or drawdown labels.

Dangerous overfitting

The MDB exclusion is dangerous because:

one ticker removed
→ return improves
→ no causal pre-entry rule yet

That is classic data-mining risk.

It becomes testable only if converted into a general rule, for example:

exclude trades with weak entry confirmation
exclude high-volatility gap failures
exclude low source-relevance signals
exclude poor liquidity/capacity bucket

Not:

exclude MDB
Task641 recommendation

Run three controlled experiments:

Task641-A: Entry Confirmation Gate

Task639 signal unchanged.

Add VWAP/opening-range/relative-strength confirmation.

Task641-B: Risk-Normalized Sizing

Task639 signal unchanged.

Replace equal max5 with ATR/volatility-adjusted max5.

Task641-C: Signal Tier Sizing

Same features only.

Size by feature strength, not ticker identity.

Promotion remains blocked until live-readable source rules, source latency, paper-shadow replay, and fresh-OOS validation pass.