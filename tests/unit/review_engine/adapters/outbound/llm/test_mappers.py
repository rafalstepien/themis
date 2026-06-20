from src.review_engine.adapters.outbound.llm.dto import (
    BusinessRequirementDTO,
    CodeReviewResponseDTO,
    CohortChangeDTO,
    CohortDTO,
    CommentDTO,
)
from src.review_engine.adapters.outbound.llm.mappers import to_domain


def test_map_dto_to_domain_object():
    cohort_change = CohortChangeDTO(id=1, overview="overview")

    cohort = CohortDTO(
        name="cohort-1",
        description="description",
        changes=[cohort_change],
    )

    business_requirement = BusinessRequirementDTO(
        requirement="req1", status="met", evidence="evidence"
    )

    comment = CommentDTO(content="comment-content", links=["https://..."])

    dto = CodeReviewResponseDTO(
        cohorts=[cohort],
        business_requirements_matrix=[business_requirement],
        code_review_comments=[comment],
    )

    domain = to_domain(dto)

    assert domain
    assert domain.cohorts[0].change_ids == [1]


def test_map_dto_to_domain_object__no_comments():
    cohort_change = CohortChangeDTO(id=1, overview="overview")

    cohort = CohortDTO(
        name="cohort-1",
        description="description",
        changes=[cohort_change],
    )

    business_requirement = BusinessRequirementDTO(
        requirement="req1", status="met", evidence="evidence"
    )

    dto = CodeReviewResponseDTO(
        cohorts=[cohort],
        business_requirements_matrix=[business_requirement],
        code_review_comments=[],
    )

    domain = to_domain(dto)
    assert domain
    assert domain.cohorts[0].change_ids == [1]
