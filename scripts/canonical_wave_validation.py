from __future__ import annotations

import ast
import csv
import importlib
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
TASK750_PLAN = (
    ROOT
    / "docs"
    / "reports"
    / "task_750_canonical_package_extraction_plan"
    / "task750_canonical_package_plan.csv"
)
TASK_DIR = ROOT / "docs" / "reports" / "task_751_w0_w1_extraction_validation"

ALLOWED_W1_INTERNAL_IMPORTS = {
    "common",
    "common.models",
    "typing",
    "__future__",
}

BLOCKED_IMPORT_PREFIXES = {
    "app",
    "backtest",
    "data",
    "execution.cancel_loop",
    "execution.policies",
    "integration",
    "risk.policies",
    "state.continuation_capture",
    "strategy.conditions",
    "strategy.validator",
}

W0_NAMESPACE_ONLY_ALLOWLIST = {
    "src/__init__.py",
    "src/app/__init__.py",
    "src/common/__init__.py",
    "src/execution/__init__.py",
    "src/integration/__init__.py",
    "src/market/__init__.py",
    "src/reporting/__init__.py",
}

W0_RECLASSIFY_REQUIRED = {
    "src/backtest/__init__.py": "imports W2 backtest.models",
    "src/risk/__init__.py": "imports concrete risk implementation modules",
    "src/state/__init__.py": "exports concrete SQLite state.store implementation functions",
    "src/strategy/__init__.py": "imports strategy.conditions and backtest.indicators transitively",
}

W1_RECLASSIFY_REQUIRED = {
    "src/state/store.py": "large SQLite persistence implementation, not a pure contract/interface",
}

TASK752_W1_ADDITIONS = {
    "src/state/interface.py": {
        "wave_id": "W1",
        "path": "src/state/interface.py",
    }
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def module_name_from_path(src_path: str) -> str:
    if src_path == "src/__init__.py":
        return "src"
    rel = Path(src_path).relative_to("src")
    if rel.name == "__init__.py":
        return ".".join(rel.parts[:-1])
    return ".".join(rel.with_suffix("").parts)


def imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    imports: list[str] = []
    package = path.parent.relative_to(SRC_ROOT).as_posix().replace("/", ".")
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


def has_blocked_import(imports: list[str]) -> tuple[bool, str]:
    for module in imports:
        for prefix in BLOCKED_IMPORT_PREFIXES:
            if module == prefix or module.startswith(prefix + "."):
                return True, module
    return False, ""


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
    except Exception as exc:  # noqa: BLE001 - diagnostic artifact needs exact failure text.
        return "FAIL", f"{type(exc).__name__}: {exc}"
    finally:
        if added:
            try:
                sys.path.remove(str(SRC_ROOT))
            except ValueError:
                pass


def classify_row(row: dict[str, str]) -> dict[str, str]:
    path = row["path"]
    abs_path = ROOT / path
    imports = imported_modules(abs_path)
    module_name = module_name_from_path(path)
    import_status, import_error = import_check(module_name)
    blocked_import, blocked_module = has_blocked_import(imports)

    if row["wave_id"] == "W0":
        if path in W0_RECLASSIFY_REQUIRED:
            verdict = "BLOCK_RECLASSIFY_REQUIRED"
            reason = W0_RECLASSIFY_REQUIRED[path]
        elif path in W0_NAMESPACE_ONLY_ALLOWLIST and not imports:
            verdict = "PASS_NAMESPACE_ONLY"
            reason = "namespace-only package marker"
        elif path in W0_NAMESPACE_ONLY_ALLOWLIST:
            verdict = "WARN_IMPORT_FANOUT"
            reason = "allowlisted W0 package has import fan-out"
        else:
            verdict = "BLOCK_UNMAPPED_W0"
            reason = "W0 path lacks namespace-only evidence"
    elif path in W1_RECLASSIFY_REQUIRED:
        verdict = "BLOCK_RECLASSIFY_REQUIRED"
        reason = W1_RECLASSIFY_REQUIRED[path]
    elif blocked_import:
        verdict = "BLOCK_FORBIDDEN_IMPORT"
        reason = f"imports blocked module {blocked_module}"
    elif import_status == "PASS":
        verdict = "CONDITIONAL_PASS_CONTRACT_ONLY"
        reason = "contract/interface import graph is narrow enough for W1 candidate status"
    else:
        verdict = "BLOCK_IMPORT_FAIL"
        reason = import_error

    if import_status != "PASS" and verdict.startswith("PASS"):
        verdict = "BLOCK_IMPORT_FAIL"
        reason = import_error

    return {
        "path": path,
        "wave_id": row["wave_id"],
        "module_name": module_name,
        "import_status": import_status,
        "import_error": import_error,
        "top_level_imports": ";".join(imports),
        "blocked_import_detected": "yes" if blocked_import else "no",
        "blocked_import_module": blocked_module,
        "validation_verdict": verdict,
        "reason": reason,
        "strategy_acceptance_effect": "none",
        "deployment_effect": "none",
        "real_capital_effect": "none",
    }


def build_validation() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    plan_rows = [row for row in read_csv(TASK750_PLAN) if row["wave_id"] in {"W0", "W1"}]
    existing_paths = {row["path"] for row in plan_rows}
    for path, row in TASK752_W1_ADDITIONS.items():
        if path not in existing_paths and (ROOT / path).exists():
            plan_rows.append(row)
    rows = [classify_row(row) for row in plan_rows]
    counts = Counter(row["validation_verdict"] for row in rows)
    blocked = sum(1 for row in rows if row["validation_verdict"].startswith("BLOCK"))
    conditional_pass = sum(1 for row in rows if row["validation_verdict"].startswith("CONDITIONAL_PASS"))
    namespace_pass = sum(1 for row in rows if row["validation_verdict"].startswith("PASS_NAMESPACE"))
    decision_verdict = "PARTIAL_PASS_WITH_RECLASSIFICATION_BLOCKERS" if blocked else "PRIMARY_PASS"
    summary_rows = [
        {"field": "task_id", "value": "Task751"},
        {"field": "verdict", "value": decision_verdict},
        {"field": "scope", "value": "W0-W1 extraction validation only"},
        {"field": "targets_checked", "value": str(len(rows))},
        {"field": "namespace_pass", "value": str(namespace_pass)},
        {"field": "conditional_contract_pass", "value": str(conditional_pass)},
        {"field": "blocked_or_reclassify_required", "value": str(blocked)},
        {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
        {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
        {"field": "real_capital", "value": "FORBIDDEN"},
        {"field": "next_safe_task", "value": "Task752 W0-W1 package init and state boundary repair plan"},
    ]
    for verdict, count in sorted(counts.items()):
        summary_rows.append({"field": f"count_{verdict.lower()}", "value": str(count)})

    decision_rows = [
        {"field": "task_id", "value": "Task751"},
        {"field": "decision", "value": decision_verdict},
        {"field": "promote_w0_w1_now", "value": "no"},
        {"field": "reason", "value": "W0 contains non-namespace fan-out and state/store is implementation not contract"},
        {"field": "allowed_next_work", "value": "repair W0 package init fan-out and split state store contract from implementation"},
        {"field": "new_alpha_allowed", "value": "no"},
        {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
        {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
        {"field": "real_capital", "value": "FORBIDDEN"},
    ]
    return rows, summary_rows, decision_rows


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row.get(col, "") for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def write_report(rows: list[dict[str, str]], summary_rows: list[dict[str, str]]) -> None:
    compact_rows = [
        {
            "path": row["path"],
            "wave": row["wave_id"],
            "verdict": row["validation_verdict"],
            "reason": row["reason"],
        }
        for row in rows
    ]
    report = f"""# Task751 W0-W1 Extraction Validation

## Decision Summary

Task751 is a partial pass with blockers.

W0/W1 were checked, but they should not be promoted as canonical yet.

Main blockers:

1. Several W0 `__init__.py` files are not namespace-only.
2. `src/state/store.py` is implementation, not a pure contract/interface.
3. Import tests do not change strategy acceptance, deployment readiness, or real capital status.

## Quant Expert Report

Validation rows:

{markdown_table(compact_rows, ["path", "wave", "verdict", "reason"])}

Required next fix:

```text
Move package __init__ files toward namespace-only exports.
Separate state contract from SQLite store implementation.
Keep runtime/integration out of W0-W1.
```

## No-Background Decision-Maker Report

1. 일부는 통과했습니다.
2. 하지만 전체 승격은 아직 안 됩니다.
3. 껍데기 파일 몇 개가 너무 많은 코드를 끌고 옵니다.
4. `state/store.py`는 계약서가 아니라 실제 저장소 구현입니다.
5. 다음은 이 경계를 고치는 작업입니다.

## Artifact Manifest

Primary artifacts:

- `task751_w0_w1_validation.csv`
- `task751_summary.csv`
- `task_751_decision.csv`
- `gpt_review_notes.md`
- `artifact_manifest.csv`

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (TASK_DIR / "task_751_w0_w1_extraction_validation.md").write_text(report, encoding="utf-8")


def write_gpt_notes_placeholder() -> None:
    notes = """# Task751 GPT Review Notes

GPT was used as a review-only backend/platform architecture critic.

## Applied Review Points

1. Task751 verdict should be `PARTIAL_PASS`.
2. W0 namespace-only gate is violated by:
   - `src/backtest/__init__.py`
   - `src/risk/__init__.py`
   - `src/state/__init__.py`
   - `src/strategy/__init__.py`
3. W1 conditional pass candidates are:
   - `src/common/models.py`
   - `src/execution/interface.py`
   - `src/market/interface.py`
   - `src/reporting/interface.py`
   - `src/risk/interface.py`
   - `src/strategy/interface.py`
4. `src/state/store.py` should be reclassified away from W1 because it is SQLite persistence implementation, not a pure contract/interface.
5. Mojibake in contract comments/docstrings is a contract readability risk.

GPT review is not a source of truth and does not approve strategy or deployment.
"""
    (TASK_DIR / "gpt_review_notes.md").write_text(notes, encoding="utf-8")


def main() -> None:
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    rows, summary_rows, decision_rows = build_validation()
    validation_fields = [
        "path",
        "wave_id",
        "module_name",
        "import_status",
        "import_error",
        "top_level_imports",
        "blocked_import_detected",
        "blocked_import_module",
        "validation_verdict",
        "reason",
        "strategy_acceptance_effect",
        "deployment_effect",
        "real_capital_effect",
    ]
    write_csv(TASK_DIR / "task751_w0_w1_validation.csv", rows, validation_fields)
    write_csv(TASK_DIR / "task751_summary.csv", summary_rows, ["field", "value"])
    write_csv(TASK_DIR / "task_751_decision.csv", decision_rows, ["field", "value"])
    write_report(rows, summary_rows)
    write_gpt_notes_placeholder()
    print(f"[TASK751] wrote={TASK_DIR}")


if __name__ == "__main__":
    main()
