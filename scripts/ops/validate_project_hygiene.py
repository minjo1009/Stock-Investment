from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

from ops_common import ROOT, load_yaml, print_result


POLICY_PATH = "ops/project_hygiene_policy.yaml"


def normalize(path: Path) -> str:
    return path.name.replace("\\", "/")


def root_entries() -> list[Path]:
    return sorted(ROOT.iterdir(), key=lambda item: item.name.lower())


def policy_entries(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for item in policy.get("root_entries", []):
        name = str(item.get("name") or "").strip()
        if name:
            entries[name] = item
    return entries


def write_inventory(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "name",
                "actual_kind",
                "declared_kind",
                "classification",
                "action",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-out")
    parser.add_argument("--strict-known-debt", action="store_true")
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        policy = load_yaml(POLICY_PATH)
    except Exception as exc:
        return print_result("PROJECT HYGIENE VALIDATION", [], [], [str(exc)])

    declared = policy_entries(policy)
    if not declared:
        failures.append("no root_entries declared in project hygiene policy")

    seen_declared: set[str] = set()
    duplicates: set[str] = set()
    for item in policy.get("root_entries", []):
        name = str(item.get("name") or "").strip()
        if name in seen_declared:
            duplicates.add(name)
        seen_declared.add(name)
    for name in sorted(duplicates):
        failures.append(f"duplicate root entry declaration: {name}")

    inventory_rows: list[dict[str, str]] = []
    unclassified: list[str] = []
    known_debt: list[str] = []
    sensitive: list[str] = []

    for entry in root_entries():
        name = normalize(entry)
        actual_kind = "directory" if entry.is_dir() else "file"
        declared_entry = declared.get(name)
        if declared_entry is None:
            unclassified.append(name)
            inventory_rows.append(
                {
                    "name": name,
                    "actual_kind": actual_kind,
                    "declared_kind": "",
                    "classification": "UNCLASSIFIED",
                    "action": "classify_or_remove",
                    "status": "FAIL",
                }
            )
            continue

        declared_kind = str(declared_entry.get("kind") or "")
        classification = str(declared_entry.get("classification") or "")
        action = str(declared_entry.get("action") or "")
        status = "PASS"
        if declared_kind and declared_kind != actual_kind:
            failures.append(
                f"root entry kind mismatch: {name} actual={actual_kind} declared={declared_kind}"
            )
            status = "FAIL"
        if "known_debt" in classification:
            known_debt.append(name)
            status = "WARN" if status == "PASS" else status
        if "secret" in classification or "token" in classification:
            sensitive.append(name)
            status = "WARN" if status == "PASS" else status
        inventory_rows.append(
            {
                "name": name,
                "actual_kind": actual_kind,
                "declared_kind": declared_kind,
                "classification": classification,
                "action": action,
                "status": status,
            }
        )

    missing = sorted(set(declared) - {normalize(entry) for entry in root_entries()})
    for name in missing:
        if str(declared.get(name, {}).get("presence") or "required") == "optional":
            passes.append(f"optional root entry absent: {name}")
            continue
        warnings.append(f"declared root entry not present: {name}")

    if unclassified and policy.get("validation", {}).get("fail_on_unclassified_root_entry", True):
        failures.extend(f"unclassified root entry: {name}" for name in sorted(unclassified))
    elif unclassified:
        warnings.extend(f"unclassified root entry: {name}" for name in sorted(unclassified))

    if known_debt:
        message = f"known_debt root entries: {', '.join(sorted(known_debt))}"
        if args.strict_known_debt:
            failures.append(message)
        elif policy.get("validation", {}).get("warn_on_known_debt", True):
            warnings.append(message)

    if sensitive and policy.get("validation", {}).get("warn_on_sensitive_root_file", True):
        warnings.append(f"sensitive local root entries classified do-not-read: {', '.join(sorted(sensitive))}")

    for path in policy.get("canonical_surfaces", {}).get("governance", []):
        if not (ROOT / path).exists():
            failures.append(f"missing governance surface: {path}")

    closeout_path = ROOT / "scripts/ops/validate_codex_closeout.py"
    closeout_text = closeout_path.read_text(encoding="utf-8") if closeout_path.exists() else ""
    if "validate_project_hygiene.py" in closeout_text:
        passes.append("closeout_gate_includes_project_hygiene")
    else:
        failures.append("closeout gate does not include validate_project_hygiene.py")

    if args.inventory_out:
        write_inventory(ROOT / args.inventory_out, inventory_rows)
        passes.append(f"inventory_written: {args.inventory_out}")

    passes.append(f"root_entries_seen: {len(inventory_rows)}")
    passes.append(f"root_entries_classified: {len(inventory_rows) - len(unclassified)}")
    if not unclassified:
        passes.append("no_unclassified_root_entries")

    return print_result("PROJECT HYGIENE VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
