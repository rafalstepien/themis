# Overview
This project is an advanced, open-source, GitLab-native code review validation gate. It analyzes code submitted within Merge Requests (MRs), identifies critical logical bugs, security vulnerabilities, and architectural errors, and injects high-signal feedback directly into the MR thread using the GitLab API.

# Core Assumptions & Product Pillars
* **GitLab-Exclusive Focus:** Optimized entirely for GitLab workflows, but leaves the door open for later GitHub integration.
* **5-Minute Onboarding:** Designed as a native GitLab (later also GitHub) CI/CD Component. Teams can integrate the validation gate into existing workflows with zero external infrastructure setup.
* **AST-Native Parsing:** Utilizes Tree-sitter abstract syntax tree parsing to ensure precise, byte-offset grounding of recommendations rather than relying on brittle regex or raw token slicing.
* **Secure BYOK Architecture:** Follows a strict Bring-Your-Own-Key model. Because execution occurs entirely within the customer’s-owned CI runners, source code never leaves corporate boundaries, completely removing enterprise compliance and data-retention friction.
* **High-Signal Noise Filtering:** Purpose-built to reject minor stylistic or syntax modifications ("linter nits"). It cross-references active local linter configurations (e.g., ESLint, Ruff) to suppress redundant feedback, dedicating its context window strictly to non-trivial logic and architectural flaws.
* **Multi-Context Integration Layer:** Synthesizes multiple unique metadata channels to ground reviews:
    * **Version-Controlled Rule Inheritance:** Uses an offline compiler to translate resolved debates from past merge requests into plain-text, repo-level guidelines.
    * **Heterogeneous Module Context:** Adjusts evaluation strictness and architectural tolerances dynamically based on the target folder/directory (e.g., legacy codebases vs. clean microservices).
    * **Domain Best Practices:** Out-of-the-box depth covering common web frameworks (Django, FastAPI), concurrency bottlenecks, and OWASP top-10 security patterns.
    * **Functional Business Context (Jira/GitLab Issues):** Automatically cross-references changes against linked project tracking requirements to generate an inline Ticket Requirements Verification Matrix.
* **Native Cohort Layouts:** Appends structural change cohorts directly to the MR text description, allowing reviewers to conceptualize large diffs without forcing them out of the native GitLab UI.
* **Architecture awareness:** Cross-repository system architecture and API contract awareness to detect downstream dependency and integration breakages.

# Intentionally Omitted Scope (MVP Phase)
* **Autonomous Fixing (Non-Agentic):** The goal is strictly to lower cognitive overhead and ensure code integrity, not to auto-commit structural changes back to the branch.
* **Proprietary Dashboards / External Interfaces:** Avoids the steep learning curves and workflow friction associated with external code-review browsers (e.g., CodeRabbit Atlas). Reviewers remain entirely within their native GitLab Merge Request view.
* **In-Comment Conversational Chat Loops:** Replaced by a lightweight, command-triggered mutation framework (e.g., a dev replying with `/dismiss` auto-generates an exclusion pattern committed back to the repo settings).

