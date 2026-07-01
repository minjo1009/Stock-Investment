from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ops_common import ROOT, load_yaml, print_result


POLICY = "ops/project_structure_policy.yaml"


def as_list(node: Any) -> list[str]:
    if isinstance(node, list):
        return [str(item) for item in node]
    return []


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        policy = load_yaml(POLICY)
    except Exception as exc:
        return print_result("PROJECT STRUCTURE POLICY VALIDATION", [], [], [str(exc)])

    target_root = policy.get("target_root") or {}
    keep = set(as_list(target_root.get("keep")))
    local_only = set(as_list(target_root.get("local_only")))
    sensitive = set(as_list(target_root.get("sensitive_local_only")))
    legacy_active = set(as_list(target_root.get("legacy_active_migration_required")))
    review = set(as_list(target_root.get("review_before_move_or_delete")))
    declared = keep | local_only | sensitive | legacy_active | review
    if not declared:
        failures.append("target_root has no declared entries")

    actual = {path.name for path in ROOT.iterdir()}
    unclassified = sorted(actual - declared - {".git", ".gitignore", ".dvcignore"})
    if unclassified:
        failures.append(f"root entries missing from structure policy: {', '.join(unclassified)}")
    else:
        passes.append("all root entries covered by structure policy")

    for path in keep:
        if not (ROOT / path).exists():
            warnings.append(f"target keep path absent: {path}")

    duplicate_axes = policy.get("duplicate_axis_decisions") or []
    if duplicate_axes:
        passes.append(f"duplicate axes declared: {len(duplicate_axes)}")
    else:
        failures.append("duplicate_axis_decisions is empty")
    for row in duplicate_axes:
        if not row.get("canonical") or not row.get("current_action"):
            failures.append(f"duplicate axis missing canonical/current_action: {row}")

    docs_policy = policy.get("docs_surface_policy") or {}
    keep_docs = as_list(docs_policy.get("keep_canonical"))
    review_docs = as_list(docs_policy.get("review_surfaces"))
    if not keep_docs:
        failures.append("docs_surface_policy.keep_canonical is empty")
    if not review_docs:
        warnings.append("docs_surface_policy.review_surfaces is empty")
    docs_dir = ROOT / "docs"
    if docs_dir.exists():
        actual_docs = {f"docs/{item.name}" for item in docs_dir.iterdir() if item.is_dir()}
        classified_docs = set(keep_docs) | set(review_docs) | {"docs/archive"}
        missing_docs = sorted(actual_docs - classified_docs)
        if missing_docs:
            failures.append(f"docs surfaces missing policy classification: {', '.join(missing_docs)}")
        else:
            passes.append("all docs surfaces classified")

    closeout = policy.get("closeout_requirements") or {}
    validators = as_list(closeout.get("validators"))
    for command in [
        "python scripts/ops/validate_project_hygiene.py",
        "python scripts/ops/validate_project_structure_policy.py",
        "python scripts/ops/validate_knowledge_surfaces.py",
        "python scripts/ops/validate_internal_cleanliness.py",
    ]:
        if command in validators:
            passes.append(f"closeout validator declared: {command}")
        else:
            failures.append(f"missing closeout validator declaration: {command}")

    closeout_path = ROOT / "scripts/ops/validate_codex_closeout.py"
    closeout_text = closeout_path.read_text(encoding="utf-8") if closeout_path.exists() else ""
    if "validate_project_structure_policy.py" in closeout_text:
        passes.append("codex closeout runs structure policy validator")
    else:
        failures.append("codex closeout does not run structure policy validator")
    if "validate_knowledge_surfaces.py" in closeout_text:
        passes.append("codex closeout runs knowledge surface validator")
    else:
        failures.append("codex closeout does not run knowledge surface validator")
    if "validate_internal_cleanliness.py" in closeout_text:
        passes.append("codex closeout runs internal cleanliness validator")
    else:
        failures.append("codex closeout does not run internal cleanliness validator")

    return print_result("PROJECT STRUCTURE POLICY VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
