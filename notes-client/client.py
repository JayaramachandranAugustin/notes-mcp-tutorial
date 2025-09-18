import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Optional, List

# --- OpenAI SDK ---
from openai import AsyncOpenAI

from dotenv import load_dotenv
load_dotenv()


# --- MCP SDK ---
from pydantic import AnyUrl
from mcp import ClientSession, StdioServerParameters
from mcp.shared.context import RequestContext
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

# ---------- Config ----------
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # or gpt-4o-mini, etc.
OPENAI = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class MCPClient:

   def __init__(self):
       self.session: Optional[ClientSession] = None
       self.exit_stack = AsyncExitStack()
       self.openai = OPENAI
       self.model = OPENAI_MODEL
       self.stdio: Optional[asyncio.StreamReader] = None
       self.write: Optional[asyncio.StreamWriter] = None


   async def connect_to_server(self, server_script_path: str):
       """Connect to an MCP server

       Args:
           server_script_path: Path to the server script (.py or .js)
       """
       is_python = server_script_path.endswith('.py')
       is_js = server_script_path.endswith('.js')
       if not (is_python or is_js):
           raise ValueError("Server script must be a .py or .js file")

       command = "python" if is_python else "node"
       server_params = StdioServerParameters(
           command=command,
           args=[server_script_path],
           env=(dict(os.environ) | {"PYTHONUNBUFFERED": "1"})
       )

       stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
       self.stdio, self.write = stdio_transport
       self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

       await self.session.initialize()

       # List available tools
       response = await self.session.list_tools()
       tools = response.tools
       print("\nConnected to server with tools:", [tool.name for tool in tools])


   async def get_mcp_tools(self) -> List[dict]:
       """Return the list of tools in OpenAI format."""
       if not self.session:
           return []
       response = await self.session.list_tools()

       tools_for_openai: List[dict] = []
       for tool in response.tools:
           # Extract JSON schema from MCP Tool
           parameters = {}
           # Try common attribute names and conversions
           candidates = [
               getattr(tool, "parameters", None),
               getattr(tool, "input_schema", None),
               getattr(tool, "inputSchema", None),
           ]
           for s in candidates:
               if not s:
                   continue
               if isinstance(s, dict):
                   parameters = s
                   break
               # pydantic model
               if hasattr(s, "model_dump"):
                   try:
                       parameters = s.model_dump(mode="json")
                       break
                   except Exception:
                       pass
               # generic attrs
               for attr in ("schema", "json_schema", "json", "to_dict"):
                   if hasattr(s, attr):
                       val = getattr(s, attr)
                       try:
                           parameters = val() if callable(val) else val
                           if isinstance(parameters, str):
                               import json as _json
                               parameters = _json.loads(parameters)
                           break
                       except Exception:
                           continue
               if parameters:
                   break

           tools_for_openai.append({
               "type": "function",
               "function": {
                   "name": tool.name,
                   "description": getattr(tool, "description", "") or "",
                   "parameters": parameters or {
                       "type": "object",
                       "properties": {},
                   },
               }
           })

       return tools_for_openai
  
   async def process_query(self, query: str) -> str:
       """Process a query using OpenAI and available MCP tools.

       Args:
           query: The user query.

       Returns:
           The response from OpenAI.
       """
       # Get available tools
       tools = await self.get_mcp_tools()

       # Initial OpenAI API call
       response = await self.openai.chat.completions.create(
           model=self.model,
           messages=[{"role": "user", "content": query}],
           tools=tools,
           tool_choice="auto",
       )

       # Get assistant's response
       assistant_message = response.choices[0].message

       # Initialize conversation with user query and assistant response
       messages = [
           {"role": "user", "content": query},
           assistant_message,
       ]
      

       # Handle tool calls if present
       if assistant_message.tool_calls:
           # Process each tool call
           for tool_call in assistant_message.tool_calls:
               # Execute tool call
               result = await self.session.call_tool(
                   tool_call.function.name,
                   arguments=json.loads(tool_call.function.arguments),
               )

               # Add tool response to conversation
               messages.append(
                   {
                       "role": "tool",
                       "tool_call_id": tool_call.id,
                       "content": result.content[0].text,
                   }
               )

           # Get final response from OpenAI with tool results
           final_response = await self.openai.chat.completions.create(
               model=self.model,
               messages=messages,
               tools=tools,
               tool_choice="none",  # Don't allow more tool calls
           )

           return final_response.choices[0].message.content

       # No tool calls, just return the direct response
       return assistant_message.content

   async def cleanup(self):
       """Clean up resources."""
       await self.exit_stack.aclose()


async def main():
   client = MCPClient()
   try:
       await client.connect_to_server("C:/learning/code/mcp/notes/main.py")
       query = "can you create a new note with the title 'Buy miter saw' with content as 'miter saw to make angle cuts' and tags as wood_work, learning, hobby and due date 2025-09-09"
       print(f"\nQuery: {query}")
       response = await client.process_query(query)
       print(f"\nResponse: {response}")
   except Exception as e:
       print(f"Failed to connect to server: {e}")
   finally:
       await client.cleanup()


if __name__ == "__main__":
   asyncio.run(main())