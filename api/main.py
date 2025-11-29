"""FastAPI application exposing simple agent endpoints."""
from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from api.agents.profile_agent import ProfileAgent

logger = logging.getLogger(__name__)

app = FastAPI(title="Agent API", version="0.1.0")
profile_agent = ProfileAgent()


class ProfileRequest(BaseModel):
    text: str = Field(..., description="The profile text to analyze.")
    mode: Optional[str] = Field(None, description="Prompt mode to use for the agent.")
    context: Optional[Mapping[str, Any]] = Field(
        default=None, description="Optional context for prompt formatting."
    )


class ProfileResponse(BaseModel):
    mode: str
    result: str


@app.post("/analyze_profile", response_model=ProfileResponse)
async def analyze_profile(request: ProfileRequest) -> ProfileResponse:
    """Analyze a profile using the profile agent."""

    try:
        result = profile_agent.analyze(
            request.text,
            mode=request.mode,
            context=request.context,
        )
        selected_mode = request.mode or profile_agent.default_mode
        return ProfileResponse(mode=selected_mode, result=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    """Simple health endpoint for uptime checks."""

    return {"status": "ok"}
