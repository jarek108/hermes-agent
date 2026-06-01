import sys
import os
from mcp.server.fastmcp import FastMCP

# Add Hermes tools directory to path
HERMES_ROOT = r"E:\projects_large\my_hermes"
if HERMES_ROOT not in sys.path:
    sys.path.append(HERMES_ROOT)

mcp = FastMCP("hermes")

@mcp.tool()
def computer_use(action: str, **kwargs) -> str:
    """Control the computer (mouse, keyboard, etc.) using Hermes' computer_use tool.
    
    Args:
        action: The action to perform (click, double_click, right_click, drag, scroll, type, key, wait, capture, list_apps, focus_app).
        **kwargs: Additional arguments for the action (e.g., x, y, text, keys, app).
    """
    from tools.computer_use.tool import handle_computer_use
    args = {"action": action}
    args.update(kwargs)
    result = handle_computer_use(args)
    return str(result)

@mcp.tool()
def browser_navigate(url: str) -> str:
    """Navigate to a URL using Hermes' browser tool."""
    from tools.browser_tool import browser_navigate as navigate
    return str(navigate(url))

@mcp.tool()
def browser_click(ref: str) -> str:
    """Click on an element in the browser by its reference ID or text."""
    from tools.browser_tool import browser_click as click
    return str(click(ref))

@mcp.tool()
def browser_type(ref: str, text: str) -> str:
    """Type text into an element in the browser."""
    from tools.browser_tool import browser_type as type_text
    return str(type_text(ref, text))

@mcp.tool()
def browser_snapshot() -> str:
    """Take a snapshot of the current page (DOM + screenshot)."""
    from tools.browser_tool import browser_snapshot as snapshot
    return str(snapshot())

@mcp.tool()
def web_search(query: str) -> str:
    """Search the web using Hermes' configured backend (Exa/Firecrawl)."""
    from tools.web_tools import web_search_tool
    return str(web_search_tool(query))

@mcp.tool()
def web_extract(urls: list[str]) -> str:
    """Extract content from one or more URLs using Hermes' configured backend."""
    from tools.web_tools import web_extract_tool
    return str(web_extract_tool(urls))

@mcp.tool()
def send_message(target: str, message: str = "", prompt: str = "", source: str = "MCP") -> str:
    """Send a message to a connected messaging platform, or list available targets.
    
    Args:
        target: Delivery target. Format: 'platform' (uses home channel), 'platform:#channel-name'. Examples: 'telegram', 'discord:#bot-home'.
        message: Static text to send. (Provide exactly one of message OR prompt).
        prompt: LLM prompt to generate the message text. (Provide exactly one of message OR prompt).
        source: Single char/string source code for the header (e.g., 'MCP').
    """
    import os
    
    if bool(message) == bool(prompt):
        return "Error: Provide exactly one of 'message' or 'prompt'."

    if prompt:
        from run_agent import AIAgent
        from hermes_cli.config import load_config
        
        cfg = load_config()
        default_model = cfg.get("model", {}).get("default", "gemini-3-flash-preview")
        default_provider = cfg.get("model", {}).get("provider", "gemini")
        
        agent = AIAgent(
            model=default_model,
            provider=default_provider,
            quiet_mode=True, 
            ephemeral_system_prompt="Be concise. Generate text only."
        )
        response_dict = agent.run_conversation(prompt)
        content = response_dict.get("final_response", "")
        os.environ["HERMES_COMM_MODEL"] = "AUTO"  # Triggers dynamic model abbreviation
    else:
        content = message
        os.environ["HERMES_COMM_MODEL"] = "M"     # Triggers 'M' (Manual)

    from tools.send_message_tool import send_message_tool as hermes_send
    
    # Inject the protocol environment variables expected by gateway/platforms/base.py
    os.environ["HERMES_COMM_SOURCE"] = source
    
    args = {"action": "send", "target": target, "message": content}
    return str(hermes_send(args))

@mcp.tool()
def manage_cronjob(action: str, schedule: str = "", prompt: str = "", job_id: str = "") -> str:
    """Create, list, or delete scheduled Hermes cron jobs.
    
    Args:
        action: 'create', 'list', or 'delete'
        schedule: Cron expression (e.g., '0 9 * * *' for daily at 9am) - used for 'create'
        prompt: The task for the agent to execute on schedule - used for 'create'
        job_id: The ID of the job to delete - used for 'delete'
    """
    from tools.cronjob_tools import cronjob as hermes_cron
    
    args = {"action": action}
    if action == "create":
        args.update({"schedule": schedule, "prompt": prompt})
    elif action == "delete":
        args.update({"job_id": job_id})
        
    return str(hermes_cron(args))

if __name__ == "__main__":
    mcp.run()
