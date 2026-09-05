# Farnaz architecture 3.0.0

Original ChatGPT agent `apps/local_agent` on port 8765 is **out of scope**.

```
message
  -> perceive (aliases, path, short/write flags)
  -> policy   (lock apps/local_agent, deny git write/delete original)
  -> engine   (plan up to 24 tool steps)
  -> critic   (redact secrets, cap size, short voice)
  -> memory + event bus
  -> JSON /grok/chat
```

Ports: Farnaz `8766`. Original `8765`.
