from abc import ABC, abstractmethod

from src.review_engine.domain.models import AnalysisContext, CodeReview, MergeRequest


class LLMPortError(Exception):
    """Part of the LLMPort contract — raised when any LLM interaction fails."""


class LLMPort(ABC):
    @abstractmethod
    def generate_code_review(self, mr: MergeRequest, context: AnalysisContext) -> CodeReview: ...
