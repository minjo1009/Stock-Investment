# Task608F GPT Review Notes

GPT was used only as a review and critique layer inside the `1. 코딩/투자` ChatGPT project. It is not a source of truth.

## Packet Sent

- Task608DE OOS evidence: clean entries +26.03% average, 92.59% win rate; entry-reduce failures -16.45% average, 0.00% win rate.
- Code finding: `entry_reduce_failure_flag` is defined from realized return <= -3%, then recomputed after cost stress.
- Prior Task524 suppression result: `SUPPRESSION_FAIL_NEEDS_NEW_FEATURES`.

## GPT Critique Summary

- The current entry-reduce field is an ex-post loss label, not a strategy component.
- Simple suppression is too coarse because the problem is conditional rather than categorical.
- The missing layer is early post-entry diagnostics that distinguish continuation from exhaustion.
- Task608F should prioritize live-detectable failure states, not headline return improvement.

## Accepted Repo-Native Interpretation

The project should treat entry-reduce as an unresolved live-detectability problem. Refinement is blocked until path diagnostics prove that failed entries can be detected before or shortly after entry without using outcome labels.
