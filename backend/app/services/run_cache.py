import uuid

from app.core.redis import redis_client


def delete_run_cache(
    *,
    owner_id: uuid.UUID,
    run_id: uuid.UUID,
) -> None:
    redis_client.delete(
        f"run:{owner_id}:{run_id}"
    )
