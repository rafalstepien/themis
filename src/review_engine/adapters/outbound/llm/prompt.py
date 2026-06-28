"""Prompt construction for the LLM code-review call.

The prompt is intentionally flexible: the same response schema (cohorts +
business requirements matrix + code review comments) is always requested, but
the *instructions* and the *context* shift depending on what is available. In
particular the business requirements matrix is only produced when business /
ticket context is supplied (i.e. a Jira token was provided); otherwise the
model is told to leave it empty.
"""

import json

from src.review_engine.domain.diff_hunks import DiffLineKind, parse_diff
from src.review_engine.domain.models import AnalysisContext, MergeRequest

_LINE_MARKERS = {
    DiffLineKind.ADDED: "+",
    DiffLineKind.REMOVED: "-",
    DiffLineKind.CONTEXT: " ",
}

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
- Use correct markdown formatting for comment content

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

Each comment must, in its `content`:
- Name the specific file and describe the problem concisely
- Explain the risk or consequence and suggest a concrete fix
- Cite its grounding in `references` when the problem violates a rule or \
architecture contract you were given (see "references" below)

**Anchoring (`file_path` + `line`).** Pin each comment to the exact changed line \
it is about so it can be posted inline:
- Set `file_path` to that file's path exactly as shown in its `[change_id=...]` header.
- Set `line` to the number in the left gutter of the offending line in the \
annotated diff. Gutter numbers are new-file line numbers; only added (`+`) and \
context (` `) lines have one. Copy the number — do not count or guess.
- A removed (`-`) line has no gutter number; if the problem is fundamentally \
about a deletion (no nearby added/context line captures it), leave `file_path` \
and `line` as null and it will be posted as a general comment.
- Anchor to the most relevant single line. If a comment spans a file rather than \
a line, leave both null.

**One comment per problem.** Each distinct problem gets exactly ONE comment. Do \
NOT file several comments describing the same underlying issue from different \
angles — consolidate them into a single comment that names the root cause. Two \
comments are duplicates when fixing one would resolve the other (e.g. "imports \
catalog directly", "instantiates a concrete repository", and "bypasses the \
gateway" are usually one architectural violation, not three).

Only raise a comment when it adds real value. When in doubt, stay silent.
Use an empty list when there are none.

### references — how to cite

`references` grounds a comment in this repo's own documented context. NEVER \
invent URLs or links, and only cite context that was actually provided to you \
in this prompt. Each reference is exactly one of:

- A violated learned rule (from the "Rules learned from past merge requests" section):
  { "kind": "rule", "module": "<the rule's module>", "rule": "<the rule text, copied VERBATIM>" }
- A violated architecture contract (from the "Architecture rules" section):
  { "kind": "architecture", "module": "<the module>" }   (no "rule" field — cite the whole file, not a section)

Copy `module` and `rule` exactly as shown in those sections. If a comment is not \
grounded in any provided rule or architecture contract (e.g. a plain logic bug), \
return an empty `references` list for that comment.

**Good comment example (architecture violation):**
{
  "content": "`orders/domain/services.py` imports and instantiates `CatalogService` directly, creating a hard dependency from the orders domain into catalog and bypassing the outbound ports and anti-corruption layer. Reserve stock through an injected port realized by a catalog gateway adapter instead.",
  "references": [ { "kind": "architecture", "module": "orders" } ],
  "file_path": "src/orders/domain/services.py",
  "line": 42
}

**Good comment example (rule violation):**
{
  "content": "`price` is held as a float here; currency arithmetic on floats accumulates rounding errors in totals and tax. Use the shared Money value object (integer minor units).",
  "references": [ { "kind": "rule", "module": "catalog", "rule": "Represent money as integer minor units, never as float." } ],
  "file_path": "src/catalog/domain/pricing.py",
  "line": 17
}

**Bad comment example (do NOT produce):**
{ "content": "Consider renaming `amt` to `amount` for clarity." }   ← linter/style nit, out of scope
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
        sections += ["", "# Architecture rules", _format_architecture(context.architecture_rules)]
    if context.past_mr_rules:
        sections += [
            "",
            "# Rules learned from past merge requests",
            _format_rules(context.past_mr_rules),
        ]
    if context.best_practices_context:
        sections += ["", "# Best practices", _format_mapping(context.best_practices_context)]
    if context.business_context:
        sections += ["", "# Business / ticket context", context.business_context]

    return "\n".join(sections)


def _format_files(mr: MergeRequest) -> str:
    blocks: list[str] = []
    for f in mr.files:
        blocks.append(
            f"## [change_id={f.change_id}] {f.new_path}\n"
            "Left gutter = new-file line number (cite it as `line`).\n"
            f"```\n{_annotate_diff(f.raw_diff)}\n```"
        )
    return "\n\n".join(blocks)


def _annotate_diff(raw_diff: str) -> str:
    """Render a unified diff with a new-file line-number gutter on each line.

    The gutter gives the model a number to copy into a comment's ``line``
    instead of counting hunk offsets itself. Added/context lines show their
    new-file number; removed lines show none (they cannot be anchored).
    """
    rendered: list[str] = []
    for line in parse_diff(raw_diff):
        gutter = "" if line.new_line is None else str(line.new_line)
        rendered.append(f"{gutter:>5} {_LINE_MARKERS[line.kind]}{line.content}")
    return "\n".join(rendered)


def _format_architecture(architecture: dict) -> str:
    """Render each module's architecture contract under a citable module header."""
    blocks: list[str] = []
    for module, payload in architecture.items():
        blocks.append(f"## Module: {module}\n```json\n{json.dumps(payload, indent=2)}\n```")
    return "\n\n".join(blocks)


def _format_rules(rules: dict) -> str:
    """Render each module's learned rules verbatim so the model can cite them exactly."""
    blocks: list[str] = []
    for module, payload in rules.items():
        lines = [f"## Module: {module}"]
        rule_items = payload.get("rules") if isinstance(payload, dict) else None
        if rule_items:
            for item in rule_items:
                rule = item.get("rule", "")
                severity = item.get("severity")
                header = f'- "{rule}" ({severity})' if severity else f'- "{rule}"'
                lines.append(header)
                if item.get("reason"):
                    lines.append(f"  Why: {item['reason']}")
        else:
            lines.append(f"```json\n{json.dumps(payload, indent=2)}\n```")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _format_mapping(mapping: dict) -> str:
    return "\n".join(f"- {key}: {value}" for key, value in mapping.items())
