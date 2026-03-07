from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.internal import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(db_session)) -> HealthResponse:
    db.execute(text("SELECT 1"))
    return HealthResponse(status="ok")
