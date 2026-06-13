from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChangedFile:
    path: str
    diff: str

    @classmethod
    def create(cls, path: str, diff: str) -> "ChangedFile":
        return cls(
            path=path,
            diff=diff,
        )

    @property
    def file_extension(self) -> str:
        return self.file_path.split(".")[-1] if "." in self.file_path else ""


@dataclass(frozen=True)
class AnalysisContext:
    """
    Sourced from rules.json, architecture.json and Jira API
    """

    past_mr_rules: dict
    architecture_rules: dict
    business_context: str
    best_practices_context: dict
    code: str


@dataclass
class MergeRequest:  # Aggregate Root
    mr_id: str
    target_branch: str
    files: dict[str, ChangedFile]

    @classmethod
    def create(cls, mr_id: str, target_branch: str, files: list[ChangedFile]) -> "MergeRequest":
        if not mr_id:
            raise ValueError("mr_id cannot be empty")
        if not target_branch:
            raise ValueError("target_branch cannot be empty")
        return cls(
            mr_id=mr_id,
            target_branch=target_branch,
            files={f.path: f for f in files},
        )

    def should_be_reviewed(self) -> bool:
        """
        Business Rule (Invariant): We should not run an AI review if
        MR is empty or excessively massive.
        """
        if len(self.files) == 0:
            return False
        if len(self.files) > 100:  # Protect API token limits
            return False
        return True

    def _file_too_big(self, content: str) -> bool:
        """
        Business Rule (Invariant): We should not run an AI review on
        the files that are very large (eg. lock files)
        """
        ...
        return False
