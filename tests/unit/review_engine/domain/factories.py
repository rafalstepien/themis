import factory

from src.review_engine.domain.models import (
    ChangedFile,
    CodeReview,
    Cohort,
    CommentAnchor,
    DiffRefs,
    MergeRequest,
    ReviewComment,
)


class DiffRefsFactory(factory.Factory[DiffRefs]):
    class Meta:
        model = DiffRefs

    base_sha = "base-sha"
    start_sha = "start-sha"
    head_sha = "head-sha"


class CommentAnchorFactory(factory.Factory[CommentAnchor]):
    class Meta:
        model = CommentAnchor

    new_path = "new-path"
    old_path = "old-path"
    new_line = 11
    old_line = None


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
    references = factory.LazyFunction(lambda: [])


class CodeReviewFactory(factory.Factory[CodeReview]):
    class Meta:
        model = CodeReview

    cohorts = factory.LazyFunction(lambda: [CohortFactory()])
    business_requirements_matrix = factory.LazyFunction(lambda: [])
    comments = factory.LazyFunction(lambda: [ReviewCommentFactory()])
