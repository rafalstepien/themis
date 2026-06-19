from src.bootstrap.config import LLMConfig, LLMProvider
from src.review_engine.ports.outbound import LLMPort

from .mock_client import MockLLMClient
from .openai_client import OpenAIClient


class LLMClientResolver:
    """Selects the concrete LLM adapter for the configured provider."""

    @staticmethod
    def resolve(llm_config: LLMConfig, token: str, test_mode: bool) -> LLMPort:
        if test_mode:
            return MockLLMClient()

        match llm_config.provider:
            case LLMProvider.OPENAI:
                return OpenAIClient(model=llm_config.model, token=token)
            case _:
                raise NotImplementedError(
                    f"LLM provider '{llm_config.provider}' is not supported yet."
                )
