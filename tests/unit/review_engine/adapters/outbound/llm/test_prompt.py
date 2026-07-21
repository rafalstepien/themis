from src.review_engine.adapters.outbound.llm.prompt import _annotate_diff, build_user_prompt
from src.review_engine.domain.models import AnalysisContext
from tests.unit.review_engine.domain.factories import ChangedFileFactory, MergeRequestFactory


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
