from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.models import Conversation, Message, WorkflowModel, WorkflowRun
from app.schemas.internal import (
    ConversationDetailResponse,
    ConversationMessage,
    ConversationRun,
    ConversationSummary,
    NotFoundErrorResponse,
    ReloadWorkflowsResponse,
    WorkflowInventoryResponse,
)
from app.schemas.openai import (
    OpenAIErrorBody,
    OpenAIErrorResponse,
    WorkflowInventoryItem,
)
from app.services.workflow_registry import ensure_seed_models


router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/workflows", response_model=WorkflowInventoryResponse)
def list_workflows(db: Session = Depends(db_session)) -> WorkflowInventoryResponse:
    models = db.scalars(
        select(WorkflowModel).order_by(WorkflowModel.model_id.asc())
    ).all()
    return WorkflowInventoryResponse(
        data=[
            WorkflowInventoryItem(
                model_id=m.model_id,
                display_name=m.display_name,
                kind=m.kind,
                workflow_id=m.workflow_id,
                workflow_path=m.workflow_path,
                registry=m.registry,
                metadata=m.metadata_json,
                is_active=m.is_active,
            )
            for m in models
        ]
    )


@router.post("/workflows/reload", response_model=ReloadWorkflowsResponse)
def reload_workflows(db: Session = Depends(db_session)) -> ReloadWorkflowsResponse:
    result = ensure_seed_models(db)
    return ReloadWorkflowsResponse(
        status="ok",
        created=result.created,
        updated=result.updated,
        disabled=result.disabled,
        warnings=result.warnings,
    )


@router.get(
    "/conversations/{external_id}",
    response_model=ConversationDetailResponse,
    responses={404: {"model": NotFoundErrorResponse}},
)
def get_conversation(
    external_id: str, db: Session = Depends(db_session)
) -> ConversationDetailResponse:
    convo = db.scalar(
        select(Conversation).where(Conversation.external_conversation_id == external_id)
    )
    if convo is None:
        error = OpenAIErrorResponse(
            error=OpenAIErrorBody(
                message=f"Conversation `{external_id}` was not found.",
                type="invalid_request_error",
                param="external_id",
                code="not_found",
            )
        )
        raise HTTPException(status_code=404, detail=error.model_dump())
    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == convo.id)
        .order_by(Message.turn_index.asc())
    ).all()
    runs = db.scalars(
        select(WorkflowRun)
        .where(WorkflowRun.conversation_id == convo.id)
        .order_by(WorkflowRun.created_at.desc())
    ).all()
    return ConversationDetailResponse(
        conversation=ConversationSummary(
            id=str(convo.id),
            external_conversation_id=convo.external_conversation_id,
            model_id=convo.model_id,
            title=convo.title,
            status=convo.status,
        ),
        messages=[
            ConversationMessage(
                id=str(m.id),
                role=m.role,
                content=m.content,
                turn_index=m.turn_index,
                created_at=m.created_at,
            )
            for m in messages
        ],
        runs=[
            ConversationRun(
                id=str(r.id),
                workflow_id=r.workflow_id,
                terminal_node=r.terminal_node,
                trace_id=r.trace_id,
                status=r.status,
                created_at=r.created_at,
            )
            for r in runs
        ],
    )
