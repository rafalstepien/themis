from src.bootstrap.config import LLMConfig
from src.bootstrap.environment import LLM_TOKEN_ENV_VAR
from src.bootstrap.exceptions import MissingEnvironmentError
from src.review_engine.ports.outbound import LLMPort

from .mock_client import MockLLMClient
from .openai_compatible_client import OpenAICompatibleClient


class LLMClientResolver:
    """Selects the concrete LLM adapter for the configured provider."""

    @staticmethod
    def resolve(llm_config: LLMConfig, token: str | None, test_mode: bool) -> LLMPort:
        if test_mode:
            return MockLLMClient()

        if llm_config.requires_token and not token:
            raise MissingEnvironmentError([LLM_TOKEN_ENV_VAR])

        return OpenAICompatibleClient(
            model=llm_config.model, base_url=llm_config.base_url, token=token
        )
