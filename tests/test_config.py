from app.core.config import Settings


def test_settings_can_load_without_secrets(monkeypatch):
    monkeypatch.delenv("HF_API_KEY", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("NOTION_PARENT_PAGE_ID", raising=False)

    settings = Settings(_env_file=None)

    assert settings.hf_api_key == ""
    assert settings.notion_token == ""
    assert settings.notion_parent_page_id == ""
