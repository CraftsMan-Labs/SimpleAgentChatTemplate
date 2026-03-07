from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.openai import OpenAIErrorBody
from app.schemas.openai import WorkflowInventoryItem


class HealthResponse(BaseModel):
    status: str


class WorkflowInventoryResponse(BaseModel):
    data: list[WorkflowInventoryItem]


class ReloadWorkflowsResponse(BaseModel):
    status: str = "ok"
    created: int
    updated: int
    disabled: int
    warnings: list[str] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    id: str
    external_conversation_id: str | None
    model_id: str
    title: str | None
    status: str


class ConversationMessage(BaseModel):
    id: str
    role: str
    content: str
    turn_index: int
    created_at: datetime | None


class ConversationRun(BaseModel):
    id: str
    workflow_id: str
    terminal_node: str | None
    trace_id: str | None
    status: str
    created_at: datetime | None


class ConversationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation: ConversationSummary
    messages: list[ConversationMessage]
    runs: list[ConversationRun]


class NotFoundErrorResponse(BaseModel):
    error: OpenAIErrorBody
