import logging

from src.review_engine.domain.diff_hunks import DiffLine, anchorable_lines_by_new_line
from src.review_engine.domain.models import (
    ChangedFile,
    CodeReview,
    Cohort,
    CommentAnchor,
    MergeRequest,
    Reference,
    ReferenceKind,
    ReviewComment,
)

from .dto import CodeReviewResponseDTO, CommentDTO

logger = logging.getLogger(__name__)


def to_domain(
    dto: CodeReviewResponseDTO,
    mr: MergeRequest,
    rule_modules: set[str] | None = None,
    architecture_modules: set[str] | None = None,
) -> CodeReview:
    """Map the LLM response DTO into the domain ``CodeReview``.

    ``mr`` is needed to validate each comment's cited ``file_path``/``line``
    against the actual diff so a comment only carries an anchor when it points
    at a real changed line.
    """
    cohorts = [
        Cohort(
            name=c.name, description=c.description, change_ids=[change.id for change in c.changes]
        )
        for c in dto.cohorts
    ]

    anchor_index = _AnchorIndex(mr)

    return CodeReview(
        cohorts=cohorts,
        business_requirements_matrix=[r.model_dump() for r in dto.business_requirements_matrix],
        comments=[
            ReviewComment(
                content=c.content,
                references=_to_references(c, rule_modules, architecture_modules),
                anchor=anchor_index.resolve(c),
            )
            for c in dto.code_review_comments
        ],
    )


class _AnchorIndex:
    """Resolves a comment's cited (file_path, line) to a validated ``CommentAnchor``.

    Built once per review from the MR's files: for each changed file it holds
    the file's paths plus a map of new-file line number -> ``DiffLine``. A cited
    line is accepted only if the file is in the diff and the line is one it
    actually touches; anything else resolves to ``None`` (a general comment).
    """

    def __init__(self, mr: MergeRequest):
        self._by_path: dict[str, tuple[ChangedFile, dict[int, DiffLine]]] = {
            file.new_path: (file, anchorable_lines_by_new_line(file.raw_diff)) for file in mr.files
        }

    def resolve(self, comment: CommentDTO) -> CommentAnchor | None:
        if comment.file_path is None or comment.line is None:
            return None

        entry = self._by_path.get(comment.file_path)
        if entry is None:
            logger.warning(
                "Dropping anchor for comment citing unknown file %r; posting as general comment",
                comment.file_path,
            )
            return None

        file, anchorable = entry
        line = anchorable.get(comment.line)
        if line is None:
            logger.warning(
                "Dropping anchor for comment citing line %s of %r which is not a changed line; "
                "posting as general comment",
                comment.line,
                comment.file_path,
            )
            return None

        return CommentAnchor(
            new_path=file.new_path,
            old_path=file.old_path,
            new_line=line.new_line,
            old_line=line.old_line,
        )


def _to_references(
    comment: CommentDTO,
    rule_modules: set[str] | None,
    architecture_modules: set[str] | None,
) -> list[Reference]:
    """
    Ensures that the references listed by LLM are coming from correct
    modules and are not made up.
    """
    references: list[Reference] = []
    for ref in comment.references:
        kind = ReferenceKind(ref.kind)
        if kind is ReferenceKind.RULE:
            if rule_modules is not None and ref.module not in rule_modules:
                continue
            references.append(Reference(kind=kind, module=ref.module, rule=ref.rule))
        else:
            if architecture_modules is not None and ref.module not in architecture_modules:
                continue
            references.append(Reference(kind=kind, module=ref.module, rule=None))
    return references
