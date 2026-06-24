import logging
from pathlib import Path

from pydantic import ValidationError
import pytest

from src.bootstrap.config import Config, LLMProvider

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
  provider: anthropic
  model: claude-opus-4-8
"""

_CONFIG_WITHOUT_REVIEW = """
version: 1

llm:
  provider: openai
  model: gpt-4o
"""

_OPENAI_COMPATIBLE_CONFIG = """
version: 1

llm:
  provider: openai_compatible
  model: qwen2.5-coder
  base_url: http://localhost:8000/v1
"""


def _write_config(tmp_path: Path, body: str) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(body)
    return str(path)


def test_loads_full_config(tmp_path: Path) -> None:
    config = Config.from_yaml(_write_config(tmp_path, _FULL_CONFIG))

    assert config.version == 1
    assert config.review.max_file_chars == 12345
    assert config.review.max_changed_files == 9
    assert config.review.modules == [
        "src/orders",
        "src/engine",
        "helpers/logging",
    ]
    assert config.llm.provider is LLMProvider.ANTHROPIC
    assert config.llm.model == "claude-opus-4-8"


def test_review_section_defaults_when_omitted(tmp_path: Path) -> None:
    config = Config.from_yaml(_write_config(tmp_path, _CONFIG_WITHOUT_REVIEW))

    assert config.review.max_file_chars == 60_000
    assert config.review.max_changed_files == 50
    assert config.review.modules == []


def test_warns_when_no_modules_declared(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        Config.from_yaml(_write_config(tmp_path, _CONFIG_WITHOUT_REVIEW))

    assert any(
        "No modules declared" in record.message and record.levelno == logging.WARNING
        for record in caplog.records
    )


def test_does_not_warn_when_modules_declared(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING):
        Config.from_yaml(_write_config(tmp_path, _FULL_CONFIG))

    assert caplog.records == []


def test_unknown_provider_is_rejected(tmp_path: Path) -> None:
    body = _FULL_CONFIG.replace("provider: anthropic", "provider: bedrock")

    with pytest.raises(ValidationError):
        Config.from_yaml(_write_config(tmp_path, body))


def test_missing_required_key_is_rejected(tmp_path: Path) -> None:
    body = _FULL_CONFIG.replace("version: 1", "")

    with pytest.raises(ValidationError):
        Config.from_yaml(_write_config(tmp_path, body))


def test_nonexistent_path_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Config.from_yaml(str(tmp_path / "does-not-exist.yaml"))


def test_custom_path_argument_is_honoured(tmp_path: Path) -> None:
    path = tmp_path / "custom-name.yaml"
    path.write_text(_FULL_CONFIG)

    config = Config.from_yaml(str(path))

    assert config.llm.model == "claude-opus-4-8"


def test_openai_compatible_provider_loads_base_url(tmp_path: Path) -> None:
    config = Config.from_yaml(_write_config(tmp_path, _OPENAI_COMPATIBLE_CONFIG))

    assert config.llm.provider is LLMProvider.OPENAI_COMPATIBLE
    assert config.llm.base_url == "http://localhost:8000/v1"


def test_openai_compatible_provider_requires_base_url(tmp_path: Path) -> None:
    body = _OPENAI_COMPATIBLE_CONFIG.replace("  base_url: http://localhost:8000/v1\n", "")

    with pytest.raises(ValidationError, match="base_url"):
        Config.from_yaml(_write_config(tmp_path, body))
