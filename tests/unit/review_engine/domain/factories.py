import factory

from src.review_engine.domain.models import (
    Change,
    ChangedFile,
    ChangeType,
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


RAW_DIFF_EXAMPLE = """
diff --git a/.themis-ai/config.yaml b/.themis-ai/config.yaml
index 3f6c1d056419a08f56ba9108e27521f55e9437c8..16f07efd7039c4fdf968ad591a57da7fbb93a0bc 100644
--- a/.themis-ai/config.yaml
+++ b/.themis-ai/config.yaml
@@ -10,7 +10,8 @@ review:
     - src/payments
 
 llm:
-  provider: openai
+  deployment_type: cloud
   model: gpt-5-nano
+  base_url: https://api.openai.com/v1
 
 test_mode: false
"""


EXAMPLE_DIFF_WITH_SIX_LINES_CHANGED = """
--- a/.themis-ai/config.yaml
+++ b/.themis-ai/config.yaml
@@ -10,7 +10,8 @@ review:
     - src/payments
 
 llm:
-  provider: openai
+  deployment_type: cloud
+  deployment_type: cloud
+  deployment_type: cloud
+  deployment_type: cloud
   model: gpt-5-nano
+  base_url: https://api.openai.com/v1
"""


class ChangedFileFactory(factory.Factory[ChangedFile]):
    class Meta:
        model = ChangedFile

    new_path = "new-path"
    old_path = "old-path"
    raw_diff = RAW_DIFF_EXAMPLE
    change_type = ChangeType.MODIFIED
    too_large = False
    generated_file = False


class MergeRequestFactory(factory.Factory[MergeRequest]):
    class Meta:
        model = MergeRequest

    mr_id = 1
    source_branch = "source-branch"
    target_branch = "target-branch"
    title = "title"
    description = "description"
    files = factory.LazyFunction(lambda: [ChangedFileFactory()])


class CohortChangeFactory(factory.Factory[Change]):
    class Meta:
        model = Change

    id = 1
    overview = "overview"


class CohortFactory(factory.Factory[Cohort]):
    class Meta:
        model = Cohort

    name = "cohort-1"
    description = "cohort-description"
    changes = factory.LazyFunction(lambda: [CohortChangeFactory()])


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
