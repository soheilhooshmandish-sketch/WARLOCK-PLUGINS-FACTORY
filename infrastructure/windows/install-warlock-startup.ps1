$ErrorActionPreference = "Stop"

$TaskName = "Warlock Plugins Factory"
$Supervisor = Join-Path $PSScriptRoot "warlock-supervisor.ps1"

if (-not (Test-Path -LiteralPath $Supervisor -PathType Leaf)) {
    throw "Supervisor not found: $Supervisor"
}

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
$Arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Supervisor`""

$Action = New-ScheduledTaskAction -Execute $PowerShell -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet \
    -AllowStartIfOnBatteries \
    -DontStopIfGoingOnBatteries \
    -StartWhenAvailable \
    -ExecutionTimeLimit ([TimeSpan]::Zero) \
    -RestartCount 3 \
    -RestartInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal \
    -UserId $env:USERNAME \
    -LogonType Interactive \
    -RunLevel Limited

Register-ScheduledTask \
    -TaskName $TaskName \
    -Action $Action \
    -Trigger $Trigger \
    -Settings $Settings \
    -Principal $Principal \
    -Description "Starts and supervises the Warlock Local Agent, Gateway, and Cloudflare Tunnel." \
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 5

$Task = Get-ScheduledTask -TaskName $TaskName
$Info = Get-ScheduledTaskInfo -TaskName $TaskName

Write-Host "Warlock startup installed."
Write-Host "Task state: $($Task.State)"
Write-Host "Last task result: $($Info.LastTaskResult)"
Write-Host "Logs: .warlock\runtime"
