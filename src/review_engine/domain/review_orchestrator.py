import logging

from src.bootstrap.config import ReviewConfig
from src.review_engine.domain.models import AnalysisContext
from src.review_engine.ports.outbound import (
    BestPracticesPort,
    BusinessContextPort,
    GitProviderPort,
    LLMPort,
    ModuleContextPort,
)

logger = logging.getLogger(__name__)


class ReviewOrchestrator:
    def __init__(
        self,
        review_config: ReviewConfig,
        git_provider_port: GitProviderPort,
        llm_port: LLMPort,
        business_context_port: BusinessContextPort,
        best_practices_port: BestPracticesPort,
        module_context_port: ModuleContextPort,
    ):
        self.git_provider_port = git_provider_port
        self.llm_port = llm_port
        self.business_context_port = business_context_port
        self.best_practices_port = best_practices_port
        self.review_config = review_config
        self.module_context_port = module_context_port

    def execute(self):
        """
        1. Fetch base MR data and exclude MR and/or individual files from review
        2. Fetch file contents only for the relevant files
        3. Gather additional context for analysis
        4. Send to LLM for code review
        5. Post comments
        """
        mr = self.git_provider_port.get_mr_data()

        mr.remove_too_big_files(self.review_config.max_changed_lines_per_file)
        if not mr.should_be_reviewed(self.review_config.max_changed_files):
            return

        modules = mr.affected_modules(self.review_config)
        past_mr_rules = self.module_context_port.load_rules(modules)
        architecture = self.module_context_port.load_architecture(modules)
        business_context = None

        token_owner_details = self.git_provider_port.get_token_owner_details()
        mr_comments = self.git_provider_port.get_mr_comments()

        if mr_comments.code_review_already_performed(token_owner_details):
            logger.info("Code review was already executed. Exiting ...")
            return

        best_practices_context = {}

        analysis_context = AnalysisContext(
            past_mr_rules=past_mr_rules,
            architecture_rules=architecture,
            business_context=business_context,
            best_practices_context=best_practices_context,
        )
        self._log_loaded_context(modules, analysis_context)
        review = self.llm_port.generate_code_review(mr, analysis_context)

        if not self.review_config.skip_cohorts_comment:
            cohorts_comment = review.build_general_cohort_comment()
            if cohorts_comment:
                self.git_provider_port.post_general_comment(cohorts_comment)

        for comment in review.comments:
            if comment.anchor is not None and mr.diff_refs is not None:
                self.git_provider_port.post_inline_comment(comment, mr.diff_refs)
            else:
                self.git_provider_port.post_general_comment(comment)

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
