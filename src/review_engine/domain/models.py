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
