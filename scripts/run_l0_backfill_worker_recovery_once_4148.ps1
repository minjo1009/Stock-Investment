param(
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
if ($ProjectRoot -eq "") {
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
Set-Location -LiteralPath $ProjectRoot

python (Join-Path $ProjectRoot "scripts\run_l0_backfill_worker_recovery_4148.py")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
