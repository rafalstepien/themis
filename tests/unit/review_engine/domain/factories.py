import factory

from src.review_engine.domain.models import (
    ChangedFile,
    CodeReview,
    Cohort,
    MergeRequest,
    ReviewComment,
)


class ChangedFileFactory(factory.Factory[ChangedFile]):
    class Meta:
        model = ChangedFile

    change_id = 1
    new_path = "new-path"
    old_path = "old-path"
    new_content = "new-content"
    old_content = "old-content"
    raw_diff = "+2312 -342"


class MergeRequestFactory(factory.Factory[MergeRequest]):
    class Meta:
        model = MergeRequest

    mr_id = 1
    source_branch = "source-branch"
    target_branch = "target-branch"
    title = "title"
    description = "description"
    files = factory.LazyFunction(lambda: [ChangedFileFactory()])


class CohortFactory(factory.Factory[Cohort]):
    class Meta:
        model = Cohort

    name = "cohort-1"
    description = "cohort-description"
    change_ids = factory.LazyFunction(lambda: [1])


class ReviewCommentFactory(factory.Factory[ReviewComment]):
    class Meta:
        model = ReviewComment

    content = "content"
    links = factory.LazyFunction(lambda: ["https://..."])


class CodeReviewFactory(factory.Factory[CodeReview]):
    class Meta:
        model = CodeReview

    cohorts = factory.LazyFunction(lambda: [CohortFactory()])
    business_requirements_matrix = factory.LazyFunction(lambda: [])
    comments = factory.LazyFunction(lambda: [ReviewCommentFactory()])
