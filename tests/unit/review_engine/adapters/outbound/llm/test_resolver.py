from src.bootstrap.config import LLMConfig, LLMProvider
from src.review_engine.adapters.outbound.llm.mock_client import MockLLMClient
from src.review_engine.adapters.outbound.llm.openai_compatible_client import OpenAICompatibleClient
from src.review_engine.adapters.outbound.llm.resolver import LLMClientResolver


def test_test_mode_returns_mock_client() -> None:
    config = LLMConfig(provider="openai", model="gpt-4o")

    client = LLMClientResolver.resolve(config, token="t", test_mode=True)

    assert isinstance(client, MockLLMClient)


def test_resolves_openai_shortcut_through_openai_compatible_client() -> None:
    config = LLMConfig(provider="openai", model="gpt-4o")

    client = LLMClientResolver.resolve(config, token="t", test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "api.openai.com" in str(client._client.base_url)


def test_resolves_openai_compatible_with_configured_base_url() -> None:
    config = LLMConfig(
        provider=LLMProvider.OPENAI_COMPATIBLE,
        model="llama3.1",
        base_url="http://remote-host:8000/v1",
    )

    client = LLMClientResolver.resolve(config, token="t", test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "remote-host:8000/v1" in str(client._client.base_url)


def test_resolves_gemini_through_openai_compatible_client() -> None:
    config = LLMConfig(provider="gemini", model="gemini-2.0-flash")

    client = LLMClientResolver.resolve(config, token="key", test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "generativelanguage.googleapis.com" in str(client._client.base_url)


def test_resolves_anthropic_through_openai_compatible_client() -> None:
    config = LLMConfig(provider="anthropic", model="claude-3-5-haiku-latest")

    client = LLMClientResolver.resolve(config, token="key", test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "api.anthropic.com" in str(client._client.base_url)


def test_default_vendor_base_url_can_be_overridden() -> None:
    config = LLMConfig(
        provider="gemini", model="gemini-2.0-flash", base_url="http://proxy:8080/v1"
    )

    client = LLMClientResolver.resolve(config, token="key", test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "proxy:8080/v1" in str(client._client.base_url)
