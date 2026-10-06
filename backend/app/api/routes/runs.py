import uuid

from fastapi import APIRouter, HTTPException, status, Header, BackgroundTasks
from app.api.deps import CurrentUser, SessionDep
from app.models import RunCreate, RunPublic
from app.services import run_service, run_executor
from typing import Annotated


router = APIRouter(prefix="/runs", tags=["runs"])


@router.post(
    "",
    response_model=RunPublic,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_run(
    body: RunCreate,
    background_tasks: BackgroundTasks,
    session: SessionDep,
    current_user: CurrentUser,
):
    run = run_service.create_run(
        session=session,
        run_in=body,
        owner_id=current_user.id,
    )

    background_tasks.add_task(
        run_executor.execute_run,
        run.id,
    )

    return run


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
