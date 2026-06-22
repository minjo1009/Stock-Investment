param(
    [string]$RunsDir = "docs/reports/task_087/runs"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

$env:PYTHONPATH = "src"

$args = @(
    "-m", "app.task_088_evidence_decision",
    "--runs-dir", $RunsDir
)

python @args
exit $LASTEXITCODE

