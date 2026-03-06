from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.models import WorkflowModel
from app.schemas.openai import (
    ChatCompletionsRequest,
    ChatCompletionsResponse,
    ChatCompletionChoice,
    ChatMessageOut,
    ModelListResponse,
    OpenAIErrorResponse,
    Usage,
)
from app.services.conversations import (
    persist_assistant_message,
    persist_messages,
    persist_workflow_events,
    persist_workflow_run,
    resolve_conversation,
)
from app.services.workflow_execution import run_non_stream, run_stream
from app.services.workflow_registry import get_model_or_none, list_model_cards


router = APIRouter(prefix="/v1", tags=["openai-compatible"])
logger = logging.getLogger(__name__)


def raise_openai_error(
    status_code: int, message: str, error_type: str, param: str | None, code: str | None
) -> None:
    payload = OpenAIErrorResponse(
        error={"message": message, "type": error_type, "param": param, "code": code}  # type: ignore[arg-type]
    )
    raise HTTPException(status_code=status_code, detail=payload.model_dump())


@router.get("/models", response_model=ModelListResponse)
def get_models(db: Session = Depends(db_session)) -> ModelListResponse:
    return ModelListResponse(data=list_model_cards(db))


def _resolve_model_or_error(db: Session, model_id: str) -> WorkflowModel:
    model = get_model_or_none(db, model_id)
    if model is None:
        raise_openai_error(
            404,
            f"The model `{model_id}` does not exist.",
            "invalid_request_error",
            "model",
            "model_not_found",
        )
    return model


@router.post("/chat/completions", response_model=None)
def chat_completions(
    payload: ChatCompletionsRequest,
    db: Session = Depends(db_session),
    x_conversation_id: str | None = Header(default=None, alias="X-Conversation-Id"),
) -> Any:
    if not payload.messages:
        raise_openai_error(
            400,
            "`messages` must not be empty.",
            "invalid_request_error",
            "messages",
            None,
        )

    model = _resolve_model_or_error(db, payload.model)

    conversation, conversation_external_id = resolve_conversation(
        db,
        external_conversation_id=x_conversation_id,
        model=model,
        user_id=payload.user,
    )
    request_message_id = persist_messages(
        db, conversation=conversation, messages=payload.messages
    )

    if payload.stream:
        db.commit()
        completion_id = f"chatcmpl_{uuid.uuid4().hex[:24]}"
        created = int(time.time())

        def stream_events() -> Any:
            role_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": payload.model,
                "choices": [
                    {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
                ],
            }
            yield f"data: {json.dumps(role_chunk)}\n\n"

            final_payload: dict[str, Any] | None = None

            for item in run_stream(payload.messages, model, conversation_external_id):
                if item.get("type") == "delta":
                    chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": payload.model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": item.get("content", "")},
                                "finish_reason": None,
                            }
                        ],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    continue
                if item.get("type") == "completed":
                    final_payload = item

            if final_payload is None:
                raise RuntimeError("Stream completed without a final payload")

            assistant_text = str(final_payload.get("assistant_text") or "")
            raw_result = final_payload.get("raw_result", {})
            events = final_payload.get("events", [])
            usage = final_payload.get("usage", {})

            try:
                response_message_id = persist_assistant_message(
                    db, conversation=conversation, text=assistant_text
                )
                workflow_run = persist_workflow_run(
                    db,
                    conversation=conversation,
                    request_message_id=request_message_id,
                    response_message_id=response_message_id,
                    model=model,
                    result=raw_result if isinstance(raw_result, dict) else {},
                    usage=usage if isinstance(usage, dict) else {},
                )
                if isinstance(events, list):
                    persist_workflow_events(db, run=workflow_run, events=events)
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Failed to persist streaming completion artifacts")

            final_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": payload.model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        headers = {"X-Conversation-Id": conversation_external_id}
        return StreamingResponse(
            stream_events(), media_type="text/event-stream", headers=headers
        )

    run = run_non_stream(payload.messages, model, conversation_external_id)
    response_message_id = persist_assistant_message(
        db, conversation=conversation, text=run.assistant_text
    )
    workflow_run = persist_workflow_run(
        db,
        conversation=conversation,
        request_message_id=request_message_id,
        response_message_id=response_message_id,
        model=model,
        result=run.raw_result,
        usage=run.usage,
    )
    persist_workflow_events(db, run=workflow_run, events=run.events)
    db.commit()

    response = ChatCompletionsResponse(
        id=f"chatcmpl_{uuid.uuid4().hex[:24]}",
        object="chat.completion",
        created=int(time.time()),
        model=payload.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessageOut(role="assistant", content=run.assistant_text),
                finish_reason="stop",
            )
        ],
        usage=Usage(**run.usage),
        metadata={
            "conversation_id": conversation_external_id,
            "workflow_id": run.raw_result.get("workflow_id") or model.workflow_id,
            "terminal_node": run.raw_result.get("terminal_node"),
            "trace_id": run.raw_result.get("trace_id"),
        },
    )

    return JSONResponse(
        response.model_dump(), headers={"X-Conversation-Id": conversation_external_id}
    )
