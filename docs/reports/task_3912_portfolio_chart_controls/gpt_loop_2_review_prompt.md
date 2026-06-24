# GPT Loop 2 Review Prompt - Portfolio Chart QA

You are reviewing the implemented Portfolio diagnostic chart controls.

Please inspect the current code and available screenshots, then check:

- 1D, 3D, 5D, 1M, 3M, ALL buttons map to visible chart windows
- `이전` and `최근` slider controls update the visible window
- slider labels accurately describe latest vs prior windows
- chart remains source-gated and read-only
- no fake per-symbol market data was invented
- no broker, paper, live, order, or real-capital path was introduced

Return actionable defects only.
