from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Conversation, Message, WorkflowEvent, WorkflowModel, WorkflowRun
from app.schemas.openai import ChatMessage
from app.schemas.workflow_execution import WorkflowEventRecord, WorkflowUsage


def resolve_conversation(
    db: Session,
    *,
    external_conversation_id: str | None,
    model: WorkflowModel,
    user_id: str | None,
) -> tuple[Conversation, str]:
    if external_conversation_id:
        existing = db.scalar(
            select(Conversation).where(
                Conversation.external_conversation_id == external_conversation_id
            )
        )
        if existing is not None:
            return existing, external_conversation_id

    external_id = external_conversation_id or f"conv_{uuid.uuid4().hex[:20]}"
    conversation = Conversation(
        external_conversation_id=external_id,
        model_id=model.model_id,
        title=settings.default_chat_title,
        user_id=user_id,
        status="active",
    )
    db.add(conversation)
    db.flush()
    return conversation, external_id


def persist_messages(
    db: Session, *, conversation: Conversation, messages: list[ChatMessage]
) -> uuid.UUID | None:
    if not messages:
        return None
    max_turn = db.scalar(
        select(func.max(Message.turn_index)).where(
            Message.conversation_id == conversation.id
        )
    )
    turn_index = int(max_turn or 0)
    last_id: uuid.UUID | None = None
    for msg in messages:
        turn_index += 1
        row = Message(
            conversation_id=conversation.id,
            role=msg.role,
            content=msg.content,
            name=msg.name,
            tool_call_id=msg.tool_call_id,
            tool_calls=msg.tool_calls,
            turn_index=turn_index,
        )
        db.add(row)
        db.flush()
        last_id = row.id
    return last_id


def persist_assistant_message(
    db: Session, *, conversation: Conversation, text: str
) -> uuid.UUID:
    max_turn = db.scalar(
        select(func.max(Message.turn_index)).where(
            Message.conversation_id == conversation.id
        )
    )
    turn_index = int(max_turn or 0) + 1
    row = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=text,
        turn_index=turn_index,
    )
    db.add(row)
    db.flush()
    return row.id


def persist_workflow_run(
    db: Session,
    *,
    conversation: Conversation,
    request_message_id: uuid.UUID | None,
    response_message_id: uuid.UUID | None,
    model: WorkflowModel,
    result: dict[str, Any],
    usage: WorkflowUsage,
    status: str = "completed",
    error: dict[str, Any] | None = None,
) -> WorkflowRun:
    run = WorkflowRun(
        conversation_id=conversation.id,
        request_message_id=request_message_id,
        response_message_id=response_message_id,
        model_id=model.model_id,
        workflow_id=result.get("workflow_id") or model.workflow_id,
        workflow_path=model.workflow_path,
        terminal_node=result.get("terminal_node"),
        terminal_output=result.get("terminal_output")
        if isinstance(result.get("terminal_output"), dict)
        else None,
        trace=result.get("trace") if isinstance(result.get("trace"), list) else None,
        trace_id=result.get("trace_id"),
        step_timings=result.get("step_timings")
        if isinstance(result.get("step_timings"), list)
        else None,
        usage=usage.model_dump(),
        total_elapsed_ms=result.get("total_elapsed_ms"),
        raw_result=result,
        status=status,
        error=error,
    )
    db.add(run)
    db.flush()
    return run


def persist_workflow_events(
    db: Session, *, run: WorkflowRun, events: list[WorkflowEventRecord]
) -> None:
    for idx, event in enumerate(events, start=1):
        row = WorkflowEvent(
            run_id=run.id,
            seq=idx,
            event_type=event.event_type,
            node_id=event.node_id,
            delta=event.delta,
            payload=event.payload,
        )
        db.add(row)
