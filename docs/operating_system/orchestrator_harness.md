# Orchestrator Harness Protocol

## Purpose
Every user command enters through the Architecture Orchestrator. The orchestrator classifies the command, assigns a phase/task, selects an owner sub-agent and required skill, creates a handoff packet, and records continuity state.

## Command Flow

1. Intake user command.
2. Classify into `phase_id`, `task_id`, owner agent, sub-agents, required skill, safety level, output path.
3. If confidence is low, create a `needs_clarification` task owned by Architecture Orchestrator.
4. Create task spec under `docs/phases/{PHASE_ID}/tasks/{TASK_ID}.md`.
5. Create handoff/context packet under `docs/phases/{PHASE_ID}/reports/{TASK_ID}/`.
6. Sub-agent executes only within its boundary.
7. Task completion updates `task_state.json` and `agent_memory.json`.
8. Repeatable operating knowledge goes to `skill_update_queue.md`, not directly to skill files.

## External Execution Policy

The harness must not automatically run backtests, Graphify regeneration, broker/API calls, order workflows, or file move/delete migrations. It must mark the task as `requires_user_execution` and provide PowerShell commands.

## Storage Discipline

- Harness files live in `docs/operating_system/`.
- Phase/task artifacts live in `docs/phases/{PHASE_ID}/`.
- Graphify context packs live in `docs/graphify/context_packs/` or the task report folder.
- No one-off output may be written to repo root or bare `docs/` root.

## Memory Rules

- Store validated summaries, constraints, decisions, artifact paths, unresolved blockers.
- Do not store secrets, credentials, raw broker responses, speculative conclusions, or unvalidated claims.

