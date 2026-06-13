import json
import os
import sys
from typing import Any, Dict

from src.review_engine.adapters.outbound import GitLabClient
from src.review_engine.domain.review_orchestrator import ReviewOrchestrator


class ReviewEngineCLIAdapter:
    """
    Translates the raw CLI environment context into domain-understandable
    use-cases, insulating the domain logic from env variable layout changes.
    """

    def run(self) -> None:
        secrets = self._parse_gitlab_secrets()

        gitlab_client = GitLabClient(
            token=secrets["gitlab_token"],
            project_id=secrets["project_id"],
            mr_iid=int(secrets["mr_iid"]),
            api_base=os.getenv("CI_API_V4_URL"),
        )

        orchestrator = ReviewOrchestrator(
            gitlab_port=gitlab_client,
            llm_port=None,
            code_representation_port=None,
            business_context_port=None,
            best_practices_port=None,
        )

        orchestrator.execute()

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
