from unittest.mock import Mock

from src.bootstrap.config import ReviewConfig
from src.review_engine.domain.review_orchestrator import ReviewOrchestrator

from .factories import CodeReviewFactory, MergeRequestFactory, ReviewCommentFactory


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
    )

    o.execute()

    assert not llm_port_mock.generate_code_review.called
    assert not gitlab_port_mock.post_comment.called


def test_execute__happy_path():
    gitlab_port_mock = Mock()
    gitlab_port_mock.get_mr_data.return_value = MergeRequestFactory()

    llm_port_mock = Mock()
    llm_port_mock.generate_code_review.return_value = CodeReviewFactory(
        comments=[ReviewCommentFactory(), ReviewCommentFactory()]
    )

    o = ReviewOrchestrator(
        review_config=ReviewConfig(),
        gitlab_port=gitlab_port_mock,
        llm_port=llm_port_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
    )

    o.execute()

    assert llm_port_mock.generate_code_review.call_count == 1
    assert gitlab_port_mock.post_comment.call_count == 2


def test_execute__review_with_no_comments():
    gitlab_port_mock = Mock()
    gitlab_port_mock.get_mr_data.return_value = MergeRequestFactory()

    llm_port_mock = Mock()
    llm_port_mock.generate_code_review.return_value = CodeReviewFactory(comments=[])

    o = ReviewOrchestrator(
        review_config=ReviewConfig(),
        gitlab_port=gitlab_port_mock,
        llm_port=llm_port_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
    )

    o.execute()

    assert llm_port_mock.generate_code_review.call_count == 1
    assert not gitlab_port_mock.post_comment.called
