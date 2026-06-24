import logging

from src.bootstrap.config import ReviewConfig
from src.review_engine.domain.models import AnalysisContext
from src.review_engine.ports.outbound import (
    BestPracticesPort,
    BusinessContextPort,
    GitLabPort,
    LLMPort,
    ModuleContextPort,
)

logger = logging.getLogger(__name__)


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
        self._log_loaded_context(modules, analysis_context)
        review = self.llm_port.generate_code_review(mr, analysis_context)

        # TODO: Add POST for cohorts with nice formatting
        for comment in review.comments:
            self.gitlab_port.post_comment(comment)

    def _get_technologies(self) -> list:
        return list()

    @staticmethod
    def _log_loaded_context(modules: list[str], context: AnalysisContext) -> None:
        """Report which review contexts were gathered for this MR.

        INFO gives a one-line presence/size summary; DEBUG dumps the full
        loaded content (enable with ``THEMIS_LOG_LEVEL=DEBUG``).
        """

        def _summary(value) -> str:
            if not value:
                return "absent"
            if isinstance(value, dict):
                return f"present ({len(value)} entries)"
            if isinstance(value, str):
                return f"present ({len(value)} chars)"
            return "present"

        logger.info(
            "Loaded context for modules %s | architecture rules: %s | past-MR rules: %s "
            "| best practices: %s | business context: %s",
            modules or "(none)",
            _summary(context.architecture_rules),
            _summary(context.past_mr_rules),
            _summary(context.best_practices_context),
            _summary(context.business_context),
        )
        logger.debug(
            "Full loaded context:\n"
            "  architecture_rules=%r\n"
            "  past_mr_rules=%r\n"
            "  best_practices_context=%r\n"
            "  business_context=%r",
            context.architecture_rules,
            context.past_mr_rules,
            context.best_practices_context,
            context.business_context,
        )
