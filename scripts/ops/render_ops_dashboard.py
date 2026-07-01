from __future__ import annotations

import csv
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

from ops_common import ROOT, doc_registry, load_yaml, rel, write_text


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def table(headers: list[str], rows: list[list[object]]) -> str:
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def link(path: str) -> str:
    return f'<a href="../../{esc(path)}">{esc(path)}</a>'


def validation_summaries() -> list[list[str]]:
    rows: list[list[str]] = []
    for path in sorted((ROOT / "docs" / "reports").glob("task_*/validation_results.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        result = "UNKNOWN"
        if "FAIL" in text:
            result = "HAS_FAIL"
        elif "PASS_WITH_WARNINGS" in text:
            result = "PASS_WITH_WARNINGS"
        elif "PASS" in text:
            result = "PASS"
        rows.append([rel(path), result])
    return rows


def context_usage() -> list[list[str]]:
    rows: list[list[str]] = []
    for manifest in sorted((ROOT / "docs" / "generated_context").glob("*_manifest.csv")):
        token_sum = 0
        file_count = 0
        with manifest.open("r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                file_count += 1
                try:
                    token_sum += int(row.get("tokens") or 0)
                except ValueError:
                    pass
        rows.append([rel(manifest), file_count, token_sum])
    return rows


def main() -> int:
    try:
        tasks = load_yaml("ops/task_registry.yaml").get("tasks", [])
        docs = doc_registry().get("documents", [])
        operating = load_yaml("ops/operating_state.yaml")
    except Exception as exc:
        print(f"FAIL {exc}")
        return 1

    active = [t for t in tasks if t.get("status") == "IN_PROGRESS"]
    blocked = [t for t in tasks if t.get("status") == "BLOCKED"]
    review = [t for t in tasks if t.get("status") == "REVIEW"]
    done = [t for t in tasks if t.get("status") == "DONE"][-10:]
    doc_counts = Counter(d.get("status", "UNKNOWN") for d in docs)
    hard = operating.get("hard_boundaries", {})

    task_rows = [
        [
            t.get("task_id"),
            t.get("title"),
            t.get("status"),
            t.get("priority"),
            t.get("profile"),
            t.get("closeout", {}).get("status"),
            t.get("updated_at"),
        ]
        for t in tasks
    ]
    validator_rows = [
        [t.get("task_id"), validator]
        for t in tasks
        for validator in t.get("required_validators", [])
    ]
    artifact_rows = [
        [t.get("task_id"), artifact]
        for t in tasks
        for artifact in t.get("required_artifacts", [])
    ]

    summary = {
        "project": operating.get("project", {}),
        "task_counts": Counter(t.get("status", "UNKNOWN") for t in tasks),
        "document_counts": doc_counts,
        "hard_boundaries": hard,
    }
    summary_path = ROOT / "ops" / "dashboard" / "dashboard_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Codex Ops Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Arial, sans-serif;
      background: #f6f7f9;
      color: #17202a;
    }}
    body {{ margin: 0; }}
    header {{ background: #17202a; color: white; padding: 24px 32px; }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    section {{ margin: 0 0 28px; }}
    h1 {{ margin: 0; font-size: 28px; }}
    h2 {{ font-size: 18px; margin: 0 0 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .metric {{ background: white; border: 1px solid #d7dce2; border-radius: 6px; padding: 14px; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #d7dce2; }}
    th, td {{ padding: 8px 10px; border-bottom: 1px solid #e6e9ed; text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ background: #edf1f5; font-weight: 700; }}
    a {{ color: #0b5cad; }}
    code {{ font-family: Consolas, monospace; }}
  </style>
</head>
<body>
  <header>
    <h1>Codex Ops Dashboard</h1>
    <p>{esc(operating.get('project', {}).get('identity'))} / read-only static dashboard</p>
  </header>
  <main>
    <section>
      <h2>Operating State</h2>
      <div class="grid">
        <div class="metric">Project<strong>{esc(operating.get('project', {}).get('name'))}</strong></div>
        <div class="metric">Identity<strong>{esc(operating.get('project', {}).get('identity'))}</strong></div>
        <div class="metric">Updated<strong>{esc(operating.get('project', {}).get('updated_at'))}</strong></div>
        <div class="metric">Tasks<strong>{esc(len(tasks))}</strong></div>
        <div class="metric">Documents<strong>{esc(len(docs))}</strong></div>
      </div>
    </section>
    <section><h2>Active Tasks</h2>{table(['Task', 'Title', 'Priority', 'Profile'], [[t.get('task_id'), t.get('title'), t.get('priority'), t.get('profile')] for t in active])}</section>
    <section><h2>Blocked Tasks</h2>{table(['Task', 'Title', 'Priority', 'Profile'], [[t.get('task_id'), t.get('title'), t.get('priority'), t.get('profile')] for t in blocked])}</section>
    <section><h2>Review Tasks</h2>{table(['Task', 'Title', 'Priority', 'Profile'], [[t.get('task_id'), t.get('title'), t.get('priority'), t.get('profile')] for t in review])}</section>
    <section><h2>Recently Done Tasks</h2>{table(['Task', 'Title', 'Priority', 'Profile'], [[t.get('task_id'), t.get('title'), t.get('priority'), t.get('profile')] for t in done])}</section>
    <section><h2>Task Detail Table</h2>{table(['Task', 'Title', 'Status', 'Priority', 'Profile', 'Closeout', 'Updated'], task_rows)}</section>
    <section><h2>Required Validators</h2>{table(['Task', 'Validator'], validator_rows)}</section>
    <section><h2>Artifact Links</h2>{table(['Task', 'Artifact'], [[task, link(path)] for task, path in artifact_rows])}</section>
    <section><h2>Document Status Summary</h2>{table(['Status', 'Count'], [[k, v] for k, v in sorted(doc_counts.items())])}</section>
    <section><h2>Context Bundle Token Usage</h2>{table(['Manifest', 'Files', 'Tokens'], context_usage())}</section>
    <section><h2>Validation Reports</h2>{table(['Report', 'Result'], validation_summaries())}</section>
    <section><h2>Hard Boundaries</h2>{table(['Boundary', 'State'], [[k, v] for k, v in hard.items()])}</section>
  </main>
</body>
</html>
"""
    output = ROOT / "ops" / "dashboard" / "index.html"
    write_text(output, html_doc)
    print(f"PASS dashboard: {rel(output)}")
    print(f"PASS dashboard_summary: {rel(summary_path)}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
