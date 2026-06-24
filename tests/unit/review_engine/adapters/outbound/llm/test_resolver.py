from src.bootstrap.config import LLMConfig, LLMProvider
from src.review_engine.adapters.outbound.llm.mock_client import MockLLMClient
from src.review_engine.adapters.outbound.llm.openai_client import OpenAIClient
from src.review_engine.adapters.outbound.llm.openai_compatible_client import OpenAICompatibleClient
from src.review_engine.adapters.outbound.llm.resolver import LLMClientResolver


def test_test_mode_returns_mock_client() -> None:
    config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o")

    client = LLMClientResolver.resolve(config, token="t", test_mode=True)

    assert isinstance(client, MockLLMClient)


def test_resolves_openai_provider_to_openai_client() -> None:
    config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o")

    client = LLMClientResolver.resolve(config, token="t", test_mode=False)

    assert isinstance(client, OpenAIClient)


def test_resolves_openai_compatible_with_configured_base_url() -> None:
    config = LLMConfig(
        provider=LLMProvider.OPENAI_COMPATIBLE,
        model="llama3.1",
        base_url="http://remote-host:8000/v1",
    )

    client = LLMClientResolver.resolve(config, token="t", test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "remote-host:8000/v1" in str(client._client.base_url)
