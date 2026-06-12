from abc import ABC, abstractmethod


class BestPracticesPort(ABC):
    ...

    @abstractmethod
    def get_applicable_best_practices(self): ...
