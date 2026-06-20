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
