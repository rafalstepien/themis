from src.review_engine.domain.models import CodeReview, Cohort, ReviewComment

from .dto import CodeReviewResponseDTO


def to_domain(dto: CodeReviewResponseDTO) -> CodeReview:
    return CodeReview(
        cohorts=[
            Cohort(name=c.name, description=c.description, change_ids=c.change_ids)
            for c in dto.cohorts
        ],
        business_requirements_matrix=dto.business_requirements_matrix,
        comments=[
            ReviewComment(content=c.content, links=c.links) for c in dto.code_review_comments
        ],
    )
