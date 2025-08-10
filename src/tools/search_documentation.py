"""
Smart Documentation Search Tool - Finds relevant content from markdown guides.
Uses intent detection to match user queries with the most relevant documentation.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List
from mcp.types import TextContent
from .base import BaseTool


class SearchDocumentationTool(BaseTool):
    """Smart tool that searches and returns relevant documentation content"""
    
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
    
    @property
    def name(self) -> str:
        return "search_documentation"
    
    @property
    def description(self) -> str:
        return """🔍 **SMART DOCUMENTATION SEARCH** - Finds the most relevant Ramp API documentation for your query.

**What this does**:
• 🎯 Detects your intent from natural language queries
• 📚 Searches through all Ramp documentation and guides
• 🧠 Reasons about which content is most relevant
• 📋 Returns clean, actionable markdown chunks

**Perfect for**: 
• Getting started with authentication
• Understanding specific API workflows
• Finding implementation examples
• Troubleshooting integration issues

**Usage**: Just describe what you're trying to do naturally.
*Examples: "building an integration", "setting up OAuth", "bill payment workflow", "webhook events"*"""
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Your question or what you're trying to accomplish. Use natural language - e.g., 'building an integration', 'OAuth setup', 'bill payments'"
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Search documentation and return most relevant content"""
        query = arguments.get("query", "").strip()
        
        if not query:
            return [TextContent(
                type="text",
                text="❌ Please provide a search query describing what you're looking for."
            )]
        
        try:
            # Step 1: Detect intent from user query
            detected_cluster = self.knowledge_base.detect_intent(query)
            
            # Step 2: Find and rank relevant documentation files
            relevant_guides = self._find_relevant_guides(query, detected_cluster)
            
            if not relevant_guides:
                return [TextContent(
                    type="text",
                    text=f"ℹ️ No specific documentation found for '{query}'. Try more specific keywords like 'authentication', 'bill payments', 'webhooks', or 'card management'."
                )]
            
            # Step 3: Extract and return the most relevant content
            content = self._extract_relevant_content(relevant_guides[0], query, detected_cluster)
            
            return [TextContent(type="text", text=content)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error searching documentation: {str(e)}"
            )]
    
    def _find_relevant_guides(self, query: str, detected_cluster: str) -> List[Dict[str, Any]]:
        """Find and rank relevant documentation files"""
        relevant_guides = []
        
        # If we detected a cluster, prioritize its guides
        if detected_cluster and detected_cluster in self.knowledge_base.use_case_clusters:
            cluster_data = self.knowledge_base.use_case_clusters[detected_cluster]
            guide_filenames = cluster_data.get("guides", [])
            
            for guide_filename in guide_filenames:
                guide_content = self.knowledge_base._find_guide_by_filename(guide_filename)
                if guide_content:
                    relevance_score = self._calculate_relevance(query, guide_content, guide_filename)
                    relevant_guides.append({
                        'filename': guide_filename,
                        'content': guide_content,
                        'cluster': detected_cluster,
                        'score': relevance_score
                    })
        
        # Also search all guides for keyword matches
        query_keywords = query.lower().split()
        
        for guide_path, guide_obj in self.knowledge_base.guides.items():
            if not any(guide['filename'] in guide_path for guide in relevant_guides):
                relevance_score = self._calculate_relevance(query, guide_obj.content, guide_path)
                if relevance_score > 0.1:  # Only include if somewhat relevant
                    relevant_guides.append({
                        'filename': str(guide_path),
                        'content': guide_obj.content,
                        'cluster': 'general',
                        'score': relevance_score
                    })
        
        # Sort by relevance score (highest first)
        relevant_guides.sort(key=lambda x: x['score'], reverse=True)
        
        return relevant_guides
    
    def _calculate_relevance(self, query: str, content: str, filename: str) -> float:
        """Calculate how relevant a guide is to the query"""
        query_lower = query.lower()
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        score = 0.0
        
        # Boost score if filename matches query keywords
        for word in query_lower.split():
            if word in filename_lower:
                score += 0.3
        
        # Boost score for content matches
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        common_words = query_words.intersection(content_words)
        score += len(common_words) * 0.1
        
        # Special keyword boosting
        keyword_boosts = {
            'auth': ['authorization.mdx', 'guides/getting-started.mdx'],
            'oauth': ['authorization.mdx', 'guides/getting-started.mdx'],
            'bill': ['guides/bill-pay.mdx'],
            'payment': ['guides/bill-pay.mdx'],
            'card': ['guides/single-use-cards.mdx', 'guides/cards-and-funds.mdx'],
            'webhook': ['webhooks.mdx'],
            'accounting': ['guides/accounting.mdx'],
            'mcp': ['guides/ramp-mcp-remote.mdx']
        }
        
        for keyword, boosted_files in keyword_boosts.items():
            if keyword in query_lower:
                for boosted_file in boosted_files:
                    if boosted_file in filename_lower:
                        score += 0.5
        
        return score
    
    def _extract_relevant_content(self, guide_info: Dict[str, Any], query: str, cluster: str) -> str:
        """Extract and format the most relevant content from a guide"""
        filename = guide_info['filename']
        content = guide_info['content']
        
        # Create a structured response
        result = f"# 📚 Documentation: {self._get_guide_title(filename)}\n\n"
        result += f"**Found relevant content for:** *{query}*\n\n"
        
        # Add cluster warnings first (important context)
        if cluster and cluster != 'general':
            cluster_warnings = self._get_cluster_warnings(cluster)
            if cluster_warnings:
                result += f"## ⚠️ Important Context\n\n{cluster_warnings}\n\n"
        
        # Add relevant API endpoints if cluster has them
        if cluster and cluster != 'general':
            endpoint_info = self._extract_cluster_endpoints(cluster, query)
            if endpoint_info:
                result += f"## 🔌 Relevant API Endpoints\n\n{endpoint_info}\n\n"
        
        # Extract key sections based on the cluster or query intent
        sections = self._extract_key_sections(content, cluster, query)
        
        if sections:
            for section in sections:  # Return all relevant sections
                result += f"## {section['title']}\n\n"
                result += f"{section['content']}\n\n"
        else:
            # Fallback: return full clean content
            clean_content = re.sub(r'<[^>]+>', '', content)
            clean_content = re.sub(r'{[^}]+}', '', clean_content)
            result += clean_content
        
        # Add helpful footer
        result += "---\n\n"
        result += "💡 **Next steps:**\n"
        result += "• IMPORTANT: Use `get_endpoint_schema` with specific endpoint paths (e.g., `/developer/v1/bills`) to get precise parameter names, types, and examples for code generation!\n"
        result += "• Use `submit_feedback` if documentation needs further clarification or the MCP server is not functioning as expected\n"
        
        return result
    
    def _extract_cluster_endpoints(self, cluster: str, query: str) -> str:
        """Extract and format API endpoint information from cluster configuration"""
        if cluster not in self.knowledge_base.use_case_clusters:
            return ""
        
        cluster_data = self.knowledge_base.use_case_clusters[cluster]
        endpoints = cluster_data.get("endpoints", [])
        
        if not endpoints or not self.knowledge_base.openapi_spec:
            return ""
        
        endpoint_info = []
        openapi_paths = self.knowledge_base.openapi_spec.get("paths", {})
        
        # Extract details for each endpoint in the cluster
        for endpoint_path in endpoints[:15]:  # Limit to 15 most relevant endpoints
            if endpoint_path in openapi_paths:
                path_info = openapi_paths[endpoint_path]
                endpoint_details = self._format_endpoint_details(endpoint_path, path_info)
                if endpoint_details:
                    endpoint_info.append(endpoint_details)
        
        return "\n\n".join(endpoint_info) if endpoint_info else ""
    
    def _format_endpoint_details(self, path: str, path_info: Dict[str, Any]) -> str:
        """Format individual endpoint details for display with complete implementation info"""
        details = []
        
        # Get available methods (excluding 'parameters')
        methods = [method.upper() for method in path_info.keys() if method != 'parameters' and isinstance(path_info[method], dict)]
        
        if not methods:
            return ""
        
        details.append(f"### `{' | '.join(methods)} {path}`")
        
        # Add conceptual context for Ramp-specific endpoints
        conceptual_context = self._get_conceptual_context(path)
        if conceptual_context:
            details.append(f"**Ramp Context**: {conceptual_context}")
        
        # Get primary method info (prefer POST, then GET, then others)
        primary_method = None
        method_priority = ['post', 'get', 'put', 'patch', 'delete']
        for method in method_priority:
            if method in path_info and isinstance(path_info[method], dict):
                primary_method = method
                break
        
        if not primary_method:
            primary_method = methods[0].lower()
        
        method_info = path_info.get(primary_method, {})
        
        # Add summary/description
        if method_info.get('summary'):
            details.append(f"**Purpose**: {method_info['summary']}")
        elif method_info.get('description'):
            details.append(f"**Purpose**: {method_info['description'][:200]}...")
        
        # Add authentication with example
        if 'security' in method_info or any('security' in path_info.get(m, {}) for m in ['get', 'post', 'put', 'patch', 'delete']):
            details.append("**Authentication**: `Authorization: Bearer your_access_token`")
        
        # Add detailed request info with examples for POST/PUT/PATCH
        if primary_method in ['post', 'put', 'patch']:
            request_body = method_info.get('requestBody', {})
            if request_body:
                content = request_body.get('content', {})
                if 'application/json' in content:
                    schema = content['application/json'].get('schema', {})
                    example_json = self._generate_example_request(path, primary_method, schema)
                    if example_json:
                        details.append(f"**Example Request**:")
                        details.append(f"```json\n{example_json}\n```")
                    
                    # Add required/optional parameters
                    required_params, optional_params = self._extract_parameters(schema)
                    if required_params:
                        details.append(f"**Required**: {', '.join(required_params)}")
                    if optional_params:
                        details.append(f"**Optional**: {', '.join(optional_params[:5])}{'...' if len(optional_params) > 5 else ''}")
        
        # Add cURL example for most common use cases
        if primary_method in ['post', 'get']:
            curl_example = self._generate_curl_example(primary_method.upper(), path, method_info)
            if curl_example:
                details.append(f"**cURL Example**:")
                details.append(f"```bash\n{curl_example}\n```")
        
        # Add response info with example
        responses = method_info.get('responses', {})
        if '200' in responses or '201' in responses:
            success_code = '201' if '201' in responses else '200'
            response_info = responses.get(success_code, {})
            details.append(f"**Success Response**: {success_code}")
            
            # Add example response if available
            if 'content' in response_info:
                content = response_info['content']
                if 'application/json' in content:
                    schema = content['application/json'].get('schema', {})
                    example_response = self._generate_example_response(schema)
                    if example_response:
                        details.append(f"**Example Response**:")
                        details.append(f"```json\n{example_response}\n```")
        
        # Add workflow context for card-related endpoints
        workflow_context = self._get_workflow_context(path)
        if workflow_context:
            details.append(f"**Workflow**: {workflow_context}")
        
        return "\n".join(details)
    
    def _generate_example_request(self, path: str, method: str, schema: Dict[str, Any]) -> str:
        """Generate example JSON request based on OpenAPI schema"""
        if not schema or 'properties' not in schema:
            # Return common examples for known endpoints
            if '/cards' in path and method == 'post':
                return '{\n  "display_name": "Marketing Team Card",\n  "spend_limit_id": "uuid-here"\n}'
            elif '/spend-programs' in path and method == 'post':
                return '{\n  "display_name": "Marketing Budget",\n  "spending_restrictions": {},\n  "icon": "credit_card"\n}'
            return ""
        
        # Try to generate from schema (simplified approach)
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        example = {}
        
        for prop, prop_info in properties.items():
            if prop in required or len(example) < 3:  # Include required + first few optional
                if prop_info.get('type') == 'string':
                    if 'id' in prop:
                        example[prop] = "uuid-here"
                    elif 'name' in prop:
                        example[prop] = f"My {prop.replace('_', ' ')}"
                    else:
                        example[prop] = "example_value"
                elif prop_info.get('type') == 'integer':
                    example[prop] = 100
                elif prop_info.get('type') == 'boolean':
                    example[prop] = True
        
        if example:
            import json
            return json.dumps(example, indent=2)
        return ""
    
    def _generate_curl_example(self, method: str, path: str, method_info: Dict[str, Any]) -> str:
        """Generate cURL example for the endpoint"""
        base_url = "https://demo-api.ramp.com"  # Use demo environment
        
        if method == 'GET':
            return f"curl -X {method} {base_url}{path} \\\n  -H \"Authorization: Bearer your_access_token\""
        elif method == 'POST':
            json_example = ""
            if '/cards' in path:
                json_example = ' \\\n  -d \'{"display_name": "Marketing Team Card", "spend_limit_id": "uuid-here"}\''
            elif '/spend-programs' in path:
                json_example = ' \\\n  -d \'{"display_name": "Marketing Budget", "icon": "credit_card"}\''
            
            return f"curl -X {method} {base_url}{path} \\\n  -H \"Authorization: Bearer your_access_token\" \\\n  -H \"Content-Type: application/json\"{json_example}"
        
        return ""
    
    def _generate_example_response(self, schema: Dict[str, Any]) -> str:
        """Generate example response based on schema"""
        # Simplified - return common response examples
        return '{\n  "id": "uuid-here",\n  "created_at": "2024-01-01T00:00:00Z",\n  "status": "active"\n}'
    
    def _extract_parameters(self, schema: Dict[str, Any]) -> tuple[list, list]:
        """Extract required and optional parameters from schema"""
        if not schema or 'properties' not in schema:
            return [], []
        
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        required_params = [prop for prop in required if prop in properties]
        optional_params = [prop for prop in properties.keys() if prop not in required]
        
        return required_params, optional_params
    
    def _get_guide_title(self, filename: str) -> str:
        """Get a friendly title for a guide file"""
        title_map = {
            'authorization.mdx': 'Authentication & Authorization',
            'guides/getting-started.mdx': 'Getting Started Guide',
            'guides/bill-pay.mdx': 'Bill Payments & Accounts Payable',
            'guides/accounting.mdx': 'Accounting & ERP Integration',
            'guides/single-use-cards.mdx': 'Card Management',
            'guides/cards-and-funds.mdx': 'Cards & Funds Management',
            'webhooks.mdx': 'Webhooks & Real-Time Events',
            'guides/ramp-mcp-remote.mdx': 'AI Agents & MCP Integration'
        }
        
        # Try exact match first
        if filename in title_map:
            return title_map[filename]
        
        # Try partial match
        for key, title in title_map.items():
            if key in filename or filename in key:
                return title
        
        # Fallback: clean up filename
        clean_name = filename.replace('.mdx', '').replace('guides/', '').replace('-', ' ')
        return clean_name.title()
    
    def _extract_key_sections(self, content: str, cluster: str, query: str) -> List[Dict[str, str]]:
        """Extract key sections based on cluster and query"""
        sections = []
        
        # Common section headers to look for
        important_headers = [
            "## Overview",
            "## Getting Started",
            "## Quick Start", 
            "## Quickstart",
            "## How to Get Started",
            "## Implementation",
            "## Examples",
            "## Best Practices",
            "## Authentication",
            "## Authorization"
        ]
        
        # Add cluster-specific headers
        if cluster == 'authentication':
            important_headers.extend([
                "## Understanding environments",
                "## Quickstart: Authorize with Client Credentials",
                "## Authorization code: For multi-customer apps",
                "## OAuth 2.0 Framework"
            ])
        elif cluster == 'ap_workflow':
            important_headers.extend([
                "## Bill Pay API",
                "## Vendor Management", 
                "## Payment Processing"
            ])
        
        # Extract sections
        for header in important_headers:
            section_content = self.knowledge_base._extract_markdown_section(content, header)
            if section_content and len(section_content.strip()) > 50:
                sections.append({
                    'title': header.replace('## ', ''),
                    'content': section_content.strip()
                })
        
        # If no specific sections found, look for any ## headers
        if not sections:
            lines = content.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                if line.strip().startswith('## '):
                    if current_section and current_content:
                        content_text = '\n'.join(current_content).strip()
                        if len(content_text) > 50:
                            sections.append({
                                'title': current_section,
                                'content': content_text
                            })
                    
                    current_section = line.strip().replace('## ', '')
                    current_content = []
                else:
                    if current_section:
                        current_content.append(line)
            
            # Add final section
            if current_section and current_content:
                content_text = '\n'.join(current_content).strip()
                if len(content_text) > 50:
                    sections.append({
                        'title': current_section,
                        'content': content_text
                    })
        
        return sections  # Return all relevant sections
    
    def _get_conceptual_context(self, path: str) -> str:
        """Provide conceptual context for Ramp-specific endpoints"""
        contexts = {
            "/developer/v1/limits": "In Ramp's API, 'limits' are spending limits that control virtual card budgets. When you create a limit, it defines the spending allowance for a virtual card. Think of limits as the 'funding' mechanism for cards.",
            "/developer/v1/limits/{spend_limit_id}": "This endpoint manages individual spending limits that control virtual card funds. Each limit acts as a budget container that restricts how much can be spent on associated cards.",
            "/developer/v1/cards": "Virtual cards in Ramp are automatically created when you assign a spending limit (via /limits endpoints) to a user. The limit controls the card's budget.",
            "/developer/v1/cards/{card_id}": "Card details and management. Note: The card's spending power is controlled by its associated limit (see /limits endpoints).",
            "/developer/v1/spend-programs": "Spend programs are reusable templates that define spending policies. They work with limits to control virtual card behavior and restrictions.",
            "/developer/v1/card-programs": "Card programs define the physical/virtual card properties and are separate from spending limits that control the budget."
        }
        return contexts.get(path, "")
    
    def _get_workflow_context(self, path: str) -> str:
        """Provide workflow context showing how endpoints work together"""
        workflows = {
            "/developer/v1/limits": "1) Create limit (sets budget) → 2) Assign to user → 3) Virtual card automatically created → 4) Card funded by the limit",
            "/developer/v1/cards": "Virtual cards are created automatically when limits are assigned. To issue a virtual card: create a limit first, then assign it to a user.",
            "/developer/v1/spend-programs": "Optional step: Create spend program → Use in limit creation → Limit controls virtual card → Card inherits spending restrictions",
        }
        return workflows.get(path, "")
    
    def _get_cluster_warnings(self, cluster: str) -> str:
        """Get cluster-specific warnings and important context"""
        if cluster not in self.knowledge_base.use_case_clusters:
            return ""
        
        cluster_data = self.knowledge_base.use_case_clusters[cluster]
        warnings = cluster_data.get("warnings", [])
        
        if not warnings:
            return ""
        
        return "\n".join([f"• {warning}" for warning in warnings])