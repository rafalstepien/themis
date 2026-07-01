import pytest

from src.review_engine.domain.models import Change, CodeReview, Cohort, ReviewComment

EXPECTED_COMMENT_MARKDOWN = """# Overview of the changes in this MR

## Cohort 1: cohort-1
cohort-1-description

CHANGES:
<1>: change-1-overview
<2>: change-2-overview


## Cohort 2: cohort-2
cohort-2-description

CHANGES:
<3>: change-3-overview


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
                        Change(id=1, overview="change-1-overview"),
                        Change(id=2, overview="change-2-overview"),
                    ],
                ),
                Cohort(
                    name="cohort-2",
                    description="cohort-2-description",
                    changes=[
                        Change(id=3, overview="change-3-overview"),
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
