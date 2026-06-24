import pytest

from src.bootstrap.environment import Secrets
from src.bootstrap.exceptions import MissingEnvironmentError


def test_loads_all_tokens_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITLAB_API_TOKEN", "gl-token")
    monkeypatch.setenv("LLM_API_TOKEN", "llm-token")
    monkeypatch.setenv("JIRA_API_TOKEN", "jira-token")

    secrets = Secrets.load()

    assert secrets.gitlab_token == "gl-token"
    assert secrets.llm_token == "llm-token"
    assert secrets.jira_token == "jira-token"


def test_jira_token_defaults_to_none_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITLAB_API_TOKEN", "gl-token")
    monkeypatch.setenv("LLM_API_TOKEN", "llm-token")

    secrets = Secrets.load()

    assert secrets.jira_token is None


def test_llm_token_defaults_to_none_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITLAB_API_TOKEN", "gl-token")

    secrets = Secrets.load()

    assert secrets.llm_token is None


def test_unrelated_env_vars_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITLAB_API_TOKEN", "gl-token")
    monkeypatch.setenv("LLM_API_TOKEN", "llm-token")
    monkeypatch.setenv("SOME_UNRELATED_VAR", "noise")

    secrets = Secrets.load()

    assert secrets.gitlab_token == "gl-token"
    assert secrets.llm_token == "llm-token"


def test_missing_single_mandatory_token_reports_that_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_API_TOKEN", "llm-token")

    with pytest.raises(MissingEnvironmentError) as exc_info:
        Secrets.load()

    assert exc_info.value.variables == ["GITLAB_API_TOKEN"]


def test_missing_mandatory_token_reports_variable_with_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(MissingEnvironmentError) as exc_info:
        Secrets.load()

    assert set(exc_info.value.variables) == {"GITLAB_API_TOKEN"}
    assert "Missing essential environment variables" in str(exc_info.value)
