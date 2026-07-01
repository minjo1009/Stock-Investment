# Task608I GPT Review Notes

GPT was used only inside the `1. 코딩/투자` ChatGPT project as a review and critique layer. It is not a source of truth.

## Packet Sent

- Task608DE: clean entries +26.03%, 92.59% win rate; entry-reduce failures -16.45%, 0% win rate.
- Task608F: `entry_reduce_failure_flag` is an outcome label, not a live reducer.
- Task608G: simple live signals failed; state/path interactions looked promising diagnostically.
- Task608H: fold-forward no-label reduce/exit simulation failed. Best 50bp scenario had avg net delta -1.76 pct points and entry-reduce delta 0.00%.

## GPT Critique Summary

- Entry-reduce failure exists, but live detection has not been proven.
- Diagnostic explanation is not the same as fold-forward prediction.
- Trigger sample sizes are too small for firm-grade acceptance.
- The failure population is likely a mix of different mechanisms.
- Current evidence supports shifting from reducer optimization to failure taxonomy and entry qualification.

## Accepted Repo-Native Interpretation

The next task should not tune reducer thresholds. It should build mechanism-level failure taxonomy and add live features around liquidity location, breakout quality, relative positioning, market participation, and prior-day context.
