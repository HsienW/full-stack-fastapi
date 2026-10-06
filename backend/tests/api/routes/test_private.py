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
