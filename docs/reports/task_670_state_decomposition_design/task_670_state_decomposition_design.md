# Task670 State Decomposition Design

## Decision Summary

- Verdict: `STATE_DECOMPOSITION_DESIGN_READY_IMPLEMENTATION_REQUIRED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

The six-layer proposal is not sufficient. It is a useful skeleton, but firm-grade decomposition requires separate source, macro, liquidity, factor, theme, catalyst, price/flow, crowding, microstructure, and portfolio-capacity axes.

## Quant Expert Report

Task669 showed that Task668 playbook states are compressed. `normal_participation`, `confirmation_required`, and `rotation_selective` mix market state, theme state, relation state, catalyst quality, and price acceptance.

The next step cannot be another wrapper. Task670 must first preserve the separate axes that were previously collapsed into action-style names.

### Core Implementable Axes

1. `source_integrity_state`
2. `market_macro_state`
3. `liquidity_credit_state`
4. `theme_leadership_state`
5. `rotation_participation_state`
6. `company_catalyst_quality_state`
7. `price_acceptance_state`
8. `portfolio_capacity_state`

### Diagnostic-Only Axes

9. `factor_exposure_state`
10. `microstructure_state`
11. `crowding_risk_state`

### Why Six Layers Are Not Enough

Six layers miss three important distinctions:

- liquidity/credit pressure can break high-growth or high-beta trades even when broad market state is mixed;
- portfolio capacity and displacement risk matter because the strategy has max5 slots;
- microstructure/crowding/factor exposure cannot be hidden inside price acceptance.

### Required Implementation Artifacts

- `task670_state_axis_panel.csv`
- `task670_state_purity_report.csv`
- `task670_state_cross_tab_matrix.csv`
- `task670_sparse_cell_report.csv`
- `task670_mdd_axis_exposure_report.csv`
- `task670_capacity_context_report.csv`
- `task670_axis_definition.md`

## No-Background Decision-Maker Report

사장님 말이 맞습니다.

6개로는 부족합니다. 지금 문제는 상태가 너무 크게 뭉쳐 있다는 것입니다.

`confirmation_required` 같은 이름은 실제 상태가 아닙니다. 시장, 테마, catalyst, 가격 수용, 포트폴리오 슬롯 압박이 섞인 결과 이름입니다.

다음 단계는 매매룰 추가가 아니라 상태 분해입니다. 상태를 정확히 분해하지 않으면 MDD를 줄이면서 수익을 살리기 어렵습니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| gpt_review_completed | 1 | completed | external review of axis sufficiency |
| six_layer_design_rejected_as_complete | 1 | rejected_as_complete | six layers cannot be final firm-grade design |
| core_axes_defined | 1 | 8 | source market liquidity theme rotation catalyst price capacity |
| diagnostic_axes_defined | 1 | 3 | factor microstructure crowding |
| trading_action_allowed | 0 | design_only | no action mapping in Task670 |
| real_capital_allowed | 0 | forbidden | strategy remains not accepted |

## Artifact Manifest

- `task_670_gpt_review_packet.md`
- `task_670_gpt_review_response.md`
- `task_670_axis_definition.md`
- `task_670_state_decomposition_design.md`
- `task_670_decision.csv`
- `task_670_pass_fail_matrix.csv`

