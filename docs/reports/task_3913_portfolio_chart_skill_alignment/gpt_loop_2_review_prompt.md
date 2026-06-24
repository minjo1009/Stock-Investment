# GPT Loop 2 Review Prompt - Chart Implementation QA

You are reviewing the implemented Portfolio diagnostic chart after Codex applied chart-skill guidance.

Please inspect the code and screenshot evidence, then check:

- chart geometry uses actual plot size
- y-axis guide labels match the visible data window
- range buttons change the visible window
- previous/latest slider controls change the visible window
- selected point readout or crosshair-style marker appears
- chart remains source-gated and read-only
- no fake per-symbol price or volume was invented
- no broker/API/order/paper/live/real-capital path was introduced

Return actionable defects only.
