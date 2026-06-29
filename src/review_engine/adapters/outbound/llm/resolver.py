from src.bootstrap.config import LLMConfig
from src.review_engine.ports.outbound import LLMPort

from .mock_client import MockLLMClient
from .openai_compatible_client import OpenAICompatibleClient


class LLMClientResolver:
    """Selects the concrete LLM adapter for the configured provider."""

    @staticmethod
    def resolve(llm_config: LLMConfig, token: str | None, test_mode: bool) -> LLMPort:
        if test_mode:
            return MockLLMClient()

        # Every provider has been desugared to openai_compatible with a concrete
        # base_url (vendor shortcuts get a default; explicit self-host is required
        # to set one), so there is a single client to build.
        assert llm_config.base_url is not None
        return OpenAICompatibleClient(
            model=llm_config.model, base_url=llm_config.base_url, token=token
        )
