# Task668 Promotion Blocker Report

- Decision: `REGIME_THEME_PLAYBOOK_TESTED_NO_PROMOTION_CANDIDATE`
- Strategy: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`

## Simple Reason

The playbook layer was built and tested, but no candidate improved return, drawdown, validation, and recent OOS together.

## Rule Hygiene

- return_used_in_assignment = 0
- label_used_in_assignment = 0
- symbol_blacklist = 0
- return-tuned theme blacklist = 0
- exit_changed = 0
- fixed_hold_override = 0

## Candidate Summary

| candidate_name | all_final_capital_usd | all_max_drawdown_pct | all_accepted_trade_count | all_avg_size_multiplier | all_entry_reduce_failure_rate | recent_oos_final_capital_usd | recent_oos_max_drawdown_pct | recent_oos_accepted_trade_count | recent_oos_avg_size_multiplier | recent_oos_entry_reduce_failure_rate | validation_final_capital_usd | validation_max_drawdown_pct | validation_accepted_trade_count | validation_avg_size_multiplier | validation_entry_reduce_failure_rate | beats_all_task639_flag | all_drawdown_not_worse_flag | validation_improves_task639_flag | recent_oos_improves_task639_flag | validation_drawdown_not_worse_flag | recent_oos_drawdown_not_worse_flag | promotion_allowed_flag | promotion_candidate_flag | failure_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | 10887.474713480713 | -30.524857842425657 | 51.0 | 1.0 | 0.3333333333333333 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1327.5223368015004 | -5.866934869678831 | 13.0 | 1.0 | 0.15384615384615385 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| relation_priority_playbook_lite_sizing | 10183.615927393126 | -28.61213359654865 | 51.0 | 0.9323529411764705 | 0.3333333333333333 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1298.0005109893289 | -5.866934869678831 | 13.0 | 0.9769230769230769 | 0.15384615384615385 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| baseline_task639 | 7639.620310821465 | -23.755747663170702 | 54.0 | 1.0 | 0.35185185185185186 | 1531.9029143138666 | -0.811391994497368 | 10.0 | 1.0 | 0.1 | 1069.2312936091898 | -7.363321689343804 | 15.0 | 1.0 | 0.4 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 0 | full_period_return_not_better |
| playbook_priority_only | 7585.473449655701 | -27.39107520958347 | 51.0 | 1.0 | 0.37254901960784315 | 1489.3083455052943 | -4.8618878385964575 | 11.0 | 1.0 | 0.36363636363636365 | 1517.5761093266472 | -5.473756162118882 | 14.0 | 1.0 | 0.21428571428571427 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| playbook_priority_lite_sizing | 7162.954375227895 | -25.473908307011584 | 51.0 | 0.9352941176470588 | 0.37254901960784315 | 1466.4856373271239 | -4.8618878385964575 | 11.0 | 0.9727272727272727 | 0.36363636363636365 | 1517.5761093266472 | -5.473756162118882 | 14.0 | 1.0 | 0.21428571428571427 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| relation_priority_block_research_only | 6003.618767530641 | -36.49683272433539 | 50.0 | 1.0 | 0.34 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1441.1653829501581 | -5.866934869678831 | 13.0 | 1.0 | 0.15384615384615385 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| playbook_dynamic_cap | 5173.940688581928 | -18.758042531894326 | 46.0 | 1.0 | 0.3695652173913043 | 1667.2809903209381 | -3.525899653039477 | 11.0 | 1.0 | 0.18181818181818182 | 1038.3854696195574 | -6.578720639095326 | 14.0 | 1.0 | 0.42857142857142855 | 0 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| playbook_contextual_sizing | 4516.131131173615 | -20.894240403450148 | 51.0 | 0.7834313725490196 | 0.37254901960784315 | 1445.5648214971343 | -4.8618878385964575 | 11.0 | 0.9477272727272728 | 0.36363636363636365 | 1417.987245788115 | -4.359972185882177 | 14.0 | 0.888392857142857 | 0.21428571428571427 | 0 | 1 | 1 | 0 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| playbook_block_research_only | 3570.132743535869 | -22.95937566909021 | 42.0 | 0.8561904761904762 | 0.38095238095238093 | 1535.8995887310816 | -2.9117736523479376 | 11.0 | 0.9818181818181819 | 0.2727272727272727 | 1047.5631289095495 | -5.330247326121795 | 14.0 | 0.8628571428571429 | 0.42857142857142855 | 0 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| playbook_priority_cap_sizing | 3106.670420157094 | -16.39484760752351 | 46.0 | 0.7789130434782608 | 0.3695652173913043 | 1581.8359801820704 | -2.9117736523479376 | 11.0 | 0.875 | 0.18181818181818182 | 1026.7251485188701 | -5.330247326121795 | 14.0 | 0.8342857142857143 | 0.42857142857142855 | 0 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | full_period_return_not_better |
