$ErrorActionPreference = "Stop"

$TaskName = "Warlock Plugins Factory"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Supervisor = Join-Path $PSScriptRoot "warlock-supervisor.ps1"
$HiddenLauncher = Join-Path $PSScriptRoot "run-warlock-supervisor-hidden.vbs"
$RuntimeDir = Join-Path $ProjectRoot ".warlock\runtime"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"

if (-not (Test-Path -LiteralPath $Supervisor -PathType Leaf)) {
    throw "Supervisor not found: $Supervisor"
}

if (-not (Test-Path -LiteralPath $HiddenLauncher -PathType Leaf)) {
    throw "Hidden launcher not found: $HiddenLauncher"
}

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Virtual environment Python not found: $Python"
}

if (-not (Test-Path -LiteralPath $Requirements -PathType Leaf)) {
    throw "Requirements file not found: $Requirements"
}

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

$RequiredVariables = @(
    "WARLOCK_AGENT_TOKEN",
    "WARLOCK_CF_TEAM_DOMAIN",
    "WARLOCK_CF_ACCESS_AUD"
)

foreach ($Name in $RequiredVariables) {
    $Value = [Environment]::GetEnvironmentVariable($Name, "User")
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "Required user environment variable is missing: $Name"
    }
}

Write-Host "Updating Warlock runtime dependencies..."
& $Python -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed with exit code $LASTEXITCODE"
}

$WScript = "$env:SystemRoot\System32\wscript.exe"
$UserId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Arguments = '"{0}"' -f $HiddenLauncher

$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -ne $ExistingTask -and $ExistingTask.State -eq "Running") {
    Stop-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2
}

$Action = New-ScheduledTaskAction -Execute $WScript -Argument $Arguments -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $UserId

$SettingsParams = @{
    AllowStartIfOnBatteries = $true
    DontStopIfGoingOnBatteries = $true
    StartWhenAvailable = $true
    ExecutionTimeLimit = [TimeSpan]::Zero
    RestartCount = 3
    RestartInterval = (New-TimeSpan -Minutes 1)
}
$Settings = New-ScheduledTaskSettingsSet @SettingsParams

$PrincipalParams = @{
    UserId = $UserId
    LogonType = "Interactive"
    RunLevel = "Limited"
}
$Principal = New-ScheduledTaskPrincipal @PrincipalParams

$RegisterParams = @{
    TaskName = $TaskName
    Action = $Action
    Trigger = $Trigger
    Settings = $Settings
    Principal = $Principal
    Description = "Starts and supervises the Warlock Local Agent, Gateway, MCP server, and Cloudflare Tunnel without opening a console window."
    Force = $true
}
Register-ScheduledTask @RegisterParams | Out-Null

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 5

$Task = Get-ScheduledTask -TaskName $TaskName
$Info = Get-ScheduledTaskInfo -TaskName $TaskName

Write-Host "Warlock startup installed."
Write-Host "User: $UserId"
Write-Host "Task state: $($Task.State)"
Write-Host "Last task result: $($Info.LastTaskResult)"
Write-Host "Launcher: hidden"
Write-Host "MCP: http://127.0.0.1:8790/mcp"
Write-Host "Logs: .warlock\runtime"
