# Task 489 - Broad Regime Intraday Cell Portfolio

## Quant Expert Report

- Goal achieved flag: 1
- Selected cells: 7
- Count / avg net / win / entry_reduce: 856 / 0.650% / 56.5% / 24.8%
- Validation count / avg net: 87 / 1.766%
- Recent OOS count / avg net: 264 / 0.911%
- Inferred lifecycle matching used: NO
- Label fields used in assignment: NO
- Acceptance: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY

## Selected Portfolio Quality

```csv
lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate,false_positive_rate
856,0.650388409915038,0.5654205607476636,0.39953271028037385,0.24766355140186916,0.514018691588785
```

## Split Quality

```csv
split_name,lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate,false_positive_rate
validation,87,1.7663917361751973,0.6551724137931034,0.45977011494252873,0.13793103448275862,0.42528735632183906
recent_oos,264,0.9105187198762589,0.625,0.49242424242424243,0.22348484848484848,0.4772727272727273
train_design,505,0.3221375362231641,0.5188118811881188,0.3405940594059406,0.27920792079207923,0.5485148514851486
```

## Selected Cells

```csv
cell_dims,cell_values,lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate,false_positive_rate,train_design_count,train_design_avg_net_pct,train_design_win_rate,train_design_entry_reduce_rate,validation_count,validation_avg_net_pct,validation_win_rate,validation_entry_reduce_rate,recent_oos_count,recent_oos_avg_net_pct,recent_oos_win_rate,recent_oos_entry_reduce_rate,candidate_cell_flag,selected_cell_order
broad_market_score|forward_live_breadth_positive_rate|forward_live_theme_return,"(np.int64(1), np.int64(3), np.int64(3))",244,0.6344257503490386,0.5737704918032787,0.4262295081967213,0.2459016393442623,0.4713114754098361,144,0.3571229158412453,0.5138888888888888,0.3125,47,1.4541710426313534,0.7021276595744681,0.06382978723404255,53,0.6609083811387263,0.6226415094339622,0.22641509433962265,1,1
broad_market_score|broad_market_stress|forward_live_theme_breadth_positive_rate,"(np.int64(1), np.int64(0), np.int64(2))",57,0.6333925272313573,0.631578947368421,0.49122807017543857,0.22807017543859648,0.49122807017543857,0,,,,0,,,,57,0.6333925272313573,0.631578947368421,0.22807017543859648,1,2
broad_market_score|broad_market_stress|payoff_theme_score,"(np.int64(1), np.int64(0), np.int64(4))",69,0.6243114201591292,0.5507246376811594,0.37681159420289856,0.30434782608695654,0.5942028985507246,0,,,,0,,,,69,0.6243114201591292,0.5507246376811594,0.30434782608695654,1,3
payoff_theme_score|forward_live_breadth_positive_rate|forward_live_theme_return,"(np.int64(1), np.int64(0), np.int64(2))",234,0.6206787217697598,0.5470085470085471,0.3717948717948718,0.26495726495726496,0.5341880341880342,162,0.22935195474026343,0.5123456790123457,0.2777777777777778,23,2.520494404115989,0.5652173913043478,0.2608695652173913,49,1.0227027128884367,0.6530612244897959,0.22448979591836735,1,4
forward_live_breadth_positive_rate|forward_live_theme_breadth_positive_rate|forward_live_theme_return,"(np.int64(1), np.int64(4), np.int64(1))",47,0.6182426343444593,0.6382978723404256,0.3617021276595745,0.19148936170212766,0.44680851063829785,34,0.59740538405741,0.6764705882352942,0.20588235294117646,7,0.02387715670726703,0.42857142857142855,0.2857142857142857,6,1.4297467765477947,0.6666666666666666,0.0,1,5
broad_market_score|forward_live_breadth_positive_rate|forward_live_theme_breadth_positive_rate,"(np.int64(0), np.int64(0), np.int64(1))",148,0.5963297931532366,0.5743243243243243,0.3716216216216216,0.25675675675675674,0.5743243243243243,92,0.46499519700439246,0.5434782608695652,0.2826086956521739,8,3.315321604277002,0.875,0.125,48,0.3948891339178938,0.5833333333333334,0.22916666666666666,1,6
broad_market_stress|payoff_theme_stress_score|forward_live_breadth_positive_rate,"(np.int64(4), np.int64(1), np.int64(2))",90,0.5786533204646275,0.4888888888888889,0.3888888888888889,0.23333333333333334,0.5333333333333333,75,0.14024077481954728,0.44,0.24,2,0.33447890886700493,0.5,0.0,13,3.1455217625089555,0.7692307692307693,0.23076923076923078,1,7
```

## No-Background Decision-Maker Report

이번 결과는 broad-market 500개 일봉 regime과 당일 market/theme participation을 결합하면 기존 목표 지표를 충족하는 regime-only 포트폴리오가 나온다는 뜻이다. 단, IEX 기반 diagnostic 데이터이고 cell portfolio 탐색 결과이므로 실전 승인 전에는 SIP급 데이터와 더 긴 OOS 검증이 필요하다.