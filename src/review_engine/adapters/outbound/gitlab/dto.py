from pydantic import BaseModel


class FileDiffDTO(BaseModel):
    """Represents a single file change in a merge request."""

    new_path: str
    old_path: str
    diff: str
    new_file: bool
    renamed_file: bool
    deleted_file: bool
    old_content: str | None = None
    new_content: str | None = None

    def enrich_with_content(self, old_content: str, new_content: str) -> None:
        self.new_content = new_content
        self.old_content = old_content


class DiffRefsDTO(BaseModel):
    """The commit SHAs GitLab resolves an inline comment's position against."""

    base_sha: str
    start_sha: str
    head_sha: str


class MergeRequestDTO(BaseModel):
    """Represents complete merge request data from GitLab API."""

    id: int
    iid: int
    project_id: int
    title: str
    description: str
    source_branch: str
    target_branch: str
    changes: list[FileDiffDTO]
    diff_refs: DiffRefsDTO | None = None


class GitLabFileResponse(BaseModel):
    content: str
    encoding: str
