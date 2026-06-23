from src.review_engine.adapters.outbound.llm.dto import (
    BusinessRequirementDTO,
    CodeReviewResponseDTO,
    CohortChangeDTO,
    CohortDTO,
    CommentDTO,
    ReferenceDTO,
)
from src.review_engine.adapters.outbound.llm.mappers import to_domain
from src.review_engine.domain.models import ReferenceKind


def _response(comments: list[CommentDTO]) -> CodeReviewResponseDTO:
    cohort = CohortDTO(
        name="cohort-1",
        description="description",
        changes=[CohortChangeDTO(id=1, overview="overview")],
    )
    return CodeReviewResponseDTO(
        cohorts=[cohort],
        business_requirements_matrix=[
            BusinessRequirementDTO(requirement="req1", status="met", evidence="evidence")
        ],
        code_review_comments=comments,
    )


def test_map_dto_to_domain_object():
    comment = CommentDTO(content="comment-content", references=[])

    domain = to_domain(_response([comment]))

    assert domain
    assert domain.cohorts[0].change_ids == [1]
    assert domain.comments[0].references == []


def test_map_dto_to_domain_object__no_comments():
    domain = to_domain(_response([]))

    assert domain
    assert domain.cohorts[0].change_ids == [1]
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

    domain = to_domain(_response([comment]))

    assert len(domain.comments[0].references) == 1
