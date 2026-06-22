param(
    [int]$IntervalMinutes = 5,
    [string]$DbPath = "trading.db",
    [string]$EnvFile = "config/kis_paper.env",
    [string]$Symbols = "",
    [int]$MaxRuns = 0
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

if ($IntervalMinutes -lt 0) {
    Write-Warning "[PARAM INVALID] IntervalMinutes cannot be negative. Skipping execution."
    exit 0
}
if ($IntervalMinutes -eq 0) {
    Write-Warning "[PARAM GUARD] IntervalMinutes=0 is test mode (no sleep)."
}

function Test-UsMarketSession {
    try {
        $tz = [System.TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time")
    } catch {
        return $false
    }
    $nowUtc = [DateTime]::UtcNow
    $ny = [System.TimeZoneInfo]::ConvertTimeFromUtc($nowUtc, $tz)

    # Monday=1 .. Friday=5
    $dow = [int]$ny.DayOfWeek
    if ($dow -eq 0 -or $dow -eq 6) { return $false }

    $minutes = ($ny.Hour * 60) + $ny.Minute
    $open = (9 * 60) + 35
    $close = (15 * 60) + 50
    return ($minutes -ge $open -and $minutes -le $close)
}

function Get-SymbolList {
    param([string]$RawSymbols)
    if (-not $RawSymbols) { return @() }
    $tokens = $RawSymbols.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
    if ($tokens.Count -eq 0) {
        Write-Warning "[PARAM GUARD] Symbols value was empty after parsing. Falling back to default selector."
        return @()
    }
    return $tokens
}

function Invoke-StepScript {
    param(
        [string]$StepName,
        [string]$ScriptPath,
        [hashtable]$StepArgs
    )
    try {
        & $ScriptPath @StepArgs
        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 0 }
        if ($code -ne 0) {
            return @{
                ok = $false
                code = [int]$code
                reason = "STEP_NON_ZERO_EXIT"
                stack = ""
            }
        }
        return @{
            ok = $true
            code = 0
            reason = ""
            stack = ""
        }
    } catch {
        return @{
            ok = $false
            code = -1
            reason = "STEP_EXCEPTION"
            stack = ($_.Exception | Out-String)
        }
    }
}

$runCount = 0
Write-Host "[LOOP START] interval=${IntervalMinutes}m db=$DbPath env_file=$EnvFile"
$symbolList = Get-SymbolList -RawSymbols $Symbols

while ($true) {
    if ($MaxRuns -gt 0 -and $runCount -ge $MaxRuns) {
        Write-Host "[LOOP STOP] reached max runs: $MaxRuns"
        break
    }

    if (Test-UsMarketSession) {
        $runCount += 1
        Write-Host "[RUN $runCount] market session open - executing Task 089 -> Task 087 -> Task 088"

        $task089Args = @{
            DbPath = $DbPath
            EnvFile = $EnvFile
        }
        if ($symbolList.Count -gt 0) {
            $task089Args["Symbols"] = ($symbolList -join ",")
        }

        $step089 = Invoke-StepScript -StepName "task_089" -ScriptPath (Join-Path $PSScriptRoot "run_task_089_market_refresh.ps1") -StepArgs $task089Args
        $externalFailureReasons = @()
        $failedComponent = ""
        $externalStackTrace = ""
        $task087DryRun = $false
        if (-not $step089.ok) {
            Write-Warning "[RUN $runCount] Task 089 failed code=$($step089.code) reason=$($step089.reason)"
            $externalFailureReasons += "TASK_089_FAILED"
            $externalFailureReasons += "TASK_089_$($step089.reason)"
            $failedComponent = "task_089"
            $externalStackTrace = $step089.stack
            $task087DryRun = $true
        }

        $task087Args = @{
            DbPath = $DbPath
            EnvFile = $EnvFile
        }
        if ($task087DryRun) {
            $task087Args["DryRun"] = $true
            if ($failedComponent -ne "") {
                $task087Args["FailedComponent"] = $failedComponent
            }
            if ($externalStackTrace -ne "") {
                $task087Args["ExternalStackTrace"] = $externalStackTrace
            }
            if ($externalFailureReasons.Count -gt 0) {
                $task087Args["ExternalFailureReasons"] = $externalFailureReasons
            }
        }

        $step087 = Invoke-StepScript -StepName "task_087" -ScriptPath (Join-Path $PSScriptRoot "run_task_087_paper_pilot.ps1") -StepArgs $task087Args
        if (-not $step087.ok) {
            Write-Warning "[RUN $runCount] Task 087 failed code=$($step087.code) reason=$($step087.reason)"
        }

        $step088 = Invoke-StepScript -StepName "task_088" -ScriptPath (Join-Path $PSScriptRoot "run_task_088_evidence_decision.ps1") -StepArgs @{}
        if (-not $step088.ok) {
            Write-Warning "[RUN $runCount] Task 088 failed code=$($step088.code) reason=$($step088.reason)"
        }
    } else {
        Write-Host "[WAIT] outside US market session, sleeping..."
    }

    Start-Sleep -Seconds ($IntervalMinutes * 60)
}
