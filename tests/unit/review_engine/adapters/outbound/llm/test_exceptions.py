import httpx
import openai
import pytest

from src.review_engine.adapters.outbound.llm.exceptions import LLMAPIError, handle_llm_api_errors


def _response(status_code: int) -> httpx.Response:
    request = httpx.Request("POST", "https://provider.test/v1/chat/completions")
    return httpx.Response(status_code, request=request)


def test_authentication_error_points_at_the_token() -> None:
    with pytest.raises(LLMAPIError) as exc_info:
        with handle_llm_api_errors():
            raise openai.AuthenticationError("Unauthorized", response=_response(401), body=None)

    assert exc_info.value.status_code == 401
    assert "LLM_API_TOKEN" in str(exc_info.value)


def test_permission_denied_points_at_the_token() -> None:
    with pytest.raises(LLMAPIError) as exc_info:
        with handle_llm_api_errors():
            raise openai.PermissionDeniedError("Forbidden", response=_response(403), body=None)

    assert exc_info.value.status_code == 403
    assert "LLM_API_TOKEN" in str(exc_info.value)


def test_other_status_errors_keep_a_plain_message() -> None:
    with pytest.raises(LLMAPIError) as exc_info:
        with handle_llm_api_errors():
            raise openai.NotFoundError("Missing", response=_response(404), body=None)

    assert exc_info.value.status_code == 404
    assert "404" in str(exc_info.value)
    assert "LLM_API_TOKEN" not in str(exc_info.value)
