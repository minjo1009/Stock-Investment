# CodeRabbit Status

CodeRabbit was requested for this audit. The Windows PowerShell environment could not run the CLI directly, so WSL was used.

## Checks

| Check | Result |
|---|---|
| `.git` directory | present |
| Windows `git` command | not available in PATH |
| Windows `coderabbit` command | not available in PATH |
| WSL `git` command | available |
| WSL CodeRabbit install | installed manually from the official Linux x64 zip |
| WSL CodeRabbit review | blocked by agent authentication timeout |

## PowerShell Install Failure

```text
sh : The term 'sh' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

## WSL Install Notes

The official installer required `unzip`, which was missing in WSL. The Linux x64 zip was downloaded from the official CodeRabbit release URL and extracted with Python's standard `zipfile` module to:

```text
/home/minjo1009/.local/bin/coderabbit
```

## Review Failure

CodeRabbit review commands reached the agent authentication flow, then timed out waiting for browser authentication.

```text
authentication_failed: Automatic login timed out. Use the printed fallback URL to finish authentication.
```

## Consequence

No CodeRabbit review was completed. Findings in the A004 audit report are repository-local operating-system audit findings, not CodeRabbit findings.

## Resolution

Authenticate the installed WSL CodeRabbit CLI, then rerun the review:

```bash
/home/minjo1009/.local/bin/coderabbit auth login --agent
/home/minjo1009/.local/bin/coderabbit review --agent -c AGENTS.md --dir docs/active
```
