import os
from typing import Optional

from openai import OpenAI


def get_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """Return an OpenAI client using the provided or environment API key."""
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY is not configured")

    return OpenAI(api_key=key)
