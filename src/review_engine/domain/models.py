from dataclasses import dataclass
from enum import StrEnum

from src.bootstrap.config import (
    ReviewConfig,
    architecture_file_path,
    rule_file_path,
)


@dataclass(frozen=True)
class AnalysisContext:
    """
    Sourced from rules.json, architecture.json, Jira API and repo-maintained best practices.
    """

    past_mr_rules: dict | None = None
    architecture_rules: dict | None = None
    business_context: str | None = None
    best_practices_context: dict | None = None


_SENTINEL_PATHS = {"", "/dev/null"}


@dataclass(frozen=True, slots=True)
class DiffRefs:
    """The commit SHAs an inline comment's position is resolved against.

    GitLab's discussion position API requires all three: ``base_sha`` and
    ``head_sha`` bound the diff, and ``start_sha`` pins the comparison's
    starting point. Sourced from the merge request's ``diff_refs``.
    """

    base_sha: str
    start_sha: str
    head_sha: str


class ChangeType(StrEnum):
    ADDITION = "addition"
    DELETION = "deletion"
    CONTENT_CHANGE = "content_change"


@dataclass(frozen=True, slots=True)
class ChangedFile:
    change_id: int
    new_path: str
    old_path: str
    new_content: str
    old_content: str
    raw_diff: str
    change_type: ChangeType | None = None  # TODO: handle change type inference

    @classmethod
    def create(
        cls,
        change_id: int,
        new_path: str,
        old_path: str,
        new_content: str,
        old_content: str,
        raw_diff: str,
    ) -> "ChangedFile":
        return cls(
            change_id=change_id,
            new_path=new_path,
            old_path=old_path,
            new_content=new_content,
            old_content=old_content,
            raw_diff=raw_diff,
        )


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

    def should_be_reviewed(self, config: ReviewConfig) -> bool:
        """
        Business Rule (Invariant): We should not run an AI review if
        MR is empty or excessively massive.
        """
        if len(self.files) == 0:
            return False
        if len(self.files) > config.max_changed_files:
            return False
        # TODO: add rule
        #  for each file in the merge request
        #      if number of changes exceeds max number of changes
        #          return False
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
class Cohort:
    name: str
    description: str
    change_ids: list[int]


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
    anchor: CommentAnchor | None = None
    """When set, the comment is posted inline at ``anchor``; otherwise it is
    posted as a general MR note."""


@dataclass(frozen=True, slots=True)
class CodeReview:
    cohorts: list[Cohort]
    business_requirements_matrix: list  # TODO Phase 2: model as list[BusinessRequirement]
    comments: list[ReviewComment]
