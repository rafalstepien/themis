from src.review_engine.domain.models import AnalysisContext, CodeReview, MergeRequest
from src.review_engine.ports.outbound import LLMPort

from .dto import CodeReviewResponseDTO, CommentDTO
from .mappers import to_domain


class OpenAIClient(LLMPort):
    def __init__(self, token: str): ...

    def generate_code_review(self, mr: MergeRequest, context: AnalysisContext) -> CodeReview:
        dto = CodeReviewResponseDTO(
            cohorts=[],
            business_requirements_matrix=[],
            code_review_comments=[
                CommentDTO(content="Dummy review comment.", links=[]),
            ],
        )
        return to_domain(dto)
