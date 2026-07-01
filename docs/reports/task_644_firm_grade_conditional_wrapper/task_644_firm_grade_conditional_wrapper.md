# Task644 Firm-Grade Conditional Wrapper

## Decision Summary

- Verdict: `FAIL_NO_FIRM_GRADE_CONDITIONAL_WRAPPER_OVER_TASK639`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Best config: `base` / `existing` / `equal`
- Best final: $7639.62
- Best DD: -23.76%
- Task639: $7639.62, DD -23.76%

## Quant Expert Report

Task644 implements the GPT-reviewed firm-grade redesign: conditional confirmation, signal-quality-aware volatility sizing, soft tier sizing, and partial capital recycling.

### Source Audit

| task_id | task643_execution_rows | conditional_candidate_rows | gpt_design_captured_flag | label_used_in_assignment_flag | symbol_blacklist_used_flag | theme_blacklist_used_flag | global_confirmation_only_flag | atr_only_sizing_only_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Task644 | 10824 | 34626 | 1 | 0 | 0 | 0 | 0 | 0 |

### Top Full-Period Candidates

| split_name | entry_wrapper | exit_wrapper | sizing_wrapper | round_trip_cost_bps | source_trade_count | accepted_trade_count | partial_exit_count | final_capital_usd | capital_return_pct | avg_net_return_pct | win_rate | entry_reduce_failure_rate | max_drawdown_pct | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | symbol_blacklist_used_flag | theme_blacklist_used_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | base | existing | equal | 50 | 1621 | 54 | 0 | 7639.620310821464 | 663.9620310821465 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -23.755747663170702 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | existing | soft_tier | 50 | 1621 | 54 | 0 | 7185.435165738926 | 618.5435165738926 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -22.35244028043538 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | existing | quality_vol | 50 | 1621 | 54 | 0 | 6600.978471801894 | 560.0978471801894 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -23.18335782602442 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | existing | quality_vol_tier | 50 | 1621 | 54 | 0 | 6353.81984696376 | 535.381984696376 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -21.65524455438198 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | partial30_third | equal | 50 | 1621 | 54 | 26 | 5759.92373723616 | 475.9923737236161 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -23.697664293934462 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | partial30_third | soft_tier | 50 | 1621 | 54 | 26 | 5461.117025496071 | 446.11170254960706 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -22.321167757869954 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | partial30_third | quality_vol | 50 | 1621 | 54 | 26 | 5085.065784442445 | 408.50657844424455 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -23.175346511421125 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | partial30_third | quality_vol_tier | 50 | 1621 | 54 | 26 | 4909.2893179252405 | 390.928931792524 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -21.66472575138266 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | badvol_partial20_half | equal | 50 | 1621 | 54 | 16 | 4349.324185049317 | 334.93241850493166 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -23.309050485409454 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | weak_badvol_confirm_vwap_rs | existing | equal | 50 | 1387 | 53 | 0 | 4210.463436129261 | 321.04634361292614 | 19.2675628658693 | 0.6226415094339622 | 0.37735849056603776 | -28.18093416038475 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | partial20_half | equal | 50 | 1621 | 54 | 33 | 4203.799101491845 | 320.3799101491845 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -24.152680566394825 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | weak_trail10 | equal | 50 | 1621 | 60 | 0 | 4186.49540715431 | 318.649540715431 | 15.52553293300464 | 0.6166666666666667 | 0.3 | -24.172700936110324 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | weak_trail10 | soft_tier | 50 | 1621 | 60 | 0 | 4175.068971729889 | 317.5068971729889 | 15.52553293300464 | 0.6166666666666667 | 0.3 | -23.76732457360212 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | badvol_partial20_half | soft_tier | 50 | 1621 | 54 | 16 | 4135.333706229957 | 313.53337062299573 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -21.945897679546466 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | weak_trail10 | quality_vol | 50 | 1621 | 60 | 0 | 4047.6079871142306 | 304.76079871142304 | 15.52553293300464 | 0.6166666666666667 | 0.3 | -24.580105741927007 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | weak_badvol_confirm_vwap_rs | existing | soft_tier | 50 | 1387 | 53 | 0 | 4021.561099247089 | 302.1561099247089 | 19.2675628658693 | 0.6226415094339622 | 0.37735849056603776 | -26.392442271757165 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | partial20_half | soft_tier | 50 | 1621 | 54 | 33 | 4019.180752920936 | 301.9180752920936 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -22.75594068460418 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | weak_trail10 | quality_vol_tier | 50 | 1621 | 60 | 0 | 4018.3875942012655 | 301.83875942012656 | 15.52553293300464 | 0.6166666666666667 | 0.3 | -24.02174814443635 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | weak_hold20 | soft_tier | 50 | 1621 | 59 | 0 | 3943.1877452306667 | 294.3187745230666 | 15.344123991437474 | 0.576271186440678 | 0.3050847457627119 | -27.118445109440525 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | badvol_partial20_half | quality_vol | 50 | 1621 | 54 | 16 | 3939.6803437880094 | 293.96803437880095 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -22.76892988565715 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | weak_hold20 | equal | 50 | 1621 | 59 | 0 | 3934.6674146582964 | 293.4667414658296 | 15.344123991437474 | 0.576271186440678 | 0.3050847457627119 | -27.92187842675632 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | weak_hold20 | quality_vol | 50 | 1621 | 59 | 0 | 3827.239773988983 | 282.72397739889834 | 15.344123991437474 | 0.576271186440678 | 0.3050847457627119 | -27.235797352419144 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | weak_hold20 | quality_vol_tier | 50 | 1621 | 59 | 0 | 3817.3114459189514 | 281.73114459189514 | 15.344123991437474 | 0.576271186440678 | 0.3050847457627119 | -26.60138447960915 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | partial20_half | quality_vol | 50 | 1621 | 54 | 33 | 3795.0424970878207 | 279.5042497087821 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -23.663729850362316 | 1606.8278306897957 | 1 | 0 | 0 | 0 |
| all | base | badvol_partial20_half | quality_vol_tier | 50 | 1621 | 54 | 16 | 3785.4819865377567 | 278.54819865377567 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -21.291339868779225 | 1606.8278306897957 | 1 | 0 | 0 | 0 |

### Top OOS Rows

| split_name | entry_wrapper | exit_wrapper | sizing_wrapper | round_trip_cost_bps | source_trade_count | accepted_trade_count | partial_exit_count | final_capital_usd | capital_return_pct | avg_net_return_pct | win_rate | entry_reduce_failure_rate | max_drawdown_pct | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | symbol_blacklist_used_flag | theme_blacklist_used_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent_oos | base | existing | quality_vol_tier | 50 | 332 | 10 | 0 | 1565.2390582415735 | 56.52390582415736 | 25.78265294363888 | 0.5 | 0.1 | -0.8840725011891037 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | weak_hold20 | quality_vol_tier | 50 | 332 | 10 | 0 | 1565.2390582415735 | 56.52390582415736 | 25.78265294363888 | 0.5 | 0.1 | -0.8840725011891037 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | weak_trail10 | quality_vol_tier | 50 | 332 | 10 | 0 | 1565.2390582415735 | 56.52390582415736 | 25.78265294363888 | 0.5 | 0.1 | -0.8840725011891037 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | existing | quality_vol_tier | 50 | 293 | 10 | 0 | 1565.2390582415735 | 56.52390582415736 | 25.78265294363888 | 0.5 | 0.1 | -0.8840725011891037 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | weak_hold20 | quality_vol_tier | 50 | 293 | 10 | 0 | 1565.2390582415735 | 56.52390582415736 | 25.78265294363888 | 0.5 | 0.1 | -0.8840725011891037 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | weak_trail10 | quality_vol_tier | 50 | 293 | 10 | 0 | 1565.2390582415735 | 56.52390582415736 | 25.78265294363888 | 0.5 | 0.1 | -0.8840725011891037 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | existing | soft_tier | 50 | 332 | 10 | 0 | 1559.3511774402173 | 55.93511774402173 | 25.78265294363888 | 0.5 | 0.1 | -0.8413683997520294 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | weak_hold20 | soft_tier | 50 | 332 | 10 | 0 | 1559.3511774402173 | 55.93511774402173 | 25.78265294363888 | 0.5 | 0.1 | -0.8413683997520294 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | weak_trail10 | soft_tier | 50 | 332 | 10 | 0 | 1559.3511774402173 | 55.93511774402173 | 25.78265294363888 | 0.5 | 0.1 | -0.8413683997520294 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | existing | soft_tier | 50 | 293 | 10 | 0 | 1559.3511774402173 | 55.93511774402173 | 25.78265294363888 | 0.5 | 0.1 | -0.8413683997520294 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | weak_hold20 | soft_tier | 50 | 293 | 10 | 0 | 1559.3511774402173 | 55.93511774402173 | 25.78265294363888 | 0.5 | 0.1 | -0.8413683997520294 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | weak_trail10 | soft_tier | 50 | 293 | 10 | 0 | 1559.3511774402173 | 55.93511774402173 | 25.78265294363888 | 0.5 | 0.1 | -0.8413683997520294 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | existing | quality_vol | 50 | 332 | 10 | 0 | 1537.7447265473918 | 53.77447265473918 | 25.78265294363888 | 0.5 | 0.1 | -0.8545445089436554 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | weak_hold20 | quality_vol | 50 | 332 | 10 | 0 | 1537.7447265473918 | 53.77447265473918 | 25.78265294363888 | 0.5 | 0.1 | -0.8545445089436554 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | weak_trail10 | quality_vol | 50 | 332 | 10 | 0 | 1537.7447265473918 | 53.77447265473918 | 25.78265294363888 | 0.5 | 0.1 | -0.8545445089436554 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | existing | quality_vol | 50 | 293 | 10 | 0 | 1537.7447265473918 | 53.77447265473918 | 25.78265294363888 | 0.5 | 0.1 | -0.8545445089436554 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | weak_hold20 | quality_vol | 50 | 293 | 10 | 0 | 1537.7447265473918 | 53.77447265473918 | 25.78265294363888 | 0.5 | 0.1 | -0.8545445089436554 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | weak_trail10 | quality_vol | 50 | 293 | 10 | 0 | 1537.7447265473918 | 53.77447265473918 | 25.78265294363888 | 0.5 | 0.1 | -0.8545445089436554 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | existing | equal | 50 | 332 | 10 | 0 | 1531.9029143138666 | 53.19029143138667 | 25.78265294363888 | 0.5 | 0.1 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | weak_hold20 | equal | 50 | 332 | 10 | 0 | 1531.9029143138666 | 53.19029143138667 | 25.78265294363888 | 0.5 | 0.1 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | weak_trail10 | equal | 50 | 332 | 10 | 0 | 1531.9029143138666 | 53.19029143138667 | 25.78265294363888 | 0.5 | 0.1 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | existing | equal | 50 | 293 | 10 | 0 | 1531.9029143138666 | 53.19029143138667 | 25.78265294363888 | 0.5 | 0.1 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | weak_hold20 | equal | 50 | 293 | 10 | 0 | 1531.9029143138666 | 53.19029143138667 | 25.78265294363888 | 0.5 | 0.1 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | weak_trail10 | equal | 50 | 293 | 10 | 0 | 1531.9029143138666 | 53.19029143138667 | 25.78265294363888 | 0.5 | 0.1 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | badvol_partial20_half | quality_vol_tier | 50 | 332 | 10 | 1 | 1477.77269471518 | 47.77726947151799 | 25.78265294363888 | 0.5 | 0.1 | -0.9430138310187797 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | badvol_partial20_half | quality_vol_tier | 50 | 293 | 10 | 1 | 1477.77269471518 | 47.77726947151799 | 25.78265294363888 | 0.5 | 0.1 | -0.9430138310187797 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | badvol_partial20_half | soft_tier | 50 | 332 | 10 | 1 | 1467.660790634041 | 46.766079063404085 | 25.78265294363888 | 0.5 | 0.1 | -0.9002755949209185 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | badvol_partial20_half | soft_tier | 50 | 293 | 10 | 1 | 1467.660790634041 | 46.766079063404085 | 25.78265294363888 | 0.5 | 0.1 | -0.9002755949209185 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | badvol_partial20_half | quality_vol | 50 | 332 | 10 | 1 | 1454.78675753228 | 45.47867575322799 | 25.78265294363888 | 0.5 | 0.1 | -0.9092135644709676 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | badvol_partial20_half | quality_vol | 50 | 293 | 10 | 1 | 1454.78675753228 | 45.47867575322799 | 25.78265294363888 | 0.5 | 0.1 | -0.9092135644709676 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | partial30_third | quality_vol_tier | 50 | 332 | 10 | 3 | 1450.0944392263439 | 45.0094439226344 | 25.78265294363888 | 0.5 | 0.1 | -0.9207461020265151 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | partial30_third | quality_vol_tier | 50 | 293 | 10 | 3 | 1450.0944392263439 | 45.0094439226344 | 25.78265294363888 | 0.5 | 0.1 | -0.936650952655238 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | partial30_third | soft_tier | 50 | 332 | 10 | 3 | 1444.720976272023 | 44.4720976272023 | 25.78265294363888 | 0.5 | 0.1 | -0.8777070052592095 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | partial30_third | soft_tier | 50 | 293 | 10 | 3 | 1444.720976272023 | 44.4720976272023 | 25.78265294363888 | 0.5 | 0.1 | -0.8921480435213014 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | badvol_partial20_half | equal | 50 | 332 | 10 | 1 | 1444.720922018972 | 44.472092201897205 | 25.78265294363888 | 0.5 | 0.1 | -0.8660401375810256 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | badvol_partial20_half | equal | 50 | 293 | 10 | 1 | 1444.720922018972 | 44.472092201897205 | 25.78265294363888 | 0.5 | 0.1 | -0.8660401375810256 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | partial30_third | quality_vol | 50 | 332 | 10 | 3 | 1428.245868021458 | 42.82458680214578 | 25.78265294363888 | 0.5 | 0.1 | -0.8886055809248727 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | partial30_third | quality_vol | 50 | 293 | 10 | 3 | 1428.245868021458 | 42.82458680214578 | 25.78265294363888 | 0.5 | 0.1 | -0.9034105020521821 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | base | partial30_third | equal | 50 | 332 | 10 | 3 | 1422.9090528730453 | 42.290905287304525 | 25.78265294363888 | 0.5 | 0.1 | -0.845135448292289 | 1124.192829329964 | 1 | 0 | 0 | 0 |
| recent_oos | supply_badvol_confirm_vwap_or_volume | partial30_third | equal | 50 | 293 | 10 | 3 | 1422.9090528730453 | 42.290905287304525 | 25.78265294363888 | 0.5 | 0.1 | -0.8585163949047292 | 1124.192829329964 | 1 | 0 | 0 | 0 |

### Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| gpt_design_captured | 1 | captured=1 | GPT design review must be captured as review-only input |
| best_candidate_beats_task639_return | 0 | best=$7639.62; task639=$7639.62 | best final capital must exceed Task639 |
| best_candidate_reduces_task639_drawdown | 0 | best_dd=-23.76%; task639_dd=-23.76% | best drawdown must be less severe than Task639 |
| same_config_validation_and_recent_beat_qqq | 1 | validation=$1069.23/QQQ $1049.91; recent=$1531.90/QQQ $1124.19 | same config must beat QQQ in validation and recent OOS |
| no_shortcut_blacklist_or_label | 1 | symbol_blacklist=0; theme_blacklist=0; label_assignment=0 | no blacklist or after-the-fact label shortcut |
| trading_promotion | 0 | research backtest only | requires live rule lock, latency audit, source readiness, and paper-shadow replay |

## No-Background Decision-Maker Report

- We avoided global filters, ATR-only sizing, short-exit-only logic, blacklists, and loser labels.
- Conditional wrappers are tested against Task639 using the same $1000 account and 50bp cost.
- Real trading remains forbidden even if a research candidate passes.

## Artifact Manifest

- `task_644_gpt_design_packet.txt`
- `task_644_gpt_design_response.md`
- `task_644_gpt_result_packet.txt`
- `task_644_gpt_result_response.md`
- `task_644_conditional_candidate_panel.csv`
- `task_644_account_grid.csv`
- `task_644_oos_grid.csv`
- `task_644_source_audit.csv`
- `task_644_pass_fail_matrix.csv`
- `task_644_decision.csv`
- `artifact_manifest.csv`
