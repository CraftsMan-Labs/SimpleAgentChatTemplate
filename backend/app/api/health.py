from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import db_session


router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(db_session)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
