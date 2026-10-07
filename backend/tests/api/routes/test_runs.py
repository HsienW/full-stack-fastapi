import uuid
import pytest

from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models import Run
from app.repositories import run_repository

@pytest.fixture(autouse=True)
def mock_run_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_execute_run(run_id: uuid.UUID) -> None:
        return None

    monkeypatch.setattr(
        "app.services.run_executor.execute_run",
        fake_execute_run,
    )


def test_run_status_transitions(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    response = client.post(
        "/api/v1/runs",
        headers=superuser_token_headers,
        json={
            "agent_id": "lifecycle-agent",
            "session_id": "lifecycle-session",
            "input": "lifecycle regression test",
        },
    )

    assert response.status_code == 202

    run_id = uuid.UUID(response.json()["id"])

    running_run = run_repository.update_run_status(
        session=db,
        run_id=run_id,
        status="running",
    )

    assert running_run is not None
    assert running_run.status == "running"

    completed_run = run_repository.update_run_status(
        session=db,
        run_id=run_id,
        status="completed",
    )

    assert completed_run is not None
    assert completed_run.status == "completed"


def test_create_run(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/runs",
        headers=superuser_token_headers,
        json={
            "agent_id": "test-agent",
            "session_id": "test-session",
            "input": "hello from pytest",
        },
    )

    assert response.status_code == 202

    data = response.json()

    assert data["agent_id"] == "test-agent"
    assert data["session_id"] == "test-session"
    assert data["input"] == "hello from pytest"
    assert data["id"]
    assert data["status"] in {
        "queued",
        "running",
        "completed",
    }


def test_get_run(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    create_response = client.post(
        "/api/v1/runs",
        headers=superuser_token_headers,
        json={
            "agent_id": "test-agent",
            "session_id": "test-session",
            "input": "get run test",
        },
    )

    assert create_response.status_code == 202

    run_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/runs/{run_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == run_id
    assert data["agent_id"] == "test-agent"


def test_get_nonexistent_run(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    run_id = uuid.uuid4()

    response = client.get(
        f"/api/v1/runs/{run_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Run not found"


def test_get_run_with_invalid_uuid(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/v1/runs/not-a-uuid",
        headers=superuser_token_headers,
    )

    assert response.status_code == 422


def test_create_run_without_auth(
     client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/runs",
        json={
            "agent_id": "test-agent",
            "session_id": "test-session",
            "input": "unauthorized run",
        },
    )

    assert response.status_code == 401


def test_create_run_persists_to_db(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    response = client.post(
        "/api/v1/runs",
        headers=superuser_token_headers,
        json={
            "agent_id": "db-test-agent",
            "session_id": "db-test-session",
            "input": "database regression test",
        },
    )

    assert response.status_code == 202

    run_id = uuid.UUID(response.json()["id"])

    run = db.get(Run, run_id)

    assert run is not None
    assert run.id == run_id
    assert run.agent_id == "db-test-agent"
    assert run.session_id == "db-test-session"
    assert run.owner_id is not None


def test_cannot_get_another_users_run(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    create_response = client.post(
        "/api/v1/runs",
        headers=superuser_token_headers,
        json={
            "agent_id": "ownership-agent",
            "session_id": "ownership-session",
            "input": "ownership regression test",
        },
    )

    assert create_response.status_code == 202

    run_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/runs/{run_id}",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 404


def test_create_run_with_same_idempotency_key_returns_same_run(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed_run_ids: list[uuid.UUID] = []

    async def fake_execute_run(run_id: uuid.UUID) -> None:
        executed_run_ids.append(run_id)

    monkeypatch.setattr(
        "app.services.run_executor.execute_run",
        fake_execute_run,
    )

    payload = {
        "agent_id": "idempotency-agent",
        "session_id": "idempotency-session",
        "input": "idempotency regression test",
    }

    idempotency_key = f"pytest-{uuid.uuid4()}"

    headers = {
        **superuser_token_headers,
        "Idempotency-Key": idempotency_key,
    }

    first_response = client.post(
        "/api/v1/runs",
        headers=headers,
        json=payload,
    )

    second_response = client.post(
        "/api/v1/runs",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 202
    assert second_response.status_code == 202

    first_run = first_response.json()
    second_run = second_response.json()

    assert first_run["id"] == second_run["id"]

    assert len(executed_run_ids) == 1
    assert str(executed_run_ids[0]) == first_run["id"]
