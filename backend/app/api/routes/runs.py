import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionDep, CurrentUser
from app.models import Run, RunCreate, RunPublic

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
) -> Run:
    db_run = Run.model_validate(
         body,
         update={"owner_id": current_user.id},
    )

    session.add(db_run)
    session.commit()
    session.refresh(db_run)

    return db_run


@router.get(
    "/{run_id}",
    response_model=RunPublic,
)
def get_run(
    run_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Run:
    run = session.get(Run, run_id)

    if not run or run.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    return run
