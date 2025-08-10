"""
Ping tool - Simple connectivity test.
"""

from typing import Any, Dict, List
from mcp.types import TextContent
from .base import BaseTool


class PingTool(BaseTool):
    """Simple connectivity test tool"""
    
    @property
    def name(self) -> str:
        return "ping"
    
    @property
    def description(self) -> str:
        return "Test connectivity to the MCP server"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute ping tool"""
        return [
            TextContent(type="text", text="Pong! Ramp Developer MCP server is running")
        ]