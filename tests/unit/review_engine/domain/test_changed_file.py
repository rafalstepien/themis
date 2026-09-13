import pytest

from src.review_engine.domain.models import ChangedFile, ChangeType
from tests.unit.review_engine.domain.factories import (
    EXAMPLE_DIFF_WITH_SIX_LINES_CHANGED,
    ChangedFileFactory,
)


@pytest.mark.parametrize(
    ["change_type", "expected_path"],
    [
        pytest.param(
            ChangeType.DELETED,
            "old-path",
            id="Displays old path when file is deleted (because new path does not exist).",
        ),
        pytest.param(
            ChangeType.RENAMED, "old-path -> new-path", id="Displays arrow when file is renamed."
        ),
        pytest.param(
            ChangeType.MODIFIED, "new-path", id="Displays new path when file is modified."
        ),
        pytest.param(
            ChangeType.ADDED,
            "new-path",
            id="Displays new path when file is added (because old path does not exist)",
        ),
    ],
)
def test_changed_file_display_path(change_type: ChangeType, expected_path: str):
    changed_file = ChangedFileFactory.build(change_type=change_type)
    assert changed_file.display_path == expected_path


@pytest.mark.parametrize(
    ["changed_file", "should_be_reviewed"],
    [
        pytest.param(ChangedFileFactory.build(), True, id="Happy path"),
        pytest.param(ChangedFileFactory.build(generated_file=True), False, id="Generated file"),
        pytest.param(
            ChangedFileFactory.build(too_large=True), False, id="File marked as too large by GitLab"
        ),
        pytest.param(
            ChangedFileFactory.build(raw_diff=EXAMPLE_DIFF_WITH_SIX_LINES_CHANGED),
            False,
            id="Changes exceed config limit",
        ),
    ],
)
def test_changed_file_is_reviewable(changed_file: ChangedFile, should_be_reviewed: bool):
    assert changed_file.is_reviewable(max_changed_lines_per_file=4) is should_be_reviewed
