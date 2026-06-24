import logging
import sys

import click

from src.bootstrap.config import DEFAULT_CONFIG_PATH, THEMIS_DIR, ThemisConfig
from src.bootstrap.environment import CIContext, Secrets
from src.bootstrap.exceptions import MissingEnvironmentError
from src.review_engine.adapters.outbound import (
    BestPracticesClient,
    GitLabClient,
    JiraClient,
    LLMClientResolver,
    LocalFileContextAdapter,
)
from src.review_engine.domain.review_orchestrator import ReviewOrchestrator
from src.review_engine.ports.outbound import GitLabPortError, LLMPortError

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

        config = ThemisConfig.from_yaml(ci_context.project_dir / DEFAULT_CONFIG_PATH)

        gitlab_client = GitLabClient(
            token=secrets.gitlab_token,
            project_id=ci_context.project_id,
            mr_iid=ci_context.mr_iid,
        )

        llm_client = LLMClientResolver.resolve(
            llm_config=config.llm,
            token=secrets.llm_token,
            test_mode=config.test_mode,
        )

        orchestrator = ReviewOrchestrator(
            review_config=config.review,
            gitlab_port=gitlab_client,
            llm_port=llm_client,
            business_context_port=JiraClient(token=secrets.jira_token),
            best_practices_port=BestPracticesClient(),
            module_context_port=LocalFileContextAdapter(
                themis_dir=ci_context.project_dir / THEMIS_DIR
            ),
        )

        try:
            orchestrator.execute()
        except GitLabPortError:
            logger.exception("GitLab interaction failed")
            click.echo(
                "Error: could not complete the review — GitLab is unavailable or returned unexpected data.",
                err=True,
            )
            sys.exit(1)
        except LLMPortError:
            logger.exception("LLM interaction failed")
            click.echo(
                "Error: could not complete the review — the LLM provider is unavailable or returned unexpected data.",
                err=True,
            )
            sys.exit(1)
