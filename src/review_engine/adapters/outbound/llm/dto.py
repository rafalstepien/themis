from pydantic import BaseModel



class CohortChangeDTO(BaseModel):
    id: int
    overview: str


class CohortDTO(BaseModel):
    name: str
    description: str
    changes: list[CohortChangeDTO]


class CommentDTO(BaseModel):
    content: str
    links: list[str]


class BusinessRequirementDTO(BaseModel):
    requirement: str
    status: str  # e.g. "met", "partially_met", "not_met"
    evidence: str


class CodeReviewResponseDTO(BaseModel):
    cohorts: list[CohortDTO]
    business_requirements_matrix: list[BusinessRequirementDTO]
    code_review_comments: list[CommentDTO]
