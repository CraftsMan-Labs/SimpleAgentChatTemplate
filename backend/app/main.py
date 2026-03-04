from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.internal import router as internal_router
from app.api.openai import router as openai_router
from app.core.config import settings
from app.core.db import engine
from app.models import Base
from app.services.workflow_registry import ensure_seed_models


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Conversation-Id"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        ensure_seed_models(db)
    finally:
        db.close()


@app.exception_handler(HTTPException)
async def openai_error_handler(_, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": str(exc.detail),
                "type": "invalid_request_error",
                "param": None,
                "code": None,
            }
        },
    )


app.include_router(health_router)
app.include_router(internal_router)
app.include_router(openai_router)
