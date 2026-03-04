from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ChatCompletionsRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    user: str | None = None
    metadata: dict[str, Any] | None = None


class ChatMessageOut(BaseModel):
    role: Literal["assistant"]
    content: str
    refusal: None = None


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessageOut
    finish_reason: str | None = None


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionsResponse(BaseModel):
    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: Usage
    system_fingerprint: str | None = "yaml-workflow-v1"
    metadata: dict[str, Any] | None = None


class ModelCard(BaseModel):
    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str = "simple-agent-chat"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelListResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[ModelCard]


class OpenAIErrorBody(BaseModel):
    message: str
    type: str
    param: str | None = None
    code: str | None = None


class OpenAIErrorResponse(BaseModel):
    error: OpenAIErrorBody


class WorkflowInventoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_id: str
    display_name: str
    kind: str
    workflow_id: str
    workflow_path: str
    registry: dict[str, str]
    metadata: dict[str, Any]
    is_active: bool
