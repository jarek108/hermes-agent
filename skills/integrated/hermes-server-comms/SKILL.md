---
name: hermes-server-comms
description: Notify the user on their phone via Telegram or WhatsApp using the local Hermes Server engine. Default to Telegram and static messages.
---

# Hermes Server Communications

This skill allows the agent to reach the user's mobile devices. All communications are routed through a unified Python script sitting in the Hermes data directory.

## Core Infrastructure

- **Hermes Python Venv**: `C:\Users\chojn\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe`
- **Unified Script**: `C:\Users\chojn\AppData\Local\hermes\scripts\hermes_comm.py`
- **Home Directory**: `C:\Users\chojn\AppData\Local\hermes`

## Execution Rules

1. **Default Target**: Always use `--target telegram` unless the user explicitly mentions WhatsApp or "both".
2. **Default Delivery**: Always prefer direct execution over creating a cron job. Only use `hermes cron` if the user asks for a repeating/cyclic action.
3. **Default Mode**: Always prefer `--message` (static text) over `--prompt` (LLM-generated). Only use `--prompt` if the user asks for a summary, a creative message, or if the content requires LLM analysis.

## Usage Templates

### 1. Simple Notification (The Default)
Use this for instant alerts.
```bash
& "C:\Users\chojn\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" "C:\Users\chojn\AppData\Local\hermes\scripts\hermes_comm.py" --target telegram --message "Your message here"
```

### 2. WhatsApp Notification
```bash
& "C:\Users\chojn\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" "C:\Users\chojn\AppData\Local\hermes\scripts\hermes_comm.py" --target whatsapp --message "Your message here"
```

### 3. LLM-Generated Status (The "Prompt" Mode)
Use this when you need the server's LLM to generate content.
```bash
& "C:\Users\chojn\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" "C:\Users\chojn\AppData\Local\hermes\scripts\hermes_comm.py" --target telegram --prompt "Summarize the recent changes in this directory"
```

### 4. Scheduled Report (The "Cron" Mode)
Use this for cyclic tasks (e.g. daily at 9 AM).
```bash
hermes cron create "0 9 * * *" "& `"C:\Users\chojn\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe`" `"C:\Users\chojn\AppData\Local\hermes\scripts\hermes_comm.py`" --target both --prompt 'Generate a daily system health summary'"
```

## Maintenance
- Logs: `C:\Users\chojn\AppData\Local\hermes\logs\agent.log`
- Configuration: `C:\Users\chojn\AppData\Local\hermes\config.yaml`
- Credentials: `C:\Users\chojn\AppData\Local\hermes\.env`