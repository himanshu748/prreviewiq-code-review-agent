import os
from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    hf_api_key: str = Field(
        "",
        validation_alias=AliasChoices("HF_API_KEY", "HF_TOKEN"),
    )
    hf_model: str = Field("Qwen/Qwen2.5-72B-Instruct", alias="HF_MODEL")
    notion_token: str = Field(
        "",
        validation_alias=AliasChoices("NOTION_TOKEN", "NOTION_API_KEY"),
    )
    notion_parent_page_id: str = Field("", alias="NOTION_PARENT_PAGE_ID")
    github_token: str = Field("", alias="GITHUB_TOKEN")
    notion_mcp_command: str = "npx"
    notion_mcp_package: str = "@notionhq/notion-mcp-server"
    github_mcp_package: str = "@modelcontextprotocol/server-github"
    notion_mcp_startup_timeout_seconds: float = 45.0
    notion_mcp_protocol_version: str = "2025-06-18"
    state_file: str = ".prreviewiq/state.json"

    @field_validator(
        "hf_api_key",
        "hf_model",
        "notion_token",
        "notion_parent_page_id",
        "github_token",
        "notion_mcp_command",
        "notion_mcp_package",
        "github_mcp_package",
        "notion_mcp_protocol_version",
        "state_file",
        mode="before",
    )
    @classmethod
    def strip_string_values(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def apply_blank_primary_alias_fallbacks(self) -> "Settings":
        if not self.hf_api_key:
            self.hf_api_key = os.getenv("HF_TOKEN", "").strip()
        if not self.notion_token:
            self.notion_token = os.getenv("NOTION_API_KEY", "").strip()
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
