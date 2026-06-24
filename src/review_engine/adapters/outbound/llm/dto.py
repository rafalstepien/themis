from typing import Literal

from pydantic import BaseModel


class CohortChangeDTO(BaseModel):
    id: int
    overview: str


class CohortDTO(BaseModel):
    name: str
    description: str
    changes: list[CohortChangeDTO]


class ReferenceDTO(BaseModel):
    kind: Literal["rule", "architecture"]
    module: str
    rule: str | None = None  # TODO: consider rules to have ids for references


class CommentDTO(BaseModel):
    content: str
    references: list[ReferenceDTO]


class BusinessRequirementDTO(BaseModel):
    requirement: str
    status: str  # e.g. "met", "partially_met", "not_met"
    evidence: str


class CodeReviewResponseDTO(BaseModel):
    cohorts: list[CohortDTO]
    business_requirements_matrix: list[BusinessRequirementDTO]
    code_review_comments: list[CommentDTO]
