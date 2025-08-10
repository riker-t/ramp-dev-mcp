#!/usr/bin/env python3
"""
Ramp Developer MCP Server
A focused MCP server for Ramp API development.

Features:
- Precise endpoint schema retrieval from OpenAPI specification
- Developer documentation search and guidance
- Use case exploration with related endpoints
- Direct access to Ramp API technical specifications

Version: Streamlined for Developer Experience
"""

import asyncio
from pathlib import Path
import sys
from typing import Any, Dict, List

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent))
from knowledge_base import RampKnowledgeBase

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import all tools  
from tools import PingTool, SearchDocumentationTool, SubmitFeedbackTool, GetEndpointSchemaTool

# Create server instance with enhanced capabilities
server = Server("ramp-developer-mcp-enhanced")


def initialize_knowledge_base():
    """Initialize the Ramp knowledge base"""
    project_root = Path(__file__).parent.parent
    return RampKnowledgeBase(project_root)


# Initialize knowledge base and tools
try:
    knowledge_base = initialize_knowledge_base()
    
    # Initialize all tools with dependencies
    tools = [
        PingTool(),
        SearchDocumentationTool(knowledge_base),
        SubmitFeedbackTool(),
        GetEndpointSchemaTool(knowledge_base)
    ]
    
    # Create tool lookup for easy access
    tool_lookup = {tool.name: tool for tool in tools}
    
    # Startup info
    print(f"✅ Ramp MCP Server initialized successfully", file=sys.stderr)
    print(f"   📋 Loaded {len(tools)} tools: {', '.join(tool_lookup.keys())}", file=sys.stderr)
    if hasattr(knowledge_base, 'openapi_spec') and knowledge_base.openapi_spec:
        print(f"   🔧 OpenAPI specification loaded", file=sys.stderr)
    print(f"   🚀 Ready to serve developer requests", file=sys.stderr)
    
except Exception as e:
    print(f"❌ Failed to initialize Ramp MCP Server: {e}", file=sys.stderr)
    print(f"   Working directory: {Path.cwd()}", file=sys.stderr)
    print(f"   Python path: {sys.path}", file=sys.stderr)
    # Still create empty structures to prevent crashes
    tools = []
    tool_lookup = {}


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all tools available in the server."""
    return [tool.to_tool() for tool in tools]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls with enhanced error handling"""
    if name not in tool_lookup:
        return [TextContent(
            type="text",
            text=f"❌ Unknown tool: {name}. Available tools: {list(tool_lookup.keys())}"
        )]
    
    try:
        tool = tool_lookup[name]
        result = await tool.execute(arguments)
        
        # Ensure result is always a list
        if not isinstance(result, list):
            result = [result]
            
        return result
        
    except Exception as e:
        # Enhanced error handling with useful debug information
        error_msg = f"❌ Error executing tool '{name}': {str(e)}"
        
        # Add debug info for errors
        if name == "search_documentation" and arguments:
            content_preview = arguments.get("content", "")[:100]
            error_msg += f"\n\nContent preview: {content_preview}..."
            error_msg += f"\nArguments: {list(arguments.keys())}"
        
        return [TextContent(
            type="text",
            text=error_msg
        )]


async def main():
    """Run the MCP server"""
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())