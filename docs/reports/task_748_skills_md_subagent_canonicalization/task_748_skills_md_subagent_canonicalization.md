# Task748 Skills MD Subagent Canonicalization

## Decision Summary

- Verdict: `PRIMARY_PASS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Scope: skills, operating markdown, subagent routing, and GPT review contracts
- Key metric: 52 skills/MD/subagent rows classified
- Required next action count: 0
- What changed: Skills, GPT review, subagent packets, and operating docs now reference source-code and test-authority maps.
- Next action: Task749 should close the five-pass cleanup loop with a final operating runbook and registry closeout.

Task748 does not change strategy acceptance, deployment readiness, broker truth, or real-capital permission.

## Quant Expert Report

### Data Source And Source Readiness

Input:

- `skills/**`
- `AGENTS.md`
- `docs/ownership/**`
- `docs/operating_system/**`
- `docs/architecture/**`
- `docs/contracts/**`
- Task746 source-code map
- Task747 test-authority map

Task748 uses repository governance metadata only. It does not use market data, PnL, labels, broker fills, or source-event contents.

### Exact Join Keys

No trade/lifecycle joins are used.

The inventory scans explicit files and classifies:

- surface
- role
- owner
- authority level
- GPT mention
- test-authority mention
- source-map mention
- overclaim phrase context
- mojibake/readability hints

### Leakage Audit

No outcome fields are used.

Forbidden inputs not used:

- realized PnL
- return labels
- accepted trade labels
- broker truth rows
- source interpretation scores
- strategy results

### Inventory Results

| Surface | Count |
| --- | ---: |
| operating_system | 17 |
| architecture | 13 |
| skill | 8 |
| ownership | 7 |
| contract | 6 |
| root_agent_rules | 1 |

| Authority Level | Count |
| --- | ---: |
| SUPPORTING_DOC | 30 |
| OPERATING_RULE | 13 |
| CANONICAL_REFERENCE | 9 |

Final result:

```text
required_next_action = 0
```

### Main Changes

- Replaced unreadable `skills/skill.md` with a readable operating skill.
- Replaced unreadable broker lifecycle skill lines with a readable operating skill.
- Added validation authority to subagent packets and handoff templates.
- Added Task747 test-authority boundary to GPT/Chrome packet generation.
- Added Task746 source-code boundary to skill/subagent rules.
- Added `docs/operating_system/project_operating_state.md`.
- Added `docs/architecture/project_status_authority_matrix.md`.
- Added `docs/architecture/skill_md_subagent_canonicalization_map.md`.

### GPT/Chrome Review

GPT/Chrome review was captured successfully in the existing `1. 코딩/투자` tab.

Review status: `review_notes`

Key findings converted into Task748:

- `Inventory complete` can be mistaken for validation complete.
- `Active brain` can be mistaken for canonical or accepted architecture.
- `Governance PASS` can be mistaken for acceptance progress.
- Add a one-page operating state.
- Add a project status authority matrix.

Task748 implemented these findings as repo-native documents.

### Remaining Blockers

- This is still governance cleanup only.
- It does not validate strategy logic.
- It does not promote Task727-742 active brain code.
- It does not certify package code.
- It does not run the full test suite.

## No-Background Decision-Maker Report

### What Happened

We cleaned the project operating instructions.

Codex, GPT, skills, and subagents now have one shared rule:

```text
Passing tests or completing inventory does not mean the strategy is accepted.
```

### Why It Matters

Before this, future work could easily confuse:

- old research tests with current quality gates
- active brain code with accepted architecture
- GPT review with source truth
- governance pass with deployment readiness

Now those boundaries are written into the operating docs and skills.

### Whether This Changes Capital Or Deployment Readiness

No.

Strategy remains `NOT_ACCEPTED`.

Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.

Real capital remains `FORBIDDEN`.

### Plain-Language Next Step

Task749 should close the full 5-pass cleanup loop.

It should create the final runbook and registry closeout so future Codex sessions know exactly where to start.

## Artifact Manifest

### Inputs

| Artifact | Purpose |
| --- | --- |
| `docs/architecture/src_canonicalization_map.md` | Source-code boundary |
| `docs/architecture/test_validation_canonicalization_map.md` | Test-authority boundary |
| `skills/**` | Skill surface |
| `docs/ownership/**` | Subagent and ownership surface |
| `docs/operating_system/**` | Operating markdown surface |
| `docs/contracts/**` | Contract surface |

### Outputs

| Artifact | Rows | Purpose |
| --- | ---: | --- |
| `docs/reports/task_748_skills_md_subagent_canonicalization/task748_skill_md_subagent_inventory.csv` | 52 | File-level skill/MD/subagent classification |
| `docs/reports/task_748_skills_md_subagent_canonicalization/task748_skill_md_subagent_summary.md` | n/a | Summary counts |
| `docs/architecture/skill_md_subagent_canonicalization_map.md` | n/a | Human-readable map |
| `docs/operating_system/project_operating_state.md` | n/a | One-page current project state |
| `docs/architecture/project_status_authority_matrix.md` | n/a | Authority matrix |
| `scripts/skill_md_subagent_inventory.py` | n/a | Reproducible classifier |
| `docs/reports/task_748/gpt_chrome_review_packet.md` | n/a | GPT review packet |

### Validation Commands

```powershell
python scripts/skill_md_subagent_inventory.py
python -m py_compile scripts/skill_md_subagent_inventory.py skills/gpt-chrome-review-subagent/scripts/new_review_packet.py
python scripts/task_artifact_manifest.py --task-dir docs/reports/task_748_skills_md_subagent_canonicalization
python scripts/task_registry_validate.py
python scripts/operating_closeout_validate.py
python scripts/governance_completion_audit.py
```
