import json

import pytest

from src.engine.adapters.outbound.llm.exceptions import LLMResponseError
from src.engine.adapters.outbound.llm.output_parser import (
    extract_json_object,
    parse_code_review,
)

_VALID = {
    "cohorts": [
        {
            "name": "Contract change",
            "description": "Root cause.",
            "changes": [{"path": "src/dto.py", "overview": "Adds a field."}],
        }
    ],
    "business_requirements_matrix": [],
    "code_review_comments": [
        {
            "content": "**Problem:** bug.",
            "references": [],
            "file_path": "src/dto.py",
            "line": 3,
        }
    ],
}
_VALID_JSON = json.dumps(_VALID)


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(_VALID_JSON, id="bare-json"),
        pytest.param(f"```json\n{_VALID_JSON}\n```", id="json-code-fence"),
        pytest.param(f"```\n{_VALID_JSON}\n```", id="plain-code-fence"),
        pytest.param(f"Here is my review:\n\n{_VALID_JSON}\n\nLet me know!", id="prose-around"),
        pytest.param(f"Sure!\n```json\n{_VALID_JSON}\n```\nDone.", id="prose-and-fence"),
        pytest.param(f"<think>I should use {{braces}}.</think>\n{_VALID_JSON}", id="think-block"),
        pytest.param(json.dumps(_VALID, indent=2), id="pretty-printed"),
    ],
)
def test_parse_code_review_accepts_common_provider_output_shapes(raw: str) -> None:
    # Given a response wrapped the way various providers tend to wrap JSON
    # When it is parsed
    dto = parse_code_review(raw)

    # Then the full review is recovered
    assert dto.cohorts[0].changes[0].path == "src/dto.py"
    assert dto.code_review_comments[0].line == 3


def test_parse_code_review_unwraps_tool_call_style_parameters() -> None:
    # Given a model that nests the answer under "parameters" (seen with some providers)
    raw = json.dumps({"parameters": _VALID})

    # When / Then it still parses
    assert len(parse_code_review(raw).code_review_comments) == 1


def test_parse_code_review_accepts_empty_review() -> None:
    raw = '{"cohorts": [], "business_requirements_matrix": [], "code_review_comments": []}'

    dto = parse_code_review(raw)

    assert dto.code_review_comments == []


def test_parse_code_review_reports_missing_fields_by_name() -> None:
    # Given the empty object Anthropic returned under `response_format` (issue #35)
    # When it is parsed / Then the error names every missing key so the model can fix it
    with pytest.raises(LLMResponseError) as exc_info:
        parse_code_review("{}")

    message = str(exc_info.value)
    assert "cohorts" in message
    assert "business_requirements_matrix" in message
    assert "code_review_comments" in message


@pytest.mark.parametrize("raw", [None, "", "   \n"])
def test_extract_json_object_rejects_empty_response(raw: str | None) -> None:
    with pytest.raises(LLMResponseError, match="empty"):
        extract_json_object(raw)


def test_extract_json_object_rejects_text_without_json() -> None:
    with pytest.raises(LLMResponseError, match="does not contain a JSON object"):
        extract_json_object("I cannot review this merge request.")


def test_parse_code_review_rejects_truncated_json() -> None:
    # Given an answer cut off mid-object, whose nested objects are still complete
    truncated = _VALID_JSON[: _VALID_JSON.index('"business_requirements_matrix"')]

    # When / Then a nested object is not mistaken for the review
    with pytest.raises(LLMResponseError, match="cohorts"):
        parse_code_review(truncated)


def test_extract_json_object_prefers_the_review_over_other_objects() -> None:
    # Given an unrelated JSON example preceding the actual review
    raw = 'For example {"note": "ignored"} and the review: ' + _VALID_JSON

    # When / Then
    assert extract_json_object(raw) == _VALID


def test_extract_json_object_skips_braces_that_are_not_json() -> None:
    # Given prose that contains a non-JSON brace before the real object
    raw = "Consider `f(x) {return x}` — anyway, the review: " + _VALID_JSON

    # When / Then the real object is found
    assert extract_json_object(raw) == _VALID
