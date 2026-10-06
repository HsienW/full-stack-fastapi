import uuid

from sqlmodel import Session

from app.core.redis import redis_client
from app.models import Run, RunCreate, RunPublic
from app.repositories import run_repository


RUN_CACHE_TTL_SECONDS = 60


def create_run(
    *,
    session: Session,
    run_in: RunCreate,
    owner_id: uuid.UUID,
    idempotency_key: str | None = None,
) -> Run:
    if idempotency_key:
        existing_run = (
            run_repository.get_run_by_idempotency_key(
                session=session,
                owner_id=owner_id,
                idempotency_key=idempotency_key,
            )
        )

        if existing_run:
            return existing_run

    return run_repository.create_run(
        session=session,
        run_in=run_in,
        owner_id=owner_id,
        idempotency_key=idempotency_key,
    )


def get_run_for_user(
    *,
    session: Session,
    run_id: uuid.UUID,
    user_id: uuid.UUID,
) -> RunPublic | None:
    cache_key = f"run:{user_id}:{run_id}"

    cached = redis_client.get(cache_key)

    if cached:
        return RunPublic.model_validate_json(cached)

    run = run_repository.get_run_by_id(
        session=session,
        run_id=run_id,
    )

    if not run:
        return None

    if run.owner_id != user_id:
        return None

    result = RunPublic.model_validate(run)

    redis_client.set(
        cache_key,
        result.model_dump_json(),
        ex=RUN_CACHE_TTL_SECONDS,
    )

    return result

def delete_run_cache(
    *,
    owner_id: uuid.UUID,
    run_id: uuid.UUID,
) -> None:
    redis_client.delete(
        f"run:{owner_id}:{run_id}"
    )
