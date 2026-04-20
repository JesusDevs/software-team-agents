from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class Settings(BaseSettings):
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    langchain_api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")
    langchain_tracing_v2: str = Field(default="false", alias="LANGCHAIN_TRACING_V2")
    langchain_project: str = Field(default="software-team-agents", alias="LANGCHAIN_PROJECT")
    default_run_id: str = Field(default="default", alias="DEFAULT_RUN_ID")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    artifacts_dir: Path = ROOT_DIR / "artifacts"
    rag_dir: Path = ROOT_DIR / "rag" / ".chroma"

    class Config:
        env_file = ROOT_DIR / ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True

    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.startswith("sk-"))

    def has_openrouter_key(self) -> bool:
        return bool(self.openrouter_api_key and self.openrouter_api_key.startswith("sk-or-"))

    def active_provider(self) -> str:
        """Returns 'openai' or 'openrouter' based on available keys."""
        if self.has_openai_key():
            return "openai"
        if self.has_openrouter_key():
            return "openrouter"
        return "none"


settings = Settings()
