from pathlib import Path

import pytest

from src.bootstrap.environment import CIContext
from src.bootstrap.exceptions import MissingEnvironmentError


def test_loads_context_and_coerces_mr_iid_to_int(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CI_PROJECT_ID", "42")
    monkeypatch.setenv("CI_MERGE_REQUEST_IID", "7")

    ci_context = CIContext.load()

    assert ci_context.project_id == "42"
    assert ci_context.mr_iid == 7
    assert isinstance(ci_context.mr_iid, int)


def test_project_dir_defaults_to_cwd_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CI_PROJECT_DIR", raising=False)
    monkeypatch.setenv("CI_PROJECT_ID", "42")
    monkeypatch.setenv("CI_MERGE_REQUEST_IID", "7")

    ci_context = CIContext.load()

    assert ci_context.project_dir == Path(".")


def test_project_dir_anchors_to_ci_project_dir_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CI_PROJECT_DIR", "/builds/acme/shop")
    monkeypatch.setenv("CI_PROJECT_ID", "42")
    monkeypatch.setenv("CI_MERGE_REQUEST_IID", "7")

    ci_context = CIContext.load()

    assert ci_context.project_dir == Path("/builds/acme/shop")


def test_missing_all_context_reports_each_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(MissingEnvironmentError) as exc_info:
        CIContext.load()

    assert set(exc_info.value.variables) == {
        "CI_PROJECT_ID",
        "CI_MERGE_REQUEST_IID",
    }


def test_non_integer_mr_iid_raises_with_empty_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Pins current behaviour: a non-"missing" validation error (bad int) is
    # still surfaced as MissingEnvironmentError, but with no variable names,
    # because load() only collects errors of type "missing". This is a known
    # rough edge worth revisiting separately.
    monkeypatch.setenv("CI_PROJECT_ID", "42")
    monkeypatch.setenv("CI_MERGE_REQUEST_IID", "not-a-number")

    with pytest.raises(MissingEnvironmentError) as exc_info:
        CIContext.load()

    assert exc_info.value.variables == []
