from pydantic import BaseModel, Field

class RMCPServerConfig(BaseModel):
    port: int = Field(8000, title="port")
    host: str = Field("0.0.0.0", title="host")
    notion_token: str = Field(..., title="Notion token")
    notion_root_database_id: str = Field(..., title="Notion root database id")
    app_token: str = Field(..., title="App token")