# Warlock Grok Agent

Separate from the original ChatGPT agent.

| Agent | Path | Port |
| --- | --- | --- |
| Original (ChatGPT) | `apps/local_agent` | `127.0.0.1:8765` |
| Grok | `apps/grok_local_agent` | `127.0.0.1:8766` |

Do not edit `apps/local_agent` when changing this service.

## Offline default

`WARLOCK_GROK_OFFLINE` defaults to `1`. `/grok/chat` then returns a local stub and does not call `api.x.ai`.

## File tools

Same workspace gate as the original agent:

- `POST /files/list`
- `POST /files/read`
- `POST /files/write`
- `POST /files/mkdir`
- `POST /files/move`
- `POST /files/delete`

Console logs look like `GROK POST /files/write -> 200 (12ms)` plus `FILE write path=...`.

## Desktop avatar (4.4)

Compact floating face + PTT. Not a second brain.

```powershell
python -m apps.grok_local_agent.run_agent
# then open http://127.0.0.1:8766/desktop
```

Modules live in `apps/grok_local_agent/avatar/`. Swap TTS/portrait without touching the brain.
Backup branch before this upgrade: `backup/farnaz-pre-avatar-20260905`.


```powershell
cd C:\Users\sohei\WARLOCK-PLUGINS-FACTORY
.\ .venv\Scripts\Activate.ps1
python -m apps.grok_local_agent.run_agent
```

## Health

```powershell
curl http://127.0.0.1:8766/health
```
