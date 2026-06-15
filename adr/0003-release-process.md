# ADR-0003: Release Process

Date: 2026-06-15
Status: Accepted

## Context

The project ships two separate artifacts that must stay version-aligned:

1. **The AI Code Review Engine** — source on GitHub, built as a Docker image and pushed to a public DockerHub repository.
2. **The GitLab CI/CD Component** — a thin wrapper hosted on GitLab and published to the GitLab CI/CD Catalog, which references a specific Engine image.

We need a release process that is easy to work against day-to-day, gives room to test changes before they are blessed, and makes it hard to ship a broken image to consumers once the project is public.

Constraints and preferences shaping the decision:

- Development is trunk-based: changes land on a branch, merge to `main` via MR.
- We want a runnable, testable image for every merge to `main`, not only at release time.
- The two artifacts live on two different forges (GitHub and GitLab), so cross-forge coordination has to be accounted for.

## Decision

### Versioning and branching

- **The git tag is the single source of truth for the version.** The maintainer decides patch/minor/major and encodes it in an annotated tag of the form `v1.2.3` (semver). The pipeline reads the tag; it does not compute or bump the version itself.
- **Tags are cut directly from `main`. No release branches** for now. Release branches will only be introduced if/when multiple released versions must be supported simultaneously (e.g. backporting a fix to an old minor line).
- **Version tags are immutable.** A published `1.2.3` is never re-pushed or moved.

### Pipelines (GitHub Actions, Engine repo)

- **On every MR to `main`:** run lint + unit tests. These checks gate the merge.
- **On every merge to `main`:** run the full test suite, then build and push a testing image tagged:
  - `edge` — moving, always points at newest `main`.
  - `sha-<short>` — immutable, identifies that exact commit.
  
  These images are **not** version-numbered. The version is unknown at merge time because it is chosen by the maintainer at tag time.
- **On a `v1.2.3` tag:** run the full pipeline (lint + test + build) and push the released image tagged:
  - `1.2.3` — immutable; this is what consumers pin.
  - `1.2`, `1`, `latest` — optional moving "convenience" tags pointing at the same digest, offered for external consumers who want to track a patch line / major line / newest stable. May be reduced to just `1.2.3` + `latest` initially.
  
  `latest` must never point at a pre-release.

### Pre-release (optional)

- A release candidate may be cut as `v1.2.3-rc.1`, which runs the full release pipeline and produces a `1.2.3-rc.1` image built exactly the way the real release builds it. Used as a dry run to validate the release path (signing, multi-arch, base image) before blessing `v1.2.3`. Skippable for routine releases.

### GitLab CI/CD Component

- **Component version tracks the Engine image version 1:1.** Component `1.2.3` references Engine image `1.2.3`.
- **The component pins an exact image version** (ideally by digest), never a moving tag, so that "component `1.2.3` runs only image `1.2.3`" stays true.
- **The component bump is manual:** when a new released image is available, open an MR in the component repo to update the referenced image version, tag the GitLab repo with the matching semver, and publish to the catalog. Cross-forge automation is explicitly out of scope for now.

### Guardrails

- **Branch protection on `main`:** MR checks must pass before merge.
- **Protected tags:** restrict tag creation to a `v*` pattern / authorized maintainers so arbitrary contributors cannot trigger a release once the repo is public.
- **`[skip ci]` isolation:** the Async Indexer and `/dismiss` learning-loop commits carry `[skip ci]`. These must never trigger a release pipeline, and a release pipeline must never be suppressible by them.

## Consequences

**Positive**

- Clean separation between "buildable" (every commit, via `edge` / `sha-`) and "released" (tagged, versioned). There is always something to test without polluting the release channel.
- The version is a deliberate human decision recorded in one place (the tag), with no hidden bump logic to debug.
- Consumers get a stable contract: pin `1.2.3` (or a digest) and it never changes underneath them; the component rides an exact version, not a moving tag.
- Minimal ceremony for a solo maintainer — no release branches, no version-computation tooling to start.
- Guardrails make it hard to ship a broken or unauthorized image once public.

**Negative / costs**

- The Engine and Component releases are coordinated manually across two forges; a release is "done" only after the second, manual component bump. Forgetting it leaves the catalog pointing at an old image.
- Choosing the semver bump is a manual judgement call (no Conventional Commits automation yet), so version discipline depends on the maintainer.
- Moving tags (`1.2`, `1`, `latest`) are a convenience that must be maintained correctly; a mistake (e.g. `latest` on a pre-release) would mislead consumers.

**Deferred (revisit later)**

- Automating the version decision via Conventional Commits + release-please / semantic-release, paired with a `CHANGELOG.md` (Keep a Changelog format).
- Supply-chain hardening: cosign image signing, SBOM generation, base image pinned by digest, multi-arch (amd64/arm64) builds.
- Cross-forge automation: a bot that opens the component bump MR when a GitHub release lands.
- Release branches, if multiple released versions ever need parallel support.
- The exact GitLab catalog / `release` publish YAML should be verified against current GitLab documentation at implementation time, as that syntax has evolved.