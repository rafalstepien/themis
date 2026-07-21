from unittest.mock import Mock, patch

import pytest

from src.review_engine.adapters.outbound.gitlab.client import GitLabClient
from src.review_engine.domain.models import (
    CommentAnchor,
    DiffRefs,
    Reference,
    ReferenceKind,
    ReviewComment,
)


def test_format_body_without_references_is_just_content():
    comment = ReviewComment(content="A plain logic bug.", references=[])

    assert GitLabClient._format_body(comment) == "A plain logic bug."


def test_format_body_renders_rule_reference_with_path_and_rule_name():
    comment = ReviewComment(
        content="Use Money, not float.",
        references=[
            Reference(
                kind=ReferenceKind.RULE,
                module="catalog",
                rule="Represent money as integer minor units, never as float.",
            )
        ],
    )

    body = GitLabClient._format_body(comment)

    assert body == (
        "Use Money, not float.\n\n"
        "**References:**\n"
        "- `.themis-ai/rules/catalog/rule.json` "
        '— "Represent money as integer minor units, never as float."'
    )


def test_format_body_renders_architecture_reference_as_file_path_only():
    comment = ReviewComment(
        content="Bypasses the gateway.",
        references=[Reference(kind=ReferenceKind.ARCHITECTURE, module="orders")],
    )

    body = GitLabClient._format_body(comment)

    assert body == (
        "Bypasses the gateway.\n\n"
        "**References:**\n"
        "- `.themis-ai/architecture/orders/architecture.json`"
    )


def _client() -> GitLabClient:
    return GitLabClient(token="tok", project_id="42", mr_iid=7)


@patch("httpx.Client.post")
def test_post_general_comment_posts_to_notes_endpoint(mock_post):
    mock_post.return_value = Mock()

    _client().post_general_comment(ReviewComment(content="a finding", references=[]))

    url = mock_post.call_args.args[0]
    assert url.endswith("/projects/42/merge_requests/7/notes")
    assert mock_post.call_args.kwargs["json"] == {"body": "a finding"}


@patch("httpx.Client.post")
def test_post_inline_comment_builds_position_for_added_line(mock_post):
    mock_post.return_value = Mock()
    comment = ReviewComment(
        content="float price",
        references=[],
        anchor=CommentAnchor(new_path="a.py", old_path="a.py", new_line=11, old_line=None),
    )
    diff_refs = DiffRefs(base_sha="base", start_sha="start", head_sha="head")

    _client().post_inline_comment(comment, diff_refs)

    url = mock_post.call_args.args[0]
    assert url.endswith("/projects/42/merge_requests/7/discussions")
    payload = mock_post.call_args.kwargs["json"]
    assert payload["body"] == "float price"
    assert payload["position"] == {
        "position_type": "text",
        "base_sha": "base",
        "start_sha": "start",
        "head_sha": "head",
        "new_path": "a.py",
        "old_path": "a.py",
        "new_line": 11,
    }


@patch("httpx.Client.post")
def test_post_inline_comment_includes_old_line_for_context_line(mock_post):
    mock_post.return_value = Mock()
    comment = ReviewComment(
        content="context",
        references=[],
        anchor=CommentAnchor(new_path="a.py", old_path="a.py", new_line=10, old_line=10),
    )

    _client().post_inline_comment(comment, DiffRefs("base", "start", "head"))

    position = mock_post.call_args.kwargs["json"]["position"]
    assert position["new_line"] == 10
    assert position["old_line"] == 10


def test_post_inline_comment_requires_anchor():
    comment = ReviewComment(content="no anchor", references=[])

    with pytest.raises(ValueError):
        _client().post_inline_comment(comment, DiffRefs("base", "start", "head"))
