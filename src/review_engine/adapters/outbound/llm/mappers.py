from src.review_engine.domain.models import (
    CodeReview,
    Cohort,
    Reference,
    ReferenceKind,
    ReviewComment,
)

from .dto import CodeReviewResponseDTO, CommentDTO


def to_domain(
    dto: CodeReviewResponseDTO,
    rule_modules: set[str] | None = None,
    architecture_modules: set[str] | None = None,
) -> CodeReview:
    """Map the LLM response DTO into the domain ``CodeReview``."""
    cohorts = [
        Cohort(
            name=c.name, description=c.description, change_ids=[change.id for change in c.changes]
        )
        for c in dto.cohorts
    ]

    return CodeReview(
        cohorts=cohorts,
        business_requirements_matrix=[r.model_dump() for r in dto.business_requirements_matrix],
        comments=[
            ReviewComment(
                content=c.content,
                references=_to_references(c, rule_modules, architecture_modules),
            )
            for c in dto.code_review_comments
        ],
    )


def _to_references(
    comment: CommentDTO,
    rule_modules: set[str] | None,
    architecture_modules: set[str] | None,
) -> list[Reference]:
    """
    Ensures that the references listed by LLM are coming from correct
    modules and are not made up.
    """
    references: list[Reference] = []
    for ref in comment.references:
        kind = ReferenceKind(ref.kind)
        if kind is ReferenceKind.RULE:
            if rule_modules is not None and ref.module not in rule_modules:
                continue
            references.append(Reference(kind=kind, module=ref.module, rule=ref.rule))
        else:
            if architecture_modules is not None and ref.module not in architecture_modules:
                continue
            references.append(Reference(kind=kind, module=ref.module, rule=None))
    return references
