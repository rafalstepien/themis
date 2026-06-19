import logging
import sys

import click

from src.bootstrap.config import Config, LLMProvider
from src.bootstrap.environment import CIContext, Secrets
from src.bootstrap.exceptions import MissingEnvironmentError
from src.review_engine.adapters.outbound.best_practices_client import BestPracticesClient
from src.review_engine.adapters.outbound.gitlab import GitLabClient
from src.review_engine.adapters.outbound.jira_client import JiraClient
from src.review_engine.adapters.outbound.llm.mock_client import MockLLMClient
from src.review_engine.adapters.outbound.llm.openai_client import OpenAIClient
from src.review_engine.domain.review_orchestrator import ReviewOrchestrator
from src.review_engine.ports.outbound.gitlab import GitLabPortError
from src.review_engine.ports.outbound.llm_port import LLMPort, LLMPortError

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

        gitlab_client = GitLabClient(
            token=secrets.gitlab_token,
            project_id=ci_context.project_id,
            mr_iid=ci_context.mr_iid,
        )

        llm_client = self._resolve_llm_client(
            provider=config.llm.provider,
            model=config.llm.model,
            token=secrets.llm_token,
            test_mode=config.test_mode,
        )

        orchestrator = ReviewOrchestrator(
            config=config,
            gitlab_port=gitlab_client,
            llm_port=llm_client,
            business_context_port=JiraClient(token=secrets.jira_token),
            best_practices_port=BestPracticesClient(),
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

    def _resolve_llm_client(
        self, provider: LLMProvider, model: str, token: str, test_mode: bool
    ) -> LLMPort:
        if test_mode:
            return MockLLMClient()

        match provider:
            case LLMProvider.OPENAI:
                return OpenAIClient(model=model, token=token)
            case _:
                raise NotImplementedError(f"LLM provider '{provider}' is not supported yet.")
