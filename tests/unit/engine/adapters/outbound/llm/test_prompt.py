import json

import pytest

from src.engine.adapters.outbound.llm.dto import CodeReviewResponseDTO
from src.engine.adapters.outbound.llm.prompt import (
    _annotate_diff,
    build_system_prompt,
    build_user_prompt,
)
from src.engine.domain.models import AnalysisContext
from tests.unit.engine.domain.factories import ChangedFileFactory, MergeRequestFactory


def test_annotate_diff_puts_new_file_line_numbers_in_the_gutter():
    raw = "@@ -10,1 +10,2 @@\n unchanged\n+added\n-removed\n"

    annotated = _annotate_diff(raw)

    assert annotated.splitlines() == [
        "   10  unchanged",
        "   11 +added",
        "      -removed",
    ]


def test_build_user_prompt_renders_change_header_and_gutter():
    mr = MergeRequestFactory.build(
        files=[
            ChangedFileFactory.build(
                new_path="src/catalog/pricing.py",
                raw_diff="@@ -1,0 +1,1 @@\n+price = 1.5\n",
            )
        ]
    )

    prompt = build_user_prompt(mr, AnalysisContext())

    assert "## src/catalog/pricing.py" in prompt
    assert "    1 +price = 1.5" in prompt


@pytest.mark.parametrize("has_business_context", [True, False])
def test_system_prompt_embeds_the_response_schema(has_business_context: bool):
    # Given / When
    prompt = build_system_prompt(has_business_context)

    # Then the schema the parser validates against is spelled out for the model
    schema = json.dumps(CodeReviewResponseDTO.model_json_schema())
    assert "## Output format" in prompt
    assert schema in prompt


def test_system_prompt_cohort_example_uses_schema_field_names():
    # The cohort example must match `CohortChangeDTO`, otherwise models copy the
    # wrong key and fail validation.
    prompt = build_system_prompt(has_business_context=False)

    assert '"id":' not in prompt
    assert '"path": "src/dtos/order_item_dto.py"' in prompt


def test_user_prompt_ends_with_output_format_reminder():
    prompt = build_user_prompt(MergeRequestFactory.build(), AnalysisContext())

    assert prompt.rstrip().endswith("JSON only, no surrounding text.")
