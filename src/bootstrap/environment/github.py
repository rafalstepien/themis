from pathlib import Path

from pydantic import Field

from src.bootstrap.environment.common import LLM_TOKEN_ENV_VAR, _EnvSettings


class GitHubSettings(_EnvSettings):
    github_api_token: str = Field(alias="GITHUB_API_TOKEN")
    llm_api_token: str = Field(alias=LLM_TOKEN_ENV_VAR)
    pull_request_id: int = Field(alias="PULL_REQUEST_ID")
    settings_dir_path: Path = Field(alias="SETTINGS_DIR_PATH")
    owner: str = Field(alias="OWNER")
    repo: str = Field(alias="REPO")
