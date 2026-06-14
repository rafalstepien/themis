#!/usr/bin/env bash
#
# collect-context.sh — gather everything needed to review the current branch
# against `main`, plus run Themis's own quality gates so the reviewer sees what
# is already broken before reading a single line of the diff.
#
# Usage (from repo root):
#   ./.claude/skills/review-themis/collect-context.sh [BASE]
#
# BASE defaults to `main`. The diff uses the three-dot form
# (`git diff BASE...HEAD`) so it shows only what this branch changed relative
# to the merge-base, ignoring commits that landed on main in the meantime.
#
# Exit code is always 0 — this is a reporting tool, not a gate. The reviewer
# interprets the gate output (ruff / ty / pytest) as findings.

set -uo pipefail

BASE="${1:-main}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

hr() { printf '\n========== %s ==========\n' "$1"; }

hr "BRANCH"
git rev-parse --abbrev-ref HEAD

hr "CHANGED FILES vs ${BASE}"
git diff "${BASE}...HEAD" --stat

hr "COMMITS ON THIS BRANCH (atomicity check — CLAUDE.md §6)"
git log --oneline "${BASE}..HEAD"

# ---------------------------------------------------------------------------
# Automated convention probes. These are heuristics, not proof — every hit is
# a candidate finding the reviewer must confirm against the actual code.
# ---------------------------------------------------------------------------

hr "PROBE: I/O imports inside the domain layer (must be empty — hexagonal core is pure)"
grep -rEn --include='*.py' 'import (httpx|requests|os|sys|socket)|^import os|from pathlib|click' \
  src/*/domain/ 2>/dev/null || echo "(clean)"

hr "PROBE: pydantic / DTOs leaking into domain or ports (ADR-0002 — ports return domain objects)"
grep -rEn --include='*.py' 'pydantic|DTO' src/*/domain/ src/*/ports/ 2>/dev/null || echo "(clean)"

hr "PROBE: legacy typing (prefer '|' and stdlib generics — coding-standards.md)"
grep -rEn --include='*.py' 'Union\[|Optional\[|: Dict|: List|-> Dict|-> List|from typing import' src/ 2>/dev/null \
  || echo "(clean)"

hr "PROBE: print() in non-CLI code (use logging; Raise-Low/Catch-High)"
grep -rEn --include='*.py' '\bprint\(' src/ 2>/dev/null || echo "(clean)"

hr "PROBE: broad except without 'from' chaining (Preserve Traceback Context)"
grep -rEn --include='*.py' 'except .*:' src/ 2>/dev/null || echo "(clean)"

hr "PROBE: secret-looking values printed/logged (Security §8)"
grep -rEn --include='*.py' '(print|log).*(token|secret|api_key|password)' src/ 2>/dev/null || echo "(clean)"

# ---------------------------------------------------------------------------
# Quality gates — the same commands CONTRIBUTING expects to pass.
# ---------------------------------------------------------------------------

hr "GATE: ruff check"
uv run ruff check 2>&1 || true

hr "GATE: ty check"
uv run ty check 2>&1 || true

hr "GATE: pytest"
uv run pytest 2>&1 | tail -5 || true

hr "FULL DIFF vs ${BASE} (review this against the checklist in SKILL.md)"
git diff "${BASE}...HEAD"

exit 0
