import sys
import os
from mcp.server.fastmcp import FastMCP

# Load Hermes .env file so the MCP server has access to TELEGRAM_BOT_TOKEN, etc.
from dotenv import load_dotenv
hermes_env_path = os.path.expanduser("~/.hermes/.env")
if os.path.exists(hermes_env_path):
    load_dotenv(hermes_env_path)

# 1. First, check if variables are loaded from OpenCode's MCP runtime context (in os.environ)
# 2. Second, explicitly fall back to reading ~/.hermes/.env
# NOTE: The MCP server executes as a subprocess when started by OpenCode, 
# and OpenCode natively injects the "environment" block from opencode.json.

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
        
        # 1. Resolve Target -> Chat ID and Chat Type
        from gateway.config import load_gateway_config, Platform
        from tools.send_message_tool import _parse_target_ref
        from gateway.channel_directory import resolve_channel_name, lookup_channel_type
        
        parts = target.split(":", 1)
        platform_name = parts[0].strip().lower()
        target_ref = parts[1].strip() if len(parts) > 1 else None
        
        chat_id = None
        thread_id = None
        try:
            platform = Platform(platform_name)
        except ValueError:
            return f"Error: Unknown platform {platform_name}"
            
        if target_ref:
            chat_id, thread_id, is_explicit = _parse_target_ref(platform_name, target_ref)
            if not is_explicit:
                try:
                    resolved = resolve_channel_name(platform_name, target_ref)
                    if resolved:
                        chat_id, thread_id, _ = _parse_target_ref(platform_name, resolved)
                except Exception:
                    pass
                    
        g_config = load_gateway_config()
        if not chat_id:
            home = g_config.get_home_channel(platform)
            if home:
                chat_id = home.chat_id
                
        # 2. Extract context history if target resolves
        history = []
        db_session_id = None
        if chat_id:
            from gateway.session import SessionSource, build_session_key, SessionStore
            from hermes_state import SessionDB
            from pathlib import Path
            
            chat_type = lookup_channel_type(platform_name, chat_id) or "dm"
            session_src = SessionSource(platform=platform, chat_id=chat_id, chat_type=chat_type)
            session_key = build_session_key(session_src)
            
            hermes_home = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
            session_store = SessionStore(sessions_dir=hermes_home / "sessions", config=g_config)
            session_store._ensure_loaded()
            
            if session_key in session_store._entries:
                db_session_id = session_store._entries[session_key].session_id
                try:
                    db = SessionDB()
                    history = db.get_messages_as_conversation(db_session_id)
                except Exception:
                    pass
        
        agent = AIAgent(
            session_id=db_session_id,  # Associate prompt execution with the platform session
            model=default_model,
            provider=default_provider,
            quiet_mode=True, 
            ephemeral_system_prompt="Be concise. Generate text only."
        )
        response_dict = agent.run_conversation(prompt, conversation_history=history)
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

@mcp.tool()
def delegate_to_hermes(prompt: str) -> str:
    """Delegate a complex task to the Hermes AI agent for autonomous execution.
    
    Use this tool when you need Hermes to perform a multi-step task, use its own memory/skills,
    or figure out how to accomplish a goal using its full suite of capabilities.
    
    Args:
        prompt: Natural language description of the task for Hermes to execute.
    """
    import os
    from run_agent import AIAgent
    from hermes_cli.config import load_config
    
    cfg = load_config()
    default_model = cfg.get("model", {}).get("default", "gemini-3-flash-preview")
    default_provider = cfg.get("model", {}).get("provider", "gemini")
    
    agent = AIAgent(
        model=default_model,
        provider=default_provider,
        quiet_mode=True, 
        ephemeral_system_prompt="You are executing a task delegated by another AI agent. Perform the task autonomously and return a concise summary of the results."
    )
    
    response_dict = agent.run_conversation(prompt)
    content = response_dict.get("final_response", "")
    return str(content)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hermes MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Transport protocol to use")
    parser.add_argument("--port", type=int, default=8123, help="Port for SSE server (default: 8123)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host for SSE server")
    args = parser.parse_args()

    if args.transport == "sse":
        print(f"Starting Hermes MCP server on {args.host}:{args.port} (SSE)")
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run("sse")
    else:
        mcp.run("stdio")
