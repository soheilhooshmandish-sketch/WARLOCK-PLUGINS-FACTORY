# Warlock Grok Agent

Separate agent from the original ChatGPT local agent.

- Original ChatGPT agent: `apps/local_agent` on `127.0.0.1:8765`
- This Grok agent: `apps/grok_local_agent` on `127.0.0.1:8766`

Do not edit `apps/local_agent` when changing this service.

## Start

```powershell
cd C:\Users\sohei\WARLOCK-PLUGINS-FACTORY
.\.venv\Scripts\Activate.ps1
python -m apps.grok_local_agent.run_agent
```

## Health

```powershell
curl http://127.0.0.1:8766/health
```

Set `XAI_API_KEY` for `/grok/chat`. Token: `WARLOCK_GROK_AGENT_TOKEN` or `WARLOCK_AGENT_TOKEN`.
