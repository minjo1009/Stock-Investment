# Task673 Setup Quality Layer

## Decision Summary

- Verdict: `SETUP_QUALITY_LAYER_BUILT_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

## Quant Expert Report

This task uses current entry-time data only. It does not use microstructure, future returns, future labels, symbol blacklist, or theme blacklist for assignment.

### Setup Performance

| split_name | setup_quality_bucket | candidate_count | avg_return_costed_pct_eval_only | win_rate_eval_only | entry_reduce_failure_rate_eval_only | return_used_in_assignment_flag | label_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all | fragile_setup | 37 | 19.572390891802925 | 0.7027027027027027 | 0.2702702702702703 | 0 | 0 |
| all | high_quality_setup | 698 | 4.526877134481727 | 0.504297994269341 | 0.4383954154727794 | 0 | 0 |
| all | medium_quality_setup | 656 | 7.091229508111228 | 0.5929878048780488 | 0.34146341463414637 | 0 | 0 |
| all | research_only_setup | 156 | 2.999886256010976 | 0.5 | 0.4551282051282051 | 0 | 0 |
| all | uncertain_setup | 74 | -5.968925849351178 | 0.32432432432432434 | 0.6486486486486487 | 0 | 0 |
| recent_oos | fragile_setup | 10 | 2.7327975738797785 | 0.7 | 0.3 | 0 | 0 |
| recent_oos | high_quality_setup | 163 | 7.865919418125755 | 0.4723926380368098 | 0.4539877300613497 | 0 | 0 |
| recent_oos | medium_quality_setup | 105 | 5.916725574326394 | 0.5523809523809524 | 0.3619047619047619 | 0 | 0 |
| recent_oos | research_only_setup | 45 | 9.267792409255474 | 0.5777777777777777 | 0.4 | 0 | 0 |
| recent_oos | uncertain_setup | 9 | 7.595017938776953 | 0.5555555555555556 | 0.3333333333333333 | 0 | 0 |
| validation | fragile_setup | 21 | 7.420256103938123 | 0.6666666666666666 | 0.2857142857142857 | 0 | 0 |
| validation | high_quality_setup | 243 | 4.673594743100945 | 0.5473251028806584 | 0.36213991769547327 | 0 | 0 |
| validation | medium_quality_setup | 333 | 7.073874386637824 | 0.6336336336336337 | 0.3063063063063063 | 0 | 0 |
| validation | research_only_setup | 17 | -15.884735250790552 | 0.058823529411764705 | 0.9411764705882353 | 0 | 0 |
| validation | uncertain_setup | 41 | -2.7098938891124096 | 0.36585365853658536 | 0.6097560975609756 | 0 | 0 |

### Pass Fail

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| setup_quality_panel_built | 1 | rows=1621 | setup quality exists |
| all_required_buckets_present | 1 | buckets=5 | multiple setup buckets |
| no_return_label_future_assignment | 1 | violations=0 | 0 violations |
| relation_name_alone_not_high | 1 | violations=0 | 0 violations |
| proxy_not_hard_rule | 1 | violations=0 | 0 violations |
| setup_oos_perf_report_built | 1 | rows=15 | split setup quality performance |
| strategy_accepted | 0 | research only | promotion gates required |

## No-Background Decision-Maker Report

이번 작업은 바로 실전 매매로 승격하지 않습니다.

상태를 더 쪼개고, 슬롯 경쟁과 동시 노출을 분리해서 다음 매매 룰 후보가 과최적화인지 확인하는 단계입니다.

## Artifact Manifest

- See `artifact_manifest.csv`.
