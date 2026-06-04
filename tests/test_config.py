from app.core.config import Settings


def test_settings_can_load_without_secrets(monkeypatch):
    monkeypatch.delenv("HF_API_KEY", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    monkeypatch.delenv("NOTION_PARENT_PAGE_ID", raising=False)

    settings = Settings(_env_file=None)

    assert settings.hf_api_key == ""
    assert settings.notion_token == ""
    assert settings.notion_parent_page_id == ""


def test_settings_accept_notion_api_key_alias(monkeypatch):
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.setenv("NOTION_API_KEY", "  ntn_test  ")

    settings = Settings(_env_file=None)

    assert settings.notion_token == "ntn_test"


def test_settings_fall_back_to_hf_token_when_primary_is_blank(monkeypatch):
    monkeypatch.setenv("HF_API_KEY", "  ")
    monkeypatch.setenv("HF_TOKEN", "hf_test")

    settings = Settings(_env_file=None)

    assert settings.hf_api_key == "hf_test"


def test_settings_fall_back_to_notion_api_key_when_primary_is_blank(monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "\t")
    monkeypatch.setenv("NOTION_API_KEY", "ntn_test")

    settings = Settings(_env_file=None)

    assert settings.notion_token == "ntn_test"


def test_settings_treat_blank_required_env_as_missing(monkeypatch):
    monkeypatch.setenv("HF_API_KEY", "  ")
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("NOTION_TOKEN", "\t")
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    monkeypatch.setenv("NOTION_PARENT_PAGE_ID", "")
    monkeypatch.setenv("GITHUB_TOKEN", " ")

    settings = Settings(_env_file=None)

    assert settings.hf_api_key == ""
    assert settings.notion_token == ""
    assert settings.notion_parent_page_id == ""
    assert settings.github_token == ""
