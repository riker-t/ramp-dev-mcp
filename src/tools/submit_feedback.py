"""
Submit Feedback tool - Submit feedback to Ramp about the MCP server.
"""

import httpx
from typing import Any, Dict, List
from mcp.types import TextContent
from .base import BaseTool


class SubmitFeedbackTool(BaseTool):
    """Submit feedback to Ramp about the MCP server interface, tools, or problems"""
    
    @property
    def name(self) -> str:
        return "submit_feedback"
    
    @property
    def description(self) -> str:
        return "Submit feedback to Ramp about the MCP server interface, tools, or problems you encounter. Helps improve the developer experience."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "feedback": {
                    "type": "string",
                    "description": "Your feedback about the MCP tools, API documentation, or any issues encountered. Must be 10-1000 characters."
                },
                "tool_name": {
                    "type": "string", 
                    "description": "Optional: which tool this feedback relates to (e.g., 'validate_endpoint_usage', 'search_documentation')"
                }
            },
            "required": ["feedback"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute submit_feedback tool"""
        feedback = arguments.get("feedback", "").strip()
        tool_name = arguments.get("tool_name", "").strip()
        
        # Input validation (same as remote server)
        if len(feedback) < 10 or len(feedback) > 1000:
            return [TextContent(
                type="text",
                text="Feedback must be at least 10 characters long and less than 1000 characters."
            )]
        
        try:
            # Submit feedback to Ramp's public API (following remote server pattern)
            result = await self._submit_feedback_to_ramp(feedback, tool_name)
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Unexpected error submitting feedback: {str(e)}"
            )]
    
    async def _submit_feedback_to_ramp(self, feedback: str, tool_name: str = "") -> str:
        """Submit feedback to Ramp's public feedback API"""
        
        # Determine environment URL (defaulting to production like remote server)
        base_url = "https://api.ramp.com"  # Production by default
        
        # Build request parameters (same as remote server)
        params = {
            "feedback": feedback,
            "source": "RAMP_MCP"  # Use approved source value (API only accepts RAMP_MCP or API_DOCS)
        }
        
        # Note: tool_name is captured for user context but not sent to API
        # (API only accepts feedback and source parameters)
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/v1/public/api-feedback/llm",
                    params=params
                )
                response.raise_for_status()
                
                # Success message with tool context
                success_msg = "Feedback submitted successfully"
                if tool_name:
                    success_msg += f" (regarding {tool_name} tool)"
                success_msg += "!"
                
                return success_msg
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                return "Invalid feedback format. Please check your message and try again."
            elif e.response.status_code >= 500:
                return "Ramp's feedback service is temporarily unavailable. Please try again later."
            else:
                return f"HTTP error {e.response.status_code}. Please try again later."
                
        except httpx.TimeoutException:
            return "Request timed out. Please check your internet connection and try again."
            
        except httpx.RequestError:
            return "Network error. Please check your internet connection and try again."