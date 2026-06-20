"""Prompt construction for the LLM code-review call.

The prompt is intentionally flexible: the same response schema (cohorts +
business requirements matrix + code review comments) is always requested, but
the *instructions* and the *context* shift depending on what is available. In
particular the business requirements matrix is only produced when business /
ticket context is supplied (i.e. a Jira token was provided); otherwise the
model is told to leave it empty.
"""

from src.review_engine.domain.models import AnalysisContext, MergeRequest

_SYSTEM_PROMPT_BASE = """\
You are a Senior Staff Software Engineer performing a code review of a merge request.

## Your mission

Give high-signal, actionable feedback. Stay silent on trivia.
Focus exclusively on:
- Logic bugs
- Security vulnerabilities
- Architectural violations
- Broken domain/business rules

Do NOT comment on formatting, naming style, or anything a linter already catches.

Notes:
- Every file must appear in exactly one cohort, referenced by its numeric change_id.
- Return cohorts in the order a reviewer should read them — root cause first, downstream effects \
 after.
- The `overview` per file must describe what happened in that file, not repeat the cohort \
description.
- Omit code_review_comments from the JSON if there are none (use an empty list).

---

## Cohorts — detailed rules

The purpose of cohorts is to make the reviewer's job easier by grouping related changes and \
establishing a reading order.

**Ordering rule:** Surface the origin of the change first.
If a change in a DTO/interface/contract causes cascading changes downstream, the DTO file \
comes first — in its own cohort or at the top of a cohort — so the reviewer understands \
the "why" before seeing the "what".

**Good cohort example:**

Input files:
  [change_id=1] src/dtos/order_item_dto.py  — added `discount_amount` field
  [change_id=2] src/services/pricing_service.py — reads new field, applies discount
  [change_id=3] src/api/orders_router.py — exposes discount in response schema
  [change_id=4] tests/test_pricing_service.py — unit tests for discount logic

Good output:
{
  "cohorts": [
    {
      "name": "Contract change",
      "description": "The DTO is the origin of this change. Review this first to understand what new data is flowing through the system.",
      "changes": [
        { "id": 1, "overview": "Adds `discount_amount: Decimal` to OrderItemDTO. This is the root cause of all downstream changes in this MR." }
      ]
    },
    {
      "name": "Business logic",
      "description": "Core discount calculation added to the pricing layer. Depends on the contract change above.",
      "changes": [
        { "id": 2, "overview": "Implements discount deduction in `calculate_total()`. Check rounding mode and whether negative discounts are guarded." },
        { "id": 4, "overview": "Unit tests covering happy path and zero-discount edge case. Missing test for discount > item price." }
      ]
    },
    {
      "name": "API surface",
      "description": "Exposes the new field to API consumers. Review last — only makes sense after understanding the contract and logic.",
      "changes": [
        { "id": 3, "overview": "Response schema now includes `discount_amount`. Verify the field is not accidentally exposed in contexts where discounts aren't applicable." }
      ]
    }
  ]
}

**Bad cohort (avoid):**
- One mega-cohort containing every file — gives the reviewer no guidance.
- Cohort description that just restates the file list without explaining the relationship.
- Reading order that puts the API router before the DTO that caused the change.

## code_review_comments — detailed rules

Each comment must:
- Identify the specific file and line range (if known)
- Describe the problem concisely
- Explain the risk or consequence
- Suggest a concrete fix or point to relevant documentation

Only raise a comment when it adds real value. When in doubt, stay silent.
Use an empty list when there are none.

**Good comment example:**
{
  "file": "src/services/pricing_service.py",
  "lines": "42-45",
  "severity": "bug",
  "comment": "`total -= discount_amount` does not guard against `discount_amount > total`, which can produce a negative order total. Add `discount_amount = min(discount_amount, total)` before subtraction.",
}

**Bad comment example (do NOT produce):**
{
  "comment": "Consider renaming `amt` to `amount` for clarity."  ← linter/style nit, out of scope
}
"""

_MATRIX_INSTRUCTION_ENABLED = """\
3. business_requirements_matrix — for each business requirement found in the \
provided business/ticket context, state the requirement, whether the change \
meets it (status), and the evidence from the diff supporting that verdict.
"""

_MATRIX_INSTRUCTION_DISABLED = """\
3. business_requirements_matrix — no business/ticket context was provided for \
this review, so you MUST return an empty list here.
"""


def build_system_prompt(has_business_context: bool) -> str:
    matrix = _MATRIX_INSTRUCTION_ENABLED if has_business_context else _MATRIX_INSTRUCTION_DISABLED
    return f"{_SYSTEM_PROMPT_BASE}\n{matrix}"


def build_user_prompt(mr: MergeRequest, context: AnalysisContext) -> str:
    """Assemble the user prompt from the merge request and whatever context exists."""
    sections: list[str] = [
        "# Merge Request",
        f"Title: {mr.title}",
        f"Description:\n{mr.description or '(no description)'}",
        "",
        "# Changed files",
        _format_files(mr),
    ]

    if context.architecture_rules:
        sections += ["", "# Architecture rules", _format_mapping(context.architecture_rules)]
    if context.past_mr_rules:
        sections += [
            "",
            "# Rules learned from past merge requests",
            _format_mapping(context.past_mr_rules),
        ]
    if context.best_practices_context:
        sections += ["", "# Best practices", _format_mapping(context.best_practices_context)]
    if context.business_context:
        sections += ["", "# Business / ticket context", context.business_context]

    return "\n".join(sections)


def _format_files(mr: MergeRequest) -> str:
    blocks: list[str] = []
    for f in mr.files:
        blocks.append(f"## [change_id={f.change_id}] {f.new_path}\n```diff\n{f.raw_diff}\n```")
    return "\n\n".join(blocks)


def _format_mapping(mapping: dict) -> str:
    return "\n".join(f"- {key}: {value}" for key, value in mapping.items())
