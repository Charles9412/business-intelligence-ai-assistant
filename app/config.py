"""Configuration loading for local paths and LLM settings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables.

    TODO: Replace defaults with python-dotenv based loading and validation.
    """

    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "change-me"
    llm_model: str = "local-model-name"
    database_path: str = "data/business_data.sqlite"
    vector_store_path: str = "vector_store"


def load_settings() -> Settings:
    """Load application settings.

    TODO: Read `.env`, validate required values, and normalize filesystem paths.
    """
    return Settings()
