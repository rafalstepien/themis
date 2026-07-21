import pytest

from src.review_engine.domain.models import ChangeType
from tests.unit.review_engine.domain.factories import ChangedFileFactory


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
