import pytest

from src.bootstrap.environment import CISecrets
from src.bootstrap.exceptions import MissingEnvironmentError


def test_loads_all_secrets_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITLAB_API_TOKEN", "gl-token")
    monkeypatch.setenv("LLM_API_TOKEN", "llm-token")
    monkeypatch.setenv("JIRA_API_TOKEN", "jira-token")

    secrets = CISecrets.load()

    assert secrets.gitlab_token == "gl-token"
    assert secrets.llm_token == "llm-token"
    assert secrets.jira_token == "jira-token"


def test_optional_secrets_default_to_none_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITLAB_API_TOKEN", "gl-token")
    # missing JIRA_API_TOKEN
    # missing LLM_API_TOKEN

    secrets = CISecrets.load()

    assert secrets.jira_token is None
    assert secrets.llm_token is None


def test_missing_mandatory_token_reports_variable_with_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(MissingEnvironmentError) as exc_info:
        CISecrets.load()

    assert exc_info.value.variables == ["GITLAB_API_TOKEN"]
    assert "Missing essential environment variables" in str(exc_info.value)
