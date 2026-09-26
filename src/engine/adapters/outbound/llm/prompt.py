"""Prompt construction for the LLM code-review call.

The prompt is intentionally flexible: the same response schema (cohorts +
business requirements matrix + code review comments) is always requested, but
the *instructions* and the *context* shift depending on what is available. In
particular the business requirements matrix is only produced when business /
ticket context is supplied (i.e. a Jira token was provided); otherwise the
model is told to leave it empty.
"""

import json

from src.engine.domain.diff_hunks import DiffLineKind, parse_diff
from src.engine.domain.models import AnalysisContext, MergeRequest

from .dto import CodeReviewResponseDTO

_LINE_MARKERS = {
    DiffLineKind.ADDED: "+",
    DiffLineKind.REMOVED: "-",
    DiffLineKind.CONTEXT: " ",
}


# region
_CODE_REVIEW_COMMENTS_SECTION = """\
## Code Review Comments
### High level goal of this section
Provide suggestions for the implementation to make it better, safer, more optimized.
Raise comments for things that are absent in the implementation, but should be there
(eg. when developer forgot to test some critical path, flow, user journey).

### Rules
  - When there are no additional comments to be made in the Merge Request, and the proposed changes are good enough, respond with empty code_review_comments list (`[]`)
  - Use correct markdown formatting for comment content.
  - Each comment must, in its `content`:
    - Name the specific file and describe the problem concisely
    - Explain the risk or consequence and suggest a concrete fix
    - Cite its grounding in `references` when the problem violates a rule or \
    architecture contract you were given (see "references" below)
  - **Anchoring (`file_path` + `line`).** Pin each comment to the exact changed line \
  it is about so it can be posted inline:
    - Set `file_path` to that file's path exactly.
    - Set `line` to the number in the left gutter of the offending line in the \
    annotated diff. Gutter numbers are new-file line numbers; only added (`+`) and \
    context (` `) lines have one. Copy the number — do not count or guess.
    - A removed (`-`) line has no gutter number; if the problem is fundamentally \
    about a deletion (no nearby added/context line captures it), leave `file_path` \
    and `line` as null and it will be posted as a general comment.
    - Anchor to the most relevant single line. If a comment spans a file rather than \
    a line, leave both null.

  - **One comment per problem.** Each distinct problem gets exactly ONE comment. Do \
    NOT file several comments describing the same underlying issue from different \
    angles — consolidate them into a single comment that names the root cause. Two \
    comments are duplicates when fixing one would resolve the other (e.g. "imports \
    catalog directly", "instantiates a concrete repository", and "bypasses the \
    gateway" are usually one architectural violation, not three).

  - Only raise a comment when it adds real value. When in doubt, stay silent.
  - Each comment should be formatted in Markdown. Wrap all code-related concepts (paths, classes, functions, variables, keywords) in backticks (\``). Use bold text for structural emphasis (e.g., **Problem:**), but strictly avoid using Markdown headers (# or ##) to ensure the comment remains compact and readable in a standard PR interface.


### Comment format template
[Problem] One concise sentence naming the issue.
[How it breaks] A step-by-step breakdown or concrete scenario of how the code fails in practice.
[Suggested Fix] description of the suggested fix, corrected code sample, or list of potential solutions to be considered in this scenario instead.


### Good comments examples
**Example 1: Hardcoded path**
```json
{
  "content": "**Problem:** The script hardcodes an absolute path tied to a specific user's local setup.\n**How it breaks:**\n* Another developer clones the repository into `~/projects/themis`.\n* They execute `scripts/run_github.sh`.\n* The script crashes with a `File not found` error because it is looking for your specific `~/repos/sandbox/...` directory.\n**The Fix:** Invoke the script using a relative path: `uv run main.py github`.",
  "file_path": "scripts/run_github.sh",
  "line": 1
}
```

**Example 2: Consecutive `if` statements**
```json
{
  "content": "**Problem:** Using consecutive `if` statements causes the program to incorrectly trigger the final `else` fallback block.\n**How it breaks (Example: `git_provider == \"gitlab\"`):**\n1. The first statement (`if git_provider == \"gitlab\"`) evaluates to `True`. `GitLabCLIAdapter` runs successfully.\n2. Execution continues to the next independent `if` statement.\n3. Because the provider is \"gitlab\", this second check evaluates to `False`.\n4. The code falls into the attached `else` block, incorrectly logging an error and crashing the app with `sys.exit(1)`.\n**The Fix:** Change `if git_provider == \"github\":` to `elif git_provider == \"github\":`.",
  "file_path": "src/themis/main.py",
  "line": 15
}
```
**Example 3: Architecture violation**
```json
{
  "content": "**Problem:** The `orders` domain imports and instantiates `CatalogService` directly, creating a hard dependency.\n**How it breaks:**\n* The `orders` domain becomes tightly coupled to `catalog`'s internal implementation.\n* It bypasses the anti-corruption layer, meaning any data model changes in `catalog` will directly bleed into and break `orders` logic.\n* If `CatalogService` changes its initialization, the `orders` domain fails to execute.\n**The Fix:** Reserve stock through an injected port realized by a catalog gateway adapter instead.",
  "references": [ { "kind": "architecture", "module": "orders" } ],
  "file_path": "src/orders/domain/services.py",
  "line": 42
}
```

**Example 4: Rule violation**
```json
{
  "content": "**Problem:** The `price` variable uses a `float` to represent a monetary value.\n**How it breaks:**\n* Floating-point math cannot precisely represent base-10 decimals (e.g., `0.1 + 0.2` evaluates to `0.30000000000000004`).\n* When calculating totals, taxes, or applying discounts, these micro-errors compound.\n* This leads to incorrect final customer charges or accounting mismatches in the database.\n**The Fix:** Use the shared `Money` value object (integer minor units).",
  "references": [ { "kind": "rule", "module": "catalog", "rule": "Represent money as integer minor units, never as float." } ],
  "file_path": "src/catalog/domain/pricing.py",
  "line": 17
}
```

### Bad comment examples
**Example 1: Hardcoded path**
```json
{
  "content": "It is generally best practice to avoid hardcoding absolute paths in shared scripts. Using `$HOME/repos/sandbox/themis-repos/themis/main.py` means this script is tied to your specific machine setup. If someone else tries to use it, it will fail. Please change this to a relative path so the script works anywhere.",
  "file_path": "scripts/run_github.sh",
  "line": 1
}
```

**Example 2: Consecutive `if` statements**
{
  "content": "In main(), consecutive if statements are used for checking git_provider. When git_provider == 'gitlab', the first branch runs GitLabCLIAdapter().run(), and then execution falls through to evaluate if git_provider == 'github':. Because this condition is False, the else branch executes, logging an error and terminating the process with sys.exit(1). Change if git_provider == 'github': to elif.",
  "file_path": "src/themis/main.py",
  "line": 15
}


**Example 3: do NOT produce linter/style nits**
```json
{
  "content": "Consider renaming `amt` to `amount` for clarity.",
  "file_path": "src/catalog/domain/pricing.py",
  "line": 19
}
```

### References (citations)
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

"""
# endregion


# region
_COHORTS_SECTION = """\
## Cohorts
### High level goal of this section

Make the reviewer's job easier by grouping related changes and establishing a reading order.

### Rules
  - Return cohorts in the order a reviewer should read them — root cause first, downstream effects\
  after. If a change in a DTO/interface/contract causes cascading changes downstream, the DTO file \
comes first — in its own cohort or at the top of a cohort — so the reviewer understands \
the "why" before seeing the "what".
  - Every file must appear in exactly one cohort, referenced by its path.
  - The `overview` per file must describe what happened in that file, not repeat the cohort \
description.

**Good cohort example:**
Input files:
  src/dtos/order_item_dto.py  — added `discount_amount` field
  src/services/pricing_service.py — reads new field, applies discount
  src/api/orders_router.py — exposes discount in response schema
  tests/test_pricing_service.py — unit tests for discount logic

Good output:
{
  "cohorts": [
    {
      "name": "Contract change",
      "description": "The DTO is the origin of this change. Review this first to understand what new data is flowing through the system.",
      "changes": [
        { "path": "src/dtos/order_item_dto.py", "overview": "Adds `discount_amount: Decimal` to OrderItemDTO. This is the root cause of all downstream changes in this MR." }
      ]
    },
    {
      "name": "Business logic",
      "description": "Core discount calculation added to the pricing layer. Depends on the contract change above.",
      "changes": [
        { "path": "src/services/pricing_service.py", "overview": "Implements discount deduction in `calculate_total()`. Check rounding mode and whether negative discounts are guarded." },
        { "path": "tests/test_pricing_service.py", "overview": "Unit tests covering happy path and zero-discount edge case. Missing test for discount > item price." }
      ]
    },
    {
      "name": "API surface",
      "description": "Exposes the new field to API consumers. Review last — only makes sense after understanding the contract and logic.",
      "changes": [
        { "path": "src/api/orders_router.py", "overview": "Response schema now includes `discount_amount`. Verify the field is not accidentally exposed in contexts where discounts aren't applicable." }
      ]
    }
  ]
}

**Bad cohort (avoid):**
- One mega-cohort containing every file — gives the reviewer no guidance.
- Cohort description that just restates the file list without explaining the relationship.
- Reading order that puts the API router before the DTO that caused the change.

"""

# endregion

# region
_SYSTEM_PROMPT_BASE = f"""\
You are a Senior Staff Software Engineer performing a code review of a merge request.

## Goal
Give high-signal, actionable feedback. Stay silent on trivia.
Focus exclusively on:
- Logic bugs
- Security vulnerabilities
- Architectural violations
- Broken domain/business rules
- What the implementation is missing

Do NOT comment on formatting, naming style, or anything a linter already catches.

---

{_COHORTS_SECTION}

---

{_CODE_REVIEW_COMMENTS_SECTION}

"""
# endregion


# region
_MATRIX_INSTRUCTION_ENABLED = """\
3. business_requirements_matrix — for each business requirement found in the \
provided business/ticket context, state the requirement, whether the change \
meets it (status), and the evidence from the diff supporting that verdict.
"""
# endregion

# region
_MATRIX_INSTRUCTION_DISABLED = """\
3. business_requirements_matrix — no business/ticket context was provided for \
this review, so you MUST return an empty list here.
"""
# endregion


# region
# Structured output is requested through the prompt rather than the provider's
# `response_format`, because not every OpenAI-compatible provider enforces a JSON
# schema (Anthropic's compatibility layer does not). The schema is generated from
# the DTO so the prompt can never drift from what the parser validates.
_OUTPUT_FORMAT_SECTION = f"""\
---

## Output format
Respond with a single JSON object and nothing else:
  - No prose, explanations or Markdown before or after the object.
  - Do not wrap the object in a code fence.
  - The object MUST contain all three top-level keys: `cohorts`, \
`business_requirements_matrix` and `code_review_comments`. Use an empty list \
(`[]`) for a section that has nothing to report — never omit the key.
  - Use `null` (not an empty string) for `file_path`, `line` or `rule` when they \
do not apply.

The object must validate against this JSON Schema:
```json
{json.dumps(CodeReviewResponseDTO.model_json_schema())}
```

Minimal valid response (a review with nothing to report):
{{"cohorts": [], "business_requirements_matrix": [], "code_review_comments": []}}
"""
# endregion

_OUTPUT_FORMAT_REMINDER = (
    "Respond now with the JSON object described in the Output format section — "
    "JSON only, no surrounding text."
)


def build_system_prompt(has_business_context: bool) -> str:
    matrix = _MATRIX_INSTRUCTION_ENABLED if has_business_context else _MATRIX_INSTRUCTION_DISABLED
    return f"{_SYSTEM_PROMPT_BASE}\n{matrix}\n{_OUTPUT_FORMAT_SECTION}"


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
        sections += [
            "",
            "# Architecture rules",
            _format_architecture(context.architecture_rules),
        ]
    if context.past_mr_rules:
        sections += [
            "",
            "# Rules learned from past merge requests",
            _format_rules(context.past_mr_rules),
        ]
    if context.business_context:
        sections += ["", "# Business / ticket context", context.business_context]

    # The diff can be long; repeating the format demand at the very end keeps it
    # the last thing the model reads before answering.
    sections += ["", _OUTPUT_FORMAT_REMINDER]

    return "\n".join(sections)


def _format_files(mr: MergeRequest) -> str:
    blocks: list[str] = []
    for f in mr.files:
        blocks.append(
            f"## {f.display_path}\n"
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
