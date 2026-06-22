from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python -m pip install PyYAML") from exc


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "operating_system" / "harness_manifest.yml"
STATE_PATH = ROOT / "docs" / "operating_system" / "task_state.json"
MEMORY_PATH = ROOT / "docs" / "operating_system" / "agent_memory.json"
SKILL_QUEUE_PATH = ROOT / "docs" / "operating_system" / "skill_update_queue.md"


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def command_id(command: str) -> str:
    return "CMD_" + hashlib.sha1(command.encode("utf-8")).hexdigest()[:12].upper()


def normalize(text: str) -> str:
    return text.casefold()


def classify_command(command: str) -> dict[str, Any]:
    manifest = load_yaml(MANIFEST_PATH)
    text = normalize(command)
    phase_scores: dict[str, int] = {}
    for phase_id, info in manifest["phase_registry"].items():
        score = 0
        for keyword in info.get("keywords", []):
            if normalize(str(keyword)) in text:
                score += 1
        phase_scores[phase_id] = score

    phase_id = max(phase_scores, key=lambda p: phase_scores[p])
    confidence = phase_scores[phase_id]
    if confidence <= 0:
        phase_id = "PHASE_00"

    phase = manifest["phase_registry"][phase_id]
    owner_agent = phase["owner_agent"]
    required_skill = phase["default_skill"]

    safety_terms = manifest["safety_gates"]
    blocked = any(term in text for term in map(normalize, safety_terms.get("blocked_terms", [])))
    requires_user_execution = any(
        term in text for term in map(normalize, safety_terms.get("user_execution_terms", []))
    )
    safety_level = "blocked" if blocked else ("requires_user_execution" if requires_user_execution else "normal")

    powershell_commands: list[str] = []
    external = manifest.get("external_execution_requests", {})
    if "backtest" in text and "backtest" in external:
        powershell_commands.append(external["backtest"]["powershell"])
    if "graphify" in text or "grapphify" in text:
        if "graphify" in external:
            powershell_commands.append(external["graphify"]["powershell"])
    if "validate" in text or "검증" in text:
        if "harness_validation" in external:
            powershell_commands.append(external["harness_validation"]["powershell"])

    status = "needs_clarification" if confidence <= 0 else ("blocked" if blocked else "classified")
    return {
        "command_id": command_id(command),
        "original_command": command,
        "phase_id": phase_id,
        "phase_title": phase["title"],
        "owner_agent": owner_agent,
        "sub_agents": [],
        "required_skill": required_skill,
        "confidence": confidence,
        "status": status,
        "safety_level": safety_level,
        "requires_user_execution": bool(requires_user_execution or blocked),
        "powershell_commands": powershell_commands,
        "routing_scores": phase_scores,
    }


def next_task_id(state: dict[str, Any], phase_id: str) -> str:
    nums: list[int] = []
    for task in state.get("tasks", []):
        if task.get("phase_id") == phase_id:
            match = re.match(r"TASK_(\d{3})$", str(task.get("task_id", "")))
            if match:
                nums.append(int(match.group(1)))
    phase_task_dir = ROOT / "docs" / "phases" / phase_id / "tasks"
    if phase_task_dir.exists():
        for path in phase_task_dir.glob("TASK_*.md"):
            match = re.match(r"TASK_(\d{3})$", path.stem)
            if match:
                nums.append(int(match.group(1)))
    return f"TASK_{(max(nums) + 1) if nums else 1:03d}"


def task_paths(phase_id: str, task_id: str) -> dict[str, Path]:
    base = ROOT / "docs" / "phases" / phase_id
    report_dir = base / "reports" / task_id
    return {
        "phase_dir": base,
        "task_spec": base / "tasks" / f"{task_id}.md",
        "report_dir": report_dir,
        "handoff": report_dir / "handoff.md",
        "summary": report_dir / "summary.md",
        "validation": report_dir / "validation.md",
        "context_pack": report_dir / "context_pack.md",
        "decision": base / "decisions" / f"{task_id}_decision.md",
    }


def create_task(command: str) -> dict[str, Any]:
    classification = classify_command(command)
    state = load_json(STATE_PATH, {"version": 1, "updated_at": None, "tasks": []})
    task_id = next_task_id(state, classification["phase_id"])
    phase_id = classification["phase_id"]
    paths = task_paths(phase_id, task_id)
    for key in ("task_spec", "handoff", "summary", "validation", "context_pack", "decision"):
        paths[key].parent.mkdir(parents=True, exist_ok=True)

    manifest = load_yaml(MANIFEST_PATH)
    storage = manifest["storage_rules"]
    rel = lambda p: p.relative_to(ROOT).as_posix()
    output_artifacts = {
        "task_spec": rel(paths["task_spec"]),
        "handoff": rel(paths["handoff"]),
        "summary": rel(paths["summary"]),
        "validation": rel(paths["validation"]),
        "context_pack": rel(paths["context_pack"]),
        "decision": rel(paths["decision"]),
    }

    now = utc_now()
    task_spec = f"""# {task_id} - Orchestrated Task

## Metadata

- task_id: {task_id}
- phase_id: {phase_id}
- command_id: {classification['command_id']}
- owner_agent: {classification['owner_agent']}
- sub_agents: {classification['sub_agents']}
- required_skill: {classification['required_skill']}
- status: {classification['status']}
- safety_level: {classification['safety_level']}
- requires_user_execution: {str(classification['requires_user_execution']).lower()}

## Original Command

{command}

## Output Locations

- handoff: `{output_artifacts['handoff']}`
- summary: `{output_artifacts['summary']}`
- validation: `{output_artifacts['validation']}`
- context_pack: `{output_artifacts['context_pack']}`
- decision: `{output_artifacts['decision']}`

## File Change Boundary

- allowed roots: `docs/operating_system/`, `docs/phases/`, task-approved files only
- forbidden by default: broker/API calls, order workflows, DB mutation, strategy behavior changes, file moves/deletes

## Acceptance Criteria

- Task result is written to the phase report folder.
- Continuity facts are recorded through `complete-task`.
- External execution, if needed, is requested with PowerShell commands instead of auto-running.
"""
    paths["task_spec"].write_text(task_spec, encoding="utf-8")

    handoff = f"""# Sub-Agent Handoff - {task_id}

- created_at: {now}
- phase_id: {phase_id}
- phase_title: {classification['phase_title']}
- owner_agent: {classification['owner_agent']}
- required_skill: {classification['required_skill']}
- safety_level: {classification['safety_level']}
- requires_user_execution: {classification['requires_user_execution']}

## Original Command

{command}

## Routing Rationale

- routing_scores: `{classification['routing_scores']}`
- confidence: `{classification['confidence']}`

## Required Skill

Use `{classification['required_skill']}` and follow the storage rules in `docs/operating_system/harness_manifest.yml`.

## PowerShell Commands For User Execution

"""
    if classification["powershell_commands"]:
        for cmd in classification["powershell_commands"]:
            handoff += f"```powershell\n{cmd}\n```\n\n"
    else:
        handoff += "- None required at classification time.\n\n"
    handoff += """## Stop Conditions

- Stop before broker/API execution, order submission/cancel/fill workflows, DB mutation, file move/delete migrations, or trading behavior changes unless explicitly approved.

## Required Handoff Output

- changed files:
- artifacts:
- validation:
- continuity facts:
- skill update proposals:
- unresolved risks:
"""
    paths["handoff"].write_text(handoff, encoding="utf-8")

    paths["summary"].write_text(f"# Summary - {task_id}\n\nPending.\n", encoding="utf-8")
    paths["validation"].write_text(f"# Validation - {task_id}\n\nPending.\n", encoding="utf-8")
    paths["context_pack"].write_text(
        f"# Context Pack - {task_id}\n\n- command_id: {classification['command_id']}\n- phase_id: {phase_id}\n- owner_agent: {classification['owner_agent']}\n",
        encoding="utf-8",
    )
    paths["decision"].write_text(f"# Decision - {task_id}\n\nPending.\n", encoding="utf-8")

    record = {
        **classification,
        "task_id": task_id,
        "created_at": now,
        "updated_at": now,
        "artifacts": output_artifacts,
        "validation_result": "pending",
        "unresolved_risks": [],
        "next_recommended_tasks": [],
    }
    state.setdefault("tasks", []).append(record)
    state["updated_at"] = now
    write_json(STATE_PATH, state)
    return record


def context_pack(task_id: str) -> dict[str, Any]:
    state = load_json(STATE_PATH, {"version": 1, "tasks": []})
    task = next((t for t in state.get("tasks", []) if t.get("task_id") == task_id), None)
    if task is None:
        raise SystemExit(f"task not found: {task_id}")
    memory = load_json(MEMORY_PATH, {"version": 1, "agents": {}})
    agent = task["owner_agent"]
    facts = memory.get("agents", {}).get(agent, {}).get("facts", [])
    pack = {
        "task": task,
        "agent_memory": facts[-10:],
        "skill_update_queue": str(SKILL_QUEUE_PATH.relative_to(ROOT)),
    }
    path = ROOT / task["artifacts"]["context_pack"]
    path.write_text("# Context Pack\n\n```json\n" + json.dumps(pack, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    return pack


def complete_task(task_id: str, summary_path: str) -> dict[str, Any]:
    state = load_json(STATE_PATH, {"version": 1, "updated_at": None, "tasks": []})
    task = next((t for t in state.get("tasks", []) if t.get("task_id") == task_id), None)
    if task is None:
        raise SystemExit(f"task not found: {task_id}")
    summary_file = (ROOT / summary_path).resolve()
    if not summary_file.exists():
        raise SystemExit(f"summary path not found: {summary_path}")
    summary = summary_file.read_text(encoding="utf-8", errors="ignore").strip()
    now = utc_now()
    task["status"] = "completed"
    task["updated_at"] = now
    task["summary_path"] = summary_file.relative_to(ROOT).as_posix()
    task["validation_result"] = "completed_from_user_summary"
    task["continuity_summary"] = summary[:1200]
    state["updated_at"] = now
    write_json(STATE_PATH, state)

    memory = load_json(MEMORY_PATH, {"version": 1, "updated_at": None, "agents": {}})
    agent = task["owner_agent"]
    agent_bucket = memory.setdefault("agents", {}).setdefault(agent, {"facts": []})
    agent_bucket.setdefault("facts", []).append(
        {
            "timestamp": now,
            "task_id": task_id,
            "phase_id": task["phase_id"],
            "summary": summary[:1200],
            "artifacts": task.get("artifacts", {}),
        }
    )
    memory["updated_at"] = now
    write_json(MEMORY_PATH, memory)
    return task


def validate_state() -> dict[str, Any]:
    errors: list[str] = []
    manifest = load_yaml(MANIFEST_PATH)
    state = load_json(STATE_PATH, {"version": 1, "tasks": []})
    memory = load_json(MEMORY_PATH, {"version": 1, "agents": {}})
    if "phase_registry" not in manifest:
        errors.append("missing phase_registry")
    if "agent_registry" not in manifest:
        errors.append("missing agent_registry")
    if not isinstance(state.get("tasks", []), list):
        errors.append("task_state.tasks must be a list")
    if not isinstance(memory.get("agents", {}), dict):
        errors.append("agent_memory.agents must be an object")
    for task in state.get("tasks", []):
        for key in ("task_id", "phase_id", "owner_agent", "required_skill", "artifacts", "status"):
            if key not in task:
                errors.append(f"{task.get('task_id', '<unknown>')}: missing {key}")
        for name, rel_path in task.get("artifacts", {}).items():
            if name in {"task_spec", "handoff", "summary", "validation", "context_pack", "decision"}:
                if not (ROOT / rel_path).exists():
                    errors.append(f"{task.get('task_id')}: missing artifact {name}: {rel_path}")
    return {"ok": not errors, "errors": errors, "task_count": len(state.get("tasks", []))}


def main() -> int:
    parser = argparse.ArgumentParser(description="File-based Architecture Orchestrator harness")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("classify")
    p.add_argument("--command", required=True)
    p = sub.add_parser("create-task")
    p.add_argument("--command", required=True)
    p = sub.add_parser("context-pack")
    p.add_argument("--task-id", required=True)
    p = sub.add_parser("complete-task")
    p.add_argument("--task-id", required=True)
    p.add_argument("--summary-path", required=True)
    sub.add_parser("validate-state")
    args = parser.parse_args()

    if args.cmd == "classify":
        payload = classify_command(args.command)
    elif args.cmd == "create-task":
        payload = create_task(args.command)
    elif args.cmd == "context-pack":
        payload = context_pack(args.task_id)
    elif args.cmd == "complete-task":
        payload = complete_task(args.task_id, args.summary_path)
    elif args.cmd == "validate-state":
        payload = validate_state()
    else:  # pragma: no cover
        raise AssertionError(args.cmd)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
