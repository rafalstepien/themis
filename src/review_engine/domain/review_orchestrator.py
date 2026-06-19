from src.bootstrap.config import Config
from src.review_engine.domain.models import AnalysisContext
from src.review_engine.ports.outbound import (
    BestPracticesPort,
    BusinessContextPort,
    GitLabPort,
    LLMPort,
)


class ReviewOrchestrator:
    def __init__(
        self,
        config: Config,
        gitlab_port: GitLabPort,
        llm_port: LLMPort,
        business_context_port: BusinessContextPort,
        best_practices_port: BestPracticesPort,
    ):
        self.gitlab_port = gitlab_port
        self.llm_port = llm_port
        self.business_context_port = business_context_port
        self.best_practices_port = best_practices_port

    def execute(self):
        mr = self.gitlab_port.get_mr_data()

        if not mr.should_be_reviewed():
            return

        analysis_context = AnalysisContext(None, None, None, None)
        review = self.llm_port.generate_code_review(mr, analysis_context)

        for comment in review.comments:
            self.gitlab_port.post_comment(comment)
