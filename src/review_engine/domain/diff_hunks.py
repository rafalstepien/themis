"""Parsing of unified diffs into per-line anchor information.

GitLab inline comments must be pinned to a concrete line via the position API.
A free-standing review comment knows only *what* is wrong; to post it inline we
need the line's number in the new file (and, for unchanged context lines, its
number in the old file too). This module turns a file's raw unified ``diff``
into the list of lines it touches, each tagged with those numbers, so a comment
can be anchored to — and validated against — a real changed line.
"""

from dataclasses import dataclass
from enum import StrEnum
import re

# Matches a hunk header like ``@@ -12,7 +14,9 @@ def foo():`` and captures the
# old/new starting line numbers. The counts are intentionally ignored — we walk
# the body line by line and let each line advance its own counter.
_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


class DiffLineKind(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    CONTEXT = "context"


@dataclass(frozen=True, slots=True)
class DiffLine:
    """A single line of a unified diff, with its resolved line numbers.

    ``old_line`` is the line's number in the old file (``None`` for added
    lines); ``new_line`` is its number in the new file (``None`` for removed
    lines). Context lines carry both.
    """

    kind: DiffLineKind
    old_line: int | None
    new_line: int | None
    content: str


def parse_diff(raw_diff: str) -> list[DiffLine]:
    """Parse a single file's unified diff into its touched lines.

    Lines outside any hunk (file headers, ``diff --git``/``index`` lines, the
    leading material before the first ``@@``) and the ``\\ No newline at end of
    file`` marker are skipped. Malformed input yields whatever could be parsed
    rather than raising — a bad diff should not abort a review.
    """
    lines: list[DiffLine] = []
    old_line = 0
    new_line = 0
    in_hunk = False

    for raw in raw_diff.splitlines():
        is_header = _HUNK_HEADER.match(raw)
        if is_header:
            old_line = int(is_header.group(1))
            new_line = int(is_header.group(2))
            in_hunk = True
            continue

        if not in_hunk:
            continue

        if raw.startswith("\\"):  # "\ No newline at end of file"
            continue

        # File headers can appear interleaved when a diff carries several files;
        # they are never part of a hunk body, so leave the counters untouched.
        if raw.startswith("+++") or raw.startswith("---"):
            continue

        marker = raw[:1]
        content = raw[1:]
        if marker == "+":
            lines.append(DiffLine(DiffLineKind.ADDED, None, new_line, content))
            new_line += 1
        elif marker == "-":
            lines.append(DiffLine(DiffLineKind.REMOVED, old_line, None, content))
            old_line += 1
        else:
            # A leading space marks a context line; a fully blank line is an
            # empty context line rendered without its space — treat both alike.
            lines.append(DiffLine(DiffLineKind.CONTEXT, old_line, new_line, content))
            old_line += 1
            new_line += 1

    return lines


def anchorable_lines_by_new_line(raw_diff: str) -> dict[int, DiffLine]:
    """Map new-file line number -> ``DiffLine`` for every anchorable line.

    A comment cites a line by its number in the *new* file, so only lines that
    exist there (added and context lines) can be anchored. Pure deletions have
    no new-file line and are therefore excluded; a comment about one falls back
    to a general MR note.
    """
    return {line.new_line: line for line in parse_diff(raw_diff) if line.new_line is not None}
