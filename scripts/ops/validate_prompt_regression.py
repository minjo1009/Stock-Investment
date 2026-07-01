from __future__ import annotations

import argparse
import re
import sys

from ops_common import ROOT, load_yaml, print_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="ops/prompt_regression_cases.yaml")
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        config = load_yaml(args.cases)
    except Exception as exc:
        return print_result("PROMPT REGRESSION VALIDATION", [], [], [str(exc)])

    for case in config.get("cases", []):
        case_id = case.get("id", "unknown")
        path = ROOT / case.get("path", "")
        if not path.exists():
            failures.append(f"{case_id}: path missing: {case.get('path')}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for phrase in case.get("must_contain", []):
            if phrase not in text:
                failures.append(f"{case_id}: missing phrase: {phrase}")
        for pattern in case.get("must_not_match", []):
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                failures.append(f"{case_id}: forbidden pattern matched: {pattern}")
        if not any(failure.startswith(f"{case_id}:") for failure in failures):
            passes.append(case_id)

    return print_result("PROMPT REGRESSION VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
