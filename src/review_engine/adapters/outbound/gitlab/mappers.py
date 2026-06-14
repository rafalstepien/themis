from src.review_engine.domain.models import ChangedFile, MergeRequest

from .dto import MergeRequestDTO


def to_domain(dto: MergeRequestDTO) -> MergeRequest:
    return MergeRequest.create(
        id=str(dto.iid),
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
    )
