<div align="center">

# ⚖️ Themis

### ⚡ The GitLab-native, AI code reviewer that runs entirely on your private CI runners.
### 🔒 Entirely non-agentic, follows a strict Bring-Your-Own-Key (BYOK) model.
- Zero Third-Party Infra: Execution happens 100% inside your GitLab CI runners.
- Data Isolation: Your source code never leaves your corporate boundary or hits an external SaaS dashboard.
- LLM Transparency: It connects directly to your enterprise LLM provider via masked environment variables.

[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build](https://img.shields.io/github/actions/workflow/status/rafalstepien/themis/ci.yml?branch=main&label=CI)](https://github.com/rafalstepien/themis/actions)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</div>

---

> **Themis** is an open-source, GitLab-native AI code review gate. It plugs into your CI/CD pipeline as a single component, analyzes every Merge Request for logical bugs, security vulnerabilities, and architectural violations, then posts structured, byte-offset-grounded feedback directly into the MR thread — all without your source code ever leaving your own runners.

---

## About the Name

**Themis** is named after the Greek goddess of order and justice. While often associated with justice alone, Themis was fundamentally a guardian of **order** — the personification of divine law, fairness, and the natural order that prevents chaos. This mirrors the tool's core mission: enforcing order and consistency in your codebase through automated, principled code review, ensuring that architecture, practices, and standards remain coherent across your entire system.

---

## Why Themis?

Most AI code review tools either route your source code through a third-party SaaS, flood your MR with low-value noise, or drag reviewers into a separate dashboard. Themis is built differently:

| Pain point | Themis approach |
|---|---|
| Source code exits corporate boundary | Runs entirely on **your** GitLab runners — code never leaves |
| AI produces 40 "fix your semicolons" comments | Cross-references your linter config and suppresses anything it already catches |
| Another dashboard to maintain | Inline comments, cohort summaries, and requirements matrix — all native GitLab UI |
| Hours of setup and external infra | Three lines in `.gitlab-ci.yml`, two masked variables — done in 5 minutes |

---

## Features

- **Bring Your Own Key (BYOK)** — LLM API token stays in GitLab Masked Variables; your source code never transits a third-party service
- **AST-native precision** — Tree-sitter chunks diffs into structural code blocks; every comment is grounded to the exact offending construct, not a raw line number
- **5-minute onboarding** — ships as a GitLab CI/CD Component; add three lines to `.gitlab-ci.yml` and you're live
- **High-signal noise filtering** — reads your linter config (`.eslintrc.json`, `pyproject.toml`, …) and suppresses any nit your linter already catches
- **Multi-context synthesis** — aggregates module rules, architecture constraints, domain best practices, and Jira ticket requirements into a single grounded review prompt
- **Native GitLab UX** — cohort summaries, a ticket requirements matrix, and inline comments posted directly via the GitLab API

---

## Quick Start

**Step 1 — Create a dedicated bot account for Themis:**

Themis posts review comments on behalf of a GitLab user. You must create a dedicated service account for this — do not use a personal account, as its token would grant Themis access far beyond what it needs.

1. **Create a new GitLab account** for the bot (e.g. `themis-reviewer` or `your-org-code-reviewer`). Use a shared team mailbox (e.g. `themis-reviewer@your-company.com`) so no single person owns it.
2. **Add the bot account to each repository** that Themis will review:
   - Go to your project → **Manage → Members → Invite members**.
   - Search for the bot account and set its role to **Developer** (Themis needs permission to read diffs and post comments; Reporter is not enough).
   - Click **Invite**.
3. **Generate a GitLab personal access token** for the bot account:
   - Sign in as the bot account.
   - Go to **User settings → Access tokens → Add new token**.
   - Give it a descriptive name (e.g. `themis-ci`), set an expiry date appropriate for your rotation policy, and grant the **`api`** scope.
   - Copy the token — you will use it as `GITLAB_API_TOKEN` in the next step.

**Step 2 — Add Themis to your Merge Request pipeline:**

```yaml
# .gitlab-ci.yml
include:
  - component: gitlab.com/your-org/themis/review@~latest

stages:
  - review
```

**Step 3 — Set two masked variables in your GitLab project settings:**

Go to your project → **Settings → CI/CD → Variables** and add:

| Variable | Description |
|---|---|
| `LLM_API_TOKEN` | API key for your LLM provider |
| `GITLAB_API_TOKEN` | Personal access token of the Themis bot account (from Step 1) |

Mark both variables as **Masked** to prevent them from appearing in job logs.

**Step 4 — Open a Merge Request.** Themis runs automatically and posts inline review comments under the bot account.

> Optional: set `JIRA_API_TOKEN` to enable automatic ticket requirements verification inside the MR.

---

## How It Works

```
MR opened  →  CI triggers Themis  →  fetch changed files
    →  AST chunking  →  module identification
    →  context aggregation (rules, architecture, best practices, Jira)
    →  single LLM call  →  structured JSON output
    →  GitLab API: post cohorts + requirements matrix + inline comments
```

Themis ships as a single Docker image with two modes:

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Image                         │
│                                                             │
│  ┌──────────────────────────┐  ┌─────────────────────────┐  │
│  │   AI Code Review Engine  │  │     Async Indexer       │  │
│  │                          │  │                         │  │
│  │  GitLab API → diff       │  │  Crawls historical MRs  │  │
│  │  Tree-sitter → AST       │  │  Generates rules.json   │  │
│  │  Context aggregation     │  │  Generates arch.json    │  │
│  │  LLM → review            │  │  Commits back to repo   │  │
│  │  GitLab API → post       │  │                         │  │
│  └──────────────────────────┘  └─────────────────────────┘  │
│                                                             │
│  ai-review-tool --mode=engine | --mode=indexer              │
└─────────────────────────────────────────────────────────────┘
```

---

## Context Files

Themis reads optional per-module context files committed alongside your code:

| File | Purpose |
|------|---------|
| `<module>/rules.json` | Accumulated review rules derived from past MR discussions |
| `<module>/architecture.json` | Module architecture constraints (e.g. hexagonal boundaries, forbidden imports) |
| `best_practices/<tech>.toml` | Community-maintained, technology-specific rulesets (Django, FastAPI, security, …) |

These files can be authored manually or auto-generated by the **Async Indexer** component, which crawls your historical MR discussions and distills them into reviewable rules.

---

## Configuration

### GitLab Masked Variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `LLM_API_TOKEN` | ✅ | API key for your LLM provider |
| `GITLAB_API_TOKEN` | ✅ | GitLab token with `api` scope |
| `JIRA_API_TOKEN` | ➖ | Enables Jira ticket requirements context |

### `config.json` (committed to the reviewed repo)

Per-repo overrides — documentation landing in `v1.0.0`.

---

## Local Development

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.14+ |
| [uv](https://docs.astral.sh/uv/) | latest |
| [Task](https://taskfile.dev/) | latest |
| Docker | 24+ |

### Setup

```bash
git clone https://github.com/rafalstepien/themis.git
cd themis
uv sync --group dev
```

### Common commands

```bash
task run-linters     # lint & format
uv run pytest        # run the test suite
task run-engine      # run the review engine locally
task run-indexer     # run the async indexer locally
```

---

## Roadmap

| Phase | Version | Status |
|-------|---------|:------:|
| Core pipeline — CLI → LLM → GitLab comment | `v0.1.0-alpha` | 🔨 In progress |
| AST precision, linter filtering, structured output | `v1.0.0` | 📋 Planned |
| Async Indexer, Jira sync, `/dismiss` feedback loop | `v1.1.0+` | 📋 Planned |

See [`docs/roadmap.md`](docs/roadmap.md) for full milestone definitions and acceptance criteria.

---

## Project Structure

```
themis/
├── src/
│   ├── cli/                        # CLI entrypoint (Click)
│   ├── review_engine/
│   │   ├── domain/                 # Pure business logic, no I/O
│   │   │   ├── models/
│   │   │   └── services/
│   │   ├── ports/                  # Interfaces (inbound & outbound)
│   │   └── adapters/               # Concrete implementations
│   │       ├── inbound/            # CLI adapter
│   │       └── outbound/           # GitLab, LLM, Jira, AST clients
│   ├── indexer/                    # Async Indexer component
│   └── best_practices/             # Bundled best-practice rulesets
├── tests/
├── docs/
├── adr/                            # Architecture Decision Records
├── Taskfile.yml
└── pyproject.toml
```

The codebase follows **Hexagonal Architecture (Ports & Adapters)** — the domain layer contains zero infrastructure dependencies. See [`adr/`](adr/) for design decisions and [`docs/coding-standards.md`](docs/coding-standards.md) for coding conventions.

---

## Contributing

Contributions are welcome! Read [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup instructions, branching conventions, and how to run the full test suite locally.

**Before opening a PR:**

1. Review [`docs/roadmap.md`](docs/roadmap.md) and open an issue to discuss significant changes
2. Check [`adr/`](adr/) — patterns that conflict with existing ADRs will be rejected
3. Run `task run-linters && uv run pytest`
4. Keep commits small and atomic — one logical change per commit

New to the codebase? Look for [`good first issue`](https://github.com/rafalstepien/themis/issues?q=label%3A%22good+first+issue%22) labels — these are curated tasks that don't require deep familiarity with the core engine.

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

---

## License

[MIT](LICENSE)
