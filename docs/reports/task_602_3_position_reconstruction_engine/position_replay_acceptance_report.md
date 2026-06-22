# Problem

T602-3 needed Position Match to be rebuilt from entry fill, exit fill, and lifecycle state using exact IDs only.

# Evidence

- decision_match_rate=1.0, status=PASS
- order_match_rate=0.888889, status=FAIL
- fill_match_rate=1.0, status=PASS
- position_match_rate=0.958333, status=STRETCH
- reconstructed_positions=24
- material_diff_evidence=Missing Exit; Missing Fill Link; Position Lifecycle Error; Missing Exit; Missing Fill Link; Position Lifecycle Error
- inferred_matching_used_flag=0

# Root Cause

Position reconstruction fails when exact exit_fill_id links are absent and passes only when lifecycle rows contain exact CLOSED or PARTIAL_EXIT lineage.

# Fix Candidate

Use the exact-ID reconstruction engine against the current runtime lifecycle and fills tables after T600-3 writes runtime paper exit IDs.

# Acceptance Impact

- decision_status=STRETCH
- Strategy remains NOT_ACCEPTED and deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- No symbol/date/price/time fallback matching was used.
