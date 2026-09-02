$ErrorActionPreference = "Stop"

$TaskName = "Warlock Plugins Factory"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RuntimeDir = Join-Path $ProjectRoot ".warlock\runtime"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Pythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$RuntimeChild = Join-Path $ProjectRoot "apps\runtime_child.py"
$RuntimePreflight = Join-Path $ProjectRoot "apps\runtime_preflight.py"
$PhysicalPythonResolver = Join-Path $PSScriptRoot "resolve_physical_python.py"
$Cloudflared = Join-Path $ProjectRoot "infrastructure\cloudflare\cloudflared.exe"
$LegacySupervisor = Join-Path $PSScriptRoot "warlock-supervisor.ps1"
$LegacyVbs = Join-Path $PSScriptRoot "run-warlock-supervisor-hidden.vbs"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Virtual environment Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Requirements -PathType Leaf)) { throw "Requirements file not found: $Requirements" }
if (-not (Test-Path -LiteralPath $RuntimeChild -PathType Leaf)) { throw "Runtime child bootstrap not found: $RuntimeChild" }
if (-not (Test-Path -LiteralPath $RuntimePreflight -PathType Leaf)) { throw "Runtime preflight module not found: $RuntimePreflight" }
if (-not (Test-Path -LiteralPath $PhysicalPythonResolver -PathType Leaf)) { throw "Physical Python resolver not found: $PhysicalPythonResolver" }
if (-not (Test-Path -LiteralPath $Cloudflared -PathType Leaf)) { throw "cloudflared not found: $Cloudflared" }

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

$RequiredVariables = @("WARLOCK_AGENT_TOKEN", "WARLOCK_CF_TEAM_DOMAIN", "WARLOCK_CF_ACCESS_AUD")
foreach ($Name in $RequiredVariables) {
    $Value = [Environment]::GetEnvironmentVariable($Name, "User")
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Required user environment variable is missing: $Name" }
}

function Test-WarlockHealth {
    param(
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][string]$IdentityProperty,
        [Parameter(Mandatory = $true)][string]$IdentityValue
    )

    try {
        $Response = Invoke-RestMethod `
            -Uri "http://127.0.0.1:$Port/health" `
            -Method Get `
            -TimeoutSec 1 `
            -ErrorAction Stop

        if ([string]$Response.status -ne "healthy") { return $false }
        $Identity = $Response.PSObject.Properties[$IdentityProperty]
        if ($null -eq $Identity) { return $false }
        return [string]$Identity.Value -eq $IdentityValue
    }
    catch {
        return $false
    }
}

function Resolve-PhysicalPython {
    $Output = & $Python $PhysicalPythonResolver
    if ($LASTEXITCODE -ne 0) {
        throw "Physical Python resolver failed with exit code $LASTEXITCODE"
    }

    $Resolved = ($Output | Select-Object -Last 1).ToString().Trim()
    if ([string]::IsNullOrWhiteSpace($Resolved)) {
        throw "Could not resolve the physical Python runtime behind the virtual environment launcher."
    }
    if (-not (Test-Path -LiteralPath $Resolved -PathType Leaf)) {
        throw "Resolved physical Python runtime does not exist: $Resolved"
    }
    return (Resolve-Path -LiteralPath $Resolved).Path
}

function Invoke-RuntimePreflight {
    param([Parameter(Mandatory = $true)][string]$RuntimePython)

    Write-Host "Running Warlock runtime preflight..."
    $PreviousPythonPath = $env:PYTHONPATH
    try {
        if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
            $env:PYTHONPATH = $ProjectRoot
        }
        else {
            $env:PYTHONPATH = "$ProjectRoot;$PreviousPythonPath"
        }

        Push-Location $ProjectRoot
        try {
            & $RuntimePython -m apps.runtime_child apps.runtime_preflight
            if ($LASTEXITCODE -ne 0) {
                throw "Warlock runtime preflight failed with exit code $LASTEXITCODE"
            }
        }
        finally {
            Pop-Location
        }
    }
    finally {
        $env:PYTHONPATH = $PreviousPythonPath
    }
}

function Stop-WarlockProjectProcesses {
    $VenvScripts = (Join-Path $ProjectRoot ".venv\Scripts").ToLowerInvariant()
    $PythonLower = $Python.ToLowerInvariant()
    $PythonwLower = $Pythonw.ToLowerInvariant()
    $CloudflaredLower = $Cloudflared.ToLowerInvariant()
    $LegacySupervisorLower = $LegacySupervisor.ToLowerInvariant()
    $LegacyVbsLower = $LegacyVbs.ToLowerInvariant()

    $Processes = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    foreach ($Process in $Processes) {
        if ($Process.ProcessId -eq $PID) { continue }

        $Executable = if ($null -ne $Process.ExecutablePath) { $Process.ExecutablePath.ToLowerInvariant() } else { "" }
        $Command = if ($null -ne $Process.CommandLine) { $Process.CommandLine.ToLowerInvariant() } else { "" }
        $ExecutableName = if ($Executable) { [System.IO.Path]::GetFileName($Executable) } else { "" }

        $IsWarlockPythonCommand = (
            $Command.Contains("apps.local_agent.run_agent") -or
            $Command.Contains("apps.gateway.server:app") -or
            $Command.Contains("apps.mcp_server.run_mcp") -or
            $Command.Contains("apps.runtime_supervisor") -or
            $Command.Contains("apps.runtime_child")
        )

        $IsPythonExecutable = ($ExecutableName -eq "python.exe" -or $ExecutableName -eq "pythonw.exe")
        $UsesProjectPython = (
            $Executable.StartsWith($VenvScripts) -or
            $Command.Contains($PythonLower) -or
            $Command.Contains($PythonwLower) -or
            $IsPythonExecutable
        )

        $ProjectPython = $IsWarlockPythonCommand -and $UsesProjectPython
        $ProjectTunnel = (($Executable -eq $CloudflaredLower) -or $Command.Contains($CloudflaredLower)) -and $Command.Contains("warlock-agent")
        $LegacyPowerShell = $Command.Contains($LegacySupervisorLower)
        $LegacyLauncher = $Command.Contains($LegacyVbsLower)

        if ($ProjectPython -or $ProjectTunnel -or $LegacyPowerShell -or $LegacyLauncher) {
            Write-Host "Stopping stale Warlock process PID $($Process.ProcessId)..."
            Stop-Process -Id $Process.ProcessId -Force -ErrorAction SilentlyContinue
        }
    }

    Start-Sleep -Seconds 2
}

function Remove-ExistingWarlockTask {
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -eq $ExistingTask) { return }

    if ($ExistingTask.State -eq "Running") {
        Write-Host "Stopping existing Warlock scheduled task..."
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

        $StopDeadline = (Get-Date).AddSeconds(10)
        do {
            Start-Sleep -Milliseconds 250
            $CurrentTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($null -eq $CurrentTask -or $CurrentTask.State -ne "Running") { break }
        } while ((Get-Date) -lt $StopDeadline)
    }

    Write-Host "Removing existing Warlock scheduled task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

function Show-RecentRuntimeLogs {
    $BootstrapLog = Join-Path $RuntimeDir "supervisor.bootstrap.log"
    $SupervisorLog = Join-Path $RuntimeDir "supervisor.log"
    $AgentErrorLog = Join-Path $RuntimeDir "agent.err.log"
    $GatewayErrorLog = Join-Path $RuntimeDir "gateway.err.log"
    $McpErrorLog = Join-Path $RuntimeDir "mcp.err.log"

    foreach ($Entry in @(
        @{ Path = $BootstrapLog; Label = "supervisor.bootstrap.log" },
        @{ Path = $SupervisorLog; Label = "supervisor.log" },
        @{ Path = $AgentErrorLog; Label = "agent.err.log" },
        @{ Path = $GatewayErrorLog; Label = "gateway.err.log" },
        @{ Path = $McpErrorLog; Label = "mcp.err.log" }
    )) {
        if (Test-Path -LiteralPath $Entry.Path -PathType Leaf) {
            Write-Host "--- $($Entry.Label) (last 40 lines) ---"
            Get-Content -LiteralPath $Entry.Path -Tail 40 -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Updating Warlock runtime dependencies..."
& $Python -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed with exit code $LASTEXITCODE" }

Write-Host "Resolving physical Python runtime..."
$RuntimePython = Resolve-PhysicalPython
Write-Host "Physical Python runtime: $RuntimePython"

# Validate the exact physical-interpreter + runtime-child path before stopping
# any currently running Warlock task or service.
Invoke-RuntimePreflight -RuntimePython $RuntimePython

Remove-ExistingWarlockTask
Stop-WarlockProjectProcesses
Get-ChildItem -LiteralPath $RuntimeDir -Filter "*.pid" -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

$UserId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

$Action = New-ScheduledTaskAction `
    -Execute $RuntimePython `
    -Argument "-m apps.runtime_supervisor" `
    -WorkingDirectory $ProjectRoot
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
    -Description "Runs the self-healing Warlock Python supervisor for Agent, Gateway, MCP, and Cloudflare Tunnel." `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName

$SupervisorPidFile = Join-Path $RuntimeDir "supervisor.pid"
$Deadline = (Get-Date).AddSeconds(30)
do {
    $AgentHealthy = Test-WarlockHealth -Port 8765 -IdentityProperty "agent" -IdentityValue "Warlock Local Agent"
    $GatewayHealthy = Test-WarlockHealth -Port 8780 -IdentityProperty "gateway" -IdentityValue "warlock"
    $McpHealthy = Test-WarlockHealth -Port 8790 -IdentityProperty "service" -IdentityValue "warlock-mcp"
    $SupervisorReady = Test-Path -LiteralPath $SupervisorPidFile -PathType Leaf
    if ($SupervisorReady -and $AgentHealthy -and $GatewayHealthy -and $McpHealthy) { break }
    Start-Sleep -Seconds 1
} while ((Get-Date) -lt $Deadline)

$Task = Get-ScheduledTask -TaskName $TaskName
$Info = Get-ScheduledTaskInfo -TaskName $TaskName
$SupervisorPid = if (Test-Path -LiteralPath $SupervisorPidFile -PathType Leaf) { (Get-Content -LiteralPath $SupervisorPidFile -Raw).Trim() } else { "missing" }
$SupervisorReady = $SupervisorPid -ne "missing"

Write-Host "Warlock startup installed."
Write-Host "User: $UserId"
Write-Host "Task state: $($Task.State)"
Write-Host "Last task result: $($Info.LastTaskResult)"
Write-Host "Launcher: Task Scheduler -> physical Python runtime"
Write-Host "Runtime Python: $RuntimePython"
Write-Host "Supervisor PID: $SupervisorPid"
Write-Host "Agent 8765 healthy: $AgentHealthy"
Write-Host "Gateway 8780 healthy: $GatewayHealthy"
Write-Host "MCP 8790 healthy: $McpHealthy"
Write-Host "MCP: http://127.0.0.1:8790/mcp"
Write-Host "Logs: .warlock\runtime"

if (-not ($SupervisorReady -and $AgentHealthy -and $GatewayHealthy -and $McpHealthy)) {
    Show-RecentRuntimeLogs
    throw "Warlock runtime did not become healthy within 30 seconds. See the logs printed above."
}
