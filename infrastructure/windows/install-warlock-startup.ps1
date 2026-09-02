$ErrorActionPreference = "Stop"

$TaskName = "Warlock Plugins Factory"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RuntimeDir = Join-Path $ProjectRoot ".warlock\runtime"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Pythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$Cloudflared = Join-Path $ProjectRoot "infrastructure\cloudflare\cloudflared.exe"
$LegacySupervisor = Join-Path $PSScriptRoot "warlock-supervisor.ps1"
$LegacyVbs = Join-Path $PSScriptRoot "run-warlock-supervisor-hidden.vbs"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Virtual environment Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Requirements -PathType Leaf)) { throw "Requirements file not found: $Requirements" }
if (-not (Test-Path -LiteralPath $Cloudflared -PathType Leaf)) { throw "cloudflared not found: $Cloudflared" }

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

$RequiredVariables = @("WARLOCK_AGENT_TOKEN", "WARLOCK_CF_TEAM_DOMAIN", "WARLOCK_CF_ACCESS_AUD")
foreach ($Name in $RequiredVariables) {
    $Value = [Environment]::GetEnvironmentVariable($Name, "User")
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Required user environment variable is missing: $Name" }
}

function Test-LocalPort {
    param([Parameter(Mandatory = $true)][int]$Port)
    try {
        $Client = New-Object System.Net.Sockets.TcpClient
        $Async = $Client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $Async.AsyncWaitHandle.WaitOne(400)) {
            $Client.Close()
            return $false
        }
        $Client.EndConnect($Async)
        $Client.Close()
        return $true
    }
    catch {
        return $false
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
            $Command.Contains("apps.runtime_supervisor")
        )

        # Python 3.14 venv launchers can hand off to the physical python.exe in
        # AppData\Local\Python\pythoncore-*. Accept a real Python executable
        # only when its command line is one of Warlock's known module commands.
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

Remove-ExistingWarlockTask
Stop-WarlockProjectProcesses
Get-ChildItem -LiteralPath $RuntimeDir -Filter "*.pid" -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

$UserId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# Use python.exe directly. Task Scheduler launches it without an interactive
# console window, and unlike the pythonw venv launcher its process lifecycle is
# reliably visible to Task Scheduler on Python 3.14.
$Action = New-ScheduledTaskAction `
    -Execute $Python `
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
    $AgentListening = Test-LocalPort 8765
    $GatewayListening = Test-LocalPort 8780
    $McpListening = Test-LocalPort 8790
    $SupervisorReady = Test-Path -LiteralPath $SupervisorPidFile -PathType Leaf
    if ($SupervisorReady -and $AgentListening -and $GatewayListening -and $McpListening) { break }
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
Write-Host "Launcher: Task Scheduler -> python.exe self-healing supervisor"
Write-Host "Supervisor PID: $SupervisorPid"
Write-Host "Agent 8765 listening: $AgentListening"
Write-Host "Gateway 8780 listening: $GatewayListening"
Write-Host "MCP 8790 listening: $McpListening"
Write-Host "MCP: http://127.0.0.1:8790/mcp"
Write-Host "Logs: .warlock\runtime"

if (-not ($SupervisorReady -and $AgentListening -and $GatewayListening -and $McpListening)) {
    Show-RecentRuntimeLogs
    throw "Warlock runtime did not become healthy within 30 seconds. See the logs printed above."
}