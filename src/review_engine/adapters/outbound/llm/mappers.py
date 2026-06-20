from src.review_engine.domain.models import CodeReview, Cohort, ReviewComment

from .dto import CodeReviewResponseDTO


def to_domain(dto: CodeReviewResponseDTO) -> CodeReview:
    cohorts = []
    for c in dto.cohorts:
        cohort = Cohort(
            name=c.name, description=c.description, change_ids=[change.id for change in c.changes]
        )
        cohorts.append(cohort)

    return CodeReview(
        cohorts=cohorts,
        business_requirements_matrix=[r.model_dump() for r in dto.business_requirements_matrix],
        comments=[
            ReviewComment(content=c.content, links=c.links) for c in dto.code_review_comments
        ],
    )
