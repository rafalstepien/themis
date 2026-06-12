# ADR-0001: Versioning

## Context

The project operates as an open-source tool distributed across client-owned infrastructure. It consists of four tightly decoupled elements that must interact seamlessly without causing breaking changes in user pipelines:

1. **The AI Review Engine Core:** The central application logic packaged as a Docker image.
2. **The GitLab CI/CD Component Code:** The thin wrapper configuration that executes inside the user's pipeline.
3. **The Async Indexer:** The codebase crawler used to extract context (history and architecture) and write configuration templates.
4. **Repository-Level Data Files:** Configuration and context files (`config.json`, `rules.json`, `architecture.json`) that live permanently inside the user's repository.

Managing independent semantic versions for all four items creates an aggressive "compatibility matrix" support overhead that a solo developer cannot sustain.

---

## Decision
We will implement a **Dual-Track Versioning System** to isolate application delivery from repository-stored data configurations. Additionally, the application tools (Async Indexer) will be bundled into a single codebase to enforce version synchronization.

### Track A: Software Release Lockstep (Engine, Indexer, and Component)
The Core Engine, Async Indexer, and GitLab CI/CD Component will share the exact same version tag (e.g., `v1.2.0`) in strict lockstep.

* **Monorepo Delivery:** The Engine and the Indexer are compiled into a **single application container image**. Their execution behavior is controlled simply via CLI mode flags: `ai-review-tool --mode=engine` and `ai-review-tool --mode=indexer`
* **Component Automation:** The GitLab CI/CD Component at version `v1.2.0` is hardcoded to pull the Docker image tag `v1.2.0`.
* **Bumping Cadence:** Versions follow standard Semantic Versioning (SemVer). Any update to the system—even if it only modifies the engine—bumps the version tag for all software components simultaneously.

### Track B: Data Schema Versioning
To prevent un-updated engines from breaking when encountering updated repository files (see scenario below), a hardcoded schema version key (`$schema_version`) will be embedded directly within user-space JSON files (e.g., `rules.json`).
* **Decoupled Verification:** The Engine reads the `$schema_version` integer first.
* **Fallback Behavior:** If an older engine hits a newer schema version that it does not understand, it will terminate gracefully with a clear instruction message rather than throwing an unhandled parsing crash inside the user's production pipeline.


### Example: The Pipeline Crash Scenario
1. A company adopts the system at version `v1.0.0`. The engine reads a basic `rules.json` file.
2. Two months later, we release version `v2.0.0` with a brand-new architectural review feature that completely changes the key names inside `rules.json`.
3. A developer at that company updates their local Async Indexer to `v2.0.0` to generate the new rules format. The tool overwrites their repository's `rules.json`.
4. **The Failure:** The company's automated CI pipeline is still pinned to the stable `v1.0.0` engine wrapper. The old engine pulls the new `rules.json`, encounters keys it doesn't recognize, crashes hard, and completely blocks the company's internal merge request pipelines.
With Track B implemented, the `v1.0.0` engine safely catches the schema version mismatch and outputs a clean warning message instead of a crash.

---
## Consequences
### Positive

* **Zero Compatibility Matrix Support:** Users instantly know that if they run the `v1.3.0` pipeline component, they must run the `v1.3.0` indexer version to generate matching data structures.
* **Simplified Solo Maintenance:** One code repository, one automated build pipeline, and one unified Docker tag to push per release.
* **Pipeline Resilience:** Client execution loops are explicitly protected against structural local database changes.


### Negative
* **Redundant Image Bumps:** Fixing a minor typo or prompt inside the Review Engine forces an image version bump for the Indexer component, even if the indexer's source code was untouched.
* **Slightly Larger Image Size:** Packaging both execution modes into a single Docker container marginally increases the initial image footprint, though runtime execution performance remains completely unaffected.