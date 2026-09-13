import pytest

from src.bootstrap.config import ReviewConfig
from src.review_engine.domain.models import ChangedFile
from tests.unit.review_engine.domain.factories import (
    EXAMPLE_DIFF_WITH_SIX_LINES_CHANGED,
    ChangedFileFactory,
    MergeRequestFactory,
)

MAX_CHANGED_FILES = 2


@pytest.mark.parametrize(
    ["files", "should_be_reviewed"],
    [
        pytest.param(
            [ChangedFileFactory.build()], True, id="Number of changed files less than max"
        ),
        pytest.param(
            [ChangedFileFactory.build(), ChangedFileFactory.build()],
            True,
            id="Number of changed files equal to max",
        ),
        pytest.param(
            [ChangedFileFactory.build(), ChangedFileFactory.build(), ChangedFileFactory.build()],
            False,
            id="Number of changed files exceeds max",
        ),
        pytest.param([], False, id="No files"),
    ],
)
def test_should_be_reviewed_variable_number_of_files(
    files: list[ChangedFile], should_be_reviewed: bool
):
    mr = MergeRequestFactory.build(files=files)
    assert mr.should_be_reviewed(MAX_CHANGED_FILES) is should_be_reviewed


def test_remove_files_that_are_too_big():
    files = [
        ChangedFileFactory.build(raw_diff=EXAMPLE_DIFF_WITH_SIX_LINES_CHANGED),
        ChangedFileFactory.build(),
        ChangedFileFactory.build(raw_diff=EXAMPLE_DIFF_WITH_SIX_LINES_CHANGED),
        ChangedFileFactory.build(),
        ChangedFileFactory.build(raw_diff=EXAMPLE_DIFF_WITH_SIX_LINES_CHANGED),
    ]
    mr = MergeRequestFactory.build(files=files)

    assert len(mr.files) == 5

    mr.remove_too_big_files(max_changed_lines_per_file=5)

    assert len(mr.files) == 2


MODULES_CONFIG = ReviewConfig(modules=["src/orders", "src/engine", "helpers/logging"])


def test_affected_modules_single_file_in_one_module():
    mr = MergeRequestFactory.build(
        files=[
            ChangedFileFactory.build(
                new_path="src/orders/domain.py", old_path="src/orders/domain.py"
            )
        ]
    )

    assert mr.affected_modules(MODULES_CONFIG) == ["src/orders"]


def test_affected_modules_spans_multiple_modules_in_config_order():
    mr = MergeRequestFactory.build(
        files=[
            ChangedFileFactory.build(
                new_path="helpers/logging/app.py", old_path="helpers/logging/app.py"
            ),
            ChangedFileFactory.build(
                new_path="src/orders/domain.py", old_path="src/orders/domain.py"
            ),
        ]
    )

    # Declaration order, not file order.
    assert mr.affected_modules(MODULES_CONFIG) == [
        "src/orders",
        "helpers/logging",
    ]


def test_affected_modules_deduplicates_files_in_same_module():
    mr = MergeRequestFactory.build(
        files=[
            ChangedFileFactory.build(new_path="src/engine/a.py", old_path="src/engine/a.py"),
            ChangedFileFactory.build(new_path="src/engine/b.py", old_path="src/engine/b.py"),
        ]
    )

    assert mr.affected_modules(MODULES_CONFIG) == ["src/engine"]


def test_affected_modules_deletion_resolves_via_old_path():
    mr = MergeRequestFactory.build(
        files=[ChangedFileFactory.build(new_path="/dev/null", old_path="src/engine/gone.py")]
    )

    assert mr.affected_modules(MODULES_CONFIG) == ["src/engine"]


def test_affected_modules_cross_module_move_attributed_to_both():
    mr = MergeRequestFactory.build(
        files=[
            ChangedFileFactory.build(new_path="src/engine/moved.py", old_path="src/orders/moved.py")
        ]
    )

    assert mr.affected_modules(MODULES_CONFIG) == [
        "src/orders",
        "src/engine",
    ]


def test_affected_modules_ignores_paths_outside_declared_modules():
    mr = MergeRequestFactory.build(
        files=[ChangedFileFactory.build(new_path="README.md", old_path="README.md")]
    )

    assert mr.affected_modules(MODULES_CONFIG) == []


def test_affected_modules_overlapping_declarations_pick_most_specific():
    config = ReviewConfig(modules=["src", "src/orders"])
    mr = MergeRequestFactory.build(
        files=[
            ChangedFileFactory.build(
                new_path="src/orders/domain.py", old_path="src/orders/domain.py"
            )
        ]
    )

    assert mr.affected_modules(config) == ["src/orders"]


def test_affected_modules_empty_when_no_modules_declared():
    mr = MergeRequestFactory.build(
        files=[
            ChangedFileFactory.build(
                new_path="src/orders/domain.py", old_path="src/orders/domain.py"
            )
        ]
    )

    assert mr.affected_modules(ReviewConfig()) == []
