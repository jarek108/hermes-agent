---
name: gdrive-sync
description: Sync files (reports, logs, data) with Google Drive using the modern Hermes Google Workspace engine.
---

# GDrive Sync Skill

This skill provides a way to synchronize files (reports, logs, data) with Google Drive using the modern Hermes Google Workspace engine.

## Core Engine
The engine is the Hermes API wrapper located at:
`C:\Users\chojn\AppData\Local\hermes\skills\productivity\google-workspace\scripts\google_api.py`

## Capabilities

### 1. Upload a File
```powershell
python C:\Users\chojn\AppData\Local\hermes\skills\productivity\google-workspace\scripts\google_api.py drive upload "<local_path>"
```

### 2. Search for Files
```powershell
python C:\Users\chojn\AppData\Local\hermes\skills\productivity\google-workspace\scripts\google_api.py drive search "query"
```

### 3. Download a File
```powershell
python C:\Users\chojn\AppData\Local\hermes\skills\productivity\google-workspace\scripts\google_api.py drive download <file_id> --output "<path>"
```

## Setup & Auth
- **Token**: Uses the unified `C:\Users\chojn\AppData\Local\hermes\google_token.json`.
- **Scopes**: Broad Workspace access (Drive, Gmail, Docs, etc.).

## Usage for Agents
Use this skill whenever the user wants to "upload results", "save to drive", or "cloud sync" any generated artifacts. Always return the `webViewLink` to the user so they can click and view the result in their browser.