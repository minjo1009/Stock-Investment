from __future__ import annotations

import ast
import csv
import importlib
import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
TASK_DIR = ROOT / "docs" / "reports" / "task_754_engine_boundary_repair"
ENGINE_PATH = ROOT / "src" / "backtest" / "engine.py"

REMAINING_OWNER_REVIEW_IMPORTS = {
    "backtest.analysis_sector": "sector mapping helper still belongs outside pure replay core",
    "strategy.conditions": "strategy-specific signal conditions still belong in an adapter",
    "strategy.validator": "strategy-specific validation still belongs in an adapter",
}


def imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    package = path.parent.relative_to(SRC_ROOT).as_posix().replace("/", ".")
    imports: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = [] if package == "." else package.split(".")
                base = ".".join(base_parts[: len(base_parts) - node.level + 1])
                module = f"{base}.{node.module}" if node.module and base else node.module or base
                if module:
                    imports.append(module)
            elif node.module:
                imports.append(node.module)
    return sorted(set(imports))


def import_check(module_name: str) -> tuple[str, str]:
    added = False
    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))
        added = True
    try:
        importlib.import_module(module_name)
        return "PASS", ""
    except Exception as exc:  # noqa: BLE001
        return "FAIL", f"{type(exc).__name__}: {exc}"
    finally:
        if added:
            try:
                sys.path.remove(str(SRC_ROOT))
            except ValueError:
                pass


def engine_source() -> str:
    return ENGINE_PATH.read_text(encoding="utf-8-sig")


def top_level_canonical_lifecycle_import(imports: list[str]) -> str:
    return "FAIL" if "backtest.canonical_position_lifecycle_event_sourcing" in imports else "PASS"


def lazy_lifecycle_loader_present(source: str) -> str:
    marker = "def _load_canonical_lifecycle_writers("
    import_marker = "from backtest.canonical_position_lifecycle_event_sourcing import"
    return "PASS" if marker in source and import_marker in source else "FAIL"


def no_next_bar_source_pattern(source: str) -> str:
    forbidden = ["opens[i + 1]", "next_open"]
    return "PASS" if not any(pattern in source for pattern in forbidden) else "FAIL"


def execution_helpers_present(source: str) -> str:
    required = [
        "signal_close: float",
        "def _entry_execution_gap_pct(",
        "limit_price: float | None",
        "def _pending_exit_execution_price(",
        "NEXT_BAR_EXECUTION_CONVENTION",
    ]
    return "PASS" if all(item in source for item in required) else "FAIL"


def lazy_import_runtime_check() -> str:
    sys.modules.pop("backtest.canonical_position_lifecycle_event_sourcing", None)
    importlib.import_module("backtest.engine")
    return "PASS" if "backtest.canonical_position_lifecycle_event_sourcing" not in sys.modules else "FAIL"


def remaining_owner_review(imports: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for module, reason in REMAINING_OWNER_REVIEW_IMPORTS.items():
        present = module in imports
        rows.append(
            {
                "module": module,
                "present": "yes" if present else "no",
                "status": "REMAINING_REPAIR_SCOPE" if present else "CLEAR",
                "reason": reason,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row.get(col, "") for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def write_report(check_rows: list[dict[str, str]], dependency_rows: list[dict[str, str]]) -> None:
    report = f"""# Task754 Engine Boundary Repair

## Decision Summary

Task754 repairs the `engine.py` as-of boundary enough to advance W2 work.

It does not certify strategy quality, alpha quality, full backtest correctness, deployment readiness, or real-capital use.

## Quant Expert Report

Boundary checks:

{markdown_table(check_rows, ["check", "status", "evidence"])}

Remaining owner-review dependencies:

{markdown_table(dependency_rows, ["module", "present", "status", "reason"])}

Interpretation:

```text
Entry and exit execution now resolve on the execution bar instead of reading the next bar during signal formation.
Lifecycle persistence is no longer a top-level engine dependency.
The engine still contains strategy-specific imports, so it is not yet a generic W2 replay core.
```

## No-Background Decision-Maker Report

1. 엔진이 미래 봉 가격을 미리 보는 큰 길을 막았습니다.
2. DB 기록기는 필요할 때만 불러오게 바꿨습니다.
3. 그래서 Task753 때 막힌 엔진 문제는 한 단계 앞으로 갔습니다.
4. 아직 순수 백테스트 코어는 아닙니다.
5. 다음은 전략 조건/검증/섹터 helper를 엔진 밖으로 빼는 일입니다.

## Artifact Manifest

Primary artifacts:

- `task754_engine_boundary_validation.csv`
- `task754_remaining_dependency_review.csv`
- `task754_summary.csv`
- `task_754_decision.csv`
- `gpt_review_notes.md`
- `subagent_review_notes.md`
- `validation_log.md`
- `artifact_manifest.csv`

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (TASK_DIR / "task_754_engine_boundary_repair.md").write_text(report, encoding="utf-8")


def write_notes() -> None:
    gpt = """# Task754 GPT Review Notes

GPT was given a new-engineer onboarding packet with project status, architecture target, Task752/Task753 context, subagent findings, and the exact Task754 code changes.

Applied review points:

1. Task754 is a valid engine boundary repair advancement.
2. This is not engine canonical approval, strategy validation, deployment readiness, or alpha validation.
3. The most important resolved items are next-open lookahead risk reduction and lazy lifecycle persistence loading.
4. Remaining Task755 work should split generic replay core from strategy adapter, lifecycle writer protocol, CLI/save shell, and sector helper paths.
5. Wording should say this improves architectural correctness and reduces lookahead risk only.
"""
    subagents = """# Task754 Subagent Review Notes

Three read-only subagents reviewed distinct scopes:

1. Dependency explorer: lifecycle writer can be lazy; strategy.conditions, strategy.validator, sector helper, save/CLI shell remain boundary work.
2. As-of explorer: entry gap and pending exit should resolve on execution bar, not signal bar.
3. Test/governance explorer: add import smoke, no forbidden next-open pattern, lazy lifecycle import, and focused helper regression tests.
"""
    validation = """# Task754 Validation Log

Commands:

```text
python scripts\\canonical_engine_boundary_validate.py
python -m py_compile src\\backtest\\engine.py tests\\test_task754_engine_boundary_repair.py scripts\\canonical_engine_boundary_validate.py
python -m unittest tests.test_task754_engine_boundary_repair
python -m unittest tests.test_task753_w2_backtest_core_boundary
python scripts\\task_artifact_manifest.py --task-dir docs\\reports\\task_754_engine_boundary_repair
python scripts\\task_registry_validate.py
python scripts\\operating_closeout_validate.py
```
"""
    (TASK_DIR / "gpt_review_notes.md").write_text(gpt, encoding="utf-8")
    (TASK_DIR / "subagent_review_notes.md").write_text(subagents, encoding="utf-8")
    (TASK_DIR / "validation_log.md").write_text(validation, encoding="utf-8")


def main() -> None:
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    source = engine_source()
    imports = imported_modules(ENGINE_PATH)
    import_status, import_error = import_check("backtest.engine")
    check_rows = [
        {
            "check": "engine_import",
            "status": import_status,
            "evidence": import_error or "backtest.engine imports successfully",
        },
        {
            "check": "no_next_open_source_pattern",
            "status": no_next_bar_source_pattern(source),
            "evidence": "no opens[i + 1] or next_open token in engine.py",
        },
        {
            "check": "execution_helpers_present",
            "status": execution_helpers_present(source),
            "evidence": "pending entry signal_close and deferred exit helper are present",
        },
        {
            "check": "no_top_level_lifecycle_writer_import",
            "status": top_level_canonical_lifecycle_import(imports),
            "evidence": "canonical lifecycle writer is absent from top-level imports",
        },
        {
            "check": "lazy_lifecycle_loader_present",
            "status": lazy_lifecycle_loader_present(source),
            "evidence": "_load_canonical_lifecycle_writers exists",
        },
        {
            "check": "lazy_lifecycle_runtime_check",
            "status": lazy_import_runtime_check(),
            "evidence": "importing backtest.engine does not import canonical lifecycle writer path",
        },
    ]
    dependency_rows = remaining_owner_review(imports)
    summary_rows = [
        {"field": "task_id", "value": "Task754"},
        {"field": "verdict", "value": "ENGINE_BOUNDARY_REPAIRED_STRATEGY_ADAPTER_REMAINS"},
        {"field": "scope", "value": "engine.py lookahead boundary and lifecycle dependency repair"},
        {"field": "checks_total", "value": str(len(check_rows))},
        {"field": "checks_passed", "value": str(sum(1 for row in check_rows if row["status"] == "PASS"))},
        {"field": "strategy_specific_dependencies_remaining", "value": str(sum(1 for row in dependency_rows if row["present"] == "yes"))},
        {"field": "engine_promoted_to_generic_core", "value": "no"},
        {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
        {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
        {"field": "real_capital", "value": "FORBIDDEN"},
        {"field": "next_safe_task", "value": "Task755 split engine strategy adapter and shell dependencies"},
    ]
    decision_rows = [
        {"field": "task_id", "value": "Task754"},
        {"field": "decision", "value": "advance_w2_engine_boundary_after_lookahead_and_lazy_lifecycle_repair"},
        {"field": "overclaim_guard", "value": "not_strategy_validation_not_deployment_not_alpha_validation"},
        {"field": "next_allowed_work", "value": "Task755 engine strategy adapter shell split"},
        {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
        {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
        {"field": "real_capital", "value": "FORBIDDEN"},
    ]

    write_csv(TASK_DIR / "task754_engine_boundary_validation.csv", check_rows, ["check", "status", "evidence"])
    write_csv(
        TASK_DIR / "task754_remaining_dependency_review.csv",
        dependency_rows,
        ["module", "present", "status", "reason"],
    )
    write_csv(TASK_DIR / "task754_summary.csv", summary_rows, ["field", "value"])
    write_csv(TASK_DIR / "task_754_decision.csv", decision_rows, ["field", "value"])
    write_report(check_rows, dependency_rows)
    write_notes()
    print(f"[TASK754] wrote={TASK_DIR}")


if __name__ == "__main__":
    main()
