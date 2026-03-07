from __future__ import annotations

import json
import uuid
from typing import Any


def create_completion_id() -> str:
    return f"chatcmpl_{uuid.uuid4().hex[:24]}"


def sse_data(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def chunk_payload(
    *, completion_id: str, created: int, model_id: str, delta: dict[str, Any]
) -> dict[str, Any]:
    return {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model_id,
        "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
    }


def role_chunk(*, completion_id: str, created: int, model_id: str) -> str:
    return sse_data(
        chunk_payload(
            completion_id=completion_id,
            created=created,
            model_id=model_id,
            delta={"role": "assistant"},
        )
    )


def content_chunk(
    *, completion_id: str, created: int, model_id: str, content: str
) -> str:
    return sse_data(
        chunk_payload(
            completion_id=completion_id,
            created=created,
            model_id=model_id,
            delta={"content": content},
        )
    )


def stop_chunk(*, completion_id: str, created: int, model_id: str) -> str:
    payload = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model_id,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    return sse_data(payload)
