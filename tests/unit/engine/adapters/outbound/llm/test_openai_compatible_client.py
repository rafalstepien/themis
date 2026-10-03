import json
from typing import Any, cast
from unittest.mock import Mock, patch

import pytest

from src.engine.adapters.outbound.llm.exceptions import (
    LLMConfigurationError,
    LLMResponseError,
)
from src.engine.adapters.outbound.llm.openai_compatible_client import (
    OpenAICompatibleClient,
)
from src.engine.domain.models import AnalysisContext, MergeRequest
from tests.unit.engine.domain.factories import MergeRequestFactory

_BASE_URL = "http://localhost:11434/v1"
BASE_CLIENT_PARAMS: dict[str, Any] = {
    "model": "qwen2.5-coder",
    "base_url": _BASE_URL,
    "max_tokens": 32_000,
    "reasoning_effort": "minimal",
    "token": "token",
}
TEST_CLIENT = OpenAICompatibleClient(**BASE_CLIENT_PARAMS, max_repair_attempts=1)
TEST_MR: MergeRequest = cast(MergeRequest, MergeRequestFactory())
TEST_ANALYSIS_CONTEXT = AnalysisContext()
TEST_COMMENT_CONTENT = "This is some comment."

TEST_JSON_CODE_REVIEW_RESPONSE = json.dumps(
    {
        "cohorts": [],
        "business_requirements_matrix": [],
        "code_review_comments": [{"content": TEST_COMMENT_CONTENT, "references": []}],
    }
)


def _wrap_in_completions_response(
    message_content: str, refusal: str | None = None, finish_reason: str | None = None
) -> Mock:
    return Mock(
        choices=[
            Mock(
                message=Mock(content=message_content, refusal=refusal),
                finish_reason=finish_reason,
            )
        ]
    )


def test_generate_code_review_maps_handles_clean_json() -> None:
    # Given: Provider responding with regular, clean JSON
    with patch(
        "openai.resources.chat.completions.Completions.create",
        return_value=_wrap_in_completions_response(TEST_JSON_CODE_REVIEW_RESPONSE),
    ):
        review = TEST_CLIENT.generate_code_review(TEST_MR, TEST_ANALYSIS_CONTEXT)

    # Then: This JSON is parsed to domain object correctly
    assert review.comments[0].content == TEST_COMMENT_CONTENT


def test_generate_code_review_handles_json_with_additional_llm_text() -> None:
    # Given: Provider adding some filler words instead of returning clean JSON

    response_with_filler_words = (
        f"Here is the review:\n```json\n{TEST_JSON_CODE_REVIEW_RESPONSE}\n```"
    )
    with patch(
        "openai.resources.chat.completions.Completions.create",
        return_value=_wrap_in_completions_response(response_with_filler_words),
    ):
        review = TEST_CLIENT.generate_code_review(TEST_MR, TEST_ANALYSIS_CONTEXT)

    # Then: This response is parsed to domain object correctly
    assert review.comments[0].content == TEST_COMMENT_CONTENT


def test_request_does_not_rely_on_provider_response_format() -> None:
    with patch(
        "openai.resources.chat.completions.Completions.create",
        return_value=_wrap_in_completions_response(TEST_JSON_CODE_REVIEW_RESPONSE),
    ) as create_request:
        # When: Requesting the provider
        TEST_CLIENT.generate_code_review(TEST_MR, TEST_ANALYSIS_CONTEXT)

    # Then: We do not pass the schema as an OpenAI param
    _, kwargs = create_request.call_args
    assert "response_format" not in kwargs


def test_unparsable_response_is_repaired_with_a_follow_up_turn() -> None:
    # Given: LLM responds with wrong format for the first time
    first_response = _wrap_in_completions_response("{}")
    second_response = _wrap_in_completions_response(TEST_JSON_CODE_REVIEW_RESPONSE)

    # When: We enter the repair loop
    with patch(
        "openai.resources.chat.completions.Completions.create",
        side_effect=[first_response, second_response],
    ) as create_request:
        review = TEST_CLIENT.generate_code_review(TEST_MR, TEST_ANALYSIS_CONTEXT)

    # Then: If LLM corrects itself, the response is parsed sucesfully in the second turn
    assert review.comments[0].content == TEST_COMMENT_CONTENT
    assert create_request.call_count == 2
    repair_messages = create_request.call_args_list[1].kwargs["messages"]
    assert [m["role"] for m in repair_messages] == [
        "system",
        "user",
        "assistant",
        "user",
    ]


def test_still_unparsable_after_repair_raises_response_error() -> None:
    # Given: LLM responds with wrong format two times
    first_response = _wrap_in_completions_response("Bad model")
    second_response = _wrap_in_completions_response("Very bad model!!!")

    # When: We exceed the repair attempts limit
    with (
        pytest.raises(LLMResponseError),
        patch(
            "openai.resources.chat.completions.Completions.create",
            side_effect=[first_response, second_response],
        ) as create_request,
    ):
        TEST_CLIENT.generate_code_review(TEST_MR, TEST_ANALYSIS_CONTEXT)

    # Then: LLM was called two times, but raised LLMResponseError in both cases
    assert create_request.call_count == 2


def test_repair_can_be_disabled() -> None:
    # Given: LLM client configured without repair attempts
    client = OpenAICompatibleClient(**BASE_CLIENT_PARAMS, max_repair_attempts=0)

    # When: Client responds with wrong format
    with (
        pytest.raises(LLMResponseError),
        patch(
            "openai.resources.chat.completions.Completions.create",
            return_value=_wrap_in_completions_response("Bad model"),
        ) as create_request,
    ):
        client.generate_code_review(TEST_MR, TEST_ANALYSIS_CONTEXT)

    # Then: Error is raised, and no repair attempt is made
    assert create_request.call_count == 1


def test_negative_repair_raises() -> None:
    # Given: LLM client configured with negative repair attempts
    with pytest.raises(LLMConfigurationError):
        # When: Instantiating the client
        OpenAICompatibleClient(**BASE_CLIENT_PARAMS, max_repair_attempts=-1)
        # Then: Client creation fails


def test_refusal_raises_response_error_without_repair_attempt() -> None:
    # Given: LLM response contains refusal
    with (
        pytest.raises(LLMResponseError),
        patch(
            "openai.resources.chat.completions.Completions.create",
            return_value=_wrap_in_completions_response("Bad model", refusal="I cannot help."),
        ) as create_request,
    ):
        TEST_CLIENT.generate_code_review(TEST_MR, TEST_ANALYSIS_CONTEXT)

    # Then: No repair attempt is made
    assert create_request.call_count == 1


def test_truncated_response_raises_actionable_error_without_repair() -> None:
    # Given: LLM response cut off by the output token limit
    with (
        pytest.raises(LLMResponseError) as e,
        patch(
            "openai.resources.chat.completions.Completions.create",
            return_value=_wrap_in_completions_response('{"cohorts": [', finish_reason="length"),
        ) as create_request,
    ):
        TEST_CLIENT.generate_code_review(TEST_MR, TEST_ANALYSIS_CONTEXT)

    error_message = e.value.args[0]

    # Then: Error with actionable message is raised
    assert create_request.call_count == 1
    assert (
        error_message
        == "LLM response was cut off by the token limit. Increase the token limit or reduce the review size."
    )


def test_none_response_raises_response_error() -> None:
    with (
        pytest.raises(LLMResponseError),
        patch(
            "openai.resources.chat.completions.Completions.create",
            return_value=_wrap_in_completions_response(None),  # type: ignore
        ),
    ):
        TEST_CLIENT.generate_code_review(TEST_MR, TEST_ANALYSIS_CONTEXT)
