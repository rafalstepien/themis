from pydantic import BaseModel


class FileDiff(BaseModel):
    """Represents a single file change in a merge request."""

    old_path: str
    new_path: str
    a_mode: str
    b_mode: str
    diff: str
    new_file: bool
    renamed_file: bool
    deleted_file: bool
    additions: int | None = None
    deletions: int | None = None


class MergeRequestData(BaseModel):
    """Represents complete merge request data from GitLab API."""

    mr_iid: int
    source_branch: str
    target_branch: str
    changes: list[FileDiff]
