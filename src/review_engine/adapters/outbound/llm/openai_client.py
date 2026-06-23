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
        return to_domain(
            dto,
            rule_modules=set(context.past_mr_rules or {}),
            architecture_modules=set(context.architecture_rules or {}),
        )

    def _request_review(self, mr: MergeRequest, context: AnalysisContext) -> CodeReviewResponseDTO:
        has_business_context = context.business_context is not None

        system_prompt = build_system_prompt(has_business_context)
        user_prompt = build_user_prompt(mr, context)

        logger.info("Sending review request to LLM model %s", self.model)
        logger.debug(
            "LLM request payload:\n"
            "----- SYSTEM PROMPT -----\n%s\n"
            "----- USER PROMPT -----\n%s\n"
            "----- END -----",
            system_prompt,
            user_prompt,
        )

        with handle_llm_api_errors():
            response = self._client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                text_format=CodeReviewResponseDTO,
            )

        logger.debug("Raw LLM response output_text:\n%s", getattr(response, "output_text", None))

        with handle_llm_data_errors():
            dto: CodeReviewResponseDTO | None = response.output_parsed

        if dto is None:
            raise LLMResponseError("LLM returned no parsable structured output (possible refusal).")

        logger.debug("Parsed LLM response DTO:\n%s", dto.model_dump_json(indent=2))
        logger.info(
            f"LLM responded with {len(dto.code_review_comments)} comments and identified {len(dto.cohorts)} cohorts"
        )

        return dto
