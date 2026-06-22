from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.reporting.readiness_registry import build_readiness_registry_payload


REQUIRED_CARD_TITLES = [
    "Acceptance Status",
    "Broker Truth Coverage",
    "Replay Health",
    "Risk Snapshot Coverage",
    "Concentration Health",
    "Top Blockers",
]


def _status_tone(value: object) -> str:
    text = str(value or "").upper()
    if "FORBIDDEN" in text or "FAIL" in text or "BLOCKED" in text or "NOT_ACCEPTED" in text:
        return "bad"
    if "READY" in text or "PASS" in text or "CLEAR" in text:
        return "good"
    return "warn"


def _priority_rank(blocker: dict[str, Any]) -> tuple[int, str]:
    priority = str(blocker.get("priority") or "")
    if priority.startswith("P") and priority[1:].isdigit():
        return (int(priority[1:]), str(blocker.get("blocker_id") or ""))
    return (99, str(blocker.get("blocker_id") or ""))


def _gate_by_id(registry: dict[str, Any], gate_id: str) -> dict[str, Any]:
    for gate in registry.get("acceptance_gates", []):
        if gate.get("gate_id") == gate_id:
            return gate
    return {}


def _blocker_by_id(registry: dict[str, Any], blocker_id: str) -> dict[str, Any]:
    for blocker in registry.get("blockers", []):
        if blocker.get("blocker_id") == blocker_id:
            return blocker
    return {}


def _card(title: str, value: object, note: object = "", *, evidence: object = "") -> dict[str, Any]:
    return {
        "title": title,
        "value": str(value or "-"),
        "note": str(note or ""),
        "evidence": str(evidence or ""),
        "tone": _status_tone(value),
    }


def _owner_actions(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions = []
    for blocker in sorted(blockers, key=_priority_rank):
        actions.append(
            {
                "blocker_id": blocker.get("blocker_id", ""),
                "priority": blocker.get("priority", ""),
                "owner": blocker.get("owner", ""),
                "team": blocker.get("team", ""),
                "status": blocker.get("status", ""),
                "next_gate": blocker.get("next_gate", ""),
                "artifact": blocker.get("artifact", ""),
                "validation": blocker.get("validation", ""),
            }
        )
    return actions


def build_acceptance_status_catalog(root: Path = Path("."), *, registry_path: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    source_path = registry_path or Path("docs/ownership/readiness_registry.yaml")
    if not source_path.is_absolute():
        source_path = root / source_path
    registry = build_readiness_registry_payload(source_path)
    state = registry.get("registry", {})
    blockers = registry.get("blockers", [])
    top_blockers = sorted(blockers, key=_priority_rank)[:5]

    paper_status = state.get("paper_operation_status") or registry.get("paper_operation", {}).get("status", "")
    strategy_status = state.get("strategy_acceptance_status") or registry.get("strategy_acceptance", {}).get("status", "NOT_ACCEPTED")
    deployment_status = state.get("deployment_readiness_status") or registry.get("deployment_readiness", {}).get("status", "")
    real_capital_status = state.get("real_capital_status") or registry.get("real_capital", {}).get("status", "FORBIDDEN")

    broker_gate = _gate_by_id(registry, "SELL_FILLS_EXIST")
    replay_gate = _gate_by_id(registry, "REPLAY_MATCH_99_PLUS")
    risk_gate = _gate_by_id(registry, "KILL_SWITCH_TESTED")
    concentration_gate = _gate_by_id(registry, "CANDIDATE_FUNNEL_AUDITED")
    broker_blocker = _blocker_by_id(registry, "P0_EXIT_LIFECYCLE")
    replay_blocker = _blocker_by_id(registry, "P0_EXACT_REPLAY")
    concentration_blocker = _blocker_by_id(registry, "P0_CANDIDATE_FUNNEL")

    first_screen_cards = [
        _card(
            "Acceptance Status",
            strategy_status,
            f"Paper {paper_status} / Deployment {deployment_status} / Real Capital {real_capital_status}",
        ),
        _card(
            "Broker Truth Coverage",
            broker_gate.get("current_status") or broker_blocker.get("status"),
            broker_blocker.get("next_gate", ""),
            evidence=broker_gate.get("evidence", ""),
        ),
        _card(
            "Replay Health",
            replay_gate.get("current_status") or replay_blocker.get("status"),
            replay_blocker.get("next_gate", ""),
            evidence=replay_gate.get("evidence", ""),
        ),
        _card(
            "Risk Snapshot Coverage",
            risk_gate.get("current_status", "MISSING_RISK_SNAPSHOT_EVIDENCE"),
            "Kill-switch and risk snapshot evidence remain acceptance gates.",
            evidence=risk_gate.get("evidence", ""),
        ),
        _card(
            "Concentration Health",
            concentration_gate.get("current_status") or concentration_blocker.get("status"),
            concentration_blocker.get("next_gate", ""),
            evidence=concentration_gate.get("evidence", ""),
        ),
        _card(
            "Top Blockers",
            f"{len(top_blockers)} listed",
            " / ".join(blocker.get("blocker_id", "") for blocker in top_blockers[:3]),
            evidence="; ".join(str(blocker.get("status", "")) for blocker in top_blockers[:3]),
        ),
    ]

    generated_utc = datetime.now(UTC).isoformat()
    return {
        "generated_utc": generated_utc,
        "contract_version": "acceptance-status-catalog-v1",
        "source_task": "T603-6",
        "canonical_source": registry.get("canonical_source", source_path.as_posix()),
        "rules": {
            "ui_reads_catalog_only": True,
            "strategy_entry_universe_alpha_changes_allowed": False,
            "deployment_claim_allowed": False,
            "real_capital_allowed": False,
            "missing_source_approximation_allowed": False,
        },
        "paper_status": paper_status,
        "strategy_status": strategy_status,
        "deployment_status": deployment_status,
        "real_capital_status": real_capital_status,
        "banner_values": {
            "Paper": paper_status,
            "Strategy": strategy_status,
            "Deployment": deployment_status,
            "Real Capital": real_capital_status,
        },
        "top_blockers": top_blockers,
        "acceptance_progress": {
            "gate_status_counts": registry.get("acceptance_gate_status_counts", {}),
            "blocker_status_counts": registry.get("blocker_status_counts", {}),
            "gates": registry.get("acceptance_gates", []),
            "first_screen_cards": first_screen_cards,
        },
        "first_screen_cards": first_screen_cards,
        "owner_actions": _owner_actions(blockers),
        "last_updated": generated_utc,
    }


def write_acceptance_status_catalog(payload: dict[str, Any], outputs: list[Path]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str, allow_nan=False)
    for output in outputs:
        output.mkdir(parents=True, exist_ok=True)
        (output / "acceptance_status_catalog.json").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--registry", type=Path, default=Path("docs/ownership/readiness_registry.yaml"))
    parser.add_argument("--out", type=Path, default=Path("frontend_data/catalog"))
    parser.add_argument("--app-public", type=Path, default=Path("frontend/trader-terminal/public/catalog"))
    args = parser.parse_args()
    payload = build_acceptance_status_catalog(args.root, registry_path=args.registry)
    write_acceptance_status_catalog(payload, [args.out, args.app_public])
    print(f"[ACCEPTANCE_STATUS_CATALOG_OK] cards={len(payload['first_screen_cards'])} blockers={len(payload['top_blockers'])}")


if __name__ == "__main__":
    main()
