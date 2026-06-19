from src.review_engine.domain.models import AnalysisContext, CodeReview, MergeRequest
from src.review_engine.ports.outbound import LLMPort

from .dto import CodeReviewResponseDTO, CommentDTO
from .mappers import to_domain


class MockLLMClient(LLMPort):
    """Stand-in LLM used when ``config.test_mode`` is enabled.

    Returns a hardcoded review so the full pipeline (diff fetch -> review ->
    posting comments) can be exercised without spending tokens or needing a
    real provider key.
    """

    def generate_code_review(self, mr: MergeRequest, context: AnalysisContext) -> CodeReview:
        dto = CodeReviewResponseDTO(
            cohorts=[],
            business_requirements_matrix=[],
            code_review_comments=[
                CommentDTO(content="Dummy review comment.", links=[]),
            ],
        )
        return to_domain(dto)
