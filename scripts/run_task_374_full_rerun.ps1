param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$DbPath = "trading.db",
    [string]$CaptureBatchId = "task374_prod",
    [string]$OutDir = "docs\\reports\\task_374_forward_pure_breakout",
    [string]$StdoutPath = "",
    [string]$StderrPath = "",
    [string]$StatusPath = "",
    [switch]$Detached
)

$ErrorActionPreference = "Stop"

$logDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$stdout = if ($StdoutPath) { $StdoutPath } else { Join-Path $logDir "task374_full_rerun_stdout.log" }
$stderr = if ($StderrPath) { $StderrPath } else { Join-Path $logDir "task374_full_rerun_stderr.log" }
$status = if ($StatusPath) { $StatusPath } else { Join-Path $logDir "task374_full_rerun_status.txt" }

if ($Detached) {
    $runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $stdout = Join-Path $logDir "task374_full_rerun_stdout_$runStamp.log"
    $stderr = Join-Path $logDir "task374_full_rerun_stderr_$runStamp.log"
    $status = Join-Path $logDir "task374_full_rerun_status.txt"
    if (Test-Path $status) {
        Remove-Item $status -Force
    }
    $cmd = "& '" + $PSCommandPath + "' -Root '" + $Root + "' -DbPath '" + $DbPath + "' -CaptureBatchId '" + $CaptureBatchId + "' -OutDir '" + $OutDir + "' -StdoutPath '" + $stdout + "' -StderrPath '" + $stderr + "' -StatusPath '" + $status + "'"
    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd)
    $proc = Start-Process powershell -ArgumentList $args -WorkingDirectory $Root -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -PassThru
    "STARTED:$($proc.Id)" | Set-Content -Path $status -Encoding utf8
    Write-Output "PID=$($proc.Id)"
    Write-Output "STATUS=$status"
    Write-Output "STDOUT=$stdout"
    Write-Output "STDERR=$stderr"
    exit 0
}

"RUNNING" | Set-Content -Path $status -Encoding utf8
Set-Location $Root
$env:PYTHONPATH = "src"

try {
    python -m src.backtest.analysis_structural_breakout_forward_pure_breakout_374 --db-path $DbPath --capture-batch-id $CaptureBatchId --out-dir $OutDir
    $exitCode = $LASTEXITCODE
}
catch {
    $_ | Out-String | Set-Content -Path $stderr -Encoding utf8
    $exitCode = 1
}

if ($exitCode -eq 0) {
    "DONE" | Set-Content -Path $status -Encoding utf8
}
else {
    "FAIL:$exitCode" | Set-Content -Path $status -Encoding utf8
    exit $exitCode
}
