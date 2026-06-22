# Problem

- T601-2 showed top3_share=1.0 and symbol_entropy=1.059385 before this slice.
- The portfolio selection layer needed concentration controls without changing entry strategy, regime, universe, or alpha research.
- Sector concentration must be capped only when a sector source exists; unavailable sector data must be reported as source-blocked.

# Evidence

- top3_share_before=1.0 from stage=FILLED.
- top3_share_after=0.75.
- symbol_entropy_before=1.059385.
- symbol_entropy_after=1.386294.
- explanation_coverage=1.0.
- symbol_cooldown_minutes=390.
- sector_cap_status=SOURCE_BLOCKED_SECTOR_UNAVAILABLE.
- liquidity_source_status=SOURCE_BLOCKED_NO_LIQUIDITY_FIELD.
- AMD selected count=3; reasons=ENTRY_OR_SOURCE_BLOCKED_BY_FUNNEL=90; SAME_SYMBOL_CAP_0.25=61; SYMBOL_COOLDOWN_ACTIVE_390_MINUTES=60; PORTFOLIO_FULL=5; PASSED_RANK_LIQUIDITY_DIVERSIFICATION_COOLDOWN_POSITION_CONTROLS=3.
- AMZN selected count=3; rejected/dropped reasons=SAME_SYMBOL_CAP_0.25=54; ENTRY_OR_SOURCE_BLOCKED_BY_FUNNEL=8; SYMBOL_COOLDOWN_ACTIVE_390_MINUTES=5; PASSED_RANK_LIQUIDITY_DIVERSIFICATION_COOLDOWN_POSITION_CONTROLS=3.
- MSFT selected count=3; re-selection reasons=ENTRY_OR_SOURCE_BLOCKED_BY_FUNNEL=605; SYMBOL_COOLDOWN_ACTIVE_390_MINUTES=30; PORTFOLIO_FULL=6; PASSED_RANK_LIQUIDITY_DIVERSIFICATION_COOLDOWN_POSITION_CONTROLS=3.

# Root Cause

- Prior ordered and filled candidates concentrated before fills, so the fix belongs in portfolio selection controls rather than exit, regime, or alpha logic.
- Repeated same-symbol selections were possible because no 390 minute symbol cooldown was enforced in the audited funnel.
- Same-sector concentration cannot be attributed or capped from current evidence because no sector source was available in candidate_funnel_events.

# Fix Candidate

- Add a deterministic selection engine that groups rows by exact candidate_id only.
- Score every candidate with rank_score, liquidity_score, diversification_score, cooldown_score, and existing_position_penalty.
- Enforce same-symbol weight cap and 390 minute symbol cooldown; report sector cap as source-blocked when sector evidence is unavailable.
- Select AMD when it passes eligibility, cooldown, and symbol cap; drop excess AMZN candidates when cooldown, symbol cap, or portfolio capacity blocks them; re-select MSFT only after cooldown and cap checks pass.

# Acceptance Impact

- implementation_status=PASS_SELECTION_LAYER_IMPLEMENTED.
- Strategy acceptance remains NOT_ACCEPTED because this is a selection-control slice, not a live deployment or strategy acceptance proof.
- Inferred lifecycle matching was not used; matching policy is exact candidate_id grouping only, with no symbol/date/price/time fallback.
- Remaining blocker: sector concentration needs a real sector source before the same-sector cap can be enforced.
