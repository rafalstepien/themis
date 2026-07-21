import pytest

from src.review_engine.domain.models import Change, CodeReview, Cohort, ReviewComment

EXPECTED_COMMENT_MARKDOWN = """# Overview of the changes in this MR

## Cohort 1: cohort-1
cohort-1-description

**CHANGES**

* `dummy/path1.py`: change-1-overview
* `dummy/path2.py`: change-2-overview


## Cohort 2: cohort-2
cohort-2-description

**CHANGES**

* `dummy/path3.py`: change-3-overview


"""


@pytest.mark.parametrize(
    ["cohorts", "expected_comment"],
    [
        pytest.param(
            [
                Cohort(
                    name="cohort-1",
                    description="cohort-1-description",
                    changes=[
                        Change(path="dummy/path1.py", overview="change-1-overview"),
                        Change(path="dummy/path2.py", overview="change-2-overview"),
                    ],
                ),
                Cohort(
                    name="cohort-2",
                    description="cohort-2-description",
                    changes=[
                        Change(path="dummy/path3.py", overview="change-3-overview"),
                    ],
                ),
            ],
            ReviewComment(content=EXPECTED_COMMENT_MARKDOWN, references=[], anchor=None),
            id="Happy path",
        ),
        pytest.param(
            [],
            None,
            id="Empty cohorts",
        ),
    ],
)
def test_build_cohort_comment(cohorts: list[Cohort], expected_comment: ReviewComment) -> None:
    cr = CodeReview(cohorts=cohorts, comments=[], business_requirements_matrix=[])

    assert cr.build_general_cohort_comment() == expected_comment
