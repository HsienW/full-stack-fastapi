import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.models import RunCreate, RunPublic
from app.services import run_service

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post(
    "",
    response_model=RunPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_run(
    body: RunCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    return run_service.create_run(
        session=session,
        run_in=body,
        owner_id=current_user.id,
    )


@router.get(
    "/{run_id}",
    response_model=RunPublic,
)
def get_run(
    run_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
):
    run = run_service.get_run_for_user(
        session=session,
        run_id=run_id,
        user_id=current_user.id,
    )

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    return run
