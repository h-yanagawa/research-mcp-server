# Research MCP Server

[![smithery badge](https://smithery.ai/badge/@h-yanagawa/research-mcp-server)](https://smithery.ai/server/@h-yanagawa/research-mcp-server)

This is a repository for the research project on the MCP server.

## Features
* Work as an MCP server.
* Retrieve survey data from Notion.
* Create survey pages in Notion.

## Prerequisites

* Python 3.12.1 or later
* uv 0.5.25 or later
* Claude Desktop Client

## How to Use

### Installing via Smithery

To install Research MCP Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@h-yanagawa/research-mcp-server):

```bash
npx -y @smithery/cli install @h-yanagawa/research-mcp-server --client claude
```

1. Clone the repository.
2. Obtain a Notion token from [Notion Integrations](https://www.notion.so/my-integrations).
3. Create a database page in Notion and retrieve the database ID. The database ID is the last part of the page URL.
4. Create a `.env` file as shown below:
    ```shell
    NOTION_TOKEN=[YOUR_NOTION_TOKEN]
    NOTION_ROOT_DATABASE_ID=[YOUR_NOTION_DATABASE_ID]
    ```
5. Add an MCP server definition to `claude_desktop.json`:
    ```json
    {
      ...
      "mcpServers": {
        "Research MCP Server": {
          "command": "uv",
          "args": [
            "run",
            "--with", "mcp[cli]",
            "--with", "notion-client",
            "--with", "pydantic",
            "mcp",
            "run",
            "/path/to/research-mcp-server/server.py"
          ]
        }
      }
    }
    ```
6. Restart the Claude Desktop Client to launch the Research MCP Server.
7. Ask Claude to perform a survey and review the results.
