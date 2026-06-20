from dataclasses import dataclass
from enum import StrEnum

from src.bootstrap.config import ReviewConfig


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


def _longest_module_match(path: str, modules: list[str]) -> str | None:
    """Return the most specific declared module that contains ``path``.

    A path belongs to a module when it equals the module path or sits beneath
    it. When declarations overlap (e.g. ``services`` and ``services/payments``)
    the longest match wins, so a file is attributed to the most specific module.
    Sentinel paths (empty or ``/dev/null``, used by GitLab for the missing side
    of an addition or deletion) match nothing.
    """
    if path in _SENTINEL_PATHS:
        return None
    matches = [m for m in modules if path == m or path.startswith(m + "/")]
    return max(matches, key=len) if matches else None


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

    @classmethod
    def create(
        cls,
        mr_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        files: list[ChangedFile],
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
        """Modules touched by this MR, restricted to those declared in config.

        Both ``new_path`` and ``old_path`` are considered so deletions (whose
        new side is a sentinel) resolve via the old path and cross-module moves
        are attributed to both source and destination modules. The result is
        deduplicated and returned in config-declaration order, making it
        deterministic regardless of file ordering.
        """
        matched = set()
        for file in self.files:
            for path in (file.new_path, file.old_path):
                module = _longest_module_match(path, config.modules)
                if module is not None:
                    matched.add(module)
        return [module for module in config.modules if module in matched]


@dataclass(frozen=True, slots=True)
class Cohort:
    name: str
    description: str
    change_ids: list[int]


@dataclass(frozen=True, slots=True)
class ReviewComment:
    content: str
    links: list[str]
    # TODO Phase 2 (Milestone 2): add file path + line anchor from Tree-sitter offsets


@dataclass(frozen=True, slots=True)
class CodeReview:
    cohorts: list[Cohort]
    business_requirements_matrix: list  # TODO Phase 2: model as list[BusinessRequirement]
    comments: list[ReviewComment]
