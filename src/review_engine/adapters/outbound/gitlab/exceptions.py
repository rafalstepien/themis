from contextlib import contextmanager

import httpx
import pydantic

from src.review_engine.ports.outbound.gitlab.exceptions import GitLabPortError


class GitLabError(GitLabPortError):
    """Base for all GitLab adapter errors."""


class GitLabAPIError(GitLabError):
    """
    Raised when there is a problem fetching data from GitLab.
    """

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GitLabDataError(GitLabError):
    """
    Raised when GitLab responds with undexpected payload.
    """

    def __init__(self, message: str):
        super().__init__(message)


@contextmanager
def handle_gitlab_api_errors(mr_id: int):
    try:
        yield
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        raise GitLabAPIError(
            f"GitLab returned HTTP {status_code} for MR {mr_id}", status_code=status_code
        ) from e
    except httpx.RequestError as e:
        raise GitLabAPIError("Could not reach GitLab") from e


@contextmanager
def handle_gitlab_data_errors():
    try:
        yield
    except pydantic.ValidationError as e:
        raise GitLabDataError(
            "GitLab responded with unexpected format. Could not create a DTO."
        ) from e
