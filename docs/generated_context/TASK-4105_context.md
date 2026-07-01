# Codex Context Bundle

Task: TASK-4105
Profile: DOCS_GOVERNANCE
Generated At: 2026-06-29T02:28:51+00:00
Token Count: 1793
Token Count Mode: approximate
Max Tokens: 22000

---

## Included Files

| Path | Bytes | Tokens | Reason |
|---|---:|---:|---|
| .codex/skills/l5-policy-action/SKILL.md | 644 | 161 | must_include |
| .codex/skills/task-closeout/SKILL.md | 758 | 189 | must_include |
| .codex/skills/ui-storybook-vision/SKILL.md | 708 | 177 | must_include |
| AGENTS.md | 1380 | 345 | must_include |
| docs/reports/task_4105_prompt_regression_eval/report.md | 1130 | 282 | optional_include |
| ops/prompt_regression_cases.yaml | 1076 | 269 | must_include |
| scripts/ops/validate_prompt_regression.py | 1481 | 370 | must_include |

---

## Excluded Files

| Pattern/Path | Reason |
|---|---|
| docs/archive/** | configured exclude |
| node_modules/** | configured exclude |
| data/** | configured exclude |
| db/** | configured exclude |

---

## File: .codex/skills/l5-policy-action/SKILL.md

```md
# L5 Policy Action Skill

Use this skill to translate thesis state into review-only policy actions without broker or execution mutation.

Profile:
- `L5_POLICY_ACTION` in `ops/task_profiles.yaml`

Hard forbidden actions:
- no broker mutation
- no live order
- no real capital
- no auto approval
- no order execution
- Candidate must not convert directly to Buy

Required checks:
- policy action schema
- no broker mutation
- no live order

Required validators:
- `python scripts/ops/validate_task_registry.py`
- `python scripts/ops/validate_task_scope.py --task <TASK_ID>`
- `python scripts/ops/validate_required_artifacts.py --task <TASK_ID>`

```

---

## File: .codex/skills/task-closeout/SKILL.md

```md
# Task Closeout Skill

Use this skill before marking any task complete.

Rules:
- Update `ops/task_registry.yaml`.
- Update `ops/doc_registry.yaml` when documents were created or changed.
- Write or update the task report.
- Write or update the artifact manifest.
- Run required validators.
- Do not mark DONE unless validators pass.
- Keep forbidden paths clean.

Required validators:
- `python scripts/ops/validate_task_registry.py`
- `python scripts/ops/validate_doc_registry.py --soft`
- `python scripts/ops/validate_context_bundle.py --task <TASK_ID>`
- `python scripts/ops/validate_task_scope.py --task <TASK_ID>`
- `python scripts/ops/validate_required_artifacts.py --task <TASK_ID>`
- `python scripts/ops/validate_codex_closeout.py --task <TASK_ID>`

```

---

## File: .codex/skills/ui-storybook-vision/SKILL.md

```md
# UI Storybook Vision Skill

Use this skill for Expo/React Native UI implementation using component-first development, Storybook, screenshots, and visual QA.

Profile:
- `UI_STORYBOOK_VISION` in `ops/task_profiles.yaml`

Rules:
- no one-off components
- Storybook before P0 screens
- screenshot/Vision QA required
- UI is pure rendering
- no business logic in UI
- no promotion calculation in UI
- no risk calculation in UI
- no IA redesign without approval
- no chart-first screens
- no order mutation

Required validators:
- `python scripts/ops/validate_task_registry.py`
- `python scripts/ops/validate_task_scope.py --task <TASK_ID>`
- `python scripts/ops/validate_required_artifacts.py --task <TASK_ID>`

```

---

## File: AGENTS.md

```md
# AGENTS.md

## Project Identity

This repository is a Trading Operating System for observing, verifying, monitoring, and controlling an automated US equity trading engine.

It is not a retail brokerage UI, stock recommendation app, or chart-first app.

## Mandatory Operating Rules

1. Do not start work without a task id.
2. Do not scan the whole repository by default.
3. Read generated context bundles first when they exist.
4. Follow `ops/task_profiles.yaml`.
5. Respect `ops/doc_registry.yaml`.
6. Never treat archived/superseded docs as active SSOT.
7. Do not create new markdown reports outside the relevant task report folder.
8. All task outputs must update `ops/task_registry.yaml`.
9. All new docs must update `ops/doc_registry.yaml`.
10. Run required validators before closeout.

## Trading Safety

- No real capital.
- No live order.
- No broker mutation.
- No paper promotion unless explicitly accepted.
- Missing or stale data is UNKNOWN/BLOCKER, not negative evidence.

## UI Safety

- No one-off components.
- No business logic in UI.
- No IA redesign without approval.
- Storybook before P0 screens.
- Screenshot/Vision QA required for UI screens.

## Completion Definition

A task is complete only when:

- task registry updated
- doc registry updated
- required validators pass
- artifact manifest exists
- no forbidden files touched
- closeout report exists

```

---

## File: docs/reports/task_4105_prompt_regression_eval/report.md

```md
# TASK-4105 Prompt Regression Eval

## Decision Summary

- Verdict: PASS
- Strategy acceptance status: `NOT_ACCEPTED`
- Key metrics: lightweight prompt regression suite added without promptfoo or heavy dependencies
- What changed: `ops/prompt_regression_cases.yaml` and `validate_prompt_regression.py` check core Codex safety and closeout instructions
- Next action: Add more regression cases as new skills are introduced

## Quant Expert Report

- Data source and source readiness: Governance prompts and skill markdown only
- Exact join keys: File paths in regression case config
- Leakage audit: No trading labels or outcomes used
- Split/OOS metrics: Not applicable
- Failure decomposition: Prompt safety rules had no regression guard
- Cost/slippage stress where PnL changed: Not applicable
- Remaining blockers: This is phrase/pattern regression, not semantic LLM eval

## No-Background Decision-Maker Report

TASK-4105 adds a cheap guardrail so future Codex prompt edits do not accidentally remove no-live-order, no-broker-mutation, UI purity, or closeout-gate language.

## Artifact Manifest

See `artifact_manifest.csv`.

```

---

## File: ops/prompt_regression_cases.yaml

```yaml
version: 1
updated_at: "2026-06-29"

cases:
  - id: agents_trading_safety
    path: AGENTS.md
    must_contain:
      - No real capital.
      - No live order.
      - No broker mutation.
      - Missing or stale data is UNKNOWN/BLOCKER
    must_not_match:
      - Candidate\s*[-=]?>\s*Buy

  - id: task_closeout_done_gate
    path: .codex/skills/task-closeout/SKILL.md
    must_contain:
      - Do not mark DONE unless validators pass.
      - Keep forbidden paths clean.
    must_not_match:
      - mark DONE without

  - id: ui_storybook_purity
    path: .codex/skills/ui-storybook-vision/SKILL.md
    must_contain:
      - Storybook before P0 screens
      - UI is pure rendering
      - no business logic in UI
      - no IA redesign without approval
    must_not_match:
      - promotion calculation in UI is allowed

  - id: l5_policy_no_execution
    path: .codex/skills/l5-policy-action/SKILL.md
    must_contain:
      - no broker mutation
      - no live order
      - Candidate must not convert directly to Buy
    must_not_match:
      - Candidate\s*[-=]?>\s*Buy

```

---

## File: scripts/ops/validate_prompt_regression.py

```py
from __future__ import annotations

import argparse
import re
import sys

from ops_common import ROOT, load_yaml, print_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="ops/prompt_regression_cases.yaml")
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        config = load_yaml(args.cases)
    except Exception as exc:
        return print_result("PROMPT REGRESSION VALIDATION", [], [], [str(exc)])

    for case in config.get("cases", []):
        case_id = case.get("id", "unknown")
        path = ROOT / case.get("path", "")
        if not path.exists():
            failures.append(f"{case_id}: path missing: {case.get('path')}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for phrase in case.get("must_contain", []):
            if phrase not in text:
                failures.append(f"{case_id}: missing phrase: {phrase}")
        for pattern in case.get("must_not_match", []):
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                failures.append(f"{case_id}: forbidden pattern matched: {pattern}")
        if not any(failure.startswith(f"{case_id}:") for failure in failures):
            passes.append(case_id)

    return print_result("PROMPT REGRESSION VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())

```
