from abc import ABC, abstractmethod
import logging

from openai import OpenAI

from src.review_engine.domain.models import AnalysisContext, CodeReview, MergeRequest
from src.review_engine.ports.outbound import LLMPort

from .dto import CodeReviewResponseDTO
from .exceptions import LLMResponseError
from .mappers import to_domain
from .prompt import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)


class _StructuredOutputLLMClient(LLMPort, ABC):
    """Base for clients that request a structured code review from an LLM."""

    _client: OpenAI

    def __init__(self, model: str) -> None:
        self.model = model

    def generate_code_review(self, mr: MergeRequest, context: AnalysisContext) -> CodeReview:
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
        dto = self._request_with_structured_output(user_prompt, system_prompt)

        if dto is None:
            raise LLMResponseError("LLM returned no parsable structured output.")

        logger.debug("Parsed LLM response DTO:\n%s", dto.model_dump_json(indent=2))
        logger.info(
            f"LLM responded with {len(dto.code_review_comments)} comments "
            f"and identified {len(dto.cohorts)} cohorts"
        )

        return to_domain(
            dto=dto,
            mr=mr,
            rule_modules=set(context.past_mr_rules or {}),
            architecture_modules=set(context.architecture_rules or {}),
        )

    @abstractmethod
    def _request_with_structured_output(
        self, user_prompt: str, system_prompt: str
    ) -> CodeReviewResponseDTO | None: ...
