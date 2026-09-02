$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Cloudflared = Join-Path $ProjectRoot "infrastructure\cloudflare\cloudflared.exe"
$CloudflareConfig = Join-Path $ProjectRoot "infrastructure\cloudflare\config\config.yml"
$RuntimeDir = Join-Path $ProjectRoot ".warlock\runtime"

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
Set-Location $ProjectRoot

function Get-UserEnvironmentValue {
    param([Parameter(Mandatory = $true)][string]$Name)

    $Value = [Environment]::GetEnvironmentVariable($Name, "User")
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "Required user environment variable is missing: $Name"
    }
    return $Value
}

function Assert-FileExists {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file not found: $Path"
    }
}

Assert-FileExists $Python
Assert-FileExists $Cloudflared
Assert-FileExists $CloudflareConfig

$env:WARLOCK_AGENT_TOKEN = Get-UserEnvironmentValue "WARLOCK_AGENT_TOKEN"
$env:WARLOCK_CF_TEAM_DOMAIN = Get-UserEnvironmentValue "WARLOCK_CF_TEAM_DOMAIN"
$env:WARLOCK_CF_ACCESS_AUD = Get-UserEnvironmentValue "WARLOCK_CF_ACCESS_AUD"

$Services = @(
    @{
        Name = "agent"
        FilePath = $Python
        Arguments = @("-m", "apps.local_agent.run_agent")
    },
    @{
        Name = "gateway"
        FilePath = $Python
        Arguments = @("-m", "uvicorn", "apps.gateway.server:app", "--host", "127.0.0.1", "--port", "8780")
    },
    @{
        Name = "tunnel"
        FilePath = $Cloudflared
        Arguments = @("tunnel", "--config", $CloudflareConfig, "run", "warlock-agent")
    }
)

$Processes = @{}

function Start-WarlockService {
    param([Parameter(Mandatory = $true)][hashtable]$Service)

    $Name = $Service.Name
    $Stdout = Join-Path $RuntimeDir "$Name.out.log"
    $Stderr = Join-Path $RuntimeDir "$Name.err.log"

    $StartParams = @{
        FilePath = $Service.FilePath
        ArgumentList = $Service.Arguments
        WorkingDirectory = $ProjectRoot
        WindowStyle = "Hidden"
        RedirectStandardOutput = $Stdout
        RedirectStandardError = $Stderr
        PassThru = $true
    }

    $Process = Start-Process @StartParams
    $Processes[$Name] = $Process
}

foreach ($Service in $Services) {
    Start-WarlockService $Service
    Start-Sleep -Seconds 1
}

try {
    while ($true) {
        Start-Sleep -Seconds 5

        foreach ($Service in $Services) {
            $Name = $Service.Name
            $Process = $Processes[$Name]

            if ($null -eq $Process -or $Process.HasExited) {
                Start-Sleep -Seconds 2
                Start-WarlockService $Service
            }
        }
    }
}
finally {
    foreach ($Process in $Processes.Values) {
        if ($null -ne $Process -and -not $Process.HasExited) {
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}
