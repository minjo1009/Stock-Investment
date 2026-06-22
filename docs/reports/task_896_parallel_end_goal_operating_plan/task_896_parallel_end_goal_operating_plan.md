# Task896 Parallel End-Goal Operating Plan

## Decision Summary

- Verdict: implemented.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Operating mode: `parallel_vertical_slice_plus_data_corpus`.
- End goal: US equity quant trading automation through source evidence, economic meaning, relationship graph, candidate thesis, validated backtest, and paper/live gate.
- Current position: L1 seed and local-lineage attachment exist; L2-L5 and brain-driven backtest do not yet exist.
- Vertical slice scope: 8 symbols: AMD, AMZN, AVGO, GOOGL, META, MSFT, NVDA, TSLA.
- Data corpus scope: 62 missing-seed symbols.
- External GPT/Chrome review: captured and incorporated as review-only feedback.
- First next task: Task897.

## Quant Expert Report

The project should stop adding isolated diagnostic tasks. The next work must move two lanes at the same time:

- Vertical slice lane: prove the L1 -> L2 -> L3 -> L4 -> L5 brain mechanics on the 8 seed symbols.
- Data corpus lane: fill source-time coverage for the other 62 symbols under a provider/schema contract.
- Integration lane: merge the two lanes only after Task901 and Task905 exist.

Task897-Task906 are fixed as the next program:

- Task897: L2 primitive fact builder for attached L1 seeds.
- Task898: L2 meaning gate and uncertainty tags, blocked until Task897 and Task903 pass.
- Task899: minimal as-of relation snapshot.
- Task900: review-only candidate thesis packets.
- Task901: dry trader decision and backtest gate check.
- Task902: raw source schema and provider map.
- Task903: small corpus reality check for 8 seed symbols.
- Task904: source-time seed acquisition for 62 missing symbols.
- Task905: coverage validator and gap dashboard.
- Task906: merge data corpus into vertical slice.

External GPT review changed the plan in four ways:

- Task897 success now requires source span, as-of timestamp, deterministic rule id, reproducibility, and uncertainty per primitive.
- Task902 must separate source time, publication time, ingestion time, effective time, revision handling, and source priority.
- Task903 must happen before Task898 so raw-source reality is checked before meaning promotion.
- Architecture freeze is forbidden until Task904 and Task906 re-review the 62 missing-seed symbols.

Stop-doing rules:

- Do not create another pure diagnosis task unless it changes an execution gate.
- Do not expand beyond Task897-906 until Task901 and Task905 both exist.
- Do not run a brain backtest before L5 dry decisions create explicit adapter fields.
- Do not broad-download sources outside the Task902 provider contract.
- Do not treat missing source coverage as bearish or negative evidence.
- Stop Task898-901 if primitive acceptance is below 80 percent.
- Keep relation graph outputs provisional if raw source linkage is below 95 percent for the promoted subset.
- Do not generate candidate thesis packets if uncertainty propagation is missing.
- Do not freeze architecture before the missing-seed symbols are reviewed through Task904/906.

## No-Background Decision-Maker Report

We are not close to a real strategy backtest yet. We are at the point where the first L1 evidence seed is organized enough to start a narrow brain slice.

The correct next move is not to wait for perfect data. It is also not to fake a full backtest. The correct move is parallel:

- Build one thin brain path on 8 symbols.
- Build the missing data corpus for the other 62 symbols.
- Reconnect them at Task906.

## Artifact Manifest

- Script: `scripts/trader_brain_896_parallel_end_goal_operating_plan.py`.
- Validator: `scripts/trader_brain_896_parallel_end_goal_operating_plan_validate.py`.
- Test: `tests/test_trader_brain_896_parallel_end_goal_operating_plan.py`.
- Scorecard: `data/artifacts/task_896_parallel_end_goal_operating_plan/end_goal_progress_scorecard.csv`.
- Plan: `data/artifacts/task_896_parallel_end_goal_operating_plan/parallel_execution_plan_task897_906.csv`.
- Expert panel: `data/artifacts/task_896_parallel_end_goal_operating_plan/expert_panel_review_synthesis.csv`.
- External GPT review: `data/artifacts/task_896_parallel_end_goal_operating_plan/external_gpt_review_synthesis.csv`.
- Stop rules: `data/artifacts/task_896_parallel_end_goal_operating_plan/stop_doing_rules.csv`.
- Symbol scope: `data/artifacts/task_896_parallel_end_goal_operating_plan/parallel_lane_symbol_scope.csv`.
- Summary: `data/artifacts/task_896_parallel_end_goal_operating_plan/task_896_parallel_end_goal_operating_plan_summary.json`.
- Validation command: `python scripts/trader_brain_896_parallel_end_goal_operating_plan_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
