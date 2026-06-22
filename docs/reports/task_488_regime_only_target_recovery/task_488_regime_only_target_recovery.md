# Task 488 - Regime Only Target Recovery Search

## Quant Expert Report

- Candidate rules tested: 14889
- Full-sample target passing rules: 6
- Selected rule: `payoff_market_score between 29.011935 and 49.644024; stress_sum between 118.220481 and 152.316095`
- Full-sample count / avg net / win / entry_reduce: 832 / 0.601% / 53.7% / 25.5%
- Validation avg net: 0.020%
- Recent OOS avg net: 0.183%
- Inferred lifecycle matching used: NO
- Label/outcome fields used in assignment: NO
- Strategy acceptance: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY

### Selected Candidate

```csv
candidate_name,candidate_rule,left_factor,left_low,left_high,right_factor,right_low,right_high,lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate,false_positive_rate,train_design_count,train_design_avg_net_pct,train_design_win_rate,train_design_entry_reduce_rate,validation_count,validation_avg_net_pct,validation_win_rate,validation_entry_reduce_rate,recent_oos_count,recent_oos_avg_net_pct,recent_oos_win_rate,recent_oos_entry_reduce_rate,target_count_pass,target_avg_net_pass,target_win_pass,target_entry_reduce_pass,all_targets_pass,diagnostic_only_flag,deployment_ready_flag
regime_only_grid_3269,payoff_market_score between 29.011935 and 49.644024; stress_sum between 118.220481 and 152.316095,payoff_market_score,29.011935,49.644024,stress_sum,118.220481,152.316095,832,0.6013937756061458,0.5372596153846154,0.38461538461538464,0.2548076923076923,0.5036057692307693,615,0.7882711642951157,0.5593495934959349,0.24390243902439024,148,0.01977245374500331,0.4594594594594595,0.28378378378378377,69,0.18328307403705346,0.5072463768115942,0.2898550724637681,1,1,1,1,1,1,0
```

### Split Quality

```csv
split_name,lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate,false_positive_rate
train_design,615,0.7882711642951157,0.5593495934959349,0.4,0.24390243902439024,0.4861788617886179
recent_oos,69,0.18328307403705346,0.5072463768115942,0.36231884057971014,0.2898550724637681,0.5362318840579711
validation,148,0.01977245374500331,0.4594594594594595,0.3310810810810811,0.28378378378378377,0.5608108108108109
```

### Quarterly Quality

```csv
quarter,lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate,false_positive_rate
2024Q1,125,1.8687525013978528,0.696,0.472,0.168,0.408
2025Q1,169,1.3195159806988068,0.6035502958579881,0.46745562130177515,0.2485207100591716,0.514792899408284
2025Q4,16,0.4666315193547118,0.625,0.3125,0.125,0.5
2024Q3,213,0.2903473769579134,0.5023474178403756,0.38028169014084506,0.2535211267605634,0.48826291079812206
2026Q1,69,0.18328307403705346,0.5072463768115942,0.36231884057971014,0.2898550724637681,0.5362318840579711
2024Q2,28,0.07966798899475391,0.5714285714285714,0.21428571428571427,0.14285714285714285,0.42857142857142855
2025Q3,202,-0.06676567569824954,0.4405940594059406,0.31683168316831684,0.297029702970297,0.5495049504950495
2024Q4,10,-2.6933307019590913,0.1,0.1,0.9,0.9
```

### Theme Quality

```csv
theme_id,lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate,false_positive_rate
ai_semiconductors,31,1.919247439834061,0.8387096774193549,0.6774193548387096,0.0967741935483871,0.2903225806451613
crypto_fintech,179,1.3213202002921385,0.5418994413407822,0.5083798882681564,0.26256983240223464,0.43575418994413406
cloud_ai_platforms,64,0.6430114588663236,0.640625,0.3125,0.203125,0.578125
data_devops_software,65,0.6352440603155259,0.5384615384615384,0.49230769230769234,0.2,0.47692307692307695
biotech_glp1_healthcare,7,0.5361105539634357,0.5714285714285714,0.2857142857142857,0.2857142857142857,0.42857142857142855
power_grid_electrification,138,0.510707148326808,0.5362318840579711,0.41304347826086957,0.35507246376811596,0.5434782608695652
aerospace_defense_space,154,0.2568921484332353,0.4935064935064935,0.2597402597402597,0.18831168831168832,0.5
ev_autonomy_mobility,160,0.10253203639824292,0.49375,0.33125,0.2875,0.5375
industrial_automation_robotics,17,-0.19209767364419236,0.47058823529411764,0.17647058823529413,0.11764705882352941,0.47058823529411764
cybersecurity,17,-0.295775238124623,0.4117647058823529,0.058823529411764705,0.47058823529411764,0.8823529411764706
```

## No-Background Decision-Maker Report

Regime-only 조건만으로 목표를 만족하는 후보는 발견됐다. 다만 이 후보는 연구용 진단 결과다. 전체 표본에서는 목표를 넘지만 validation 구간은 거의 flat이고, recent OOS 표본도 작다. 따라서 바로 실전 투입이 아니라 다음 단계에서 동일 규칙을 더 긴 기간/더 넓은 breadth source로 검증해야 한다.
