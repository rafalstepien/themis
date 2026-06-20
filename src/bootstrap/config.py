from enum import StrEnum
import logging
from pathlib import Path

from pydantic import BaseModel, Field
import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = ".themis-ai/config.yaml"


class LLMProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class ReviewConfig(BaseModel):
    max_file_chars: int = Field(default=60_000)
    max_changed_files: int = Field(default=50)
    modules: list[str] = Field(default_factory=list)


class LLMConfig(BaseModel):
    provider: LLMProvider
    model: str


class Config(BaseModel):
    version: int
    test_mode: bool = Field(default=False)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    llm: LLMConfig

    @classmethod
    def from_yaml(cls, path: str | Path = DEFAULT_CONFIG_PATH) -> "Config":
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
