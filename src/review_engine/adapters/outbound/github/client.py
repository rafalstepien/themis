import base64
import logging
from urllib.parse import quote

import httpx

from src.review_engine.domain.models import (
    CommentAnchor,
    DiffRefs,
    MergeRequest,
    MRComments,
    ReviewComment,
)
from src.review_engine.ports.outbound import (
    GitProviderPort,
)  # Assuming GitHubPort inherits or mirrors this

from .dto import (
    GitHubCommentDTO,
    GitHubFileContentResponseDTO,
    GitHubPullRequestDTO,
    GitHubUserDTO,
)
from .exceptions import handle_github_api_errors, handle_github_data_errors
from .mappers import pr_comments_to_domain, pr_to_domain, token_owner_to_domain

logger = logging.getLogger(__name__)


class GitHubClient(
    GitProviderPort
):  # You would likely rename GitLabPort to VersionControlPort
    BASE_API_URL = "https://api.github.com"

    def __init__(self, token: str, owner: str, repo: str, pull_number: int):
        self.owner = owner
        self.repo = repo
        self.pull_number = pull_number
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def post_general_comment(self, comment: ReviewComment) -> None:
        """Post a review comment as a general issue comment on the pull request."""
        body = self._format_body(comment)
        if not body.strip():
            logger.warning("Skipping empty review comment for PR %s", self.pull_number)
            return

        url = f"{self.BASE_API_URL}/repos/{self.owner}/{self.repo}/issues/{self.pull_number}/comments"

        with handle_github_api_errors(self.pull_number):
            response = self._client.post(url, json={"body": body})
            response.raise_for_status()

    def post_inline_comment(self, comment: ReviewComment, diff_refs: DiffRefs) -> None:
        """Post a review comment anchored to specific line"""
        if comment.anchor is None:
            raise ValueError("post_inline_comment requires comment.anchor to be set")

        body = self._format_body(comment)
        if not body.strip():
            logger.warning("Skipping empty review comment for PR %s", self.pull_number)
            return

        url = f"{self.BASE_API_URL}/repos/{self.owner}/{self.repo}/pulls/{self.pull_number}/comments"

        # GitHub uses standard parameters for inline PR comments
        # Requires the line number, path, commit ID, and side of the diff.
        payload = {
            "body": body,
            "commit_id": diff_refs.head_sha,
            "path": comment.anchor.new_path or comment.anchor.old_path,
        }

        if comment.anchor.new_line is not None:
            payload["line"] = comment.anchor.new_line
            payload["side"] = "RIGHT"
        elif comment.anchor.old_line is not None:
            payload["line"] = comment.anchor.old_line
            payload["side"] = "LEFT"

        with handle_github_api_errors(self.pull_number):
            response = self._client.post(url, json=payload)
            response.raise_for_status()

    def get_mr_data(self) -> MergeRequest:
        pr_url = f"{self.BASE_API_URL}/repos/{self.owner}/{self.repo}/pulls/{self.pull_number}"
        files_url = f"{pr_url}/files"

        with handle_github_api_errors(self.pull_number):
            pr_response = self._client.get(pr_url)
            pr_response.raise_for_status()

            # Note: For very large PRs, this endpoint is paginated.
            files_response = self._client.get(files_url, params={"per_page": 100})
            files_response.raise_for_status()

        pr_data = pr_response.json()
        pr_data["files"] = files_response.json()

        with handle_github_data_errors():
            dto = GitHubPullRequestDTO.model_validate(pr_data)

        return pr_to_domain(dto)

    def get_token_owner_details(self):
        url = f"{self.BASE_API_URL}/user"

        with handle_github_api_errors(self.pull_number):
            response = self._client.get(url)
            response.raise_for_status()

        with handle_github_data_errors():
            dto = GitHubUserDTO.model_validate(response.json())

        return token_owner_to_domain(dto)

    def get_mr_comments(self) -> MRComments:
        # Every pull request is an issue, but not every issue is a pull request.
        # General conversation uses the issues comments endpoint, whereas line-specific code feedback uses the pull request review comments endpoint.
        issues_url = f"{self.BASE_API_URL}/repos/{self.owner}/{self.repo}/issues/{self.pull_number}/comments"
        review_url = f"{self.BASE_API_URL}/repos/{self.owner}/{self.repo}/pulls/{self.pull_number}/comments"

        with handle_github_api_errors(self.pull_number):
            issues_response = self._client.get(issues_url, params={"per_page": 100})
            issues_response.raise_for_status()

            review_response = self._client.get(review_url, params={"per_page": 100})
            review_response.raise_for_status()

        with handle_github_data_errors():
            general_comments = [
                GitHubCommentDTO.model_validate(c) for c in issues_response.json()
            ]
            review_comments = [
                GitHubCommentDTO.model_validate(c) for c in review_response.json()
            ]

        return pr_comments_to_domain(general_comments, review_comments)

    def _get_branch_file_content(self, file_path: str, branch: str) -> str:
        """Fetch raw file content from a specific branch, decoding base64."""
        encoded_path = quote(file_path, safe="")
        url = f"{self.BASE_API_URL}/repos/{self.owner}/{self.repo}/contents/{encoded_path}"

        with handle_github_api_errors(self.pull_number):
            response = self._client.get(url, params={"ref": branch})
            if response.status_code == 404:
                return ""
            response.raise_for_status()

        with handle_github_data_errors():
            data = GitHubFileContentResponseDTO.model_validate(response.json())

        if data.encoding == "base64":
            return base64.b64decode(data.content).decode("utf-8")
        return data.content

    @staticmethod
    def _format_body(comment: ReviewComment) -> str:
        if not comment.references:
            return comment.content
        references = "\n".join(
            (
                f'- `{ref.file_path}` — "{ref.rule}"'
                if ref.rule
                else f"- `{ref.file_path}`"
            )
            for ref in comment.references
        )
        return f"{comment.content}\n\n**References:**\n{references}"

    def get_file_content(self) -> str:
        return ""
