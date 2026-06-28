from typing import Literal

from pydantic import BaseModel, Field


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
    file_path: str | None = Field(
        description="New-file path of the change the comment is about, copied from its `change_id` header. `None` when the comment is not tied to one file.",
        default=None,
    )
    line: int | None = Field(
        description="New-file line number (the left-gutter number in the annotated diff) the comment anchors to. `None` when no single line applies.",
        default=None,
    )


class BusinessRequirementDTO(BaseModel):
    requirement: str
    status: str  # e.g. "met", "partially_met", "not_met"
    evidence: str


class CodeReviewResponseDTO(BaseModel):
    cohorts: list[CohortDTO]
    business_requirements_matrix: list[BusinessRequirementDTO]
    code_review_comments: list[CommentDTO]
