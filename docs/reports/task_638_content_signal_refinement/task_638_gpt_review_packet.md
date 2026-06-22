# Task638 GPT Review Packet

Use only supplied facts. GPT is review-only, not source truth.

## Result

- Highest-return 50bp final: $6660.26
- Highest-return max drawdown: -53.67%
- Risk-controlled 50bp final: $5618.37
- Risk-controlled max drawdown: -30.04%
- Prior Task637 best: $5148.31
- Highest-return universe/timing/exit/sizing: `refined_best_combo` / `immediate` / `hold10` / `dynamic_10_20_30`
- Risk-controlled universe/timing/exit/sizing: `refined_best_combo` / `immediate` / `hold10` / `equal_max5`
- Same risk-controlled rule validation: $863.73 vs QQQ $1020.64
- Same risk-controlled rule recent OOS: $1374.52 vs QQQ $1140.89

## Top Candidates

- refined_best_combo | immediate | hold10 | dynamic_10_20_30 | final $6660.26 | accepted 248
- refined_best_combo | vwap_reclaim | hold10 | dynamic_10_20_30 | final $6660.26 | accepted 248
- refined_best_combo | delay15m | hold10 | dynamic_10_20_30 | final $6354.41 | accepted 248
- refined_best_combo | delay30m | hold10 | dynamic_10_20_30 | final $6116.76 | accepted 248
- positive_backlog_order | immediate | existing_exit | dynamic_10_20_40 | final $5939.81 | accepted 57
- positive_high_quality | vwap_reclaim | existing_exit | dynamic_10_20_40 | final $5939.81 | accepted 57
- positive_high_quality | immediate | existing_exit | dynamic_10_20_40 | final $5939.81 | accepted 57
- positive_backlog_order | vwap_reclaim | existing_exit | dynamic_10_20_40 | final $5939.81 | accepted 57

## Review Questions

1. Is the winning candidate economically plausible, or does it look like timing/exit curve-fit?
2. Should the negative-event branch be traded as post-shock reversal rather than bad-news long?
3. Which live-readable subtype rules should be locked first?
4. Which extra blocker should prevent paper-runtime assignment?
5. What validation should come before any real-time trade decision use?