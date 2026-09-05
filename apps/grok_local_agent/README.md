# Warlock Grok Agent

Separate from the original ChatGPT agent.

| Agent | Path | Port |
| --- | --- | --- |
| Original (ChatGPT) | `apps/local_agent` | `127.0.0.1:8765` |
| Grok | `apps/grok_local_agent` | `127.0.0.1:8766` |

Do not edit `apps/local_agent` when changing this service.

## Offline default

`WARLOCK_GROK_OFFLINE` defaults to `1`. `/grok/chat` then returns a local stub and does not call `api.x.ai`.

Live API:

```powershell
[Environment]::SetEnvironmentVariable("WARLOCK_GROK_OFFLINE", "0", "User")
```

Requires a real key from https://console.x.ai starting with `xai-` plus API credits. Creating a key is free; usage is prepaid.

## Start

```powershell
cd C:\Users\sohei\WARLOCK-PLUGINS-FACTORY
.\ .venv\Scripts\Activate.ps1
python -m apps.grok_local_agent.run_agent
```

## Health

```powershell
curl http://127.0.0.1:8766/health
```
