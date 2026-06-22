# Problem

Replay promotion needs an explicit gap breakdown so missing lifecycle or lineage evidence cannot be hidden inside a blended score.

# Evidence

- Position Match: MATCH_GAP gap_rows=1 evidence=Position Match matched 23/24; match_rate=0.958333
- Lineage Match: MATCH_GAP gap_rows=23 evidence=Lineage Match matched 0/23; match_rate=0.0

# Root Cause

- broker trade lineage source is missing or lacks complete broker_fill_id linkage
- position lifecycle lacks exact entry/exit fill closure for replay

# Fix Candidate

- provide broker_fill_id-linked broker_trade_lineage rows or Program A lineage summary with approved lineage rate evidence
- write exact CLOSED or PARTIAL_EXIT lifecycle rows with entry_fill_id and exit_fill_id

# Acceptance Impact

- replay_completeness_score=0.791667
- position_match_rate=0.958333
- replay_acceptance_status=FAIL
- Acceptance remains blocked unless replay_completeness_score > 0.99 and position_match_rate > 0.99.
- Missing raw sources are reported, not approximated.
