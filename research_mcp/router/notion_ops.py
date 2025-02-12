import json

from fastapi import APIRouter, Request, Depends
from llama_index.core.llms.llm import ToolSelection

from research_mcp.tools.notion_tool import NotionToolSpec
from research_mcp.utils.custom_call_tool import custom_call_tool_with_selection


def get_router(notion_tool: NotionToolSpec, auth_dependency):
    router = APIRouter()
    tools = notion_tool.to_tool_list()
    oai_tools = [t.metadata.to_openai_tool()['function'] for t in tools]
    for t in oai_tools:
        t['type'] = 'function'  # TODO: OpenAI docs didn't say this was needed, but it was


    @router.get("/notion/tools", dependencies=[Depends(auth_dependency)])
    async def get_tools():
        """
        利用可能なツールの一覧を取得するエンドポイント。
        """
        return oai_tools


    @router.post("/notion/{function_name}", dependencies=[Depends(auth_dependency)])
    async def post_notion_ops(function_name: str, request: Request):
        """
        Notion APIを操作するエンドポイント。
        """
        body = await request.body()
        tool_selection = ToolSelection(
            tool_id="tool_id",
            tool_name=function_name,
            tool_kwargs=json.loads(body.decode())
        )
        tool_result = await custom_call_tool_with_selection(tool_selection, tools, verbose=True)
        return tool_result.content

    @router.get("/notion/{function_name}", dependencies=[Depends(auth_dependency)])
    async def get_notion_ops(function_name: str, request: Request):
        """
        Notion APIを操作するエンドポイント。
        """
        tool_selection = ToolSelection(
            tool_id="tool_id",
            tool_name=function_name,
            tool_kwargs=dict(request.query_params)
        )
        tool_result = await custom_call_tool_with_selection(tool_selection, tools, verbose=True)
        return tool_result.content


    return router