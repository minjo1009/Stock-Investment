# TASK-4115 Dirty Worktree Generated Data Ignore Cleanup

## Goal

Reduce unrelated dirty worktree noise from generated data outputs without
deleting source/test/app work or operational data.

## Results

- Added generated-data ignore rules to `.gitignore`.
- Ignored `data/artifacts/`, `data/raw/`, snapshots, readonly MCP exports,
  frontend snapshots, local DB files, local JSONL captures, and local `config/*.env`.
- Reduced untracked `data` exposure from 248,454 files to 2 top-level files
  under `git ls-files --others --exclude-standard` grouping.
- Preserved tracked DVC pointer deletions and source/test/app changes for
  explicit commit/stash handling instead of deleting them.

## Dirty Worktree After Ignore

Tracked-only dirty status:

- deleted tracked files: 104
- modified tracked files: 16

Untracked groups still exist outside generated data:

- docs
- src
- scripts
- tests
- apps
- tools
- ops
- skills

These are not safe to delete by ignore policy alone.

## Safety Boundary Check

- Broker mutation: none.
- Live order: none.
- Paper promotion: none.
- Real capital: none.
- DB schema: none.
- Scheduler code: none.
- Strategy acceptance: unchanged.
