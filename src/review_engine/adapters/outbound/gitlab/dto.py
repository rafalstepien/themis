from pydantic import BaseModel, Field


class FileDiffDTO(BaseModel):
    """Represents a single file change in a merge request."""

    new_path: str
    old_path: str
    diff: str
    new_file: bool
    renamed_file: bool
    deleted_file: bool


class FileContents(BaseModel):
    old: str | None = None
    new: str | None = None


class DiffRefsDTO(BaseModel):
    """
    Identifies a specific merge request diff version: the three commit SHAs
    that pin down what was diffed against what, and when. Used to compute
    the diff content itself, detect target-branch drift, and resolve inline
    comment positions across diff versions.

    For visualization see docs/commit-sha.md
    """

    base_sha: str = Field(
        description="Last common commit of source and target. Changes only during rebase."
    )
    start_sha: str = Field(
        description="Snapshot of target (main) branch's HEAD at the moment of diff generation"
    )
    head_sha: str = Field(
        description="Head of the source (feature) branch at the moment of diff generation"
    )


class MergeRequestDTO(BaseModel):
    """Represents complete merge request data from GitLab API."""

    iid: int = Field(description="Merge request id within the project")
    project_id: int = Field(description="ID of a project where MR sits")
    title: str = Field(description="Merge request title")
    description: str = Field(description="Merge request description")
    source_branch: str = Field(description="Branch that introduces the change")
    target_branch: str = Field(description="Target, usually main")
    changes: list[FileDiffDTO]
    diff_refs: DiffRefsDTO | None = None


class GitLabFileResponse(BaseModel):
    content: str
    encoding: str
