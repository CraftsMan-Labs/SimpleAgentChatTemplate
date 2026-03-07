from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.openai import ChatMessage


class WorkflowUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class WorkflowOptions(BaseModel):
    trace: dict[str, Any]
    telemetry: dict[str, Any]


class WorkflowInput(BaseModel):
    messages: list[dict[str, Any]]
    email_text: str
    workflow_registry: dict[str, str] | None = None


class WorkflowRunResult(BaseModel):
    assistant_text: str
    raw_result: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)
    usage: WorkflowUsage = Field(default_factory=WorkflowUsage)


class WorkflowEventRecord(BaseModel):
    event_type: str = "unknown"
    node_id: str | None = None
    delta: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowStreamDelta(BaseModel):
    type: Literal["delta"] = "delta"
    content: str
    step_id: str | None = None
    step_name: str | None = None


class WorkflowStreamCompleted(BaseModel):
    type: Literal["completed"] = "completed"
    assistant_text: str
    raw_result: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)
    usage: WorkflowUsage = Field(default_factory=WorkflowUsage)


WorkflowStreamItem = WorkflowStreamDelta | WorkflowStreamCompleted


def messages_to_payload(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    return [m.model_dump(exclude_none=True) for m in messages]
