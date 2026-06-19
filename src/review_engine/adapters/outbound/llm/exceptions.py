from contextlib import contextmanager

import openai
import pydantic

from src.review_engine.ports.outbound.llm_port import LLMPortError


class LLMError(LLMPortError):
    """Base for all LLM adapter errors."""


class LLMAPIError(LLMError):
    """
    Raised when there is a problem reaching the LLM provider.
    """

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class LLMResponseError(LLMError):
    """
    Raised when the LLM responds with an unexpected or unparsable payload
    (refusal, schema violation, missing fields).
    """

    def __init__(self, message: str):
        super().__init__(message)


@contextmanager
def handle_llm_api_errors():
    try:
        yield
    except openai.APIStatusError as e:
        raise LLMAPIError(
            f"LLM provider returned HTTP {e.status_code}", status_code=e.status_code
        ) from e
    except openai.APIConnectionError as e:
        raise LLMAPIError("Could not reach the LLM provider") from e
    except openai.APIError as e:
        raise LLMAPIError("LLM provider returned an unexpected error") from e


@contextmanager
def handle_llm_data_errors():
    try:
        yield
    except pydantic.ValidationError as e:
        raise LLMResponseError(
            "LLM responded with unexpected format. Could not create a DTO."
        ) from e
