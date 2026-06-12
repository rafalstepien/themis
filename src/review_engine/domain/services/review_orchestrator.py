from src.review_engine.domain.models.models import AnalysisContext, MergeRequest
from src.review_engine.ports.outbound import (
    BestPracticesPort,
    BusinessContextPort,
    CodeRepresentationPort,
    GitLabPort,
    LLMPort,
)


class ReviewOrchestrator:
    def __init__(
        self,
        gitlab_port: GitLabPort,
        llm_port: LLMPort,
        code_representation_port: CodeRepresentationPort,
        business_context_port: BusinessContextPort,
        best_practices_port: BestPracticesPort,
    ):
        self.gitlab_port = gitlab_port
        self.llm_port = llm_port
        self.code_representation_port = code_representation_port
        self.business_context_port = business_context_port
        self.best_practices_port = best_practices_port

    def execute(self, mr_id: str):
        mr_data = self.gitlab_port.get_mr_data(mr_id)

        mr = MergeRequest(**mr_data)
        for path, content in self.gitlab_port.get_mr_files(mr_id):
            mr.add_file(path, content)

        if not mr.should_be_reviewed():
            return

        analysis_context = AnalysisContext(
            code=self.code_representation_port.get_code(),
            architecture_rules=self.gitlab_port.get_file_content(
                mr.module, "architecture.json"
            ),
            past_mr_rules=self.gitlab_port.get_file_content(mr.module, "rules.json"),
            business_context=self.business_context_port.get_business_context(
                mr.ticket_id
            ),
            best_practices_context=self.best_practices_port.get_applicable_best_practices(
                mr.technologies
            ),
        )

        # 1) cohort aggregation, 2) business requirements matrix, 3) code review comments
        review_data = self.llm_port.generate_code_review(analysis_context)

        self.gitlab_port.post_comment(review_data.cohorts)
        self.gitlab_port.post_comment(review_data.business_requirements_matrix)

        for comment in review_data.code_review_comments:
            self.gitlab_port.post_comment(comment)
