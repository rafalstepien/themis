"""Provider-agnostic parsing of the LLM's code-review answer.

Native structured output (``response_format`` with a JSON schema) is not
honoured the same way by every OpenAI-compatible provider — Anthropic's
compatibility layer, for example, does not enforce the schema. Instead of
relying on it, the prompt asks for a bare JSON object and this module pulls
that object out of whatever text the model actually returned, tolerating the
usual deviations:

- a Markdown code fence around the JSON (```json ... ```),
- prose before or after the JSON ("Here is the review: {...}"),
- reasoning blocks emitted by thinking models (``<think>...</think>``).

The extracted object is then validated against ``CodeReviewResponseDTO``.
"""

import json
import re

import pydantic

from .dto import CodeReviewResponseDTO
from .exceptions import LLMResponseError

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_CODE_FENCE = re.compile(r"```(?:json|JSON)?\s*\n?(.*?)```", re.DOTALL)

# Keys identifying the review object among other JSON objects in the text
# ("parameters" covers models that answer in a tool-call-like envelope).
_EXPECTED_TOP_LEVEL_KEYS = {*CodeReviewResponseDTO.model_fields, "parameters"}

# How much of the raw answer to echo back in an error message.
_SNIPPET_LENGTH = 200


def parse_code_review(content: str | None) -> CodeReviewResponseDTO:
    """Extract and validate the code-review JSON object from a raw LLM answer.

    Raises ``LLMResponseError`` when no JSON object can be found or when the
    object does not match ``CodeReviewResponseDTO``. The error message is
    descriptive enough to be fed back to the model for a repair attempt.
    """
    payload = extract_json_object(content)
    try:
        return CodeReviewResponseDTO.model_validate(payload)
    except pydantic.ValidationError as e:
        raise LLMResponseError(
            "LLM response JSON does not match the expected schema: " + _describe(e)
        ) from e


def extract_json_object(content: str | None) -> dict:
    """Return the first JSON object found in ``content``.

    Candidates are tried from most to least specific: the whole answer, the
    content of each Markdown code fence, then every ``{`` in the text as the
    start of an embedded object.
    """
    if not content or not content.strip():
        raise LLMResponseError("LLM returned an empty response.")

    text = _THINK_BLOCK.sub("", content).strip()

    for candidate in (text, *_CODE_FENCE.findall(text)):
        parsed = _loads_object(candidate.strip())
        if parsed is not None:
            return parsed

    embedded = _first_embedded_object(text)
    if embedded is not None:
        return embedded

    raise LLMResponseError(
        f"LLM response does not contain a JSON object. Response starts with: {_snippet(content)!r}"
    )


def _loads_object(candidate: str) -> dict | None:
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _first_embedded_object(text: str) -> dict | None:
    """Find the review object embedded in surrounding text.

    Every ``{`` is tried as a start position. An object carrying one of the
    review's top-level keys wins over any other, so that a truncated answer is
    not mistaken for one of its own nested objects (e.g. a single cohort).
    """
    decoder = json.JSONDecoder()
    fallback: dict | None = None
    start = text.find("{")
    while start != -1:
        try:
            parsed, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
            continue
        if isinstance(parsed, dict):
            if _EXPECTED_TOP_LEVEL_KEYS & parsed.keys():
                return parsed
            fallback = fallback or parsed
        # Skip past the decoded value; objects nested inside it are not candidates.
        start = text.find("{", end)
    return fallback


def _describe(error: pydantic.ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in err['loc']) or '<root>'}: {err['msg']}"
        for err in error.errors(include_url=False)
    )


def _snippet(content: str) -> str:
    return content[:_SNIPPET_LENGTH] + ("..." if len(content) > _SNIPPET_LENGTH else "")
