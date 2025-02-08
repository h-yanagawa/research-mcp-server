from pydantic import BaseModel, Field

class RMCPServerConfig(BaseModel):
    port: int = Field(8000, title="port")
    host: str = Field("localhost", title="host")
