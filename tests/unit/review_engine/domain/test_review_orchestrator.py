import logging
from unittest.mock import Mock

import pytest

from src.bootstrap.config import ReviewConfig
from src.review_engine.domain.models import MRComment, MRCommentAuthor, MRComments, TokenOwner
from src.review_engine.domain.review_orchestrator import ReviewOrchestrator

from .factories import (
    CodeReviewFactory,
    CommentAnchorFactory,
    DiffRefsFactory,
    MergeRequestFactory,
    ReviewCommentFactory,
)


@pytest.fixture
def gitlab_client_mock() -> Mock:
    client = Mock()
    client.get_mr_comments.return_value = MRComments(comments=[])
    client.get_mr_data.return_value = MergeRequestFactory()
    return client


def test_execute__not_reviewable_mr(gitlab_client_mock: Mock):
    gitlab_client_mock.get_mr_data.return_value = MergeRequestFactory(files=[])

    llm_client_mock = Mock()

    o = ReviewOrchestrator(
        review_config=Mock(),
        gitlab_port=gitlab_client_mock,
        llm_port=llm_client_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
        module_context_port=Mock(),
    )

    o.execute()

    assert not llm_client_mock.generate_code_review.called
    assert not gitlab_client_mock.post_general_comment.called
    assert not gitlab_client_mock.post_inline_comment.called


def test_execute__unanchored_comments_posted_as_general(gitlab_client_mock: Mock):
    llm_client_mock = Mock()
    llm_client_mock.generate_code_review.return_value = CodeReviewFactory(
        comments=[ReviewCommentFactory(), ReviewCommentFactory()],
        cohorts=[],
    )

    o = ReviewOrchestrator(
        review_config=ReviewConfig(),
        gitlab_port=gitlab_client_mock,
        llm_port=llm_client_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
        module_context_port=Mock(),
    )

    o.execute()

    assert llm_client_mock.generate_code_review.call_count == 1
    assert gitlab_client_mock.post_general_comment.call_count == 2
    assert not gitlab_client_mock.post_inline_comment.called


def test_execute__anchored_comment_posted_inline_with_diff_refs(gitlab_client_mock: Mock):
    diff_refs = DiffRefsFactory()
    anchored = ReviewCommentFactory(anchor=CommentAnchorFactory())
    plain = ReviewCommentFactory()
    llm_client_mock = Mock()
    llm_client_mock.generate_code_review.return_value = CodeReviewFactory(
        comments=[anchored, plain], cohorts=[]
    )
    gitlab_client_mock.get_mr_data.return_value = MergeRequestFactory(diff_refs=diff_refs)

    o = ReviewOrchestrator(
        review_config=ReviewConfig(),
        gitlab_port=gitlab_client_mock,
        llm_port=llm_client_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
        module_context_port=Mock(),
    )

    o.execute()

    gitlab_client_mock.post_inline_comment.assert_called_once_with(anchored, diff_refs)
    gitlab_client_mock.post_general_comment.assert_called_once_with(plain)


def test_execute__review_with_no_comments(gitlab_client_mock: Mock):
    llm_client_mock = Mock()
    llm_client_mock.generate_code_review.return_value = CodeReviewFactory(comments=[], cohorts=[])

    o = ReviewOrchestrator(
        review_config=ReviewConfig(),
        gitlab_port=gitlab_client_mock,
        llm_port=llm_client_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
        module_context_port=Mock(),
    )

    o.execute()

    assert llm_client_mock.generate_code_review.call_count == 1
    assert not gitlab_client_mock.post_general_comment.called
    assert not gitlab_client_mock.post_inline_comment.called


def test_execute__does_not_rerun_code_review_when_already_present(gitlab_client_mock: Mock, caplog):
    llm_client_mock = Mock()
    gitlab_client_mock.get_token_owner_details.return_value = TokenOwner(
        id=100001, username="username", name="User Name", email="username@example.com"
    )
    mr_comment_author = MRCommentAuthor(
        id=100001,
        username="username",
        name="User Name",
    )
    gitlab_client_mock.get_mr_comments.return_value = MRComments(
        comments=[MRComment(id=12345, system=False, author=mr_comment_author)]
    )

    o = ReviewOrchestrator(
        review_config=ReviewConfig(),
        gitlab_port=gitlab_client_mock,
        llm_port=llm_client_mock,
        business_context_port=Mock(),
        best_practices_port=Mock(),
        module_context_port=Mock(),
    )

    with caplog.at_level(logging.INFO):
        o.execute()

    llm_client_mock.assert_not_called()
    assert "Code review was already executed. Exiting ..." in caplog.text
