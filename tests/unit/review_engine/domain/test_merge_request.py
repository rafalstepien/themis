from src.bootstrap.config import ReviewConfig
from tests.unit.review_engine.domain.factories import ChangedFileFactory, MergeRequestFactory

TEST_CONFIG = ReviewConfig(max_changed_files=2)


def test_should_be_reviewed_happy_path():
    mr = MergeRequestFactory.build()
    assert mr.should_be_reviewed(TEST_CONFIG)


def test_should_be_reviewed_happy_path_on_max():
    mr = MergeRequestFactory.build(
        files=[
            ChangedFileFactory.build(),
            ChangedFileFactory.build(),
        ]
    )

    assert mr.should_be_reviewed(TEST_CONFIG)


def test_should_be_reviewed_returns_false_when_files_array_empty():
    mr = MergeRequestFactory.build(files=[])
    assert not mr.should_be_reviewed(TEST_CONFIG)


def test_should_be_reviewed_returns_false_when_too_much_files_changed():
    mr = MergeRequestFactory.build(
        files=[
            ChangedFileFactory.build(),
            ChangedFileFactory.build(),
            ChangedFileFactory.build(),
        ]
    )
    assert not mr.should_be_reviewed(TEST_CONFIG)


MODULES_CONFIG = ReviewConfig(modules=["src/orders", "src/engine", "helpers/logging"])


def _changed_file(new_path: str, old_path: str):
    return ChangedFileFactory.build(new_path=new_path, old_path=old_path)


def test_affected_modules_single_file_in_one_module():
    mr = MergeRequestFactory.build(
        files=[_changed_file("src/orders/domain.py", "src/orders/domain.py")]
    )

    assert mr.affected_modules(MODULES_CONFIG) == ["src/orders"]


def test_affected_modules_spans_multiple_modules_in_config_order():
    mr = MergeRequestFactory.build(
        files=[
            _changed_file("helpers/logging/app.py", "helpers/logging/app.py"),
            _changed_file("src/orders/domain.py", "src/orders/domain.py"),
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
            _changed_file("src/engine/a.py", "src/engine/a.py"),
            _changed_file("src/engine/b.py", "src/engine/b.py"),
        ]
    )

    assert mr.affected_modules(MODULES_CONFIG) == ["src/engine"]


def test_affected_modules_deletion_resolves_via_old_path():
    mr = MergeRequestFactory.build(files=[_changed_file("/dev/null", "src/engine/gone.py")])

    assert mr.affected_modules(MODULES_CONFIG) == ["src/engine"]


def test_affected_modules_cross_module_move_attributed_to_both():
    mr = MergeRequestFactory.build(
        files=[_changed_file("src/engine/moved.py", "src/orders/moved.py")]
    )

    assert mr.affected_modules(MODULES_CONFIG) == [
        "src/orders",
        "src/engine",
    ]


def test_affected_modules_ignores_paths_outside_declared_modules():
    mr = MergeRequestFactory.build(files=[_changed_file("README.md", "README.md")])

    assert mr.affected_modules(MODULES_CONFIG) == []


def test_affected_modules_overlapping_declarations_pick_most_specific():
    config = ReviewConfig(modules=["src", "src/orders"])
    mr = MergeRequestFactory.build(
        files=[_changed_file("src/orders/domain.py", "src/orders/domain.py")]
    )

    assert mr.affected_modules(config) == ["src/orders"]


def test_affected_modules_empty_when_no_modules_declared():
    mr = MergeRequestFactory.build(
        files=[_changed_file("src/orders/domain.py", "src/orders/domain.py")]
    )

    assert mr.affected_modules(ReviewConfig()) == []
