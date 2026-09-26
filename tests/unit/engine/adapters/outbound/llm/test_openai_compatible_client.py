import json
from typing import cast
from unittest.mock import Mock

import pytest

from src.engine.adapters.outbound.llm.exceptions import LLMResponseError
from src.engine.adapters.outbound.llm.openai_compatible_client import (
    OpenAICompatibleClient,
)
from src.engine.domain.models import AnalysisContext, MergeRequest
from tests.unit.engine.domain.factories import MergeRequestFactory

_BASE_URL = "http://localhost:11434/v1"


def _merge_request() -> MergeRequest:
    # factory-boy's typing does not narrow the call to the model type.
    return cast(MergeRequest, MergeRequestFactory())


def _review_json(comment_content: str) -> str:
    return json.dumps(
        {
            "cohorts": [],
            "business_requirements_matrix": [],
            "code_review_comments": [{"content": comment_content, "references": []}],
        }
    )


def _stub_response(
    content: str | None, refusal: str | None = None, finish_reason: str = "stop"
) -> Mock:
    message = Mock(content=content, refusal=refusal)
    return Mock(choices=[Mock(message=message, finish_reason=finish_reason)])


def _client_returning(*responses: Mock, max_repair_attempts: int = 1) -> tuple:
    create = Mock(side_effect=list(responses))
    mock_client = Mock()
    mock_client.chat.completions.create = create
    client = OpenAICompatibleClient(
        model="qwen2.5-coder", base_url=_BASE_URL, max_repair_attempts=max_repair_attempts
    )
    client._client = mock_client
    return client, create


def test_generate_code_review_maps_parsed_json_to_domain() -> None:
    # Given a provider answering with plain JSON
    client, _ = _client_returning(_stub_response(_review_json("A real bug.")))

    # When
    review = client.generate_code_review(_merge_request(), AnalysisContext())

    # Then
    assert review.comments[0].content == "A real bug."


def test_generate_code_review_parses_fenced_json_with_prose() -> None:
    # Given a provider (e.g. Anthropic) that wraps the JSON in prose and a code fence
    raw = f"Here is the review:\n```json\n{_review_json('Fenced.')}\n```"
    client, _ = _client_returning(_stub_response(raw))

    # When
    review = client.generate_code_review(_merge_request(), AnalysisContext())

    # Then
    assert review.comments[0].content == "Fenced."


def test_request_does_not_rely_on_provider_response_format() -> None:
    # Given
    client, create = _client_returning(_stub_response(_review_json("x")))

    # When
    client.generate_code_review(_merge_request(), AnalysisContext())

    # Then the schema travels in the prompt, not in `response_format`
    _, kwargs = create.call_args
    assert "response_format" not in kwargs
    assert [message["role"] for message in kwargs["messages"]] == ["system", "user"]
    assert '"code_review_comments"' in kwargs["messages"][0]["content"]


def test_unparsable_response_is_repaired_with_a_follow_up_turn() -> None:
    # Given a first answer missing every field, then a corrected one
    client, create = _client_returning(
        _stub_response("{}"),
        _stub_response(_review_json("Repaired.")),
    )

    # When
    review = client.generate_code_review(_merge_request(), AnalysisContext())

    # Then the model was shown its own answer plus the concrete parsing error
    assert review.comments[0].content == "Repaired."
    assert create.call_count == 2
    repair_messages = create.call_args_list[1].kwargs["messages"]
    assert [m["role"] for m in repair_messages] == ["system", "user", "assistant", "user"]
    assert repair_messages[2]["content"] == "{}"
    assert "code_review_comments" in repair_messages[3]["content"]


def test_still_unparsable_after_repair_raises_response_error() -> None:
    # Given a model that keeps answering in prose
    client, create = _client_returning(
        _stub_response("Looks good to me!"),
        _stub_response("Still looks good!"),
    )

    # When / Then
    with pytest.raises(LLMResponseError, match="does not contain a JSON object"):
        client.generate_code_review(_merge_request(), AnalysisContext())
    assert create.call_count == 2


def test_repair_can_be_disabled() -> None:
    client, create = _client_returning(_stub_response("{}"), max_repair_attempts=0)

    with pytest.raises(LLMResponseError):
        client.generate_code_review(_merge_request(), AnalysisContext())
    assert create.call_count == 1


def test_refusal_raises_response_error_without_repair() -> None:
    client, create = _client_returning(_stub_response(None, refusal="I cannot help."))

    with pytest.raises(LLMResponseError, match="refused"):
        client.generate_code_review(_merge_request(), AnalysisContext())
    assert create.call_count == 1


def test_truncated_response_raises_actionable_error_without_repair() -> None:
    # Given an answer cut off by the output token limit
    client, create = _client_returning(
        _stub_response('{"cohorts": [', finish_reason="length"),
    )

    # When / Then
    with pytest.raises(LLMResponseError, match="output token limit"):
        client.generate_code_review(_merge_request(), AnalysisContext())
    assert create.call_count == 1


def test_empty_response_raises_response_error() -> None:
    client, _ = _client_returning(_stub_response(None), _stub_response(""))

    with pytest.raises(LLMResponseError, match="empty"):
        client.generate_code_review(_merge_request(), AnalysisContext())
