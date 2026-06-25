from src.review_engine.domain.models import AnalysisContext, CodeReview, MergeRequest
from src.review_engine.ports.outbound import LLMPort

from .dto import CodeReviewResponseDTO, CommentDTO
from .mappers import to_domain


class MockLLMClient(LLMPort):
    """

    Used when ``config.test_mode`` is enabled to not burn tokens in testing phase.
    Responds with dummy code review comment.
    """

    def generate_code_review(self, mr: MergeRequest, context: AnalysisContext) -> CodeReview:
        dto = CodeReviewResponseDTO(
            cohorts=[],
            business_requirements_matrix=[],
            code_review_comments=[
                CommentDTO(content="Dummy review comment.", references=[]),
            ],
        )
        return to_domain(dto, mr)
