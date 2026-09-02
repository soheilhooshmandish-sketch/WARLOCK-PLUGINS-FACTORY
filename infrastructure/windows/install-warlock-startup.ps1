$ErrorActionPreference = "Stop"

$TaskName = "Warlock Plugins Factory"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Supervisor = Join-Path $PSScriptRoot "warlock-supervisor.ps1"
$HiddenLauncher = Join-Path $PSScriptRoot "run-warlock-supervisor-hidden.vbs"
$RuntimeDir = Join-Path $ProjectRoot ".warlock\runtime"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$WScript = "$env:SystemRoot\System32\wscript.exe"

if (-not (Test-Path -LiteralPath $Supervisor -PathType Leaf)) { throw "Supervisor not found: $Supervisor" }
if (-not (Test-Path -LiteralPath $HiddenLauncher -PathType Leaf)) { throw "Hidden launcher not found: $HiddenLauncher" }
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Virtual environment Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Requirements -PathType Leaf)) { throw "Requirements file not found: $Requirements" }

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

$RequiredVariables = @("WARLOCK_AGENT_TOKEN", "WARLOCK_CF_TEAM_DOMAIN", "WARLOCK_CF_ACCESS_AUD")
foreach ($Name in $RequiredVariables) {
    $Value = [Environment]::GetEnvironmentVariable($Name, "User")
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Required user environment variable is missing: $Name" }
}

function Stop-WarlockPidFile {
    param([Parameter(Mandatory = $true)][string]$PidFile, [Parameter(Mandatory = $true)][string]$ExpectedText)
    if (-not (Test-Path -LiteralPath $PidFile -PathType Leaf)) { return }
    $RawPid = (Get-Content -LiteralPath $PidFile -Raw).Trim()
    $ProcessId = 0
    if ([int]::TryParse($RawPid, [ref]$ProcessId)) {
        $Process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
        if ($null -ne $Process -and $Process.CommandLine -like "*$ExpectedText*") {
            Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        }
    }
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
}

Write-Host "Updating Warlock runtime dependencies..."
& $Python -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed with exit code $LASTEXITCODE" }

$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -ne $ExistingTask -and $ExistingTask.State -eq "Running") {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Stop-WarlockPidFile (Join-Path $RuntimeDir "supervisor.pid") "warlock-supervisor.ps1"
Stop-WarlockPidFile (Join-Path $RuntimeDir "agent.pid") "apps.local_agent.run_agent"
Stop-WarlockPidFile (Join-Path $RuntimeDir "gateway.pid") "apps.gateway.server:app"
Stop-WarlockPidFile (Join-Path $RuntimeDir "mcp.pid") "apps.mcp_server.run_mcp"
Stop-WarlockPidFile (Join-Path $RuntimeDir "tunnel.pid") "warlock-agent"

$UserId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$LauncherArguments = '"{0}"' -f $HiddenLauncher
$Action = New-ScheduledTaskAction -Execute $WScript -Argument $LauncherArguments -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $UserId

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

$Principal = New-ScheduledTaskPrincipal -UserId $UserId -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Starts and supervises the Warlock Local Agent, Gateway, MCP server, and Cloudflare Tunnel without opening a console window." `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 8

$Task = Get-ScheduledTask -TaskName $TaskName
$Info = Get-ScheduledTaskInfo -TaskName $TaskName

Write-Host "Warlock startup installed."
Write-Host "User: $UserId"
Write-Host "Task state: $($Task.State)"
Write-Host "Last task result: $($Info.LastTaskResult)"
Write-Host "Launcher: hidden VBS -> supervisor"
Write-Host "MCP: http://127.0.0.1:8790/mcp"
Write-Host "Logs: .warlock\runtime"
