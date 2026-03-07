from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import WorkflowModel
from app.schemas.openai import ModelCard
from app.schemas.workflow_registry import SeedModelsResult


def model_id_from_workflow_id(workflow_id: str) -> str:
    return f"{settings.model_prefix}/{workflow_id}"


def parse_workflow_file(path: Path) -> dict[str, Any] | None:
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    if not isinstance(parsed.get("id"), str):
        return None
    return parsed


def scan_workflows(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    results: list[tuple[Path, dict[str, Any]]] = []
    for path in root.rglob("*.yaml"):
        parsed = parse_workflow_file(path)
        if parsed is None:
            continue
        results.append((path.resolve(), parsed))
    return results


def upsert_workflow_model(
    db: Session,
    *,
    model_id: str,
    display_name: str,
    kind: str,
    workflow_id: str,
    workflow_path: str,
    registry: dict[str, str] | None = None,
    metadata: dict[str, Any] | None = None,
    is_active: bool = True,
) -> WorkflowModel:
    existing = db.scalar(
        select(WorkflowModel).where(WorkflowModel.model_id == model_id)
    )
    payload_registry = registry or {}
    payload_metadata = metadata or {}
    if existing is None:
        existing = WorkflowModel(
            model_id=model_id,
            display_name=display_name,
            kind=kind,
            workflow_id=workflow_id,
            workflow_path=workflow_path,
            registry=payload_registry,
            metadata_json=payload_metadata,
            is_active=is_active,
        )
        db.add(existing)
    else:
        existing.display_name = display_name
        existing.kind = kind
        existing.workflow_id = workflow_id
        existing.workflow_path = workflow_path
        existing.registry = payload_registry
        existing.metadata_json = payload_metadata
        existing.is_active = is_active
    return existing


def ensure_seed_models(db: Session) -> SeedModelsResult:
    created = 0
    updated = 0
    disabled = 0
    warnings: list[str] = []

    root = settings.workflow_root_path
    if not root.exists():
        warnings.append(f"Workflow root does not exist: {root}")
        return SeedModelsResult(
            created=created,
            updated=updated,
            disabled=disabled,
            warnings=warnings,
        )

    seen_model_ids: set[str] = set()

    starter_path = (root / settings.workflow_starter_file).resolve()
    if starter_path.exists():
        starter_workflow = parse_workflow_file(starter_path)
        if starter_workflow is not None:
            wid = starter_workflow["id"]
            mid = model_id_from_workflow_id(wid)
            seen_model_ids.add(mid)
            existing = db.scalar(
                select(WorkflowModel).where(WorkflowModel.model_id == mid)
            )
            upsert_workflow_model(
                db,
                model_id=mid,
                display_name=starter_workflow.get("metadata", {}).get("name", wid),
                kind="single_workflow",
                workflow_id=wid,
                workflow_path=str(starter_path),
                registry={},
                metadata={
                    "tags": starter_workflow.get("metadata", {}).get("tags", []),
                    "version": starter_workflow.get("version"),
                },
                is_active=True,
            )
            if existing is None:
                created += 1
            else:
                updated += 1
    else:
        warnings.append(f"Starter workflow not found: {starter_path}")

    orchestrator_path = (root / settings.workflow_orchestrator_file).resolve()
    subgraph_path = (root / settings.workflow_subgraph_file).resolve()
    if orchestrator_path.exists() and subgraph_path.exists():
        orchestrator_workflow = parse_workflow_file(orchestrator_path)
        if orchestrator_workflow is not None:
            mid = f"{settings.model_prefix}/orchestrator-hr-bundle"
            seen_model_ids.add(mid)
            existing = db.scalar(
                select(WorkflowModel).where(WorkflowModel.model_id == mid)
            )
            upsert_workflow_model(
                db,
                model_id=mid,
                display_name="Orchestrator HR Bundle",
                kind="workflow_bundle",
                workflow_id=orchestrator_workflow["id"],
                workflow_path=str(orchestrator_path),
                registry={"hr_warning_email_subgraph": str(subgraph_path)},
                metadata={
                    "tags": orchestrator_workflow.get("metadata", {}).get("tags", []),
                    "version": orchestrator_workflow.get("version"),
                },
                is_active=True,
            )
            if existing is None:
                created += 1
            else:
                updated += 1
    elif orchestrator_path.exists() and not subgraph_path.exists():
        warnings.append(f"Orchestrator exists but subgraph missing: {subgraph_path}")
    elif subgraph_path.exists() and not orchestrator_path.exists():
        warnings.append(
            f"Subgraph exists but orchestrator missing: {orchestrator_path}"
        )
    else:
        warnings.append(
            "Grouped workflow bundle skipped because orchestrator/subgraph files were not found"
        )

    all_models = db.scalars(select(WorkflowModel)).all()
    for model in all_models:
        if model.model_id not in seen_model_ids and model.is_active:
            model.is_active = False
            disabled += 1

    db.commit()
    return SeedModelsResult(
        created=created,
        updated=updated,
        disabled=disabled,
        warnings=warnings,
    )


def list_model_cards(db: Session) -> list[ModelCard]:
    models = db.scalars(
        select(WorkflowModel)
        .where(WorkflowModel.is_active.is_(True))
        .order_by(WorkflowModel.model_id.asc())
    ).all()
    now = int(time.time())
    return [
        ModelCard(
            id=model.model_id,
            created=now,
            metadata={
                "kind": model.kind,
                "workflow_id": model.workflow_id,
                "workflow_path": model.workflow_path,
                **model.metadata_json,
                **(
                    {"registry_keys": sorted(model.registry.keys())}
                    if model.registry
                    else {}
                ),
            },
        )
        for model in models
    ]


def get_model_or_none(db: Session, model_id: str) -> WorkflowModel | None:
    return db.scalar(
        select(WorkflowModel).where(
            WorkflowModel.model_id == model_id, WorkflowModel.is_active.is_(True)
        )
    )
