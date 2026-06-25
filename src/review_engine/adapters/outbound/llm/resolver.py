from src.bootstrap.config import (
    ANTHROPIC_OPENAI_BASE_URL,
    GEMINI_OPENAI_BASE_URL,
    LLMConfig,
    LLMProvider,
)
from src.review_engine.ports.outbound import LLMPort

from .mock_client import MockLLMClient
from .openai_client import OpenAIClient
from .openai_compatible_client import OpenAICompatibleClient

# Vendors served through OpenAICompatibleClient with a default base_url the user may override.
_DEFAULT_OPENAI_COMPATIBLE_BASE_URLS = {
    LLMProvider.GEMINI: GEMINI_OPENAI_BASE_URL,
    LLMProvider.ANTHROPIC: ANTHROPIC_OPENAI_BASE_URL,
}


class LLMClientResolver:
    """Selects the concrete LLM adapter for the configured provider."""

    @staticmethod
    def resolve(llm_config: LLMConfig, token: str | None, test_mode: bool) -> LLMPort:
        if test_mode:
            return MockLLMClient()

        match llm_config.provider:
            case LLMProvider.OPENAI:
                return OpenAIClient(model=llm_config.model, token=token)
            case LLMProvider.OPENAI_COMPATIBLE | LLMProvider.GEMINI | LLMProvider.ANTHROPIC:
                base_url = llm_config.base_url or _DEFAULT_OPENAI_COMPATIBLE_BASE_URLS.get(
                    llm_config.provider
                )
                # openai_compatible always has a base_url (LLMConfig validator); the
                # vendors fall back to their default above.
                assert base_url is not None
                return OpenAICompatibleClient(
                    model=llm_config.model, base_url=base_url, token=token
                )
            case _:
                raise NotImplementedError(
                    f"LLM provider '{llm_config.provider}' is not supported yet."
                )
