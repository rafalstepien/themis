from abc import ABC, abstractmethod


class BestPracticesPort(ABC):
    @abstractmethod
    def load_best_practices(self, applicable_technologies: list[str]) -> dict:
        """
        applicable_technologies would be something like
        ["fastapi", "concurency"] that will map to best_practices/fastapi, best_practices/concurency
        """
        return {}
