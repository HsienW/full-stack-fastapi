import asyncio
import uuid

from sqlmodel import Session
from app.core.db import engine
from app.repositories import run_repository
from app.services.run_cache import delete_run_cache


async def execute_run(run_id: uuid.UUID) -> None:
    with Session(engine) as session:
        run = run_repository.update_run_status(
            session=session,
            run_id=run_id,
            status="running",
        )

        if run:
            delete_run_cache(
                owner_id=run.owner_id,
                run_id=run.id,
            )

    try:
        await asyncio.sleep(5)

        with Session(engine) as session:
            run = run_repository.update_run_status(
                session=session,
                run_id=run_id,
                status="completed",
            )

            if run:
                delete_run_cache(
                    owner_id=run.owner_id,
                    run_id=run.id,
                )

    except Exception:
        with Session(engine) as session:
            run = run_repository.update_run_status(
                session=session,
                run_id=run_id,
                status="failed",
            )

            if run:
                delete_run_cache(
                    owner_id=run.owner_id,
                    run_id=run.id,
                )

        raise
