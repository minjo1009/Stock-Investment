# Boundary Test Plan

## Purpose
Define architecture tests that can be implemented after approval. This task documents exact proposed tests but does not create executable test files yet.

## Proposed Tests

### 1. Forbidden Imports

- Parse all Python files under `src/` with `ast`.
- Map file path to canonical layer.
- Fail if an import violates `docs/architecture/architecture_manifest.yml` forbidden dependencies.

### 2. Task Files Not Under Production App

- Fail if `src/app/task_*.py` exists unless listed in an explicit promotion allowlist.
- Current expected result: fail until migration moves or promotes existing task modules.

### 3. External References Not Imported By Production

- Fail if any production file imports modules from `참고 Context/` or future `archive/external_references/`.

### 4. Strategy Cannot Import Broker/Execution

- Fail if files under `src/strategy` import `integration`, `kis_client`, `execution`, or broker adapters.

### 5. Intelligence Cannot Import Execution

- Fail if future `src/intelligence` or Graphify automation code imports `execution` or `integration`.

### 6. Backtest Cannot Import Live Broker

- Fail if files under `src/backtest` import `integration.kis_client`, `KISClient`, or live broker auth modules.

### 7. Apps Contain Orchestration Only

- Warn, not fail initially, when `src/app` modules define durable domain constants, SQL schema, or strategy conditions.

## Proposed Test Code

```python
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

FORBIDDEN = {
    "src/strategy": ("integration", "execution", "kis_client"),
    "src/backtest": ("integration.kis_client", "KISClient"),
    "src/execution": ("strategy.conditions", "backtest.entry_gates"),
}

def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add(node.module or "")
    return found

def test_forbidden_layer_imports():
    violations = []
    for file in SRC.rglob("*.py"):
        rel = file.relative_to(ROOT).as_posix()
        refs = imports(file)
        for prefix, banned in FORBIDDEN.items():
            if rel.startswith(prefix):
                for ref in refs:
                    if any(ref == b or ref.startswith(b + ".") for b in banned):
                        violations.append((rel, ref))
    assert not violations, violations
```

## Implementation Recommendation
Implement as non-blocking first. Promote to blocking only after Stage 2 and Stage 3 reduce known legacy violations.

