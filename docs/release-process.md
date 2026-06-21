# Release Process

The operational runbook for shipping a new version. For *why* it's shaped this
way (trunk-based, two forges, manual component bump, deferred automation), see
[`adr/0003-release-process.md`](../adr/0003-release-process.md).

A release ships three version-locked artifacts across two forges:

| Artifact | Lives on | Tagged |
|---|---|---|
| Engine + Indexer Docker image | DockerHub (`rafalstepien/themis`) | `0.1.0` |
| `themis-ci` GitLab component | GitLab | `0.1.0` |
| Git tag on `themis` | GitHub | `0.1.0` |

## Version convention

**One string, used verbatim everywhere — no `v` prefix.** The git tag, the
Docker image tag, the GitLab component tag, and the `push_image.sh` argument are
all the identical string (e.g. `0.1.0`, or `0.1.0-rc.1` for a pre-release).

> The git tag is the single source of truth for the version. The pipeline does
> not compute or bump it — you choose the semver bump and encode it in the tag.
> Published version tags are immutable: never re-push or move a `0.1.0`.

## Prerequisites (one-time)

- `docker login` to the DockerHub account that owns `rafalstepien/themis`
  (`push_image.sh` builds multi-arch `linux/amd64,linux/arm64` via buildx).
- `env_files/.env.test` exists (copy from the example and fill in the GitLab
  token + project details) — required by the pre-release gate below.
- Push access to the `themis-ci` GitLab repo and the consumer repo.

---

## Step 0 — Pre-release gate (do this BEFORE tagging)

The release is only worth cutting if the review is actually good. This gate runs
the engine **from source** against `themis-example` — no image, no tag needed.

```bash
./scripts/test_local.sh        # runs the engine against themis-example
```

**Pass criterion (for 0.1.0):** on the four canonical experiments the review
must produce a strong, specific result — not a generic nit:

1. Architecture violation — `orders/domain/services.py` imports `catalog.domain` directly instead of via a port.
2. Rules violation — a price represented as `float` instead of `Money` minor units.
3. Rules violation — `gateway.authorize(...)` wrapped in a bare `except Exception`.
4. A pure logic bug (off-by-one / missing `await`).

If the output is weak or generic, **stop** — fix prompt/context loading first.
No image, README, or visual saves a bad review.

---

## Step 1 — Repository `themis` (engine)

1. Create a feature branch and implement the change.
2. Open an MR to `main`. CI (`.github/workflows/ci.yml`) runs lint, type-check
   and unit tests automatically — these gate the merge.
3. Collect approvals and merge.
4. Tag `main` with the version, no `v` prefix:
   ```bash
   git tag -a 0.1.0 -m "Release 0.1.0" && git push origin 0.1.0
   ```
5. Build and push the multi-arch image (currently manual — see "Automation" below):
   ```bash
   ./scripts/push_image.sh 0.1.0
   ```
6. Verify `rafalstepien/themis:0.1.0` is live on DockerHub.

## Step 2 — Repository `themis-ci` (component)

1. Branch `feat/bump-to-0.1.0`.
2. Update the image reference in `themis-ci/templates/themis-ci.yml` to
   `rafalstepien/themis:0.1.0`.
3. MR → merge to `main`.
4. Tag the repo with the **matching** version `0.1.0` and publish to the catalog.

> The component tag must always equal the image version. Component `0.1.0` runs
> only image `0.1.0`.

## Step 3 — Consumer repo (`themis-example` / client)

1. Bump the component in `.gitlab-ci.yml`:
   `component: gitlab.com/rafalstepien/themis-ci/themis-ci@0.1.0`.
2. Open a test MR and confirm the live review meets the Step 0 pass criterion —
   this time end-to-end through the published image, not from source.

---

## 0.1.0 launch checklist

- [ ] Step 0 gate passes on all four experiments (`test_local.sh`).
- [ ] `themis` tagged `0.1.0`; image `rafalstepien/themis:0.1.0` on DockerHub.
- [ ] `themis-ci` bumped + tagged `0.1.0`, published to catalog.
- [ ] `themis-example` `.gitlab-ci.yml` pinned to `@0.1.0`; live MR review verified.
- [ ] Engine frozen — no further engine work before launch (per CLAUDE.md §10).

## Automation status

- **Automated today:** lint + type-check + unit tests on every MR to `main`.
- **Still manual:** image build/push (`push_image.sh`) and the cross-forge
  component bump. ADR-0003 describes the deferred target state (CI image build
  on tag, `edge`/`sha-` images on merge, protected tags, `[skip ci]` isolation,
  supply-chain hardening). **Out of scope for the 0.1.0 launch** — do not build
  it now.
