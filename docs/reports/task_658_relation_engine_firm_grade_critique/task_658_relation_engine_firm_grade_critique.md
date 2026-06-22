# Task658 Relation Engine Firm-Grade Critique

## Decision Summary

- Verdict: `RELATION_ENGINE_NOT_FIRM_GRADE_THEME_EXPOSURE_LAYER_REQUIRED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- What changed: no trading rule changed. This task locks the critique and Task659 implementation direction.
- Key finding: the current relation engine is not yet a relation engine. It is a global macro sentiment overlay.
- Next action: build a theme-specific macro exposure translation layer, then retest only soft permitted actions.

## Quant Expert Report

### Data Source And Source Readiness

Task655 made macro usable as pragmatic release-time context for all Task639 core rows. Task656 allowed macro only as a soft modifier. Task657 retested soft macro wrappers and found no candidate beating Task639.

Task657 evidence:

- Task639 baseline: $1000 to $7639.62, max drawdown -23.76 percent.
- Best non-baseline: `soft_pressure_hold10`, $7625.35, max drawdown -23.16 percent.
- Macro pressure did not behave like a simple bad state.

### Exact Join Keys

The current macro join is adequate for research tagging under Task656. The missing part is not a join key. The missing part is exposure translation:

`macro driver -> theme exposure -> company catalyst -> action permission`

### Leakage Audit

GPT was used only as review guidance and not as a market data source. Task658 does not create a new trading rule and does not use labels or future returns in assignment.

### Split/OOS Metrics

No new PnL strategy was promoted. Task657 showed that global soft wrappers did not beat Task639.

### Failure Decomposition

The current logic fails for six reasons:

1. It uses macro state without macro exposure.
2. It uses one global threshold across all themes.
3. It jumps from macro state to action before explaining the mechanism.
4. It does not respect sparse cells enough.
5. It tries risk control globally instead of where the theme is actually exposed.
6. It assumes supportive macro is bullish, which the data contradicts.

### Firm-Grade Example

The same macro state should not mean the same thing for every theme:

- Rates pressure can hurt biotech and software more than defense.
- Oil pressure can support energy but pressure transport and some consumer demand.
- Dollar strength can pressure exporters and commodities more than domestic demand themes.
- Credit stress matters more for funding-sensitive growth, biotech, fintech, and crypto.
- Defense/space and power-grid themes may be driven more by contracts, geopolitics, and capex durability than by broad macro pressure.

### Remaining Blockers

- No theme macro exposure matrix.
- No theme-translated macro state panel.
- No mechanism-level relation states such as duration pressure, funding stress, input cost pressure, or demand offset.
- No theme-specific soft wrapper grid.
- No promotion candidate over Task639.

## No-Background Decision-Maker Report

사장님, 쉽게 말하면 지금 엔진은 너무 둔합니다.

지금은 이렇게 봅니다:

`macro pressure = 조심`

그런데 실제로는 이렇게 봐야 합니다:

`macro pressure + 바이오 = 더 조심`

`macro pressure + 방산/우주 = 별 영향 없거나 오히려 강한 이벤트면 유지`

`rates pressure + 소프트웨어 = 조심`

`rates pressure + 반도체 = 회사/수요가 강하면 유지`

즉, macro 자체가 답이 아니라, macro가 이 산업군에 어떤 의미인지가 답입니다.

Task659는 이걸 구현해야 합니다.

## Artifact Manifest

- `task_658_gpt_review_packet.md`
- `task_658_gpt_review_response.md`
- `task_658_theme_macro_observation.csv`
- `task_658_current_logic_gap.csv`
- `task_658_minimal_theme_exposure_matrix_spec.csv`
- `task_658_task659_spec.csv`
- `task_658_decision.csv`
- `artifact_manifest.csv`
