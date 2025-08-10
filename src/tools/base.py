"""
Base class for MCP tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from mcp.types import Tool, TextContent


class BaseTool(ABC):
    """Abstract base class for MCP tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description"""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """Tool input schema"""
        pass
    
    def to_tool(self) -> Tool:
        """Convert to MCP Tool object"""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema
        )
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the tool with given arguments"""
        pass