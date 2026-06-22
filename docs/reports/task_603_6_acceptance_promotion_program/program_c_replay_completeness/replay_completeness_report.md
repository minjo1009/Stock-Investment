# Problem

Program C replay promotion needs one score that weighs Decision, Order, Fill, Position, and Lineage at 20 percent each, without strategy, entry, universe, alpha, or real-capital changes.

# Evidence

- replay_completeness_score=0.791667
- decision_status=FAIL
- Decision Match: matched=965/965 match_rate=1.0 weight=0.2 status=PASS
- Order Match: matched=54/54 match_rate=1.0 weight=0.2 status=PASS
- Fill Match: matched=48/48 match_rate=1.0 weight=0.2 status=PASS
- Position Match: matched=23/24 match_rate=0.958333 weight=0.2 status=FAIL
- Lineage Match: matched=0/23 match_rate=0.0 weight=0.2 status=FAIL
- inferred_matching_used_flag=0
- real_capital_used_flag=0

# Root Cause

Replay completeness is blocked when any exact replay surface is below threshold or when broker trade lineage evidence is absent or incomplete. Missing sources are reported as source blocks and are not approximated.

# Fix Candidate

Keep using exact replay validation for Decision, Order, Fill, and Position, then add broker_fill_id-linked broker_trade_lineage rows or an approved Program A lineage summary before promotion review.

# Acceptance Impact

- Acceptance rule: PASS iff replay_completeness_score > 0.99 and position_match_rate > 0.99.
- Current replay acceptance status: FAIL.
- Strategy acceptance remains NOT_ACCEPTED and deployment readiness remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- No symbol/date/price/time proximity fallback was used.
