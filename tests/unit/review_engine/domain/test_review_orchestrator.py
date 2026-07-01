from unittest.mock import Mock

from src.bootstrap.config import ReviewConfig
from src.review_engine.domain.review_orchestrator import ReviewOrchestrator

from .factories import (
    CodeReviewFactory,
    CommentAnchorFactory,
    DiffRefsFactory,
    MergeRequestFactory,
    ReviewCommentFactory,
)


def test_execute__not_reviewable_mr():
    gitlab_port_mock = Mock()
    gitlab_port_mock.get_mr_data.return_value = MergeRequestFactory(files=[])

    llm_port_mock = Mock()

    o = ReviewOrchestrator(
        review_config=Mock(),
        gitlab_port=gitlab_port_mock,
        llm_port=llm_port_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
        module_context_port=Mock(),
    )

    o.execute()

    assert not llm_port_mock.generate_code_review.called
    assert not gitlab_port_mock.post_general_comment.called
    assert not gitlab_port_mock.post_inline_comment.called


def test_execute__unanchored_comments_posted_as_general():
    gitlab_port_mock = Mock()
    gitlab_port_mock.get_mr_data.return_value = MergeRequestFactory()

    llm_port_mock = Mock()
    llm_port_mock.generate_code_review.return_value = CodeReviewFactory(
        comments=[ReviewCommentFactory(), ReviewCommentFactory()],
        cohorts=[],
    )

    o = ReviewOrchestrator(
        review_config=ReviewConfig(),
        gitlab_port=gitlab_port_mock,
        llm_port=llm_port_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
        module_context_port=Mock(),
    )

    o.execute()

    assert llm_port_mock.generate_code_review.call_count == 1
    assert gitlab_port_mock.post_general_comment.call_count == 2
    assert not gitlab_port_mock.post_inline_comment.called


def test_execute__anchored_comment_posted_inline_with_diff_refs():
    diff_refs = DiffRefsFactory()
    gitlab_port_mock = Mock()
    gitlab_port_mock.get_mr_data.return_value = MergeRequestFactory(diff_refs=diff_refs)

    anchored = ReviewCommentFactory(anchor=CommentAnchorFactory())
    plain = ReviewCommentFactory()
    llm_port_mock = Mock()
    llm_port_mock.generate_code_review.return_value = CodeReviewFactory(
        comments=[anchored, plain], cohorts=[]
    )

    o = ReviewOrchestrator(
        review_config=ReviewConfig(),
        gitlab_port=gitlab_port_mock,
        llm_port=llm_port_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
        module_context_port=Mock(),
    )

    o.execute()

    gitlab_port_mock.post_inline_comment.assert_called_once_with(anchored, diff_refs)
    gitlab_port_mock.post_general_comment.assert_called_once_with(plain)


def test_execute__review_with_no_comments():
    gitlab_port_mock = Mock()
    gitlab_port_mock.get_mr_data.return_value = MergeRequestFactory()

    llm_port_mock = Mock()
    llm_port_mock.generate_code_review.return_value = CodeReviewFactory(comments=[], cohorts=[])

    o = ReviewOrchestrator(
        review_config=ReviewConfig(),
        gitlab_port=gitlab_port_mock,
        llm_port=llm_port_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
        module_context_port=Mock(),
    )

    o.execute()

    assert llm_port_mock.generate_code_review.call_count == 1
    assert not gitlab_port_mock.post_general_comment.called
    assert not gitlab_port_mock.post_inline_comment.called
