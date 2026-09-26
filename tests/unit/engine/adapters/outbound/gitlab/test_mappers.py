import pytest

from src.engine.adapters.outbound.gitlab.dto import (
    DiffRefsDTO,
    FileDiffDTO,
)
from src.engine.adapters.outbound.gitlab.mappers import mr_to_domain
from src.engine.domain.models import ChangeType, DiffRefs

from .factories import FileDiffDTOFactory, MergeRequestDTOFactory


def test_map_to_domain_object():
    dto = MergeRequestDTOFactory.build()

    domain_mr = mr_to_domain(dto)

    assert domain_mr
    assert domain_mr.files[0].change_type == ChangeType.MODIFIED
    assert domain_mr.diff_refs is None


def test_map_to_domain_object__maps_diff_refs():
    diff_refs = DiffRefsDTO(base_sha="base", start_sha="start", head_sha="head")
    dto = MergeRequestDTOFactory.build(diff_refs=diff_refs)

    domain_mr = mr_to_domain(dto)

    assert domain_mr.diff_refs == DiffRefs(base_sha="base", start_sha="start", head_sha="head")


@pytest.mark.parametrize(
    ["file_diff_dto", "expected_change_type"],
    [
        pytest.param(
            FileDiffDTOFactory.build(deleted_file=True),
            ChangeType.DELETED,
            id="Deleted file",
        ),
        pytest.param(
            FileDiffDTOFactory.build(new_file=True),
            ChangeType.ADDED,
            id="Added file",
        ),
        pytest.param(
            FileDiffDTOFactory.build(renamed_file=True),
            ChangeType.RENAMED,
            id="Renamed file",
        ),
        pytest.param(
            FileDiffDTOFactory.build(),
            ChangeType.MODIFIED,
            id="Modified file",
        ),
        pytest.param(
            FileDiffDTOFactory.build(deleted_file=True, new_file=True),
            ChangeType.DELETED,
            id="Deleted takes precedence over added",
        ),
        pytest.param(
            FileDiffDTOFactory.build(deleted_file=True, renamed_file=True),
            ChangeType.DELETED,
            id="Deleted takes precedence over renamed",
        ),
        pytest.param(
            FileDiffDTOFactory.build(new_file=True, renamed_file=True),
            ChangeType.ADDED,
            id="Added takes precedence over renamed",
        ),
    ],
)
def test_map_to_domain_object__maps_change_type(
    file_diff_dto: FileDiffDTO, expected_change_type: ChangeType
):
    dto = MergeRequestDTOFactory.build(changes=[file_diff_dto])

    domain_mr = mr_to_domain(dto)

    assert domain_mr.files[0].change_type == expected_change_type
