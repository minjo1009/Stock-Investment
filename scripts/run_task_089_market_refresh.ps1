param(
    [string]$DbPath = "trading.db",
    [string]$EnvFile = "config/kis_paper.env",
    [string]$Symbols = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

$env:PYTHONPATH = "src"

$args = @(
    "-m", "app.task_089_market_data_signal_refresh",
    "--db-path", $DbPath,
    "--env-file", $EnvFile
)

if ($Symbols -and $Symbols.Trim().Length -gt 0) {
    $args += @("--symbols", $Symbols)
}

python @args
exit $LASTEXITCODE

