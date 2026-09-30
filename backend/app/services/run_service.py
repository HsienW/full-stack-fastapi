import uuid

from sqlmodel import Session

from app.models import Run, RunCreate
from app.repositories import run_repository


def create_run(
    *,
    session: Session,
    run_in: RunCreate,
    owner_id: uuid.UUID,
) -> Run:
    return run_repository.create_run(
        session=session,
        run_in=run_in,
        owner_id=owner_id,
    )


def get_run_for_user(
    *,
    session: Session,
    run_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Run | None:
    run = run_repository.get_run_by_id(
        session=session,
        run_id=run_id,
    )

    if not run:
        return None

    if run.owner_id != user_id:
        return None

    return run
