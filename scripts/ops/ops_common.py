from __future__ import annotations

import csv
import fnmatch
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def rel(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.relative_to(ROOT)
        except ValueError:
            return p.as_posix()
    return p.as_posix()


def require_yaml():
    try:
        import yaml  # type: ignore
    except Exception as exc:
        print(f"FAIL PyYAML is required for ops YAML files: {exc}")
        sys.exit(2)
    return yaml


def load_yaml(path: str) -> dict[str, Any]:
    yaml = require_yaml()
    full = ROOT / path
    if not full.exists():
        raise FileNotFoundError(path)
    with full.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def write_yaml(path: str, data: dict[str, Any]) -> None:
    yaml = require_yaml()
    full = ROOT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    with full.open("w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=False)


def task_registry() -> dict[str, Any]:
    return load_yaml("ops/task_registry.yaml")


def task_profiles() -> dict[str, Any]:
    return load_yaml("ops/task_profiles.yaml")


def doc_registry() -> dict[str, Any]:
    return load_yaml("ops/doc_registry.yaml")


def context_config() -> dict[str, Any]:
    return load_yaml("ops/context_bundles.yaml")


def get_task(task_id: str) -> dict[str, Any]:
    for task in task_registry().get("tasks", []):
        if task.get("task_id") == task_id:
            return task
    raise KeyError(f"task not found: {task_id}")


def doc_map() -> dict[str, dict[str, Any]]:
    return {d.get("path"): d for d in doc_registry().get("documents", []) if d.get("path")}


def has_glob(pattern: str) -> bool:
    return any(ch in pattern for ch in "*?[")


def match_path(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/")
    pattern = pattern.replace("\\", "/")
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatch(path, pattern)


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(match_path(path, pattern) for pattern in patterns)


def is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\0" in chunk


def run_command(args: list[str]) -> tuple[int, str]:
    try:
        env = os.environ.copy()
        if args and (Path(args[0]).name.lower().startswith("python")):
            env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run(
            args,
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except FileNotFoundError as exc:
        return 127, str(exc)
    return proc.returncode, proc.stdout


def git_changed_files() -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    changed: set[str] = set()
    code, out = run_command(["git", "diff", "--name-only"])
    if code != 0:
        warnings.append(f"git diff unavailable: {out.strip()}")
    else:
        changed.update(line.strip().replace("\\", "/") for line in out.splitlines() if line.strip())

    code, out = run_command(["git", "status", "--porcelain"])
    if code != 0:
        warnings.append(f"git status unavailable: {out.strip()}")
    else:
        for line in out.splitlines():
            if not line.strip():
                continue
            path = line[3:] if len(line) > 3 else line.strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            changed.add(path.strip().replace("\\", "/"))
    return sorted(changed), warnings


def artifact_manifest_path(task: dict[str, Any]) -> Path | None:
    for path in task.get("required_artifacts", []):
        if path.endswith("artifact_manifest.csv"):
            return ROOT / path
    return None


def artifact_manifest_files(task: dict[str, Any]) -> list[str]:
    manifest = artifact_manifest_path(task)
    if not manifest or not manifest.exists():
        return []
    files: list[str] = []
    with manifest.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            path = (row.get("path") or "").strip()
            if path:
                files.append(path.replace("\\", "/"))
    return sorted(set(files))


def print_result(title: str, passes: list[str], warnings: list[str], failures: list[str]) -> int:
    print(title)
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    if failures:
        print("RESULT: FAIL")
        return 1
    if warnings:
        print("RESULT: PASS_WITH_WARNINGS")
        return 0
    print("RESULT: PASS")
    return 0


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8", newline="\n")


def now_utc_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
