# Task703 Event-Linked Source Axis Full-Period Backtest

## Decision Summary

- Verdict: EVENT_LINKED_SOURCE_AXIS_FULL_PERIOD_BACKTEST_COMPLETE_RESEARCH_ONLY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Scope: full baseline 5265 rows, event-linked 2445 rows.
- Eligible count: 585.
- Key $1,000 max5: eligible $4,725.31; event-linked $3,498.04; baseline $1,664.47; QQQ $1,746.31.
- GPT review complete flag: 1.
- Main finding: The five-axis parser was moved upstream to all Task636 event-linked candidates and backtested over the full baseline horizon.
- Next action: Diagnose eligible split/OOS durability and compare against Task639 before any promotion discussion.

## Quant Expert Report

### Parser Scope

- Parser moved from Task702 19 source-packet rows to Task636 2,445 event-linked lifecycles.
- Full freeze scope remains the 5,265 baseline candidates.
- Price context uses Task704 raw daily plus intraday as-of-entry backfill when available.
- Outcomes are attached only after freeze.

### GPT Review

| gpt_review_required_flag | gpt_review_complete_flag | gpt_review_path | gpt_used_as_source_flag | gpt_role | review_scope |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | docs\reports\task_703_event_linked_source_axis_backtest\gpt_review_raw.md | 0 | external_design_reviewer_only | full event-linked source-axis parser before final full-period backtest |

### Action Summary

| full_event_axis_action | candidate_count | source_event_count | symbols_sample | avg_costed_return_pct | median_costed_return_pct | win_rate | avg_excess_vs_qqq_costed_pct | outcome_used_for_selection_flag | outcome_used_for_evaluation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONFIRMATION_REQUIRED_HIGH_NOISE | 144 | 144 | CEG\|CEG\|GE\|TER\|TER\|TER\|GEV\|TER\|TER\|ASTS\|RTX\|RTX\|RTX\|RKLB\|RKLB\|RKLB\|RKLB\|RKLB\|GEV\|RKLB\|GEV\|CEG\|TEAM\|TEAM\|SNOW\|BA\|TEAM\|TEAM\|SNOW\|TEAM\|SNOW\|TEAM\|SNOW\|TEAM\|RKLB\|BA\|RKLB\|PLTR\|PLTR\|RTX | 19.7404 | 4.9529 | 0.6111 | 15.2261 | 0 | 1 |
| RESEARCH_ONLY_LOW_NOVELTY | 537 | 537 | ROK\|ROK\|TER\|RTX\|GE\|PH\|ROK\|DDOG\|GE\|GE\|PH\|CEG\|GE\|MDB\|PLTR\|SNOW\|DDOG\|CEG\|SNOW\|SNOW\|DDOG\|MDB\|DDOG\|SNOW\|PLTR\|CEG\|PLTR\|ROK\|MDB\|PH\|SNOW\|CEG\|GE\|ROK\|DDOG\|MDB\|PLTR\|SNOW\|PH\|PLTR | 18.5282 | 8.6727 | 0.6182 | 15.4692 | 0 | 1 |
| CONFIRMATION_REQUIRED_FINANCING | 58 | 58 | GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|MDB\|DDOG\|DDOG\|ASTS\|ASTS\|PH\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS | 18.1990 | -3.0033 | 0.4483 | 15.0091 | 0 | 1 |
| ELIGIBLE_RULE_CANDIDATE | 585 | 585 | CEG\|CEG\|CEG\|CEG\|ASTS\|ASTS\|ASTS\|TER\|ASTS\|ASTS\|ASTS\|ASTS\|GEV\|GEV\|GEV\|GEV\|CEG\|GEV\|GEV\|CEG\|RTX\|TEAM\|TEAM\|TEAM\|TEAM\|TEAM\|CEG\|CEG\|AMZN\|CRM\|CRWD\|DDOG\|ESTC\|GTLB\|MDB\|NET\|NOW\|OKTA\|SNOW\|TEAM | 10.6425 | 3.1040 | 0.5504 | 7.7752 | 0 | 1 |
| CONFIRMATION_REQUIRED_PRICE | 842 | 842 | RKLB\|RKLB\|CEG\|CEG\|CEG\|CEG\|CEG\|CEG\|PH\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|CEG\|CEG\|CEG\|PANW\|S\|HOOD\|IBIT\|COIN\|GE\|GOOGL\|HOOD\|RKLB\|COIN\|IBIT\|OKTA\|TEAM\|ZS\|RTX\|ISRG\|PLTR\|HOOD\|MSTR\|SNOW\|COIN\|CRWD\|ESTC | 6.9481 | 1.0955 | 0.5238 | 2.8370 | 0 | 1 |
| CONFIRMATION_REQUIRED_GUIDANCE_WEAK | 279 | 279 | EMR\|ETN\|GD\|GE\|LMT\|NOC\|PWR\|RKLB\|RTX\|IR\|GM\|ASTS\|GTLB\|SOFI\|IBIT\|TSM\|GEV\|OKTA\|ASML\|ORCL\|ARM\|HOOD\|VST\|AVGO\|CEG\|MSTR\|NET\|VRT\|COIN\|ARM\|ASML\|VRT\|AMZN\|MSFT\|COIN\|CRWD\|HOOD\|IBIT\|NOW\|TSM | 2.0209 | 3.5453 | 0.5556 | -0.7987 | 0 | 1 |
| RESEARCH_ONLY_NO_SOURCE_PACKET | 2820 | 0 | AMGN\|F\|ISRG\|MRNA\|REGN\|VRTX\|EMR\|GM\|HON\|IR\|AFRM\|GOOGL\|META\|S\|FTNT\|REGN\|ARM\|LLY\|NEE\|AMGN\|GM\|HOOD\|NEE\|NVO\|AFRM\|AMGN\|COIN\|EMR\|MSTR\|VRTX\|AVGO\|S\|AMD\|LLY\|FTNT\|REGN\|AMGN\|ARM\|AVGO\|CRWD | 0.5360 | -0.0317 | 0.4996 | -2.4041 | 0 | 1 |

### Split Summary For Eligible Candidates

| split_name | eligible_count | avg_costed_return_pct | median_costed_return_pct | win_rate | avg_excess_vs_qqq_costed_pct |
| --- | --- | --- | --- | --- | --- |
| recent_oos | 165 | 5.4305 | -0.0069 | 0.4970 | 1.8416 |
| train_design | 172 | 19.6718 | 5.6306 | 0.5407 | 18.8205 |
| validation | 248 | 7.8481 | 4.2320 | 0.5927 | 4.0624 |

### Portfolio Comparison

| portfolio_cohort | max_positions | source_candidate_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | beats_qqq_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_5265_baseline_costed | 5 | 5265 | 56 | 1664.4681 | 66.4468 | -20.0863 | 0 |
| all_5265_baseline_costed | 10 | 5265 | 117 | 1382.3937 | 38.2394 | -24.9357 | 0 |
| all_5265_baseline_costed | 20 | 5265 | 235 | 1829.3879 | 82.9388 | -23.2993 | 1 |
| event_linked_2445_costed | 5 | 2445 | 60 | 3498.0401 | 249.8040 | -23.3348 | 1 |
| event_linked_2445_costed | 10 | 2445 | 115 | 3240.1176 | 224.0118 | -19.3863 | 1 |
| event_linked_2445_costed | 20 | 2445 | 227 | 3475.0386 | 247.5039 | -15.1675 | 1 |
| full_event_axis_eligible | 5 | 585 | 48 | 4725.3052 | 372.5305 | -29.1212 | 1 |
| full_event_axis_eligible | 10 | 585 | 90 | 3443.6488 | 244.3649 | -28.9635 | 1 |
| full_event_axis_eligible | 20 | 585 | 154 | 3493.6574 | 249.3657 | -20.1907 | 1 |
| QQQ_buy_and_hold_same_horizon | 1 | 1 | 1 | 1746.3103 | 74.6310 | 0.0000 | 0 |

### Interpretation

- The five-axis parser now has materially broader coverage.
- This is still research-only because parser quality, OOS durability, and source certification need separate audit.

## No-Background Decision-Maker Report

- What happened: the parser moved upstream to all event-linked candidates.
- What changed: full-period backtest now covers 5,265 baseline candidates and 2,445 event-linked candidates.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task636 links/predictions, Task633/632 full baseline backtest panel, Task704 price context, Task684 legacy fallback context, QQQ daily.
- Outputs: freeze panel, eval panel, summaries, portfolio comparison, GPT review status, audit, decision, pass/fail, manifest.
- Row counts: freeze 5265, eval 5265, action summary 7.
- Validation commands: `python src/backtest/build_task703_event_linked_source_axis_backtest.py`; `python -m unittest tests.test_task703_event_linked_source_axis_backtest`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| freeze_scope_5265 | PRIMARY_PASS | 1 | rows=5265 | full baseline candidate scope |
| event_linked_scope_2445 | PRIMARY_PASS | 1 | event_linked=2445 | Task636 event-linked lifecycle coverage |
| eligible_nonzero | PRIMARY_PASS | 1 | eligible=585 | parser should produce eligible candidates |
| price_context_full_coverage | PRIMARY_PASS | 1 | price_context=5265/5265 | Task704 as-of-entry price context should cover the full freeze scope |
| gpt_review_complete_before_report | PRIMARY_PASS | 1 | gpt_review_complete=1 | GPT review artifact must exist before final Task703 report |
| eval_rows_complete | PRIMARY_PASS | 1 | eval_rows=5265 | evaluation attaches outcomes after freeze |
| portfolio_comparison_present | PRIMARY_PASS | 1 | QQQ_buy_and_hold_same_horizon\|all_5265_baseline_costed\|event_linked_2445_costed\|full_event_axis_eligible | portfolio cohorts and QQQ benchmark present |
| no_strategy_or_trade_promotion | PRIMARY_PASS | 1 | allocation_approved=0; paper_or_live_trade_approved=0 | Task703 is research-only |
