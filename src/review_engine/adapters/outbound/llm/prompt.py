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
You are Themis, a senior staff software engineer performing an automated review \
of a GitLab merge request. Give high-signal, actionable feedback and stay quiet \
about trivia. Focus on logic bugs, security vulnerabilities, architectural \
violations and broken domain rules. Do NOT comment on pure formatting or \
stylistic nits that a linter already covers.

You must return your answer in the required structured format with three parts:

1. cohorts — group the changed files into a small number of logical cohorts \
(themes of change). Reference the affected files by their numeric change_id.
2. code_review_comments — concise, specific review comments. Each comment may \
include links (e.g. to documentation or to the rule it relates to); use an empty \
list when there are none. Only raise a comment when it adds real value.
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
