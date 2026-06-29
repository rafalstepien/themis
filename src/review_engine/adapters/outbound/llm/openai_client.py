import logging

from openai import OpenAI

from .dto import CodeReviewResponseDTO
from .exceptions import handle_llm_api_errors, handle_llm_data_errors
from .structured_output_llm_client import _StructuredOutputLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(_StructuredOutputLLMClient):
    def __init__(self, model: str, token: str | None):
        super().__init__(model)
        self._client = OpenAI(api_key=token)

    def _request_with_structured_output(
        self, user_prompt: str, system_prompt: str
    ) -> CodeReviewResponseDTO | None:
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

        return dto
