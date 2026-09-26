from contextlib import contextmanager

import httpx
import pydantic

from src.engine.ports.outbound.git_provider_port import GitProviderPortError


class GitHubError(GitProviderPortError):
    """Base for all GitHub adapter errors."""


class GitHubAPIError(GitHubError):
    """Raised when there is a problem fetching data from GitHub."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GitHubDataError(GitHubError):
    """Raised when GitHub responds with an unexpected payload."""


@contextmanager
def handle_github_api_errors(pull_number: int):
    try:
        yield
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        try:
            # GitHub usually returns errors in a JSON payload with a "message" field
            error_data = e.response.json()
            detail = error_data.get("message", e.response.text.strip()[:500])
        except ValueError:
            detail = e.response.text.strip()[:500]

        message = f"GitHub returned HTTP {status_code} for PR {pull_number}"
        if detail:
            message = f"{message}: {detail}"
        raise GitHubAPIError(message, status_code=status_code) from e
    except httpx.RequestError as e:
        raise GitHubAPIError("Could not reach GitHub") from e


@contextmanager
def handle_github_data_errors():
    try:
        yield
    except pydantic.ValidationError as e:
        raise GitHubDataError(
            "GitHub responded with unexpected format. Could not create a DTO."
        ) from e
