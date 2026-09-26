from src.engine.domain.models import (
    ChangedFile,
    ChangeType,
    DiffRefs,
    MergeRequest,
    MRComment,
    MRCommentAuthor,
    MRComments,
    TokenOwner,
)

from .dto import (
    DiffRefsDTO,
    GitLabNotesResponseDTO,
    MergeRequestDTO,
    TokenOwnerIdentityDTO,
)


def mr_to_domain(
    dto: MergeRequestDTO,
) -> MergeRequest:
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
                raw_diff=c.diff,
                change_type=_infer_change_type(c.new_file, c.renamed_file, c.deleted_file),
                generated_file=c.generated_file,
                too_large=c.too_large,
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


def mr_comments_to_domain(dto: GitLabNotesResponseDTO) -> MRComments:
    return MRComments(
        comments=[
            MRComment(
                id=c.id,
                system=c.system,
                author=MRCommentAuthor(
                    id=c.author.id,
                    username=c.author.username,
                    name=c.author.name,
                ),
            )
            for c in dto.notes
        ]
    )


def token_owner_to_domain(dto: TokenOwnerIdentityDTO) -> TokenOwner:
    return TokenOwner(
        id=dto.id,
        username=dto.username,
        name=dto.name,
        email=dto.email,
    )
