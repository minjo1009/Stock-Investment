# Sublead Onboarding

Last updated: 2026-05-21

## How New Subleads Start

Every new sublead receives a narrow responsibility, not a blank mandate. The lead remains accountable for final acceptance.

## Required First Day Checklist

1. Read `AGENTS.md`.
2. Read `docs/ownership/team_charter.md`.
3. Read the relevant section of `docs/ownership/module_ownership_map.md`.
4. Identify the current canonical or active task rows in `tasks/task_registry.csv`.
5. Open the listed reports before touching code.
6. Run or record the validation command before claiming anything is complete.
7. If GPT/Chrome is used, create a bounded review packet with `skills/gpt-chrome-review-subagent/SKILL.md` and record the output only as `review_notes` or `ideation_notes`.

## Training Rules

- Do not create a new folder convention without 중훈 approval.
- Do not create strategy claims without 필수 approval.
- Do not treat missing labels as negative outcomes.
- Do not infer lifecycle identity by symbol/date/price/time proximity.
- Do not let frontend read raw task CSVs directly.
- Do not let Slack delivery status imply trade success.
- Do not describe diagnostic backtests as deployable.

## Handoff Packet Template

```text
Sublead:
Lead:
Objective:
Read Scope:
Write Scope:
Current Evidence:
Known Blockers:
Forbidden Actions:
Validation Command:
Expected Artifact:
Reviewer:
GPT/Chrome Review:
```

## Acceptance

A sublead task is accepted only when the lead can point to:

- exact files changed or reviewed
- exact artifact/report location
- validation command and result
- remaining blocker or next action
- GPT/Chrome review packet and notes when external GPT review influenced the task
