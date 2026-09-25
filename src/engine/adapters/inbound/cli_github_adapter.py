import logging
import sys

from src.bootstrap.config import DEFAULT_CONFIG_PATH, THEMIS_DIR, ThemisConfig
from src.bootstrap.environment_github import GitHubSettings
from src.engine.adapters.outbound import (
    GitHubClient,
    LLMClientResolver,
    LocalFileContextAdapter,
)
from src.engine.domain.review_orchestrator import ReviewOrchestrator
from src.engine.ports.outbound import GitProviderPortError, LLMPortError

logger = logging.getLogger(__name__)


class GitHubCLIAdapter:
    """
    Translates the raw CLI environment context into domain-understandable
    use-cases, insulating the domain logic from env variable layout changes.
    """

    def run(self) -> None:
        settings = GitHubSettings()  # type: ignore
        config = ThemisConfig.from_yaml(settings.settings_dir_path / DEFAULT_CONFIG_PATH)
        github_client = GitHubClient(
            token=settings.github_api_token,
            owner=settings.owner,
            repo=settings.repo,
            pull_number=settings.pull_request_id,
        )
        llm_client = LLMClientResolver.resolve(
            llm_config=config.llm,
            token=settings.llm_api_token,
            test_mode=config.test_mode,
        )

        orchestrator = ReviewOrchestrator(
            review_config=config.review,
            git_provider_port=github_client,
            llm_port=llm_client,
            business_context_port=None,
            module_context_port=LocalFileContextAdapter(
                themis_dir=settings.settings_dir_path / THEMIS_DIR
            ),
        )

        try:
            orchestrator.execute()
        except GitProviderPortError:
            logger.exception("GitHub interaction failed")
            logger.error(
                "Error: could not complete the review — GitHub is unavailable or returned unexpected data."
            )
            sys.exit(1)
        except LLMPortError:
            logger.exception("LLM interaction failed")
            logger.error(
                "Error: could not complete the review — the LLM provider is unavailable or returned unexpected data."
            )
            sys.exit(1)
