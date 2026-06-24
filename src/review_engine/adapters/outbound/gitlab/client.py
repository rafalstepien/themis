import base64
import logging
from urllib.parse import quote

import httpx

from src.review_engine.domain.models import MergeRequest, ReviewComment
from src.review_engine.ports.outbound import GitLabPort

from .dto import (
    GitLabFileResponse,
    MergeRequestDTO,
)
from .exceptions import handle_gitlab_api_errors, handle_gitlab_data_errors
from .mappers import to_domain

logger = logging.getLogger(__name__)


class GitLabClient(GitLabPort):
    BASE_API_URL = "https://gitlab.com/api/v4"

    def __init__(self, token: str, project_id: str, mr_iid: int):
        self.project_id = project_id
        self.mr_iid = mr_iid
        self.headers = {"PRIVATE-TOKEN": token}

    def get_mr_data(self) -> MergeRequest:
        """
        First fetch merge request data.
        Then update the DTO with the file versions from both branches
        (couldn't do it in single request)
        """
        mr_data = self._get_mr_data()

        # TODO: Use asyncio.gather to paralellize
        for change in mr_data.changes:
            old_content = self._get_branch_file_content(change.old_path, mr_data.target_branch)
            new_content = self._get_branch_file_content(change.new_path, mr_data.source_branch)
            change.enrich_with_content(old_content, new_content)

        return to_domain(mr_data)

    def _get_mr_data(self) -> MergeRequestDTO:
        """Fetch all file changes for a merge request from GitLab API."""
        url = f"{self.BASE_API_URL}/projects/{self.project_id}/merge_requests/{self.mr_iid}/changes"

        with handle_gitlab_api_errors(self.mr_iid):
            response = httpx.get(url, headers=self.headers)
            response.raise_for_status()

        with handle_gitlab_data_errors():
            return MergeRequestDTO(**response.json())

    def _get_branch_file_content(self, file_path: str, branch: str) -> str:
        """Fetch raw file content from a specific branch, decoding base64. Returns empty string for missing files."""
        encoded_path = quote(file_path, safe="")
        url = f"{self.BASE_API_URL}/projects/{self.project_id}/repository/files/{encoded_path}"

        with handle_gitlab_api_errors(self.mr_iid):
            response = httpx.get(url, headers=self.headers, params={"ref": branch})
            if response.status_code == 404:
                return ""  # if the file does not exist, assume it's empty
            response.raise_for_status()

        with handle_gitlab_data_errors():
            data = GitLabFileResponse(**response.json())

        if data.encoding == "base64":
            return base64.b64decode(data.content).decode("utf-8")
        return data.content

    def post_comment(self, comment: ReviewComment) -> None:
        """Post a review comment as a general note on the merge request."""
        body = self._format_body(comment)
        if not body.strip():
            # GitLab rejects a blank note body with HTTP 400
            logger.warning("Skipping empty review comment for MR %s", self.mr_iid)
            return

        url = f"{self.BASE_API_URL}/projects/{self.project_id}/merge_requests/{self.mr_iid}/notes"

        with handle_gitlab_api_errors(self.mr_iid):
            response = httpx.post(url, headers=self.headers, json={"body": body})
            response.raise_for_status()

    @staticmethod
    def _format_body(comment: ReviewComment) -> str:
        if not comment.references:
            return comment.content
        references = "\n".join(
            f'- `{ref.file_path}` — "{ref.rule}"' if ref.rule else f"- `{ref.file_path}`"
            for ref in comment.references
        )
        return f"{comment.content}\n\n**References:**\n{references}"

    def get_file_content(self) -> str:
        return ""
