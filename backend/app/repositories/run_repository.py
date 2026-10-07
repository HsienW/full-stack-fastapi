import uuid

from sqlmodel import Session, select
from app.models import Run, RunCreate
from sqlalchemy.exc import IntegrityError


def create_run(
    *,
    session: Session,
    run_in: RunCreate,
    owner_id: uuid.UUID,
    idempotency_key: str | None = None,
) -> tuple[Run, bool]:
    db_run = Run.model_validate(
        run_in,
        update={
            "owner_id": owner_id,
            "idempotency_key": idempotency_key,
        },
    )

    session.add(db_run)

    try:
        session.commit()

    except IntegrityError:
        session.rollback()

        if idempotency_key:
            existing_run = get_run_by_idempotency_key(
                session=session,
                owner_id=owner_id,
                idempotency_key=idempotency_key,
            )

            if existing_run:
                return existing_run, False

        raise

    session.refresh(db_run)

    return db_run, True


def get_run_by_id(
    *,
    session: Session,
    run_id: uuid.UUID,
) -> Run | None:
    return session.get(Run, run_id)


def get_run_by_idempotency_key(
    *,
    session: Session,
    owner_id: uuid.UUID,
    idempotency_key: str,
) -> Run | None:
    statement = select(Run).where(
        Run.owner_id == owner_id,
        Run.idempotency_key == idempotency_key,
    )

    return session.exec(statement).first()


def update_run_status(
    *,
    session: Session,
    run_id: uuid.UUID,
    status: str,
) -> Run | None:
    run = session.get(Run, run_id)

    if not run:
        return None

    run.status = status

    session.add(run)
    session.commit()
    session.refresh(run)

    return run
