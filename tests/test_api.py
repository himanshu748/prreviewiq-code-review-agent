from fastapi.testclient import TestClient

from app.api import routes
from app.core.config import Settings
from app.main import app


def test_health_and_static_index_work_without_env_tokens(monkeypatch):
    monkeypatch.setattr(
        routes,
        "get_settings",
        lambda: Settings(
            _env_file=None,
            notion_token="",
            notion_parent_page_id="",
        ),
    )
    client = TestClient(app)

    health = client.get("/api/health")
    index = client.get("/")

    assert health.status_code == 200
    payload = health.json()
    assert payload["status"] == "ok"
    assert payload["notion_token"] is False
    assert payload["parent_page_id"] is False
    assert payload["notion_transport"] in {"mcp-stdio", "rest-fallback"}
    assert index.status_code == 200
    assert "PRReviewIQ" in index.text


def test_review_pr_rejects_oversized_diff_before_services_run():
    client = TestClient(app)

    response = client.post(
        "/api/review-pr",
        json={
            "diff": "x" * 120_001,
            "pr_title": "Demo",
            "repo": "demo",
        },
    )

    assert response.status_code == 422


def test_review_github_pr_rejects_oversized_url_before_services_run():
    client = TestClient(app)

    response = client.post("/api/review-github-pr", json={"pr_url": "x" * 301})

    assert response.status_code == 422
