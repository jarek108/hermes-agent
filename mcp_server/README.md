# Hermes MCP Bridge

The Model Context Protocol (MCP) Bridge allows external scripts (like Python standalone clients) and external LLMs (like OpenCode or Claude) to programmatically interface with the internal capabilities of the Hermes Agent engine.

It exposes core Hermes tools as structured JSON-RPC methods, enabling seamless and lightning-fast communication without the overhead of booting the Hermes CLI for every execution.

## Context-Aware Prompt Execution

When using the `prompt` parameter in `send_message`, the MCP server uses a smart target-resolution pipeline to run the prompt *in the context of the user's active conversation*:

1. **Target Resolution:** The `target` string (e.g., `telegram`) is evaluated exactly as it would be for a standard message send. It maps to a specific `Platform` and numeric `chat_id`.
2. **Session Lookup:** The system builds the deterministic session key (e.g., `agent:main:telegram:dm:12345`) and finds its corresponding active SQLite session ID from the `SessionStore`.
3. **History Hydration:** The server reads the full conversation history from `state.db`.
4. **Contextual Execution:** A headless `AIAgent` is instantiated with this history. When your `prompt` executes, the agent is fully aware of recent messages in that specific chat. 
   - *Example:* If you send `prompt="Summarize our conversation"` to `telegram`, the agent summarizes the actual Telegram chat history before sending the response back to Telegram.

## Available Tools

### `send_message`
Sends a message to a connected messaging platform, or lists available delivery targets.

## Architecture and Lifecycle

The Hermes MCP Bridge runs as a **Server-Sent Events (SSE) FastMCP web server** spawned as an isolated subprocess by the primary Hermes Gateway.

- **Unified Lifecycle**: When you start Hermes (`hermes gateway start`), it automatically spins up the FastMCP SSE server on `http://127.0.0.1:8123/sse` as a detached subprocess. When Hermes stops, the MCP server is cleanly terminated.
- **Process Isolation**: Because the MCP server runs in its own isolated Python process, it safely avoids `asyncio` thread contention and SQLite `OperationalError: database is locked` errors, ensuring maximum stability.
- **Multi-Agent Ready**: Multiple external agents (OpenCode, Claude Desktop, Cursor) can connect to the single `http://127.0.0.1:8123/sse` endpoint simultaneously. For OpenCode, configure this using the `"remote"` type.

*(Note: Prior iterations used a `stdio` subprocess model where the calling agent owned the lifecycle, which led to duplicated API keys and isolated logs. Embedding it into the Gateway lifecycle centralizes all Hermes operations into a single instance.)*

**Arguments:**
*   `target` (string): Delivery target. Format: `'platform'` (uses home channel) or `'platform:#channel-name'`. Examples: `'telegram'`, `'whatsapp'`, `'discord:#bot-home'`.
*   `message` (string, optional): Static text to send. (Provide exactly one of `message` OR `prompt`).
*   `prompt` (string, optional): LLM prompt to generate the message text. (Provide exactly one of `message` OR `prompt`).
*   `source` (string, optional): Single character source code for the unified header. Defaults to `'E'` (External).

### `manage_cronjob`
Create, list, or delete scheduled Hermes cron jobs. Cron jobs created here are executed by the native Hermes scheduling engine.

**Arguments:**
*   `action` (string): `'create'`, `'list'`, or `'delete'`.
*   `schedule` (string, optional): Cron expression (e.g., `'0 9 * * *'` for daily at 9am). Used only for `'create'`.
*   `prompt` (string, optional): The task for the agent to execute on schedule. Used only for `'create'`.
*   `job_id` (string, optional): The ID of the job to delete. Used only for `'delete'`.

### `delegate_to_hermes`
Delegate a complex, multi-step task to the Hermes AI agent for autonomous execution. Use this tool when you need Hermes to use its own internal memory, custom skills, or figure out how to accomplish a goal using its full suite of capabilities.

**Arguments:**
*   `prompt` (string): Natural language description of the task for the headless Hermes `AIAgent` to execute. Returns a concise summary of the results.

### `computer_use`
Control the local OS (mouse, keyboard, app focus) using Hermes' OS-level drivers.

### `browser_navigate` / `browser_click` / `browser_type` / `browser_snapshot`
Control the local Hermes Camoufox (stealth browser) instance. 

### `web_search` / `web_extract`
Execute semantic searches (Exa/Tavily) or markdown extractions (Firecrawl) using the configured Hermes backends.

---

## Send Message Header Protocol

The `send_message` tool guarantees that headers are consistently formatted regardless of whether the message was initiated by an external script, an LLM, a cron job, or the native CLI.

The unified header format automatically attached to all messages is:
* `[🤖 {Flags}_{Model}]` (If routing flags exist)
* `[🤖 {Model}]` (If no routing flags exist)

### Protocol Matrix

| ID | Initiator | Execution | Payload | Resulting Header | Example Scenario |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **External (MCP)** | One-time | Static Text (`M`) | `[🤖 E_M]` | Python script sends an alert via MCP. |
| 2 | **External (MCP)** | One-time | LLM Generated (`AUTO`) | `[🤖 E_GF3.P]` | Python script asks MCP to summarize logs. |
| 3 | **Hermes Native** | One-time | Static Text (`M`) | `[🤖 M]` | CLI `tools run send_message` command. |
| 4 | **Hermes Native** | One-time | LLM Generated (`AUTO`) | `[🤖 GF3.P]` | `hermes "reply to whatsapp"` |
| 5 | **Hermes Cron** | Scheduled | Static/Verbatim (`M`) | `[🤖 C_M]` | A `no_agent=True` cron script outputs an alert. |
| 6 | **Hermes Cron** | Scheduled | LLM Generated (`AUTO`) | `[🤖 C_GF3.P]` | A scheduled LLM task finishes a report. |

### Detailed Data Flows

#### Component Legend
*   **A**: External Caller (Python script or OpenCode LLM)
*   **B**: MCP Bridge (`mcp/hermes_mcp_server.py`)
*   **C**: Hermes Native Engine (`cli.py`, cron executor, or `AIAgent`)
*   **D**: Send Message Tool (`send_message_tool.py`)
*   **E**: Header Formatter (`gateway/platforms/base.py`)
*   **F**: Target Platform (Telegram, WhatsApp, etc.)

#### Row 1: External | Static | `[🤖 E_M]`
1. **A** calls MCP `send_message(message="Alert")`.
2. **B** **sets `os.environ["HERMES_COMM_SOURCE"] = "E"` and `os.environ["HERMES_COMM_MODEL"] = "M"`**.
3. **B** passes text to **D**.
4. **D** calls **E**.
5. **E** sees `E` and `M`, formats `[🤖 E_M]`, and delivers to **F**.

#### Row 2: External | LLM (`AUTO`) | `[🤖 E_GF3.P]`
1. **A** calls MCP `send_message(prompt="Summarize logs")`.
2. **B** detects prompt, boots headless `AIAgent`, generates text: *"Logs clear."*
3. **B** **sets `os.environ["HERMES_COMM_SOURCE"] = "E"` and `os.environ["HERMES_COMM_MODEL"] = "AUTO"`**.
4. **B** passes generated text to **D**.
5. **D** calls **E**.
6. **E** sees `E` and `AUTO`, detects active model, formats `[🤖 E_GF3.P]`, and delivers to **F**.

#### Row 3: Hermes Native | Static | `[🤖 M]`
1. **C** (CLI) invoked: `hermes tools run send_message --message "Test"`. (No env vars are set).
2. **C** passes text to **D**.
3. **D** calls **E**.
4. **E** sees empty Source, empty Context, empty Model (defaulting to `M`), formats `[🤖 M]`, and delivers to **F**.

#### Row 4: Hermes Native | LLM (`AUTO`) | `[🤖 GF3.P]`
1. **C** (`AIAgent`) invoked via direct user chat or CLI: `hermes "reply to whatsapp"`. (No env vars are set).
2. **C** generates reply text.
3. **C** autonomously calls **D**.
4. **D** calls **E**.
5. **E** sees empty Source, empty Context, sees `AUTO` (implied by native agent), detects active model, formats `[🤖 GF3.P]`, and delivers to **F**.

#### Row 5: Hermes Cron | Static | `[🤖 C_M]`
1. **C** (Cron) wakes up to run a `no_agent=True` script. **It natively sets `os.environ["HERMES_CRON_JOB_ID"] = <id>`**.
2. **C** collects script stdout: *"Disk 90% full"*.
3. **C** calls **D** (bypassing LLM generation, leaving Model empty).
4. **D** calls **E**.
5. **E** detects the Cron ID flag (setting Context to `C`), sees empty Source, sees empty Model (defaulting to `M`), formats `[🤖 C_M]`, and delivers to **F**.

#### Row 6: Hermes Cron | LLM (`AUTO`) | `[🤖 C_GF3.P]`
1. **C** (Cron) wakes up to run a scheduled prompt. **It natively sets `os.environ["HERMES_CRON_JOB_ID"] = <id>`**.
2. **C** passes prompt to `AIAgent`, generating text: *"Daily report: All good."*
3. **C** autonomously calls **D**.
4. **D** calls **E**.
5. **E** detects the Cron ID flag (setting Context to `C`), sees empty Source, sees `AUTO` (implied by native agent), detects active model, formats `[🤖 C_GF3.P]`, and delivers to **F**.

### Implementation Note
The string concatenation logic is handled centrally in `gateway/platforms/base.py`'s `_apply_unified_header` function. Do not modify formatting logic directly in individual skills or MCP bridge scripts.
