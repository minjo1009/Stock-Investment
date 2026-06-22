# Task1151-1160 Official Universe Redefinition

## Decision Summary

- Verdict: `official_universe_basis_defined_replay_blocked_until_historical_listing_membership`.
- Custom 10x7 universe is no longer allowed as the selection universe.
- It may only be used as diagnostic theme labels after official universe membership.
- Official current SEC exchange universe rows: 10400.
- Seed panel rows: 63000.
- True historical listing PIT rows: 0.
- Replay executed: 0.
- Selection promoted: 0.

## Quant Expert Report

The target architecture changes from handpicked candidates to a broad official universe.

New rule:

1. Build an official as-of universe first.
2. Run L1-L5 features only inside that universe.
3. Select 3, 5, or 10 names from the ranked universe.
4. Theme labels are explanatory features, not candidate admission rules.

Source finding:

- SEC `company_tickers_exchange.json` is useful for current official identity and exchange mapping.
- Nasdaq Trader symbol directory is official but current-day only.
- SEC bulk submissions can support public-filer as-of membership through filing acceptance times, but it is not a pure exchange-listing feed.
- A true official historical listed universe likely requires exchange/vendor historical listing data.

Leakage decision:

- No current snapshot is promoted into historical membership.
- No replay was executed.

## No-Background Decision-Maker Report

We changed the game board.

Before: the model picked from a handpicked 70-stock theme basket.

After: the model must pick from an official market universe first. The theme basket can explain ideas, but it cannot decide who is eligible.

This fixes the biggest conceptual flaw. It does not yet produce a valid historical backtest because the true 2021-2026 historical listing feed is not built yet.

## Artifact Manifest

- `data/artifacts/task_1151_1160_official_universe_redefinition/task1151_universe_basis_decision.csv`
- `data/artifacts/task_1151_1160_official_universe_redefinition/task1152_official_source_feasibility.csv`
- `data/artifacts/task_1151_1160_official_universe_redefinition/task1153_current_sec_exchange_universe.csv`
- `data/artifacts/task_1151_1160_official_universe_redefinition/task1154_historical_asof_universe_contract.csv`
- `data/artifacts/task_1151_1160_official_universe_redefinition/task1155_decision_calendar.csv`
- `data/artifacts/task_1151_1160_official_universe_redefinition/task1156_official_universe_seed_panel.csv`
- `data/artifacts/task_1151_1160_official_universe_redefinition/task1157_theme_label_policy.csv`
- `data/artifacts/task_1151_1160_official_universe_redefinition/task1158_selection_policy_contract.csv`
- `data/artifacts/task_1151_1160_official_universe_redefinition/task1159_official_universe_replay_gate.csv`
- `data/artifacts/task_1151_1160_official_universe_redefinition/task1160_official_universe_redefinition_closeout.csv`
- `data/artifacts/task_1151_1160_official_universe_redefinition/task1160_official_universe_redefinition_closeout.json`
