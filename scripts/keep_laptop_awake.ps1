$ErrorActionPreference = "Stop"

Add-Type @"
using System;
using System.Runtime.InteropServices;

public static class AwakeNative {
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern uint SetThreadExecutionState(uint esFlags);
}
"@

$ES_CONTINUOUS = [Convert]::ToUInt32("80000000", 16)
$ES_SYSTEM_REQUIRED = [Convert]::ToUInt32("00000001", 16)
$ES_AWAYMODE_REQUIRED = [Convert]::ToUInt32("00000040", 16)
$flags = $ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_AWAYMODE_REQUIRED
$script:ScriptPath = $MyInvocation.MyCommand.Path

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$logPath = Join-Path $root "logs\keep_laptop_awake.log"
$statusPath = Join-Path $root "data\artifacts\l0_source_acquisition\keep_laptop_awake_status.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $logPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $statusPath) | Out-Null

function UtcNowText {
    return [DateTimeOffset]::UtcNow.ToString("o")
}

function Write-KeepAwakeStatus {
    $status = @{
        updated_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
        started_at = $script:StartedAt
        pid = $PID
        script = $script:ScriptPath
        mode = "SetThreadExecutionState"
        scheduled_task = "not_used"
    }
    $status | ConvertTo-Json -Depth 5 | Set-Content -Path $statusPath -Encoding UTF8
}

"$(UtcNowText) [KEEP_AWAKE_START] pid=$PID" | Add-Content -Path $logPath -Encoding UTF8
$script:StartedAt = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
Write-KeepAwakeStatus

try {
    while ($true) {
        [AwakeNative]::SetThreadExecutionState($flags) | Out-Null
        Write-KeepAwakeStatus
        "$(UtcNowText) [KEEP_AWAKE_HEARTBEAT] pid=$PID" | Add-Content -Path $logPath -Encoding UTF8
        Start-Sleep -Seconds 60
    }
} finally {
    [AwakeNative]::SetThreadExecutionState($ES_CONTINUOUS) | Out-Null
    "$(UtcNowText) [KEEP_AWAKE_STOP] pid=$PID" | Add-Content -Path $logPath -Encoding UTF8
}
