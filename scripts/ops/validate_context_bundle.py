from __future__ import annotations

import argparse
import csv
import re
import sys

from ops_common import ROOT, context_config, doc_map, has_glob, match_path, print_result


def choose_bundle(config: dict, task_id: str | None, bundle_name: str | None) -> tuple[str, dict]:
    if bundle_name:
        bundles = config.get("bundles", {})
        if bundle_name not in bundles:
            raise KeyError(f"bundle not found: {bundle_name}")
        return bundle_name, bundles[bundle_name]
    if not task_id:
        raise ValueError("provide --task or --bundle")
    for name, bundle in config.get("bundles", {}).items():
        if bundle.get("task_id") == task_id:
            return name, bundle
    raise KeyError(f"bundle for task not found: {task_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task")
    parser.add_argument("--bundle")
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        config = context_config()
        name, bundle = choose_bundle(config, args.task, args.bundle)
    except Exception as exc:
        return print_result("CONTEXT BUNDLE VALIDATION", [], [], [str(exc)])

    task_or_bundle = bundle.get("task_id") or args.task or name
    safe_name = str(task_or_bundle).replace("_", "-")
    context_path = ROOT / "docs" / "generated_context" / f"{safe_name}_context.md"
    manifest_path = ROOT / "docs" / "generated_context" / f"{safe_name}_manifest.csv"
    if not context_path.exists():
        failures.append(f"bundle missing: {context_path.relative_to(ROOT).as_posix()}")
        return print_result("CONTEXT BUNDLE VALIDATION", passes, warnings, failures)
    if not manifest_path.exists():
        failures.append(f"manifest missing: {manifest_path.relative_to(ROOT).as_posix()}")
        return print_result("CONTEXT BUNDLE VALIDATION", passes, warnings, failures)

    text = context_path.read_text(encoding="utf-8")
    count_match = re.search(r"^Token Count:\s*(\d+)\s*$", text, re.MULTILINE)
    mode_match = re.search(r"^Token Count Mode:\s*(exact|approximate)\s*$", text, re.MULTILINE)
    if not count_match:
        failures.append("token count missing")
        token_count = 0
    else:
        token_count = int(count_match.group(1))
        passes.append(f"token_count_present: {token_count}")
    if not mode_match:
        failures.append("token count mode missing")

    max_tokens = int(bundle.get("max_tokens") or config.get("defaults", {}).get("max_tokens") or 20000)
    if token_count > max_tokens:
        failures.append(f"token budget exceeded: {token_count} > {max_tokens}")
    else:
        passes.append(f"token_budget: {token_count}/{max_tokens}")

    with manifest_path.open("r", encoding="utf-8", newline="") as fh:
        included = [row.get("path", "") for row in csv.DictReader(fh) if row.get("path")]
    included_set = set(included)
    docs = doc_map()
    for path in included:
        metadata = docs.get(path)
        if metadata and metadata.get("codex_read") == "NEVER":
            failures.append(f"codex_read NEVER included: {path}")
        if metadata and metadata.get("status") == "SUPERSEDED":
            failures.append(f"SUPERSEDED included: {path}")

    for pattern in bundle.get("must_include", []):
        if has_glob(pattern):
            matches = [
                p.relative_to(ROOT).as_posix()
                for p in ROOT.glob(pattern)
                if p.is_file() and not any(match_path(p.relative_to(ROOT).as_posix(), ex) for ex in bundle.get("exclude", []))
            ]
            if matches and not any(path in included_set for path in matches):
                failures.append(f"required pattern has matches but none included: {pattern}")
            elif not matches:
                warnings.append(f"required glob matched nothing: {pattern}")
        elif pattern not in included_set:
            failures.append(f"required file not included: {pattern}")

    if str(context_path.relative_to(ROOT).as_posix()) not in docs:
        warnings.append("generated context markdown is not registered; acceptable if reported as task artifact")

    passes.append(f"included_files: {len(included)}")
    return print_result("CONTEXT BUNDLE VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
