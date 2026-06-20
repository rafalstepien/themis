from src.bootstrap.config import ReviewConfig
from src.review_engine.domain.models import AnalysisContext
from src.review_engine.ports.outbound import (
    BestPracticesPort,
    BusinessContextPort,
    GitLabPort,
    LLMPort,
    ModuleContextPort,
)


class ReviewOrchestrator:
    def __init__(
        self,
        review_config: ReviewConfig,
        gitlab_port: GitLabPort,
        llm_port: LLMPort,
        business_context_port: BusinessContextPort,
        best_practices_port: BestPracticesPort,
        module_context_port: ModuleContextPort,
    ):
        self.gitlab_port = gitlab_port
        self.llm_port = llm_port
        self.business_context_port = business_context_port
        self.best_practices_port = best_practices_port
        self.review_config = review_config
        self.module_context_port = module_context_port

    def execute(self):
        mr = self.gitlab_port.get_mr_data()

        if not mr.should_be_reviewed(self.review_config):
            return

        modules = mr.affected_modules(self.review_config)
        past_mr_rules = self.module_context_port.load_rules(modules)
        architecture = self.module_context_port.load_architecture(modules)
        business_context = None
        technologies = self._get_technologies()
        best_practices_context = self.best_practices_port.load_best_practices(technologies)

        analysis_context = AnalysisContext(
            past_mr_rules=past_mr_rules,
            architecture_rules=architecture,
            business_context=business_context,
            best_practices_context=best_practices_context,
        )
        review = self.llm_port.generate_code_review(mr, analysis_context)

        for comment in review.comments:
            self.gitlab_port.post_comment(comment)

    def _get_technologies(self) -> list:
        return list()
