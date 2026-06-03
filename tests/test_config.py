from app.core.config import Settings


def test_settings_can_load_without_secrets():
    settings = Settings(_env_file=None)

    assert settings.hf_api_key == ""
    assert settings.notion_token == ""
    assert settings.notion_parent_page_id == ""
