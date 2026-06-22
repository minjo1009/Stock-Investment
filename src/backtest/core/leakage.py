from __future__ import annotations

import pandas as pd


DEFAULT_BLOCKED_FIELDS = {
    "failure_group",
    "lifecycle_outcome_class",
    "return_from_entry",
    "net_return_from_entry",
    "add_flag",
    "scale_flag",
    "reduce_flag",
    "exit_flag",
    "exit_ts",
    "event_path",
    "win_flag",
    "add_scale_success_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
}


def assignment_leakage_audit(assignment_fields: list[str], *, inferred_matching_used_flag: int = 0) -> pd.DataFrame:
    blocked = sorted(set(assignment_fields) & DEFAULT_BLOCKED_FIELDS)
    return pd.DataFrame(
        [
            {
                "assignment_fields": "|".join(sorted(assignment_fields)),
                "blocked_outcome_field_used_count": len(blocked),
                "blocked_outcome_fields": "|".join(blocked),
                "label_used_in_assignment_flag": int(bool(blocked)),
                "inferred_lifecycle_matching_used_flag": int(inferred_matching_used_flag),
                "leakage_pass_flag": int(not blocked and not inferred_matching_used_flag),
            }
        ]
    )
