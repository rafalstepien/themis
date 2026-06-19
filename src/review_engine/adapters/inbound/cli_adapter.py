import logging
import sys

import click

from src.bootstrap.config import Config
from src.bootstrap.environment import CIContext, Secrets
from src.bootstrap.exceptions import MissingEnvironmentError

logger = logging.getLogger(__name__)


class ReviewEngineCLIAdapter:
    """
    Translates the raw CLI environment context into domain-understandable
    use-cases, insulating the domain logic from env variable layout changes.
    """

    def run(self) -> None:
        try:
            secrets = Secrets.load()
            ci_context = CIContext.load()
        except MissingEnvironmentError as exc:
            click.echo(f"CRITICAL: {exc}", err=True)
            sys.exit(1)

        config = Config.from_yaml()

        print(config)

        # gitlab_client = GitLabClient(
        #     token=secrets.gitlab_token,
        #     project_id=ci_context.project_id,
        #     mr_iid=ci_context.mr_iid,
        # )

        # openai_client = OpenAIClient(token=secrets.llm_token)

        # orchestrator = ReviewOrchestrator(
        #     gitlab_port=gitlab_client,
        #     llm_port=openai_client,
        #     business_context_port=JiraClient(token=secrets.jira_token),
        #     best_practices_port=BestPracticesClient(),
        # )

        # try:
        #     orchestrator.execute()
        # except GitLabPortError:
        #     logger.exception("GitLab interaction failed")
        #     click.echo(
        #         "Error: could not complete the review — GitLab is unavailable or returned unexpected data.",
        #         err=True,
        #     )
        #     sys.exit(1)

