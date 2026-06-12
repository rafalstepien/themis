from dataclasses import dataclass


class ChangedFile:  # Entity
    def __init__(self, file_path: str, raw_content: str):
        self.file_path = file_path  # Unique Identity
        self.raw_content = raw_content
        self.ast_chunks: list[dict] = []  # Internal state

    def assign_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            raise ValueError(f"Cannot assign empty chunks to {self.file_path}")
        self.ast_chunks = chunks

    @property
    def file_extension(self) -> str:
        return self.file_path.split(".")[-1] if "." in self.file_path else ""


@dataclass(frozen=True)
class AnalysisContext:  # Value Object
    """
    Sourced from rules.json, architecture.json and Jira API
    """

    past_mr_rules: dict
    architecture_rules: dict
    business_context: str
    best_practices_context: dict
    code: str


class MergeRequest:  # Aggregate Root
    def __init__(self, mr_id: str, target_branch: str):
        self.mr_id = mr_id
        self.target_branch = target_branch
        self._files: dict[str, ChangedFile] = {}

    def add_file(self, file_path: str, content: str) -> None:
        if not file_path:
            return
        if self._file_too_big(content):
            return
        self._files[file_path] = ChangedFile(file_path, content)

    def get_all_chunks(self) -> list[dict]:
        all_chunks = []
        for file in self._files.values():
            all_chunks.extend(file.ast_chunks)
        return all_chunks

    def should_be_reviewed(self) -> bool:
        """
        Business Rule (Invariant): We should not run an AI review if
        MR is empty or excessively massive.
        """
        if len(self._files) == 0:
            return False
        if len(self._files) > 100:  # Protect API token limits
            return False
        return True

    def _file_too_big(self, content: str) -> bool:
        """
        Business Rule (Invariant): We should not run an AI review on
        the files that are very large (eg. lock files)
        """
        ...
        return False
