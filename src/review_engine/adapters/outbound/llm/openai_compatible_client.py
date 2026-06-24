import logging

from openai import OpenAI

from src.review_engine.domain.models import AnalysisContext, CodeReview, MergeRequest
from src.review_engine.ports.outbound import LLMPort

from .dto import CodeReviewResponseDTO
from .exceptions import LLMResponseError, handle_llm_api_errors, handle_llm_data_errors
from .mappers import to_domain
from .prompt import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)

# Keyless servers (e.g. a self-hosted vLLM) ignore the key, but the OpenAI SDK
# still requires a non-empty one to build the client. "EMPTY" is the conventional
# placeholder used by the vLLM docs for exactly this case.
_PLACEHOLDER_API_KEY = "EMPTY"


class OpenAICompatibleClient(LLMPort):
    """Talks to any OpenAI-compatible server (self-hosted vLLM/LM Studio, or hosted OSS providers).

    Unlike :class:`OpenAIClient`, which uses the OpenAI-only Responses API, this
    adapter speaks the Chat Completions API that every compatible backend exposes.
    """

    def __init__(self, model: str, base_url: str, token: str | None = None):
        self.model = model
        self._client = OpenAI(base_url=base_url, api_key=token or _PLACEHOLDER_API_KEY)

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
            response = self._client.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=CodeReviewResponseDTO,
            )

        message = response.choices[0].message
        logger.debug("Raw LLM response content:\n%s", message.content)

        if message.refusal:
            raise LLMResponseError(f"LLM refused to respond: {message.refusal}")

        with handle_llm_data_errors():
            dto: CodeReviewResponseDTO | None = message.parsed

        if dto is None:
            raise LLMResponseError("LLM returned no parsable structured output.")

        logger.debug("Parsed LLM response DTO:\n%s", dto.model_dump_json(indent=2))
        logger.info(
            f"LLM responded with {len(dto.code_review_comments)} comments "
            f"and identified {len(dto.cohorts)} cohorts"
        )

        return dto
