import logging
from pathlib import Path

from pydantic import ValidationError
import pytest

from src.bootstrap.config import LLMDeploymentType, ThemisConfig

_FULL_CONFIG = """
version: 1

review:
  max_file_chars: 12345
  max_changed_files: 9
  modules:
    - src/orders
    - src/engine
    - helpers/logging

llm:
  deployment_type: cloud
  model: claude-opus-4-8
  base_url: https://api.anthropic.com/v1/
"""

_CONFIG_WITHOUT_REVIEW = """
version: 1

llm:
  deployment_type: cloud
  model: gpt-4o
  base_url: https://api.openai.com/v1
"""

_SELF_HOSTED_CONFIG = """
version: 1

llm:
  deployment_type: self_hosted
  model: qwen2.5-coder
  base_url: http://localhost:8000/v1
"""


def _write_config(tmp_path: Path, body: str) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(body)
    return str(path)


def test_loads_full_config(tmp_path: Path) -> None:
    config = ThemisConfig.from_yaml(_write_config(tmp_path, _FULL_CONFIG))

    assert config.version == 1
    assert config.review.max_file_chars == 12345
    assert config.review.max_changed_files == 9
    assert config.review.modules == [
        "src/orders",
        "src/engine",
        "helpers/logging",
    ]
    assert config.llm.deployment_type is LLMDeploymentType.CLOUD
    assert config.llm.base_url == "https://api.anthropic.com/v1/"
    assert config.llm.model == "claude-opus-4-8"


def test_warns_when_no_modules_declared(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        ThemisConfig.from_yaml(_write_config(tmp_path, _CONFIG_WITHOUT_REVIEW))

    assert any(
        "No modules declared" in record.message and record.levelno == logging.WARNING
        for record in caplog.records
    )


def test_unknown_deployment_type_is_rejected(tmp_path: Path) -> None:
    body = _FULL_CONFIG.replace("deployment_type: cloud", "deployment_type: bedrock")

    with pytest.raises(ValidationError):
        ThemisConfig.from_yaml(_write_config(tmp_path, body))


def test_missing_required_key_is_rejected(tmp_path: Path) -> None:
    body = _FULL_CONFIG.replace("version: 1", "")

    with pytest.raises(ValidationError):
        ThemisConfig.from_yaml(_write_config(tmp_path, body))


def test_base_url_is_required(tmp_path: Path) -> None:
    body = _FULL_CONFIG.replace("  base_url: https://api.anthropic.com/v1/\n", "")

    with pytest.raises(ValidationError, match="base_url"):
        ThemisConfig.from_yaml(_write_config(tmp_path, body))


def test_nonexistent_path_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ThemisConfig.from_yaml(str(tmp_path / "does-not-exist.yaml"))


def test_custom_path_argument_is_honoured(tmp_path: Path) -> None:
    path = tmp_path / "custom-name.yaml"
    path.write_text(_FULL_CONFIG)

    config = ThemisConfig.from_yaml(str(path))

    assert config.llm.model == "claude-opus-4-8"


def test_cloud_deployment_requires_a_token(tmp_path: Path) -> None:
    config = ThemisConfig.from_yaml(_write_config(tmp_path, _CONFIG_WITHOUT_REVIEW))

    assert config.llm.requires_token is True


def test_self_hosted_deployment_is_keyless(tmp_path: Path) -> None:
    config = ThemisConfig.from_yaml(_write_config(tmp_path, _SELF_HOSTED_CONFIG))

    assert config.llm.requires_token is False
