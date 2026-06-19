import logging

from openai import OpenAI

from src.review_engine.domain.models import AnalysisContext, CodeReview, MergeRequest
from src.review_engine.ports.outbound import LLMPort

from .dto import CodeReviewResponseDTO
from .exceptions import LLMResponseError, handle_llm_api_errors, handle_llm_data_errors
from .mappers import to_domain
from .prompt import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)


class OpenAIClient(LLMPort):
    def __init__(self, model: str, token: str):
        self.model = model
        self._client = OpenAI(api_key=token)

    def generate_code_review(self, mr: MergeRequest, context: AnalysisContext) -> CodeReview:
        dto = self._request_review(mr, context)
        return to_domain(dto)

    def _request_review(self, mr: MergeRequest, context: AnalysisContext) -> CodeReviewResponseDTO:
        has_business_context = context.business_context is not None

        with handle_llm_api_errors():
            response = self._client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": build_system_prompt(has_business_context)},
                    {"role": "user", "content": build_user_prompt(mr, context)},
                ],
                text_format=CodeReviewResponseDTO,
            )

        with handle_llm_data_errors():
            dto = response.output_parsed

        if dto is None:
            raise LLMResponseError("LLM returned no parsable structured output (possible refusal).")

        return dto
