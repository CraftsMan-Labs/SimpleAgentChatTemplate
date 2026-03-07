from __future__ import annotations

import uuid

from app.schemas.stream import (
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionDelta,
)


def create_completion_id() -> str:
    return f"chatcmpl_{uuid.uuid4().hex[:24]}"


def sse_data(payload: ChatCompletionChunk) -> str:
    return f"data: {payload.model_dump_json(exclude_none=True)}\n\n"


def chunk_payload(
    *, completion_id: str, created: int, model_id: str, delta: ChatCompletionDelta
) -> ChatCompletionChunk:
    return ChatCompletionChunk(
        id=completion_id,
        created=created,
        model=model_id,
        choices=[ChatCompletionChunkChoice(index=0, delta=delta, finish_reason=None)],
    )


def role_chunk(*, completion_id: str, created: int, model_id: str) -> str:
    return sse_data(
        chunk_payload(
            completion_id=completion_id,
            created=created,
            model_id=model_id,
            delta=ChatCompletionDelta(role="assistant"),
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
            delta=ChatCompletionDelta(content=content),
        )
    )


def stop_chunk(*, completion_id: str, created: int, model_id: str) -> str:
    payload = ChatCompletionChunk(
        id=completion_id,
        created=created,
        model=model_id,
        choices=[
            ChatCompletionChunkChoice(
                index=0,
                delta=ChatCompletionDelta(),
                finish_reason="stop",
            )
        ],
    )
    return sse_data(payload)
