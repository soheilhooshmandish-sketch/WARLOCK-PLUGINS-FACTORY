$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Agent = Join-Path $Root "apps\local-agent"

Write-Host ""
Write-Host "==========================================" 
Write-Host " WARLOCK PLUGINS FACTORY BOOTSTRAP"
Write-Host "=========================================="
Write-Host ""

# Create required directories
New-Item -ItemType Directory -Force -Path $Agent | Out-Null

# Create local configuration
$configPath = Join-Path $Agent "config.py"

$config = @'
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_NAME = "Warlock Local Agent"
AGENT_VERSION = "0.2.0"

ALLOWED_OPERATIONS = {
    "python_version",
    "git_status",
    "git_branch",
}
'@

Set-Content -Path $configPath -Value $config -Encoding UTF8

# Create a basic test
$testPath = Join-Path $Agent "test_agent.py"

$test = @'
from config import AGENT_NAME, AGENT_VERSION, PROJECT_ROOT


def test_agent_config():
    assert AGENT_NAME == "Warlock Local Agent"
    assert AGENT_VERSION == "0.2.0"
    assert PROJECT_ROOT.exists()


if __name__ == "__main__":
    test_agent_config()
    print("Agent configuration test: PASS")
'@

Set-Content -Path $testPath -Value $test -Encoding UTF8

Write-Host "Created:"
Write-Host "  apps\local-agent\config.py"
Write-Host "  apps\local-agent\test_agent.py"
Write-Host ""
Write-Host "Bootstrap completed successfully."
Write-Host ""