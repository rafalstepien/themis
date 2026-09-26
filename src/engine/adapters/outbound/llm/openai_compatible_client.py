import logging

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from .dto import CodeReviewResponseDTO
from .exceptions import LLMResponseError, handle_llm_api_errors
from .output_parser import parse_code_review
from .structured_output_llm_client import _StructuredOutputLLMClient

logger = logging.getLogger(__name__)


# Keyless servers (e.g. a self-hosted vLLM) ignore the key, but the OpenAI SDK
# still requires a non-empty one to build the client. "EMPTY" is the conventional
# placeholder used by the vLLM docs for exactly this case.
_PLACEHOLDER_API_KEY = "EMPTY"

# How many times the model is asked to fix an answer that could not be parsed.
# One is enough in practice: a model that ignored the format once almost always
# complies when shown the concrete parsing error.
_DEFAULT_MAX_REPAIR_ATTEMPTS = 1

_REPAIR_PROMPT = """\
Your previous response could not be parsed: {error}

Reply again with ONLY the complete, corrected JSON object described in the \
Output format section. Keep your review content; fix only the format. No \
prose, no code fences."""


class OpenAICompatibleClient(_StructuredOutputLLMClient):
    """
    Talks to any OpenAI-compatible server (self-hosted vLLM/LM Studio, or hosted OSS providers).

    The expected JSON shape is requested in the prompt and parsed from the plain
    text answer rather than through ``response_format``, because providers do not
    enforce JSON schemas consistently (Anthropic's compatibility layer ignores it).
    This keeps the behaviour identical across OpenAI, xAI, Gemini, Anthropic and
    self-hosted servers.
    """

    def __init__(
        self,
        model: str,
        base_url: str | None,
        token: str | None = None,
        max_repair_attempts: int = _DEFAULT_MAX_REPAIR_ATTEMPTS,
    ):
        super().__init__(model)
        self._client = OpenAI(base_url=base_url, api_key=token or _PLACEHOLDER_API_KEY)
        self._max_repair_attempts = max_repair_attempts

    def _request_with_structured_output(
        self, user_prompt: str, system_prompt: str
    ) -> CodeReviewResponseDTO | None:
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(self._max_repair_attempts + 1):
            content = self._complete(messages)
            try:
                return parse_code_review(content)
            except LLMResponseError as e:
                if attempt == self._max_repair_attempts:
                    raise
                logger.warning(
                    "LLM response could not be parsed (%s); asking the model to repair it "
                    "(attempt %d of %d).",
                    e,
                    attempt + 1,
                    self._max_repair_attempts,
                )
                messages = [
                    *messages,
                    {"role": "assistant", "content": content or ""},
                    {"role": "user", "content": _REPAIR_PROMPT.format(error=e)},
                ]

        return None  # unreachable: the loop either returns or raises

    def _complete(self, messages: list[ChatCompletionMessageParam]) -> str | None:
        with handle_llm_api_errors():
            response = self._client.chat.completions.create(model=self.model, messages=messages)

        choice = response.choices[0]
        message = choice.message
        logger.debug("Raw LLM response content:\n%s", message.content)

        refusal = getattr(message, "refusal", None)
        if refusal:
            raise LLMResponseError(f"LLM refused to respond: {refusal}")

        if choice.finish_reason == "length":
            # A truncated answer cannot be repaired by asking again with the same
            # budget, so fail loudly with an actionable message instead.
            raise LLMResponseError(
                "LLM response was cut off by the provider's output token limit before "
                "the JSON was complete. Reduce the review size (review.max_changed_files / "
                "review.max_changed_lines_per_file) or use a model with a larger output limit."
            )

        return message.content
