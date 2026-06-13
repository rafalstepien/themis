import base64
import logging
from urllib.parse import quote

import httpx

from src.review_engine.domain.models import MergeRequest
from src.review_engine.ports.outbound import GitLabPort

from .mappers import to_domain
from .models import (
    GitLabFileResponse,
    MergeRequestDTO,
)

logger = logging.getLogger(__name__)


class GitLabClient(GitLabPort):
    BASE_API_URL = "https://gitlab.com/api/v4"

    def __init__(self, token: str, project_id: str, mr_iid: int):
        self.project_id = project_id
        self.mr_iid = mr_iid
        self.headers = {"PRIVATE-TOKEN": token}

    def get_mr_data(self) -> MergeRequest:
        """
        Fetch merge request data including all file changes from GitLab API
        and return domain object.
        """
        mr_data = self._get_mr_data()

        for change in mr_data.changes:
            old_content = self._get_branch_file_content(change.old_path, mr_data.target_branch)
            new_content = self._get_branch_file_content(change.new_path, mr_data.source_branch)
            change.enrich_with_content(old_content, new_content)

        return to_domain(mr_data)

    def _get_mr_data(self) -> MergeRequestDTO:
        """Fetch all file changes for a merge request from GitLab API."""
        url = f"{self.BASE_API_URL}/projects/{self.project_id}/merge_requests/{self.mr_iid}/changes"
        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()
        return MergeRequestDTO(**response.json())

    def _get_branch_file_content(self, file_path: str, branch: str) -> str:
        """Fetch raw file content from a specific branch, decoding base64. Returns empty string for missing files."""
        encoded_path = quote(file_path, safe="")
        url = f"{self.BASE_API_URL}/projects/{self.project_id}/repository/files/{encoded_path}"
        response = httpx.get(url, headers=self.headers, params={"ref": branch})
        if response.status_code == 404:
            return ""
        response.raise_for_status()
        data = GitLabFileResponse(**response.json())
        if data.encoding == "base64":
            return base64.b64decode(data.content).decode("utf-8")
        return data.content

    def post_comment(self) -> None: ...

    def get_file_content(self) -> str:
        return ""
