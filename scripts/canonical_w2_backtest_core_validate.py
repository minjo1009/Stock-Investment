from __future__ import annotations

import ast
import csv
import inspect
import importlib
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
TASK_DIR = ROOT / "docs" / "reports" / "task_753_w2_backtest_core_validation"

W2_CANDIDATES = [
    "src/backtest/models.py",
    "src/backtest/data_loader.py",
    "src/backtest/engine.py",
    "src/backtest/engine_full.py",
    "src/backtest/analysis.py",
]

BLOCKING_IMPORT_PREFIXES = {
    "analytics",
    "execution",
    "portfolio",
    "risk.policies",
    "sector",
    "state.store",
    "strategy.conditions",
    "strategy.validator",
    "universe",
}


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


def module_name_from_path(src_path: str) -> str:
    rel = Path(src_path).relative_to("src")
    return ".".join(rel.with_suffix("").parts)


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


def blocked_imports(imports: list[str]) -> list[str]:
    out: list[str] = []
    for module in imports:
        for prefix in BLOCKING_IMPORT_PREFIXES:
            if module == prefix or module.startswith(prefix + "."):
                out.append(module)
                break
    return out


def quick_loader_fallback_status() -> str:
    added = False
    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))
        added = True
    try:
        data_loader = importlib.import_module("backtest.data_loader")
        signature = inspect.signature(data_loader.load_bars_for_quick_backtest)
        parameter = signature.parameters.get("allow_sample_fallback")
        if parameter is None:
            return "FAIL_NO_EXPLICIT_FALLBACK_PARAMETER"
        if parameter.default is not False:
            return "FAIL_FALLBACK_DEFAULT_NOT_FALSE"
        return "PASS_EXPLICIT_OPT_IN_ONLY"
    finally:
        if added:
            try:
                sys.path.remove(str(SRC_ROOT))
            except ValueError:
                pass


def classify(path: str) -> dict[str, str]:
    abs_path = ROOT / path
    imports = imported_modules(abs_path)
    blocked = blocked_imports(imports)
    module_name = module_name_from_path(path)
    import_status, import_error = import_check(module_name)

    if import_status != "PASS":
        verdict = "BLOCK_IMPORT_FAIL"
        reason = import_error
    elif path == "src/backtest/models.py":
        verdict = "PASS_CONTRACT_CANDIDATE"
        reason = "stdlib-only backtest result contracts; reconcile duplication with common.models before wider use"
    elif path == "src/backtest/data_loader.py":
        fallback_status = quick_loader_fallback_status()
        verdict = "PASS_LOADER_AFTER_FALLBACK_REPAIR" if fallback_status.startswith("PASS") else "BLOCK_FAKE_DATA_FALLBACK"
        reason = fallback_status
    elif path == "src/backtest/analysis.py":
        verdict = "SUPPORTING_ANALYZER_NOT_ENGINE_CORE"
        reason = "exported trades analyzer; useful but not simulation engine core"
    elif path == "src/backtest/engine.py":
        verdict = "BLOCK_REPAIR_REQUIRED"
        reason = "imports strategy/validator/sector/lifecycle implementation and uses next-open execution convention needing as-of contract"
    elif path == "src/backtest/engine_full.py":
        verdict = "OWNER_REVIEW_ONLY"
        reason = "broad integration engine imports execution/risk/portfolio/universe/strategy and has portfolio full-snapshot leakage risk"
    elif blocked:
        verdict = "BLOCK_FORBIDDEN_IMPORTS"
        reason = ";".join(blocked)
    else:
        verdict = "REVIEW_REQUIRED"
        reason = "unclassified W2 candidate"

    return {
        "path": path,
        "module_name": module_name,
        "import_status": import_status,
        "top_level_imports": ";".join(imports),
        "blocking_imports": ";".join(blocked),
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


def write_report(rows: list[dict[str, str]]) -> None:
    compact = [
        {
            "path": row["path"],
            "verdict": row["validation_verdict"],
            "reason": row["reason"],
        }
        for row in rows
    ]
    report = f"""# Task753 W2 Backtest Core Validation

## Decision Summary

W2 work moved forward by fixing the raw-data fallback issue in `data_loader.py` and mapping the rest of the backtest candidates.

`engine.py` and `engine_full.py` are not promoted. They need boundary and as-of repairs before they can be treated as canonical core.

## Quant Expert Report

Current W2 classification:

{markdown_table(compact, ["path", "verdict", "reason"])}

Immediate implications:

```text
models.py: usable contract candidate, but check overlap with common.models.
data_loader.py: usable after explicit sample fallback opt-in repair.
analysis.py: supporting analyzer, not engine core.
engine.py: repair required before promotion.
engine_full.py: owner-review-only integration engine.
```

Subagent/GPT review agreed on the main blockers:

```text
No fake data fallback in canonical loader.
No broad strategy/risk/execution/portfolio import fan-out in W2 core.
No next-open/as-of ambiguity without explicit execution convention.
No full-period portfolio snapshot ranking in historical replay.
```

## No-Background Decision-Maker Report

1. 가짜 샘플 데이터 자동 사용은 막았습니다.
2. 백테스트 뼈대 중 바로 믿을 수 있는 건 아직 작습니다.
3. `engine.py`는 고쳐야 합니다.
4. `engine_full.py`는 아직 핵심 엔진이 아니라 큰 통합 엔진입니다.
5. 다음은 `engine.py`를 순수 replay core로 줄이는 작업입니다.

## Artifact Manifest

Primary artifacts:

- `task753_w2_backtest_core_validation.csv`
- `task753_summary.csv`
- `task_753_decision.csv`
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
    (TASK_DIR / "task_753_w2_backtest_core_validation.md").write_text(report, encoding="utf-8")


def write_notes() -> None:
    gpt = """# Task753 GPT Review Notes

GPT was given a new-engineer onboarding packet with project status, architecture, cleanup history, W2 files, imports, and forbidden claims.

Applied review points:

1. Do not promote `engine.py` or `engine_full.py` as canonical W2 core.
2. Remove or explicitly gate sample fallback from canonical data loading.
3. Treat next-open usage as requiring an explicit as-of/execution convention.
4. Keep `engine_full.py` owner-review-only because it imports risk/execution/portfolio/universe/strategy layers.
5. No strategy or deployment status changes.
"""
    subagents = """# Task753 Subagent Review Notes

Three read-only subagents reviewed distinct scopes:

1. Backtest Core: `models.py`, `data_loader.py`, and `analysis.py` are the only near-term reusable candidates. `engine.py` needs repair. `engine_full.py` remains owner-review-only.
2. Data/As-of: sample fallback violates missing-source rules; next-open and full-period portfolio ranking require leakage/as-of gates.
3. Test/Governance: W2 has weak direct test coverage. Historical/EVIDENCE_ONLY tests cannot promote W2.
"""
    validation = """# Task753 Validation Log

Commands:

```text
python scripts\\canonical_w2_backtest_core_validate.py
python -m py_compile src\\backtest\\data_loader.py scripts\\canonical_w2_backtest_core_validate.py tests\\test_task753_w2_backtest_core_boundary.py
python -m unittest tests.test_task753_w2_backtest_core_boundary
python -m unittest tests.unit.test_structure.TestRepositoryFoundationStructure.test_backtest_daily_loader_loads_and_sorts_csv tests.unit.test_structure.TestRepositoryFoundationStructure.test_backtest_daily_loader_missing_required_columns_raises tests.unit.test_structure.TestRepositoryFoundationStructure.test_backtest_universe_loader_returns_symbol_map
```
"""
    (TASK_DIR / "gpt_review_notes.md").write_text(gpt, encoding="utf-8")
    (TASK_DIR / "subagent_review_notes.md").write_text(subagents, encoding="utf-8")
    (TASK_DIR / "validation_log.md").write_text(validation, encoding="utf-8")


def main() -> None:
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    rows = [classify(path) for path in W2_CANDIDATES]
    counts = Counter(row["validation_verdict"] for row in rows)
    summary_rows = [
        {"field": "task_id", "value": "Task753"},
        {"field": "verdict", "value": "W2_BOUNDARY_ADVANCED_ENGINE_REPAIR_REQUIRED"},
        {"field": "scope", "value": "W2 backtest core validation and first loader repair"},
        {"field": "w2_candidates_checked", "value": str(len(rows))},
        {"field": "data_loader_sample_fallback_default", "value": quick_loader_fallback_status()},
        {"field": "engine_promoted", "value": "no"},
        {"field": "engine_full_promoted", "value": "no"},
        {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
        {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
        {"field": "real_capital", "value": "FORBIDDEN"},
        {"field": "next_safe_task", "value": "Task754 backtest engine as-of and boundary repair"},
    ]
    for verdict, count in sorted(counts.items()):
        summary_rows.append({"field": f"count_{verdict.lower()}", "value": str(count)})
    decision_rows = [
        {"field": "task_id", "value": "Task753"},
        {"field": "decision", "value": "advance_w2_by_repairing_loader_and_blocking_engines_until_boundary_repair"},
        {"field": "new_alpha_allowed", "value": "no"},
        {"field": "next_allowed_work", "value": "Task754 engine.py pure replay and as-of boundary repair"},
        {"field": "strategy_acceptance", "value": "NOT_ACCEPTED"},
        {"field": "deployment_readiness", "value": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"},
        {"field": "real_capital", "value": "FORBIDDEN"},
    ]
    fields = [
        "path",
        "module_name",
        "import_status",
        "top_level_imports",
        "blocking_imports",
        "validation_verdict",
        "reason",
    ]
    write_csv(TASK_DIR / "task753_w2_backtest_core_validation.csv", rows, fields)
    write_csv(TASK_DIR / "task753_summary.csv", summary_rows, ["field", "value"])
    write_csv(TASK_DIR / "task_753_decision.csv", decision_rows, ["field", "value"])
    write_report(rows)
    write_notes()
    print(f"[TASK753] wrote={TASK_DIR}")


if __name__ == "__main__":
    main()
