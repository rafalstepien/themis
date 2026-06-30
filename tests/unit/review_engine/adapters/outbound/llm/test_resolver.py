import pytest

from src.bootstrap.config import LLMConfig, LLMDeploymentType
from src.bootstrap.exceptions import MissingEnvironmentError
from src.review_engine.adapters.outbound.llm.mock_client import MockLLMClient
from src.review_engine.adapters.outbound.llm.openai_compatible_client import (
    OpenAICompatibleClient,
)
from src.review_engine.adapters.outbound.llm.resolver import LLMClientResolver


def _cloud_config(**overrides: object) -> LLMConfig:
    fields: dict[str, object] = {
        "deployment_type": LLMDeploymentType.CLOUD,
        "model": "gpt-4o",
        "base_url": "https://api.openai.com/v1",
        **overrides,
    }
    return LLMConfig(**fields)


def _self_hosted_config(**overrides: object) -> LLMConfig:
    fields: dict[str, object] = {
        "deployment_type": LLMDeploymentType.SELF_HOSTED,
        "model": "qwen2.5-coder",
        "base_url": "http://localhost:8000/v1",
        **overrides,
    }
    return LLMConfig(**fields)


def test_test_mode_returns_mock_client() -> None:
    client = LLMClientResolver.resolve(_cloud_config(), token="t", test_mode=True)

    assert isinstance(client, MockLLMClient)


def test_resolves_cloud_through_openai_compatible_client() -> None:
    client = LLMClientResolver.resolve(_cloud_config(), token="t", test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "api.openai.com" in str(client._client.base_url)


def test_resolves_self_hosted_with_configured_base_url() -> None:
    config = _self_hosted_config(base_url="http://remote-host:8000/v1")

    client = LLMClientResolver.resolve(config, token=None, test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
    assert "remote-host:8000/v1" in str(client._client.base_url)


def test_cloud_deployment_without_token_is_rejected() -> None:
    with pytest.raises(MissingEnvironmentError, match="LLM_API_TOKEN"):
        LLMClientResolver.resolve(_cloud_config(), token=None, test_mode=False)


def test_self_hosted_deployment_may_be_keyless() -> None:
    client = LLMClientResolver.resolve(_self_hosted_config(), token=None, test_mode=False)

    assert isinstance(client, OpenAICompatibleClient)
