# Task660 GPT Review Packet

GPT role: external review-only critic.

Requested reviewers:

- Professional equity trader / PM.
- Professional economist / macro strategist.

Sanitized project facts supplied:

- Task639 baseline: `$1,000 -> $7,639.62`, max drawdown `-23.76%`.
- Task639 entry logic: `positive_contract_customer OR content_supply_demand`.
- Task659 theme-specific relation engine: fixed theme macro exposure matrix, driver-level conflict flags, theme-specific relation states, soft wrappers only.
- Best Task659 candidate: `theme_conflict_hold5`, `$1,000 -> $8,308.82`, max drawdown `-21.97%`.
- Task659 is `NOT_ACCEPTED` because validation and recent OOS did not show distinct improvement over Task639.
- Current implementation has rates/oil/dollar/credit/liquidity exposure by theme, but relation states are still mechanical and sparse-cell handling is simple.

Institutional report patterns supplied:

- BlackRock: AI capex is macro-scale; front-loaded investment and back-loaded revenue create financing pressure; energy and bond-yield shocks matter.
- Morgan Stanley: themes come from macro plus industry analysis; AI diffusion, future of energy, multipolar world, and societal shifts affect stocks differently.
- J.P. Morgan: AI, fragmentation, and inflation interact; infrastructure and innovation-linked sectors need portfolio resilience.
- Guggenheim: capex broadens across sectors; financing complexity and credit spread pressure matter.

Questions asked:

1. Professional trader critique: what is missing before this is tradable?
2. Professional economist critique: what macro transmission logic is shallow?
3. Compare the engine to institutional report standards.
4. What concrete upgrades should be coded with current data only?
5. What should be promoted and what should remain research-only?
6. Give artifacts and pass/fail criteria for Task660/661.

Redactions:

- No broker credentials.
- No API keys.
- No private user data.
- No raw account data beyond already reported synthetic `$1,000` backtest metrics.
