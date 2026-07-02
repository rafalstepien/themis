import factory

from src.review_engine.adapters.outbound.gitlab.dto import (
    FileDiffDTO,
    MergeRequestDTO,
)


class FileDiffDTOFactory(factory.Factory[FileDiffDTO]):
    class Meta:
        model = FileDiffDTO

    new_path = "new-path"
    new_content = "new-content"
    old_path = "old-path"
    old_content = "old-content"
    diff = "diff"
    new_file = False
    deleted_file = False
    renamed_file = False


class MergeRequestDTOFactory(factory.Factory[MergeRequestDTO]):
    class Meta:
        model = MergeRequestDTO

    id = 1
    iid = 101
    project_id = 11111
    title = "title"
    description = "description"
    source_branch = "source-branch"
    target_branch = "target-branch"
    changes = factory.LazyFunction(lambda: [FileDiffDTOFactory()])
    diff_refs = None
