from abc import ABC, abstractmethod

from src.review_engine.domain.models import MergeRequest, ReviewComment


class GitLabPort(ABC):
    @abstractmethod
    def get_mr_data(self) -> MergeRequest:
        """Fetch merge request data including all file changes from GitLab API."""
        ...

    @abstractmethod
    def post_comment(self, comment: ReviewComment) -> None: ...

    @abstractmethod
    def get_file_content(self) -> str: ...
