## Core Value To Deliver
Getting high-signal, contextual feedback directly inside a GitLab Merge Request without the code leaving user's infrastructure.

## Implementation phases

### (✅ done) Phase 1: The Core Pipeline (`0.1.0`)
#### Implementation
- [x] Fetch MR diff, identify affected modules, load per-module rules + architecture
- [x] Ask the LLM for a review and post free-standing comments back to the MR

**Capability:** Given a GitLab MR, Themis produces a real, context-aware code review from the plain diff and posts it back as comments — running entirely on the user's own runners, without the code leaving their infrastructure, and without crashing.

---

### Phase 2: Finish the Pipeline (`0.2.0`)
*Theme: stop discarding what the engine already computes, and plug in what's built but disconnected.*
#### Implementation
- [ ] Inline comments: anchor each review comment to its changed line (from diff hunks) and post via the GitLab position API instead of as free-standing comments
- [ ] Post Cohorts and as a top-level summary comment (reading guide)
- [ ] Wire technology detection (from `pyproject.toml` / file extensions) so per-technology best-practices context loads
- [ ] Linter Noise Filtering: parse local linter config (e.g. `[tool.ruff]`, `.eslintrc.json`) and instruct the LLM to stay silent on anything the linter already covers
- [ ] Enforce a per-file change-size limit in `should_be_reviewed` (skip oversized/generated files)

**Capability:** Themis leaves inline comments on the exact changed lines, opens with a cohort-based reading guide, pulls in technology best-practices, and stays quiet on anything a linter already flags. Nothing the engine computes is silently dropped.

---

### Phase 3: High-Signal & Precision (`1.0.0`)
*Theme: better context in, fewer false positives out.*
#### Implementation
- [ ] Tree-sitter chunking: map the diff against logical code blocks, send whole changed units (not bare hunks) with precise line anchors for context and inline placement
- [ ] False-positive gate: a self-critique pass that re-checks each proposed comment against the full file and drops the ones it can't substantiate
- [ ] Harden LLM-response handling: malformed, truncated, or missing-field responses degrade gracefully instead of failing the pipeline

**Capability:** Themis reasons over complete logical code units rather than raw hunks, places comments precisely, and filters its own output so what lands in the MR is trustworthy enough that a reviewer rarely has to dismiss a comment as wrong.

---

### Phase 4: Learning & Refinement (`1.1.0+`)
*Theme: the system learns from history and from reviewer feedback.*
#### Implementation
- [ ] Indexer: crawl historical MRs, analyze discussions, and auto-generate `rules.json` and `architecture.json` in the repo
- [ ] `/dismiss` feedback loop: webhook listener intercepts `/dismiss` comments, triggers a lightweight job, and commits the new exception into `rules.json`
- [ ] MR Description Mutation: move cohorts from a comment into the MR description
- [ ] Agentic context retrieval: let the LLM request related files, bounded to the module tree / `public.py` surfaces, to deepen architectural findings
- [ ] Multi-language grammar support for chunking beyond Python

**Capability:** Themis bootstraps its own rules and architecture context from a repo's past MRs, gets sharper every time a reviewer dismisses a comment, and can pull in related code on demand to ground deeper architectural findings — across more than one language.

## Measuring adoption
- DockerHub pulls: tracking unique image download trends
- GitLab Component Marketplace Metrics: Monitor how many unique project configurations import CI/CD component wrapper
- Using the engine to revew the engine code
- Track the creation of community-submitted `best-practices/` JSON templates
