# Task747 Test Validation Canonicalization

## Decision Summary

- Verdict: `PRIMARY_PASS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Scope: formal `tests/` classification only
- Key metric: 378 formal test rows classified
- What changed: Added a reproducible test validation inventory, authority tags, and PASS implication rules.
- Next action: Task748 must align skills, MD files, and subagent workflows to these validation lanes.

Task747 does not delete, move, rewrite, or run the full test suite.

## Quant Expert Report

### Data Source And Source Readiness

Input:

- `docs/reports/task_745_project_surface_inventory/task745_project_surface_inventory.csv`
- `tasks/task_registry.csv`
- Task746 `src` canonicalization map

Task747 uses repository metadata only. It does not use market data, PnL, labels, source-event contents, or broker fills.

### Exact Join Keys

- Test rows are filtered with `top_level == tests`.
- Task registry lookup uses extracted `Task###` identifiers when present in a path.
- There is no lifecycle, symbol, price, timestamp, or trade join.

### Leakage Audit

No outcome fields are used.

Forbidden inputs not used:

- realized PnL
- return labels
- accepted trade labels
- broker truth rows
- source interpretation scores
- strategy results

### Validation Lane Results

| Lane | Count | Decision |
| --- | ---: | --- |
| historical_task_validation | 224 | Preserve as evidence, not current gate. |
| supporting_task_validation | 39 | Keep with owner lane. |
| fixture_support_not_quality_gate | 27 | Not standalone validation. |
| canonical_package_validation_candidate | 24 | Needs target mapping before official gate. |
| governance_validation | 18 | Useful governance health lane. |
| active_brain_validation | 14 | Research-only brain regression lane. |
| execution_broker_truth_validation | 13 | Separate from fast unit gate. |
| microstructure_data_validation | 12 | Data health lane, not coverage acceptance. |
| frontend_reporting_validation | 7 | Reporting health lane. |

### Authority Tag Results

| Authority Tag | Count |
| --- | ---: |
| EVIDENCE_ONLY | 263 |
| SUPPORT_ONLY | 27 |
| PACKAGE_HEALTH | 24 |
| GOVERNANCE_HEALTH | 18 |
| RESEARCH_ONLY | 14 |
| DATA_HEALTH | 12 |
| EXECUTION_HEALTH | 9 |
| REPORTING_HEALTH | 7 |
| ACCEPTANCE_EVIDENCE_REVIEW | 4 |

### Main Finding

Most tests are not current quality gates.

263 of 378 formal test rows are `EVIDENCE_ONLY`. These preserve historical task behavior but should not be used to claim current package health, strategy acceptance, or deployment readiness.

### Package Test Gap

There are 24 package-health candidates.

Only 4 have a clear target hint now:

- `tests/test_data_quality.py`
- `tests/test_engine_entry_gate_off.py`
- `tests/test_execution_policies.py`
- `tests/test_risk_policies.py`

The remaining 20 need owner mapping to Task746 canonical package candidates before they become official package gates.

### GPT/Chrome Review

GPT/Chrome review was captured successfully in the existing `1. 코딩/투자` tab.

Review status: `review_notes`

Key findings converted into Task747:

- Lane separation is directionally right.
- The missing artifact was a PASS implication / promotion contract.
- Historical task validation must not become a fast quality gate.
- Broker/execution validation must stay separate from fast unit validation.
- Any output saying `All tests passed`, `Validation complete`, `System healthy`, `Production ready`, `Brain validated`, or `Canonical package certified` can overclaim.

Task747 implemented the recommended authority tags and PASS implication fields in the inventory.

### Remaining Blockers

- Package-health candidates still need exact target mapping.
- No full test suite run was performed.
- Test lanes are classification-only until Task748 aligns skills/subagents/MD references.

## No-Background Decision-Maker Report

### What Happened

We sorted the tests.

There are 378 formal test rows. Most are old task evidence, not current project quality gates.

### Why It Matters

Before this, a passing test could be misunderstood as “the system is good.”

Now each test says what a pass means and what it does not mean.

### Whether This Changes Capital Or Deployment Readiness

No.

Strategy remains `NOT_ACCEPTED`.

Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.

Real capital remains `FORBIDDEN`.

### Plain-Language Next Step

Next, clean skills, MD files, and subagent routing.

They must use these test lanes without overclaiming.

## Artifact Manifest

### Inputs

| Artifact | Purpose |
| --- | --- |
| `docs/reports/task_745_project_surface_inventory/task745_project_surface_inventory.csv` | Formal test surface |
| `tasks/task_registry.csv` | Task status lookup |
| `docs/architecture/src_canonicalization_map.md` | Source-code map for target interpretation |

### Outputs

| Artifact | Rows | Purpose |
| --- | ---: | --- |
| `docs/reports/task_747_test_validation_canonicalization/task747_test_validation_inventory.csv` | 378 | Test-level lane and authority classification |
| `docs/reports/task_747_test_validation_canonicalization/task747_test_validation_summary.md` | n/a | Summary counts |
| `docs/architecture/test_validation_canonicalization_map.md` | n/a | Human-readable test validation map |
| `scripts/test_validation_inventory.py` | n/a | Reproducible classifier |
| `docs/reports/task_747/gpt_chrome_review_packet.md` | n/a | GPT review packet |

### Validation Commands

```powershell
python scripts/test_validation_inventory.py
python -m py_compile scripts/test_validation_inventory.py
python scripts/task_artifact_manifest.py --task-dir docs/reports/task_747_test_validation_canonicalization
python scripts/task_registry_validate.py
python scripts/operating_closeout_validate.py
python scripts/governance_completion_audit.py
```
