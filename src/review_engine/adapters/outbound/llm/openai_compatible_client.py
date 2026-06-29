import logging

from openai import OpenAI

from .dto import CodeReviewResponseDTO
from .exceptions import LLMResponseError, handle_llm_api_errors, handle_llm_data_errors
from .structured_output_llm_client import _StructuredOutputLLMClient

logger = logging.getLogger(__name__)


# Keyless servers (e.g. a self-hosted vLLM) ignore the key, but the OpenAI SDK
# still requires a non-empty one to build the client. "EMPTY" is the conventional
# placeholder used by the vLLM docs for exactly this case.
_PLACEHOLDER_API_KEY = "EMPTY"


class OpenAICompatibleClient(_StructuredOutputLLMClient):
    """Talks to any OpenAI-compatible server (self-hosted vLLM/LM Studio, or hosted OSS providers).

    Defined as specialized client as it uses completions API and not standard responses API.
    """

    def __init__(self, model: str, base_url: str, token: str | None = None):
        super().__init__(model)
        self._client = OpenAI(base_url=base_url, api_key=token or _PLACEHOLDER_API_KEY)

    def _request_with_structured_output(
        self, user_prompt: str, system_prompt: str
    ) -> CodeReviewResponseDTO | None:
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

        return dto
