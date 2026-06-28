param(
    [string]$Sources = "prnewswire,globenewswire",
    [int]$MaxHeadlines = 25,
    [string]$RawDir = "data/raw/l0_public_headline_browser_smoke",
    [string]$EventPath = "data/artifacts/l0_public_headline_browser_smoke/collector_events.jsonl",
    [string]$SummaryPath = "data/artifacts/l0_public_headline_browser_smoke/smoke_summary.json",
    [string]$ChromePath = "C:/Program Files/Google/Chrome/Application/chrome.exe"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$RuntimeRoot = Join-Path $env:USERPROFILE ".cache/codex-runtimes/codex-primary-runtime/dependencies"
$BundledNode = Join-Path $RuntimeRoot "node/bin/node.exe"
$NodeModulePath = Join-Path $RuntimeRoot "node/node_modules"
$PnpmNodeModulePath = Join-Path $RuntimeRoot "node/node_modules/.pnpm/node_modules"

if (Test-Path -LiteralPath $BundledNode) {
    $NodeExe = $BundledNode
    $env:NODE_PATH = "$NodeModulePath;$PnpmNodeModulePath;$env:NODE_PATH"
} else {
    $NodeExe = "node"
}

& $NodeExe "tools/db/source_acquisition/public_headline_browser_crawler.js" `
    "--sources" $Sources `
    "--max-headlines" ([string]$MaxHeadlines) `
    "--raw-dir" $RawDir `
    "--event-path" $EventPath `
    "--summary-path" $SummaryPath `
    "--chrome-path" $ChromePath
