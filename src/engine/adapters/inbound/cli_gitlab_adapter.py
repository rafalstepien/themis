import logging
import sys

from src.bootstrap.config import DEFAULT_CONFIG_PATH, THEMIS_DIR, ThemisConfig
from src.bootstrap.environment_gitlab import GitLabCIContext, GitLabCISecrets
from src.bootstrap.exceptions import MissingEnvironmentError
from src.engine.adapters.outbound import (
    GitLabClient,
    JiraClient,
    LLMClientResolver,
    LocalFileContextAdapter,
)
from src.engine.domain.review_orchestrator import ReviewOrchestrator
from src.engine.ports.outbound import GitProviderPortError, LLMPortError

logger = logging.getLogger(__name__)


class GitLabCLIAdapter:
    """
    Translates the raw CLI environment context into domain-understandable
    use-cases, insulating the domain logic from env variable layout changes.
    """

    def run(self) -> None:
        try:
            secrets = GitLabCISecrets.load()
            ci_context = GitLabCIContext.load()
        except MissingEnvironmentError as exc:
            logger.error("CRITICAL: {%s}", exc)
            sys.exit(1)

        config = ThemisConfig.from_yaml(ci_context.project_dir / DEFAULT_CONFIG_PATH)

        gitlab_client = GitLabClient(
            token=secrets.gitlab_api_token,
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
            git_provider_port=gitlab_client,
            llm_port=llm_client,
            business_context_port=JiraClient(token=secrets.jira_token),
            module_context_port=LocalFileContextAdapter(
                themis_dir=ci_context.project_dir / THEMIS_DIR
            ),
        )

        try:
            orchestrator.execute()
        except GitProviderPortError:
            logger.exception("GitLab interaction failed")
            logger.error(
                "Error: could not complete the review — GitLab is unavailable or returned unexpected data."
            )
            sys.exit(1)
        except LLMPortError:
            logger.exception("LLM interaction failed")
            logger.error(
                "Error: could not complete the review — the LLM provider is unavailable or returned unexpected data."
            )
            sys.exit(1)
