# from langchain_core.tools import tool

# from langchain.tools import BaseTool
# from mcp_protocol import MCPClient  # Hypothetical MCP library

# class MCPClientTool(BaseTool):
#     name = "mcp_client"
#     description = "Call external MCP servers (GitHub/Google Maps)"

#     def _run(self, server_url: str, action: str, params: dict):
#         client = MCPClient(server_url)
#         return client.execute_action(action, params)

# # Define custom tool
# @tool
# def fetch_github_issues(repo: str) -> str:
#     """Fetch open issues from a GitHub repo via MCP"""
#     mcp_response = MCPClientTool().run(
#         server_url="https://api.github.com/mcp",
#         action="get_issues",
#         params={"repo": repo}
#     )
#     return format_issues(mcp_response)