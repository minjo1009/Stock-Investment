# Task757 Brain Dependency DAG And Supersession Audit

## Decision Summary

- Verdict: `BRAIN_DAG_AND_SUPERSESSION_AUDIT_COMPLETE_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `qa_resolver`
- Owner team: Research Governance
- Reviewer team: Backtest & Simulation Infra
- Decision: Task727-742 are mapped as review-only research artifacts. Task742 is the current pragmatic economic meaning candidate for Task756 reuse, Task741 is superseded for active meaning but retained as denominator audit evidence, and Task729 remains the relation engine candidate that needs a Task761 adapter and Task762 gate repair before reuse.

This task does not promote code, approve a strategy, approve deployment, or permit real capital.

## Quant Expert Report

### Objective

Task757 maps Task727-742 files, reports, tests, current/superseded status, and dependency order before implementation reuse in the Task756 Trader Brain 15-step program.

Success criteria:

```text
One current/superseded map exists; no active brain file is reused without a stated owner and output contract.
```

### Scope Reviewed

- `docs/architecture/brain_layer_map.md`
- `docs/reports/task_756_trader_brain_15_step_program/step_registry.csv`
- `tasks/task_registry.csv` rows for Task727-742
- `src/backtest/build_task727_*.py` through `src/backtest/build_task742_*.py`
- `tests/test_task727_*.py` through `tests/test_task742_*.py`
- Matching Task727-742 reports, decision CSVs, and pass/fail matrices

No `src/`, `tests/`, registry, or non-Task757 documentation files were edited.

### Dependency Finding

The practical reuse chain for Task756 is:

```text
Task731 source routing
-> Task732 circuit context
-> Task733 context quality and operating connection permission
-> Task734 candidate deep dive
-> Task735 generic 8-K classifier repair
-> Task736 semantic translator
-> Task737 candidate bundle modifier attachment
-> Task738 enrichment requirements
-> Task739 resolver workbench
-> Task740 high-priority primitive/resolver completion
-> Task741 denominator meaning audit
-> Task742 pragmatic meaning packets
-> Task761 adapter design
-> Task729 relation engine candidate
```

Task727 and Task728 remain relation-contract ancestors. They define the required object layers and rule families but should not be reused as accepted architecture.

Task730 remains a historical primitive/reality packet builder. Task731 supersedes its blocked-source framing for source routing. Task740 is the stronger current primitive/resolver completion candidate.

### Supersession Finding

Task742 supersedes Task741 for active economic meaning because Task741 converts too many unavailable high-grade sources into hard blockers. Task741 remains useful as denominator and missing-source audit evidence.

Task731 supersedes the Task730 source discard/block framing for L1 routing, but Task730 remains useful as a primitive extraction and Task729 injection precursor audit.

Task735 repairs the generic 8-K classifier assumptions used by Task733/734. Earlier Task733/734 outputs remain historical review evidence, not final operating support.

No Task727-742 file is accepted for trading architecture. Reuse requires the owner, contract, and next validation authority shown in `current_supersession_map.csv`.

### Output Artifacts

- `brain_dependency_dag.csv`: task-level dependency order and reuse gates.
- `current_supersession_map.csv`: current/superseded status, owner, output contract, source file, report, and test for each Task727-742 task.
- `task_757_decision.csv`: compact decision record for this audit.
- `artifact_manifest.csv`: regenerated manifest for Task757 artifacts.

### Validation

Local consistency checks were run after writing artifacts:

```text
python -c "import csv, pathlib; base=pathlib.Path('docs/reports/task_757_brain_dependency_dag_supersession'); files=['brain_dependency_dag.csv','current_supersession_map.csv','task_757_decision.csv']; [list(csv.DictReader((base/f).open(newline='',encoding='utf-8-sig'))) for f in files]; print('csv_ok')"
python -c "import csv, pathlib; base=pathlib.Path('docs/reports/task_757_brain_dependency_dag_supersession'); dag=list(csv.DictReader((base/'brain_dependency_dag.csv').open(newline='',encoding='utf-8-sig'))); sup=list(csv.DictReader((base/'current_supersession_map.csv').open(newline='',encoding='utf-8-sig'))); assert len(dag) >= 16; assert len(sup) == 16; assert any(r['task_id']=='Task742' and r['reuse_status']=='current_review_only_candidate' for r in sup); assert any(r['task_id']=='Task741' and r['reuse_status']=='superseded_by_Task742_for_active_meaning' for r in sup); assert any(r['task_id']=='Task729' and 'Task761' in r['retained_for'] for r in sup); assert all(r['backtest_permission']=='FAIL' for r in sup); print('task757_consistency_ok')"
python scripts/trader_brain_program_validate.py
```

Validation authority: research-only governance validation.

One initial local assertion failed because the check looked for `Task761` in `known_blocker_or_gate` while the CSV stores that dependency in `retained_for`. The corrected consistency check passed.

## No-Background Decision-Maker Report

1. 완료: Task727-742 연결 순서를 CSV로 만들었습니다.
2. 결론: Task742만 현재 경제 의미 후보입니다.
3. 보존: Task741은 폐기하지 않습니다. 분모 감사 자료입니다.
4. 주의: Task729는 관계 엔진 후보입니다. 바로 재사용하면 안 됩니다.
5. 다음: Task761에서 Task742를 Task729로 연결하는 어댑터 계약이 필요합니다.

## Artifact Manifest

| Artifact | Class | Purpose |
| --- | --- | --- |
| `task_757_brain_dependency_dag_supersession.md` | report | Task757 decision and expert report |
| `brain_dependency_dag.csv` | audit_csv | Task727-742 dependency order and reuse gates |
| `current_supersession_map.csv` | audit_csv | Current/superseded status and output contract map |
| `task_757_decision.csv` | decision | Compact research-only decision record |
| `artifact_manifest.csv` | manifest | File size and hash manifest |

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
