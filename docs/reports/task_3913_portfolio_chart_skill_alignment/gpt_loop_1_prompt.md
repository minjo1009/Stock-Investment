# GPT Loop 1 Prompt - Chart Skill Alignment

You are a senior mobile financial chart UX engineer and trading-governance reviewer.

Please inspect the Stock-Investment GitHub repository, especially the Portfolio tab, Portfolio V2 production spec, mobile visual QA spec, and frontend chart contracts.

Goal: review whether the Portfolio diagnostic chart should be implemented as a source-gated trend chart with:

- 1D/3D/5D/1M/3M/ALL range buttons
- slider previous/latest window controls
- automatic plot sizing
- y-axis value/price guide lines
- selected-point readout or crosshair-style behavior
- no fake per-symbol price, volume, broker, order, paper, live, or real-capital paths

Return implementation-level P0/P1 defects and exact patch guidance only.
