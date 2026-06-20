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


MODULES_CONFIG = ReviewConfig(modules=["services/payments", "services/booking", "webapps/boost"])


def _changed_file(new_path: str, old_path: str):
    return ChangedFileFactory.build(new_path=new_path, old_path=old_path)


def test_affected_modules_single_file_in_one_module():
    mr = MergeRequestFactory.build(
        files=[_changed_file("services/payments/domain.py", "services/payments/domain.py")]
    )

    assert mr.affected_modules(MODULES_CONFIG) == ["services/payments"]


def test_affected_modules_spans_multiple_modules_in_config_order():
    mr = MergeRequestFactory.build(
        files=[
            _changed_file("webapps/boost/app.py", "webapps/boost/app.py"),
            _changed_file("services/payments/domain.py", "services/payments/domain.py"),
        ]
    )

    # Declaration order, not file order.
    assert mr.affected_modules(MODULES_CONFIG) == [
        "services/payments",
        "webapps/boost",
    ]


def test_affected_modules_deduplicates_files_in_same_module():
    mr = MergeRequestFactory.build(
        files=[
            _changed_file("services/booking/a.py", "services/booking/a.py"),
            _changed_file("services/booking/b.py", "services/booking/b.py"),
        ]
    )

    assert mr.affected_modules(MODULES_CONFIG) == ["services/booking"]


def test_affected_modules_deletion_resolves_via_old_path():
    mr = MergeRequestFactory.build(files=[_changed_file("/dev/null", "services/booking/gone.py")])

    assert mr.affected_modules(MODULES_CONFIG) == ["services/booking"]


def test_affected_modules_cross_module_move_attributed_to_both():
    mr = MergeRequestFactory.build(
        files=[_changed_file("services/booking/moved.py", "services/payments/moved.py")]
    )

    assert mr.affected_modules(MODULES_CONFIG) == [
        "services/payments",
        "services/booking",
    ]


def test_affected_modules_ignores_paths_outside_declared_modules():
    mr = MergeRequestFactory.build(files=[_changed_file("README.md", "README.md")])

    assert mr.affected_modules(MODULES_CONFIG) == []


def test_affected_modules_overlapping_declarations_pick_most_specific():
    config = ReviewConfig(modules=["services", "services/payments"])
    mr = MergeRequestFactory.build(
        files=[_changed_file("services/payments/domain.py", "services/payments/domain.py")]
    )

    assert mr.affected_modules(config) == ["services/payments"]


def test_affected_modules_empty_when_no_modules_declared():
    mr = MergeRequestFactory.build(
        files=[_changed_file("services/payments/domain.py", "services/payments/domain.py")]
    )

    assert mr.affected_modules(ReviewConfig()) == []
