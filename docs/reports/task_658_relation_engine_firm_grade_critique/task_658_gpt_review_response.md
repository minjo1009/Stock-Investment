# Task658 GPT Review Response Summary

GPT's review was blunt:

- Current logic is not a real relation engine. It is closer to a macro sentiment overlay.
- The main missing layer is not more data. The missing layer is macro exposure translation by industry/theme.
- Current code asks whether macro is pressure/supportive, but not who is exposed to that macro state.
- Macro pressure outperforming supportive should not be read as pressure being bullish. It may be selection effect: Task639 already selects strong company catalysts, and the few that survive macro pressure may be unusually strong.
- Macro pressure has only 53 rows, so it must not be rule-locked.
- Same macro variable must mean different things across themes.

Concrete examples GPT gave:

- Rates up: pressure for biotech and cloud/long-duration growth, mixed for semis, weak relevance for defense, possible support for financials.
- Oil up: supportive for energy, pressure for airlines/transport, mixed for defense.
- Dollar up: pressure for exporters/commodities, weaker effect for domestic services.
- Credit stress: more relevant for leveraged growth/biotech/crypto than for defense or cash-generative large semis.

Recommended minimal next design:

- Build a small `theme_macro_exposure_matrix.csv`.
- Keep taxonomy small at first: AI semis, cloud AI, aerospace/defense/space, biotech/healthcare, industrial automation, financials/crypto, energy or energy-sensitive, power grid/electrification, cybersecurity, software/devops, EV/mobility.
- Translate macro state through theme exposure before action logic.
- Create `theme_macro_company_state_panel.csv`.

Explicit "do not do" list:

- Do not treat macro_pressure as skip.
- Do not treat macro_supportive as full entry.
- Do not rule-lock 53 macro_pressure rows.
- Do not tune macro pressure/support thresholds globally.
- Do not use macro as standalone action.
- Do not create theme blacklists.
