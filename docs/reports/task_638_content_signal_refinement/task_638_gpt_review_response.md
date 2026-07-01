Bottom-line Recommendation

[promotion_blocker] refined_best_combo / hold10 / dynamic_10_20_30은 현재 기준으로 rule-lock 후보가 아니다.

[interpretation] 이유는 수익 개선 자체는 확인됐지만, 동일 규칙이 validation-only에서 QQQ를 이기지 못했고, 최대 낙폭이 -53.67%로 매우 큼.

[interpretation] Task639의 우선순위는 "더 높은 수익"이 아니라 "동일 규칙 안정성"이다.

[interpretation] 현재 가장 가치 있는 자산은 이미 확인된 stable feature들: content_negative_score, content_guidance_margin, content_supply_demand.

[interpretation] 특히 same-rule pass 후보군을 중심으로 발전시키는 것이 firm-grade에 더 가깝다.

Why Current Best Is Not Enough
[interpretation] 1. Train-like optimization 흔적. full-period는 매우 좋지만 validation-only 실패라 full-period 적합 가능성이 있다.
[interpretation] 2. Drawdown 비용이 너무 큼. 최고 수익 후보는 final $6,660.26, DD -53.67%라 firm-grade 승격 불가.
[interpretation] 3. Dynamic sizing이 edge인지 불명. signal edge인지 sizing amplification인지 분리 안 됨.
[promotion_blocker] 현재는 alpha 증명보다 position sizing 증폭 가능성을 먼저 배제해야 함.

Refined Best Combo
[interpretation] 완전히 버릴 필요는 없지만 rule-lock은 금지.
[interpretation] same-rule validation PASS and same-rule recent PASS 후보군 우선: content_negative_score, positive_contract_customer, content_supply_demand.

Regime Switching
[inference] 지금 단계에서는 NO. 현재 확보 사실은 feature stability이지 regime classification edge가 아님.
[promotion_blocker] Regime switch를 넣으면 새 모델이 된다. 기존 alpha 검증도 안 끝남.

Drawdown Reduction
[interpretation] 가장 유망한 방향은 entry 감소가 아니라 position risk 관리.
[interpretation] Signal Confidence Tier, Drawdown Throttle, Hold Window 단축을 테스트.

Task639 Recommendation
[interpretation] Task639 = OOS-first Rule Lock Study.
[interpretation] Experiment 1: Same-rule pass candidates only: content_negative_score, positive_contract_customer, content_supply_demand.
[interpretation] Experiment 2: Overlay sizing study: signal fixed, equal_max5 vs dynamic compare to separate alpha vs sizing.
[interpretation] Experiment 3: Hold window study: existing_exit, hold5, hold10 only.
[promotion_blocker] Regime switch, new semantic score, full-period-only optimization reject.

Most Economically Plausible Candidate
[interpretation] positive_contract_customer is most plausible because contract/customer/demand has clear economic linkage.
[interpretation] Next: content_supply_demand, then content_guidance_margin.
[source_gap] Causal hierarchy requires repo validation.

Promotion Blockers
[promotion_blocker] Same rule must pass validation and recent OOS.
[promotion_blocker] 50bp account robustness not enough yet.
[promotion_blocker] highest-return candidate DD -53.67% unresolved.
[promotion_blocker] alpha and sizing effect not separated.
[promotion_blocker] Strategy NOT_ACCEPTED, Real Capital FORBIDDEN.
