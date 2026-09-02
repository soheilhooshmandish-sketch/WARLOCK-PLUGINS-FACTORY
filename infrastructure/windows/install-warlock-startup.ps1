$ErrorActionPreference = "Stop"

$TaskName = "Warlock Plugins Factory"
$Supervisor = Join-Path $PSScriptRoot "warlock-supervisor.ps1"
$RuntimeDir = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path ".warlock\runtime")
$TaskStdout = Join-Path $RuntimeDir "task.out.log"
$TaskStderr = Join-Path $RuntimeDir "task.err.log"

if (-not (Test-Path -LiteralPath $Supervisor -PathType Leaf)) {
    throw "Supervisor not found: $Supervisor"
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

$PowerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$EscapedSupervisor = $Supervisor.Replace("'", "''")
$EscapedStdout = $TaskStdout.Replace("'", "''")
$EscapedStderr = $TaskStderr.Replace("'", "''")
$Command = "& '$EscapedSupervisor' 1>>'$EscapedStdout' 2>>'$EscapedStderr'"
$Arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -Command `"$Command`""
$WorkingDirectory = $PSScriptRoot
$UserId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -ne $ExistingTask -and $ExistingTask.State -eq "Running") {
    Stop-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2
}

$Action = New-ScheduledTaskAction -Execute $PowerShell -Argument $Arguments -WorkingDirectory $WorkingDirectory
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
    Description = "Starts and supervises the Warlock Local Agent, Gateway, and Cloudflare Tunnel."
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
Write-Host "Logs: .warlock\runtime"
