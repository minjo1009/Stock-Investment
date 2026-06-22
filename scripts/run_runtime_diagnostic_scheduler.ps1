param(
    [string]$Config = "configs/runtime_diagnostic_scheduler.json",
    [int]$IntervalSeconds = 60,
    [int]$MaxRuns = 0,
    [switch]$ForceDue,
    [string]$LogDir = "logs"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

if ($IntervalSeconds -lt 1) {
    throw "IntervalSeconds must be positive."
}
if (-not (Test-Path $Config)) {
    throw "Missing runtime scheduler config: $Config"
}

$env:PYTHONPATH = "src" + [System.IO.Path]::PathSeparator + $env:PYTHONPATH
$env:KIS_ENVIRONMENT = "paper"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stdout = Join-Path $LogDir "runtime_diagnostic_scheduler_stdout.log"
$stderr = Join-Path $LogDir "runtime_diagnostic_scheduler_stderr.log"

$runCount = 0
while ($true) {
    if ($MaxRuns -gt 0 -and $runCount -ge $MaxRuns) {
        break
    }
    $runCount += 1
    $args = @("-m", "src.app.runtime_scheduler_supervisor", "--config", $Config)
    if ($ForceDue) {
        $args += "--force-due"
    }
    $stamp = [DateTime]::UtcNow.ToString("o")
    Add-Content -Path $stdout -Value "[$stamp] RUN runtime diagnostic scheduler supervisor"
    & python @args 1>> $stdout 2>> $stderr
    if ($LASTEXITCODE -ne 0) {
        Add-Content -Path $stderr -Value "[$stamp] supervisor exit_code=$LASTEXITCODE"
        if ($MaxRuns -eq 1) {
            exit $LASTEXITCODE
        }
    }
    if ($MaxRuns -eq 1) {
        break
    }
    Start-Sleep -Seconds $IntervalSeconds
}
