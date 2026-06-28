from abc import ABC, abstractmethod

from src.review_engine.domain.models import DiffRefs, MergeRequest, ReviewComment


class GitLabPort(ABC):
    @abstractmethod
    def get_mr_data(self) -> MergeRequest:
        """Fetch merge request data including all file changes from GitLab API."""
        ...

    @abstractmethod
    def post_general_comment(self, comment: ReviewComment) -> None:
        """
        Post a comment as a general note on the merge request (no line anchor).
        """
        ...

    @abstractmethod
    def post_inline_comment(self, comment: ReviewComment, diff_refs: DiffRefs) -> None:
        """Post a comment inline at ``comment.anchor`` via the discussion position API.

        ``diff_refs`` provides the commit SHAs the position is resolved against.
        ``comment.anchor`` must be set.
        """
        ...

    @abstractmethod
    def get_file_content(self) -> str: ...
