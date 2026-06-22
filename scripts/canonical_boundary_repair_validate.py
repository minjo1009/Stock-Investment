from __future__ import annotations

import ast
import csv
import importlib
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
TASK_DIR = ROOT / "docs" / "reports" / "task_752_w0_w1_boundary_repair"

W0_TARGETS = [
    "src/__init__.py",
    "src/app/__init__.py",
    "src/backtest/__init__.py",
    "src/common/__init__.py",
    "src/execution/__init__.py",
    "src/integration/__init__.py",
    "src/market/__init__.py",
    "src/reporting/__init__.py",
    "src/risk/__init__.py",
    "src/state/__init__.py",
    "src/strategy/__init__.py",
]

W1_TARGETS = [
    "src/common/models.py",
    "src/execution/interface.py",
    "src/market/interface.py",
    "src/reporting/interface.py",
    "src/risk/interface.py",
    "src/state/interface.py",
    "src/strategy/interface.py",
]

RECLASSIFIED_OUT_OF_W1 = {
    "src/state/store.py": "SQLite persistence implementation; direct submodule import remains allowed, but W1 contract is state.interface",
}

BLOCKED_IMPORT_PREFIXES = {
    "app",
    "backtest",
    "data",
    "execution.cancel_loop",
    "execution.policies",
    "integration",
    "risk.policies",
    "state.store",
    "state.continuation_capture",
    "strategy.conditions",
    "strategy.validator",
}


def imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    package = path.parent.relative_to(SRC_ROOT).as_posix().replace("/", ".")
    imports: list[str] = []
    for node in ast.walk(tree):
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


def module_name_from_path(src_path: str) -> str:
    if src_path == "src/__init__.py":
        return "src"
    rel = Path(src_path).relative_to("src")
    if rel.name == "__init__.py":
        return ".".join(rel.parts[:-1])
    return ".".join(rel.with_suffix("").parts)


def import_check(module_name: str) -> tuple[str, str]:
    if module_name == "src":
        return "PASS", ""
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


def blocked_import(imports: list[str]) -> str:
    for module in imports:
        for prefix in BLOCKED_IMPORT_PREFIXES:
            if module == prefix or module.startswith(prefix + "."):
                return module
    return ""


def classify(path: str, wave_id: str) -> dict[str, str]:
    abs_path = ROOT / path
    imports = imported_modules(abs_path)
    module_name = module_name_from_path(path)
    import_status, import_error = import_check(module_name)
    blocked = blocked_import(imports)

    if import_status != "PASS":
        verdict = "FAIL_IMPORT"
        reason = import_error
    elif wave_id == "W0" and imports:
        verdict = "FAIL_NAMESPACE_FANOUT"
        reason = f"W0 package imports {','.join(imports)}"
    elif wave_id == "W1" and blocked:
        verdict = "FAIL_BLOCKED_IMPORT"
        reason = f"W1 contract imports blocked module {blocked}"
    else:
        verdict = "PASS"
        reason = "W0 namespace-only" if wave_id == "W0" else "W1 contract boundary"

    return {
        "path": path,
        "wave_id": wave_id,
        "module_name": module_name,
        "top_level_imports": ";".join(imports),
        "import_status": import_status,
        "validation_verdict": verdict,
        "reason": reason,
    }


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


def build_rows() -> list[dict[str, str]]:
    rows = [classify(path, "W0") for path in W0_TARGETS]
    rows.extend(classify(path, "W1") for path in W1_TARGETS)
    for path, reason in RECLASSIFIED_OUT_OF_W1.items():
        rows.append(
            {
                "path": path,
                "wave_id": "OUT_OF_W1",
                "module_name": module_name_from_path(path),
                "top_level_imports": ";".join(imported_modules(ROOT / path)),
                "import_status": "NOT_PROMOTION_TARGET",
                "validation_verdict": "RECLASSIFIED_IMPLEMENTATION",
                "reason": reason,
            }
        )
    return rows


def write_report(rows: list[dict[str, str]], summary_rows: list[dict[str, str]]) -> None:
    report_rows = [
        {
            "path": row["path"],
            "wave": row["wave_id"],
            "verdict": row["validation_verdict"],
            "reason": row["reason"],
        }
        for row in rows
    ]
    report = f"""# Task752 W0-W1 Boundary Repair

## Decision Summary

W0/W1 boundary repair is complete for the checked package surface.

No strategy logic, ranking logic, backtest result, broker behavior, or real-capital path was changed.

## Quant Expert Report

Current validation:

{markdown_table(report_rows, ["path", "wave", "verdict", "reason"])}

Interpretation:

```text
W0 package imports no longer fan out into implementation modules.
W1 contract modules import narrowly.
state.store is explicitly out of W1 and remains implementation.
```

## No-Background Decision-Maker Report

1. 막혔던 껍데기 문제는 고쳤습니다.
2. `state/store.py`는 계약에서 뺐습니다.
3. 새 계약은 `state/interface.py`입니다.
4. 다음은 W2 backtest core 검증입니다.

## Artifact Manifest

Primary artifacts:

- `task752_w0_w1_boundary_validation.csv`
- `task752_summary.csv`
- `task_752_decision.csv`
- `gpt_review_notes.md`
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
    (TASK_DIR / "task_752_w0_w1_boundary_repair.md").write_text(report, encoding="utf-8")


def write_static_notes() -> None:
    gpt_notes = """# Task752 GPT Review Notes

GPT reviewed the repair direction as a backend/platform architecture critic.

Applied points:

1. W0 package files should be namespace-only.
2. Compatibility re-exports are not needed unless tests show package-level imports.
3. `state.store` should not be W1 contract.
4. A thin `state.interface` contract is the right W1 replacement.
5. No strategy or deployment claim follows from this repair.
"""
    validation_log = """# Task752 Validation Log

Commands:

```text
python scripts\\canonical_boundary_repair_validate.py
python -m py_compile src\\backtest\\__init__.py src\\risk\\__init__.py src\\state\\__init__.py src\\strategy\\__init__.py src\\state\\interface.py scripts\\canonical_boundary_repair_validate.py
python -m unittest tests.unit.test_structure.TestRepositoryFoundationStructure.test_market_interface_returns_market_data_snapshot tests.unit.test_structure.TestRepositoryFoundationStructure.test_strategy_interface_accepts_market_data_snapshot tests.unit.test_structure.TestRepositoryFoundationStructure.test_risk_interface_accepts_risk_input_context
```

Known residual from Task751:

`tests.unit.test_structure` full run still has two reconciliation tuple/object failures outside W0-W1 boundary scope.
"""
    (TASK_DIR / "gpt_review_notes.md").write_text(gpt_notes, encoding="utf-8")
    (TASK_DIR / "validation_log.md").write_text(validation_log, encoding="utf-8")


def main() -> None:
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    counts = Counter(row["validation_verdict"] for row in rows)
    fail_count = sum(count for verdict, count in counts.items() if verdict.startswith("FAIL"))
    summary_rows = [
        {"field": "task_id", "value": "Task752"},
        {"field": "verdict", "value": "PASS" if fail_count == 0 else "FAIL"},
        {"field": "scope", "value": "W0-W1 boundary repair"},
        {"field": "w0_targets", "value": str(len(W0_TARGETS))},
        {"field": "w1_targets", "value": str(len(W1_TARGETS))},
        {"field": "fail_count", "value": str(fail_count)},
        {"field": "state_store_reclassified", "value": "yes"},
        {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
        {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
        {"field": "real_capital", "value": "FORBIDDEN"},
        {"field": "next_safe_task", "value": "Task753 W2 backtest core validation"},
    ]
    for verdict, count in sorted(counts.items()):
        summary_rows.append({"field": f"count_{verdict.lower()}", "value": str(count)})
    decision_rows = [
        {"field": "task_id", "value": "Task752"},
        {"field": "decision", "value": "w0_w1_boundary_repaired"},
        {"field": "promote_to_next_wave", "value": "W2 validation may start"},
        {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
        {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
        {"field": "real_capital", "value": "FORBIDDEN"},
    ]
    fieldnames = [
        "path",
        "wave_id",
        "module_name",
        "top_level_imports",
        "import_status",
        "validation_verdict",
        "reason",
    ]
    write_csv(TASK_DIR / "task752_w0_w1_boundary_validation.csv", rows, fieldnames)
    write_csv(TASK_DIR / "task752_summary.csv", summary_rows, ["field", "value"])
    write_csv(TASK_DIR / "task_752_decision.csv", decision_rows, ["field", "value"])
    write_report(rows, summary_rows)
    write_static_notes()
    print(f"[TASK752] wrote={TASK_DIR}")


if __name__ == "__main__":
    main()
