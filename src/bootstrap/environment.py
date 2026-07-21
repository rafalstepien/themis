from pathlib import Path
from typing import Self

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.bootstrap.exceptions import MissingEnvironmentError

LLM_TOKEN_ENV_VAR = "LLM_API_TOKEN"


class _EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    @classmethod
    def load(cls) -> Self:
        try:
            return cls()
        except ValidationError as exc:
            missing = [
                str(location)
                for error in exc.errors()
                if error["type"] == "missing"
                for location in error["loc"]
            ]
            raise MissingEnvironmentError(missing) from exc


class CISecrets(_EnvSettings):
    """
    Secret tokens sourced from the runner environment.

    GITLAB_API_TOKEN is only one required for the review to run.
    LLM_API_TOKEN is optional, because a keyless self-hosted backend needs no credential
    """

    gitlab_token: str = Field(alias="GITLAB_API_TOKEN")
    llm_token: str | None = Field(default=None, alias=LLM_TOKEN_ENV_VAR)
    jira_token: str | None = Field(default=None, alias="JIRA_API_TOKEN")


class CIContext(_EnvSettings):
    """
    Non-secret CI runtime context injected by the GitLab runner.
    All of them are required.
    """

    project_id: str = Field(alias="CI_PROJECT_ID")
    mr_iid: int = Field(alias="CI_MERGE_REQUEST_IID")
    project_dir: Path = Field(default=Path("."), alias="CI_PROJECT_DIR")
