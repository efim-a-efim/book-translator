from __future__ import annotations

from openai import AsyncOpenAI


def create_client(api_key: str, base_url: str | None) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        max_retries=0,
    )
