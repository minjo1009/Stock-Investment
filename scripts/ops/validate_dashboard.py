from __future__ import annotations

import argparse
import re
import sys

from ops_common import ROOT, print_result


REQUIRED_SECTIONS = [
    "Operating State",
    "Active Tasks",
    "Blocked Tasks",
    "Review Tasks",
    "Recently Done Tasks",
    "Task Detail Table",
    "Required Validators",
    "Artifact Links",
    "Document Status Summary",
    "Context Bundle Token Usage",
    "Hard Boundaries",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="ops/dashboard/index.html")
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    path = ROOT / args.path
    if not path.exists():
        return print_result("DASHBOARD VALIDATION", [], [], [f"dashboard missing: {args.path}"])
    text = path.read_text(encoding="utf-8")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            failures.append(f"missing section: {section}")
        else:
            passes.append(f"section: {section}")
    if re.search(r"https?://|<script\s+src=|<link\s+[^>]*href=[\"']https?", text, re.IGNORECASE):
        failures.append("network dependency detected")
    else:
        passes.append("no_network_dependency")
    if "<form" in text.lower() or "contenteditable" in text.lower():
        failures.append("editable control detected")
    else:
        passes.append("read_only_static")
    return print_result("DASHBOARD VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
