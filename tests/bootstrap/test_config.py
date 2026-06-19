from pathlib import Path

import pytest
from pydantic import ValidationError

from src.bootstrap.config import Config, LLMProvider

_FULL_CONFIG = """
version: 1

review:
  max_file_chars: 12345
  max_changed_files: 9

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


def _write_config(tmp_path: Path, body: str) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(body)
    return str(path)


def test_loads_full_config(tmp_path: Path) -> None:
    config = Config.from_yaml(_write_config(tmp_path, _FULL_CONFIG))

    assert config.version == 1
    assert config.review.max_file_chars == 12345
    assert config.review.max_changed_files == 9
    assert config.llm.provider is LLMProvider.ANTHROPIC
    assert config.llm.model == "claude-opus-4-8"


def test_review_section_defaults_when_omitted(tmp_path: Path) -> None:
    config = Config.from_yaml(_write_config(tmp_path, _CONFIG_WITHOUT_REVIEW))

    assert config.review.max_file_chars == 60_000
    assert config.review.max_changed_files == 50


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
