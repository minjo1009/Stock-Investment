from __future__ import annotations

import argparse
import sys

from ops_common import artifact_manifest_files, get_task, git_changed_files, matches_any, print_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        task = get_task(args.task)
    except Exception as exc:
        return print_result("TASK SCOPE VALIDATION", [], [], [str(exc)])

    allowed = task.get("allowed_paths", [])
    forbidden = task.get("forbidden_paths", [])
    changed, git_warnings = git_changed_files()
    warnings.extend(git_warnings)

    manifest_files = artifact_manifest_files(task)
    if manifest_files:
        scoped_files = manifest_files
        outside_dirty = sorted(set(changed) - set(scoped_files))
        if outside_dirty:
            warnings.append(f"dirty files outside task manifest ignored for scope gate: {len(outside_dirty)}")
    else:
        scoped_files = changed
        warnings.append("artifact manifest unavailable; falling back to full git diff/status")

    for path in scoped_files:
        if not matches_any(path, allowed):
            failures.append(f"outside allowed paths: {path}")
        if matches_any(path, forbidden):
            failures.append(f"forbidden path touched: {path}")

    passes.append(f"git_changed_files_seen: {len(changed)}")
    passes.append(f"scoped_files_checked: {len(scoped_files)}")
    if not any("forbidden path" in failure for failure in failures):
        passes.append("forbidden_paths_clean")
    return print_result("TASK SCOPE VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
