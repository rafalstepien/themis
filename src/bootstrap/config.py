from enum import StrEnum

from pydantic import BaseModel, Field
import yaml

DEFAULT_CONFIG_PATH = ".themis-ai/config.yaml"


class LLMProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class ReviewConfig(BaseModel):
    max_file_chars: int = Field(default=60_000)
    max_changed_files: int = Field(default=50)


class LLMConfig(BaseModel):
    provider: LLMProvider
    model: str


class Config(BaseModel):
    version: int
    test_mode: bool = Field(default=False)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    llm: LLMConfig

    @classmethod
    def from_yaml(cls, path: str = DEFAULT_CONFIG_PATH) -> "Config":
        with open(path, "r") as f:
            return cls(**yaml.safe_load(f))
