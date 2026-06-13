from abc import ABC, abstractmethod

from src.review_engine.domain.models import ChangedFile


class BestPracticesPort(ABC):
    @abstractmethod
    def get_best_practices(self, changed_files: list[ChangedFile]) -> dict: ...
