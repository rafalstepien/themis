from abc import ABC, abstractmethod

from src.engine.domain.models import (
    DiffRefs,
    MergeRequest,
    MRComments,
    ReviewComment,
    TokenOwner,
)


class GitProviderPortError(Exception):
    """Part of the GitProviderPort contract — raised when any git provider interaction fails."""


class GitProviderPort(ABC):
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

    @abstractmethod
    def get_mr_comments(self) -> MRComments: ...

    @abstractmethod
    def get_token_owner_details(self) -> TokenOwner: ...
