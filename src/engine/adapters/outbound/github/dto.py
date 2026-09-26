from typing import Literal

from pydantic import BaseModel, Field


class GitHubFileDiffDTO(BaseModel):
    """Represents a single file change in a GitHub pull request."""

    filename: str
    previous_filename: str | None = None
    status: Literal["added", "removed", "modified", "renamed", "copied", "changed", "unchanged"]
    patch: str | None = (
        None  # The actual diff, can be None for large files or renames without changes
    )


class GitHubCommitRefDTO(BaseModel):
    sha: str
    ref: str


class GitHubPullRequestDTO(BaseModel):
    """Represents pull request data from GitHub API."""

    number: int
    title: str
    body: str | None
    head: GitHubCommitRefDTO = Field(description="Source branch (feature) head")
    base: GitHubCommitRefDTO = Field(description="Target branch (main) base")
    # GitHub files are fetched via a separate endpoint, so we inject them into the DTO manually
    files: list[GitHubFileDiffDTO] = Field(default_factory=list)


class GitHubFileContentResponseDTO(BaseModel):
    """Represents file content fetched from GitHub."""

    content: str
    encoding: str


class GitHubUserDTO(BaseModel):
    id: int
    login: str
    name: str | None = None
    email: str | None = None
    type: str  # "User" or "Bot"


class GitHubCommentDTO(BaseModel):
    """Represents both general issue comments and PR review comments from GitHub."""

    id: int
    user: GitHubUserDTO
