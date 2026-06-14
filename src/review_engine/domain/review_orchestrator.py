from review_engine.domain.models import AnalysisContext
from src.review_engine.ports.outbound import (
    BestPracticesPort,
    BusinessContextPort,
    GitLabPort,
    LLMPort,
)


class ReviewOrchestrator:
    def __init__(
        self,
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

        ######################### GATHER ADDITIONAL CONTEXT #########################
        analysis_context = AnalysisContext(None, None, None, None)
        # analysis_context = AnalysisContext(
        #     architecture_rules=self.gitlab_port.get_file_content(mr.module, "architecture.json"),
        #     past_mr_rules=self.gitlab_port.get_file_content(mr.module, "rules.json"),
        #     business_context=self.business_context_port.get_business_context(mr.ticket_id),
        #     best_practices_context=self.best_practices_port.get_applicable_best_practices(
        #         mr.technologies
        #     ),
        # )

        ######################### SEND TO LLM #########################
        # # 1) cohort aggregation, 2) business requirements matrix, 3) code review comments
        self.llm_port.generate_code_review(mr, analysis_context)

        ######################### POST COMMENTS TO GITLAB #########################
        # review_data = self.llm_port.generate_code_review(mr, analysis_context)
        # self.gitlab_port.post_comment(review_data.cohorts)
        # self.gitlab_port.post_comment(review_data.business_requirements_matrix)
        # for comment in review_data.comments:
        #     self.gitlab_port.post_comment(comment)
