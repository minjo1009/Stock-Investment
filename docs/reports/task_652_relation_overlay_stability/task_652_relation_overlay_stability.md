# Task652 Relation Overlay Stability

## Decision Summary

- Verdict: `NO_RELATION_OVERLAY_BEATS_TASK639_KEEP_BASELINE_DIAGNOSTIC_ONLY`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Baseline Task639-style final: $7639.62
- Baseline max drawdown: -23.76%
- Best tested candidate: `baseline_task639_core` = $7639.62
- Relation overlays did not beat the Task639 baseline after costs.

## Quant Expert Report

Task652 tests relation tags as baseline-preserving overlays. It rejects execution changes that do not beat Task639, improve drawdown, and survive validation plus recent OOS.

### Candidate Grid

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | return_used_in_assignment_flag | promotion_candidate_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639_core | all | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| chart_not_fragile_or_unconfirmed | all | 1000.0 | 1335 | 50 | 6229.593643357528 | 522.9593643357528 | -32.898667168151405 | 0.36 | 1582.803857306673 | 1 | 0 | 0 | 0 |
| chart_not_unconfirmed | all | 1000.0 | 1502 | 52 | 6143.13573398691 | 514.313573398691 | -32.78178416923156 | 0.34615384615384615 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| moderate_or_mixed_company | all | 1000.0 | 1367 | 53 | 5533.369175810348 | 453.3369175810348 | -26.335178488404452 | 0.33962264150943394 | 1624.8616697556758 | 1 | 0 | 0 | 0 |
| company_not_strong_label | all | 1000.0 | 1367 | 53 | 5533.369175810348 | 453.3369175810348 | -26.335178488404452 | 0.33962264150943394 | 1624.8616697556758 | 1 | 0 | 0 | 0 |
| confirmed_moderate_or_mixed | all | 1000.0 | 1113 | 49 | 4512.709646732255 | 351.27096467322554 | -26.637319774300117 | 0.2857142857142857 | 1624.8616697556758 | 1 | 0 | 0 | 0 |
| chart_confirmed_only | all | 1000.0 | 1320 | 50 | 3977.8601158709803 | 297.786011587098 | -36.187491521960524 | 0.38 | 1582.803857306673 | 1 | 0 | 0 | 0 |
| macro_known_mixed_supportive | all | 1000.0 | 256 | 42 | 2660.63824641992 | 166.063824641992 | -17.842685627654898 | 0.40476190476190477 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| macro_mixed_only | all | 1000.0 | 169 | 34 | 2372.063501858014 | 137.2063501858014 | -8.160119418380996 | 0.3235294117647059 | 1606.8278306897957 | 1 | 0 | 0 | 0 |

### Split Grid

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | return_used_in_assignment_flag | promotion_candidate_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639_core | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| chart_confirmed_only | recent_oos | 1000.0 | 284 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| chart_not_unconfirmed | recent_oos | 1000.0 | 310 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| chart_not_fragile_or_unconfirmed | recent_oos | 1000.0 | 284 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| company_not_strong_label | recent_oos | 1000.0 | 234 | 12 | 1462.1909350976098 | 46.21909350976099 | -8.755323786497227 | 0.4166666666666667 | 1138.0195487861092 | 1 | 0 | 0 | 0 |
| moderate_or_mixed_company | recent_oos | 1000.0 | 234 | 12 | 1462.1909350976098 | 46.21909350976099 | -8.755323786497227 | 0.4166666666666667 | 1138.0195487861092 | 1 | 0 | 0 | 0 |
| confirmed_moderate_or_mixed | recent_oos | 1000.0 | 196 | 12 | 1449.8961892444365 | 44.98961892444366 | -8.755323786497227 | 0.4166666666666667 | 1138.0195487861092 | 1 | 0 | 0 | 0 |
| macro_known_mixed_supportive | recent_oos | 1000.0 | 32 | 12 | 1057.1217710917078 | 5.71217710917078 | -11.312279072290277 | 0.75 | 1138.0195487861092 | 0 | 0 | 0 | 0 |
| macro_mixed_only | recent_oos | 1000.0 | 20 | 11 | 916.9500390302223 | -8.304996096977767 | -17.58567666968842 | 0.6363636363636364 | 1134.887143025 | 0 | 0 | 0 | 0 |
| macro_mixed_only | validation | 1000.0 | 71 | 11 | 1204.759103533044 | 20.475910353304407 | -4.633125664747406 | 0.18181818181818182 | 1108.6381890800562 | 1 | 0 | 0 | 0 |
| macro_known_mixed_supportive | validation | 1000.0 | 106 | 12 | 1198.8650172286152 | 19.886501722861528 | -7.493089299835387 | 0.25 | 1049.908329847512 | 1 | 0 | 0 | 0 |
| baseline_task639_core | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 | 0 |
| confirmed_moderate_or_mixed | validation | 1000.0 | 484 | 13 | 1056.881922148471 | 5.688192214847088 | -4.348611759219134 | 0.23076923076923078 | 1057.1357214245677 | 0 | 0 | 0 | 0 |
| company_not_strong_label | validation | 1000.0 | 582 | 16 | 1053.303144917822 | 5.3303144917822065 | -6.128889462477849 | 0.375 | 1057.1357214245677 | 0 | 0 | 0 | 0 |
| moderate_or_mixed_company | validation | 1000.0 | 582 | 16 | 1053.303144917822 | 5.3303144917822065 | -6.128889462477849 | 0.375 | 1057.1357214245677 | 0 | 0 | 0 | 0 |
| chart_confirmed_only | validation | 1000.0 | 539 | 12 | 978.7422499743697 | -2.125775002563035 | -8.053702470259527 | 0.4166666666666667 | 1049.908329847512 | 0 | 0 | 0 | 0 |
| chart_not_fragile_or_unconfirmed | validation | 1000.0 | 546 | 12 | 978.7422499743697 | -2.125775002563035 | -8.053702470259527 | 0.4166666666666667 | 1049.908329847512 | 0 | 0 | 0 | 0 |
| chart_not_unconfirmed | validation | 1000.0 | 622 | 15 | 869.55986611704 | -13.044013388296005 | -13.044013388296005 | 0.5333333333333333 | 1049.908329847512 | 0 | 0 | 0 | 0 |

### Tag Diagnostics

| tag_column | tag_value | row_count | avg_return_pct | win_rate | entry_reduce_failure_rate | large_loss_rate | evaluation_only_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chart_gate_state | chart_confirmed | 1320 | 6.305808738486807 | 0.568939393939394 | 0.3704545454545455 | 0.26666666666666666 | 1 |
| chart_gate_state | chart_fragile | 167 | 1.3586476964000338 | 0.437125748502994 | 0.47904191616766467 | 0.3473053892215569 | 1 |
| chart_gate_state | chart_unconfirmed | 119 | 0.8456003927411092 | 0.37815126050420167 | 0.5882352941176471 | 0.4957983193277311 | 1 |
| chart_gate_state | chart_failed | 15 | 48.09192376227089 | 0.8666666666666667 | 0.06666666666666667 | 0.06666666666666667 | 1 |
| company_gate_state | mixed_company_positive_conflict | 1210 | 6.260338374096108 | 0.5644628099173554 | 0.3768595041322314 | 0.28512396694214875 | 1 |
| company_gate_state | strong_company_positive | 254 | 1.7498809130509712 | 0.4330708661417323 | 0.47244094488188976 | 0.33070866141732286 | 1 |
| company_gate_state | moderate_company_positive | 157 | 8.618393749684127 | 0.5668789808917197 | 0.40764331210191085 | 0.2611464968152866 | 1 |
| macro_gate_state | macro_source_gap | 1363 | 4.900894872249564 | 0.5304475421863536 | 0.40425531914893614 | 0.293470286133529 | 1 |
| macro_gate_state | macro_mixed | 169 | 11.671364720750747 | 0.6627218934911243 | 0.28994082840236685 | 0.21301775147928995 | 1 |
| macro_gate_state | macro_supportive | 87 | 8.799707384950668 | 0.5402298850574713 | 0.4367816091954023 | 0.367816091954023 | 1 |
| macro_gate_state | macro_hostile | 2 | -22.69394395104736 | 0.0 | 1.0 | 1.0 | 1 |
| relation_state | sizing_modifier | 1413 | 6.258958320171555 | 0.5626326963906582 | 0.38145789101203115 | 0.283793347487615 | 1 |
| relation_state | reinforcing | 206 | 1.8886608028977883 | 0.41262135922330095 | 0.49029126213592233 | 0.33495145631067963 | 1 |
| relation_state | offsetting | 2 | 69.79738573614746 | 1.0 | 0.0 | 0.0 | 1 |
| sector_gate_state | sector_aligned | 1367 | 5.432054101700802 | 0.5369422092172641 | 0.3972201901975128 | 0.29626920263350404 | 1 |
| sector_gate_state | sector_neutral | 240 | 7.092401075820177 | 0.575 | 0.39166666666666666 | 0.2625 | 1 |
| sector_gate_state | sector_weak | 14 | 17.48377057498624 | 0.7142857142857143 | 0.21428571428571427 | 0.14285714285714285 | 1 |

### GPT Review Status

| review_round | requested_via | captured_flag | status | used_as_source_flag | fallback_policy |
| --- | --- | --- | --- | --- | --- |
| task652_stability_review | Chrome ChatGPT coding/investing tab | 0 | ATTEMPTED_BUT_CHROME_TIMEOUT | 0 | Applied prior GPT review principles from Task650-651: preserve Task639 baseline, use relation as diagnostic overlay only, reject filters that do not beat Task639 after costs. |

## No-Background Decision-Maker Report

- 기준선이 아직 제일 셉니다.
- relation 태그로 차트/매크로/회사 상태를 더 똑똑하게 나눠 봤지만, 돈으로는 Task639를 못 이겼습니다.
- 그래서 지금은 매매를 바꾸면 안 됩니다.
- relation은 감시표로 두고, 다음 개선은 microstructure 원천 데이터가 차야 가능합니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| gpt_review_attempted | 1 | ATTEMPTED_BUT_CHROME_TIMEOUT | GPT review should be attempted and captured when Chrome is responsive |
| gpt_used_as_source | 1 | used_as_source=0 | GPT must not be used as source truth |
| candidate_grid_built | 1 | candidates=9 | multiple baseline-preserving overlays tested |
| baseline_beats_qqq | 1 | baseline=$7639.62; qqq=$1606.83 | baseline must beat QQQ |
| best_overlay_beats_task639 | 0 | best_overlay=chart_not_fragile_or_unconfirmed $6229.59; baseline=$7639.62 | overlay must beat Task639 baseline to be useful |
| overlay_promotion_candidate | 0 | promotion_candidates=0 | must beat Task639, improve drawdown, and beat QQQ in validation/recent |
| trading_promotion | 0 | diagnostic only | requires accepted OOS, source timing repair, paper shadow, and live readiness |

## Artifact Manifest

- `task_652_relation_tagged_execution_panel.csv`
- `task_652_candidate_account_grid.csv`
- `task_652_split_account_grid.csv`
- `task_652_tag_diagnostics.csv`
- `task_652_stability_matrix.csv`
- `task_652_gpt_review_status.csv`
- `task_652_decision.csv`
- `task_652_pass_fail_matrix.csv`
- `task_652_gpt_review_packet.md`
- `artifact_manifest.csv`