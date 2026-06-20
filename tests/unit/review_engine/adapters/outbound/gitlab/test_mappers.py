from src.review_engine.adapters.outbound.gitlab.dto import FileDiffDTO, MergeRequestDTO
from src.review_engine.adapters.outbound.gitlab.mappers import to_domain


def test_map_to_domain_object():
    file_diff = FileDiffDTO(
        new_path="new-path",
        new_content="new-content",
        old_path="old-path",
        old_content="old-content",
        diff="diff",
        new_file=False,
        deleted_file=False,
        renamed_file=False,
    )

    dto = MergeRequestDTO(
        id=1,
        iid=101,
        project_id=11111,
        title="title",
        description="description",
        source_branch="source-branch",
        target_branch="target-branch",
        changes=[
            file_diff,
        ],
    )

    domain_mr = to_domain(dto)
    assert domain_mr
    assert domain_mr.files[0].change_id == 1


def test_map_to_domain_object__none_content():
    file_diff = FileDiffDTO(
        new_path="new-path",
        new_content=None,
        old_path="old-path",
        old_content=None,
        diff="diff",
        new_file=False,
        deleted_file=False,
        renamed_file=False,
    )

    dto = MergeRequestDTO(
        id=1,
        iid=101,
        project_id=11111,
        title="title",
        description="description",
        source_branch="source-branch",
        target_branch="target-branch",
        changes=[
            file_diff,
        ],
    )

    domain_mr = to_domain(dto)
    assert domain_mr.files[0].old_content == ""
    assert domain_mr.files[0].new_content == ""
