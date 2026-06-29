import pytest

from src.bootstrap.config import LLMConfig, LLMProvider
from src.bootstrap.exceptions import MissingEnvironmentError
from src.review_engine.adapters.outbound.llm.mock_client import MockLLMClient
from src.review_engine.adapters.outbound.llm.openai_compatible_client import OpenAICompatibleClient
from src.review_engine.adapters.outbound.llm.resolver import LLMClientResolver


def _shortcut_config(**fields: object) -> LLMConfig:
    # Vendor shortcuts ("openai"/"gemini"/"anthropic") are desugared by a
    # before-validator, so they arrive as raw input rather than enum members.
    return LLMConfig.model_validate(fields)


def test_test_mode_returns_mock_client() -> None:
    config = _shortcut_config(provider="openai", model="gpt-4o")

    client = LLMClientResolver.resolve(config, token="t", test_mode=True)

    assert isinstance(client, MockLLMClient)


def test_resolves_openai_shortcut_through_openai_compatible_client() -> None:
    config = _shortcut_config(provider="openai", model="gpt-4o")

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
    config = _shortcut_config(provider="gemini", model="gemini-2.0-flash")

    client = LLMClientResolver.resolve(config, token="key", test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "generativelanguage.googleapis.com" in str(client._client.base_url)


def test_resolves_anthropic_through_openai_compatible_client() -> None:
    config = _shortcut_config(provider="anthropic", model="claude-3-5-haiku-latest")

    client = LLMClientResolver.resolve(config, token="key", test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "api.anthropic.com" in str(client._client.base_url)


def test_default_vendor_base_url_can_be_overridden() -> None:
    config = _shortcut_config(
        provider="gemini", model="gemini-2.0-flash", base_url="http://proxy:8080/v1"
    )

    client = LLMClientResolver.resolve(config, token="key", test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "proxy:8080/v1" in str(client._client.base_url)


def test_cloud_shortcut_without_token_is_rejected() -> None:
    config = _shortcut_config(provider="gemini", model="gemini-2.0-flash")

    with pytest.raises(MissingEnvironmentError, match="LLM_API_TOKEN"):
        LLMClientResolver.resolve(config, token=None, test_mode=False)


def test_explicit_self_host_may_be_keyless() -> None:
    config = LLMConfig(
        provider=LLMProvider.OPENAI_COMPATIBLE,
        model="qwen2.5-coder",
        base_url="http://localhost:8000/v1",
    )

    client = LLMClientResolver.resolve(config, token=None, test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
