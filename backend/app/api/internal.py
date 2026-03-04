from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.models import Conversation, Message, WorkflowModel, WorkflowRun
from app.services.workflow_registry import ensure_seed_models


router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/workflows")
def list_workflows(db: Session = Depends(db_session)) -> dict:
    models = db.scalars(
        select(WorkflowModel).order_by(WorkflowModel.model_id.asc())
    ).all()
    return {
        "data": [
            {
                "model_id": m.model_id,
                "display_name": m.display_name,
                "kind": m.kind,
                "workflow_id": m.workflow_id,
                "workflow_path": m.workflow_path,
                "registry": m.registry,
                "metadata": m.metadata_json,
                "is_active": m.is_active,
            }
            for m in models
        ]
    }


@router.post("/workflows/reload")
def reload_workflows(db: Session = Depends(db_session)) -> dict:
    result = ensure_seed_models(db)
    return {"status": "ok", **result}


@router.get("/conversations/{external_id}")
def get_conversation(external_id: str, db: Session = Depends(db_session)) -> dict:
    convo = db.scalar(
        select(Conversation).where(Conversation.external_conversation_id == external_id)
    )
    if convo is None:
        return {"error": "not_found"}
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
    return {
        "conversation": {
            "id": str(convo.id),
            "external_conversation_id": convo.external_conversation_id,
            "model_id": convo.model_id,
            "title": convo.title,
            "status": convo.status,
        },
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "turn_index": m.turn_index,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "runs": [
            {
                "id": str(r.id),
                "workflow_id": r.workflow_id,
                "terminal_node": r.terminal_node,
                "trace_id": r.trace_id,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ],
    }
