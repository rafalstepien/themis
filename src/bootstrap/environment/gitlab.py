from pathlib import Path

from pydantic import Field

from src.bootstrap.environment.common import LLM_TOKEN_ENV_VAR, _EnvSettings


class GitLabCISecrets(_EnvSettings):
    """
    Secret tokens sourced from the runner environment.

    GITLAB_API_TOKEN is only one required for the review to run.
    LLM_API_TOKEN is optional, because a keyless self-hosted backend needs no credential
    """

    gitlab_api_token: str = Field(alias="GITLAB_API_TOKEN")
    llm_token: str | None = Field(default=None, alias=LLM_TOKEN_ENV_VAR)
    jira_token: str | None = Field(default=None, alias="JIRA_API_TOKEN")


class GitLabCIContext(_EnvSettings):
    """
    Non-secret CI runtime context injected by the GitLab runner.
    All of them are required.
    """

    project_id: str = Field(alias="CI_PROJECT_ID")
    mr_iid: int = Field(alias="CI_MERGE_REQUEST_IID")
    project_dir: Path = Field(default=Path("."), alias="CI_PROJECT_DIR")
