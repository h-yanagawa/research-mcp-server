from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader

api_key_header: APIKeyHeader = APIKeyHeader(name="Authorization", auto_error=True)


class AuthDependency:
    def __init__(self, expected_token: str):
        self._expected_token = expected_token

    def verify_api_key(self, api_key: str = Depends(api_key_header)):
        if api_key != "Bearer " + self._expected_token:
            raise HTTPException(status_code=403, detail="Invalid API Key")
