from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os

API_KEY = os.getenv("API_KEY", "")

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Unauthorized - Invalid or missing API Key")
        
        return await call_next(request)
