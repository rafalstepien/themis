import logging

import httpx

from src.review_engine.ports.outbound import GitLabPort, MergeRequestData, FileDiff

logger = logging.getLogger(__name__)


class GitLabClient(GitLabPort):
    def __init__(self, token: str, api_base: str):
        self.token = token
        self.api_base = api_base
        self.headers = {"PRIVATE-TOKEN": self.token}

    def get_mr_data(self, project_id: int | str, mr_iid: int) -> MergeRequestData:
        """Fetch merge request data including all file changes from GitLab API."""
        mr_details = self._get_mr_details(project_id, mr_iid)
        mr_changes = self._get_mr_changes(project_id, mr_iid)

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

        return MergeRequestData(
            mr_iid=mr_iid,
            source_branch=mr_details["source_branch"],
            target_branch=mr_details["target_branch"],
            changes=changes,
        )

    def _get_mr_details(self, project_id: int | str, mr_iid: int) -> dict:
        """Fetch merge request details from GitLab API."""
        url = f"{self.api_base}/projects/{project_id}/merge_requests/{mr_iid}"
        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def _get_mr_changes(self, project_id: int | str, mr_iid: int) -> list[dict]:
        """Fetch all file changes for a merge request from GitLab API."""
        url = f"{self.api_base}/projects/{project_id}/merge_requests/{mr_iid}/changes"
        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get("changes", [])

    def post_comment(self): ...

    def get_file_content(self) -> str: ...
