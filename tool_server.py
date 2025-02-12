import os

import uvicorn
from fastapi import FastAPI, Depends

from research_mcp.data.rmcp_server_config import RMCPServerConfig
from research_mcp.dependencies.auth_dependency import AuthDependency
from research_mcp.router import notion_ops
from research_mcp.tools.notion_tool import NotionToolSpec
from dotenv import load_dotenv

load_dotenv(verbose=True)

api = FastAPI()
config = RMCPServerConfig(
    port=3031,
    notion_token=os.environ["NOTION_TOKEN"],
    notion_root_database_id=os.environ["NOTION_ROOT_DATABASE_ID"],
    app_token=os.environ["APP_TOKEN"]
)

notion_tool = NotionToolSpec(config)
auth = AuthDependency(config.app_token)
api.include_router(notion_ops.get_router(notion_tool, auth.verify_api_key))


@api.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(api, host=config.host, port=int(os.environ.get("PORT", config.port)), log_level="debug")
