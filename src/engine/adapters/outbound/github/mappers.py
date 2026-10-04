from src.engine.domain.models import (
    ChangedFile,
    ChangeType,
    DiffRefs,
    MergeRequest,
    MRComment,
    MRCommentAuthor,
    TokenOwner,
)

from .dto import (
    GitHubCommentDTO,
    GitHubPullRequestDTO,
    GitHubUserDTO,
)


def pr_to_domain(
    dto: GitHubPullRequestDTO,
    comments: list[GitHubCommentDTO],
) -> MergeRequest:
    return MergeRequest.create(
        mr_id=str(dto.number),
        target_branch=dto.base.ref,
        source_branch=dto.head.ref,
        title=dto.title,
        description=dto.body or "",
        files=[
            ChangedFile(
                new_path=c.filename,
                old_path=c.previous_filename or c.filename,
                raw_diff=c.patch or "",
                change_type=_infer_change_type(c.status),
                generated_file=False,  # GitHub API doesn't explicitly flag generated files in the standard files payload
                too_large=c.patch is None and c.status != "renamed",
            )
            for c in dto.files
        ],
        diff_refs=DiffRefs(
            base_sha=dto.base.sha,
            start_sha=dto.base.sha,  # Start SHA maps closely to the base ref
            head_sha=dto.head.sha,
        ),
        comments=[
            MRComment(
                id=c.id,
                system=c.user.type == "Bot",
                author=MRCommentAuthor(
                    id=c.user.id,
                    username=c.user.login,
                    name=c.user.name or c.user.login,
                ),
            )
            for c in comments
        ],
    )


def _infer_change_type(status: str) -> ChangeType:
    if status == "removed":
        return ChangeType.DELETED
    if status == "added":
        return ChangeType.ADDED
    if status == "renamed":
        return ChangeType.RENAMED
    return ChangeType.MODIFIED


def token_owner_to_domain(dto: GitHubUserDTO) -> TokenOwner:
    return TokenOwner(
        id=dto.id,
        username=dto.login,
        name=dto.name or dto.login,
        email=dto.email or "",
    )
