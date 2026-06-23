from src.review_engine.adapters.outbound.gitlab.client import GitLabClient
from src.review_engine.domain.models import Reference, ReferenceKind, ReviewComment


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
