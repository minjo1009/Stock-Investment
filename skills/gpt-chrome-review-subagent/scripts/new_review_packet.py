#!/usr/bin/env python
"""Create a bounded GPT/Chrome review packet for this repository."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import sys
from textwrap import dedent


LANES = {
    "strategy": ("Regime Research", "Research Governance"),
    "backtest": ("Backtest & Simulation Infra", "Research Governance"),
    "frontend": ("Frontend/UI", "Research Governance"),
    "data": ("Data & Market Microstructure", "Research Governance"),
    "execution": ("Execution & Risk", "Data & Market Microstructure"),
    "slack": ("Slack/EOD", "Research Governance"),
    "chart": ("Chart Evidence", "Intraday Continuation Research"),
    "governance": ("Research Governance", "Relevant owner team"),
}


def clean_task_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise argparse.ArgumentTypeError("task-id must use letters, digits, underscore, or hyphen")
    return value


def build_packet(args: argparse.Namespace) -> str:
    owner, reviewer = LANES[args.lane]
    artifacts = "\n".join(f"- {item}" for item in args.artifact) if args.artifact else "- not provided"
    validations = "\n".join(f"- {item}" for item in args.validation) if args.validation else "- not provided"
    return dedent(
        f"""\
# GPT/Chrome Review Packet

## Intake

- task_id: `{args.task_id}`
- review_date: `{args.review_date}`
- lane: `{args.lane}`
- objective: {args.objective}
- owner_team: {owner}
- reviewer_team: {reviewer}
- output_class: `review_notes` or `ideation_notes`

## Source Artifacts To Provide

{artifacts}

## Validation Commands To Preserve

{validations}

## Validation Authority Boundary

Use `docs/architecture/test_validation_canonicalization_map.md`.

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN

## GPT/Chrome Prompt

You are a skeptical reviewer for a governed quant trading repository.
Review only the supplied excerpts, screenshots, and artifact paths.
Return findings that can be mapped back to repo-native evidence.

Answer these questions:

1. Which statement sounds stronger than the supplied evidence?
2. Which raw source, exact ID, manifest, or validation command is missing?
3. Could this be mistaken for strategy acceptance or deployment readiness?
4. Is any proxy PnL, runtime synthetic SELL, Slack success, UI polish, or screenshot success being promoted as broker truth?
5. What repo-native validation should run next?
6. What validation authority lane applies, and what does PASS not mean?

## Forbidden Actions

- Do not declare the strategy accepted, profitable, or deployment-ready.
- Do not infer lifecycle identity by symbol/date/price/time proximity.
- Do not invent raw sources, labels, fills, metrics, or chart markers.
- Do not treat missing labels as negatives.
- Do not change registry, readiness, blocker, or acceptance status.
- Do not request secrets, tokens, cookies, passwords, or full private raw datasets.
- Do not treat passing tests as strategy acceptance, deployment readiness, broker truth completion, or real-capital permission.

## Return Format

```text
review_status: review_notes | ideation_notes | rejected
findings:
- severity:
  evidence_reference:
  issue:
  repo_native_validation:
  validation_authority:
  owner_team:
  pass_does_not_mean:
forbidden_output_detected:
- ...
next_action:
- ...
```
        """
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True, type=clean_task_id)
    parser.add_argument("--lane", required=True, choices=sorted(LANES))
    parser.add_argument("--objective", required=True)
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--validation", action="append", default=[])
    parser.add_argument("--review-date", default=date.today().isoformat())
    parser.add_argument("--output-root", default="docs/reports")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    packet = build_packet(args)
    if args.dry_run:
        print(packet)
        return 0

    target_dir = Path(args.output_root) / args.task_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "gpt_chrome_review_packet.md"
    target.write_text(packet, encoding="utf-8")
    print(target.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
