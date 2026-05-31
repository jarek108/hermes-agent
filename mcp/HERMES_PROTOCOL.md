# Hermes Header Protocol

This document outlines the protocol for routing and formatting messages sent through the Hermes Agent. 
It guarantees that headers are consistently formatted regardless of whether the message was initiated by an external script, an LLM, a cron job, or the native CLI.

## Protocol Matrix

The unified header format automatically attached to all messages is:
* `[🤖 {Flags}_{Model}]` (If routing flags exist)
* `[🤖 {Model}]` (If no routing flags exist)

| ID | Initiator | Execution | Payload | Resulting Header | Example Scenario |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **External (MCP)** | One-time | Static Text (`M`) | `[🤖 E_M]` | Python script sends an alert via MCP. |
| 2 | **External (MCP)** | One-time | LLM Generated (`AUTO`) | `[🤖 E_GF3.P]` | Python script asks MCP to summarize logs. |
| 3 | **Hermes Native** | One-time | Static Text (`M`) | `[🤖 M]` | CLI `tools run send_message` command. |
| 4 | **Hermes Native** | One-time | LLM Generated (`AUTO`) | `[🤖 GF3.P]` | `hermes "reply to whatsapp"` |
| 5 | **Hermes Cron** | Scheduled | Static/Verbatim (`M`) | `[🤖 C_M]` | A `no_agent=True` cron script outputs an alert. |
| 6 | **Hermes Cron** | Scheduled | LLM Generated (`AUTO`) | `[🤖 C_GF3.P]` | A scheduled LLM task finishes a report. |

## Detailed Data Flows

### Component Legend
*   **A**: External Caller (Python script or OpenCode LLM)
*   **B**: MCP Bridge (`mcp/hermes_mcp_server.py`)
*   **C**: Hermes Native Engine (`cli.py`, cron executor, or `AIAgent`)
*   **D**: Send Message Tool (`send_message_tool.py`)
*   **E**: Header Formatter (`gateway/platforms/base.py`)
*   **F**: Target Platform (Telegram, WhatsApp, etc.)

---

### Row 1: External | Static | `[🤖 E_M]`
1. **A** calls MCP `send_message(message="Alert")`.
2. **B** **sets `os.environ["HERMES_COMM_SOURCE"] = "E"` and `os.environ["HERMES_COMM_MODEL"] = "M"`**.
3. **B** passes text to **D**.
4. **D** calls **E**.
5. **E** sees `E` and `M`, formats `[🤖 E_M]`, and delivers to **F**.

### Row 2: External | LLM (`AUTO`) | `[🤖 E_GF3.P]`
1. **A** calls MCP `send_message(prompt="Summarize logs")`.
2. **B** detects prompt, boots headless `AIAgent`, generates text: *"Logs clear."*
3. **B** **sets `os.environ["HERMES_COMM_SOURCE"] = "E"` and `os.environ["HERMES_COMM_MODEL"] = "AUTO"`**.
4. **B** passes generated text to **D**.
5. **D** calls **E**.
6. **E** sees `E` and `AUTO`, detects active model, formats `[🤖 E_GF3.P]`, and delivers to **F**.

### Row 3: Hermes Native | Static | `[🤖 M]`
1. **C** (CLI) invoked: `hermes tools run send_message --message "Test"`. (No env vars are set).
2. **C** passes text to **D**.
3. **D** calls **E**.
4. **E** sees empty Source, empty Context, empty Model (defaulting to `M`), formats `[🤖 M]`, and delivers to **F**.

### Row 4: Hermes Native | LLM (`AUTO`) | `[🤖 GF3.P]`
1. **C** (`AIAgent`) invoked via direct user chat or CLI: `hermes "reply to whatsapp"`. (No env vars are set).
2. **C** generates reply text.
3. **C** autonomously calls **D**.
4. **D** calls **E**.
5. **E** sees empty Source, empty Context, sees `AUTO` (implied by native agent), detects active model, formats `[🤖 GF3.P]`, and delivers to **F**.

### Row 5: Hermes Cron | Static | `[🤖 C_M]`
1. **C** (Cron) wakes up to run a `no_agent=True` script. **It natively sets `os.environ["HERMES_CRON_JOB_ID"] = <id>`**.
2. **C** collects script stdout: *"Disk 90% full"*.
3. **C** calls **D** (bypassing LLM generation, leaving Model empty).
4. **D** calls **E**.
5. **E** detects the Cron ID flag (setting Context to `C`), sees empty Source, sees empty Model (defaulting to `M`), formats `[🤖 C_M]`, and delivers to **F**.

### Row 6: Hermes Cron | LLM (`AUTO`) | `[🤖 C_GF3.P]`
1. **C** (Cron) wakes up to run a scheduled prompt. **It natively sets `os.environ["HERMES_CRON_JOB_ID"] = <id>`**.
2. **C** passes prompt to `AIAgent`, generating text: *"Daily report: All good."*
3. **C** autonomously calls **D**.
4. **D** calls **E**.
5. **E** detects the Cron ID flag (setting Context to `C`), sees empty Source, sees `AUTO` (implied by native agent), detects active model, formats `[🤖 C_GF3.P]`, and delivers to **F**.

## Implementation Note
The string concatenation logic is handled centrally in `gateway/platforms/base.py`'s `_apply_unified_header` function. Do not modify formatting logic directly in individual skills or MCP bridge scripts.
