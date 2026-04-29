"""Configuration loading for local paths and LLM settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_LLM_BASE_URL = "http://localhost:1234/v1"
DEFAULT_LLM_API_KEY = "lm-studio"
DEFAULT_LLM_MODEL = "openai/gpt-oss-20b"
DEFAULT_DATABASE_PATH = "data/business_data.sqlite"
DEFAULT_VECTOR_STORE_PATH = "vector_store"


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the local-first assistant.

    The lowercase attributes are convenient for Python code. Uppercase
    properties are provided for callers that prefer environment-style names.
    """

    llm_base_url: str = DEFAULT_LLM_BASE_URL
    llm_api_key: str = DEFAULT_LLM_API_KEY
    llm_model: str = DEFAULT_LLM_MODEL
    database_path: str = DEFAULT_DATABASE_PATH
    vector_store_path: str = DEFAULT_VECTOR_STORE_PATH

    @property
    def LLM_BASE_URL(self) -> str:
        """OpenAI-compatible API base URL."""
        return self.llm_base_url

    @property
    def LLM_API_KEY(self) -> str:
        """API key used by the OpenAI-compatible local server."""
        return self.llm_api_key

    @property
    def LLM_MODEL(self) -> str:
        """Model identifier loaded by the local LLM server."""
        return self.llm_model

    @property
    def DATABASE_PATH(self) -> str:
        """Path to the local SQLite database."""
        return self.database_path

    @property
    def VECTOR_STORE_PATH(self) -> str:
        """Path to the local vector store directory."""
        return self.vector_store_path


def _env_value(name: str, default: str) -> str:
    """Read an environment variable and fall back when it is blank."""
    value = os.getenv(name, default).strip()
    return value or default


def load_settings(env_file: str | Path | None = None) -> Settings:
    """Load settings from `.env` and process environment variables.

    Secrets are loaded into memory but never printed or logged by this module.
    """
    dotenv_path = Path(env_file) if env_file is not None else PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=False)

    return Settings(
        llm_base_url=_env_value("LLM_BASE_URL", DEFAULT_LLM_BASE_URL),
        llm_api_key=_env_value("LLM_API_KEY", DEFAULT_LLM_API_KEY),
        llm_model=_env_value("LLM_MODEL", DEFAULT_LLM_MODEL),
        database_path=_env_value("DATABASE_PATH", DEFAULT_DATABASE_PATH),
        vector_store_path=_env_value("VECTOR_STORE_PATH", DEFAULT_VECTOR_STORE_PATH),
    )
