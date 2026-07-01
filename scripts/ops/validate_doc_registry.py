from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ops_common import ROOT, doc_registry, match_path, print_result, rel


REQUIRED_FIELDS = {
    "path",
    "type",
    "domain",
    "status",
    "priority",
    "codex_read",
    "owner",
    "created_by_task",
}

DEFAULT_EXCLUDES = [
    "docs/archive/**",
    "docs/generated_context/*_context.md",
]


def docs_markdown_files() -> list[str]:
    docs = ROOT / "docs"
    if not docs.exists():
        return []
    return sorted(rel(path) for path in docs.rglob("*.md") if path.is_file())


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--soft", action="store_true", help="warn on historical unregistered docs")
    mode.add_argument("--strict", action="store_true", help="fail on unregistered docs")
    args = parser.parse_args()
    strict = args.strict

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        registry = doc_registry()
    except Exception as exc:
        return print_result("DOC REGISTRY VALIDATION", [], [], [str(exc)])

    for key in ["version", "updated_at", "documents"]:
        if key not in registry:
            failures.append(f"missing root key: {key}")

    documents = registry.get("documents", [])
    if not isinstance(documents, list):
        failures.append("documents must be a list")
        documents = []
    passes.append(f"documents: {len(documents)}")

    paths: set[str] = set()
    for idx, doc in enumerate(documents):
        label = doc.get("path") or f"index {idx}"
        missing = sorted(REQUIRED_FIELDS - set(doc.keys()))
        if missing:
            failures.append(f"{label} missing fields: {', '.join(missing)}")
        path = doc.get("path")
        if path in paths:
            failures.append(f"duplicate document path: {path}")
        if path:
            paths.add(path)
            exists = (ROOT / path).exists()
            if not exists and doc.get("status") not in {"ARCHIVED", "UNKNOWN"}:
                failures.append(f"registered path missing: {path}")
        if doc.get("status") == "ACTIVE" and doc.get("codex_read") == "NEVER":
            failures.append(f"ACTIVE document cannot be codex_read NEVER: {label}")
        if doc.get("status") == "ACTIVE" and not doc.get("owner"):
            failures.append(f"ACTIVE document missing owner: {label}")
        if doc.get("status") == "SUPERSEDED" and not doc.get("superseded_by"):
            failures.append(f"SUPERSEDED document missing superseded_by: {label}")

    unregistered: list[str] = []
    for path in docs_markdown_files():
        if any(match_path(path, pattern) for pattern in DEFAULT_EXCLUDES):
            continue
        if path not in paths:
            unregistered.append(path)

    task_report_misplaced = [
        path
        for path in docs_markdown_files()
        if path.startswith("docs/reports/")
        and not path.startswith("docs/reports/task_")
        and path not in paths
    ]

    if unregistered:
        msg = f"unregistered docs/**/*.md: {len(unregistered)}"
        sample = ", ".join(unregistered[:10])
        if strict:
            failures.append(f"{msg}; sample: {sample}")
        else:
            warnings.append(f"{msg}; sample: {sample}")
    if task_report_misplaced:
        msg = f"task reports outside task folder: {', '.join(task_report_misplaced[:10])}"
        if strict:
            failures.append(msg)
        else:
            warnings.append(msg)

    if not any("missing fields" in failure for failure in failures):
        passes.append("required_fields")
    if not any("duplicate" in failure for failure in failures):
        passes.append("no_duplicate_paths")

    return print_result("DOC REGISTRY VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
