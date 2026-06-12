import json
import os
import sys
from typing import Any, Dict

from src.review_engine.adapters.outbound import GitLabClient


class ReviewEngineCLIAdapter:
    """
    Translates the raw CLI environment context into domain-understandable
    use-cases, insulating the domain logic from env variable layout changes.
    """

    def run(self) -> None:
        secrets = self._parse_gitlab_secrets()
        mr_output = self._fetch_mr_data_from_gitlab(secrets)
        print(mr_output.model_dump_json(indent=2))


    #     # 3. Instantiate Outbound Adapters
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
    def _fetch_mr_data_from_gitlab(gitlab_secrets: dict):
        gitlab_api_base = os.getenv("CI_API_V4_URL")

        gitlab_client = GitLabClient(
            token=gitlab_secrets["gitlab_token"], 
            api_base=gitlab_api_base
        )

        return gitlab_client.get_mr_data(
            project_id=gitlab_secrets["project_id"], 
            mr_iid=int(gitlab_secrets["mr_iid"])
        )


    @staticmethod
    def _parse_gitlab_secrets():
        secret_to_env_var_mapping = {
            "gitlab_token": "GITLAB_API_TOKEN",
            "project_id": "CI_PROJECT_ID",
            "mr_iid": "CI_MERGE_REQUEST_IID",
        }

        secrets = {}
        for secret, env_var in secret_to_env_var_mapping.items():
            secret_value = os.getenv(env_var)
            if not secret_value:
                print(f"CRITICAL: Missing essential {env_var}")
                sys.exit(1)
            secrets[secret] = secret_value
        return secrets

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: config.json not found, falling back to pipeline defaults.")
            return {}
