# Ramp Developer MCP Server

A local Model Context Protocol (MCP) server that provides AI assistants with access to Ramp's developer documentation, API schemas, and development guidance. This server enables natural language queries about Ramp's API endpoints, authentication methods, data relationships, and implementation patterns. Built specifically for developers building on Ramp's platform, it serves as an intelligent companion for API integration and development workflows. The server runs locally and processes Ramp's comprehensive developer documentation to provide contextual, accurate responses about API usage and best practices.

## Example Queries and Use Cases

### API Development
- "How do I authenticate with the Ramp API?"
- "Show me the schema for the cards endpoint"
- "What are the required fields for creating a new user?"
- "How do I handle rate limiting in the Ramp API?"

### Data Relationships
- "How are cards related to users in the API?"
- "What's the relationship between transactions and bills?"
- "Show me how to link a purchase order to a bill"

### Implementation Guidance
- "What are the best practices for handling webhooks?"
- "How do I implement single-use card creation?"
- "What scopes do I need for bill management?"
- "How should I structure pagination for large datasets?"

### Troubleshooting
- "Why am I getting a 403 error on the users endpoint?"
- "What's the proper format for monetary values?"
- "How do I debug failed API requests?"

## Available Tools

### Core Tools

1. **`ping`** - Test server connectivity and health
2. **`search_documentation`** - Search through Ramp's developer documentation for specific topics, endpoints, or concepts
3. **`get_endpoint_schema`** - Retrieve detailed OpenAPI schema information for specific Ramp API endpoints
4. **`submit_feedback`** - Submit feedback about the MCP server or Ramp API development experience

### Documentation Coverage

The server includes comprehensive documentation for:
- **Authentication & Authorization** - OAuth flows, API keys, scopes
- **API Endpoints** - Cards, users, bills, transactions, transfers, and more
- **Data Relationships** - How different Ramp entities connect
- **Rate Limiting** - Request limits and best practices
- **Webhooks** - Event handling and security
- **Error Handling** - Common errors and debugging approaches
- **Monetary Values** - Proper formatting and precision
- **Pagination** - Handling large result sets
- **Category Codes** - Spending categories and classifications

## How to Use

### Prerequisites

1. **Python 3.8+** with `uv` package manager
2. **MCP-compatible client** (Claude Desktop, Claude Code, or other MCP client)
3. **Git** for cloning the repository

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/riker-t/ramp-dev-mcp.git
   cd ramp-dev-mcp
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Test the server:**
   ```bash
   uv run python src/server.py
   ```
   The server should start and display initialization messages.

### Claude Desktop Configuration

1. **Locate your configuration file:**
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add the server configuration:**

   **Option 1: Full path configuration (recommended):**
   ```json
   {
     "mcpServers": {
       "ramp-developer": {
         "command": "/Users/yourusername/.local/bin/uv",
         "args": [
           "--directory",
           "/path/to/ramp-dev-mcp",
           "run",
           "src/server.py"
         ]
       }
     }
   }
   ```
   
   **Option 2: Simple configuration (if `uv` is in your PATH):**
   ```json
   {
     "mcpServers": {
       "ramp-developer": {
         "command": "uv",
         "args": ["run", "python", "src/server.py"],
         "cwd": "/path/to/ramp-dev-mcp"
       }
     }
   }
   ```
   
   **Configuration notes:**
   - Replace `/path/to/ramp-dev-mcp` with the actual path where you cloned the repository
   - Replace `/Users/yourusername/.local/bin/uv` with your actual `uv` installation path
   - To find your `uv` path, run: `which uv` in your terminal
   - If `uv` is not in your PATH, use the full path configuration

3. **Restart Claude Desktop**

### Claude Code Configuration

```bash
# Navigate to your project directory
cd /path/to/ramp-dev-mcp

# Add the MCP server
claude mcp add ramp-developer uv run python src/server.py

# Start using it in your conversations
# The server will be automatically available in your Claude Code sessions
```

### Other MCP Clients

For other MCP-compatible clients, configure them to run:
```bash
uv run python src/server.py
```

From the project directory.

### Getting Started

Once configured, you can start asking questions like:
- "How do I create a new card using the Ramp API?"
- "What's the schema for the bills endpoint?"
- "Show me documentation about webhook security"
- "How do I handle rate limiting?"

The AI assistant will use the MCP server to search documentation, retrieve schemas, and provide accurate, contextual answers about Ramp API development.

### Troubleshooting

**Server fails to start:**
- Ensure Python 3.8+ is installed
- Run `uv sync` to install dependencies
- Check that you're in the correct directory

**Configuration not working:**
- Verify the file path in your MCP client configuration
- Ensure JSON syntax is correct
- Restart your MCP client after configuration changes

**Getting help:**
- Use the `submit_feedback` tool to report issues
- Check the console output for error messages
- Ensure all dependencies are properly installed