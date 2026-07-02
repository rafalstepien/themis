from src.review_engine.domain.models import ChangedFile, ChangeType, DiffRefs, MergeRequest

from .dto import DiffRefsDTO, MergeRequestDTO


def to_domain(dto: MergeRequestDTO) -> MergeRequest:
    return MergeRequest.create(
        mr_id=str(dto.iid),
        target_branch=dto.target_branch,
        source_branch=dto.source_branch,
        title=dto.title,
        description=dto.description,
        files=[
            ChangedFile(
                new_path=c.new_path,
                old_path=c.old_path,
                new_content=c.new_content or "",
                old_content=c.old_content or "",
                raw_diff=c.diff,
                change_type=_infer_change_type(c.new_file, c.renamed_file, c.deleted_file),
            )
            for c in dto.changes
        ],
        diff_refs=_to_diff_refs(dto.diff_refs),
    )


def _infer_change_type(new_file: bool, renamed_file: bool, deleted_file: bool) -> ChangeType:
    """
    Note: rename can also carry content changes, but rename wins over content changes in terms
    of dictating the display.
    """
    if deleted_file:
        return ChangeType.DELETED
    if new_file:
        return ChangeType.ADDED
    if renamed_file:
        return ChangeType.RENAMED
    return ChangeType.MODIFIED


def _to_diff_refs(dto: DiffRefsDTO | None) -> DiffRefs | None:
    if dto is None:
        return None
    return DiffRefs(base_sha=dto.base_sha, start_sha=dto.start_sha, head_sha=dto.head_sha)
