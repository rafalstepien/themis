---
name: review-themis
description: Review the current branch against main for THIS repo's conventions — code review of a Themis MR/branch enforcing hexagonal architecture, DDD boundaries, ADR-0001/0002, Raise-Low/Catch-High, and the coding standards. Use when asked to review changes, review a branch, do a code review, check conventions, or vet a merge request before opening it.
---

# Review Themis

Code-review the **current branch against `main`** and report convention
violations grounded in this repo's own rules — not generic lint. For broad,
language-level bug-hunting use the built-in `/code-review`; this skill is the
**Themis-specific gate** (hexagonal boundaries, ADRs, coding-standards.md,
CLAUDE.md).

Paths below are relative to the repo root.

## Step 1 — Collect the review bundle (do this first)

```bash
./.claude/skills/review-themis/collect-context.sh
```

Pass a different base if needed: `./.claude/skills/review-themis/collect-context.sh develop`.

This prints, in order: the branch, changed-files stat, the branch's commits,
**automated convention probes**, the **quality gates** (`ruff` / `ty` /
`pytest`), and the full diff. The probes are heuristics — each hit is a
*candidate* finding you must confirm by reading the actual code. Read the whole
output before writing anything.

## Step 2 — Review the diff against the checklist

Go file-by-file through the diff. For each hunk, check it against the rules
below. **Source of truth:** `docs/coding-standards.md`, `adr/*`, `CLAUDE.md`.

### Architecture (hexagonal / DDD) — the highest-value checks
- **Pure domain.** `src/*/domain/` must have zero I/O or framework imports —
  no `httpx`, `os`, `sys`, file I/O, `click`, `pydantic`. Business logic and
  invariants only. (Probe: "I/O imports inside the domain layer".)
- **ADR-0002 — ports return domain objects.** Outbound ports
  (`src/*/ports/outbound/`) must expose **domain** types, never adapter DTOs.
  Each adapter owns its own `dto.py` (pydantic, wire format) **and**
  `mappers.py` with a `to_domain()`, and maps before crossing the port. A
  `pydantic` or `DTO` reference under `domain/` or `ports/` is a violation.
- **Ports are interfaces; adapters implement.** Inbound (driving) ports let the
  outside call in; outbound (driven) ports are what the core calls out through.
  Adapters wrap ports with tech-specific detail. Dependencies point inward.
- **Controllers orchestrate, domain decides.** Adapters/CLI wire things up;
  business rules live in the domain (e.g. `MergeRequest.should_be_reviewed`).
- **Dependency injection.** Collaborators are passed in (see
  `ReviewOrchestrator.__init__`), not constructed inside the domain.

### Error handling
- **Raise Low, Catch High.** Low-level components (HTTP fetch, parsing) must
  **raise descriptive, domain-specific exceptions** — never swallow, print a
  fallback, or return a default. Catching/logging belongs at the edges (CLI
  adapter, worker). A bare `print(...)`/`sys.exit` or silent fallback deep in
  an adapter is a finding. (Probes: "print() in non-CLI code", "broad except".)
- **Preserve traceback.** When translating a low-level error into a
  domain-specific one, chain with `raise NewError(...) from err`.

### Python style (coding-standards.md)
- **Types:** use `|`, not `Union`/`Optional`; use stdlib generics (`list`,
  `dict`), not `typing.List`/`Dict`. (Probe: "legacy typing".)
- **Data structures:** `dataclasses` when no validation is needed (domain
  models); `pydantic` only for data needing validation (adapter DTOs at the
  wire boundary).
- **Logging:** use the `logging` module for execution logs, not `print`.

### Tests (CLAUDE.md §4, coding-standards.md)
- New/changed behavior needs `tests/test_*.py` coverage using
  **Given-When-Then**. Flag domain logic that ships untested. (Note: the suite
  currently collects 0 tests — call this out if the diff adds logic without
  tests.)

### Hygiene & security
- **Atomic commits (CLAUDE.md §6/§7):** one logical change per commit; flag a
  commit that bundles unrelated engine + CLI + config changes.
- **ADR alignment:** structural/versioning patterns must not clash with `adr/*`
  (e.g. ADR-0001 lockstep versioning, single image + `--mode` flag).
- **Security (CLAUDE.md §8):** never reads `.env`/`.env.*`; no token/secret/key
  printed or logged. (Probe: "secret-looking values".)
- **Gates must be green:** `ruff`, `ty`, and `pytest` from the bundle must all
  pass. A failing gate is a blocking finding.

## Step 3 — Report

Group findings by severity and anchor every one to `file:line` **and** the rule
it breaks. Be specific and prescriptive; skip praise and nits the linter
already owns.

```
## Themis review — <branch> vs main

### 🔴 Blocking (architecture / ADR / failing gate)
- `src/.../x.py:42` — DTO returned across outbound port. Violates ADR-0002;
  map to a domain object in `mappers.to_domain()` before returning.

### 🟡 Should fix (standards)
- `src/.../cli_adapter.py:60` — `Dict[str, Any]` uses legacy typing. Use
  `dict[str, Any]` (coding-standards.md).

### 🟢 Consider
- ...

### Gates
- ruff: ✅ / ❌   ty: ✅ / ❌   pytest: ✅ / ❌ (N tests)
```

If there are no findings in a severity bucket, omit it. End with a one-line
verdict: **approve**, **approve-with-nits**, or **changes-requested**.

## Gotchas
- **Three-dot diff is intentional.** The helper uses `git diff main...HEAD`
  (merge-base) so commits that landed on `main` after you branched don't show
  up as your changes. Don't "fix" it to two-dot.
- **Probes flag candidates, not verdicts.** `print()` in `src/cli/` or the CLI
  inbound adapter is the *correct* place to surface errors (Catch High) — the
  probe will list it anyway. Confirm location before reporting.
- **The LLM client is a stub.** `OpenAIClient.generate_code_review` returns a
  canned comment by design (Phase 1). Don't flag it as a missing-implementation
  bug; do flag if new domain logic depends on LLM output that the stub can't
  provide.
- **`uv.lock` / generated files** appear in the diff — skip them in review.
