from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "SimpleAgentChatTemplate API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/simple_agent_chat"
    )

    workflow_root: str = str((Path(__file__).resolve().parents[2] / "workflows"))
    workflow_starter_file: str = "email-chat-draft-or-clarify.yaml"
    workflow_orchestrator_file: str = "email-chat-orchestrator-with-subgraph-tool.yaml"
    workflow_subgraph_file: str = "hr-warning-email-subgraph.yaml"

    model_prefix: str = "yaml"
    default_chat_title: str = "New Conversation"

    provider: str = "openai"
    custom_api_base: str | None = None
    custom_api_key: str | None = None

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:5178"]
    )

    @property
    def workflow_root_path(self) -> Path:
        return Path(self.workflow_root).resolve()


settings = Settings()
