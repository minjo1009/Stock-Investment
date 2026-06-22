param(
    [int]$Port = 5173,
    [string]$TailscaleExe = "C:\Program Files\Tailscale\tailscale.exe"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $TailscaleExe)) {
    throw "Tailscale CLI not found: $TailscaleExe"
}

$status = & $TailscaleExe status 2>&1
if ($LASTEXITCODE -ne 0 -or ($status -join "`n") -match "Logged out|NeedsLogin") {
    throw "Tailscale is not logged in. Run: `"$TailscaleExe`" up"
}

& $TailscaleExe serve --bg $Port
if ($LASTEXITCODE -ne 0) {
    throw "tailscale serve failed for port $Port"
}

Write-Host "[TAILSCALE_SERVE_OK]"
& $TailscaleExe serve status
