import uuid

from sqlmodel import Session

from app.models import Run, RunCreate


def create_run(
    *,
    session: Session,
    run_in: RunCreate,
    owner_id: uuid.UUID,
) -> Run:
    db_run = Run.model_validate(
        run_in,
        update={"owner_id": owner_id},
    )

    session.add(db_run)
    session.commit()
    session.refresh(db_run)

    return db_run


def get_run_by_id(
    *,
    session: Session,
    run_id: uuid.UUID,
) -> Run | None:
    return session.get(Run, run_id)
