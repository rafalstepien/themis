from typing import cast
from unittest.mock import Mock

import pytest

from src.review_engine.adapters.outbound.llm.dto import CodeReviewResponseDTO, CommentDTO
from src.review_engine.adapters.outbound.llm.exceptions import LLMResponseError
from src.review_engine.adapters.outbound.llm.openai_compatible_client import OpenAICompatibleClient
from src.review_engine.domain.models import AnalysisContext, MergeRequest
from tests.unit.review_engine.domain.factories import MergeRequestFactory

_BASE_URL = "http://localhost:11434/v1"


def _merge_request() -> MergeRequest:
    # factory-boy's typing does not narrow the call to the model type.
    return cast(MergeRequest, MergeRequestFactory())


def _dto(comment_content: str) -> CodeReviewResponseDTO:
    return CodeReviewResponseDTO(
        cohorts=[],
        business_requirements_matrix=[],
        code_review_comments=[CommentDTO(content=comment_content, references=[])],
    )


def _stub_response(parsed: CodeReviewResponseDTO | None, refusal: str | None = None) -> Mock:
    message = Mock(parsed=parsed, refusal=refusal, content="raw-content")
    return Mock(choices=[Mock(message=message)])


def _client_returning(response: Mock) -> OpenAICompatibleClient:
    mock_client = Mock()
    mock_client.chat.completions.parse.return_value = response
    client = OpenAICompatibleClient(model="qwen2.5-coder", base_url=_BASE_URL)
    client._client = mock_client
    return client


def test_generate_code_review_maps_parsed_dto_to_domain() -> None:
    client = _client_returning(_stub_response(_dto("A real bug.")))

    review = client.generate_code_review(_merge_request(), AnalysisContext())

    assert review.comments[0].content == "A real bug."


def test_request_asks_for_structured_output_via_chat_completions() -> None:
    parse = Mock(return_value=_stub_response(_dto("x")))
    mock_client = Mock()
    mock_client.chat.completions.parse = parse
    client = OpenAICompatibleClient(model="qwen2.5-coder", base_url=_BASE_URL)
    client._client = mock_client

    client.generate_code_review(_merge_request(), AnalysisContext())

    _, kwargs = parse.call_args
    assert kwargs["response_format"] is CodeReviewResponseDTO
    assert [message["role"] for message in kwargs["messages"]] == ["system", "user"]


def test_refusal_raises_response_error() -> None:
    client = _client_returning(_stub_response(None, refusal="I cannot help."))

    with pytest.raises(LLMResponseError):
        client.generate_code_review(_merge_request(), AnalysisContext())


def test_missing_parsed_output_raises_response_error() -> None:
    client = _client_returning(_stub_response(None))

    with pytest.raises(LLMResponseError):
        client.generate_code_review(_merge_request(), AnalysisContext())
