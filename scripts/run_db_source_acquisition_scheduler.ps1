param(
    [string]$Config = "configs/db_source_acquisition_scheduler.json",
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
    throw "Missing DB source acquisition scheduler config: $Config"
}

$env:PYTHONPATH = "src" + [System.IO.Path]::PathSeparator + $env:PYTHONPATH
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stdout = Join-Path $LogDir "db_source_acquisition_scheduler_stdout.log"
$stderr = Join-Path $LogDir "db_source_acquisition_scheduler_stderr.log"

function Get-BucketTs([datetime]$NowUtc, [int]$IntervalMinutes) {
    $minute = [math]::Floor($NowUtc.Minute / $IntervalMinutes) * $IntervalMinutes
    $bucket = [datetime]::SpecifyKind(
        (Get-Date -Year $NowUtc.Year -Month $NowUtc.Month -Day $NowUtc.Day -Hour $NowUtc.Hour -Minute $minute -Second 0),
        [DateTimeKind]::Utc
    )
    return $bucket.ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Test-Due([datetime]$NowUtc, [int]$IntervalMinutes) {
    $minuteOfDay = ($NowUtc.Hour * 60) + $NowUtc.Minute
    return ($NowUtc.Second -eq 0 -and ($minuteOfDay % $IntervalMinutes) -eq 0)
}

function Add-ArgsForList([object[]]$Values, [string]$Flag, [System.Collections.ArrayList]$Args) {
    foreach ($value in @($Values)) {
        $text = [string]$value
        if ($text.Trim()) {
            [void]$Args.Add($Flag)
            [void]$Args.Add($text.Trim())
        }
    }
}

$runCount = 0
while ($true) {
    if ($MaxRuns -gt 0 -and $runCount -ge $MaxRuns) {
        break
    }
    $runCount += 1
    $nowUtc = [DateTime]::UtcNow
    $stamp = $nowUtc.ToString("o")
    $configObj = Get-Content -Raw -Path $Config | ConvertFrom-Json
    $artifactDir = [string]$configObj.artifact_dir
    if (-not $artifactDir) {
        $artifactDir = "data/artifacts/task_3761_3800_db_source_scheduler_config_freshness_validator/scheduler_runs"
    }
    $secUserAgentEnvName = [string]$configObj.sec_user_agent_env_name
    $secUserAgentEnvFile = [string]$configObj.sec_user_agent_env_file
    if ($secUserAgentEnvName -and -not [Environment]::GetEnvironmentVariable($secUserAgentEnvName, "Process") -and $secUserAgentEnvFile -and (Test-Path $secUserAgentEnvFile)) {
        $secUserAgentValue = (Get-Content -Raw -Path $secUserAgentEnvFile).Trim()
        if ($secUserAgentValue -and -not $secUserAgentValue.Contains("example.com") -and -not $secUserAgentValue.Contains("TODO")) {
            [Environment]::SetEnvironmentVariable($secUserAgentEnvName, $secUserAgentValue, "Process")
        }
    }
    New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

    foreach ($job in @($configObj.jobs)) {
        if ($job.enabled -ne $true) {
            continue
        }
        $intervalMinutes = [int]$job.interval_minutes
        if ($intervalMinutes -lt 1) {
            throw "Job interval_minutes must be positive: $($job.name)"
        }
        if (-not $ForceDue -and -not (Test-Due $nowUtc $intervalMinutes)) {
            continue
        }
        $bucket = Get-BucketTs $nowUtc $intervalMinutes
        $safeJobName = ([string]$job.name) -replace '[^A-Za-z0-9_.-]', '_'
        Add-Content -Path $stdout -Value "[$stamp] RUN db source scheduler job=$safeJobName bucket=$bucket"

        $families = @($job.families)
        if ($families.Count -gt 0) {
            $jsonPath = Join-Path $artifactDir "$safeJobName`_$($bucket.Replace(':','').Replace('-','')).json"
            $argsList = [System.Collections.ArrayList]@("-m", "tools.db.run_source_acquisition_once", "--apply", "--bucket", $bucket, "--json", $jsonPath)
            $allowNetwork = [bool]$configObj.default_allow_network
            if ($job.PSObject.Properties.Name -contains "allow_network") {
                $allowNetwork = [bool]$job.allow_network
            }
            if ($allowNetwork) {
                [void]$argsList.Add("--allow-network")
            }
            Add-ArgsForList -Values $families -Flag "--family" -Args $argsList
            Add-ArgsForList -Values @($job.symbols) -Flag "--symbol" -Args $argsList
            Add-ArgsForList -Values @($job.macro_series) -Flag "--macro-series" -Args $argsList
            & python @argsList 1>> $stdout 2>> $stderr
            if ($LASTEXITCODE -ne 0) {
                Add-Content -Path $stderr -Value "[$stamp] source acquisition job=$safeJobName exit_code=$LASTEXITCODE"
            }
        }

        $registeredJson = Join-Path $artifactDir "$safeJobName`_registered_loop_$($bucket.Replace(':','').Replace('-','')).json"
        & python -m tools.db.run_registered_loop_once --apply --bucket-ts $bucket --json $registeredJson 1>> $stdout 2>> $stderr
        if ($LASTEXITCODE -ne 0) {
            Add-Content -Path $stderr -Value "[$stamp] registered loop after job=$safeJobName exit_code=$LASTEXITCODE"
        }
    }
    if ($MaxRuns -eq 1) {
        break
    }
    Start-Sleep -Seconds $IntervalSeconds
}
