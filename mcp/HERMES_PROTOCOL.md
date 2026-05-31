# Hermes Header Protocol

This document outlines the protocol for routing and formatting messages sent through the Hermes Agent. 
It guarantees that headers are consistently formatted regardless of whether the message was initiated by an external script, an LLM, a cron job, or the native CLI.

## Protocol Matrix

The unified header format automatically attached to all messages is:
* `[🤖 {Flags}_{Model}]` (If routing flags exist)
* `[🤖 {Model}]` (If no routing flags exist)

| Initiator | Execution | Payload | Resulting Header | Example Scenario |
| :--- | :--- | :--- | :--- | :--- |
| **External (MCP)** | One-time | Static Text (`M`) | `[🤖 E_M]` | Python script sends an alert via MCP. |
| **External (MCP)** | One-time | LLM Generated (`AUTO`) | `[🤖 E_GF3.P]` | Python script asks MCP to summarize logs. |
| **Hermes Native** | One-time | Static Text (`M`) | `[🤖 M]` | CLI `tools run send_message` command. |
| **Hermes Native** | One-time | LLM Generated (`AUTO`) | `[🤖 GF3.P]` | `hermes "reply to whatsapp"` |
| **Hermes Cron** | Scheduled | Static/Verbatim (`M`) | `[🤖 C_M]` | A `no_agent=True` cron script outputs an alert. |
| **Hermes Cron** | Scheduled | LLM Generated (`AUTO`) | `[🤖 C_GF3.P]` | A scheduled LLM task finishes a report. |

## Data Flows

### 1. External (MCP Bridge)

The MCP Bridge (`mcp/hermes_mcp_server.py`) acts as the external gateway. 
It forces the `HERMES_COMM_SOURCE` environment variable to `"E"`.

*   **If providing a static `message`:** The bridge sets `HERMES_COMM_MODEL="M"` and delivers the text.
*   **If providing a `prompt`:** The bridge boots a headless instance of `AIAgent`, dynamically loads the active model configuration, asks it to generate text based on the prompt, sets `HERMES_COMM_MODEL="AUTO"`, and delivers the generated text.

### 2. Native (CLI / Autonomous Agent / Cron)

Native execution relies on the default fallback logic inside `gateway/platforms/base.py`.
*   Because the MCP bridge is bypassed, `HERMES_COMM_SOURCE` remains empty.
*   The system dynamically evaluates `HERMES_CRON_JOB_ID` to determine if a `"C"` flag is needed.
*   The agent autonomously sets `HERMES_COMM_MODEL="AUTO"` if the LLM generated the content, or `"M"` if a human piped static text into a tool.

## Implementation Details
The string concatenation logic is handled centrally in `gateway/platforms/base.py`'s `prepend_hermes_header` function. Do not modify formatting logic directly in individual skills or MCP bridge scripts.
