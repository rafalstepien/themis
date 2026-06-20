from pathlib import Path
from typing import Self

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.bootstrap.exceptions import MissingEnvironmentError


class EnvSettings(BaseSettings):
    """Base for settings objects hydrated from the process environment.

    Subclasses declare their fields with ``Field(alias=...)`` naming the env
    var; mandatory fields omit a default, optional ones provide one. Reading
    and validating the environment is the model's own responsibility via
    :meth:`load`.
    """

    model_config = SettingsConfigDict(extra="ignore")

    @classmethod
    def load(cls) -> Self:
        """Build the model from the environment.

        Raises:
            MissingEnvironmentError: if any mandatory variable is unset.
        """
        try:
            return cls()
        except ValidationError as exc:
            missing = [
                str(alias)
                for error in exc.errors()
                if error["type"] == "missing"
                for alias in error["loc"]
            ]
            raise MissingEnvironmentError(missing) from exc


class Secrets(EnvSettings):
    """Sensitive tokens sourced from the process environment.

    Mandatory tokens (GitLab, LLM) have no default, so :meth:`load` fails if
    they are absent. Optional tokens (Jira) default to ``None`` when unset.
    """

    gitlab_token: str = Field(alias="GITLAB_API_TOKEN")
    llm_token: str = Field(alias="LLM_API_TOKEN")
    jira_token: str | None = Field(default=None, alias="JIRA_API_TOKEN")


class CIContext(EnvSettings):
    """Non-secret CI runtime context injected by the GitLab runner.

    These identify the merge request under review. They are mandatory: the
    review cannot run without knowing which project and MR it targets.

    ``project_dir`` is the root of the checked-out repo under review and the
    anchor for every consumer-repo read (``.themis-ai/`` config, rules,
    architecture). GitLab sets ``CI_PROJECT_DIR`` to the clone path; locally it
    defaults to the current working directory so the same code path is exercised.
    """

    project_id: str = Field(alias="CI_PROJECT_ID")
    mr_iid: int = Field(alias="CI_MERGE_REQUEST_IID")
    project_dir: Path = Field(default=Path("."), alias="CI_PROJECT_DIR")
