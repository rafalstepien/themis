from src.review_engine.domain.models import ChangedFile, DiffRefs, MergeRequest

from .dto import DiffRefsDTO, MergeRequestDTO


def to_domain(dto: MergeRequestDTO) -> MergeRequest:
    return MergeRequest.create(
        mr_id=str(dto.iid),
        target_branch=dto.target_branch,
        source_branch=dto.source_branch,
        title=dto.title,
        description=dto.description,
        files=[
            ChangedFile.create(
                change_id=c_id,
                new_path=c.new_path,
                old_path=c.old_path,
                new_content=c.new_content or "",
                old_content=c.old_content or "",
                raw_diff=c.diff,
            )
            for c_id, c in enumerate(dto.changes, 1)
        ],
        diff_refs=_to_diff_refs(dto.diff_refs),
    )


def _to_diff_refs(dto: DiffRefsDTO | None) -> DiffRefs | None:
    if dto is None:
        return None
    return DiffRefs(base_sha=dto.base_sha, start_sha=dto.start_sha, head_sha=dto.head_sha)
