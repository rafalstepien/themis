from src.bootstrap.config import LLMConfig, LLMProvider
from src.review_engine.ports.outbound import LLMPort

from .mock_client import MockLLMClient
from .openai_client import OpenAIClient
from .openai_compatible_client import OpenAICompatibleClient


class LLMClientResolver:
    """Selects the concrete LLM adapter for the configured provider."""

    @staticmethod
    def resolve(llm_config: LLMConfig, token: str | None, test_mode: bool) -> LLMPort:
        if test_mode:
            return MockLLMClient()

        match llm_config.provider:
            case LLMProvider.OPENAI:
                return OpenAIClient(model=llm_config.model, token=token)
            case LLMProvider.OPENAI_COMPATIBLE:
                assert llm_config.base_url is not None
                return OpenAICompatibleClient(
                    model=llm_config.model, base_url=llm_config.base_url, token=token
                )
            case _:
                raise NotImplementedError(
                    f"LLM provider '{llm_config.provider}' is not supported yet."
                )
