from src.review_engine.adapters.outbound.gitlab.models import MergeRequestDTO
from src.review_engine.domain.models import ChangedFile, MergeRequest


def to_domain(dto: MergeRequestDTO) -> MergeRequest:
    return MergeRequest.create(
        mr_id=str(dto.mr_iid),
        target_branch=dto.target_branch,
        files=[ChangedFile.create(c.new_path, c.diff) for c in dto.changes],
    )
