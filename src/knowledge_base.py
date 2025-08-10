# src/knowledge_base.py
from pathlib import Path
from typing import Dict, List, Optional, Any
import frontmatter
import markdown
import json
import re
import sys
from dataclasses import dataclass


@dataclass
class GuideContent:
    title: str
    content: str
    priority: Optional[int]
    file_path: str
    use_cases: List[str]




class RampKnowledgeBase:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.use_case_clusters = self._define_clusters()
        self.guides = self._load_guides()
        self.openapi_spec = self._load_openapi_spec()

    def _define_clusters(self) -> Dict[str, Dict]:
        """Define use case clusters with keywords, guides, and endpoints"""
        return {
            "authentication": {
                "keywords": [
                    "authentication",
                    "setup", 
                    "auth",
                    "oauth",
                    "authorization code",
                    "internal integration", 
                    "oauth flows",
                    "access token",
                    "bearer token",
                    "refresh token",
                ],
                "guides": ["authorization.mdx"],
                "endpoints": ["/developer/v1/token"],
                "warnings": ["⚠️ CRITICAL: Never call /developer/v1/token from browser JavaScript! This causes CORS errors. For browser-based apps: (1) Use OAuth2 Authorization Code flow to redirect users to Ramp for authentication, or (2) Use your backend server to proxy token requests with client_credentials flow."],
            },
            "ap_workflow": {
                "keywords": [
                    "bills",
                    "accounts payable",
                    "ap",
                    "vendors",
                    "payments",
                    "bill pay",
                    "invoice",
                ],
                "guides": ["guides/bill-pay.mdx"],
                "endpoints": [
                    "/developer/v1/bills",
                    "/developer/v1/bills/drafts",
                    "/developer/v1/vendors",
                    "/developer/v1/vendors/{vendor_id}/accounts",
                    "/developer/v1/vendors/{vendor_id}/update-bank-accounts"
                ],
                "warnings": ["In Ramp's API, payments are not managed by their own endpoints. Payment information is nested within the Bills endpoint and bill payments are executed by creating Bills."],
            },
            "erp_integration": {
                "keywords": [
                    "erp",
                    "accounting",
                    "gl",
                    "sync",
                ],
                "guides": ["guides/accounting.mdx"],
                "endpoints": [
                    "/developer/v1/accounting/accounts",
                    "/developer/v1/accounting/syncs",
                    "/developer/v1/accounting/connection",
                    "/developer/v1/accounting/vendors",
                    "/developer/v1/accounting/fields",
                ],
                "warnings": [],
            },
            "card_management": {
                "keywords": [
                    "cards",
                    "virtual cards", 
                    "card create",
                    "card issue", 
                    "card creation",
                    "card issuing",
                    "card endpoints",
                    "limits",
                    "spend limits", 
                    "spending limits",
                    "spend programs",
                    "card programs",
                    "card management",
                    "funds",
                    "funding",
                    "card funding",
                    "card budget",
                    "balance management",
                    "virtual card budget",
                    "card allowance",
                    "budget control",
                    "spend allowance",
                ],
                "guides": ["guides/cards-and-funds.mdx"],
                "endpoints": [
                    "/developer/v1/limits",
                    "/developer/v1/limits/{spend_limit_id}",
                    "/developer/v1/cards/deferred/physical",
                    "/developer/v1/spend-programs",
                    "/developer/v1/card-programs",
                ],
                "warnings": ["All /cards endpoints except for /developer/v1/cards/deferred/physical are deprecated and should not be used. In Ramp's API, virtual cards are funded through 'limits' endpoints. Create a limit first to set the budget, then assign it to a user to automatically generate a virtual card."],
            },
            "user_management": {
                "keywords": [
                    "users",
                    "team",
                    "onboarding",
                    "permissions",
                    "departments",
                ],
                "guides": [],
                "endpoints": [
                    "/developer/v1/users",
                    "/developer/v1/departments",
                    "/developer/v1/locations",
                    "/developer/v1/entities",
                ],
                "warnings": [],
            },
            "expense_reporting": {
                "keywords": [
                    "expenses",
                    "transactions",
                    "export",
                    "reporting",
                    "analytics",
                ],
                "guides": [],
                "endpoints": [
                    "/developer/v1/transactions",
                    "/developer/v1/receipts",
                ],
                "warnings": [],
            },
            "agents": {
                "keywords": [
                    "mcp",
                    "agents",
                    "ai",
                    "claude",
                    "automation",
                    "workflows",
                    "mcp integration",
                    "model context protocol",
                    "mcp server",
                    "mcp setup",
                ],
                "guides": ["guides/ramp-mcp-remote.mdx"],
                "endpoints": [],
                "warnings": [],
            },
            "webhooks": {
                "keywords": [
                    "webhooks",
                    "webhook",
                    "real-time",
                    "events",
                    "notifications",
                    "push notifications",
                    "event subscriptions", 
                    "webhook subscription",
                    "webhook endpoint",
                    "real time updates",
                    "event driven",
                    "real time",
                    "push",
                    "subscribe",
                    "notification",
                ],
                "guides": ["webhooks.mdx"],
                "endpoints": ["/developer/v1/webhooks"],
                "warnings": [],
            },
        }

    def _load_openapi_spec(self) -> Dict[str, Any]:
        """Load the OpenAPI specification"""
        spec_path = self.project_root / "data" / "developer-api.json"
        with open(spec_path) as f:
            return json.load(f)

    def _load_guides(self) -> Dict[str, GuideContent]:
        """Load and parse all MDX guides"""
        guides = {}
        guides_dir = self.project_root / "data" / "developer-api"

        # Walk through all .mdx files
        for mdx_file in guides_dir.rglob("*.mdx"):
            try:
                with open(mdx_file, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)

                # Extract title from frontmatter or filename
                title = post.metadata.get(
                    "title", mdx_file.stem.replace("-", " ").title()
                )
                priority = post.metadata.get("priority")

                # Convert markdown to plain text for processing
                html = markdown.markdown(post.content)
                # Basic HTML to text (you could use BeautifulSoup for better cleaning)
                content = re.sub(r"<[^>]+>", "", html)

                # Create relative path for identification
                relative_path = mdx_file.relative_to(self.project_root)

                guides[str(relative_path)] = GuideContent(
                    title=title,
                    content=content,
                    priority=priority,
                    file_path=str(mdx_file),
                    use_cases=[],  # We'll populate this based on content analysis
                )
            except Exception as e:
                print(f"Error loading {mdx_file}: {e}", file=sys.stderr)
                continue

        return guides


    def detect_intent(self, query: str) -> Optional[str]:
        """Detect which use case cluster a query belongs to"""
        # Preprocess query for better matching
        query_lower = self._preprocess_query(query.lower())
        best_match = None
        best_score = 0
        best_raw_matches = 0

        for cluster_name, cluster_data in self.use_case_clusters.items():
            raw_matches = 0
            keywords = cluster_data.get("keywords", [])
            matched_keywords = []

            # Count keyword matches and track specificity
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    raw_matches += 1
                    matched_keywords.append(keyword)

            if raw_matches > 0:
                # Score based on raw matches + specificity bonus for multi-word keywords
                score = raw_matches
                for keyword in matched_keywords:
                    if len(keyword.split()) > 1:  # Multi-word keywords get bonus
                        score += 0.5
                    if keyword in ["ap", "ai"]:  # Penalize overly broad single-letter matches
                        score -= 0.3

                # Prefer higher raw match count, then higher score
                if (raw_matches > best_raw_matches) or (raw_matches == best_raw_matches and score > best_score):
                    best_score = score
                    best_raw_matches = raw_matches
                    best_match = cluster_name

        return best_match
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query to handle synonyms, noise words, and variations"""
        
        # Synonym mapping for better matching
        synonyms = {
            # Creation/issuance variants
            "creation": "create",
            "issuance": "issue", 
            "issuing": "issue",
            "provision": "create",
            "provisioning": "create",
            "generation": "create",
            "generating": "create",
            
            # Technical variants  
            "endpoint": "api",
            "endpoints": "api",
            "route": "api",
            "routes": "api",
            
            # Process variants
            "workflow": "process",
            "procedure": "process",
            "steps": "process",
            
            # Integration variants
            "integration": "integrate",
            "connection": "connect",
            "linking": "connect",
            
            # Common variations
            "setup": "set up",
            "config": "configure",
        }
        
        # Apply synonym replacements
        for original, replacement in synonyms.items():
            query = query.replace(original, replacement)
        
        # Remove noise words that add no semantic value
        noise_words = [
            " with ramp", " with the ramp", " using ramp", " using the ramp",
            " api", " the api", " ramp's api", " ramp api",
            " with", " using", " the", " a", " an",
            " how do i", " how to", " i want to", " i need to",
        ]
        
        for noise in noise_words:
            query = query.replace(noise, " ")
        
        # Clean up extra whitespace
        query = " ".join(query.split())
        
        return query.strip()

    


    
    def get_workflow_guidance(self, use_case: str) -> str:
        """Generate comprehensive workflow guidance for a use case using markdown files"""
        # Detect the primary use case cluster
        cluster = self.detect_intent(use_case.lower())
        
        if not cluster:
            return self._extract_general_guidance(use_case)
        
        # Get the cluster configuration
        cluster_data = self.use_case_clusters.get(cluster, {})
        guide_filenames = cluster_data.get("guides", [])
        
        if not guide_filenames:
            return self._extract_general_guidance(use_case)
        
        # Extract content from the relevant markdown guides
        guidance_content = self._extract_guidance_from_markdown(guide_filenames, use_case, cluster)
        
        return guidance_content
        
    def _extract_guidance_from_markdown(self, guide_filenames: List[str], use_case: str, cluster: str) -> str:
        """Extract guidance content from the single guide for this use case cluster"""
        extracted_sections = []
        
        # Since we have one guide per cluster, just use the first (and only) guide
        if guide_filenames:
            guide_filename = guide_filenames[0]
            guide_content = self._find_guide_by_filename(guide_filename)
            if guide_content:
                sections = self._extract_key_sections_from_guide(guide_content, cluster)
                if sections:
                    extracted_sections.extend(sections)
        
        if not extracted_sections:
            return self._extract_general_guidance(use_case)
            
        # Format the extracted sections into a coherent guide
        return self._format_extracted_guidance(extracted_sections, use_case, cluster)
        
    def _find_guide_by_filename(self, filename: str) -> Optional[str]:
        """Find and return the raw content of a guide by filename"""
        # Try direct file path first
        guide_file_path = self.project_root / "data" / "developer-api" / filename
        if guide_file_path.exists():
            try:
                with open(guide_file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass
        
        # Fall back to searching through loaded guides
        for guide_path, guide_content in self.guides.items():
            if filename in guide_path:
                return guide_content.content
        return None
    
        
    def _extract_key_sections_from_guide(self, guide_content: str, cluster: str, limit_sections: Optional[int] = None) -> List[Dict[str, str]]:
        """Extract key sections from a guide based on the cluster type"""
        sections = []
        
        # Sections specific to authentication cluster (OAuth flows)
        if cluster == 'authentication':
            oauth_sections = [
                "## Understanding environments",
                "## Quickstart: Authorize with Client Credentials",
                "### 1. Create a Developer App",
                "### 2. Request an Access Token", 
                "### 3. Make an API Call",
                "## FAQ: Client credentials flow",
                "## Authorization code: For multi-customer apps",
                "### Step 1: User is redirected to Ramp authorization URL",
                "### Step 2: User authenticates and approves access",
                "### Step 3: Exchange the `code` for an access token",
                "### Step 4: Refresh the access token",
                "## FAQ: Authorization code flow",
                "## Next steps",
                "## OAuth 2.0 Framework",
                "## Permission Model & Scopes",
                "## Token Management",
                "## Authorization Flow Deep Dive",
                "### Client Credentials Flow",
                "### Authorization Code Flow"
            ]
            
            for section_header in oauth_sections:
                section_content = self._extract_markdown_section(guide_content, section_header)
                if section_content:
                    sections.append({
                        'title': section_header.replace('### ', '').replace('## ', ''),
                        'content': section_content[:1200]  # Limit section length
                    })
                    
            return sections
        
        # Common sections to extract from any guide  
        common_sections = [
            "## Overview",
            "## Getting Started", 
            "## Quick Start",
            "## Implementation",
            "## Best Practices",
            "## Common Pitfalls",
            "## Examples",
            "## Next Steps",
            "## How It Works",
            "## How to Get Started",
            "## Key Features",
            "## Example Use Cases",
            "## Why Use",
            "## Sample Code"
        ]
        
        for section_header in common_sections:
            section_content = self._extract_markdown_section(guide_content, section_header)
            if section_content:
                sections.append({
                    'title': section_header.replace('## ', ''),
                    'content': section_content[:1000]  # Limit section length
                })
                
                # Apply limit if specified (for secondary guides)
                if limit_sections and len(sections) >= limit_sections:
                    break
                
        return sections
        
    def _format_extracted_guidance(self, sections: List[Dict[str, str]], use_case: str, cluster: str) -> str:
        """Format extracted sections into a coherent workflow guide"""
        cluster_titles = {
            'ap_workflow': 'Accounts Payable & Bill Management',
            'erp_integration': 'ERP/Accounting Integration', 
            'card_management': 'Card Management & Spending Controls',
            'user_management': 'User Management & Onboarding',
            'expense_reporting': 'Expense Reporting & Analytics',
            'agents': 'AI Agents & MCP Integration',
            'webhooks': 'Webhooks & Real-Time Events',
            'authentication': 'Authentication & Authorization'
        }
        
        title = cluster_titles.get(cluster, 'Ramp API Integration')
        
        formatted_guide = f"""# {title} Workflow

**Use Case**: {use_case}

*This guidance is extracted from Ramp's developer documentation and updated automatically.*

"""
        
        for section in sections:
            formatted_guide += f"## {section['title']}\n\n"
            formatted_guide += f"{section['content']}\n\n"
            
        # Add standard footer
        formatted_guide += """---

## IMPORTANT

- **Always validate code samples**: Use `validate_endpoint_usage` to validate any code you write. This will ensure all endpoints, query parameters, and conventions used are actually available in the OpenAPI specification 
- **Search documentation**: Use `search_documentation` for implementation guidance
- **Submit feedback**: Use `submit_feedback` to report issues or suggest improvements

*This guide is automatically generated from the latest Ramp developer documentation.*
"""
        
        return formatted_guide
        
    def _extract_general_guidance(self, use_case: str) -> str:
        """Provide general integration guidance when no specific cluster matches"""
        return f"""# General Integration Guidance

**Use Case**: {use_case}

## 🏗️ Approach

Since we couldn't match your use case to a specific workflow, here's a general approach:

1. **Identify the data you need** - What Ramp data do you want to access?
2. **Check available APIs** - Review endpoints at developer.ramp.com
3. **Start with authentication** - Use `get_started` tool for setup help
4. **Test in sandbox** - Always use demo-api.ramp.com first
5. **Validate your code** - Use `validate_endpoint_usage` to check your API implementation

## 💡 Common Use Cases

Try these keywords with `explore_use_case` for specific guidance:
- "bill payments" or "accounts payable"
- "quickbooks sync" or "accounting integration"  
- "card issuing" or "spending limits"
- "user management" or "employee onboarding"
- "expense reporting" or "analytics"
- "webhooks" or "real-time events"
- "ai integration" or "mcp server"

## 🔍 Next Steps

1. Use `search_documentation` to find implementation guidance
2. Use `validate_endpoint_usage` to check your code
3. Use `submit_feedback` to request guidance for your specific use case or submit a feature request

*This is general guidance. For specific workflows, use more targeted keywords.*
"""

    def _extract_markdown_section(self, content: str, section_header: str) -> str:
        """Extract a section from markdown content by header"""
        lines = content.split('\n')
        start_idx = None
        
        # Find section start
        for i, line in enumerate(lines):
            if line.strip().startswith(section_header):
                start_idx = i
                break
                
        if start_idx is None:
            return ""
            
        # Find next section or end
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            line = lines[i].strip()
            # Stop at next ## header, --- divider, or # header
            if (line.startswith('## ') or 
                line.startswith('---') or
                line.startswith('# ')):
                end_idx = i
                break
                
        # Extract and clean the section
        section_lines = lines[start_idx + 1:end_idx]  # Skip the header line
        section_text = '\n'.join(section_lines).strip()
        
        # Remove MDX/JSX components for cleaner text
        section_text = re.sub(r'<[^>]+>', '', section_text)
        section_text = re.sub(r'{[^}]+}', '', section_text)
        section_text = re.sub(r'import\s+.*', '', section_text)
        
        return section_text

