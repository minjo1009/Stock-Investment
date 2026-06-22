param(
    [string]$DbPath = "trading.db",
    [string]$EnvFile = "config/kis_paper.env",
    [switch]$DryRun,
    [string]$FailedComponent = "",
    [string]$ExternalStackTrace = "",
    [string[]]$ExternalFailureReasons = @()
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

$env:PYTHONPATH = "src"

$args = @(
    "-m", "app.task_087_pilot_evidence",
    "--db-path", $DbPath,
    "--env-file", $EnvFile
)

if ($DryRun) {
    $args += "--dry-run"
}
if ($FailedComponent -and $FailedComponent.Trim().Length -gt 0) {
    $args += @("--failed-component", $FailedComponent)
}
if ($ExternalStackTrace -and $ExternalStackTrace.Trim().Length -gt 0) {
    $args += @("--external-stack-trace", $ExternalStackTrace)
}
foreach ($reason in $ExternalFailureReasons) {
    if ($reason -and $reason.Trim().Length -gt 0) {
        $args += @("--external-failure-reason", $reason)
    }
}

python @args
exit $LASTEXITCODE
