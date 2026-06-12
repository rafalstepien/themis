import json
import os
import sys
from typing import Any, Dict


class ReviewEngineCLIAdapter:
    """
    Translates the raw CLI environment context into domain-understandable
    use-cases, insulating the domain logic from env variable layout changes.
    """

    def run(self) -> None:
        config = self._load_config()
        gitlab_token, llm_token, jira_token = self._extract_secrets()

    #     # 3. Instantiate Outbound Adapters
    #     gitlab_client = GitLabClient(token=gitlab_token)
    #     llm_client = OpenAIClient(token=llm_token)
    #     ast_parser = ASTEngine()
    #     jira_client = JiraClient(token=jira_token) if jira_token else None

    #     # 4. Inject structural adapters into the pure Domain Service
    #     orchestrator = ReviewOrchestrator(
    #         gitlab_port=gitlab_client,
    #         llm_port=llm_client,
    #         ast_port=ast_parser,
    #         jira_port=jira_client,
    #     )

    #     # 5. Execute use case using dynamic pipeline run data
    #     mr_id = os.getenv("CI_MERGE_REQUEST_IID", "1")

    #     orchestrator.execute(
    #         mr_id=mr_id,
    #         ref_branch=config.get("reference_branch", "main"),
    #         target_branch=config.get("target_branch"),
    #     )

    @staticmethod
    def _extract_secrets():
        gitlab_token = os.getenv("GITLAB_API_TOKEN")
        if not gitlab_token:
            print("CRITICAL: Missing essential GITLAB_API_TOKEN")
            sys.exit(1)

        llm_token = os.getenv("LLM_API_TOKEN")
        if not llm_token:
            print("CRITICAL: Missing essential LLM_API_TOKEN")
            sys.exit(1)

        jira_token = os.getenv("JIRA_API_TOKEN")

        return gitlab_token, llm_token, jira_token

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: config.json not found, falling back to pipeline defaults.")
            return {}
