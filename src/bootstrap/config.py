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


class LLMDeploymentType(StrEnum):
    """Who runs the model server, which decides whether a token is required."""

    CLOUD = "cloud"
    SELF_HOSTED = "self_hosted"


class ReviewConfig(BaseModel):
    max_changed_lines_per_file: int = Field(default=800)
    max_changed_files: int = Field(default=50)
    modules: list[str] = Field(default_factory=list)
    # TODO: add parameter controlling whether to include business context


class LLMConfig(BaseModel):
    deployment_type: LLMDeploymentType = LLMDeploymentType.CLOUD
    model: str
    base_url: str | None = None

    @property
    def requires_token(self) -> bool:
        return self.deployment_type is LLMDeploymentType.CLOUD

    @model_validator(mode="after")
    def validate_config(self):
        if self.deployment_type == LLMDeploymentType.SELF_HOSTED:
            if not self.base_url:
                raise ValueError("base_url is required for self-hosted deployments")
        return self


class ThemisConfig(BaseModel):
    version: int
    test_mode: bool = Field(default=False)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    llm: LLMConfig

    @classmethod
    def from_yaml(cls, path: Path) -> "ThemisConfig":
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
