import logging

import httpx

from src.review_engine.domain.models import MergeRequest
from src.review_engine.ports.outbound import GitLabPort

from .mappers import to_domain
from .models import FileDiff, MergeRequestDTO

logger = logging.getLogger(__name__)


class GitLabClient(GitLabPort):
    def __init__(self, token: str, project_id: str, mr_iid: int, api_base: str):
        self.token = token
        self.project_id = project_id
        self.mr_iid = mr_iid
        self.api_base = api_base
        self.headers = {"PRIVATE-TOKEN": self.token}

    def get_mr_data(self) -> MergeRequest:
        """
        Fetch merge request data including all file changes from GitLab API
        and return domain object.
        """
        mr_details = self._get_mr_details()
        mr_changes = self._get_mr_changes()

        changes = [
            FileDiff(
                old_path=change["old_path"],
                new_path=change["new_path"],
                a_mode=change["a_mode"],
                b_mode=change["b_mode"],
                diff=change["diff"],
                new_file=change["new_file"],
                renamed_file=change["renamed_file"],
                deleted_file=change["deleted_file"],
                additions=change.get("additions"),
                deletions=change.get("deletions"),
            )
            for change in mr_changes
        ]

        mr_dto = MergeRequestDTO(
            mr_iid=self.mr_iid,
            source_branch=mr_details["source_branch"],
            target_branch=mr_details["target_branch"],
            changes=changes,
        )

        return to_domain(mr_dto)

    def _get_mr_details(self) -> dict:
        """Fetch merge request details from GitLab API."""
        url = f"{self.api_base}/projects/{self.project_id}/merge_requests/{self.mr_iid}"
        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def _get_mr_changes(self) -> list[dict]:
        """Fetch all file changes for a merge request from GitLab API."""
        url = f"{self.api_base}/projects/{self.project_id}/merge_requests/{self.mr_iid}/changes"
        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get("changes", [])

    def post_comment(self) -> None: ...

    def get_file_content(self) -> str: ...
