from enum import StrEnum
import logging
from pathlib import Path

from pydantic import BaseModel, Field, model_validator
import yaml

logger = logging.getLogger(__name__)

THEMIS_DIR = ".themis-ai"
DEFAULT_CONFIG_PATH = f"{THEMIS_DIR}/config.yaml"

RULES_SUBDIR = "rules"
RULES_FILENAME = "rule.json"
ARCHITECTURE_SUBDIR = "architecture"
ARCHITECTURE_FILENAME = "architecture.json"


def rule_file_path(module: str) -> str:
    return f"{THEMIS_DIR}/{RULES_SUBDIR}/{module}/{RULES_FILENAME}"


def architecture_file_path(module: str) -> str:
    return f"{THEMIS_DIR}/{ARCHITECTURE_SUBDIR}/{module}/{ARCHITECTURE_FILENAME}"


class LLMProvider(StrEnum):
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class ReviewConfig(BaseModel):
    max_file_chars: int = Field(default=60_000)
    max_changed_files: int = Field(default=50)
    modules: list[str] = Field(default_factory=list)


class LLMConfig(BaseModel):
    provider: LLMProvider
    model: str
    base_url: str | None = None

    @model_validator(mode="after")
    def _require_base_url_for_compatible(self) -> "LLMConfig":
        if self.provider is LLMProvider.OPENAI_COMPATIBLE and not self.base_url:
            raise ValueError("'base_url' is required when provider is 'openai_compatible'.")
        return self


class ThemisConfig(BaseModel):
    version: int
    test_mode: bool = Field(default=False)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    llm: LLMConfig

    @classmethod
    def from_yaml(cls, path: str | Path = DEFAULT_CONFIG_PATH) -> "ThemisConfig":
        with open(path, "r") as f:
            config = cls(**yaml.safe_load(f))
        if not config.review.modules:
            logger.warning(
                "No modules declared in config; per-module rules and "
                "architecture context cannot be loaded and reviews will not "
                "be module-scoped. Declare 'review.modules' in %s.",
                path,
            )
        return config
