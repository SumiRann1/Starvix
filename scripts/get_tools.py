from agent_cli import get_tools_sync

tools = get_tools_sync()
for tool in tools:
    print(tool.name, "-------", tool.description, "-------", tool.args_schema, "-------", tool.return_direct)