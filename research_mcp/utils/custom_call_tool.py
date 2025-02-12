import json
import traceback
from typing import Sequence

from llama_index.core.llms.llm import ToolSelection
from llama_index.core.tools import BaseTool, ToolOutput, FunctionTool


async def call_tool(tool: BaseTool, arguments: dict) -> ToolOutput:
    """Call a tool with arguments."""
    try:
        if (
            len(tool.metadata.get_parameters_dict()["properties"]) == 1
            and len(arguments) == 1
        ):
            # try:
            single_arg = arguments[next(iter(arguments))]
            if isinstance(tool, FunctionTool) and tool.async_fn:
                return await tool.acall(single_arg)
            else:
                return tool(single_arg)
            # except Exception:
            #     # some tools will REQUIRE kwargs, so try it
            #     return await tool.acall(**arguments)
        else:
            if isinstance(tool, FunctionTool) and tool.async_fn:
                return await tool.acall(**arguments)
            else:
                return tool(**arguments)
    except Exception as e:
        traceback.print_exc()
        return ToolOutput(
            content="Encountered error: " + str(e),
            tool_name=tool.metadata.name,
            raw_input=arguments,
            raw_output=str(e),
            is_error=True,
        )

async def custom_call_tool_with_selection(
    tool_call: ToolSelection,
    tools: Sequence["BaseTool"],
    verbose: bool = False,
) -> ToolOutput:

    tools_by_name = {tool.metadata.name: tool for tool in tools}
    name = tool_call.tool_name
    if verbose:
        arguments_str = json.dumps(tool_call.tool_kwargs, ensure_ascii=False)
        print("=== Calling Function ===")
        print(f"Calling function: {name} with args: {arguments_str}")
    tool = tools_by_name[name]
    output = await call_tool(tool, tool_call.tool_kwargs)

    if verbose:
        print("=== Function Output ===")
        print(output.content)

    return output