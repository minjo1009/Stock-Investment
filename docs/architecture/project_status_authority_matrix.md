# Project Status Authority Matrix

## Purpose

This matrix prevents project-management cleanup from being mistaken for trading acceptance.

## Authority Matrix

| Artifact Or Event | May Update Docs? | May Update Registry? | May Change Strategy Acceptance? | May Change Deployment Readiness? | May Permit Real Capital? |
| --- | --- | --- | --- | --- | --- |
| Skill or MD cleanup | Yes | Yes, if task row is needed | No | No | No |
| Surface inventory complete | Yes | Yes, as diagnostic task | No | No | No |
| Source-code classification complete | Yes | Yes, as diagnostic task | No | No | No |
| Test classification complete | Yes | Yes, as diagnostic task | No | No | No |
| `PACKAGE_HEALTH` pass | Yes | Maybe, as validation evidence | No | No | No |
| `GOVERNANCE_HEALTH` pass | Yes | Maybe, as validation evidence | No | No | No |
| `RESEARCH_ONLY` pass | Yes | Maybe, as research evidence | No | No | No |
| `EXECUTION_HEALTH` pass | Yes | Maybe, as execution evidence | No | No | No |
| `ACCEPTANCE_EVIDENCE_REVIEW` pass | Yes | Maybe, as reviewable evidence | No by itself | No by itself | No |
| GPT/Chrome review captured | Yes | Maybe, as review notes | No | No | No |
| Broker-truth SELL evidence accepted | Yes | Yes, through owner-reviewed task | Only through acceptance contract | Only through deployment contract | No by itself |
| Full strategy acceptance contract pass | Yes | Yes | Yes, if registry says so | No by itself | No |
| Deployment acceptance contract pass | Yes | Yes | No by itself | Yes, if registry says so | Only if real-capital policy also permits |

## Meaning Rules

| Phrase | Allowed Meaning | Forbidden Meaning |
| --- | --- | --- |
| Inventory complete | No structural follow-up found in that inventory | Validation complete |
| Validation passed | The named lane did not detect a regression | Strategy accepted |
| Governance healthy | Governance checks passed | Trading system healthy |
| Active brain | Current research path | Accepted trading architecture |
| Canonical candidate | Review target | Production-ready code |
| GPT reviewed | External critique captured | Fact certified |

## Required Closeout Language

Every cleanup task should explicitly state:

```text
This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
```
