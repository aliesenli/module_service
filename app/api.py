from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import repository
from app.database import get_db
from app.models import Module
from app.schemas import (
    ErrorResponse,
    ModuleCreate,
    ModuleResponse,
    ModuleUpdate,
)

router = APIRouter(prefix="/api/v1/modules", tags=["modules"])
DbSession = Annotated[Session, Depends(get_db)]


def _find_or_404(db: Session, module_id: UUID) -> Module:
    module = repository.get_module(db, module_id)
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MODULE_NOT_FOUND", "message": f"Module {module_id} was not found"},
        )
    return module


@router.post(
    "",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def create_module(payload: ModuleCreate, db: DbSession) -> Module:
    try:
        return repository.create_module(db, payload)
    except repository.DuplicateModuleCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "MODULE_CODE_EXISTS", "message": "Module code already exists"},
        ) from exc


@router.get("", response_model=list[ModuleResponse])
def retrieve_modules(db: DbSession) -> list[Module]:
    return repository.list_modules(db)


@router.get(
    "/{module_id}", response_model=ModuleResponse, responses={404: {"model": ErrorResponse}}
)
def retrieve_module(module_id: UUID, db: DbSession) -> Module:
    return _find_or_404(db, module_id)


@router.patch(
    "/{module_id}",
    response_model=ModuleResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_module(module_id: UUID, payload: ModuleUpdate, db: DbSession) -> Module:
    module = _find_or_404(db, module_id)
    try:
        return repository.update_module(db, module, payload)
    except repository.DuplicateModuleCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "MODULE_CODE_EXISTS", "message": "Module code already exists"},
        ) from exc


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_module(module_id: UUID, db: DbSession) -> Response:
    repository.delete_module(db, _find_or_404(db, module_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)