"""
Get Endpoint Schema Tool - Returns precise OpenAPI schema for specific endpoints.
Designed to replace multiple search_documentation calls when LLMs need exact technical specs.
"""

import json
from typing import Any, Dict, List, Optional
from mcp.types import TextContent
from .base import BaseTool


class GetEndpointSchemaTool(BaseTool):
    """Returns precise endpoint schema from OpenAPI spec + related endpoints"""
    
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.spec = knowledge_base.openapi_spec
        self.endpoints = self._extract_all_endpoints()
    
    def _extract_all_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Extract all endpoints with their details"""
        endpoints = {}
        paths = self.spec.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    key = f"{method.upper()} {path}"
                    endpoints[key] = {
                        'path': path,
                        'method': method.upper(),
                        'details': details,
                        'parameters': details.get('parameters', []),
                        'responses': details.get('responses', {}),
                        'requestBody': details.get('requestBody', {})
                    }
        return endpoints
    
    @property
    def name(self) -> str:
        return "get_endpoint_schema"
    
    @property
    def description(self) -> str:
        return """🎯 **GET PRECISE ENDPOINT SCHEMA** - Returns exact OpenAPI schema for specific endpoints.

**Perfect for when you need**:
• Exact request parameter names and types
• Response field names and structures  
• Required vs optional parameters
• Related endpoints for the same use case

**Example queries this replaces**:
• "bills endpoint response schema fields amount vendor status" → Use this tool with `/developer/v1/bills`
• "API pagination limit page_size next cursor" → Get schema for any paginated endpoint
• "cards creation request parameters" → Use this tool with `/developer/v1/cards`

**Usage**: Provide an endpoint path (and optionally method) to get the complete technical specification."""
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "endpoint": {
                    "type": "string", 
                    "description": "The endpoint path (e.g., '/developer/v1/bills', '/developer/v1/limits')"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method (GET, POST, PUT, etc.). If not specified, will show most relevant method.",
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]
                },
                "include_related": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include related endpoints for the same use case"
                }
            },
            "required": ["endpoint"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute schema retrieval"""
        endpoint = arguments.get("endpoint", "").strip()
        method = arguments.get("method", "").upper() if arguments.get("method") else None
        include_related = arguments.get("include_related", True)
        
        if not endpoint:
            return [TextContent(
                type="text",
                text="❌ Please provide an endpoint path (e.g., '/developer/v1/bills')"
            )]
        
        try:
            # Find matching endpoint(s)
            matching_endpoints = self._find_matching_endpoints(endpoint, method)
            
            if not matching_endpoints:
                similar = self._find_similar_endpoints(endpoint)
                suggestion_text = f"\n\n**Similar endpoints available:**\n" + "\n".join([f"• {ep}" for ep in similar[:5]]) if similar else ""
                
                return [TextContent(
                    type="text", 
                    text=f"❌ Endpoint not found: `{method + ' ' if method else ''}{endpoint}`{suggestion_text}"
                )]
            
            # Format the schema response
            result_text = self._format_endpoint_schemas(matching_endpoints, include_related)
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error retrieving schema: {str(e)}"
            )]
    
    def _find_matching_endpoints(self, endpoint: str, method: Optional[str]) -> List[Dict[str, Any]]:
        """Find endpoints that match the given path and method"""
        matches = []
        
        for key, endpoint_info in self.endpoints.items():
            endpoint_path = endpoint_info['path']
            endpoint_method = endpoint_info['method']
            
            # Exact path match
            if endpoint_path == endpoint:
                if method is None or endpoint_method == method:
                    matches.append(endpoint_info)
        
        # If no exact matches and no method specified, prioritize GET > POST > others
        if not matches and method is None:
            method_priority = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
            for prio_method in method_priority:
                for key, endpoint_info in self.endpoints.items():
                    if endpoint_info['path'] == endpoint and endpoint_info['method'] == prio_method:
                        matches.append(endpoint_info)
                        break
                if matches:
                    break
        
        return matches
    
    def _find_similar_endpoints(self, endpoint: str) -> List[str]:
        """Find similar endpoints for suggestions"""
        similar = []
        endpoint_lower = endpoint.lower()
        
        for key, endpoint_info in self.endpoints.items():
            path = endpoint_info['path']
            method = endpoint_info['method']
            
            # Look for partial matches in path
            if any(part in path.lower() for part in endpoint_lower.split('/') if part):
                similar.append(f"{method} {path}")
        
        return sorted(list(set(similar)))[:10]
    
    def _format_endpoint_schemas(self, endpoints: List[Dict[str, Any]], include_related: bool) -> str:
        """Format endpoint schemas into readable structure"""
        result_parts = []
        
        for endpoint_info in endpoints:
            path = endpoint_info['path']
            method = endpoint_info['method']
            details = endpoint_info['details']
            
            result_parts.append(f"# 🎯 {method} {path}")
            result_parts.append(f"**Operation**: {details.get('operationId', 'N/A')}")
            result_parts.append(f"**Description**: {details.get('summary', details.get('description', 'No description'))}")
            
            # Add cluster-specific warnings for this endpoint
            cluster = self._detect_endpoint_cluster(path)
            if cluster:
                warnings = self.knowledge_base.use_case_clusters.get(cluster, {}).get('warnings', [])
                if warnings:
                    result_parts.append("")
                    result_parts.append("## ⚠️ Important Context")
                    for warning in warnings:
                        result_parts.append(f"• {warning}")
            
            result_parts.append("")
            
            # Request Parameters
            parameters = endpoint_info['parameters']
            if parameters:
                result_parts.append("## 📥 Request Parameters")
                
                query_params = [p for p in parameters if p.get('in') == 'query']
                path_params = [p for p in parameters if p.get('in') == 'path']
                header_params = [p for p in parameters if p.get('in') == 'header']
                
                if query_params:
                    result_parts.append("### Query Parameters")
                    for param in query_params:
                        required = "**required**" if param.get('required') else "optional"
                        param_type = param.get('schema', {}).get('type', 'unknown')
                        default_val = param.get('schema', {}).get('default')
                        default_text = f" (default: {default_val})" if default_val is not None else ""
                        
                        result_parts.append(f"• **`{param['name']}`**: `{param_type}` - {required}{default_text}")
                        if param.get('description'):
                            result_parts.append(f"  {param['description']}")
                    result_parts.append("")
                
                if path_params:
                    result_parts.append("### Path Parameters")
                    for param in path_params:
                        param_type = param.get('schema', {}).get('type', 'string')
                        result_parts.append(f"• **`{param['name']}`**: `{param_type}` - **required**")
                        if param.get('description'):
                            result_parts.append(f"  {param['description']}")
                    result_parts.append("")
            
            # Request Body (for POST/PUT/PATCH)
            request_body = endpoint_info['requestBody']
            if request_body and method in ['POST', 'PUT', 'PATCH']:
                result_parts.append("## 📤 Request Body")
                required = request_body.get('required', False)
                result_parts.append(f"**Required**: {'Yes' if required else 'No'}")
                
                content = request_body.get('content', {})
                if 'application/json' in content:
                    json_schema = content['application/json'].get('schema', {})
                    result_parts.append("**Content-Type**: `application/json`")
                    if json_schema:
                        schema_example = self._generate_schema_example(json_schema)
                        if schema_example:
                            result_parts.append("**Example**:")
                            result_parts.append(f"```json\n{json.dumps(schema_example, indent=2)}\n```")
                result_parts.append("")
            
            # Response Schema
            responses = endpoint_info['responses']
            if '200' in responses:
                result_parts.append("## 📤 Response Schema (200 OK)")
                response_info = responses['200']
                
                if 'content' in response_info:
                    content = response_info['content']
                    if 'application/json' in content:
                        json_schema = content['application/json'].get('schema', {})
                        if json_schema:
                            # Show response structure
                            response_example = self._generate_schema_example(json_schema, is_response=True)
                            if response_example:
                                result_parts.append("**Response Structure**:")
                                result_parts.append(f"```json\n{json.dumps(response_example, indent=2)}\n```")
                
                result_parts.append("")
        
        # Add related endpoints if requested
        if include_related and endpoints:
            primary_endpoint = endpoints[0]
            cluster = self._detect_endpoint_cluster(primary_endpoint['path'])
            if cluster:
                related_endpoints = self._get_related_endpoints(cluster, primary_endpoint['path'])
                if related_endpoints:
                    result_parts.append("## 🔗 Related Endpoints")
                    result_parts.append(f"**Use Case**: {cluster.replace('_', ' ').title()}")
                    for related in related_endpoints[:5]:  # Top 5 related
                        result_parts.append(f"• `{related}`")
                    result_parts.append("")
        
        return "\n".join(result_parts)
    
    def _generate_schema_example(self, schema: Dict[str, Any], is_response: bool = False) -> Optional[Dict[str, Any]]:
        """Generate example JSON from OpenAPI schema"""
        if not schema:
            return None
        
        schema_type = schema.get('type')
        
        if schema_type == 'object':
            example = {}
            properties = schema.get('properties', {})
            
            for prop_name, prop_schema in properties.items():
                prop_type = prop_schema.get('type', 'string')
                
                if prop_type == 'string':
                    if prop_name.endswith('_id') or prop_name == 'id':
                        example[prop_name] = "uuid-here"
                    elif 'date' in prop_name or 'time' in prop_name:
                        example[prop_name] = "2024-01-01T00:00:00Z"
                    elif prop_name in ['email']:
                        example[prop_name] = "user@company.com"
                    else:
                        example[prop_name] = "string"
                elif prop_type == 'integer':
                    example[prop_name] = 123
                elif prop_type == 'number':
                    example[prop_name] = 123.45
                elif prop_type == 'boolean':
                    example[prop_name] = True
                elif prop_type == 'array':
                    example[prop_name] = ["item1", "item2"]
                else:
                    example[prop_name] = "value"
            
            # Add common response fields for responses
            if is_response and 'data' not in example:
                if any(key in schema.get('properties', {}) for key in ['data', 'page']):
                    # This looks like a paginated response
                    pass
                else:
                    # Wrap in common response format
                    return {
                        "data": example if example else {"id": "uuid-here"},
                        "page": {
                            "next": "https://api.ramp.com/developer/v1/endpoint?start=cursor",
                            "prev": None
                        }
                    }
            
            return example
        
        return None
    
    def _detect_endpoint_cluster(self, path: str) -> Optional[str]:
        """Detect which use case cluster this endpoint belongs to"""
        # Use the knowledge base clustering
        for cluster_name, cluster_info in self.knowledge_base.use_case_clusters.items():
            if path in cluster_info.get('endpoints', []):
                return cluster_name
        return None
    
    def _get_related_endpoints(self, cluster: str, exclude_path: str) -> List[str]:
        """Get related endpoints for the same use case cluster"""
        if cluster not in self.knowledge_base.use_case_clusters:
            return []
        
        cluster_endpoints = self.knowledge_base.use_case_clusters[cluster].get('endpoints', [])
        related = []
        
        for endpoint_path in cluster_endpoints:
            if endpoint_path != exclude_path:
                # Find methods for this path
                methods = []
                for key, endpoint_info in self.endpoints.items():
                    if endpoint_info['path'] == endpoint_path:
                        methods.append(endpoint_info['method'])
                
                if methods:
                    # Show primary method first
                    primary_method = 'GET' if 'GET' in methods else methods[0]
                    related.append(f"{primary_method} {endpoint_path}")
        
        return related