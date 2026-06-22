# Task T101-REV - CRB Bottleneck Attribution

## 1. Summary
- status: PASS
- primary_bottleneck: range_pct
- selected_single_relaxation: relax_range_pct_0p10_to_0p12

## 2. Funnel Table
| Stage | Input | Passed | Filtered | Pass Rate |
|---|---:|---:|---:|---:|
| Stage0_breakout_trigger | 1079 | 1079 | 0 | 1.0 |
| Stage1_range_pct | 1079 | 303 | 776 | 0.280816 |
| Stage2_compression | 303 | 7 | 296 | 0.023102 |
| Stage3_touch_count | 7 | 5 | 2 | 0.714286 |

## 3. Single-Condition Impact
| Case | Signals | Delta vs Stage0 | WinRate20 | AvgRet20 |
|---|---:|---:|---:|---:|
| breakout_plus_range | 303 | -776 | 0.574257 | 0.014318 |
| breakout_plus_compression | 65 | -1014 | 0.723077 | 0.039716 |
| breakout_plus_touch | 348 | -731 | 0.577586 | 0.017201 |

## 4. Combination Impact
| Case | Signals | Delta vs Stage0 | WinRate20 | AvgRet20 |
|---|---:|---:|---:|---:|
| breakout_plus_range_plus_compression | 7 | -1072 | 0.857143 | 0.031635 |
| breakout_plus_range_plus_touch | 121 | -958 | 0.61157 | 0.015893 |
| breakout_plus_compression_plus_touch | 30 | -1049 | 0.7 | 0.030373 |
| full_crb_all_three | 5 | -1074 | 1.0 | 0.038711 |

## 5. Removed-Signal Quality
| Filter | Removed | WinRate20 | AvgRet20 | NetRet20 |
|---|---:|---:|---:|---:|
| range_pct | 776 | 0.576031 | 0.021953 | 17.035268 |
| compression | 296 | 0.567568 | 0.013908 | 4.116829 |
| touch_count | 2 | 0.5 | 0.013945 | 0.027889 |

## 6. Primary Bottleneck
- range_pct

## 7. Selected Single Relaxation
- id: relax_range_pct_0p10_to_0p12
- change: max_range_pct <= 0.10 -> <= 0.12
- reason: Range gate is dominant bottleneck and removed signals retain positive forward-return profile.

## 8. Final Answer
Primary bottleneck is `range_pct`, and next single relaxation should test `relax_range_pct_0p10_to_0p12`.
