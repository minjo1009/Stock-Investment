from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from ops_common import (
    ROOT,
    context_config,
    doc_map,
    has_glob,
    is_binary,
    match_path,
    now_utc_iso,
    rel,
    write_text,
)


LARGE_FILE_BYTES = 500_000


def token_counter(encoding_name: str):
    try:
        import tiktoken  # type: ignore

        encoding = tiktoken.get_encoding(encoding_name)
        return lambda text: len(encoding.encode(text)), "exact"
    except Exception:
        return lambda text: max(1, len(text) // 4), "approximate"


def choose_bundle(config: dict, task_id: str | None, bundle_name: str | None) -> tuple[str, dict]:
    bundles = config.get("bundles", {})
    if bundle_name:
        if bundle_name not in bundles:
            raise KeyError(f"bundle not found: {bundle_name}")
        return bundle_name, bundles[bundle_name]
    if task_id:
        for name, bundle in bundles.items():
            if bundle.get("task_id") == task_id:
                return name, bundle
        raise KeyError(f"bundle for task not found: {task_id}")
    raise ValueError("provide --task or --bundle")


def expand_pattern(pattern: str) -> list[Path]:
    pattern = pattern.replace("\\", "/")
    if has_glob(pattern):
        return sorted(path for path in ROOT.glob(pattern) if path.is_file())
    full = ROOT / pattern
    if full.is_file():
        return [full]
    if full.is_dir():
        return sorted(path for path in full.rglob("*") if path.is_file())
    return []


def extension(path: str) -> str:
    suffix = Path(path).suffix.lower().lstrip(".")
    return suffix or "text"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task")
    parser.add_argument("--bundle")
    parser.add_argument("--allow-codex-read-never", action="store_true")
    parser.add_argument("--allow-superseded", action="store_true")
    args = parser.parse_args()

    try:
        config = context_config()
        name, bundle = choose_bundle(config, args.task, args.bundle)
    except Exception as exc:
        print(f"FAIL {exc}")
        return 1

    defaults = config.get("defaults", {})
    max_tokens = int(bundle.get("max_tokens") or defaults.get("max_tokens") or 20000)
    counter, token_mode = token_counter(defaults.get("encoding", "cl100k_base"))
    docs = doc_map()
    reject_never = defaults.get("reject_codex_read_never", True) and not args.allow_codex_read_never
    reject_superseded = defaults.get("reject_superseded_by_default", True) and not args.allow_superseded
    fail_on_budget = defaults.get("fail_on_token_budget_exceeded", True)

    failures: list[str] = []
    warnings: list[str] = []
    included: list[dict[str, object]] = []
    included_paths: set[str] = set()
    excluded: list[tuple[str, str]] = []

    exclude_patterns = bundle.get("exclude", [])

    def add_pattern(pattern: str, reason: str, required: bool) -> None:
        matches = expand_pattern(pattern)
        if not matches:
            if required and not has_glob(pattern):
                failures.append(f"required file missing: {pattern}")
            else:
                warnings.append(f"pattern matched nothing: {pattern}")
            return
        for path in matches:
            rpath = rel(path)
            if any(match_path(rpath, ex) for ex in exclude_patterns):
                excluded.append((rpath, "matched exclude pattern"))
                continue
            if rpath in included_paths:
                continue
            metadata = docs.get(rpath)
            if metadata and reject_never and metadata.get("codex_read") == "NEVER":
                failures.append(f"codex_read NEVER rejected: {rpath}")
                continue
            if metadata and reject_superseded and metadata.get("status") == "SUPERSEDED":
                failures.append(f"SUPERSEDED rejected: {rpath}")
                continue
            if is_binary(path):
                excluded.append((rpath, "binary file"))
                continue
            size = path.stat().st_size
            if size > LARGE_FILE_BYTES and has_glob(pattern):
                excluded.append((rpath, "large file skipped from glob"))
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                excluded.append((rpath, "not utf-8 text"))
                continue
            tokens = counter(text)
            included.append(
                {
                    "path": rpath,
                    "bytes": size,
                    "tokens": tokens,
                    "reason": reason,
                    "content": text,
                }
            )
            included_paths.add(rpath)

    for pattern in bundle.get("must_include", []):
        add_pattern(pattern, "must_include", True)
    for pattern in bundle.get("optional_include", []):
        add_pattern(pattern, "optional_include", False)

    included.sort(key=lambda item: str(item["path"]))
    total_tokens = sum(int(item["tokens"]) for item in included)
    if total_tokens > max_tokens and fail_on_budget:
        failures.append(f"token budget exceeded: {total_tokens} > {max_tokens}")

    task_id = bundle.get("task_id") or args.task or name
    safe_task = str(task_id).replace("_", "-")
    context_path = ROOT / "docs" / "generated_context" / f"{safe_task}_context.md"
    manifest_path = ROOT / "docs" / "generated_context" / f"{safe_task}_manifest.csv"

    if failures:
        for warning in warnings:
            print(f"WARN {warning}")
        for failure in failures:
            print(f"FAIL {failure}")
        print("RESULT: FAIL")
        return 1

    generated_at = now_utc_iso()
    lines: list[str] = [
        "# Codex Context Bundle",
        "",
        f"Task: {task_id}",
        f"Profile: {bundle.get('profile')}",
        f"Generated At: {generated_at}",
        f"Token Count: {total_tokens}",
        f"Token Count Mode: {token_mode}",
        f"Max Tokens: {max_tokens}",
        "",
        "---",
        "",
        "## Included Files",
        "",
        "| Path | Bytes | Tokens | Reason |",
        "|---|---:|---:|---|",
    ]
    for item in included:
        lines.append(f"| {item['path']} | {item['bytes']} | {item['tokens']} | {item['reason']} |")
    lines.extend(["", "---", "", "## Excluded Files", "", "| Pattern/Path | Reason |", "|---|---|"])
    for pattern in exclude_patterns:
        lines.append(f"| {pattern} | configured exclude |")
    for path, reason in excluded:
        lines.append(f"| {path} | {reason} |")
    for warning in warnings:
        lines.append(f"| warning | {warning} |")

    for item in included:
        path = str(item["path"])
        content = str(item["content"]).replace("```", "`` `")
        lines.extend(["", "---", "", f"## File: {path}", "", f"```{extension(path)}", content, "```"])

    write_text(context_path, "\n".join(lines) + "\n")
    with manifest_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "bytes", "tokens", "reason"])
        writer.writeheader()
        for item in included:
            writer.writerow({k: item[k] for k in ["path", "bytes", "tokens", "reason"]})

    for warning in warnings:
        print(f"WARN {warning}")
    print(f"PASS bundle: {name}")
    print(f"PASS context: {rel(context_path)}")
    print(f"PASS manifest: {rel(manifest_path)}")
    print(f"PASS token_count: {total_tokens} ({token_mode})")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
