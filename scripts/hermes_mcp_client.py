import os
import sys
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def send_via_mcp(target: str, payload: str, is_prompt: bool = False, source: str = "MCP"):
    # Path to the Hermes Python environment and our MCP server script
    python_exe = r"C:\Users\chojn\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
    server_script = r"E:\projects_large\my_hermes\mcp\hermes_mcp_server.py"
    
    server_params = StdioServerParameters(
        command=python_exe,
        args=[server_script],
        env={
            **os.environ,
            "TELEGRAM_BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
            "TELEGRAM_ALLOWED_USERS": "YOUR_CHAT_ID_HERE",
            "WHATSAPP_ENABLED": "true",
            "WHATSAPP_ALLOWED_USERS": "48792212997",
            "WHATSAPP_MODE": "self-chat"
        }
    )
    
    print(f"Connecting to Hermes MCP server...")
    # Initialize the stdio connection and the MCP session
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            payload_type = "prompt" if is_prompt else "message"
            print(f"Sending {payload_type} to '{target}' with header var [Source:{source}]...")
            
            # Call the tool over MCP
            tool_args = {
                "target": target,
                "source": source
            }
            if is_prompt:
                tool_args["prompt"] = payload
            else:
                tool_args["message"] = payload
                
            result = await session.call_tool("send_message", arguments=tool_args)
            
            if result.isError:
                print(f"Error from MCP server: {result.content}")
            else:
                print(f"Success! Response:")
                for content in result.content:
                    print(content.text)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python hermes_mcp_client.py <target> <payload> [--prompt] [source]")
        print("Example: python hermes_mcp_client.py telegram 'Hello from MCP'")
        print("Example: python hermes_mcp_client.py whatsapp 'Tell a joke' --prompt")
        sys.exit(1)
        
    target = sys.argv[1]
    payload = sys.argv[2]
    
    is_prompt = "--prompt" in sys.argv
    source = "MCP"
    
    # Simple arg parsing for optional source override
    for arg in sys.argv[3:]:
        if arg != "--prompt":
            source = arg
            break
            
    asyncio.run(send_via_mcp(target, payload, is_prompt, source))
