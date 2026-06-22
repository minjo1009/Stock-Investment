param(
  [int]$IntervalSeconds = 60,
  [int]$RetrySeconds = 10,
  [switch]$Once,
  [string]$Root = ".",
  [string]$LogPath = "data/artifacts/task_3421_expo_scanner_reference_port/catalog_regen_loop.log"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath $Root).Path
$logFullPath = Join-Path $repoRoot $LogPath
$logDir = Split-Path -Parent $logFullPath
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Invoke-CatalogBuild {
  $startedUtc = (Get-Date).ToUniversalTime().ToString("o")
  Add-Content -LiteralPath $logFullPath -Encoding UTF8 -Value "[$startedUtc] catalog build start"
  Push-Location $repoRoot
  try {
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $pythonExe) {
      $pythonExe = (Get-Command py -ErrorAction SilentlyContinue).Source
    }
    if (-not $pythonExe) {
      throw "python executable not found"
    }
    $output = & $pythonExe scripts/build_trader_terminal_catalog.py `
      --paper-ops-only `
      --out frontend_data/catalog `
      --app-public apps/trader-brain-web/public/catalog 2>&1
    $code = $LASTEXITCODE
  } finally {
    Pop-Location
  }
  $finishedUtc = (Get-Date).ToUniversalTime().ToString("o")
  Add-Content -LiteralPath $logFullPath -Encoding UTF8 -Value ($output | Out-String)
  Add-Content -LiteralPath $logFullPath -Encoding UTF8 -Value "[$finishedUtc] catalog build exit=$code"
  if ($code -ne 0) {
    throw "catalog build failed exit=$code"
  }
}

while ($true) {
  $ok = $false
  try {
    Invoke-CatalogBuild
    $ok = $true
  } catch {
    $errorUtc = (Get-Date).ToUniversalTime().ToString("o")
    Add-Content -LiteralPath $logFullPath -Encoding UTF8 -Value "[$errorUtc] ERROR $($_ | Out-String)"
    if ($Once) {
      throw
    }
  }
  if ($Once) {
    break
  }
  Start-Sleep -Seconds $(if ($ok) { $IntervalSeconds } else { $RetrySeconds })
}
