from dataclasses import dataclass, field
from enum import StrEnum
import logging

from src.bootstrap.config import (
    ReviewConfig,
    architecture_file_path,
    rule_file_path,
)

from .diff_hunks import DiffLineKind, parse_diff

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisContext:
    """
    Sourced from rules.json, architecture.json, Jira API and repo-maintained best practices.
    """

    past_mr_rules: dict | None = None
    architecture_rules: dict | None = None
    business_context: str | None = None


_SENTINEL_PATHS = {"", "/dev/null"}


@dataclass(frozen=True, slots=True)
class DiffRefs:
    base_sha: str
    start_sha: str
    head_sha: str


class ChangeType(StrEnum):
    ADDED = "added"
    DELETED = "deleted"
    RENAMED = "renamed"
    MODIFIED = "modified"


@dataclass(frozen=True, slots=True)
class ChangedFile:
    new_path: str
    old_path: str
    raw_diff: str
    generated_file: bool
    too_large: bool
    change_type: ChangeType

    @property
    def display_path(self) -> str:
        if self.change_type == ChangeType.DELETED:
            return self.old_path
        if self.change_type == ChangeType.RENAMED:
            return f"{self.old_path} -> {self.new_path}"
        return self.new_path

    @property
    def number_of_lines_changed(self) -> int:
        return sum(1 for line in parse_diff(self.raw_diff) if line.kind is not DiffLineKind.CONTEXT)

    def is_reviewable(self, max_changed_lines_per_file: int) -> bool:
        if (
            self.generated_file
            or self.too_large
            or self.number_of_lines_changed > max_changed_lines_per_file
        ):
            return False
        return True


@dataclass
class MergeRequest:  # Aggregate Root
    mr_id: str
    source_branch: str
    target_branch: str
    title: str
    description: str
    files: list[ChangedFile]
    diff_refs: DiffRefs | None = None

    @classmethod
    def create(
        cls,
        mr_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        files: list[ChangedFile],
        diff_refs: DiffRefs | None = None,
    ) -> "MergeRequest":
        if not mr_id:
            raise ValueError("id cannot be empty")
        if not target_branch:
            raise ValueError("target_branch cannot be empty")
        if not source_branch:
            raise ValueError("source_branch cannot be empty")
        return cls(
            mr_id=mr_id,
            target_branch=target_branch,
            source_branch=source_branch,
            title=title,
            description=description,
            files=files,
            diff_refs=diff_refs,
        )

    def should_be_reviewed(self, max_changed_files: int) -> bool:
        """
        Business Rule (Invariant): We should not run an AI review if
        MR is empty or excessively massive.
        """
        if not self.files:
            logger.warning("Merge Request empty (no changed files). Code review won't run.")
            return False
        if len(self.files) > max_changed_files:
            logger.warning(
                "Number of changed files exceeds the configured limit. Code review won't run."
            )
            return False
        return True

    def affected_modules(self, config: ReviewConfig) -> list[str]:
        """
        Identifies which modules are affected in this Merge Request.
        Restricted to those declared in config.

        Example: if the MR introduces changes in src/payments and src/logger
        then this method outputs ["src/payments", "src/logger"].

        """
        matched = set()
        for file in self.files:
            for path in (file.new_path, file.old_path):
                module = _longest_module_match(path, config.modules)
                if module is not None:
                    matched.add(module)
        return [module for module in config.modules if module in matched]

    def remove_too_big_files(self, max_changed_lines_per_file: int) -> None:
        new_files = []
        for f in self.files:
            if f.is_reviewable(max_changed_lines_per_file):
                new_files.append(f)
            else:
                logger.warning("Skipping not reviewable file %s", f.display_path)

        self.files = new_files


def _longest_module_match(path: str, modules: list[str]) -> str | None:
    """Return the most specific declared module that contains provided `path`.

    Example:
    For such input
        - path="src/modules/payments/dto/file.py"
        - modules=["src", "src/modules", "src/modules/payments",  "src/modules/orders"]

    Function returns "src/modules/payments" as this is the most specifically defined
    module that matches the path.
    """
    if path in _SENTINEL_PATHS:
        return None
    matches = [m for m in modules if path == m or path.startswith(m + "/")]
    return max(matches, key=len) if matches else None


@dataclass(frozen=True, slots=True)
class Change:
    path: str
    overview: str


@dataclass(frozen=True, slots=True)
class Cohort:
    name: str
    description: str
    changes: list[Change]


class ReferenceKind(StrEnum):
    RULE = "rule"
    ARCHITECTURE = "architecture"


@dataclass(frozen=True, slots=True)
class Reference:
    """A citation grounding a review comment in the repo's documented context.

    A comment may be grounded in a learned ``RULE`` (then ``rule`` carries the
    exact rule text) or in a module's ``ARCHITECTURE`` contract (whole file,
    since architecture sections are too dynamic to anchor). ``file_path`` is the
    repo-relative path of the source file, suitable for citing back in the MR.
    """

    kind: ReferenceKind
    module: str
    rule: str | None = None

    @property
    def file_path(self) -> str:
        if self.kind is ReferenceKind.RULE:
            return rule_file_path(self.module)
        return architecture_file_path(self.module)


@dataclass(frozen=True, slots=True)
class CommentAnchor:
    """The position an inline comment is pinned to within a changed file.

    ``new_line`` is the line's number in the new file (set for added and
    context lines); ``old_line`` its number in the old file (set for context
    lines). Both paths are always carried because GitLab's position payload
    requires them even when only one line number applies.
    """

    new_path: str
    old_path: str
    new_line: int | None = None
    old_line: int | None = None


@dataclass(frozen=True, slots=True)
class ReviewComment:
    content: str
    references: list[Reference]
    anchor: CommentAnchor | None = field(
        default=None,
        doc="When set, the comment is posted inline at ``anchor``; otherwise it is posted as a general MR note.",
    )


@dataclass(frozen=True, slots=True)
class CodeReview:
    cohorts: list[Cohort]
    business_requirements_matrix: list  # TODO Phase 2: model as list[BusinessRequirement]
    comments: list[ReviewComment]

    def build_general_cohort_comment(self) -> ReviewComment | None:
        if not self.cohorts:
            return None

        # TODO: consider if the placement of the method is correct
        current_comment_content = "# Overview of the changes in this MR\n\n"
        COHORT_SECTION_TEMPLATE = (
            "## Cohort {id}: {name}\n{desc}\n\n**CHANGES**\n\n{changes_list}\n\n\n"
        )

        for cohort_id, cohort in enumerate(self.cohorts, start=1):
            cl = "\n".join([f"* `{change.path}`: {change.overview}" for change in cohort.changes])
            text = COHORT_SECTION_TEMPLATE.format(
                id=cohort_id, name=cohort.name, desc=cohort.description, changes_list=cl
            )
            current_comment_content += text

        return ReviewComment(content=current_comment_content, references=[], anchor=None)


@dataclass(frozen=True, slots=True)
class MRCommentAuthor:
    id: int
    username: str
    name: str


@dataclass(frozen=True, slots=True)
class MRComment:
    id: int
    system: bool
    author: MRCommentAuthor


@dataclass(frozen=True, slots=True)
class MRComments:
    comments: list[MRComment]

    def code_review_already_performed(self, token_owner: TokenOwner) -> bool:
        for comment in self.comments:
            if not comment.system:
                if self._review_account_is_comment_author(comment.author.id, token_owner.id):
                    return True
        return False

    def _review_account_is_comment_author(
        self, comment_author_id: int, token_owner_id: int
    ) -> bool:
        return comment_author_id == token_owner_id


@dataclass(frozen=True, slots=True)
class TokenOwner:
    id: int
    username: str
    name: str
    email: str
