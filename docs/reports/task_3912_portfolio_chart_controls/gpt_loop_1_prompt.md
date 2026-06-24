# GPT Loop 1 Prompt - Portfolio Chart Control Design

You are reviewing the Stock-Investment frontend repository as a senior mobile trading UI/chart engineer.

Please read the current Portfolio tab, existing frontend safety contracts, chart/read-model constraints, and recent Portfolio table repair task report.

Goal: propose a minimal implementation plan for Portfolio chart controls:

- range buttons: 1D, 3D, 5D, 1M, 3M, ALL
- buttons must change the visible chart data window
- slider controls must move the visible window
- chart must remain read-only and source-gated
- no fake per-symbol price chart
- no broker, paper, live, order, or real-capital path

Return implementation-level feedback that Codex can apply directly.
