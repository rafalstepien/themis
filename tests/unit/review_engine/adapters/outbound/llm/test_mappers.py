from src.review_engine.adapters.outbound.llm.dto import (
    BusinessRequirementDTO,
    CodeReviewResponseDTO,
    CohortChangeDTO,
    CohortDTO,
    CommentDTO,
    ReferenceDTO,
)
from src.review_engine.adapters.outbound.llm.mappers import to_domain
from src.review_engine.domain.models import Change, MergeRequest, ReferenceKind
from tests.unit.review_engine.domain.factories import ChangedFileFactory, MergeRequestFactory

# A diff whose new file is `src/catalog/pricing.py` with a context line at new
# line 10 and an added line at new line 11.
_ANCHOR_DIFF = "@@ -10,1 +10,2 @@\n unchanged\n+price = 1.5\n"


def _response(comments: list[CommentDTO]) -> CodeReviewResponseDTO:
    cohort = CohortDTO(
        name="cohort-1",
        description="description",
        changes=[CohortChangeDTO(path="dummy/path1.py", overview="overview")],
    )
    return CodeReviewResponseDTO(
        cohorts=[cohort],
        business_requirements_matrix=[
            BusinessRequirementDTO(requirement="req1", status="met", evidence="evidence")
        ],
        code_review_comments=comments,
    )


def _mr() -> MergeRequest:
    return MergeRequestFactory.build(
        files=[
            ChangedFileFactory.build(
                new_path="src/catalog/pricing.py",
                old_path="src/catalog/pricing.py",
                raw_diff=_ANCHOR_DIFF,
            )
        ]
    )


def test_map_dto_to_domain_object():
    comment = CommentDTO(content="comment-content", references=[])

    domain = to_domain(_response([comment]), _mr())

    assert domain
    assert domain.cohorts[0].changes == [Change(path="dummy/path1.py", overview="overview")]
    assert domain.comments[0].references == []
    assert domain.comments[0].anchor is None


def test_map_dto_to_domain_object__no_comments():
    domain = to_domain(_response([]), _mr())

    assert domain
    assert domain.cohorts[0].changes == [Change(path="dummy/path1.py", overview="overview")]
    assert domain.comments == []


def test_rule_and_architecture_references_are_mapped():
    comment = CommentDTO(
        content="content",
        references=[
            ReferenceDTO(kind="rule", module="catalog", rule="Use Money, not float."),
            ReferenceDTO(kind="architecture", module="orders"),
        ],
    )

    domain = to_domain(
        _response([comment]),
        _mr(),
        rule_modules={"catalog"},
        architecture_modules={"orders"},
    )

    rule_ref, arch_ref = domain.comments[0].references
    assert rule_ref.kind is ReferenceKind.RULE
    assert rule_ref.rule == "Use Money, not float."
    assert rule_ref.file_path == ".themis-ai/rules/catalog/rule.json"
    assert arch_ref.kind is ReferenceKind.ARCHITECTURE
    assert arch_ref.rule is None
    assert arch_ref.file_path == ".themis-ai/architecture/orders/architecture.json"


def test_references_to_unloaded_modules_are_dropped():
    comment = CommentDTO(
        content="content",
        references=[
            ReferenceDTO(kind="rule", module="ghost", rule="Invented rule."),
            ReferenceDTO(kind="architecture", module="ghost"),
            ReferenceDTO(kind="rule", module="catalog", rule="Real rule."),
        ],
    )

    domain = to_domain(
        _response([comment]),
        _mr(),
        rule_modules={"catalog"},
        architecture_modules={"orders"},
    )

    references = domain.comments[0].references
    assert len(references) == 1
    assert references[0].module == "catalog"


def test_references_not_filtered_when_known_modules_absent():
    comment = CommentDTO(
        content="content",
        references=[ReferenceDTO(kind="rule", module="anything", rule="kept")],
    )

    domain = to_domain(_response([comment]), _mr())

    assert len(domain.comments[0].references) == 1


def test_anchor_resolved_for_added_line():
    comment = CommentDTO(
        content="float price", references=[], file_path="src/catalog/pricing.py", line=11
    )

    anchor = to_domain(_response([comment]), _mr()).comments[0].anchor

    assert anchor is not None
    assert anchor.new_path == "src/catalog/pricing.py"
    assert anchor.new_line == 11
    assert anchor.old_line is None


def test_anchor_resolved_for_context_line_carries_both_line_numbers():
    comment = CommentDTO(
        content="nearby", references=[], file_path="src/catalog/pricing.py", line=10
    )

    anchor = to_domain(_response([comment]), _mr()).comments[0].anchor

    assert anchor is not None
    assert anchor.new_line == 10
    assert anchor.old_line == 10


def test_anchor_dropped_when_line_is_not_a_changed_line():
    comment = CommentDTO(
        content="off-diff", references=[], file_path="src/catalog/pricing.py", line=999
    )

    anchor = to_domain(_response([comment]), _mr()).comments[0].anchor

    assert anchor is None


def test_anchor_dropped_when_file_not_in_diff():
    comment = CommentDTO(content="ghost file", references=[], file_path="src/unknown.py", line=11)

    anchor = to_domain(_response([comment]), _mr()).comments[0].anchor

    assert anchor is None


def test_anchor_none_when_line_or_path_missing():
    comment = CommentDTO(content="no anchor", references=[], file_path="src/catalog/pricing.py")

    anchor = to_domain(_response([comment]), _mr()).comments[0].anchor

    assert anchor is None
