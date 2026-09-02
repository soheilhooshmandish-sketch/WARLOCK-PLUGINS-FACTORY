$ErrorActionPreference = "Stop"

$TaskName = "Warlock Plugins Factory"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Supervisor = Join-Path $PSScriptRoot "warlock-supervisor.ps1"
$RuntimeDir = Join-Path $ProjectRoot ".warlock\runtime"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$PowerShellExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

if (-not (Test-Path -LiteralPath $Supervisor -PathType Leaf)) { throw "Supervisor not found: $Supervisor" }
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Virtual environment Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Requirements -PathType Leaf)) { throw "Requirements file not found: $Requirements" }
if (-not (Test-Path -LiteralPath $PowerShellExe -PathType Leaf)) { throw "Windows PowerShell not found: $PowerShellExe" }

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

function Test-LocalPort {
    param([Parameter(Mandatory = $true)][int]$Port)
    try {
        return @(Get-NetTCPConnection -LocalAddress "127.0.0.1" -LocalPort $Port -State Listen -ErrorAction Stop).Count -gt 0
    }
    catch {
        return $false
    }
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
$SupervisorArguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $Supervisor
$Action = New-ScheduledTaskAction -Execute $PowerShellExe -Argument $SupervisorArguments -WorkingDirectory $ProjectRoot
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
$AgentListening = Test-LocalPort 8765
$GatewayListening = Test-LocalPort 8780
$McpListening = Test-LocalPort 8790

Write-Host "Warlock startup installed."
Write-Host "User: $UserId"
Write-Host "Task state: $($Task.State)"
Write-Host "Last task result: $($Info.LastTaskResult)"
Write-Host "Launcher: Task Scheduler -> hidden PowerShell supervisor"
Write-Host "Agent 8765 listening: $AgentListening"
Write-Host "Gateway 8780 listening: $GatewayListening"
Write-Host "MCP 8790 listening: $McpListening"
Write-Host "MCP: http://127.0.0.1:8790/mcp"
Write-Host "Logs: .warlock\runtime"

if (-not $McpListening) {
    throw "MCP did not start on 127.0.0.1:8790. Check .warlock\runtime\supervisor.log and mcp.err.log."
}
