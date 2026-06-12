from abc import ABC, abstractmethod


class LLMPort(ABC):
    @abstractmethod
    def generate_code_review(self): ...
