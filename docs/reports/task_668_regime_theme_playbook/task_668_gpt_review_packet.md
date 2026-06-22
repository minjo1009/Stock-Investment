# Task668 GPT Review Packet

- captured_via: Chrome ChatGPT
- tab: 1. 코딩/투자
- source_type: external_model_interpretation
- use_rule: GPT output is review input only. Local backtest gates decide acceptance.

## Supplied Facts

- Task639 baseline: $7,639.62, MDD -23.76%.
- Active relation cap3 reference: $10,887.47, MDD -30.52%.
- relation_priority_playbook_lite_sizing: $10,183.62, MDD -28.61%.
- playbook_priority_only: $7,585.47, MDD -27.39%.
- playbook_dynamic_cap: $5,173.94, MDD -18.76%.
- playbook_contextual_sizing: $4,516.13, MDD -20.89%.
- No candidate passed promotion because none beat Task639 return and Task639 MDD together with validation/recent OOS.

## Playbook Performance Facts

Under active relation cap3, all-period accepted trades:

- normal_participation: 20 trades, avg +23.64%, entry-reduce fail 30%.
- confirmation_required: 12 trades, avg +67.24%, entry-reduce fail 25%.
- rotation_selective: 7 trades, avg +16.28%, fail 42.9%.
- research_only_sparse: 5 trades, avg +7.34%, fail 40%.
- defensive_research_only: 5 trades, avg +2.15%, fail 60%.
- narrow_leader_selective: 2 trades, avg +148.81%, fail 0%.

## Review Questions

1. Interpret Task668 results.
2. Is the market/theme/playbook view directionally validated?
3. What is missing from classification?
4. What should Task669 do next without overfitting?
5. What must remain forbidden?

