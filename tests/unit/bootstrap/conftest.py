import pytest

# Every environment variable the bootstrap settings models read. Cleared before
# each test so a developer's real shell environment can never leak into a case.
_BOOTSTRAP_ENV_VARS = (
    "GITLAB_API_TOKEN",
    "LLM_API_TOKEN",
    "JIRA_API_TOKEN",
    "CI_PROJECT_ID",
    "CI_MERGE_REQUEST_IID",
)


@pytest.fixture(autouse=True)
def clean_bootstrap_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guarantee a pristine environment for every bootstrap test."""
    for name in _BOOTSTRAP_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
