from src.review_engine.domain.diff_hunks import (
    DiffLineKind,
    anchorable_lines_by_new_line,
    parse_diff,
)


def test_parse_diff_resolves_line_numbers_across_kinds():
    raw = (
        "@@ -1,4 +1,4 @@\n"
        " unchanged one\n"
        "-removed two\n"
        "+added two\n"
        " unchanged three\n"
        " unchanged four\n"
    )

    lines = parse_diff(raw)

    assert [(line.kind, line.old_line, line.new_line) for line in lines] == [
        (DiffLineKind.CONTEXT, 1, 1),
        (DiffLineKind.REMOVED, 2, None),
        (DiffLineKind.ADDED, None, 2),
        (DiffLineKind.CONTEXT, 3, 3),
        (DiffLineKind.CONTEXT, 4, 4),
    ]


def test_parse_diff_handles_new_file_with_only_additions():
    raw = "@@ -0,0 +1,2 @@\n+first line\n+second line\n"

    lines = parse_diff(raw)

    assert all(line.kind is DiffLineKind.ADDED for line in lines)
    assert [line.new_line for line in lines] == [1, 2]
    assert [line.old_line for line in lines] == [None, None]


def test_parse_diff_continues_line_numbers_across_multiple_hunks():
    raw = "@@ -1,1 +1,2 @@\n context a\n+added a\n@@ -10,1 +11,2 @@\n context b\n+added b\n"

    added = [line for line in parse_diff(raw) if line.kind is DiffLineKind.ADDED]

    assert [line.new_line for line in added] == [2, 12]


def test_parse_diff_skips_headers_preamble_and_no_newline_marker():
    raw = (
        "diff --git a/f.py b/f.py\n"
        "index 111..222 100644\n"
        "--- a/f.py\n"
        "+++ b/f.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-old\n"
        "+new\n"
        "\\ No newline at end of file\n"
    )

    lines = parse_diff(raw)

    assert [(line.kind, line.content) for line in lines] == [
        (DiffLineKind.REMOVED, "old"),
        (DiffLineKind.ADDED, "new"),
    ]


def test_parse_diff_ignores_content_before_first_hunk():
    raw = "garbage line with no hunk\n+not a real add\n"

    assert parse_diff(raw) == []


def test_anchorable_lines_excludes_pure_deletions_and_keys_by_new_line():
    raw = "@@ -1,3 +1,2 @@\n keep\n-gone\n+changed\n"

    anchorable = anchorable_lines_by_new_line(raw)

    assert set(anchorable) == {1, 2}
    assert anchorable[1].kind is DiffLineKind.CONTEXT
    assert anchorable[2].kind is DiffLineKind.ADDED
