from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ops_common import ROOT, load_yaml, print_result


REGISTRY = "ops/project_knowledge_surfaces.yaml"


def as_list(node: Any) -> list[Any]:
    return node if isinstance(node, list) else []


def path_exists(path: str) -> bool:
    return (ROOT / path).exists()


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        registry = load_yaml(REGISTRY)
    except Exception as exc:
        return print_result("KNOWLEDGE SURFACE VALIDATION", [], [], [str(exc)])

    canonical = registry.get("canonical_surfaces") or {}
    required_surface_keys = [
        "governance_prompts",
        "codex_skills",
        "ops_harness",
        "layer_harness",
        "source_tools",
        "app_surfaces",
        "source_code",
        "contracts",
        "documents",
        "artifacts",
    ]
    for key in required_surface_keys:
        surface = canonical.get(key) or {}
        directory = surface.get("canonical_dir")
        if not directory:
            failures.append(f"canonical surface missing canonical_dir: {key}")
        elif path_exists(str(directory)):
            passes.append(f"canonical surface exists: {key} -> {directory}")
        else:
            failures.append(f"canonical surface path absent: {key} -> {directory}")

    root_prompts = ROOT / "prompts"
    if root_prompts.exists():
        failures.append("legacy root prompts/ still exists; use ops/prompts")
    else:
        passes.append("legacy root prompts absent")

    prompt_rows = as_list(registry.get("prompts"))
    if not prompt_rows:
        failures.append("no prompts registered")
    for row in prompt_rows:
        path = str(row.get("path") or "")
        if not path:
            failures.append(f"prompt row missing path: {row}")
            continue
        prompt_path = ROOT / path
        if not prompt_path.exists():
            failures.append(f"registered prompt absent: {path}")
            continue
        text = prompt_path.read_text(encoding="utf-8")
        if "\ufffd" in text or "臾" in text or "媛" in text:
            failures.append(f"registered prompt appears mojibake/corrupt: {path}")
        else:
            passes.append(f"registered prompt readable: {path}")

    skill_rows = as_list(registry.get("skills"))
    registered_skills = {str(row.get("name")) for row in skill_rows if row.get("name")}
    actual_skill_dirs = {
        path.name
        for path in (ROOT / ".codex/skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    }
    if registered_skills == actual_skill_dirs:
        passes.append(f"all codex skills registered: {len(registered_skills)}")
    else:
        missing = sorted(actual_skill_dirs - registered_skills)
        stale = sorted(registered_skills - actual_skill_dirs)
        if missing:
            failures.append(f"codex skills missing registry rows: {', '.join(missing)}")
        if stale:
            failures.append(f"registry skills missing directories: {', '.join(stale)}")
    profiles = set((load_yaml("ops/task_profiles.yaml").get("profiles") or {}).keys())
    for row in skill_rows:
        name = str(row.get("name") or "")
        path = str(row.get("path") or "")
        owner_profile = str(row.get("owner_profile") or "")
        if not path_exists(path):
            failures.append(f"registered skill path absent: {name} -> {path}")
        if owner_profile and owner_profile not in profiles:
            failures.append(f"registered skill profile unknown: {name} -> {owner_profile}")
        if not row.get("layer") or not row.get("category") or not row.get("primary_use"):
            failures.append(f"registered skill missing layer/category/use: {name}")

    harness_rows = as_list(registry.get("harness_groups"))
    if harness_rows:
        passes.append(f"harness groups registered: {len(harness_rows)}")
    else:
        failures.append("no harness groups registered")

    for required_path in [
        "tools/db/run_source_acquisition_once.py",
        "tools/db/news_l0_l1.py",
        "tools/db/source_acquisition",
        "scripts/ops/validate_codex_closeout.py",
        "scripts/ops/validate_knowledge_surfaces.py",
    ]:
        if path_exists(required_path):
            passes.append(f"required knowledge path exists: {required_path}")
        else:
            failures.append(f"required knowledge path absent: {required_path}")

    return print_result("KNOWLEDGE SURFACE VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
