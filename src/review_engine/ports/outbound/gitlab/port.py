from abc import ABC, abstractmethod

from .models import MergeRequestData


class GitLabPort(ABC):
    @abstractmethod
    def get_mr_data(self, project_id: int | str, mr_iid: int) -> MergeRequestData:
        """Fetch merge request data including all file changes from GitLab API."""
        ...

    @abstractmethod
    def post_comment(self): ...

    @abstractmethod
    def get_file_content(self) -> str: ...
