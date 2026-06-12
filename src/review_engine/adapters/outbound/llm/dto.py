from pydantic import BaseModel


class CohortDTO(BaseModel):
    name: str
    description: str
    change_ids: list[int]


class CommentDTO(BaseModel):
    content: str
    links: list[str]


class CodeReviewResponseDTO(BaseModel):
    cohorts: list[CohortDTO]
    business_requirements_matrix: list
    code_review_comments: list[CommentDTO]
