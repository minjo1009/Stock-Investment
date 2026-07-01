# Task632 GPT Review Notes

## Status

- Review lane: backtest
- GPT role: review and ideation only
- Source of truth: repository artifacts and validation commands
- Strategy acceptance impact: none

## Review Summary

GPT review agreed with the repository result: Task632 improves temporal integrity but does not prove tradable edge.

Key review points:

- Recent OOS fails: 52 trades average -0.73 percent with 51.92 percent entry-reduce failure.
- Cost/account fails: recent OOS and full panel lose 0 of 4 capacity comparisons versus Task617 at 50bp.
- Time-certified events are not enough. Entry support still needs stronger event-to-symbol relevance.
- Source time gaps are too large and must stay as a separate audit bucket.
- Qualitative information should not create entries without chart confirmation.

## Accepted Into Repo Work

Task633 should be defined as recent-OOS failure decomposition plus confirmation-gated entry replay.

Required next gates:

- Entry-support events must carry a deterministic relevance reason such as direct company, named product, named program, named contract, named customer, or named regulator action.
- Broad policy, macro, or sector events cannot support entries alone.
- Date-only events remain source-time gaps and never support entries.
- Every selected trade must pass event relevance and chart confirmation.
- Recent OOS and 50bp account comparison must be primary gates, not gross average return.

## Forbidden

- Do not use GPT output as a source or score input.
- Do not change strategy acceptance from this review.
- Do not promote real capital.
