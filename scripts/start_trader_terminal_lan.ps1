param(
    [int]$Port = 5173,
    [switch]$SkipCatalogBuild,
    [switch]$StopExisting
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$frontendRoot = Join-Path $projectRoot "frontend/trader-terminal"

Set-Location $projectRoot
if (-not $SkipCatalogBuild) {
    python scripts/build_trader_terminal_catalog.py
}

if ($StopExisting) {
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.ProcessId -ne $PID -and
            $_.Name -match "node|cmd|powershell" -and
            ($_.CommandLine -match "trader-terminal" -or $_.CommandLine -match "vite")
        } |
        ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
                Write-Host "[TRADER_TERMINAL_LAN] stopped existing process pid=$($_.ProcessId)"
            } catch {
                Write-Warning "[TRADER_TERMINAL_LAN] could not stop pid=$($_.ProcessId): $($_.Exception.Message)"
            }
        }
}

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
    Write-Host "[TRADER_TERMINAL_LAN] already listening on port $Port pid=$($listener.OwningProcess)"
    return
}

Set-Location $frontendRoot
if (-not (Test-Path "node_modules")) {
    npm install
}
if (-not (Test-Path "dist")) {
    npm run build
}

$ip = (Get-NetIPConfiguration |
    Where-Object { $_.IPv4Address -and $_.NetAdapter.Status -eq "Up" } |
    Select-Object -First 1 -ExpandProperty IPv4Address |
    Select-Object -First 1 -ExpandProperty IPAddress)

Write-Host "[TRADER_TERMINAL_LAN] local=http://127.0.0.1:$Port"
if ($ip) {
Write-Host "[TRADER_TERMINAL_LAN] phone=http://$ip`:$Port"
}
Write-Host "[TRADER_TERMINAL_LAN] serving built app; keep this PowerShell session open while monitoring."

cmd /c node_modules\.bin\vite.cmd preview --host 0.0.0.0 --port $Port --strictPort
