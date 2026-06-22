# Task660 Institutional Relation Engine Review

## Decision Summary

- Verdict: `INSTITUTIONAL_REVIEW_FINDS_DIRECTION_VALID_ENGINE_STILL_BELOW_FIRM_GRADE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Task639 baseline: `$1,000 -> $7,639.62`, max drawdown `-23.76%`.
- Task659 best full-period candidate: `theme_conflict_hold5`, `$1,000 -> $8,308.82`, max drawdown `-21.97%`.
- Promotion status: 0 candidates promoted.

Task659 is moving in the right direction, but it is not yet firm-grade.

The important finding is simple:

Task659 reached `macro -> theme`.

Institutional-grade work requires `macro -> economic transmission -> company catalyst quality -> price acceptance -> action`.

## Quant Expert Report

### Data Source And Source Readiness

This is a diagnostic review task, not a new trading backtest.

Inputs:

- Task639 baseline metrics.
- Task659 theme-specific relation engine outputs.
- Chrome ChatGPT review-only critique.
- Public institutional research/outlook pages from BlackRock, Morgan Stanley, J.P. Morgan Wealth Management, and Guggenheim Investments.

Institutional sources reviewed:

- BlackRock Investment Institute, Q2 2026 Investment Outlook: https://www.blackrock.com/us/individual/insights/blackrock-investment-institute/outlook
- Morgan Stanley, Investment Outlook 2026: https://www.morganstanley.com/insights/articles/investment-outlook-shaping-markets-2026
- Morgan Stanley, Mega Themes Converge to Outperform Markets: https://www.morganstanley.com/insights/articles/thematic-investing-megatrends-reshaping-global-markets-2026
- J.P. Morgan Wealth Management, Outlook 2026: https://www.chase.com/personal/investments/outlook
- Guggenheim Investments, 2026 Macro Themes: https://www.guggenheiminvestments.com/GuggenheimInvestments/media/PDF/2026-Macro-Themes.pdf

### Exact Join Keys

No new row-level trading join was performed in Task660.

Task661 must use existing deterministic keys:

- `entry_id`
- `lifecycle_id`
- `symbol`
- `entry_ts_et`
- `theme_id`
- `split_name`

### Leakage Audit

No strategy parameter was changed in Task660.

GPT output was used only as an external critique.

Institutional reports were used only to define comparison standards, not to create historical labels.

Task661 must not tune the economic exposure template from returns.

### Institutional Comparison

The institutional pattern is not "macro good, buy" or "macro bad, sell."

The institutional pattern is:

1. Identify macro force.
2. Translate it into an economic mechanism.
3. Identify which sectors/themes benefit or suffer.
4. Check whether the company catalyst is strong enough.
5. Check whether price accepts the narrative.
6. Size, delay, confirm, or reject based on evidence.

Task659 only covers the first two steps partially.

### Professional Trader Critique

The trader verdict is strict:

- Full-period improvement is not enough.
- Validation and recent OOS did not show distinct improvement over Task639.
- `theme_conflict_hold5` is a research candidate only.
- The engine must explain exactly which trades changed, why they changed, and how much money each change added or lost.
- Price acceptance must become a first-class state before any action promotion.

### Professional Economist Critique

The economist verdict is also strict:

- Rates, oil, dollar, credit, and liquidity are drivers, not explanations.
- The engine needs transmission paths such as:
  - rates pressure -> financing burden -> capex feasibility -> valuation duration risk.
  - credit stress -> financing availability -> capex delay risk -> equity sensitivity.
  - AI capex -> power demand -> infrastructure beneficiaries -> financing vulnerability.
  - fragmentation -> defense/localization support -> supply-chain pressure.
- Current logic says "conflict exists" better than it says "why this conflict should move this stock."

### Split/OOS Metrics

Task660 did not run a new account backtest.

The controlling evidence remains Task659:

| strategy | final capital | max drawdown | status |
| --- | ---: | ---: | --- |
| Task639 baseline | `$7,639.62` | `-23.76%` | accepted baseline for comparison only |
| Task659 `theme_conflict_hold5` | `$8,308.82` | `-21.97%` | full-period research candidate |

Task659 remains blocked because validation and recent OOS did not show distinct improvement.

### Failure Decomposition

Task660 identifies five main failure classes:

1. `oos_effect_missing`: full-period improvement did not translate into distinct validation/recent OOS improvement.
2. `mechanism_missing`: theme exposure exists, economic transmission is weak.
3. `catalyst_quality_flat`: contract/supply signals are not ranked deeply enough.
4. `price_acceptance_missing`: action is not gated by whether tape confirms the narrative.
5. `institutional_scenario_missing`: no bull/base/bear and invalidation logic per relation state.

### Remaining Blockers

- No strategy promotion.
- No real capital use.
- No macro hard block.
- No macro standalone entry.
- No size boost from relation states.
- Sparse cells cannot drive promotion.

## No-Background Decision-Maker Report

사장님, 방향은 맞습니다.

하지만 아직 돈 넣을 단계는 아닙니다.

지금 엔진은 "이 종목 테마가 금리/유가/달러/크레딧/유동성에 얼마나 민감한가"까지는 보기 시작했습니다.

기관은 거기서 멈추지 않습니다.

기관은 "그게 실제로 매출, 마진, 수주, 자금조달, 전력 비용, 고객 수요, 주가 수용으로 이어지는가"까지 봅니다.

그래서 다음 작업은 점수 하나 더 만드는 게 아닙니다.

다음 작업은 `경제 전달경로 엔진`입니다.

## Task661 Required Direction

Task661 must build:

- `institutional_transmission_template.csv`
- `theme_mechanism_state_panel.csv`
- `accepted_trade_attribution.csv`
- `oos_effect_audit.csv`
- `mechanism_soft_wrapper_grid.csv`
- `promotion_report.csv`

Task661 pass condition:

- Validation and recent OOS both improve Task639.
- Drawdown does not worsen.
- Sparse cells are not promoted.
- Macro never creates standalone entry, hard block, full-entry promotion, or size boost.
- Every changed trade has attribution.

## Artifact Manifest

- `task_660_institutional_source_review.csv`
- `task_660_gpt_review_packet.md`
- `task_660_gpt_trader_economist_response.md`
- `task_660_engine_vs_institutional_standard.csv`
- `task_660_professional_trader_critique.csv`
- `task_660_professional_economist_critique.csv`
- `task_660_task661_spec.csv`
- `task_660_pass_fail_matrix.csv`
- `task_660_decision.csv`
- `artifact_manifest.csv`

